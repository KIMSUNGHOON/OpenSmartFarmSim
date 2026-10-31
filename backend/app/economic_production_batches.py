"""Versioned batch admission around the unchanged conditional Decimal ledger."""
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime
from decimal import Decimal, Inexact, localcontext
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal, Self

from pydantic import field_validator, model_validator

from . import economic_contracts as contracts, economics as legacy, market, provenance
from .market import resolve_market_context, UnavailableMarketContext, validate_first_g1_use, validate_market_context_chain
from .provenance import FrozenContract, Name

FORMULA_VERSION = 'economic-ledger-v10-declared-production-batches'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENTS = (contracts, legacy, market, provenance)
COMPONENT_SHA256 = {m.__name__: sha256(Path(m.__file__).read_bytes()).hexdigest() for m in COMPONENTS}
MAX_BYTES = 2 * 1024**2


class ProductionBatchRef(FrozenContract):
    batch_id: Name
    revision: Name


class OwnedProductionBatch(ProductionBatchRef):
    tenant_id: Name
    production_start_at: datetime
    origin: Literal['user']
    evidence_level: Literal['assumed']
    source_ref: Name
    assumption_scope: Name
    available_at: datetime
    scope_start: date
    scope_end: date
    rights: Literal['conditional_g1_use']
    immutable: Literal[True]

    _utc = field_validator('production_start_at', 'available_at')(contracts.utc)

    @field_validator('immutable', mode='before')
    @classmethod
    def explicit_immutable(cls, value):
        if value is not True:
            raise ValueError('immutable must be the JSON boolean true')
        return value


class BatchEconomicScenario(contracts.EconomicScenario):
    schema_version: Literal['4']
    production_batches: tuple[ProductionBatchRef, ...]

    @model_validator(mode='after')
    def unique_batches(self) -> Self:
        ids = [p.batch_id for p in self.production_batches]
        if len(ids) > 512 or len(ids) != len(set(ids)):
            raise ValueError('at most 512 distinct production batches required')
        return self


@dataclass(frozen=True)
class ProductionBatchCosts:
    batch_id: str
    revision: str
    harvest_event_declared: bool
    variable_incurred: Decimal | None
    fixed_incurred: Decimal | None
    cash_paid_in_period: Decimal | None
    remaining_payable_at_period_end: Decimal | None


@dataclass(frozen=True)
class ProductionBatchResult:
    ledger: legacy.EconomicResult
    production_batches: tuple[OwnedProductionBatch, ...]
    batch_costs: tuple[ProductionBatchCosts, ...]
    code_sha256: str
    component_sha256: dict[str, str]
    scope: str = 'conditional_user_assumptions_only'
    G0_G4: str = 'not_assessed'
    R2: str = 'not_approved'


def _raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False,
                      default=lambda v: v.model_dump(mode='json') if isinstance(v, FrozenContract)
                      else str(v) if isinstance(v, Decimal) else v.isoformat()).encode()


def _code_fence():
    if (sha256(Path(__file__).read_bytes()).hexdigest() != CODE_SHA256 or
            any(sha256(Path(m.__file__).read_bytes()).hexdigest() != COMPONENT_SHA256[m.__name__]
                for m in COMPONENTS)):
        raise ValueError('CODE_HOLD: unchanged batch and legacy ledger code required')


def result_bytes(result):
    value = asdict(result)
    inventory = value['ledger']['closing_inventory']
    if inventory is not None:
        value['ledger']['closing_inventory'] = [
            {'batch_id': key[0], 'grade': key[1], 'channel': key[2], 'quantity_kg': amount}
            for key, amount in sorted(inventory.items())]
    return _raw(value)


