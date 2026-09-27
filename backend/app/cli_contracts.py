"""Server-side contracts for proposals produced by the Codex CLI worker.

The authority resolver is a trusted server dependency. A CLI answer and a caller's
input references never grant source rights, gate status, or publication authority.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Callable, Mapping

from jsonschema import Draft202012Validator


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "contracts" / "decision-v1.schema.json"
SCHEMA_BYTES = SCHEMA_PATH.read_bytes()
DECISION_SCHEMA = json.loads(SCHEMA_BYTES)
Draft202012Validator.check_schema(DECISION_SCHEMA)
_VALIDATOR = Draft202012Validator(DECISION_SCHEMA)
STAGES = frozenset({"research", "collection_review", "assessment"})
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
_COMMON = frozenset({"input_version", "tenant_id", "candidate_ids", "evidence_refs",
                     "decision_context_id", "decision_at_utc", "claim_mode",
                     "decision_time_kind"})
_STAGE_FIELDS = {
    "research": frozenset({"point", "period_start_utc", "period_end_utc",
                           "provider_ids", "goal_id"}),
    "collection_review": frozenset({"collection_plan_id", "record_sha256",
                                    "qc_report_id", "rights_evidence_id", "snapshot_id"}),
    "assessment": frozenset({"run_id", "economic_result_id", "profile_id",
                             "gate_evidence_ids"}),
}


class ProposalHold(ValueError):
    """A bounded, non-secret reason why a proposal cannot become a decision."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ProposalHold("duplicate_json_key")
        value[key] = item
    return value


def _json(data: bytes):
    if type(data) is not bytes or len(data) > 1048576:
        raise ProposalHold("invalid_json_size")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_unique_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise ProposalHold("invalid_json") from exc


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _id(value):
    return type(value) is str and _ID.fullmatch(value) is not None


def _digest(value):
    return type(value) is str and _DIGEST.fullmatch(value) is not None


def _utc(value):
    if type(value) is not str or not _UTC.fullmatch(value):
        raise ProposalHold("invalid_utc")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ProposalHold("invalid_utc") from exc


def _ids(value, *, maximum=100):
    if (type(value) is not list or len(value) > maximum or
            any(not _id(item) for item in value) or len(set(value)) != len(value)):
        raise ProposalHold("invalid_ids")
    return frozenset(value)


def _context(value):
    keys = ("decision_context_id", "decision_at_utc", "claim_mode",
            "decision_time_kind")
    values = tuple(value.get(key) for key in keys)
    if values == (None, None, None, None):
        return
    if (any(item is None for item in values) or not _id(values[0]) or
            values[2] not in ("ex_ante", "ex_post_replay") or
            values[3] not in ("actual", "hypothetical")):
        raise ProposalHold("invalid_decision_context")
    _utc(values[1])


def parse_stage_input(raw: bytes, job: Mapping, *, custom_parser=None) -> dict:
    """Parse only a versioned input; unfamiliar versions need a trusted parser."""
    if sha256(raw).hexdigest() != job.get("input_sha256"):
        raise ProposalHold("input_hash_mismatch")
    value = _json(raw)
    stage = job.get("stage")
    if type(value) is not dict or stage not in STAGES:
        raise ProposalHold("invalid_stage_input")
    expected_version = stage + "_input_v1"
    if value.get("input_version") != expected_version:
        if custom_parser is None:
            raise ProposalHold("unknown_input_version")
        try:
            parsed = custom_parser(job, value)
        except Exception as exc:
            raise ProposalHold("unknown_input_version") from exc
        if type(parsed) is not dict or parsed.get("input_version") != value.get("input_version"):
            raise ProposalHold("unknown_input_version")
        return parsed
    if set(value) != _COMMON | _STAGE_FIELDS[stage] or value.get("tenant_id") != job.get("tenant_id"):
        raise ProposalHold("input_scope_mismatch")
    candidates = _ids(value["candidate_ids"])
    refs = value["evidence_refs"]
    if (type(refs) is not list or len(refs) > 100 or any(type(ref) is not dict or
            set(ref) != {"id", "sha256"} or not _id(ref["id"]) or
            not _digest(ref["sha256"]) for ref in refs) or
            len({ref["id"] for ref in refs}) != len(refs)):
        raise ProposalHold("invalid_evidence_refs")
    _context(value)
    if stage == "research":
        point = value["point"]
        if (type(point) is not dict or set(point) != {"latitude", "longitude"} or
                any(type(point[key]) not in (int, float) for key in point) or
                not -90 <= point["latitude"] <= 90 or
                not -180 <= point["longitude"] <= 180 or
                not _id(value["goal_id"])):
            raise ProposalHold("invalid_research_scope")
        if (_utc(value["period_start_utc"]) >= _utc(value["period_end_utc"]) or
                not _ids(value["provider_ids"]) <= candidates):
            raise ProposalHold("invalid_research_scope")
    elif stage == "collection_review":
        if (not all(_id(value[key]) for key in ("collection_plan_id", "qc_report_id",
                                             "rights_evidence_id", "snapshot_id")) or
                not _digest(value["record_sha256"]) or
                not {value["qc_report_id"], value["rights_evidence_id"]} <=
                {ref["id"] for ref in refs}):
            raise ProposalHold("invalid_collection_scope")
    else:
        if (not all(_id(value[key]) for key in ("run_id", "economic_result_id", "profile_id"))
                or not _ids(value["gate_evidence_ids"]) <= {ref["id"] for ref in refs}):
            raise ProposalHold("invalid_assessment_scope")
    return value


