"""Server authority for G0 registration, review, revocation, and decisions."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4

from app.g0_store import G0Store, ReviewProof, _scope_digest
from app.gates import CheckEvidence, G0Policy, RightEvidence, SourceEvidence, evaluate_g0
from app.provenance import SourceRecord


class G0Authority:
    def __init__(self, store: G0Store):
        self.store = store

    def _principal(self, tenant: str, scope: str) -> str:
        principal = self.store.principal_provider()
        scopes = principal.get("scopes") if isinstance(principal, dict) else None
        if (not isinstance(principal, dict) or principal.get("authenticated") is not True or
                principal.get("tenant_id") != tenant or not isinstance(tenant, str) or
                not tenant or len(tenant) > 200 or tenant != tenant.strip() or
                any(ord(char) < 32 for char in tenant) or
                not isinstance(principal.get("subject"), str) or
                not principal["subject"] or principal["subject"] != principal["subject"].strip() or
                any(ord(char) < 32 for char in principal["subject"]) or
                not isinstance(scopes, (set, frozenset, tuple, list)) or scope not in scopes):
            raise PermissionError("G0 authority denied")
        return principal["subject"]

    @staticmethod
    def _deadline(valid_to: datetime, now: datetime) -> None:
        if not isinstance(valid_to, datetime) or valid_to.utcoffset() != timedelta(0) or valid_to <= now:
            raise ValueError("G0 approval needs a future UTC expiry")

    def register_record(self, tenant: str, record: SourceRecord) -> None:
        self._principal(tenant, "g0_ingest")
        record = SourceRecord.model_validate(record.model_dump())
        raw = self.store.raw_reader(tenant, record.raw_sha256)
        if not isinstance(raw, bytes) or sha256(raw).hexdigest() != record.raw_sha256:
            raise ValueError("raw content address is unavailable or mismatched")
        with self.store.connect() as conn:
            self.store._lock(conn, tenant)
            self.store._append(conn, tenant=tenant, kind="record", entry_id=record.record_id,
                record_id=record.record_id, value=record.model_dump(mode="json"))

    def approve_policy(self, tenant: str, proposal: G0Policy) -> G0Policy:
        reviewer = self._principal(tenant, "g0_policy")
        proposal = G0Policy.model_validate(proposal.model_dump())
        now = datetime.now(timezone.utc)
        server_fields = dict(required_times=tuple(dict.fromkeys((*proposal.required_times,
            "observed_at", "published_at", "available_at"))), reviewer=reviewer,
            authenticated=True, approved=True, approved_at=now,
            available_at=now, revoked_at=None)
        draft = proposal.model_copy(update=server_fields)
        data = draft.model_dump(exclude={"policy_digest"}, warnings="error")
        policy = G0Policy(policy_digest=draft.content_digest(), **data)
        with self.store.connect() as conn:
            self.store._lock(conn, tenant)
            rows = conn.execute("""
                SELECT * FROM {} WHERE tenant_id = %s AND kind = 'policy'
                    AND scope_digest = %s AND action = %s AND intended_use = %s
                ORDER BY generation DESC
            """.format(self.store._table().as_string(conn)),
                (tenant, _scope_digest(policy.scope), policy.intended_action, policy.intended_use)).fetchall()
            for row in rows:
                old = self.store._model(row, G0Policy)
                if old.policy_version == policy.policy_version:
                    raise ValueError("G0 policy version already exists")
            generation = len(rows) + 1
            self.store._append(conn, tenant=tenant, kind="policy", entry_id=policy.policy_id,
                value=policy.model_dump(mode="json"), scope_digest=_scope_digest(policy.scope),
                action=policy.intended_action, intended_use=policy.intended_use,
                generation=generation)
        return policy

    def _record(self, conn, tenant: str, record_id: str) -> SourceRecord:
        record = self.store._model(self.store._one(conn, tenant, "record", record_id), SourceRecord)
        if record is None:
            raise ValueError("G0 record is unavailable")
        return record

    def _proof_common(self, record: SourceRecord, reviewer: str, evidence_id: str,
                      now: datetime, valid_to: datetime) -> dict:
        self._deadline(valid_to, now)
        return dict(evidence_id=evidence_id, record_id=record.record_id, scope=record.scope,
            revision_id=record.revision_id, raw_sha256=record.raw_sha256, reviewer=reviewer,
            authenticated=True, approved=True, approved_at=now, available_at=now,
            valid_from=now, valid_to=valid_to, revoked_at=None)

    def _review(self, tenant: str, record: SourceRecord, reviewer: str, kind: str,
                evidence_id: str, *, variable: str | None = None,
                check_name: str | None = None, check_version: str | None = None,
                action: str | None = None, use: str | None = None) -> ReviewProof:
        try:
            candidate = self.store.review_resolver(tenant, evidence_id)
        except Exception as exc:
            raise PermissionError("independent G0 review proof is unavailable") from exc
        if not isinstance(candidate, ReviewProof):
            raise PermissionError("independent G0 review proof is unavailable")
        try:
            proof = ReviewProof.model_validate(candidate.model_dump(warnings="error"))
        except Exception as exc:
            raise PermissionError("independent G0 review proof is invalid") from exc
        if (proof.tenant_id != tenant or proof.kind != kind or proof.evidence_id != evidence_id or
                proof.record_id != record.record_id or proof.scope != record.scope or
                proof.revision_id != record.revision_id or proof.raw_sha256 != record.raw_sha256 or
                proof.reviewer != reviewer or proof.variable != variable or
                proof.check_name != check_name or proof.check_version != check_version or
                proof.action != action or proof.use != use or
                (kind == "right" and proof.conditions_met is not True)):
            raise PermissionError("independent G0 review proof scope or purpose mismatch")
        return proof

    @staticmethod
    def _review_value(review, proof: ReviewProof) -> dict:
        return {"review": review.model_dump(mode="json"), "proof_binding": proof.binding()}

    def approve_source(self, tenant: str, record_id: str, *, valid_to: datetime) -> SourceEvidence:
        reviewer = self._principal(tenant, "g0_source")
        with self.store.connect() as conn:
            self.store._lock(conn, tenant)
            record = self._record(conn, tenant, record_id)
            if record.source_reviewer != reviewer or record.source_evidence_id is None:
                raise PermissionError("source reviewer identity does not match")
            resolved = self._review(tenant, record, reviewer, "source", record.source_evidence_id)
            now = datetime.now(timezone.utc)
            proof = SourceEvidence(**self._proof_common(record, reviewer,
                record.source_evidence_id, now, valid_to))
            self.store._append(conn, tenant=tenant, kind="source", entry_id=proof.evidence_id,
                record_id=record_id, value=self._review_value(proof, resolved))
            return proof

    def approve_check(self, tenant: str, record_id: str, variable: str, check_name: str,
                      *, valid_to: datetime) -> CheckEvidence:
        reviewer = self._principal(tenant, "g0_check")
        with self.store.connect() as conn:
            self.store._lock(conn, tenant)
            record = self._record(conn, tenant, record_id)
            item = next((x for x in record.project_checks
                         if x.variable == variable and x.name == check_name), None)
            if item is None or item.status != "passed" or item.reviewer != reviewer or item.evidence_id is None:
                raise PermissionError("check review is not authorized")
            resolved = self._review(tenant, record, reviewer, "check", item.evidence_id,
                variable=variable, check_name=check_name, check_version=item.version)
            now = datetime.now(timezone.utc)
            proof = CheckEvidence(**self._proof_common(record, reviewer, item.evidence_id, now, valid_to),
                variable=variable, check_name=check_name, check_version=item.version)
            self.store._append(conn, tenant=tenant, kind="check", entry_id=proof.evidence_id,
                record_id=record_id, value=self._review_value(proof, resolved))
            return proof

    def approve_right(self, tenant: str, record_id: str, action: str, use: str,
                      *, valid_to: datetime, conditions_met: bool | None = None) -> RightEvidence:
        reviewer = self._principal(tenant, "g0_right")
        if conditions_met is not None:
            raise ValueError("rights conditions must come from the independent review proof")
        with self.store.connect() as conn:
            self.store._lock(conn, tenant)
            record = self._record(conn, tenant, record_id)
            item = next((x for x in record.rights if x.action == action), None)
            if (item is None or item.status != "allowed" or item.reviewer != reviewer or
                    item.evidence_id is None):
                raise PermissionError("right review is not authorized")
            resolved = self._review(tenant, record, reviewer, "right", item.evidence_id,
                action=action, use=use)
            now = datetime.now(timezone.utc)
            proof = RightEvidence(**self._proof_common(record, reviewer, item.evidence_id, now, valid_to),
                action=action, use=use, conditions_met=resolved.conditions_met)
            self.store._append(conn, tenant=tenant, kind="right", entry_id=proof.evidence_id,
                record_id=record_id, action=action, intended_use=use,
                value=self._review_value(proof, resolved))
            return proof

    def _revoke(self, tenant: str, target_kind: str, target_id: str) -> None:
        reviewer = self._principal(tenant, "g0_revoke")
        with self.store.connect() as conn:
            self.store._lock(conn, tenant)
            row = self.store._one(conn, tenant, target_kind, target_id)
            if row is None:
                raise ValueError("approval is unavailable")
            cls = {"policy": G0Policy, "source": SourceEvidence,
                   "check": CheckEvidence, "right": RightEvidence}[target_kind]
            proof = self.store._model(row, cls)
            if proof.reviewer != reviewer:
                raise PermissionError("only the original reviewer can revoke")
            existing = conn.execute("SELECT entry_id FROM {} WHERE tenant_id = %s AND kind = 'revocation' AND action = %s AND record_id = %s".format(
                self.store._table().as_string(conn)), (tenant, target_kind, target_id)).fetchone()
            if existing:
                raise ValueError("approval is already revoked")
            self.store._append(conn, tenant=tenant, kind="revocation", entry_id=str(uuid4()),
                record_id=target_id, action=target_kind,
                value={"target_kind": target_kind, "target_id": target_id,
                       "reviewer": reviewer})

    def revoke_policy(self, tenant: str, policy_id: str) -> None:
        self._revoke(tenant, "policy", policy_id)

    def revoke_evidence(self, tenant: str, evidence_id: str) -> None:
        self._principal(tenant, "g0_revoke")
        with self.store.connect() as conn:
            kinds = [kind for kind in ("source", "check", "right")
                     if self.store._one(conn, tenant, kind, evidence_id) is not None]
        if len(kinds) != 1:
            raise ValueError("evidence ID is missing or ambiguous")
        self._revoke(tenant, kinds[0], evidence_id)

    def evaluate(self, tenant: str, record_id: str, action: str, use: str,
                 *, decision_at: datetime | None = None) -> dict:
        self._principal(tenant, "g0_evaluate")
        record_id = record_id if isinstance(record_id, str) and len(record_id) <= 200 else ""
        action = action if isinstance(action, str) and len(action) <= 200 else ""
        use = use if isinstance(use, str) and len(use) <= 200 else ""
        now = datetime.now(timezone.utc)
        at = now if decision_at is None else decision_at
        with self.store.connect() as conn:
            self.store._lock(conn, tenant)
            if not isinstance(at, datetime) or at.utcoffset() != timedelta(0) or at > now:
                status, reasons, gate = "hold", ["decision_time_invalid"], None
                time_text = None
                approved_policy_digest = None
            else:
                result = evaluate_g0(record_id, action, use, at,
                    self.store.repository(conn, tenant, at))
                status = result.status
                reasons = list(dict.fromkeys(reason.code for reason in result.reasons))
                gate = result.model_dump(mode="json")
                time_text = at.isoformat()
                policy_row = (self.store._one(conn, tenant, "policy", result.policy_id, at)
                              if result.policy_id else None)
                approved_policy_digest = (self.store._model(policy_row, G0Policy).policy_digest
                                          if policy_row else None)
            decision_id = str(uuid4())
            decision = dict(tenant_id=tenant, decision_id=decision_id,
                record_id=record_id, action=action, intended_use=use,
                decision_at=time_text, status=status, reasons=reasons, gate=gate,
                approved_policy_digest=approved_policy_digest,
                requested_decision_at=(decision_at.isoformat()
                    if isinstance(decision_at, datetime) and decision_at.utcoffset() == timedelta(0)
                    else None), evaluated_at=now.isoformat())
            self.store._append(conn, tenant=tenant, kind="decision", entry_id=decision_id,
                record_id=record_id, action=action, intended_use=use, value=decision)
            return decision

    def get_decision(self, tenant: str, decision_id: str) -> dict | None:
        self._principal(tenant, "g0_evaluate")
        return self.store.get_decision(tenant, decision_id)
