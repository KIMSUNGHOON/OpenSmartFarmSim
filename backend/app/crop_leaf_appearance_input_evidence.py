"""Current structural evidence for an original appearance policy and stem input."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from hashlib import sha256
import hmac
import json
from pathlib import Path

from . import crop_leaf_appearance_artifact_reader as reader
from . import crop_leaf_appearance_program as program
from . import crop_morphology_input_evidence as stem
from . import provenance


VERSION = 'leaf-appearance-input-evidence-v1'
SOURCE_VERSION = 'leaf-appearance-input-source-v1'
SCOPE = 'synthetic_leaf_appearance_input_structure_only'
QC_VERSION = 'leaf-appearance-program-structure-provenance-v1'
DOMAIN = b'ossf-leaf-appearance-input-evidence-v1\0'
SOURCE_MAX = 1024**2
EVIDENCE_MAX = 2*1024**2
_ROOT = Path(__file__).resolve().parents[2]
_PATHS = (*reader.SOURCE_PATHS, 'backend/app/crop_leaf_appearance_artifact_reader.py',
    'backend/app/provenance.py', 'backend/app/crop_morphology_input_evidence.py',
    'backend/app/crop_leaf_appearance_input_evidence.py')
_MODELS = dict(reader.ROOT_CONSTANTS['model_versions'])
_PROGRAM_VERSION = program.VERSION
_DISPLAY_POLICY = dict(program.DISPLAY_POLICY)
_TOKEN = object()


class LeafAppearanceInputEvidenceHold(ValueError):
    """Original policy and parent input have no current structural evidence."""


def _need(condition):
    if not condition:
        raise LeafAppearanceInputEvidenceHold('leaf appearance input evidence unavailable')


def _pins():
    return {name:sha256((_ROOT/name).read_bytes()).hexdigest() for name in _PATHS}


_PINNED = _pins()


def _checked(fn):
    @wraps(fn)
    def run(self, *args, **kwargs):
        try:
            self._binding()
            result = fn(self, *args, **kwargs)
            self._binding()
            return result
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
            raise LeafAppearanceInputEvidenceHold('leaf appearance input evidence unavailable') from None
    return run


def _variables(value, path=''):
    if type(value) is dict and 'unit' in value:
        return {path:{'name':path, 'original_unit':value['unit'], 'time_semantics':'instant',
            'interval_start':None, 'interval_end':None, 'provider_qc_status':'not_supplied', 'provider_qc_value':None}}
    result = {}
    if type(value) is dict:
        for key, child in value.items():
            result.update(_variables(child, f'{path}.{key}' if path else key))
    elif type(value) is list:
        for index, child in enumerate(value):result.update(_variables(child, f'{path}.{index}'))
    if path == 'policy':
        for key in ('first_generative_sequence', 'vegetative_between_generative'):
            name = f'{path}.{key}'
            result[name] = {'name':name, 'original_unit':'1', 'time_semantics':'instant',
                'interval_start':None, 'interval_end':None, 'provider_qc_status':'not_supplied', 'provider_qc_value':None}
    return result


def _record(p, raw, source, review, decision_at):
    record = provenance.SourceRecord.model_validate_json(reader._canonical(source['provenance']))
    value = record.model_dump(mode='json')
    _need(reader._canonical(value) == reader._canonical(source['provenance'])
        and record.synthetic is True and record.synthetic_author is not None and record.synthetic_method is not None
        and record.scope.station_or_grid_id is None and not record.request_details
        and record.valid_from is None and record.valid_to is None
        and record.scope.product_id == p['program_id'] and record.scope.product_version == p['schema_version']
        and record.revision_id == p['rights']['revision'] and record.raw_sha256 == sha256(raw).hexdigest()
        and record.source_reviewer == review['reviewer_id'] and record.source_evidence_id == review['evidence_id'])
    times = (record.observed_at, record.published_at, record.available_at, record.retrieved_at)
    _need(all(t is not None and t <= decision_at for t in times)
        and reader._utc(p['rights']['declared_at_utc']) <= record.observed_at
        <= record.published_at <= record.available_at <= record.retrieved_at <= decision_at)
    expected = _variables(p)
    _need(len(value['variables']) == len(expected) and {v['name']:v for v in value['variables']} == expected
        and len(record.project_checks) == len(expected) and {c.variable for c in record.project_checks} == set(expected)
        and all(c.name == 'structural_software_contract' and c.version == QC_VERSION and c.status == 'passed'
            and c.evidence_id == review['evidence_id'] and c.reviewer == review['reviewer_id'] for c in record.project_checks)
        and len(record.rights) == 5 and {r.action for r in record.rights} == {'access','store','transform','display','redistribute'}
        and all(r.status == ('denied' if r.action == 'redistribute' and not p['rights']['redistribute'] else 'allowed')
            and r.evidence_id == review['evidence_id'] and r.reviewer == review['reviewer_id'] for r in record.rights))
    return value, len(expected)


@dataclass(frozen=True)
class VerifiedLeafAppearanceInputEvidence:
    _metadata_raw: bytes = field(repr=False)
    program_sha256: str
    source_sha256: str
    evidence_sha256: str
    _token: object = field(repr=False)

    @property
    def metadata(self):
        _need(self._token is _TOKEN)
        return json.loads(self._metadata_raw)

    @property
    def rights_or_gate_approval(self):
        _need(self._token is _TOKEN)
        return False


class LeafAppearanceInputEvidenceAuthority:
    def __init__(self, *, integrity_key, issuer_id, key_id, review_resolver, stem_input_authority):
        _need(type(integrity_key) is bytes and 32 <= len(integrity_key) <= 4096
            and stem._identifier(issuer_id) and stem._identifier(key_id) and callable(review_resolver)
            and type(stem_input_authority) is stem.MorphologyInputEvidenceAuthority)
        self.integrity_key, self.issuer_id, self.key_id = integrity_key, issuer_id, key_id
        self.review_resolver, self.stem_input_authority = review_resolver, stem_input_authority
        self._fixed = (integrity_key, issuer_id, key_id, review_resolver, stem_input_authority)

    def _binding(self):
        _need((self.integrity_key, self.issuer_id, self.key_id, self.review_resolver, self.stem_input_authority) == self._fixed
            and _pins() == _PINNED and reader.ROOT_CONSTANTS['model_versions'] == _MODELS
            and tuple(reader.SOURCE_PATHS) == _PATHS[:-4]
            and program.VERSION == _PROGRAM_VERSION and program.DISPLAY_POLICY == _DISPLAY_POLICY
            and Path(reader.__file__) == _ROOT/'backend/app/crop_leaf_appearance_artifact_reader.py'
            and Path(program.__file__) == _ROOT/'backend/app/crop_leaf_appearance_program.py'
            and Path(stem.__file__) == _ROOT/'backend/app/crop_morphology_input_evidence.py'
            and Path(provenance.__file__) == _ROOT/'backend/app/provenance.py')

    def _review(self, review_id, source_sha256):
        _need(stem._identifier(review_id))
        try:
            value = self.review_resolver(review_id)
        except Exception:
            raise LeafAppearanceInputEvidenceHold('leaf appearance input evidence unavailable') from None
        _need(type(value) is dict and set(value) == {'evidence_id','reviewer_id','decision_id','source_sha256','status','scope'}
            and all(stem._identifier(value[k]) for k in ('evidence_id','reviewer_id','decision_id'))
            and value['evidence_id'] == review_id and value['source_sha256'] == source_sha256
            and value['status'] == 'accepted_for_software_validation' and value['scope'] == SCOPE)
        return json.loads(reader._canonical(value))

    def _prepare(self, *, program_raw, source_raw, expected_program_sha256, expected_source_sha256,
                 review_id, decision_at, stem_arguments):
        decision = stem._decision(decision_at)
        reader._hash(expected_program_sha256); reader._hash(expected_source_sha256)
        reader._closed(stem_arguments, {'program_raw','source_raw','expected_program_sha256','expected_source_sha256',
            'evidence_raw','review_id','decision_at'})
        _need(stem_arguments['decision_at'] == decision_at)
        parent = self.stem_input_authority.verify(**stem_arguments)
        p = program.parse_leaf_appearance_program(program_raw=program_raw)
        parent_program = reader._parse(stem_arguments['program_raw'], stem.reader.PROGRAM_MAX)
        reader.population._program({**{k:p[k] for k in ('origin','program_id','rights','stem','initialization')},
            'schema_version':'leaf-population-software-program-v1', 'births':[],
            'display_policy':reader.population.POPULATION_DISPLAY_POLICY}, parent_program)
        bindings = reader._initial_bindings(p, parent_program)
        _need(p['stem']['program_sha256'] == parent.program_sha256)
        source = reader._parse(source_raw, SOURCE_MAX)
        reader._closed(source, {'schema_version','program_sha256','provenance'})
        _need(source['schema_version'] == SOURCE_VERSION
            and sha256(program_raw).hexdigest() == source['program_sha256'] == expected_program_sha256
            and sha256(source_raw).hexdigest() == expected_source_sha256)
        review = self._review(review_id, expected_source_sha256)
        record, count = _record(p, program_raw, source, review, decision_at)
        metadata = {'program_id':p['program_id'], 'source_record':record, 'variable_count':count,
            **{key+'_sha256':sha256(reader._canonical(p[key])).hexdigest() for key in ('initialization','policy','leaf_profile')},
            'initial_bindings_sha256':sha256(reader._canonical(bindings)).hexdigest(),
            'initial_leaf_count':len(p['initialization']['initial_inventory']['leaves']), 'initial_node_count':len(bindings),
            'stem_artifact_sha256':p['stem']['artifact_sha256'], 'stem_artifact_root_verified':False,
            'parent_stem_program_sha256':parent.program_sha256, 'parent_stem_source_sha256':parent.source_sha256,
            'parent_stem_evidence_sha256':parent.evidence_sha256,
            'parent_stem_metadata_sha256':sha256(reader._canonical(parent.metadata)).hexdigest(),
            'redistribution_allowed':p['rights']['redistribute']}
        fixed = {'version':VERSION, 'scope':SCOPE, 'gates':'not_assessed', 'numerical_initial_state_validation':False,
            'issuer_id':self.issuer_id, 'key_id':self.key_id, 'program_sha256':expected_program_sha256,
            'source_sha256':expected_source_sha256, 'program_bytes':len(program_raw), 'source_bytes':len(source_raw),
            'decision_at':decision, 'review':review, 'code_sha256':dict(_PINNED), 'model_versions':dict(_MODELS),
            'metadata_sha256':sha256(reader._canonical(metadata)).hexdigest()}
        return fixed, metadata

    def _signature(self, payload):
        return hmac.new(self.integrity_key, DOMAIN+reader._canonical(payload), 'sha256').hexdigest()

    def _finish(self, fixed, metadata, arguments):
        parent = self.stem_input_authority.verify(**arguments)
        _need(parent.evidence_sha256 == metadata['parent_stem_evidence_sha256']
            and sha256(reader._canonical(parent.metadata)).hexdigest() == metadata['parent_stem_metadata_sha256'])
        _need(self._review(fixed['review']['evidence_id'], fixed['source_sha256']) == fixed['review'])

    @_checked
    def issue(self, **kwargs):
        fixed, metadata = self._prepare(**kwargs)
        payload = {**fixed, 'validated_at':stem._stamp(stem._now())}
        raw = reader._canonical({'payload':payload, 'hmac_sha256':self._signature(payload)})
        _need(len(raw) <= EVIDENCE_MAX)
        self._finish(fixed, metadata, kwargs['stem_arguments'])
        return raw

    @_checked
    def verify(self, *, evidence_raw, **kwargs):
        doc = reader._parse(evidence_raw, EVIDENCE_MAX); reader._closed(doc, {'payload','hmac_sha256'})
        reader._hash(doc['hmac_sha256'])
        _need(hmac.compare_digest(self._signature(doc['payload']), doc['hmac_sha256']))
        fixed, metadata = self._prepare(**kwargs)
        stamp = doc['payload']['validated_at']; _need(type(stamp) is str)
        validated_at = datetime.fromisoformat(stamp.replace('Z','+00:00'))
        _need(validated_at.utcoffset() == timedelta(0) and stem._stamp(validated_at) == stamp
            and kwargs['decision_at'] <= validated_at <= stem._now()
            and reader._canonical(doc['payload']) == reader._canonical({**fixed,'validated_at':stamp}))
        self._finish(fixed, metadata, kwargs['stem_arguments'])
        return VerifiedLeafAppearanceInputEvidence(reader._canonical(metadata), fixed['program_sha256'],
            fixed['source_sha256'], sha256(evidence_raw).hexdigest(), _TOKEN)
