"""Current, calculation-free reads of server-signed completed morphology artifacts."""
from datetime import datetime, timedelta, timezone
from functools import wraps
from hashlib import sha256
import hmac
from pathlib import Path

from . import crop_morphology_farm_binding as farms
from . import crop_rational_morphology_artifact_reader as reader
from .content_access import ContentAccess
from .crop_morphology_artifact_io import MorphologyBlobStore


VERSION = 'morphology-server-calculated-artifact-v1'
DOMAIN = b'ossf-morphology-server-calculated-artifact-v1\0'
PROOF_MAX = 128*1024
RETURN_MAX = 2*1024**2
_ROOT = Path(__file__).resolve().parents[2]
_PATHS = tuple('backend/app/'+name+'.py' for name in ('crop_morphology_signed_artifact', 'crop_morphology_signed_producer',
    'crop_morphology_farm_binding', 'crop_morphology_input_evidence', 'crop_rational_morphology_artifact_reader',
    'crop_morphology_artifact_io', 'content_access'))
_HASH_FIELDS = ('program_sha256', 'source_sha256', 'input_evidence_sha256', 'binding_sha256', 'numerical_root_sha256')
_FIELDS = {'schema_version', *reader.FLAGS, 'issuer_id', 'key_id', 'tenant_id', 'study_id', 'revision',
    'calculated_at', 'code_sha256', *_HASH_FIELDS}
_FLAGS = dict(reader.FLAGS)


class MorphologySignedArtifactHold(ValueError):
    """No currently permitted original server-calculated morphology result."""


def _need(condition):
    if not condition:
        raise MorphologySignedArtifactHold('signed morphology artifact unavailable')


