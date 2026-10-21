"""Closed public prefix projection; the current reader authorizes access."""
from datetime import datetime
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, RootModel, model_validator

from . import api_crop_greenhouse_co2_replay as public
from . import api_crop_greenhouse_co2_execution as execution
from . import crop_greenhouse_co2_prefix as current

VERSION = 'joint-co2-solar-prefix-replay-v1'
MAX_RESPONSE_BYTES = 2*1024**2
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES = {'reader': current, 'replay': public, 'execution': execution}
_DEPENDENCIES = {k: sha256(Path(v.__file__).read_bytes()).hexdigest() for k, v in _MODULES.items()}
_FIXED = (VERSION, MAX_RESPONSE_BYTES, CODE_SHA256, public.storage._canonical(_DEPENDENCIES))
Index = public.Index
SampleCount = Annotated[int, Field(strict=True, ge=0, le=512)]
EventCount = Annotated[int, Field(strict=True, ge=0, le=128)]


class ProjectionHold(ValueError):
    pass


def _need(value):
    if not value:
        raise ProjectionHold('co2 prefix display unavailable')


def _guard():
    public.storage._pins()
    _need((VERSION, MAX_RESPONSE_BYTES, CODE_SHA256, public.storage._canonical(_DEPENDENCIES)) == _FIXED
        and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
        and {k: sha256(Path(v.__file__).read_bytes()).hexdigest() for k, v in _MODULES.items()} == _DEPENDENCIES
        and MAX_RESPONSE_BYTES == current.storage.LIMITS['page_bytes'])


class Selector(public._Public):
    publication_sequence: Annotated[int, Field(strict=True, ge=1, le=current.checkpoints.MAX_EVENTS)]
    head_sha256: public.Digest
    proof_sha256: public.Digest


class Counts(public._Public):
    samples: SampleCount
    events: EventCount


class PrefixSummary(public._Public):
    counts: Counts
    last_sample_utc: public.UtcStamp | None
    last_event_utc: public.UtcStamp | None


class PrefixSamplePage(public._Public):
    kind: Literal['samples']
    start: Index
    limit: Annotated[int, Field(strict=True, ge=1, le=64)]
    total: SampleCount
    next_offset: Index | None
    records: Annotated[list[public.Co2Sample], Field(max_length=64)]


class PrefixEventPage(public._Public):
    kind: Literal['events']
    start: Index
    limit: Annotated[int, Field(strict=True, ge=1, le=8)]
    total: EventCount
    next_offset: Index | None
    records: Annotated[list[public.Co2Event], Field(max_length=8)]


class PrefixReference(public._Public):
    selector: Selector
    checkpoint: execution.Co2ExecutionCheckpoint
    checkpoint_attempt: Annotated[int, Field(strict=True, ge=1, le=3)]
    study_id: public.Name
    revision: public.Name
    farm: public.Farm
    input: public.Input
    manifest: public.Co2Manifest
    time_grid: public.Co2TimeGrid
    rights_or_gate_approval: public.FalseApproval
    normalization: Literal['per_m2_floor']
    profile_applicability: Literal['unvalidated_for_registered_crop']
    normalization_version: Literal['joint-current-co2-solar-float64-series-provenance-v1']
    qc_version: Literal['joint-initial-co2-solar-packet-schema-utc-v1']
    input_evidence_version: Literal['joint-co2-solar-input-evidence-v1']

    @model_validator(mode='after')
    def consistent_reference(self):
        cp = self.checkpoint; grid = self.time_grid.model_dump(mode='json')
        manifest = self.manifest.model_dump(mode='json'); identity = manifest['identity']; n = manifest['numerical']
        dt = float(grid['step_seconds_decimal'])
        _need(all(getattr(self.selector, k) == getattr(cp, k) for k in Selector.model_fields)
            and cp.steps <= cp.planned_steps == grid['step_count'] == n['step_count'] <= 4096
            and cp.counts.samples <= 512 and cp.counts.events <= 128
            and (cp.artifact_sha256 is not None) == (cp.status in ('completed', 'hold'))
            and (cp.computed_through_utc is None) == (cp.status == 'ready')
            and (cp.status != 'completed' or cp.steps == cp.planned_steps)
            and (cp.status != 'ready' or cp.steps == cp.counts.samples == cp.counts.events == 0)
            and public.continuation._hash(manifest) == self.input.context_sha256
            and n['step_seconds'] == dt and n['duration_seconds'] == dt*n['step_count']
            and 0 < n['duration_seconds'] <= 600
            and grid['step_microseconds'] == Fraction(grid['step_seconds_decimal'])*1000000
            and grid['time_code_sha256'] == public.server.clock.CODE_SHA256
            and grid['start_utc'] == self.input.start_utc
            and grid['end_utc'] == self.input.end_utc == public.server.clock._at(grid, grid['step_count']))
        _need(cp.computed_through_utc is None or cp.computed_through_utc == public.server.clock._at(grid, cp.steps))
        _need(public._current_identity(identity))
        _need(cp.provenance_sha256 == self.input.provenance_sha256)
        return self


