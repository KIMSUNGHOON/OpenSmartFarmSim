"""Admit immutable leaf population references to existing deterministic simulation jobs."""
from functools import wraps
from hashlib import sha256
import hmac
from pathlib import Path

from . import crop_leaf_population_signed_artifact as signed
from .job_store import JobStore, JobIntentConflict
from .jobs import canonical_input_bytes, MAX_INPUT_BYTES


INPUT_VERSION = 'leaf-population-execution-input-v1'
INTENT_DOMAIN = b'ossf-leaf-population-execution-admission-v1\0'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_CONTRACT = (INPUT_VERSION, INTENT_DOMAIN, MAX_INPUT_BYTES)
_FIELDS = {'input_version', 'request', 'farm_binding_sha256', 'input_resolver_version',
    'authority', 'admission_code_sha256', 'intent_hmac_sha256'}


class LeafPopulationExecutionHold(ValueError):
    """The original leaf population study has no current execution admission."""


def _need(condition):
    if not condition:
        raise LeafPopulationExecutionHold('leaf population execution unavailable')


def _checked(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except PermissionError:
            raise
        except JobIntentConflict:
            raise JobIntentConflict('leaf population study revision conflict') from None
        except Exception:
            raise LeafPopulationExecutionHold('leaf population execution unavailable') from None
    return run


def _authority_identity(authority):
    return {'issuer_id': authority.issuer_id, 'key_id': authority.key_id, 'artifact_code_sha256': dict(signed._CODE_PINS)}


@_checked
def _signed_input(authority, request, binding_sha256, resolver_version):
    signed.reader._hash(binding_sha256)
    _need(signed.farms.farms.permissions._name(resolver_version))
    payload = {'input_version': INPUT_VERSION, 'request': signed.reader._parse(signed.reader._canonical(request), signed.farms.MAX_REQUEST_BYTES),
        'farm_binding_sha256': binding_sha256, 'input_resolver_version': resolver_version,
        'authority': _authority_identity(authority), 'admission_code_sha256': CODE_SHA256}
    signature = hmac.new(authority.integrity_key, INTENT_DOMAIN+canonical_input_bytes(payload), 'sha256').hexdigest()
    value = {**payload, 'intent_hmac_sha256': signature}
    canonical_input_bytes(value)
    return value


@_checked
def _verified_input(authority, raw, resolver_version):
    value = signed.reader._parse(raw, MAX_INPUT_BYTES); signed.reader._closed(value, _FIELDS)
    _need(canonical_input_bytes(value) == raw and value['input_version'] == INPUT_VERSION
        and value['admission_code_sha256'] == CODE_SHA256 and value['input_resolver_version'] == resolver_version
        and signed.reader._canonical(value['authority']) == signed.reader._canonical(_authority_identity(authority)))
    signed.reader._hash(value['farm_binding_sha256']); signed.reader._hash(value['intent_hmac_sha256'])
    payload = {k: v for k, v in value.items() if k != 'intent_hmac_sha256'}
    _need(hmac.compare_digest(value['intent_hmac_sha256'],
        hmac.new(authority.integrity_key, INTENT_DOMAIN+canonical_input_bytes(payload), 'sha256').hexdigest()))
    return value


class LeafPopulationExecutionService:
    @_checked
    def __init__(self, authority, *, input_resolver):
        _need(type(authority) is signed.LeafPopulationArtifactAuthority and callable(input_resolver)
            and signed.farms.farms.permissions._name(input_resolver.version))
        self.authority, self.input_resolver = authority, input_resolver
        self.jobs = authority.farm_binding.jobs
        self._fixed = self._pointers()
        self._binding()

    def _pointers(self):
        return (self.authority, self.authority._pointers(), self.jobs, self.jobs.principal_provider,
            self.input_resolver, self.input_resolver.version)

    def _binding(self):
        self.authority._binding()
        _need(self._pointers() == self._fixed and self.jobs is self.authority.farm_binding.jobs
            and type(self.jobs) is JobStore and (INPUT_VERSION, INTENT_DOMAIN, MAX_INPUT_BYTES) == _CONTRACT
            and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256)

    def _guard(self, tenant):
        self._binding()
        if not self.jobs._has_scope(tenant, 'simulation_create'):
            raise PermissionError('leaf population execution access denied')
        self.authority.farm_binding._guard(tenant, True)
        self._binding()
        if not self.jobs._has_scope(tenant, 'simulation_create'):
            raise PermissionError('leaf population execution access denied')

    def _resolve(self, tenant, request):
        self._binding()
        result = self.input_resolver(tenant, signed.reader._parse(signed.reader._canonical(request['input']), MAX_INPUT_BYTES))
        self._binding()
        _need(type(result) is dict and set(result) == {'program_raw', 'source_raw', 'evidence_raw'}
            and all(type(v) is bytes for v in result.values()))
        for name, key in [('program_raw', 'program_sha256'), ('source_raw', 'source_sha256'), ('evidence_raw', 'evidence_sha256')]:
            _need(sha256(result[name]).hexdigest() == request['input'][key])
        return dict(result)

    @_checked
    def current_input(self, tenant, input_raw, *, write=False):
        _need(type(write) is bool); self._binding()
        self.authority.farm_binding._guard(tenant, write)
        value = _verified_input(self.authority, input_raw, self.input_resolver.version)
        request_raw = signed.reader._canonical(value['request'])
        request = self.authority.farm_binding._request(request_raw); packet = self._resolve(tenant, request)
        with signed.MorphologyBlobStore(self.authority.directory, self.authority.access) as store:
            binding_raw = store.get(value['farm_binding_sha256'], maximum=signed.farms.MAX_BINDING_BYTES)
        _need(self.authority.farm_binding.current(tenant, request_raw, binding_raw, **packet, write=write) == binding_raw)
        self._binding(); self.authority.farm_binding._guard(tenant, write)
        return value, binding_raw, packet

    @_checked
    def submit(self, tenant, request_raw):
        self._guard(tenant)
        request = self.authority.farm_binding._request(request_raw); packet = self._resolve(tenant, request)
        binding_raw = self.authority.farm_binding.prepare(tenant, request_raw, **packet)
        with signed.MorphologyBlobStore(self.authority.directory, self.authority.access, write=True) as store:
            binding_sha256 = store.put(binding_raw, maximum=signed.farms.MAX_BINDING_BYTES)
        value = _signed_input(self.authority, request, binding_sha256, self.input_resolver.version)
        raw = canonical_input_bytes(value)
        self._guard(tenant)
        def verify():
            self._guard(tenant)
            current, checked_binding, checked_packet = self.current_input(tenant, raw, write=True)
            _need(canonical_input_bytes(current) == raw and checked_binding == binding_raw and checked_packet == packet)
            self._guard(tenant)
            _need(canonical_input_bytes(value) == raw)
        key = INPUT_VERSION+':'+sha256(INTENT_DOMAIN+signed.reader._canonical([request['study_id'], request['revision']])).hexdigest()
        return self.jobs.submit(tenant, 'simulation', value, key, commit_guard=verify)
