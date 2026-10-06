"""Pinned first-G1 joint user stress over an immutable economic ledger scenario.

The injected repository is a trusted server boundary. It must atomically persist
candidate bytes, numeric revisions, and the job pin; a request cannot supply it.
This module publishes no market snapshot, forecast, verified net price, or ranking.
"""

from copy import deepcopy
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from app.economic_contracts import (
    EconomicNumber, EconomicScenario, iter_economic_numbers,
    untrusted_data, utc,
)
from app.economics import EconomicLedger, EconomicResult, canonical_scenario_sha256, day
from app.market import UnavailableMarketContext, resolve_market_context
from app.provenance import Digest, FrozenContract, Name


def _json(value: object) -> str:
    def encode(item):
        if isinstance(item, (date, datetime)):
            return item.isoformat().replace("+00:00", "Z")
        raise TypeError("unsupported canonical value")
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=encode, allow_nan=False)


def _hash(value: object) -> str:
    return sha256(_json(value).encode("utf-8")).hexdigest()


def _parse(model, value):
    return model.model_validate_json(_json(untrusted_data(value)))


def _load(repository: object, method: str, *args):
    try:
        raw = getattr(repository, method)(*args)
    except Exception as exc:
        raise ValueError(f"trusted {method} lookup failed") from exc
    if raw is None:
        raise ValueError(f"trusted {method} reference missing")
    return untrusted_data(raw)


def _require_raw_identity(raw, tenant_id: str, id_field: str, record_id: str,
                          revision_field: str, revision: str):
    if (not isinstance(raw, dict) or
            (raw.get("tenant_id"), raw.get(id_field), raw.get(revision_field)) !=
            (tenant_id, record_id, revision)):
        raise ValueError("trusted reference ownership mismatch")
    return raw


class Rights(FrozenContract):
    use: Literal["allowed"]
    display: Literal["allowed"]
    redistribute: Literal["allowed", "denied"]


class BaselineRef(FrozenContract):
    scenario_id: Name
    revision: Name
    sha256: Digest


class ShockRef(FrozenContract):
    shock_id: Name
    revision: Name
    sha256: Digest


class MarketScenarioRequest(FrozenContract):
    schema_version: Literal["1"]
    baseline: BaselineRef
    shock: ShockRef
    decision_at: datetime
    market_context: UnavailableMarketContext

    _decision_utc = field_validator("decision_at")(utc)


class Edit(FrozenContract):
    event_group: Name
    event_id: Name
    field: Name
    number: EconomicNumber | None = None
    time: datetime | None = None
    reference: Name | None = None

    @field_validator("time")
    @classmethod
    def time_utc(cls, value):
        return utc(value) if value is not None else None

    @model_validator(mode="after")
    def one_value(self) -> Self:
        if sum(value is not None for value in (self.number, self.time, self.reference)) != 1:
            raise ValueError("edit needs exactly one explicit value")
        return self


