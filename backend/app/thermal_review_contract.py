"""Bind a CLI collection review to the signed synthetic thermal snapshot."""

from .cli_contracts import (DecisionContract, DecisionPlan, ProposalHold, _canonical,
                            parse_stage_input)
from .thermal_publisher import collection_review_input, collection_review_proposal


class ThermalReviewContract(DecisionContract):
    VERSION = "thermal-review-server-v2"
    BINDING_FIELDS = frozenset({"snapshot_id", "manifest_sha256", "weather_sha256",
                                "thermal_sha256", "context_sha256"})
    INPUT_FIELDS = BINDING_FIELDS | frozenset({
        "input_version", "decision_context_id", "decision_at_utc", "claim_mode",
        "decision_time_kind"})

    def __init__(self, run_store, authority_resolver):
        self.run_store = run_store
        super().__init__(authority_resolver, input_parser=self._parse_input)

    def binding_fields(self, job):
        return self.BINDING_FIELDS

    def _verified_sources(self, job, value):
        if (job.get("stage") != "collection_review" or type(value) is not dict or
                set(value) != self.INPUT_FIELDS or
                value.get("input_version") != "thermal-g1-collection-review-input-v1" or
                _canonical(value) != job.get("input_bytes") or
                type(value["snapshot_id"]) is not str or
                type(value["decision_context_id"]) is not str):
            raise ProposalHold("thermal_input_mismatch")
        try:
            snapshot = self.run_store.get_snapshot(job["tenant_id"], value["snapshot_id"])
            context = self.run_store.get_decision_context(
                job["tenant_id"], value["snapshot_id"], value["decision_context_id"])
        except Exception as exc:
            raise ProposalHold("thermal_authority_unavailable") from exc
        if (snapshot is None or context is None or
                value != collection_review_input(snapshot, context)):
            raise ProposalHold("thermal_input_mismatch")
        return snapshot, context

    def _parse_input(self, job, value):
        self._verified_sources(job, value)
        return {**value, "candidate_ids": [value["snapshot_id"]], "evidence_refs": []}

    def plan(self, job, final_output: bytes) -> DecisionPlan:
        plan = super().plan(job, final_output)
        if plan.disposition == "hold":
            return plan
        value = parse_stage_input(job["input_bytes"], job, custom_parser=self._parse_input)
        snapshot, context = self._verified_sources(job, {
            key: value[key] for key in self.INPUT_FIELDS})
        proposal = _canonical(collection_review_proposal(snapshot, context))
        return DecisionPlan("proceed", proposal, plan.code)
