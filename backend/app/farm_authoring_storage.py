"""Tenant-owned immutable authored farm intents over actual source authorities."""

from datetime import date, datetime, timezone
from hashlib import sha256
import json
import re
from typing import Literal, Self
from uuid import UUID

from pydantic import field_validator, model_validator
from psycopg import sql

from .api_contracts import JobStatus, public_job_status
from .economic_contracts import utc, untrusted_data
from .farm_input_compiler import compile_farm_inputs
from .farm_inputs import FarmInputs, Identifier, canonical_farm_inputs, validate_economic_scope
from .farm_replay_scenario import FarmReplayScenarioService, READ_SCOPES as REPLAY_SCOPES
from .job_store import JobIntentConflict
from .jobs import canonical_input_bytes
from .market_scenario import MarketScenarioService
from .provenance import Digest, FrozenContract
from .thermal_units import utc as utc_text


INPUT_VERSION='farm-authoring-input-v1'
READ_SCOPES=tuple(scope for scope in REPLAY_SCOPES if scope!='thermal_scenario_read')
WRITE_SCOPES=('farm_scenario_write',)+READ_SCOPES


class FarmAssumptionRights(FrozenContract):
    schema_version: Literal['farm-assumption-rights-v1']
    scenario_id: Identifier
    scenario_revision: Identifier
    declaration_id: Identifier
    revision: Identifier
    origin: Literal['user']
    evidence_level: Literal['assumed']
    ownership_asserted: bool
    access: bool
    store: bool
    transform: bool
    use: bool
    display: bool
    redistribute: bool
    available_at: datetime
    scope_start: date
    scope_end: date

    _utc=field_validator('available_at')(utc)

    @model_validator(mode='after')
    def asserted_user_use(self) -> Self:
        if (not all(getattr(self,name) is True for name in
                ('ownership_asserted','access','store','transform','use','display')) or
                self.redistribute is not False or self.scope_end < self.scope_start):
            raise ValueError('farm user assumption rights unavailable')
        return self


class FarmAuthoringRequest(FrozenContract):
    schema_version: Literal['farm-authoring-request-v1']
    farm: FarmInputs
    rights: FarmAssumptionRights

    @model_validator(mode='after')
    def bound_rights(self) -> Self:
        if ((self.farm.scenario_id,self.farm.scenario_revision) !=
                (self.rights.scenario_id,self.rights.scenario_revision) or
                self.rights.available_at > self.farm.decision_at or
                not self.rights.scope_start <= self.farm.period_start <=
                self.farm.period_end <= self.rights.scope_end):
            raise ValueError('farm rights do not cover authored version')
        return self


class FarmAuthoringSummary(FrozenContract):
    scenario_id: Identifier
    scenario_revision: Identifier
    scenario_sha256: Digest
    farm_sha256: Digest
    numeric_input_sha256: Digest
    rights_sha256: Digest
    registration_status: Literal['registered_unpublished_inputs']
    intent_job: JobStatus


class FarmAuthoringCursor(FrozenContract):
    created_at: datetime
    job_id: UUID


class FarmAuthoringPage(FrozenContract):
    items: list[FarmAuthoringSummary]
    next_cursor: FarmAuthoringCursor | None


class FarmAuthoringActivity(FrozenContract):
    kind: Literal['review','simulation']
    job: JobStatus
    review_job: JobStatus | None


class FarmAuthoringActivityPage(FrozenContract):
    scenario_id: Identifier
    scenario_revision: Identifier
    registration_sha256: Digest
    items: list[FarmAuthoringActivity]
    next_cursor: FarmAuthoringCursor | None


class FarmAuthoringHold(ValueError):
    pass


