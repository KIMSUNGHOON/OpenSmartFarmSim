"""Immutable joint input selection; registration grants no execution or claim."""

from datetime import datetime, timedelta
from hashlib import sha256
import json
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator
from psycopg import sql

from .api_contracts import JobStatus, public_job_status
from .api_economic_scenario import EconomicScenarioService
from .economic_contracts import utc
from .job_store import JobIntentConflict
from .jobs import canonical_input_bytes
from .market import UnavailableMarketContext
from .market_scenario import MarketScenarioService
from .owned_research import OwnedResearchService
from .provenance import FrozenContract, Digest
from .research_registry import ResearchRegistry
from .thermal_scenario_store import ThermalScenarioStore, IDENTIFIER


INPUT_VERSION = 'farm-replay-scenario-input-v1'
READ_SCOPES = ('farm_scenario_read', 'metadata', 'artifact', 'thermal_scenario_read',
    'thermal_snapshot_read', 'decision_context_read', 'market_hold_context_read',
    'market_source_read', 'market_candidate_read')
WRITE_SCOPES = ('farm_scenario_write',) + READ_SCOPES


class ScenarioPin(FrozenContract):
    scenario_id: str = Field(pattern=IDENTIFIER, max_length=200)
    revision: str = Field(pattern=IDENTIFIER, max_length=200)
    sha256: Digest


class EconomicPin(ScenarioPin):
    candidate_id: Digest


class FarmReplayScenarioRequest(FrozenContract):
    schema_version: Literal['farm-replay-scenario-v1']
    scenario_id: str = Field(pattern=IDENTIFIER, max_length=200)
    scenario_revision: str = Field(pattern=IDENTIFIER, max_length=200)
    research_job_id: str = Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    thermal: ScenarioPin
    economic: EconomicPin
    decision_at: datetime
    market_context: UnavailableMarketContext
    goal_id: Literal['historical-thermal-replay']
    origin: Literal['user']
    evidence_level: Literal['assumed']

    @field_validator('decision_at')
    @classmethod
    def decision_utc(cls, value):
        return utc(value)


class FarmReplayScenarioSummary(FrozenContract):
    scenario_id: str = Field(pattern=IDENTIFIER, max_length=200)
    scenario_revision: str = Field(pattern=IDENTIFIER, max_length=200)
    scenario_sha256: Digest
    registration_status: Literal['registered_intent']
    intent_job: JobStatus


class FarmReplayScenarioHold(ValueError):
    pass


