"""Current leaf inputs bound to a registered farm and a published signed stem job."""
from functools import wraps
from hashlib import sha256
import json
from pathlib import Path
from uuid import UUID

from . import crop_leaf_population_input_evidence as evidence
from . import crop_morphology_execution_query as parent_reads
from . import crop_morphology_farm_binding as farms


VERSION = 'leaf-population-farm-binding-v1'
RIGHTS_VERSION = 'leaf-population-input-rights-v1'
MAX_REQUEST_BYTES = 128*1024
MAX_BINDING_BYTES = 2*1024**2
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES = {'leaf_input':evidence,'parent_query':parent_reads,'parent_farm':farms}
DEPENDENCY_SHA256 = {k:sha256(Path(m.__file__).read_bytes()).hexdigest() for k,m in _MODULES.items()}
_DEPENDENCIES = farms.documents._canonical(DEPENDENCY_SHA256)


class LeafPopulationFarmBindingHold(ValueError):
    """Leaf inputs have no current matching registered parent result."""


def _need(condition):
    if not condition:
        raise LeafPopulationFarmBindingHold('leaf population farm binding unavailable')


def _checked(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except PermissionError:
            raise
        except Exception:
            raise LeafPopulationFarmBindingHold('leaf population farm binding unavailable') from None
    return run


class LeafPopulationFarmBinding:
    @_checked
    def __init__(self, parent_query, input_authority, *, input_rights):
        _need(type(parent_query) is parent_reads.MorphologyExecutionQuery
            and type(input_authority) is evidence.LeafPopulationInputEvidenceAuthority
            and callable(input_rights) and farms.permissions._name(input_rights.policy_version))
        self.parent_query, self.input_authority, self.input_rights = parent_query, input_authority, input_rights
        self.parent_authority = parent_query.service.authority
        self.farms = self.parent_authority.farm_binding
        self.jobs = parent_query.jobs
        self._fixed = self._pointers()
        self._binding()

    def _pointers(self):
        return (self.parent_query, self.parent_query._fixed, self.parent_authority, self.farms,
            self.farms._fixed, self.jobs, self.input_authority, self.input_rights, self.input_rights.policy_version)

    def _binding(self):
        self.parent_query._binding(); self.input_authority._binding()
        _need(self._pointers() == self._fixed and self.parent_query.service.authority is self.parent_authority
            and self.parent_authority.farm_binding is self.farms and self.farms.jobs is self.jobs
            and self.input_authority.stem_input_authority is self.farms.input_authority
            and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
            and farms.documents._canonical(DEPENDENCY_SHA256) == _DEPENDENCIES
            and {k:sha256(Path(m.__file__).read_bytes()).hexdigest() for k,m in _MODULES.items()} == DEPENDENCY_SHA256
            and MAX_REQUEST_BYTES == 128*1024 and MAX_BINDING_BYTES == 2*1024**2)

    def _guard(self, tenant, write):
        self._binding(); self.farms._guard(tenant, write); self.parent_query._guard(tenant); self._binding()

    @_checked
    def _request(self, raw):
        request = farms.documents._document(raw, max_size=MAX_REQUEST_BYTES)
        _need(set(request) == {'study_id','revision','farm','input','rights','parent'}
            and farms.permissions._name(request['study_id']) and farms.permissions._name(request['revision']))
        farm, source, rights, parent = (request[k] for k in ('farm','input','rights','parent'))
        _need(type(farm) is dict and set(farm) == {'scenario_id','scenario_revision','registration_sha256','crop_id'}
            and all(farms.permissions._name(farm[k]) for k in ('scenario_id','scenario_revision','crop_id')))
        evidence.reader._hash(farm['registration_sha256'])
        hashes = ('program_sha256','source_sha256','evidence_sha256')
        _need(type(source) is dict and set(source) == {'schema_version','program_id',*hashes}
            and source['schema_version'] == evidence.SOURCE_VERSION and farms.permissions._name(source['program_id']))
        for key in hashes: evidence.reader._hash(source[key])
        grants = ('ownership_asserted','access','store','transform','use','display')
        _need(type(rights) is dict and set(rights) == {'schema_version','declaration_id','revision',
            'input_source_sha256','available_at','redistribute',*grants}
            and rights['schema_version'] == RIGHTS_VERSION and farms.permissions._name(rights['declaration_id'])
            and farms.permissions._name(rights['revision']) and all(rights[k] is True for k in grants)
            and rights['redistribute'] is False and rights['input_source_sha256'] == source['source_sha256'])
        farms.documents._time(rights['available_at'])
        _need(type(parent) is dict and set(parent) == {'job_id','result_sha256','numerical_root_sha256'}
            and type(parent['job_id']) is str and str(UUID(parent['job_id'])) == parent['job_id'])
        evidence.reader._hash(parent['result_sha256']); evidence.reader._hash(parent['numerical_root_sha256'])
        return request

    def _parent(self, tenant, request, write):
        reference = request['parent']
        current = self.parent_query.read(tenant, reference['job_id'], view='manifest')
        proof = current['manifest']
        _need(current['job']['state'] == 'succeeded' and current['cancel_requested'] is False and type(proof) is dict
            and proof['result_sha256'] == reference['result_sha256']
            and proof['numerical_root_sha256'] == reference['numerical_root_sha256']
            and proof['farm'] == request['farm'])
        payload, binding_raw, binding, packet = self.parent_authority._load(tenant, reference['result_sha256'])
        _need(payload['numerical_root_sha256'] == proof['numerical_root_sha256']
            and payload['program_sha256'] == proof['program_sha256']
            and payload['source_sha256'] == proof['source_sha256']
            and payload['input_evidence_sha256'] == proof['input_evidence_sha256']
            and payload['binding_sha256'] == proof['binding_sha256']
            and payload['calculated_at'] == proof['calculated_at'] and binding['request']['farm'] == request['farm'])
        _need(self.farms.current(tenant, farms.documents._canonical(binding['request']), binding_raw,
            **packet, write=write) == binding_raw)
        summary = {'job_id':reference['job_id'],
            'job_sha256':sha256(farms.documents._canonical(current['job'])).hexdigest(),
            **{k:proof[k] for k in ('result_sha256','numerical_root_sha256','calculated_at','binding_sha256',
                'program_sha256','source_sha256','input_evidence_sha256')},
            'manifest_sha256':sha256(farms.documents._canonical(proof['manifest'])).hexdigest()}
        return {'summary':summary,'proof':proof,'binding_raw':binding_raw,'binding':binding,'packet':packet}

    @_checked
    def _input(self, request, parent, packet):
        reference, proof = request['input'], parent['proof']
        raw = packet['evidence_raw']
        _need(type(raw) is bytes and 0 < len(raw) <= evidence.EVIDENCE_MAX
            and sha256(raw).hexdigest() == reference['evidence_sha256'])
        parent_packet = parent['packet']
        _need(sha256(parent_packet['evidence_raw']).hexdigest() == proof['input_evidence_sha256'])
        parent_evidence = evidence.reader._parse(parent_packet['evidence_raw'], evidence.stem.EVIDENCE_MAX)['payload']
        decision = farms.documents._time(parent['binding']['registration']['decision_at'])
        arguments = {**parent_packet,'expected_program_sha256':proof['program_sha256'],
            'expected_source_sha256':proof['source_sha256'],
            'review_id':parent_evidence['review']['evidence_id'],'decision_at':decision}
        envelope = evidence.reader._parse(raw, evidence.EVIDENCE_MAX)['payload']
        checked = self.input_authority.verify(**packet, expected_program_sha256=reference['program_sha256'],
            expected_source_sha256=reference['source_sha256'],review_id=envelope['review']['evidence_id'],
            decision_at=decision,stem_arguments=arguments)
        _need(type(checked) is evidence.VerifiedLeafPopulationInputEvidence and checked.rights_or_gate_approval is False)
        metadata = checked.metadata
        _need(metadata['program_id'] == reference['program_id']
            and metadata['stem_artifact_sha256'] == proof['numerical_root_sha256']
            and metadata['parent_stem_program_sha256'] == proof['program_sha256']
            and metadata['parent_stem_source_sha256'] == proof['source_sha256']
            and metadata['parent_stem_evidence_sha256'] == proof['input_evidence_sha256'])
        source = parent['binding']['input']
        return {**metadata,'program_sha256':checked.program_sha256,'source_sha256':checked.source_sha256,
            'evidence_sha256':checked.evidence_sha256,'period':source['period'],'time_origin_utc':source['time_origin_utc'],
            'shoot_id':source['shoot_id'],'review':envelope['review'],'model_versions':envelope['model_versions'],
            'code_sha256':envelope['code_sha256'],'input_evidence_version':evidence.VERSION,'qc_version':evidence.QC_VERSION,
            'normalization':'per_tracked_shoot','numerical_initial_state_validation':False}

    @_checked
    def _scope(self, request, registration, source):
        at = farms.documents._time(registration['decision_at'])
        start, end = (farms.documents._time(source['period'][k]) for k in ('start','end'))
        crop, calendar = registration['crop']['occupancy'], registration['calendar_utc']
        _need(farms.documents._time(request['rights']['available_at']) <= at
            and farms.documents._time(source['source_record']['available_at']) <= at
            and farms.documents._time(crop['start']) <= start < end <= farms.documents._time(crop['end'])
            and farms.documents._time(calendar['start']) <= start < end <= farms.documents._time(calendar['end']))

    def _rights(self, tenant, request, source, write):
        for use in (('research_calculation','research_display') if write else ('research_display',)):
            declaration = json.loads(farms.documents._canonical(request['rights']))
            _need(self.input_rights(tenant, declaration, source['source_sha256'], use) is True
                and farms.documents._canonical(declaration) == farms.documents._canonical(request['rights']))

    def _bind(self, tenant, request_raw, packet, write):
        _need(type(write) is bool); self._guard(tenant, write)
        request = self._request(request_raw)
        parent = self._parent(tenant, request, write)
        source = self._input(request, parent, packet)
        self._scope(request, parent['binding']['registration'], source); self._rights(tenant, request, source, write)
        self._guard(tenant, write)
        after = self._parent(tenant, request, write)
        _need(after == parent and self._input(request, after, packet) == source)
        self._rights(tenant, request, source, write); self._guard(tenant, write)
        raw = farms.documents._canonical({'version':VERSION,'scope':'synthetic_leaf_population_input_binding_only',
            'G0_G4':'not_assessed','rights_or_gate_approval':False,'numerical_initial_state_validation':False,
            'tenant_id':tenant,'request':request,'registration':parent['binding']['registration'],
            'parent':parent['summary'],'parent_result_binding_verified':True,'input':source,
            'rights_policy_version':self.input_rights.policy_version,'binding_code_sha256':CODE_SHA256,
            'binding_dependency_sha256':DEPENDENCY_SHA256})
        _need(len(raw) <= MAX_BINDING_BYTES)
        return raw

    @_checked
    def prepare(self, tenant, request_raw, *, program_raw, source_raw, evidence_raw):
        return self._bind(tenant, request_raw, dict(program_raw=program_raw,source_raw=source_raw,evidence_raw=evidence_raw), True)

    @_checked
    def current(self, tenant, request_raw, expected_binding_raw, *, program_raw, source_raw, evidence_raw, write=False):
        _need(type(expected_binding_raw) is bytes and 0 < len(expected_binding_raw) <= MAX_BINDING_BYTES)
        raw = self._bind(tenant, request_raw, dict(program_raw=program_raw,source_raw=source_raw,evidence_raw=evidence_raw), write)
        _need(raw == expected_binding_raw)
        return raw
