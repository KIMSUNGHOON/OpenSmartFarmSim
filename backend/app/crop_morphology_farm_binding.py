"""Current registered-farm rights for original synthetic morphology inputs."""
from datetime import datetime, time, timedelta, timezone
from functools import wraps
from hashlib import sha256
import json
from pathlib import Path

from . import crop_morphology_input_evidence as evidence
from . import farm_authoring_storage as authored
from . import crop_result_store as permissions
from . import farm_inputs, jobs, runtime_roles, thermal_run_store as documents
from . import farm_input_compiler, farm_replay_scenario, farm_registration_read_scope, runtime_connection_scope
from . import market_candidate_store, market_reference_bundle


VERSION = 'morphology-farm-binding-v1'
RIGHTS_VERSION = 'morphology-input-rights-v1'
MAX_REQUEST_BYTES = 128*1024
MAX_BINDING_BYTES = 2*1024**2
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES = {'input_evidence': evidence, 'farm_authority': authored, 'permissions': permissions,
    'farm_inputs': farm_inputs, 'jobs': jobs, 'runtime_roles': runtime_roles, 'documents': documents,
    'farm_compiler': farm_input_compiler, 'farm_replay': farm_replay_scenario,
    'registration_scope': farm_registration_read_scope, 'connection_scope': runtime_connection_scope,
    'market_candidate': market_candidate_store, 'market_references': market_reference_bundle}
DEPENDENCY_SHA256 = {k: sha256(Path(m.__file__).read_bytes()).hexdigest() for k, m in _MODULES.items()}
_DEPENDENCIES = documents._canonical(DEPENDENCY_SHA256)


class MorphologyFarmBindingHold(ValueError):
    """Original morphology inputs have no current registered-farm binding."""


def _need(condition):
    if not condition:
        raise MorphologyFarmBindingHold('morphology farm binding unavailable')