class FarmReplayScenarioService:
    def __init__(self, jobs, thermal, candidates, registry, owned_research=None):
        self.jobs, self.thermal, self.candidates, self.registry = jobs, thermal, candidates, registry
        self.owned_research = owned_research
        self.economic = EconomicScenarioService(jobs, candidates)
        self._binding()

    def _binding(self):
        self.economic._binding()
        if (type(self.thermal) is not ThermalScenarioStore or type(self.registry) is not ResearchRegistry or
                self.economic.jobs is not self.jobs or self.economic.candidates is not self.candidates):
            raise RuntimeError('farm scenario binding rejected')
        self.thermal._binding()
        jobs, thermal, candidates = self.jobs, self.thermal, self.candidates
        if (thermal.runtime_identity != jobs.runtime_identity or thermal.dsn != jobs._dsn or
                thermal.schema != jobs.schema or thermal.runs._principal_provider is not jobs.principal_provider or
                candidates._source._holds is not thermal.holds or
                candidates._source._holds._context_store is not thermal.runs):
            raise RuntimeError('farm scenario binding rejected')
        if self.owned_research is not None:
            if (type(self.owned_research) is not OwnedResearchService or self.owned_research.store is not jobs or
                    self.owned_research.runs is not thermal.runs or self.owned_research.catalog is not self.registry):
                raise RuntimeError('farm scenario research binding rejected')
            self.owned_research._binding()

    def _pointers(self):
        return (self.jobs, self.thermal, self.candidates, id(self.registry), self.economic,
            self.thermal.runs, self.thermal.holds, self.candidates._source,
            self.candidates._source._source, self.thermal.holds._scope_resolver,
            self.thermal.runs._context_verifier, self.jobs.principal_provider,
            self.jobs._dsn, self.jobs.schema, self.jobs.runtime_identity, self.owned_research,
            self.owned_research._pointers() if self.owned_research is not None else None)

    def _guard(self, tenant, pointers, scopes):
        if not all(self.jobs._has_scope(tenant, scope) for scope in scopes):
            raise PermissionError('farm scenario access denied')
        self._binding()
        if self._pointers() != pointers:
            raise RuntimeError('farm scenario binding changed')

    @staticmethod
    def _key(scenario_id, revision):
        return INPUT_VERSION + ':' + sha256(canonical_input_bytes(
            {'scenario_id':scenario_id, 'revision':revision})).hexdigest()

    def _find(self, tenant, scenario_id, revision):
        with self.jobs.connect() as conn:
            row = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND stage='collection' AND idempotency_key=%s")
                .format(self.jobs._table('jobs')), (tenant, self._key(scenario_id, revision))).fetchone()
            if row is not None:
                self.jobs._verified_input(row)
            return row

    def _references(self, tenant, body):
        try:
            with self.jobs.connect() as conn:
                root = self.jobs._locked_job(conn, tenant, body.research_job_id)
                if root is None or root['stage'] != 'research':
                    raise ValueError()
                raw = self.jobs._verified_input(root)
            request = json.loads(raw)
            bound_context = request.get('decision_context_id') is not None
            authority = (self.owned_research if bound_context else self.registry)
            if authority is None or authority.authority_snapshot(root, request) is None:
                raise ValueError()
            selected = self.thermal.get(tenant, body.thermal.scenario_id, body.thermal.revision)
            if selected is None or selected['scenario_sha256'] != body.thermal.sha256:
                raise ValueError()
            thermal = selected['scenario']
            snapshot = self.thermal.runs.get_snapshot(tenant, thermal.snapshot_id)
            context = self.thermal.runs.get_decision_context(tenant, thermal.snapshot_id, thermal.decision_context_id)
            weather = json.loads(snapshot['weather_raw'])
            _, economic, candidate = MarketScenarioService(self.candidates).validate_pinned(
                body.economic.scenario_id, body.economic.revision, tenant)
            if (candidate['candidate_id'] != body.economic.candidate_id or
                    candidate['economic_scenario_sha256'] != body.economic.sha256 or
                    thermal.goal_id != body.goal_id or request['goal_id'] != body.goal_id or
                    thermal.market_context != body.market_context or
                    economic.market_context != body.market_context or
                    economic.decision_at != body.decision_at or
                    datetime.fromisoformat(context['decision_at_utc']) != body.decision_at or
                    context['claim_mode'] != 'ex_post_replay' or
                    (bound_context and any(request[key] != context[key] for key in
                        ('decision_context_id','decision_at_utc','claim_mode','decision_time_kind'))) or
                    weather['start_utc'] != request['period_start_utc'] or
                    weather['end_utc'] != request['period_end_utc']):
                raise ValueError()
            start = datetime.fromisoformat(weather['start_utc']).astimezone(ZoneInfo('Asia/Seoul')).date()
            end = (datetime.fromisoformat(weather['end_utc'])-timedelta(microseconds=1)).astimezone(ZoneInfo('Asia/Seoul')).date()
            if not economic.period_start <= start <= end <= economic.period_end:
                raise ValueError()
            return {'research_input_sha256':root['input_sha256'], 'research_registry_sha256':self.registry.sha256,
                'point':request['point'], 'spatial_support':'pending_research',
                'period_start_utc':request['period_start_utc'], 'period_end_utc':request['period_end_utc'],
                'snapshot_id':thermal.snapshot_id, 'decision_context_id':thermal.decision_context_id,
                'thermal_scenario_sha256':selected['scenario_sha256'], 'thermal_pins':selected['pins'],
                'economic_candidate_id':candidate['candidate_id'],
                **{key:candidate[key] for key in ('economic_scenario_sha256', 'shock_sha256',
                    'rights_manifest_sha256', 'binding_manifest_sha256')},
                'baseline_sha256':candidate['request']['baseline']['sha256']}
        except PermissionError:
            raise
        except Exception:
            raise FarmReplayScenarioHold('farm scenario references unavailable') from None

    @staticmethod
    def _summary(row, body):
        return FarmReplayScenarioSummary(scenario_id=body.scenario_id, scenario_revision=body.scenario_revision,
            scenario_sha256=row['input_sha256'], registration_status='registered_intent', intent_job=public_job_status(row))

    def submit(self, tenant, body):
        pointers = self._pointers()
        guard = lambda: self._guard(tenant, pointers, WRITE_SCOPES)
        guard()
        try:
            request_raw = canonical_input_bytes(body.model_dump(mode='json'))
            if len(request_raw) > 4096:
                raise ValueError()
            body = FarmReplayScenarioRequest.model_validate_json(request_raw)
            previous = self._find(tenant, body.scenario_id, body.scenario_revision)
            if previous is not None and canonical_input_bytes(json.loads(previous['input_bytes']).get('request')) != request_raw:
                raise JobIntentConflict('conflicting immutable farm scenario')
            bindings = self._references(tenant, body)
            value = {'input_version':INPUT_VERSION, 'tenant_id':tenant, 'request':body.model_dump(mode='json'),
                     'bindings':bindings}
            def final_guard():
                guard()
                try:
                    if canonical_input_bytes(self._references(tenant, body)) != canonical_input_bytes(bindings):
                        raise FarmReplayScenarioHold('farm scenario inputs changed')
                finally:
                    guard()
            row = self.jobs.submit(tenant, 'collection', value, self._key(body.scenario_id, body.scenario_revision),
                                   commit_guard=final_guard)
            return self._summary(row, body)
        finally:
            guard()

    def _read(self, tenant, scenario_id, revision):
        if not self.jobs._has_scope(tenant, 'metadata'):
            principal = self.jobs.principal_provider()
            if principal is None or principal.get('tenant_id') != tenant:
                return None
        pointers = self._pointers()
        guard = lambda: self._guard(tenant, pointers, READ_SCOPES)
        guard()
        try:
            row = self._find(tenant, scenario_id, revision)
            if row is None:
                return None
            value = json.loads(row['input_bytes'])
            body = FarmReplayScenarioRequest.model_validate_json(canonical_input_bytes(value['request']))
            expected = {'input_version':INPUT_VERSION,'tenant_id':tenant,'request':body.model_dump(mode='json'),
                        'bindings':self._references(tenant, body)}
            if ((body.scenario_id, body.scenario_revision) != (scenario_id, revision) or
                    canonical_input_bytes(expected) != row['input_bytes']):
                raise FarmReplayScenarioHold('farm scenario stored input differs')
            return row, body, expected['bindings']
        finally:
            guard()

    def get(self, tenant, scenario_id, revision):
        record = self._read(tenant, scenario_id, revision)
        return self._summary(record[0],record[1]) if record is not None else None

    def read_selection(self, tenant, scenario_id, revision, expected_sha256):
        record = self._read(tenant,scenario_id,revision)
        if record is None or record[0]['input_sha256'] != expected_sha256:
            raise FarmReplayScenarioHold('farm scenario execution selection unavailable')
        return {'request':record[1], 'bindings':record[2], 'scenario_sha256':record[0]['input_sha256']}
