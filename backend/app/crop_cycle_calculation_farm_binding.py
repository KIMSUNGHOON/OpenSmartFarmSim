"""Current farm authority for verified research inputs, before signed execution."""
from hashlib import sha256
import json
from pathlib import Path

from . import crop_cycle_farm_binding as original
from . import crop_cycle_calculation_context as calculation
from . import crop_cycle_input_evidence as evidence
from .crop_result_store import READ_SCOPES, WRITE_SCOPES, _name
from .farm_authoring_storage import FarmAuthoringService
from .runtime_roles import RuntimeLoginPolicy
from .thermal_run_store import _canonical

VERSION = 'crop-cycle-verified-farm-binding-v1'
MAX_BINDING_BYTES = 128*1024
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES = {'original_farm_helpers': original, 'calculation_context': calculation, 'input_evidence': evidence}
DEPENDENCY_SHA256 = {name: sha256(Path(module.__file__).read_bytes()).hexdigest()
                     for name, module in _MODULES.items()}
_DEPENDENCY_RAW = _canonical(DEPENDENCY_SHA256)


class CalculationFarmBindingHold(ValueError):
    """No current registered farm binding for this verified calculation input."""


def _need(condition):
    if not condition:
        raise CalculationFarmBindingHold('verified cycle farm input binding unavailable')


class CalculationFarmBinding:
    _request = original.CycleFarmBinding._request
    _registration = original.CycleFarmBinding._registration

    def __init__(self, farms, input_authority, *, input_rights):
        try:
            _need(type(farms) is FarmAuthoringService
                  and type(input_authority) is evidence.InputEvidenceAuthority
                  and callable(input_rights) and _name(input_rights.policy_version))
            self.farms, self.jobs = farms, farms.replay.jobs
            self.input_authority, self.input_rights = input_authority, input_rights
            self.notice_raw = input_authority.notice_raw
            self._fixed = self._pointers()
            self._binding()
        except Exception:
            raise CalculationFarmBindingHold('verified cycle farm authority unavailable') from None

    def _profiles(self):
        return dict(self.input_authority.profiles)

    def _pointers(self):
        return (self.farms, self.farms._pointers(), self.jobs, self.input_authority,
                self.input_authority._pointers(), self.notice_raw, self.input_rights,
                self.input_rights.policy_version, self.jobs._dsn, self.jobs.schema,
                self.jobs.runtime_identity, self.jobs.audit_runtime_grants)

    def _binding(self):
        self.farms._binding()
        self.input_authority._binding()
        policy, kind = self.jobs.runtime_identity
        _need(self._pointers() == self._fixed and self.farms.replay.jobs is self.jobs
              and type(policy) is RuntimeLoginPolicy and kind == 'authority'
              and policy.crop_cycle_result_storage is True and self.jobs.audit_runtime_grants is True
              and self.notice_raw == self.input_authority.notice_raw
              and CODE_SHA256 == sha256(Path(__file__).read_bytes()).hexdigest()
              and _canonical(DEPENDENCY_SHA256) == _DEPENDENCY_RAW
              and DEPENDENCY_SHA256 == {name: sha256(Path(module.__file__).read_bytes()).hexdigest()
                  for name, module in _MODULES.items()}
              and MAX_BINDING_BYTES == original.MAX_BINDING_BYTES == 128*1024)

    def _guard(self, tenant, write):
        self._binding()
        self.farms._guard(tenant, self._fixed[1], WRITE_SCOPES if write else READ_SCOPES)

    def _input(self, request, context):
        _need(type(context) is calculation.CalculationContext
              and context._authority is self.input_authority)
        context.recheck()
        root = context.reader.manifest
        _need(context.reader.root_sha256 == request['input']['root_sha256']
              and root['program_id'] == request['input']['program_id'])
        validation = context.manifest['input_validation']
        return {'root_sha256': context.reader.root_sha256,
            'calculation_sha256': context.reader.calculation_sha256,
            'program_id': root['program_id'], 'period': root['period'], 'plan': context.reader.plan,
            'profile_sha256': root['profile_sha256'], 'normalization_sha256': root['normalization_sha256'],
            'python_version': root['python_version'], 'input_validation': {
                'context_sha256': context.root_sha256,
                'evidence_sha256': sha256(context._evidence_raw).hexdigest(),
                'validated_context_sha256': validation['validated_context_sha256'],
                'engine_version': calculation.VERSION, 'input_evidence_version': evidence.VERSION,
                'calculation_code_sha256': calculation.CODE_SHA256,
                'input_evidence_code_sha256': evidence.CODE_SHA256,
                'input_evidence_dependency_sha256': dict(evidence.DEPENDENCY_SHA256)}}

    def _rights(self, tenant, request, source, write):
        for use in (('research_calculation', 'research_display') if write else ('research_display',)):
            declaration = json.loads(_canonical(request['rights']))
            _need(self.input_rights(tenant, declaration, source['root_sha256'], use) is True)
            _need(_canonical(declaration) == _canonical(request['rights']))

    def _bind(self, tenant, request_raw, context, write):
        _need(type(write) is bool)
        self._guard(tenant, write)
        request = self._request(request_raw)
        source = self._input(request, context)
        registration = self._registration(tenant, request, source)
        self._rights(tenant, request, source, write)
        self._guard(tenant, write)
        self._rights(tenant, request, source, write)
        self._guard(tenant, write)
        _need(self._input(request, context) == source)
        _need(self._registration(tenant, request, source) == registration)
        self._guard(tenant, write)
        result = _canonical({'version': VERSION, 'scope': 'synthetic_crop_math_only',
            'tenant_id': tenant, 'request': request, 'registration': registration, 'input': source,
            'rights_policy_version': self.input_rights.policy_version, 'binding_code_sha256': CODE_SHA256,
            'binding_dependency_sha256': DEPENDENCY_SHA256})
        _need(len(result) <= MAX_BINDING_BYTES)
        return result

    def prepare(self, tenant, request_raw, context):
        try:
            return self._bind(tenant, request_raw, context, True)
        except PermissionError:
            raise
        except Exception:
            raise CalculationFarmBindingHold('verified cycle farm input binding unavailable') from None

    def current(self, tenant, request_raw, context, expected_binding_raw, *, write=False):
        try:
            _need(type(expected_binding_raw) is bytes and 1 <= len(expected_binding_raw) <= MAX_BINDING_BYTES)
            result = self._bind(tenant, request_raw, context, write)
            _need(result == expected_binding_raw)
            return result
        except PermissionError:
            raise
        except Exception:
            raise CalculationFarmBindingHold('verified cycle farm input binding unavailable') from None