class ProductionBatchLedger(legacy.EconomicLedger):
    def _context(self, s):
        digest = self._verify_scenario_pin(s)
        market = resolve_market_context(s.market_context, tenant_id=s.tenant_id,
                                        decision_at=s.decision_at, repository=self._repository)
        if not isinstance(market, UnavailableMarketContext):
            raise ValueError('first conditional batch ledger requires market hold')
        validate_market_context_chain(scenario_context=s.scenario_market_context,
            economic_scenario_context=s.market_context, economic_result_context=market, assessment_context=market)
        inputs = tuple(contracts.iter_economic_numbers(s))
        if not inputs:
            raise ValueError('scoped user inputs required')
        self._verify_inputs(s, inputs)
        self._verify_settlement_evidence(s)
        validate_first_g1_use(market, economic_inputs=tuple({
            'origin': n.origin, 'evidence_level': n.evidence_level,
            'assumption_scope': n.assumption_scope} for n in inputs), assessment_status='hold')
        batches = []
        size = 0
        for ref in s.production_batches:
            try:
                raw = self._repository.get_production_batch(ref.batch_id, ref.revision)
                if not isinstance(raw, dict):
                    raise ValueError()
                batch = OwnedProductionBatch.model_validate(contracts.untrusted_data(raw))
            except Exception:
                raise ValueError('BATCH_HOLD: owned immutable production batch unavailable') from None
            if ((batch.batch_id, batch.revision, batch.tenant_id) != (ref.batch_id, ref.revision, s.tenant_id)
                    or batch.available_at > s.decision_at or batch.scope_start > s.period_start
                    or batch.scope_end < s.period_end or legacy.day(batch.production_start_at) > s.period_end):
                raise ValueError('BATCH_HOLD: production batch identity, availability or period differs')
            size += len(_raw(batch))
            if size > MAX_BYTES:
                raise ValueError('CAPACITY_HOLD: bounded owned production records required')
            batches.append(batch)
        declared = {p.batch_id: p for p in batches}
        if set(declared).intersection(lot.batch_id for lot in s.opening_inventory or ()):
            raise ValueError('BATCH_HOLD: opening saleable inventory cannot be a current production batch')
        for event in (*s.harvests, *(c for c in (*(s.variable_costs or ()), *(s.fixed_costs or ()))
                                     if c.purpose == 'production')):
            at = event.at if isinstance(event, contracts.Harvest) else event.incurred_at
            if event.batch_id not in declared or at < declared[event.batch_id].production_start_at:
                raise ValueError('BATCH_HOLD: event requires a declared batch and production chronology')
        return digest, market, inputs, tuple(batches)

    def calculate(self, scenario):
        _code_fence()
        try:
            s = BatchEconomicScenario.model_validate(contracts.untrusted_data(scenario))
            if len(_raw(s)) > MAX_BYTES:
                raise ValueError('CAPACITY_HOLD: bounded batch scenario required')
            digest, market, inputs, batches = before = self._context(s)
            try:
                with localcontext() as ctx:
                    ctx.prec = 128
                    ctx.traps[Inexact] = True
                    result = self._calculate_verified(s, market, inputs, digest)
                    summaries = self._summaries(s, result, batches)
            except Inexact:
                raise ValueError('economic arithmetic exceeds exact 128-digit domain') from None
            identity = {'scenario_sha256': digest, 'formula_version': FORMULA_VERSION,
                        'batch_records_sha256': sha256(_raw(batches)).hexdigest(),
                        'code_sha256': CODE_SHA256, 'component_sha256': COMPONENT_SHA256}
            result = replace(result, formula_version=FORMULA_VERSION,
                             result_id=sha256(_raw(identity)).hexdigest())
            output = ProductionBatchResult(result, batches, summaries, CODE_SHA256, dict(COMPONENT_SHA256))
            if len(result_bytes(output)) > MAX_BYTES:
                raise ValueError('CAPACITY_HOLD: bounded batch result required')
            if self._context(s) != before:
                raise ValueError('BATCH_HOLD: current owned context changed during calculation')
            return output
        finally:
            _code_fence()

    def _costs(self, events, scenario, harvested_batches, sales):
        return super()._costs(events, scenario, {p.batch_id for p in scenario.production_batches}, sales)

    @staticmethod
    def _summaries(s, result, batches):
        out = []
        harvested = {h.batch_id for h in s.harvests}
        for batch in batches:
            groups = [[c for c in group or () if c.purpose == 'production' and c.batch_id == batch.batch_id]
                      for group in (s.variable_costs, s.fixed_costs)]
            v, f = [None if amount is None else legacy.total(c.quantity.amount * c.unit_cost.amount for c in group)
                    for amount, group in zip((result.variable_cost, result.fixed_cost), groups, strict=True)]
            costs = groups[0] + groups[1]
            unknown = v is None or f is None or any(c.payment is None for c in costs)
            if unknown:
                paid = remaining = None
            else:
                paid = legacy.total(legacy.money(c.payment) for c in costs if legacy.in_period(c.paid_at, s))
                remaining = v + f - paid
                if remaining < 0:
                    raise ValueError('BATCH_HOLD: negative batch payable')
            out.append(ProductionBatchCosts(batch.batch_id, batch.revision,
                batch.batch_id in harvested, v, f, paid, remaining))
        return tuple(out)