class _Envelope(public._Public):
    schema_version: Literal['joint-co2-solar-prefix-replay-v1']
    scope: Literal['synthetic_joint_co2_solar_math_only']
    claim_scope: Literal['synthetic_joint_co2_solar_confirmed_prefix_only']
    G0_G4: Literal['not_assessed']
    rights_or_gate_approval: public.FalseApproval
    job: execution.jobs_public.JobStatus
    cancel_requested: Annotated[bool, Field(strict=True)]
    observed_at: public.UtcStamp

    @model_validator(mode='after')
    def simulation_job(self):
        _need(self.job.stage == 'simulation' and self.job.attempt_count <= self.job.max_attempts
            and self.job.created_at.utcoffset() is not None and self.job.updated_at.utcoffset() is not None
            and self.job.created_at <= self.job.updated_at <= datetime.fromisoformat(self.observed_at.replace('Z', '+00:00')))
        return self


class NoPrefix(_Envelope):
    prefix_status: Literal['none', 'closed']
    reference: None
    summary: None
    page: None

    @model_validator(mode='after')
    def consistent_absence(self):
        _need((self.prefix_status == 'closed') == (self.cancel_requested or self.job.state not in ('queued', 'simulating')))
        return self


class AcceptedPrefix(_Envelope):
    prefix_status: Literal['accepted']
    reference: PrefixReference
    summary: PrefixSummary | None
    page: Annotated[PrefixSamplePage | PrefixEventPage, Field(discriminator='kind')] | None

    @model_validator(mode='after')
    def consistent_prefix(self):
        ref = self.reference; cp = ref.checkpoint
        _need(not self.cancel_requested and self.job.state in ('queued', 'simulating')
            and ref.checkpoint_attempt <= self.job.attempt_count
            and self.job.created_at <= datetime.fromisoformat(cp.checkpoint_recorded_at.replace('Z', '+00:00'))
                <= datetime.fromisoformat(self.observed_at.replace('Z', '+00:00'))
            and (self.summary is None) != (self.page is None))
        grid = ref.time_grid.model_dump(mode='json'); dt = ref.manifest.numerical.step_seconds
        if self.summary is not None:
            s = self.summary
            _need(s.counts.model_dump() == cp.counts.model_dump())
            for kind, at in (('samples', s.last_sample_utc), ('events', s.last_event_utc)):
                _need((at is None) == (getattr(s.counts, kind) == 0))
                if at is not None:
                    delta = datetime.fromisoformat(at.replace('Z', '+00:00')) - datetime.fromisoformat(grid['start_utc'].replace('Z', '+00:00'))
                    micros = (delta.days*86400 + delta.seconds)*1000000 + delta.microseconds
                    _need(micros >= 0 and micros % grid['step_microseconds'] == 0
                        and micros // grid['step_microseconds'] <= cp.steps
                        and at == public.server.clock._at(grid, micros // grid['step_microseconds']))
        if self.page is not None:
            p = self.page; end = p.start + len(p.records)
            _need(p.total == getattr(cp.counts, p.kind) and p.start <= p.total
                and len(p.records) == min(p.limit, p.total-p.start)
                and p.next_offset == (end if end < p.total else None))
            previous = -1
            for row in p.records:
                public._point(row.time.model_dump(mode='json'), row.value.model_dump(mode='json'), grid, dt)
                _need(previous < row.value.step_index <= cp.steps); previous = row.value.step_index
        return self


class PrefixReplay(RootModel[Annotated[AcceptedPrefix | NoPrefix, Field(discriminator='prefix_status')]]):
    pass


def _parsed(cls, value):
    parsed = cls.model_validate(value)
    _need(public.storage._canonical(parsed.model_dump(mode='json')) == public.storage._canonical(value))
    return parsed


def _public_bytes(projected):
    try:
        _guard(); _need(type(projected) is PrefixReplay)
        checked = _parsed(PrefixReplay, projected.model_dump(mode='json'))
        raw = checked.model_dump_json().encode()
        _need(1 <= len(raw) <= MAX_RESPONSE_BYTES)
        return raw
    except Exception:
        raise ProjectionHold('co2 prefix display unavailable') from None


def project_prefix(record, *, source_program):
    try:
        _guard()
        _need(type(record) is current.PrefixRead and type(record.payload_raw) is bytes
            and 1 <= len(record.payload_raw) <= current.MAX_READ_BYTES
            and sha256(record.payload_raw).hexdigest() == record.payload_sha256)
        value = json.loads(record.payload_raw)
        _need(type(value) is dict and set(value) == {'version', 'scope', 'claim_scope', 'G0_G4', 'job',
            'rights_or_gate_approval', 'cancel_requested', 'observed_at', 'prefix_status', 'selection', 'binding', 'manifest', 'time_binding', 'summary', 'page'}
            and record.payload_raw == current.storage._canonical(value) and value['version'] == current.VERSION)
        result = {k: value[k] for k in _Envelope.model_fields if k != 'schema_version'}
        result['schema_version'] = VERSION
        result.update(prefix_status=value['prefix_status'], reference=None, summary=value['summary'], page=value['page'])
        if value['prefix_status'] != 'accepted':
            _need(all(value[k] is None for k in ('selection', 'binding', 'manifest', 'time_binding', 'summary', 'page')))
            _need(source_program is None)
        else:
            bases = public._basis_map(source_program, value['manifest'])
            selection = value['selection']
            _need(type(selection) is dict and set(selection) == {'checkpoint', 'checkpoint_recorded_at', 'checkpoint_attempt'})
            cp = current.checkpoints._payload(selection['checkpoint'])
            binding = value['binding']; source = binding['input']; request = binding['request']; registration = binding['registration']
            _need(binding['rights_or_gate_approval'] is False and value['rights_or_gate_approval'] is False
                and cp['provenance_sha256'] == source['provenance_sha256']
                and sha256(public.storage._canonical(binding)).hexdigest() == cp['farm_binding_sha256']
                and all(cp[k] == source[k] for k in ('source_sha256', 'context_sha256', 'time_binding_sha256'))
                and value['manifest']['identity'] == source['model_identity']
                and public.continuation._hash(value['time_binding']) == source['time_binding_sha256']
                and value['time_binding']['context_sha256'] == source['context_sha256'])
            farm = {**{k: request['farm'][k] for k in ('scenario_id', 'scenario_revision')},
                **{k: registration[k] for k in ('registration_sha256', 'zone_id')},
                **{k: registration['crop'][k] for k in ('crop_id', 'batch_id')}}
            checkpoint = {k: cp[k] for k in execution.Co2ExecutionCheckpoint.model_fields if k != 'checkpoint_recorded_at'}
            checkpoint['checkpoint_recorded_at'] = selection['checkpoint_recorded_at']
            result['reference'] = {'selector': {k: cp[k] for k in Selector.model_fields}, 'checkpoint': checkpoint,
                'checkpoint_attempt': selection['checkpoint_attempt'], **{k: request[k] for k in ('study_id', 'revision')},
                'farm': farm, 'input': {**{k: source[k] for k in public.Input.model_fields if k not in ('start_utc', 'end_utc')},
                    'start_utc': source['period']['start'], 'end_utc': source['period']['end']},
                'rights_or_gate_approval': False,
                **{k: registration[k] for k in ('normalization', 'profile_applicability')},
                **{k: source[k] for k in ('normalization_version', 'qc_version', 'input_evidence_version')},
                'manifest': value['manifest'], 'time_grid': {k: value['time_binding'][k] for k in public.Co2TimeGrid.model_fields}}
            if value['page'] is not None:
                _need(all(type(row) is dict and set(row) == {'value', 'time'} for row in value['page']['records']))
                rows = ([{**row, 'co2_basis': public._basis(row['value'], bases)} for row in value['page']['records']]
                    if value['page']['kind'] == 'samples' else
                    [public._event(row, value['manifest']['identity'], bases) for row in value['page']['records']])
                result['page'] = {**value['page'], 'records': rows}
        projected = _parsed(PrefixReplay, result)
        _public_bytes(projected)
        return projected
    except Exception:
        raise ProjectionHold('co2 prefix display unavailable') from None


def read_prefix(query, tenant, job_id, *, selector=None, view='summary', start=0, limit=None):
    """Serialize an authorized original record and recheck its current witness."""
    try:
        _guard()
        _need(type(query) is current.Co2ExecutionPrefixQuery)
        query._binding()
        record = query.read(tenant, job_id, selector=selector, view=view, start=start, limit=limit)
        if record is None:
            query._guard(tenant)
            return None
        source_program = query._source_program(tenant, job_id, record)
        raw = _public_bytes(project_prefix(record, source_program=source_program))
        query._after_projection(tenant, job_id, record)
        _guard()
        return raw
    except (PermissionError, current.execution.RolePolicyHold, current.Co2PrefixPending,
            current.Co2PrefixSelectionConflict, current.Co2PrefixRequestRejected):
        raise
    except Exception:
        raise ProjectionHold('co2 prefix display unavailable') from None