def _checked(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except PermissionError:
            raise
        except Exception:
            raise MorphologySignedArtifactHold('signed morphology artifact unavailable') from None
    return run


def _code_pins():
    return {p: sha256((_ROOT/p).read_bytes()).hexdigest() for p in _PATHS}


_CODE_PINS = _code_pins()


def _now():
    return datetime.now(timezone.utc)


def _stamp(value):
    return value.isoformat(timespec='microseconds').replace('+00:00', 'Z')


def _calculated_at(value):
    _need(type(value) is str)
    at = datetime.fromisoformat(value.replace('Z', '+00:00'))
    _need(at.utcoffset() == timedelta(0) and _stamp(at) == value and at <= _now())
    return at


def _linked(manifest, binding, program_raw):
    source = binding['input']
    _need(manifest['program_sha256'] == sha256(program_raw).hexdigest() == source['program_sha256']
        and manifest['initial_state_sha256'] == source['initial_state_sha256']
        and manifest['model_versions'] == source['model_versions'] == reader.MODEL_VERSIONS
        and manifest['code_sha256'] == {p: source['code_sha256'][p] for p in reader.SOURCE_PATHS}
        and manifest['samples'][-1]['at'] == source['period']['end'])


class MorphologyArtifactAuthority:
    @_checked
    def __init__(self, farm_binding, *, directory, access, integrity_key, issuer_id, key_id):
        _need(type(farm_binding) is farms.MorphologyFarmBinding and type(access) is ContentAccess
            and type(integrity_key) is bytes and 32 <= len(integrity_key) <= 4096
            and farms.evidence._identifier(issuer_id) and farms.evidence._identifier(key_id))
        directory = Path(directory)
        _need(directory.is_absolute() and '..' not in directory.parts)
        self.farm_binding, self.directory, self.access = farm_binding, directory, access
        self.integrity_key, self.issuer_id, self.key_id = integrity_key, issuer_id, key_id
        self._fixed = self._pointers()
        self._binding()

    def _pointers(self):
        return (self.farm_binding, self.farm_binding._fixed, self.directory, self.access,
            self.integrity_key, self.issuer_id, self.key_id)

    def _binding(self):
        self.farm_binding._binding()
        _need(self._pointers() == self._fixed and _code_pins() == _CODE_PINS
            and reader.FLAGS == _FLAGS and PROOF_MAX == 128*1024 and RETURN_MAX == 2*1024**2)

    def _signed(self, payload):
        return reader._canonical({'payload': payload,
            'hmac_sha256': hmac.new(self.integrity_key, DOMAIN+reader._canonical(payload), 'sha256').hexdigest()})

    def _load(self, tenant, result_sha256):
        self._binding(); reader._hash(result_sha256)
        with MorphologyBlobStore(self.directory, self.access) as store:
            raw = store.get(result_sha256, maximum=PROOF_MAX)
            doc = reader._parse(raw, PROOF_MAX); reader._closed(doc, {'payload', 'hmac_sha256'})
            reader._hash(doc['hmac_sha256']); payload = doc['payload']; reader._closed(payload, _FIELDS)
            _need(hmac.compare_digest(self._signed(payload), raw))
            _need(payload['schema_version'] == VERSION and all(payload[k] == v for k, v in reader.FLAGS.items())
                and payload['issuer_id'] == self.issuer_id and payload['key_id'] == self.key_id
                and payload['code_sha256'] == _CODE_PINS)
            for key in _HASH_FIELDS:
                reader._hash(payload[key])
            _calculated_at(payload['calculated_at'])
            if payload['tenant_id'] != tenant:
                raise PermissionError('signed morphology tenant unavailable')
            packet = {name: store.get(payload[field], maximum=maximum) for name, field, maximum in (
                ('program_raw', 'program_sha256', reader.PROGRAM_MAX),
                ('source_raw', 'source_sha256', farms.evidence.SOURCE_MAX),
                ('evidence_raw', 'input_evidence_sha256', farms.evidence.EVIDENCE_MAX))}
            binding_raw = store.get(payload['binding_sha256'], maximum=farms.MAX_BINDING_BYTES)
        binding = reader._parse(binding_raw, farms.MAX_BINDING_BYTES); request_raw = reader._canonical(binding['request'])
        _need(self.farm_binding.current(tenant, request_raw, binding_raw, **packet) == binding_raw)
        _need(binding['tenant_id'] == tenant and binding['request']['study_id'] == payload['study_id']
            and binding['request']['revision'] == payload['revision']
            and binding['input']['program_sha256'] == payload['program_sha256']
            and binding['input']['source_sha256'] == payload['source_sha256']
            and binding['input']['evidence_sha256'] == payload['input_evidence_sha256']
            and farms.documents._time(binding['registration']['decision_at']) <= _calculated_at(payload['calculated_at']))
        self._binding()
        return payload, binding_raw, binding, packet

    def _read(self, tenant, result_sha256, index):
        payload, binding_raw, binding, packet = self._load(tenant, result_sha256)
        root = payload['numerical_root_sha256']
        manifest = reader.read_rational_morphology_manifest(self.directory, self.access, root)
        _linked(manifest, binding, packet['program_raw'])
        value = manifest if index is None else reader.read_rational_morphology_frame(self.directory, self.access, root, index=index)
        after = self._load(tenant, result_sha256)
        _need(after[0] == payload and after[1] == binding_raw and after[3] == packet)
        common = {**reader.FLAGS, 'result_sha256': result_sha256, 'numerical_root_sha256': root,
            'calculated_at': payload['calculated_at'], 'study_id': payload['study_id'], 'revision': payload['revision'],
            'farm': binding['request']['farm'], 'profile_applicability': 'unvalidated_for_registered_crop',
            'program_sha256': payload['program_sha256'], 'source_sha256': payload['source_sha256'],
            'input_evidence_sha256': payload['input_evidence_sha256'], 'binding_sha256': payload['binding_sha256']}
        result = ({**common, 'schema_version': 'morphology-signed-manifest-v1', 'manifest': value} if index is None else
            {**common, 'schema_version': 'morphology-signed-frame-v1', 'frame': value, 'frame_sha256': sha256(reader._canonical(value)).hexdigest()})
        _need(len(reader._canonical(result)) <= RETURN_MAX)
        return result

    @_checked
    def read_manifest(self, tenant, result_sha256):
        return self._read(tenant, result_sha256, None)

    @_checked
    def read_frame(self, tenant, result_sha256, *, index):
        _need(type(index) is int and index >= 0)
        return self._read(tenant, result_sha256, index)
