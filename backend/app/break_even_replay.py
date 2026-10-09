"""Record fresh references observed by the existing break-even engine."""

from hashlib import sha256
from typing import Annotated, Literal, Self

from pydantic import Field, StringConstraints, model_validator

from .economic_contracts import untrusted_data
from .market_scenario import _json
from .provenance import Digest, FrozenContract, Name


_ARITY = {
    'get_break_even_plan': 1, 'get_economic_scenario': 2,
    'get_economic_scenario_pin': 2, 'get_economic_input': 2,
    'get_joint_shock': 2, 'get_joint_shock_pin': 2, 'get_input_rights': 2,
    'get_settlement_applicability': 2, 'get_settlement_evidence': 2,
    'get_prior_batch_cost': 1, 'get_market_hold_report': 1,
    'get_market_candidate': 2, 'get_decision_context': 3,
}
_MAX_READS = 16384
ReadMethod = Literal[
    'get_break_even_plan', 'get_economic_scenario', 'get_economic_scenario_pin',
    'get_economic_input', 'get_joint_shock', 'get_joint_shock_pin', 'get_input_rights',
    'get_settlement_applicability', 'get_settlement_evidence', 'get_prior_batch_cost',
    'get_market_hold_report', 'get_market_candidate', 'get_decision_context',
]
Reference = Annotated[Name, StringConstraints(max_length=200)]


class ReplayRead(FrozenContract):
    method: ReadMethod
    args: tuple[Reference, ...] = Field(min_length=1, max_length=3)
    value_sha256: Digest

    @model_validator(mode='after')
    def reference_shape(self) -> Self:
        if len(self.args) != _ARITY[self.method]:
            raise ValueError('break-even replay reference arity differs')
        return self


class BreakEvenReplayEvidence(FrozenContract):
    evidence_version: Literal['break-even-replay-evidence-v1']
    verification: Literal['full_grid_replay_evidence_only']
    tenant_id: Reference
    plan_id: Reference
    request_sha256: Digest
    plan_sha256: Digest
    result_sha256: Digest
    code_sha256: Digest
    environment_sha256: Digest
    trial_count: int = Field(ge=2, le=256)
    reads: tuple[ReplayRead, ...] = Field(min_length=1, max_length=_MAX_READS)

    @model_validator(mode='after')
    def ordered_references(self) -> Self:
        keys = [(item.method, item.args) for item in self.reads]
        if keys != sorted(set(keys)):
            raise ValueError('break-even replay references must be ordered and unique')
        plans = [item for item in self.reads if item.method == 'get_break_even_plan']
        if (len(plans) != 1 or plans[0].args != (self.plan_id,) or
                plans[0].value_sha256 != self.plan_sha256):
            raise ValueError('break-even replay plan reference differs')
        return self


def _value_hash(value):
    if value is None:
        raise ValueError('break-even replay reference missing')
    try:
        return sha256(_json(untrusted_data(value)).encode('utf-8')).hexdigest()
    except (TypeError, ValueError, OverflowError, RecursionError, UnicodeError):
        raise ValueError('break-even replay reference is not canonical data') from None


class ReplayReferences:
    def __init__(self, source, tenant_id):
        self._source, self._tenant = source, tenant_id
        self._reads = {}
        self._failed = False

    def tenant_is_authenticated(self, tenant_id):
        return (tenant_id == self._tenant and
                self._source.tenant_is_authenticated(tenant_id) is True)

    def __getattr__(self, name):
        if name not in _ARITY:
            raise AttributeError(name)

        def read(*args):
            if self._failed:
                raise ValueError('break-even replay capture already failed')
            try:
                reference = ReplayRead(method=name, args=args, value_sha256='0' * 64)
                key = (name, reference.args)
                value = getattr(self._source, name)(*reference.args)
                digest = _value_hash(value)
                previous = self._reads.get(key)
                if previous is not None and previous != digest:
                    raise ValueError('break-even replay reference changed during calculation')
                if previous is None and len(self._reads) >= _MAX_READS:
                    raise ValueError('break-even replay references exceed size limit')
                self._reads[key] = digest
                return value
            except Exception:
                self._failed = True
                raise

        return read

    def recheck(self, *, check=None):
        if self._failed:
            raise ValueError('break-even replay capture already failed')
        try:
            return self._rechecked(check)
        except Exception:
            self._failed = True
            raise

    def observed_reads(self):
        if self._failed or not self._reads:
            raise ValueError('break-even replay observations unavailable')
        return tuple(ReplayRead(method=method, args=args, value_sha256=digest)
            for (method, args), digest in sorted(self._reads.items()))

    def _rechecked(self, check):
        if check is not None and not callable(check):
            raise ValueError('break-even replay checkpoint invalid')
        if not self._reads:
            raise ValueError('break-even replay references are empty')
        verified = []
        for (method, args), digest in sorted(self._reads.items()):
            if check is not None:
                check()
            if not self.tenant_is_authenticated(self._tenant):
                raise ValueError('break-even replay tenant access denied')
            value = getattr(self._source, method)(*args)
            if _value_hash(value) != digest:
                raise ValueError('break-even replay reference changed after calculation')
            verified.append(ReplayRead(method=method, args=args, value_sha256=digest))
        if check is not None:
            check()
        if not self.tenant_is_authenticated(self._tenant):
            raise ValueError('break-even replay tenant access denied')
        return tuple(verified)
