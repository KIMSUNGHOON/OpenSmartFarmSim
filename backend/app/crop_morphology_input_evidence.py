"""Current source/review evidence for synthetic morphology inputs; no growth calculation."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import wraps
from hashlib import sha256
import hmac
import json
from pathlib import Path
import re

from . import crop_rational_morphology_artifact_reader as reader
from . import provenance


VERSION = 'morphology-input-evidence-v1'
SOURCE_VERSION = 'morphology-input-source-v1'
SCOPE = 'synthetic_morphology_input_structure_only'
QC_VERSION = 'morphology-program-structure-provenance-v1'
DOMAIN = b'ossf-morphology-input-evidence-v1\0'
SOURCE_MAX = 1024**2
EVIDENCE_MAX = 2*1024**2
_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATHS = (*reader.SOURCE_PATHS, 'backend/app/provenance.py', 'backend/app/crop_morphology_input_evidence.py')
_MODELS = dict(reader.MODEL_VERSIONS)
_TOKEN = object()


class MorphologyInputEvidenceHold(ValueError):
    """The requested original input has no current structural software evidence."""


def _need(condition):
    if not condition:
        raise MorphologyInputEvidenceHold('morphology input evidence unavailable')


def _current_pins():
    return {p: sha256((_ROOT/p).read_bytes()).hexdigest() for p in _SOURCE_PATHS}


_PINNED = _current_pins()


def _identifier(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', value) is not None


def _now():
    return datetime.now(timezone.utc)


def _stamp(value):
    return value.isoformat(timespec='microseconds').replace('+00:00', 'Z')


def _decision(value):
    _need(type(value) is datetime and value.utcoffset() == timedelta(0) and value <= _now())
    return _stamp(value)


def _operation(fn):
    @wraps(fn)
    def run(self, *args, **kwargs):
        try:
            self._binding()
            result = fn(self, *args, **kwargs)
            self._binding()
            return result
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
            raise MorphologyInputEvidenceHold('morphology input evidence unavailable') from None
    return run


def _variables(program):
    expected = {}
    def walk(value, path):
        if type(value) is dict and 'unit' in value:
            expected[path] = {'name': path, 'original_unit': value['unit'], 'time_semantics': 'instant',
                'interval_start': None, 'interval_end': None, 'provider_qc_status': 'not_supplied', 'provider_qc_value': None}
        elif type(value) is dict:
            for name, child in value.items():
                child_path = f'{path}.{name}' if path else name
                if name in ('sequence', 'next_sequence', 'inventory_start_sequence'):
                    expected[child_path] = {'name': child_path, 'original_unit': '1', 'time_semantics': 'instant',
                        'interval_start': None, 'interval_end': None, 'provider_qc_status': 'not_supplied', 'provider_qc_value': None}
                else:
                    walk(child, child_path)
        elif type(value) is list:
            for index, child in enumerate(value):
                walk(child, f'{path}.{index}')
    walk(program, '')
    for index, segment in enumerate(program['segments']):
        expected[f'segments.{index}.air_temperature'].update(time_semantics='mean',
            interval_start=segment['start_utc'], interval_end=segment['end_utc'])
    return expected


def _source_record(program, program_raw, source, review, decision_at):
    record = provenance.SourceRecord.model_validate_json(reader._canonical(source['provenance']))
    value = record.model_dump(mode='json')
    _need(reader._canonical(value) == reader._canonical(source['provenance']))
    _need(record.synthetic is True and record.synthetic_author is not None and record.synthetic_method is not None
        and record.scope.station_or_grid_id is None and not record.request_details
        and record.valid_from is None and record.valid_to is None
        and record.scope.product_id == program['program_id'] and record.scope.product_version == program['schema_version']
        and record.revision_id == program['rights']['revision']
        and record.raw_sha256 == sha256(program_raw).hexdigest()
        and record.source_reviewer == review['reviewer_id'] and record.source_evidence_id == review['evidence_id'])
    times = (record.observed_at, record.published_at, record.available_at, record.retrieved_at)
    _need(all(t is not None and t <= decision_at for t in times))
    _need(reader._utc(program['rights']['declared_at_utc']) <= record.observed_at
        <= record.published_at <= record.available_at <= record.retrieved_at <= decision_at)
    expected = _variables(program)
    _need({v['name']: v for v in value['variables']} == expected)
    _need(len(record.project_checks) == len(expected)
        and {c.variable for c in record.project_checks} == set(expected)
        and all(c.name == 'structural_software_contract' and c.version == QC_VERSION and c.status == 'passed'
            and c.evidence_id == review['evidence_id'] and c.reviewer == review['reviewer_id'] for c in record.project_checks))
    _need({r.action for r in record.rights} == {'access', 'store', 'transform', 'display', 'redistribute'}
        and all(r.status == ('denied' if r.action == 'redistribute' and not program['rights']['redistribute'] else 'allowed')
            and r.evidence_id == review['evidence_id'] and r.reviewer == review['reviewer_id'] for r in record.rights))
    return value, len(expected)


@dataclass(frozen=True)
class VerifiedMorphologyInputEvidence:
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


class MorphologyInputEvidenceAuthority:
    def __init__(self, *, integrity_key, issuer_id, key_id, review_resolver):
        _need(type(integrity_key) is bytes and 32 <= len(integrity_key) <= 4096
            and _identifier(issuer_id) and _identifier(key_id) and callable(review_resolver))
        self.integrity_key, self.issuer_id, self.key_id, self.review_resolver = integrity_key, issuer_id, key_id, review_resolver
        self._fixed = (integrity_key, issuer_id, key_id, review_resolver)

    def _binding(self):
        _need((self.integrity_key, self.issuer_id, self.key_id, self.review_resolver) == self._fixed
            and _current_pins() == _PINNED
            and reader.MODEL_VERSIONS == _MODELS and tuple(reader.SOURCE_PATHS) == _SOURCE_PATHS[:-2]
            and Path(reader.__file__) == _ROOT/'backend/app/crop_rational_morphology_artifact_reader.py'
            and Path(provenance.__file__) == _ROOT/'backend/app/provenance.py')

    def _review(self, review_id, source_sha256):
        _need(_identifier(review_id))
        try:
            value = self.review_resolver(review_id)
        except Exception:
            raise MorphologyInputEvidenceHold('morphology input evidence unavailable') from None
        _need(type(value) is dict and set(value) == {'evidence_id', 'reviewer_id', 'decision_id', 'source_sha256', 'status', 'scope'}
            and all(_identifier(value[k]) for k in ('evidence_id', 'reviewer_id', 'decision_id'))
            and value['evidence_id'] == review_id and value['source_sha256'] == source_sha256
            and value['status'] == 'accepted_for_software_validation' and value['scope'] == SCOPE)
        return json.loads(reader._canonical(value))

    def _prepare(self, *, program_raw, source_raw, expected_program_sha256, expected_source_sha256, review_id, decision_at):
        decision = _decision(decision_at)
        reader._hash(expected_program_sha256); reader._hash(expected_source_sha256)
        program = reader._parse(program_raw, reader.PROGRAM_MAX); reader._program(program)
        source = reader._parse(source_raw, SOURCE_MAX)
        reader._closed(source, {'schema_version', 'program_sha256', 'provenance'})
        _need(source['schema_version'] == SOURCE_VERSION
            and sha256(program_raw).hexdigest() == source['program_sha256'] == expected_program_sha256
            and sha256(source_raw).hexdigest() == expected_source_sha256)
        review = self._review(review_id, expected_source_sha256)
        record, count = _source_record(program, program_raw, source, review, decision_at)
        metadata = {'program_id': program['program_id'], 'source_record': record, 'variable_count': count,
            'initial_state_sha256': sha256(reader._canonical(program['initial_state'])).hexdigest(),
            'forcing_sha256': sha256(reader._canonical(program['segments'])).hexdigest(),
            'output_schedule_sha256': sha256(reader._canonical(program['output_times'])).hexdigest(),
            'redistribution_allowed': program['rights']['redistribute']}
        fixed = {'version': VERSION, 'scope': SCOPE, 'gates': 'not_assessed', 'numerical_initial_state_validation': False,
            'issuer_id': self.issuer_id, 'key_id': self.key_id, 'program_sha256': expected_program_sha256,
            'source_sha256': expected_source_sha256, 'program_bytes': len(program_raw), 'source_bytes': len(source_raw),
            'decision_at': decision, 'review': review, 'code_sha256': dict(_PINNED), 'model_versions': dict(_MODELS),
            'metadata_sha256': sha256(reader._canonical(metadata)).hexdigest()}
        return fixed, metadata

    def _signature(self, payload):
        return hmac.new(self.integrity_key, DOMAIN+reader._canonical(payload), 'sha256').hexdigest()

    def _finish_review(self, fixed):
        _need(self._review(fixed['review']['evidence_id'], fixed['source_sha256']) == fixed['review'])

    @_operation
    def issue(self, **kwargs):
        fixed, _ = self._prepare(**kwargs)
        payload = {**fixed, 'validated_at': _stamp(_now())}
        raw = reader._canonical({'payload': payload, 'hmac_sha256': self._signature(payload)})
        _need(len(raw) <= EVIDENCE_MAX)
        self._finish_review(fixed)
        return raw

    @_operation
    def verify(self, *, evidence_raw, **kwargs):
        doc = reader._parse(evidence_raw, EVIDENCE_MAX); reader._closed(doc, {'payload', 'hmac_sha256'})
        reader._hash(doc['hmac_sha256'])
        _need(hmac.compare_digest(self._signature(doc['payload']), doc['hmac_sha256']))
        fixed, metadata = self._prepare(**kwargs)
        stamp = doc['payload']['validated_at']
        _need(type(stamp) is str)
        validated_at = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        _need(validated_at.utcoffset() == timedelta(0) and _stamp(validated_at) == stamp
            and kwargs['decision_at'] <= validated_at <= _now()
            and reader._canonical(doc['payload']) == reader._canonical({**fixed, 'validated_at': stamp}))
        self._finish_review(fixed)
        return VerifiedMorphologyInputEvidence(reader._canonical(metadata), fixed['program_sha256'],
            fixed['source_sha256'], sha256(evidence_raw).hexdigest(), _TOKEN)