def _checked(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except PermissionError:
            raise
        except Exception:
            raise MorphologyFarmBindingHold('morphology farm binding unavailable') from None
    return run


class MorphologyFarmBinding:
    @_checked
    def __init__(self, farms, input_authority, *, input_rights):
        _need(type(farms) is authored.FarmAuthoringService
            and type(input_authority) is evidence.MorphologyInputEvidenceAuthority
            and callable(input_rights) and permissions._name(input_rights.policy_version))
        self.farms, self.input_authority, self.input_rights = farms, input_authority, input_rights
        self.jobs = farms.replay.jobs
        self._fixed = self._pointers()
        self._binding()

    def _pointers(self):
        return (self.farms, self.farms._pointers(), self.jobs, self.input_authority, self.input_rights,
            self.input_rights.policy_version, self.jobs._dsn, self.jobs.schema,
            self.jobs.runtime_identity, self.jobs.audit_runtime_grants)

    def _binding(self):
        self.farms._binding(); self.input_authority._binding()
        policy, kind = self.jobs.runtime_identity
        _need(self._pointers() == self._fixed and self.farms.replay.jobs is self.jobs
            and type(policy) is runtime_roles.RuntimeLoginPolicy and kind == 'authority'
            and policy.crop_cycle_result_storage is True and self.jobs.audit_runtime_grants is True
            and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
            and documents._canonical(DEPENDENCY_SHA256) == _DEPENDENCIES
            and {k: sha256(Path(m.__file__).read_bytes()).hexdigest() for k, m in _MODULES.items()} == DEPENDENCY_SHA256
            and MAX_REQUEST_BYTES == 128*1024 and MAX_BINDING_BYTES == 2*1024**2)

    def _guard(self, tenant, write):
        self._binding()
        self.farms._guard(tenant, self._fixed[1], permissions.WRITE_SCOPES if write else permissions.READ_SCOPES)

    @_checked
    def _request(self, raw):
        request = documents._document(raw, max_size=MAX_REQUEST_BYTES)
        _need(set(request) == {'study_id', 'revision', 'farm', 'input', 'rights'}
            and permissions._name(request['study_id']) and permissions._name(request['revision']))
        farm, source, rights = request['farm'], request['input'], request['rights']
        _need(type(farm) is dict and set(farm) == {'scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id'}
            and all(permissions._name(farm[k]) for k in ('scenario_id', 'scenario_revision', 'crop_id')))
        evidence.reader._hash(farm['registration_sha256'])
        hashes = ('program_sha256', 'source_sha256', 'evidence_sha256')
        _need(type(source) is dict and set(source) == {'schema_version', 'program_id', *hashes}
            and source['schema_version'] == evidence.SOURCE_VERSION and permissions._name(source['program_id']))
        for key in hashes:
            evidence.reader._hash(source[key])
        grants = ('ownership_asserted', 'access', 'store', 'transform', 'use', 'display')
        _need(type(rights) is dict and set(rights) == {'schema_version', 'declaration_id', 'revision',
            'input_source_sha256', 'available_at', 'redistribute', *grants}
            and rights['schema_version'] == RIGHTS_VERSION and permissions._name(rights['declaration_id'])
            and permissions._name(rights['revision']) and all(rights[k] is True for k in grants)
            and rights['redistribute'] is False and rights['input_source_sha256'] == source['source_sha256'])
        documents._time(rights['available_at'])
        return request

    def _registration(self, tenant, request):
        ref = request['farm']
        record = self.farms.read_registration(tenant, ref['scenario_id'], ref['scenario_revision'], ref['registration_sha256'])
        farm = record['farm']; crop = next((c for c in farm.crops if c.crop_id == ref['crop_id']), None)
        row = self.farms._find(tenant, ref['scenario_id'], ref['scenario_revision'])
        _need(crop is not None and row is not None and row['input_sha256'] == ref['registration_sha256'])
        start = datetime.combine(farm.period_start, time(), farm_inputs.KST)
        end = datetime.combine(farm.period_end+timedelta(days=1), time(), farm_inputs.KST)
        return {'registration_job_id': str(row['job_id']), 'registration_sha256': ref['registration_sha256'],
            'farm_sha256': sha256(farm_inputs.canonical_farm_inputs(farm)).hexdigest(),
            'source_binding_sha256': sha256(jobs.canonical_input_bytes(record['binding'])).hexdigest(),
            'decision_at': farm.decision_at.isoformat().replace('+00:00', 'Z'), 'crop': crop.model_dump(mode='json'),
            'calendar_utc': {k: v.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z') for k, v in [('start', start), ('end', end)]},
            'zone_id': farm.facility.zone_id, 'floor_area': farm.facility.floor_area.model_dump(mode='json'),
            'normalization': 'per_tracked_shoot', 'profile_applicability': 'unvalidated_for_registered_crop'}

    @_checked
    def _input(self, request, registration, *, program_raw, source_raw, evidence_raw):
        source = request['input']
        _need(type(evidence_raw) is bytes and 0 < len(evidence_raw) <= evidence.EVIDENCE_MAX
            and sha256(evidence_raw).hexdigest() == source['evidence_sha256'])
        checked = self.input_authority.verify(program_raw=program_raw, source_raw=source_raw, evidence_raw=evidence_raw,
            expected_program_sha256=source['program_sha256'], expected_source_sha256=source['source_sha256'],
            review_id=evidence.reader._parse(evidence_raw, evidence.EVIDENCE_MAX)['payload']['review']['evidence_id'],
            decision_at=documents._time(registration['decision_at']))
        _need(type(checked) is evidence.VerifiedMorphologyInputEvidence and checked.rights_or_gate_approval is False)
        metadata = checked.metadata
        _need(metadata['program_id'] == source['program_id'])
        program = evidence.reader._parse(program_raw, evidence.reader.PROGRAM_MAX)
        timeline = program['initial_state']['timeline_state']
        proof = evidence.reader._parse(evidence_raw, evidence.EVIDENCE_MAX)['payload']
        return {**metadata, 'program_sha256': checked.program_sha256, 'source_sha256': checked.source_sha256,
            'evidence_sha256': checked.evidence_sha256, 'period': {'start': timeline['at'], 'end': program['output_times'][-1]},
            'time_origin_utc': timeline['started_at'], 'shoot_id': timeline['shoot_id'], 'review': proof['review'],
            'model_versions': proof['model_versions'], 'code_sha256': proof['code_sha256'],
            'input_evidence_version': evidence.VERSION, 'qc_version': evidence.QC_VERSION,
            'normalization': 'per_tracked_shoot', 'numerical_initial_state_validation': False}

    @_checked
    def _scope(self, request, registration, source):
        at = documents._time(registration['decision_at'])
        start, end = (documents._time(source['period'][k]) for k in ('start', 'end'))
        crop = registration['crop']['occupancy']; calendar = registration['calendar_utc']
        _need(documents._time(request['rights']['available_at']) <= at
            and documents._time(source['source_record']['available_at']) <= at
            and documents._time(crop['start']) <= start < end <= documents._time(crop['end'])
            and documents._time(calendar['start']) <= start < end <= documents._time(calendar['end']))

    def _rights(self, tenant, request, source, write):
        for use in (('research_calculation', 'research_display') if write else ('research_display',)):
            declaration = json.loads(documents._canonical(request['rights']))
            _need(self.input_rights(tenant, declaration, source['source_sha256'], use) is True
                and documents._canonical(declaration) == documents._canonical(request['rights']))

    def _bind(self, tenant, request_raw, packet, write):
        _need(type(write) is bool); self._guard(tenant, write)
        request = self._request(request_raw)
        registration = self._registration(tenant, request)
        source = self._input(request, registration, **packet)
        self._scope(request, registration, source); self._rights(tenant, request, source, write)
        self._guard(tenant, write)
        _need(self._registration(tenant, request) == registration and self._input(request, registration, **packet) == source)
        self._guard(tenant, write); self._rights(tenant, request, source, write)
        self._guard(tenant, write)
        raw = documents._canonical({'version': VERSION, 'scope': 'synthetic_morphology_input_binding_only',
            'G0_G4': 'not_assessed', 'rights_or_gate_approval': False, 'numerical_initial_state_validation': False,
            'tenant_id': tenant, 'request': request, 'registration': registration, 'input': source,
            'rights_policy_version': self.input_rights.policy_version, 'binding_code_sha256': CODE_SHA256,
            'binding_dependency_sha256': DEPENDENCY_SHA256})
        _need(len(raw) <= MAX_BINDING_BYTES)
        return raw

    @_checked
    def prepare(self, tenant, request_raw, *, program_raw, source_raw, evidence_raw):
        return self._bind(tenant, request_raw, dict(program_raw=program_raw, source_raw=source_raw, evidence_raw=evidence_raw), True)

    @_checked
    def current(self, tenant, request_raw, expected_binding_raw, *, program_raw, source_raw, evidence_raw, write=False):
        _need(type(expected_binding_raw) is bytes and 0 < len(expected_binding_raw) <= MAX_BINDING_BYTES)
        result = self._bind(tenant, request_raw, dict(program_raw=program_raw, source_raw=source_raw, evidence_raw=evidence_raw), write)
        _need(result == expected_binding_raw)
        return result
