"""Fresh UID probe: public reader and job authority only; never a product factory."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from app.job_store import JobStore
from app.planning_events import DecisionContextVerifier, PlanningEventStore
from app.planning_roles import PlanningLoginPolicy
from app.planning_rpc import PlanningClient
from app.runtime_roles import RuntimeLoginPolicy
from app.thermal_publisher import collection_review_input
from app.thermal_run_store import ThermalRunStore


def main():
    try:
        value = json.loads(Path(os.environ["OSSF_PLANNING_CLIENT_FIXTURE_CONFIG"]).read_bytes())
        assert os.getresuid() == (value["uid"],) * 3
        for name in value["denied_paths"]:
            try:
                descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW)
            except PermissionError:
                continue
            os.close(descriptor)
            raise AssertionError("private planning file readable")
        tenant = value["tenant_id"]
        principal = lambda: {"authenticated": True, "tenant_id": tenant, "scopes": (
            "planning_event_read", "metadata", "thermal_snapshot_read", "decision_context_write", "decision_context_read")}
        plan_policy, job_policy = PlanningLoginPolicy(**value["planning_policy"]), RuntimeLoginPolicy(**value["job_policy"])
        reader = PlanningEventStore(value["reader_dsn"], plan_policy.schema,
            principal_provider=principal, runtime_identity=(plan_policy, "supervisor"))
        verifier = DecisionContextVerifier({value["key_id"]: bytes.fromhex(value["public_key"])}, reader.read_event)
        client = PlanningClient(value["socket_path"], planning_uid=value["planning_uid"], tenant_id=tenant, verifier=verifier)
        context_store = ThermalRunStore(value["job_dsn"], job_policy.schema,
            gate_key=b"synthetic-unused-gate-key-32-bytes-long", release_verifier=lambda *_: None,
            principal_provider=principal, context_verifier=verifier, runtime_identity=(job_policy, "authority"))
        jobs = JobStore(value["job_dsn"], job_policy.schema, Path(value["artifact_root"]),
                        principal_provider=principal, runtime_identity=(job_policy, "authority"))
        snapshot = context_store.get_snapshot(tenant, value["snapshot_id"])
        for kind in ("actual", "hypothetical"):
            raw, signature = client.issue(value["snapshot_id"], claim_mode="ex_post_replay", decision_time_kind=kind,
                hypothetical_at=datetime(2000, 1, 1, tzinfo=timezone.utc) if kind == "hypothetical" else None)
            context_id = context_store.put_decision_context(tenant, raw, signature)
            context = context_store.get_decision_context(tenant, value["snapshot_id"], context_id)
            assert context["decision_time_kind"] == kind
            job = jobs.submit(tenant, "collection_review", collection_review_input(snapshot, context), "uid-plan-"+kind)
            assert job["state"] == "queued"
        return 0
    except Exception:
        print("planning_client_probe_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