class FarmAuthoringService:
    def __init__(self,replay):
        self.replay=replay
        self._binding()

    def _binding(self):
        if type(self.replay) is not FarmReplayScenarioService or self.replay.owned_research is None:
            raise FarmAuthoringHold('authored farm runtime authority unavailable')
        self.replay._binding()

    def _pointers(self):
        self._binding()
        return (self.replay,self.replay._pointers())

    def _guard(self,tenant,pointers,scopes):
        if self._pointers()!=pointers:
            raise FarmAuthoringHold('authored farm runtime changed')
        self.replay._guard(tenant,pointers[1],scopes)

    @staticmethod
    def _key(scenario_id,revision):
        raw=canonical_input_bytes({'scenario_id':scenario_id,'revision':revision})
        return INPUT_VERSION+':'+sha256(raw).hexdigest()

    def _find(self,tenant,scenario_id,revision):
        jobs=self.replay.jobs
        with jobs.connect() as conn:
            row=conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND stage='collection' AND idempotency_key=%s")
                .format(jobs._table('jobs')),(tenant,self._key(scenario_id,revision))).fetchone()
            if row is not None:
                jobs._verified_input(row)
            return row

    def _prepare(self,tenant,body,review_at_utc):
        try:
            farm=body.farm
            owned=self.replay.owned_research
            with self.replay.jobs.connect() as conn:
                root=self.replay.jobs._locked_job(conn,tenant,farm.research_job_id)
                if root is None or root['stage']!='research' or root['state'] in ('canceled','failed'):
                    raise ValueError()
                research=json.loads(self.replay.jobs._verified_input(root))
            if owned.authority_snapshot(root,research) is None:
                raise ValueError()
            runs=self.replay.thermal.runs
            snapshot=runs.get_snapshot(tenant,farm.snapshot_id)
            context=runs.get_decision_context(tenant,farm.snapshot_id,farm.decision_context_id)
            hold=self.replay.thermal.holds.get_market_hold_report(farm.market_context.hold_report_id)
            if snapshot is None or context is None or hold is None:
                raise ValueError()
            weather=json.loads(snapshot['weather_raw'])
            if (research['period_start_utc']!=weather['start_utc'] or
                    research['period_end_utc']!=weather['end_utc'] or
                    research['goal_id']!=farm.goal_id or
                    research['decision_context_id']!=farm.decision_context_id or
                    research['decision_at_utc']!=context['decision_at_utc'] or
                    research['claim_mode']!=context['claim_mode'] or
                    research['decision_time_kind']!=context['decision_time_kind'] or
                    context['claim_mode']!='ex_post_replay' or
                    utc_text(context['decision_at_utc'])!=farm.decision_at or
                    (hold['tenant_id'],hold['snapshot_id'],hold['decision_context_id'],hold['decision_at'],
                     hold['claim_mode'],hold['decision_time_kind']) !=
                    (tenant,farm.snapshot_id,farm.decision_context_id,farm.decision_at,
                     context['claim_mode'],context['decision_time_kind'])):
                raise ValueError()
            _,economic,candidate=MarketScenarioService(self.replay.candidates).validate_pinned(
                farm.economic.scenario_id,farm.economic.revision,tenant)
            if candidate['candidate_id']!=farm.economic.candidate_id:
                raise ValueError()
            validate_economic_scope(farm,economic,tenant)
            compiled=compile_farm_inputs(farm,snapshot['manifest_raw'],snapshot['weather_raw'],
                snapshot['thermal_raw'],review_at_utc=review_at_utc)
            rights_raw=canonical_input_bytes(body.rights.model_dump(mode='json'))
            binding={'research_input_sha256':root['input_sha256'],
                'research_registry_sha256':self.replay.registry.sha256,
                'point':research['point'],'spatial_support':'pending_research',
                'snapshot_id':farm.snapshot_id,'decision_context_id':farm.decision_context_id,
                'context_sha256':context['context_sha256'],
                'market_hold_report_id':hold['hold_report_id'],
                'economic_candidate_id':candidate['candidate_id'],
                **{key:candidate[key] for key in ('economic_scenario_sha256','shock_sha256',
                    'rights_manifest_sha256','binding_manifest_sha256')}}
            return compiled,rights_raw,binding
        except PermissionError:
            raise
        except Exception:
            raise FarmAuthoringHold('authored farm references unavailable') from None

    @staticmethod
    def _summary(row,body,compiled,rights_raw):
        return FarmAuthoringSummary(scenario_id=body.farm.scenario_id,
            scenario_revision=body.farm.scenario_revision,scenario_sha256=row['input_sha256'],
            farm_sha256=compiled.farm_sha256,numeric_input_sha256=compiled.thermal_sha256,
            rights_sha256=sha256(rights_raw).hexdigest(),
            registration_status='registered_unpublished_inputs',intent_job=public_job_status(row))

    def submit(self,tenant,body):
        pointers=self._pointers()
        guard=lambda:self._guard(tenant,pointers,WRITE_SCOPES)
        guard()
        try:
            body=FarmAuthoringRequest.model_validate(untrusted_data(body))
            request_raw=canonical_input_bytes(body.model_dump(mode='json'))
            previous=self._find(tenant,body.farm.scenario_id,body.farm.scenario_revision)
            if previous is not None and canonical_input_bytes(json.loads(previous['input_bytes']).get('request'))!=request_raw:
                raise JobIntentConflict('conflicting immutable farm authoring version')
            review_at_utc=datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')
            if previous is not None:
                review_at_utc=json.loads(previous['input_bytes'])['review_at_utc']
            compiled,rights_raw,binding=self._prepare(tenant,body,review_at_utc)
            value={'input_version':INPUT_VERSION,'tenant_id':tenant,
                'request':body.model_dump(mode='json'),'review_at_utc':review_at_utc,
                'binding':binding,'numeric_input':json.loads(compiled.thermal_bytes),
                'farm_sha256':compiled.farm_sha256,
                'numeric_input_sha256':compiled.thermal_sha256,
                'rights_sha256':sha256(rights_raw).hexdigest()}
            def final_guard():
                guard()
                try:
                    again,rights_again,binding_again=self._prepare(tenant,body,review_at_utc)
                    if (again!=compiled or rights_again!=rights_raw or binding_again!=binding):
                        raise FarmAuthoringHold('authored farm inputs changed')
                finally:
                    guard()
            row=self.replay.jobs.submit(tenant,'collection',value,
                self._key(body.farm.scenario_id,body.farm.scenario_revision),commit_guard=final_guard)
            return self._summary(row,body,compiled,rights_raw)
        finally:
            guard()

    def _read(self,tenant,scenario_id,revision):
        if not self.replay.jobs._has_scope(tenant,'metadata'):
            principal=self.replay.jobs.principal_provider()
            if principal is None or principal.get('tenant_id')!=tenant:
                return None
        pointers=self._pointers()
        guard=lambda:self._guard(tenant,pointers,READ_SCOPES)
        guard()
        try:
            row=self._find(tenant,scenario_id,revision)
            if row is None:
                return None
            value=json.loads(row['input_bytes'])
            body=FarmAuthoringRequest.model_validate_json(canonical_input_bytes(value['request']))
            if (body.farm.scenario_id,body.farm.scenario_revision)!=(scenario_id,revision):
                raise FarmAuthoringHold('authored farm identity differs')
            compiled,rights_raw,binding=self._prepare(tenant,body,value['review_at_utc'])
            expected={'input_version':INPUT_VERSION,'tenant_id':tenant,
                'request':body.model_dump(mode='json'),'review_at_utc':value['review_at_utc'],
                'binding':binding,'numeric_input':json.loads(compiled.thermal_bytes),
                'farm_sha256':compiled.farm_sha256,
                'numeric_input_sha256':compiled.thermal_sha256,
                'rights_sha256':sha256(rights_raw).hexdigest()}
            if canonical_input_bytes(expected)!=row['input_bytes']:
                raise FarmAuthoringHold('authored farm stored input differs')
            return row,body,compiled,rights_raw,binding
        finally:
            guard()

    def get(self,tenant,scenario_id,revision):
        record=self._read(tenant,scenario_id,revision)
        return self._summary(record[0],record[1],record[2],record[3]) if record is not None else None

    def list(self,tenant,*,limit=20,before_created_at=None,before_job_id=None):
        """List owned registration metadata; selecting one still requires ``get``."""
        if (type(limit) is not int or not 1 <= limit <= 50 or
                (before_created_at is None) != (before_job_id is None) or
                (before_created_at is not None and
                 (type(before_created_at) is not datetime or before_created_at.tzinfo is None or
                  type(before_job_id) is not UUID))):
            raise ValueError('authored farm catalog cursor invalid')
        pointers=self._pointers()
        guard=lambda:self._guard(tenant,pointers,READ_SCOPES)
        guard()
        try:
            cursor=sql.SQL('')
            args=[tenant, INPUT_VERSION+':%']
            if before_created_at is not None:
                cursor=sql.SQL(' AND (created_at, job_id) < (%s, %s)')
                args.extend((before_created_at,before_job_id))
            args.append(limit+1)
            jobs=self.replay.jobs
            with jobs.connect() as conn:
                rows=conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND stage='collection' "
                    'AND idempotency_key LIKE %s{} ORDER BY created_at DESC, job_id DESC LIMIT %s')
                    .format(jobs._table('jobs'),cursor),args).fetchall()
                items=[]
                for row in rows:
                    value=json.loads(jobs._verified_input(row))
                    if (set(value)!={'input_version','tenant_id','request','review_at_utc',
                            'binding','numeric_input','farm_sha256','numeric_input_sha256',
                            'rights_sha256'} or value.get('input_version')!=INPUT_VERSION or
                            value.get('tenant_id')!=tenant):
                        raise FarmAuthoringHold('authored farm catalog input unavailable')
                    body=FarmAuthoringRequest.model_validate_json(
                        canonical_input_bytes(value['request']))
                    if (row['idempotency_key']!=self._key(body.farm.scenario_id,
                            body.farm.scenario_revision) or
                            value['farm_sha256']!=sha256(canonical_farm_inputs(body.farm)).hexdigest() or
                            value['numeric_input_sha256']!=sha256(canonical_input_bytes(
                                value['numeric_input'])).hexdigest() or
                            value['rights_sha256']!=sha256(canonical_input_bytes(
                                body.rights.model_dump(mode='json'))).hexdigest()):
                        raise FarmAuthoringHold('authored farm catalog input differs')
                    items.append(FarmAuthoringSummary(scenario_id=body.farm.scenario_id,
                        scenario_revision=body.farm.scenario_revision,
                        scenario_sha256=row['input_sha256'],farm_sha256=value['farm_sha256'],
                        numeric_input_sha256=value['numeric_input_sha256'],
                        rights_sha256=value['rights_sha256'],
                        registration_status='registered_unpublished_inputs',
                        intent_job=public_job_status(row)))
            guard()
            next_cursor=(FarmAuthoringCursor(created_at=rows[limit-1]['created_at'],
                job_id=rows[limit-1]['job_id']) if len(rows)>limit else None)
            return FarmAuthoringPage(items=items[:limit],next_cursor=next_cursor)
        finally:
            guard()

    def activity(self,tenant,scenario_id,revision,expected_sha256,*,limit=20,
                 before_created_at=None,before_job_id=None):
        """Project immutable authored job links; current use still requires admission/read checks."""
        from .farm_authored_review import INPUT_VERSION as REVIEW_VERSION, INPUT_FIELDS as REVIEW_FIELDS
        from .farm_authored_simulation import INPUT_VERSION as SIM_VERSION
        if (type(limit) is not int or not 1 <= limit <= 50 or
                (before_created_at is None)!=(before_job_id is None) or
                (before_created_at is not None and
                 (type(before_created_at) is not datetime or before_created_at.tzinfo is None or
                  type(before_job_id) is not UUID))):
            raise ValueError('authored farm activity cursor invalid')
        pointers=self._pointers()
        guard=lambda:self._guard(tenant,pointers,READ_SCOPES)
        guard()
        try:
            registration=self._find(tenant,scenario_id,revision)
            if registration is None:
                return None
            if registration['input_sha256']!=expected_sha256:
                raise FarmAuthoringHold('authored farm activity registration differs')
            jobs=self.replay.jobs
            cursor=sql.SQL('')
            args=[tenant,REVIEW_VERSION+':%',SIM_VERSION+':%',expected_sha256]
            if before_created_at is not None:
                cursor=sql.SQL(' AND (created_at, job_id) < (%s, %s)')
                args.extend((before_created_at,before_job_id))
            args.append(limit+1)
            with jobs.connect() as conn:
                rows=conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND "
                    "((stage='collection_review' AND idempotency_key LIKE %s) OR "
                    "(stage='simulation' AND idempotency_key LIKE %s)) AND "
                    "convert_from(input_bytes,'UTF8')::jsonb->>'registration_sha256'=%s{} "
                    'ORDER BY created_at DESC, job_id DESC LIMIT %s')
                    .format(jobs._table('jobs'),cursor),args).fetchall()
                items=[]
                for row in rows:
                    value=json.loads(jobs._verified_input(row))
                    review=row['stage']=='collection_review'
                    version=REVIEW_VERSION if review else SIM_VERSION
                    expected_fields=(REVIEW_FIELDS if review else {'input_version','tenant_id',
                        'review_job_id','scenario_id','scenario_revision','registration_sha256'})
                    key=row['idempotency_key'].removeprefix(version+':')
                    if (set(value)!=expected_fields or value.get('input_version')!=version or
                            value.get('tenant_id')!=tenant or
                            (value.get('scenario_id'),value.get('scenario_revision'),
                             value.get('registration_sha256')) !=
                            (scenario_id,revision,expected_sha256) or
                            re.fullmatch(r'[0-9a-f]{64}',key) is None):
                        raise FarmAuthoringHold('authored farm activity input differs')
                    linked=None
                    if not review:
                        try:
                            review_id=UUID(value['review_job_id'])
                        except (KeyError,TypeError,ValueError):
                            raise FarmAuthoringHold('authored farm activity review link unavailable') from None
                        parent=conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s "
                            "AND job_id=%s AND stage='collection_review'")
                            .format(jobs._table('jobs')),(tenant,review_id)).fetchone()
                        if parent is None:
                            raise FarmAuthoringHold('authored farm activity review link unavailable')
                        parent_value=json.loads(jobs._verified_input(parent))
                        if (set(parent_value)!=REVIEW_FIELDS or
                                parent_value.get('input_version')!=REVIEW_VERSION or
                                parent_value.get('tenant_id')!=tenant or
                                (parent_value.get('scenario_id'),
                                 parent_value.get('scenario_revision'),
                                 parent_value.get('registration_sha256'))!=
                                (scenario_id,revision,expected_sha256)):
                            raise FarmAuthoringHold('authored farm activity review link differs')
                        linked=public_job_status(parent)
                    items.append(FarmAuthoringActivity(kind='review' if review else 'simulation',
                        job=public_job_status(row),review_job=linked))
            guard()
            again=self._find(tenant,scenario_id,revision)
            if again is None or again['input_sha256']!=expected_sha256:
                raise FarmAuthoringHold('authored farm activity registration changed')
            next_cursor=(FarmAuthoringCursor(created_at=rows[limit-1]['created_at'],
                job_id=rows[limit-1]['job_id']) if len(rows)>limit else None)
            return FarmAuthoringActivityPage(scenario_id=scenario_id,
                scenario_revision=revision,registration_sha256=expected_sha256,
                items=items[:limit],next_cursor=next_cursor)
        finally:
            guard()

    def read_registration(self,tenant,scenario_id,revision,expected_sha256):
        record=self._read(tenant,scenario_id,revision)
        if record is None or record[0]['input_sha256']!=expected_sha256:
            raise FarmAuthoringHold('authored farm execution input unavailable')
        _,body,compiled,_,binding=record
        return {'farm':body.farm,'user_rights_declaration':body.rights,'binding':binding,
            'numeric_input_bytes':compiled.thermal_bytes,
            'compiled':json.loads(compiled.thermal_bytes),
            'scenario_sha256':record[0]['input_sha256']}