class Driver(FrozenContract):
    kind: Literal["demand", "supply", "macro"]
    record_id: Name
    revision: Name
    origin: Literal["user"]
    evidence_level: Literal["assumed"]
    available_at: datetime
    effective_start: date
    effective_end: date
    rights: Rights
    hypothesis: str = Field(min_length=1)
    source_ref: Name
    causal_status: Literal["unvalidated_user_hypothesis"]
    changes: list[Edit]

    _available_utc = field_validator("available_at")(utc)

    @field_validator("hypothesis")
    @classmethod
    def nonblank_hypothesis(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("driver hypothesis must be user-authored text")
        return value


class ContractCap(FrozenContract):
    record_id: Name
    revision: Name
    contract_id: Name
    sale_ids: list[Name] = Field(min_length=1)
    grade: Name
    channel: Name
    accepted_kg: EconomicNumber
    origin: Literal["user"]
    evidence_level: Literal["assumed"]
    available_at: datetime
    effective_start: date
    effective_end: date
    rights: Rights

    _available_utc = field_validator("available_at")(utc)


class JointShockPin(FrozenContract):
    shock_id: Name
    revision: Name
    tenant_id: Name
    sha256: Digest
    immutable: Literal[True]


class BindingRef(FrozenContract):
    binding_id: Name
    revision: Name
    sha256: Digest


class JointShock(FrozenContract):
    schema_version: Literal["1"]
    shock_id: Name
    revision: Name
    tenant_id: Name
    baseline_sha256: Digest
    decision_at: datetime
    effective_start: date
    effective_end: date
    available_at: datetime
    origin: Literal["user"]
    evidence_level: Literal["assumed"]
    rights: Rights
    drivers: list[Driver]
    contract_caps: list[ContractCap]
    settlement_bindings: list[BindingRef]

    _times_utc = field_validator("decision_at", "available_at")(utc)


class InputRights(FrozenContract):
    input_id: Name
    revision: Name
    tenant_id: Name
    raw_sha256: Digest
    origin: Literal["user"]
    evidence_level: Literal["assumed"]
    rights: Rights
    available_at: datetime
    effective_start: date
    effective_end: date
    immutable: Literal[True]

    _available_utc = field_validator("available_at")(utc)


class Applicability(FrozenContract):
    binding_id: Name
    revision: Name
    tenant_id: Name
    setoff_id: Name
    sale_id: Name
    path_sha256: Digest
    settlement_ref: Name
    evidence_revision: Name
    evidence_sha256: Digest
    origin: Literal["user"]
    evidence_level: Literal["assumed"]
    available_at: datetime
    effective_start: date
    effective_end: date
    rights: Rights
    immutable: Literal[True]

    _available_utc = field_validator("available_at")(utc)


_FIELDS = {
    "harvests": {"quantity": "number", "at": "time"},
    "packouts": {"quantity": "number", "grade": "reference", "channel": "reference", "at": "time"},
    "culls": {"quantity": "number", "at": "time"},
    "cull_disposals": {"quantity": "number", "at": "time"},
    "sales": {"quantity": "number", "grade": "reference", "channel": "reference",
              "price": "number", "dispatch_at": "time",
              "delivery_at": "time", "inspection_at": "time", "recognized_at": "time"},
    "collections": {"amount": "number", "at": "time"},
    "returns": {"quantity": "number", "refund": "number", "at": "time", "refund_paid_at": "time"},
    "discounts": {"amount": "number", "at": "time"},
    "setoffs": {"amount": "number", "at": "time", "evidence_revision": "reference",
                "evidence_sha256": "reference"},
    "disposals": {"quantity": "number", "at": "time"},
    "variable_costs": {"quantity": "number", "unit_cost": "number", "payment": "number",
                       "incurred_at": "time", "paid_at": "time"},
    "fixed_costs": {"quantity": "number", "unit_cost": "number", "payment": "number",
                    "incurred_at": "time", "paid_at": "time"},
}

_DRIVER_GROUPS = {
    "supply": frozenset({"harvests", "packouts", "culls", "cull_disposals", "disposals"}),
    "demand": frozenset({"sales", "collections", "returns", "discounts"}),
    "macro": frozenset({"variable_costs", "fixed_costs", "setoffs"}),
}


def settlement_path_sha256(scenario: EconomicScenario, sale_id: str) -> str:
    """Bind every linked sale, return, deduction, collection, cost, and setoff field."""
    scenario = EconomicScenario.model_validate(untrusted_data(scenario))
    sale = next((item for item in scenario.sales if item.id == sale_id), None)
    if sale is None:
        raise ValueError("settlement applicability sale missing")
    linked = {"sale": sale.model_dump(mode="json")}
    for field in ("returns", "discounts", "collections", "variable_costs", "fixed_costs", "setoffs"):
        linked[field] = [item.model_dump(mode="json") for item in getattr(scenario, field) or ()
                         if item.sale_id == sale_id]
    return _hash(linked)


@dataclass(frozen=True)
class Candidate:
    status: Literal["pinned"]
    candidate_id: str
    baseline: BaselineRef
    joint_shock: ShockRef
    scenario_id: str
    revision: str
    economic_scenario_sha256: str
    rights_manifest_sha256: str
    binding_manifest_sha256: str
    immutable_job_input_ref: str
    market_context: UnavailableMarketContext


@dataclass(frozen=True)
class MarketScenarioHold:
    status: Literal["hold"]
    hold_reasons: tuple[str, ...]
    market_context: UnavailableMarketContext


@dataclass(frozen=True)
class MarketScenarioResult:
    result_id: str
    candidate_id: str
    baseline: BaselineRef
    joint_shock: ShockRef
    economic_scenario_sha256: str
    rights_manifest_sha256: str
    binding_manifest_sha256: str
    economic_result: EconomicResult
    economic_result_ids: tuple[str, ...]
    market_context: UnavailableMarketContext
    assessment_status: Literal["hold"]
    calculation_status: Literal["conditional_user_assumption", "hold"]
    hold_reasons: tuple[str, ...]


class _UnsupportedPath(Exception):
    pass


class _InventoryUnresolved(Exception):
    pass


class _PrePinRepository:
    def __init__(self, repository, scenario, record, new_records):
        self._repository = repository
        self._scenario = scenario
        self._record = record
        self._new_records = {(item["input_id"], item["revision"]): item for item in new_records}

    def __getattr__(self, name):
        return getattr(self._repository, name)

    def get_economic_input(self, input_id, revision):
        return self._new_records.get((input_id, revision)) or self._repository.get_economic_input(
            input_id, revision)

    def get_economic_scenario_pin(self, scenario_id, revision):
        if (scenario_id, revision) != (self._scenario.scenario_id, self._scenario.scenario_revision):
            return self._repository.get_economic_scenario_pin(scenario_id, revision)
        return {"tenant_id": self._scenario.tenant_id, "scenario_id": scenario_id,
                "scenario_revision": revision, "decision_at": self._scenario.decision_at,
                "payload_sha256": self._record["economic_scenario_sha256"],
                "immutable_job_input_ref": self._record["immutable_job_input_ref"],
                "immutable_job_input_sha256": self._record["economic_scenario_sha256"],
                "immutable": True}


class MarketScenarioService:
    def __init__(self, repository: object):
        self._repository = repository

    def _owned(self, tenant_id: str):
        if not isinstance(tenant_id, str) or not tenant_id or tenant_id != tenant_id.strip():
            raise ValueError("invalid authenticated tenant")
        if _load(self._repository, "tenant_is_authenticated", tenant_id) is not True:
            raise ValueError("tenant is not authenticated")

    @staticmethod
    def _scope(record, scenario):
        if (record.available_at > scenario.decision_at or
                record.effective_start > scenario.period_start or
                record.effective_end < scenario.period_end or
                record.effective_end < record.effective_start):
            raise ValueError("assumption rights or time outside decision scope")

    def _input_rights(self, value: EconomicNumber, scenario: EconomicScenario,
                      sale_dates: tuple[date, ...] | None = None):
        raw = _require_raw_identity(_load(
            self._repository, "get_input_rights", value.input_id, value.revision),
            scenario.tenant_id, "input_id", value.input_id, "revision", value.revision)
        record = _parse(InputRights, raw)
        if sale_dates is None:
            self._scope(record, scenario)
        elif (record.available_at > scenario.decision_at or
              record.effective_end < record.effective_start or
              any(not record.effective_start <= on <= record.effective_end for on in sale_dates)):
            raise ValueError("contract cap input rights outside sale recognition date")
        if (record.tenant_id, record.input_id, record.revision, record.raw_sha256,
                record.available_at) != (scenario.tenant_id, value.input_id, value.revision,
                                         _hash(value.model_dump(mode="python")), value.available_at):
            raise ValueError("economic input rights sidecar does not match immutable revision")
        return record.model_dump(mode="json")

    def _prepare(self, request_value, tenant_id):
        request = _parse(MarketScenarioRequest, request_value)
        self._owned(tenant_id)
        raw_baseline = _require_raw_identity(_load(
            self._repository, "get_economic_scenario", request.baseline.scenario_id,
            request.baseline.revision), tenant_id, "scenario_id",
            request.baseline.scenario_id, "scenario_revision", request.baseline.revision)
        baseline = _parse(EconomicScenario, raw_baseline)
        baseline_hash = canonical_scenario_sha256(baseline)
        if ((baseline.scenario_id, baseline.scenario_revision, baseline.tenant_id,
             baseline.decision_at, baseline_hash, baseline.market_context) !=
                (request.baseline.scenario_id, request.baseline.revision, tenant_id,
                 request.decision_at, request.baseline.sha256, request.market_context)
                or baseline.scenario_market_context != request.market_context):
            raise ValueError("baseline pin, tenant, or market hold mismatch")
        resolve_market_context(request.market_context, tenant_id=tenant_id,
                               decision_at=request.decision_at, repository=self._repository)
        baseline_ledger = EconomicLedger(self._repository).calculate(baseline)
        raw_shock = _require_raw_identity(_load(
            self._repository, "get_joint_shock", request.shock.shock_id,
            request.shock.revision), tenant_id, "shock_id",
            request.shock.shock_id, "revision", request.shock.revision)
        shock = _parse(JointShock, raw_shock)
        shock_hash = _hash(raw_shock)
        raw_pin = _require_raw_identity(_load(
            self._repository, "get_joint_shock_pin", request.shock.shock_id,
            request.shock.revision), tenant_id, "shock_id",
            request.shock.shock_id, "revision", request.shock.revision)
        pin = _parse(JointShockPin, raw_pin)
        if ((pin.shock_id, pin.revision, pin.tenant_id, pin.sha256) !=
                (shock.shock_id, shock.revision, tenant_id, shock_hash)):
            raise ValueError("joint shock independent immutable pin mismatch")
        if ((shock.shock_id, shock.revision, shock.tenant_id, shock.baseline_sha256,
             shock.decision_at, shock_hash) !=
                (request.shock.shock_id, request.shock.revision, tenant_id,
                 baseline_hash, request.decision_at, request.shock.sha256)):
            raise ValueError("joint shock immutable revision mismatch")
        self._scope(shock, baseline)
        if (len(shock.drivers) != 3 or {item.kind for item in shock.drivers} !=
                {"demand", "supply", "macro"} or any(not item.changes for item in shock.drivers)):
            raise ValueError("joint shock needs demand, supply, and macro records")
        records = [(item.record_id, item.revision) for item in (*shock.drivers, *shock.contract_caps)]
        if len(records) != len(set(records)):
            raise ValueError("duplicate joint assumption record")
        for item in shock.drivers:
            self._scope(item, baseline)
        if any(cap.available_at > baseline.decision_at or
               cap.effective_end < cap.effective_start for cap in shock.contract_caps):
            raise ValueError("contract cap outside decision scope")
        candidate_data = deepcopy(baseline.model_dump(mode="python"))
        seen_edits = set()
        new_records = []
        old_inputs = {(item.input_id, item.revision) for item in iter_economic_numbers(baseline)}
        lane_edits = set()
        for driver in shock.drivers:
            for edit in driver.changes:
                if edit.event_group not in _DRIVER_GROUPS[driver.kind]:
                    raise ValueError("joint shock driver kind does not match event group")
                kind = _FIELDS.get(edit.event_group, {}).get(edit.field)
                if kind is None or getattr(edit, kind) is None:
                    raise ValueError("unsupported event field or edit type")
                key = (edit.event_group, edit.event_id, edit.field)
                if key in seen_edits:
                    raise ValueError("duplicate event edit")
                seen_edits.add(key)
                group = candidate_data[edit.event_group]
                if group is None:
                    raise _UnsupportedPath()
                matches = [item for item in group if item["id"] == edit.event_id]
                if len(matches) != 1:
                    raise _UnsupportedPath()
                target = matches[0]
                if kind == "reference" and edit.field in {"grade", "channel"}:
                    lane_edits.add((edit.event_group, edit.event_id))
                if kind == "number":
                    previous = target.get(edit.field)
                    if (edit.number.input_id, edit.number.revision) in old_inputs:
                        raise ValueError("edited number needs a new immutable input revision")
                    if previous is not None and (edit.number.input_id != previous["input_id"] or
                                                 edit.number.unit != previous["unit"]):
                        raise ValueError("edited input identity or unit changed")
                    target[edit.field] = edit.number.model_dump(mode="python")
                    new_records.append({**target[edit.field], "tenant_id": tenant_id,
                                        "scope_start": baseline.period_start,
                                        "scope_end": baseline.period_end})
                else:
                    target[edit.field] = getattr(edit, kind)
        if len({(item["input_id"], item["revision"]) for item in new_records}) != len(new_records):
            raise ValueError("duplicate replacement input revision")
        if any(sale["quantity"]["value"] == "0" for sale in candidate_data["sales"]):
            raise _UnsupportedPath()
        seed = _hash({"baseline": baseline_hash, "shock": shock_hash})
        candidate_data["scenario_id"] = f"market-{seed[:32]}"
        candidate_data["scenario_revision"] = "r1"
        derived = EconomicScenario.model_validate(candidate_data)
        if lane_edits:
            allowed_lanes = {(item.grade, item.channel) for item in baseline.packouts}
            allowed_lanes.update((item.grade, item.channel) for item in baseline.opening_inventory or ()
                                 if item.grade is not None and item.channel is not None)
            for group, event_id in lane_edits:
                event = next(item for item in getattr(derived, group) if item.id == event_id)
                if (event.grade, event.channel) not in allowed_lanes:
                    raise ValueError("revised grade/channel lane absent from immutable baseline")
        rights = [self._input_rights(item, derived) for item in iter_economic_numbers(derived)]
        numeric_keys = old_inputs | {(item.input_id, item.revision)
                                     for item in iter_economic_numbers(derived)}
        sale_by_id = {sale.id: sale for sale in derived.sales}
        for cap in shock.contract_caps:
            if cap.accepted_kg.unit != "kg" or cap.accepted_kg.amount <= 0:
                raise ValueError("contract cap must be positive kg")
            key = (cap.accepted_kg.input_id, cap.accepted_kg.revision)
            if key in numeric_keys:
                raise ValueError("contract cap needs its own numeric input revision")
            numeric_keys.add(key)
            sale_dates = tuple(day(sale_by_id[sale_id].recognized_at)
                               for sale_id in cap.sale_ids if sale_id in sale_by_id)
            rights.append(self._input_rights(cap.accepted_kg, derived, sale_dates))
        self._check_caps(shock, derived)
        bindings = self._check_bindings(shock, baseline, derived)
        rights_manifest = _hash({"numeric": sorted(rights, key=lambda x: (x["input_id"], x["revision"])),
                                 "shock": shock.rights.model_dump(mode="json"),
                                 "drivers": [d.model_dump(mode="json", exclude={"changes"}) for d in shock.drivers],
                                 "caps": [c.model_dump(mode="json", exclude={"accepted_kg"}) for c in shock.contract_caps]})
        binding_manifest = _hash(bindings)
        identity = _hash({"baseline": baseline_hash, "shock": shock_hash,
                          "rights": rights_manifest, "bindings": binding_manifest})
        candidate_data["scenario_id"] = f"market-{identity[:32]}"
        derived = EconomicScenario.model_validate(candidate_data)
        EconomicLedger(self._repository)._verify_settlement_evidence(derived)
        if baseline_ledger.closing_inventory is None:
            raise _InventoryUnresolved()
        economic_hash = canonical_scenario_sha256(derived)
        candidate_id = _hash({"shock": (shock.shock_id, shock.revision, shock_hash),
                              "rights": rights_manifest, "bindings": binding_manifest,
                              "economic_scenario": economic_hash})
        job_ref = f"market-job-{candidate_id[:32]}"
        record = {"candidate_id": candidate_id, "tenant_id": tenant_id,
                  "request": request.model_dump(mode="python"),
                  "scenario_id": derived.scenario_id, "revision": derived.scenario_revision,
                  "economic_scenario_sha256": economic_hash,
                  "shock_sha256": shock_hash, "rights_manifest_sha256": rights_manifest,
                  "binding_manifest_sha256": binding_manifest,
                  "immutable_job_input_ref": job_ref,
                  "immutable_job_input_sha256": economic_hash,
                  "market_hold_report_id": request.market_context.hold_report_id,
                  "immutable": True}
        if lane_edits:
            preflight = EconomicLedger(_PrePinRepository(
                self._repository, derived, record, new_records)).calculate(derived)
            if preflight.closing_inventory is None:
                raise _InventoryUnresolved()
        return request, derived, record, new_records

    @staticmethod
    def _check_caps(shock, scenario):
        assigned = {}
        contracts = set()
        for cap in shock.contract_caps:
            if cap.contract_id in contracts:
                raise ValueError("duplicate contract identity")
            contracts.add(cap.contract_id)
            if len(cap.sale_ids) != len(set(cap.sale_ids)):
                raise ValueError("duplicate contract cap sale")
            for sale_id in cap.sale_ids:
                if sale_id in assigned:
                    raise ValueError("duplicate contract cap sale")
                assigned[sale_id] = cap
        sale_ids = {sale.id for sale in scenario.sales}
        if set(assigned) != sale_ids:
            raise ValueError("contract cap assignment must cover each sale exactly once")
        totals = {cap.contract_id: Decimal(0) for cap in shock.contract_caps}
        for sale in scenario.sales:
            cap = assigned[sale.id]
            if ((sale.grade, sale.channel) != (cap.grade, cap.channel) or
                    not cap.effective_start <= day(sale.recognized_at) <= cap.effective_end):
                raise ValueError("sale exceeds assumed contract cap or scope")
            totals[cap.contract_id] += sale.quantity.amount
            if totals[cap.contract_id] > cap.accepted_kg.amount:
                raise ValueError("sale exceeds assumed contract cap")

    def _check_bindings(self, shock, baseline, derived):
        refs = {ref.binding_id: ref for ref in shock.settlement_bindings}
        if len(refs) != len(shock.settlement_bindings):
            raise ValueError("duplicate settlement applicability")
        resolved = []
        for ref in shock.settlement_bindings:
            raw = _require_raw_identity(_load(
                self._repository, "get_settlement_applicability", ref.binding_id, ref.revision),
                derived.tenant_id, "binding_id", ref.binding_id, "revision", ref.revision)
            binding = _parse(Applicability, raw)
            self._scope(binding, derived)
            if (binding.binding_id, binding.revision, binding.tenant_id,
                    _hash(binding.model_dump(mode="python"))) != (
                    ref.binding_id, ref.revision, derived.tenant_id, ref.sha256):
                raise ValueError("settlement applicability revision or rights mismatch")
            resolved.append(binding)
        original = {item.id: item for item in baseline.setoffs or ()}
        for item in derived.setoffs or ():
            if item.amount.amount == Decimal(0):
                continue
            changed = settlement_path_sha256(baseline, item.sale_id) != settlement_path_sha256(derived, item.sale_id)
            if not changed:
                continue
            matched = [b for b in resolved if b.setoff_id == item.id and b.sale_id == item.sale_id]
            if (len(matched) != 1 or item.id not in original or
                    item.evidence_revision == original[item.id].evidence_revision or
                    matched[0].revision == original[item.id].evidence_revision):
                raise ValueError("changed sale or fee needs fresh settlement applicability")
            binding = matched[0]
            if ((binding.path_sha256, binding.settlement_ref, binding.evidence_revision,
                 binding.evidence_sha256) !=
                    (settlement_path_sha256(derived, item.sale_id), item.settlement_ref,
                     item.evidence_revision, item.evidence_sha256)):
                raise ValueError("settlement applicability does not bind revised path")
        applicable = {(item.id, item.sale_id) for item in derived.setoffs or ()
                      if item.amount.amount != Decimal(0)}
        if any((item.setoff_id, item.sale_id) not in applicable for item in resolved):
            raise ValueError("settlement applicability is not linked to a live nonzero setoff")
        return [item.model_dump(mode="json") for item in resolved]

    def build_candidate(self, request, authenticated_tenant_id: str):
        try:
            parsed, scenario, record, new_records = self._prepare(request, authenticated_tenant_id)
        except _UnsupportedPath:
            parsed = _parse(MarketScenarioRequest, request)
            return MarketScenarioHold("hold", ("UNSUPPORTED_PATH",), parsed.market_context)
        except _InventoryUnresolved:
            parsed = _parse(MarketScenarioRequest, request)
            return MarketScenarioHold("hold", ("INVENTORY_UNRESOLVED",), parsed.market_context)
        try:
            pinned = self._repository.pin_market_candidate(
                deepcopy(record), scenario.model_dump(mode="python"), deepcopy(new_records))
        except Exception as exc:
            raise ValueError("trusted candidate pin failed") from exc
        if pinned is not True:
            raise ValueError("candidate pin was not committed")
        if (_json(_load(self._repository, "get_market_candidate", scenario.scenario_id,
                       scenario.scenario_revision)) != _json(record) or
                canonical_scenario_sha256(_parse(EconomicScenario, _require_raw_identity(_load(
                    self._repository, "get_economic_scenario", scenario.scenario_id,
                    scenario.scenario_revision), authenticated_tenant_id, "scenario_id",
                    scenario.scenario_id, "scenario_revision",
                    scenario.scenario_revision))) != record["economic_scenario_sha256"]):
            raise ValueError("candidate readback differs from immutable job input")
        EconomicLedger(self._repository)._verify_scenario_pin(scenario)
        return Candidate("pinned", record["candidate_id"], parsed.baseline, parsed.shock,
                         scenario.scenario_id, scenario.scenario_revision,
                         record["economic_scenario_sha256"], record["rights_manifest_sha256"],
                         record["binding_manifest_sha256"], record["immutable_job_input_ref"],
                         parsed.market_context)

    def validate_pinned(self, scenario_id: str, revision: str, authenticated_tenant_id: str):
        read_scope = getattr(self._repository, 'read_scope', None)
        with read_scope(authenticated_tenant_id) if callable(read_scope) else nullcontext():
            return self._validate_pinned(scenario_id, revision, authenticated_tenant_id)

    def _validate_pinned(self, scenario_id: str, revision: str, authenticated_tenant_id: str):
        self._owned(authenticated_tenant_id)
        stored = _load(self._repository, "get_market_candidate", scenario_id, revision)
        if not isinstance(stored, dict) or stored.get("tenant_id") != authenticated_tenant_id:
            raise ValueError("foreign or malformed candidate pin")
        request, derived, expected, _ = self._prepare(stored.get("request"), authenticated_tenant_id)
        if (_json(stored) != _json(expected) or
                (scenario_id, revision) != (derived.scenario_id, derived.scenario_revision)):
            raise ValueError("candidate, shock, rights, or job pin changed")
        actual = _parse(EconomicScenario, _require_raw_identity(_load(
            self._repository, "get_economic_scenario", scenario_id, revision),
            authenticated_tenant_id, "scenario_id", scenario_id,
            "scenario_revision", revision))
        if canonical_scenario_sha256(actual) != expected["economic_scenario_sha256"]:
            raise ValueError("derived economic scenario changed")
        return request, actual, expected

    def calculate_pinned(self, scenario_id: str, revision: str, authenticated_tenant_id: str):
        request, actual, expected = self.validate_pinned(scenario_id, revision, authenticated_tenant_id)
        ledger = EconomicLedger(self._repository).calculate(actual)
        result_id = _hash({"candidate": expected["candidate_id"],
                           "shock": expected["shock_sha256"],
                           "rights": expected["rights_manifest_sha256"],
                           "bindings": expected["binding_manifest_sha256"],
                           "economic_scenario": expected["economic_scenario_sha256"],
                           "economic_result": ledger.result_id})
        conditional = ledger.management_oi is not None and ledger.operating_cash is not None
        reasons = tuple(dict.fromkeys((*ledger.hold_reasons,
            *(item.hold_reason for item in ledger.sale_net_remittances if item.hold_reason))))
        return MarketScenarioResult(result_id, expected["candidate_id"], request.baseline,
                                    request.shock, expected["economic_scenario_sha256"],
                                    expected["rights_manifest_sha256"],
                                    expected["binding_manifest_sha256"], ledger,
                                    (ledger.result_id,), request.market_context, "hold",
                                    "conditional_user_assumption" if conditional else "hold",
                                    reasons)