@dataclass(frozen=True)
class EvidenceGrant:
    evidence_id: str
    tenant_id: str
    sha256: str
    intended_use: str
    rights_ok: bool
    qc_ok: bool
    available_at_utc: str | None


@dataclass(frozen=True)
class AuthoritySnapshot:
    tenant_id: str
    stage: str
    input_sha256: str
    candidate_ids: frozenset[str]
    evidence: Mapping[str, EvidenceGrant]
    allow_proceed: bool
    missing_evidence: tuple[str, ...]
    approved_claims: Mapping[str, tuple[str, ...]]
    g3a_candidate_ids: frozenset[str]
    g3b_ok: bool
    stage_bindings: Mapping[str, object]
    decision_context_id: str | None
    decision_at_utc: str | None
    claim_mode: str | None
    decision_time_kind: str | None


@dataclass(frozen=True)
class DecisionPlan:
    disposition: str
    artifact: bytes
    code: str


class DecisionContract:
    VERSION = "decision-server-v1"

    def __init__(self, authority_resolver: Callable, *, input_parser=None):
        if not callable(authority_resolver):
            raise TypeError("trusted authority resolver is required")
        self.authority_resolver = authority_resolver
        self.input_parser = input_parser

    def input_context(self, job):
        raw = job.get("input_bytes")
        if type(raw) is not bytes:
            raise ProposalHold("input_unavailable")
        value = parse_stage_input(raw, job, custom_parser=self.input_parser)
        try:
            authority = self.authority_resolver(job, value)
        except Exception as exc:
            raise ProposalHold("authority_unavailable") from exc
        if (not isinstance(authority, AuthoritySnapshot) or
                (authority.tenant_id, authority.stage, authority.input_sha256) !=
                (job["tenant_id"], job["stage"], job["input_sha256"])):
            raise ProposalHold("authority_scope_mismatch")
        _context({"decision_context_id": authority.decision_context_id,
                  "decision_at_utc": authority.decision_at_utc,
                  "claim_mode": authority.claim_mode,
                  "decision_time_kind": authority.decision_time_kind})
        for key in ("decision_context_id", "decision_at_utc", "claim_mode",
                    "decision_time_kind"):
            if value.get(key) != getattr(authority, key):
                raise ProposalHold("decision_context_mismatch")
        if not set(value.get("candidate_ids", [])) <= authority.candidate_ids:
            raise ProposalHold("candidate_scope_mismatch")
        required_bindings = _STAGE_FIELDS[job["stage"]]
        if (set(authority.stage_bindings) != required_bindings or
                any(value.get(key) != authority.stage_bindings[key]
                    for key in required_bindings)):
            raise ProposalHold("stage_identity_mismatch")
        for ref in value.get("evidence_refs", []):
            grant = authority.evidence.get(ref["id"])
            if (not isinstance(grant, EvidenceGrant) or grant.evidence_id != ref["id"] or
                    grant.tenant_id != job["tenant_id"] or grant.sha256 != ref["sha256"] or
                    grant.intended_use != job["stage"] or
                    grant.rights_ok is not True or grant.qc_ok is not True):
                raise ProposalHold("evidence_scope_mismatch")
            if grant.available_at_utc is not None:
                available = _utc(grant.available_at_utc)
                if authority.decision_at_utc is None and authority.allow_proceed:
                    raise ProposalHold("decision_time_missing")
                if (authority.claim_mode == "ex_ante" and authority.decision_at_utc is not None
                        and available > _utc(authority.decision_at_utc)):
                    raise ProposalHold("late_evidence")
        if (len(authority.missing_evidence) > 50 or
                any(not _id(item) for item in authority.missing_evidence) or
                len(set(authority.missing_evidence)) != len(authority.missing_evidence)):
            raise ProposalHold("invalid_authority_missing")
        return value, authority

    def plan(self, job, final_output: bytes) -> DecisionPlan:
        value = _json(final_output)
        if type(value) is not dict or not _VALIDATOR.is_valid(value):
            raise ProposalHold("invalid_decision_schema")
        context, authority = self.input_context(job)
        if (value["stage"] != job["stage"] or
                value["input_sha256"] != job["input_sha256"] or
                not _digest(value["input_sha256"])):
            raise ProposalHold("decision_scope_mismatch")
        for key in ("decision_context_id", "decision_at_utc", "claim_mode",
                    "decision_time_kind"):
            if value[key] != context.get(key):
                raise ProposalHold("decision_context_mismatch")
        if (type(value["reason"]) is not str or not 1 <= len(value["reason"]) <= 1000 or
                any(ord(char) < 32 and char not in "\n\t" for char in value["reason"])):
            raise ProposalHold("invalid_reason")
        selected = _ids(value["selected_ids"])
        rejected = _ids(value["rejected_ids"])
        missing = _ids(value["missing_evidence"], maximum=50)
        if (selected & rejected or not selected | rejected <=
                set(context.get("candidate_ids", [])) & authority.candidate_ids):
            raise ProposalHold("candidate_scope_mismatch")
        if job["stage"] == "research" and not selected <= set(context["provider_ids"]):
            raise ProposalHold("provider_scope_mismatch")
        if (missing != frozenset(authority.missing_evidence) or
                value["missing_evidence"] != list(authority.missing_evidence)):
            raise ProposalHold("missing_evidence_mismatch")
        if len(value["claims"]) > 50:
            raise ProposalHold("too_many_claims")
        for claim in value["claims"]:
            if (type(claim["claim"]) is not str or
                    not 1 <= len(claim["claim"]) <= 1000 or
                    type(claim["uncertainty"]) is not str or
                    not 1 <= len(claim["uncertainty"]) <= 500 or
                    not _ids(claim["evidence_ids"]) or
                    tuple(claim["evidence_ids"]) !=
                    authority.approved_claims.get(claim["claim"]) or
                    not set(claim["evidence_ids"]) <=
                    {ref["id"] for ref in context.get("evidence_refs", [])}):
                raise ProposalHold("unapproved_claim")
        if value["proposed_status"] == "proceed":
            if (not authority.allow_proceed or missing or not selected or
                    authority.decision_context_id is None):
                raise ProposalHold("gate_hold")
            if job["stage"] == "assessment" and (
                    not selected <= authority.g3a_candidate_ids or
                    not authority.g3b_ok):
                raise ProposalHold("assessment_gate_hold")
            artifact = _canonical({"schema_version": "decision_validated_v1",
                                   "stage": job["stage"],
                                   "input_sha256": job["input_sha256"],
                                   "selected_ids": sorted(selected),
                                   "rejected_ids": sorted(rejected),
                                   "decision_context_id": context.get("decision_context_id"),
                                   "decision_at_utc": context.get("decision_at_utc"),
                                   "claim_mode": context.get("claim_mode"),
                                   "decision_time_kind": context.get("decision_time_kind")})
            return DecisionPlan("proceed", artifact, "validated_proposal")
        if selected:
            raise ProposalHold("held_selection")
        artifact = _canonical({"schema_version": "hold_v1",
                               "reason_code": "evidence_missing" if missing else "decision_held",
                               "missing_evidence": list(authority.missing_evidence)})
        return DecisionPlan("hold", artifact, "validated_hold")

    def __call__(self, job, final_output: bytes, proposed_artifact: bytes):
        try:
            plan = self.plan(job, final_output)
        except ProposalHold as exc:
            return {"passed": False, "version": self.VERSION, "code": exc.code,
                    "disposition": None}
        if proposed_artifact != plan.artifact:
            return {"passed": False, "version": self.VERSION,
                    "code": "artifact_mismatch", "disposition": None}
        result = {"passed": True, "version": self.VERSION, "code": plan.code,
                  "disposition": plan.disposition}
        if plan.disposition == "hold":
            result["hold_report"] = plan.artifact
        return result
