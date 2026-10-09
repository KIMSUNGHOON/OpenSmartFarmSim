"""Software test factory only: synthetic authority, public test key, no production approval."""

from dataclasses import replace
import json
import os
from pathlib import Path

from app.authority_rpc import AuthorityServer
from app.cli_contracts import DecisionContract
from app.cli_supervisor_client import SupervisorClient
from app.cli_worker import CliWorker
from app.content_access import ContentAccess
from app.execution_attestation import ExecutionAttestationStore
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy
from test_cli_contracts import resolver
from test_job_evidence import cli_store
from test_jobs import synthetic_principal


def create():
    value = json.loads(Path(os.environ["OSSF_AUTHORITY_FIXTURE_CONFIG"]).read_bytes())
    policy = RuntimeLoginPolicy(**value["policy"])
    def authority(job, input_value):
        result = resolver(job, input_value)
        return (replace(result, allow_proceed=True, missing_evidence=(),
                        g3a_candidate_ids=result.candidate_ids, g3b_ok=True)
                if value["proceed"] else result)
    contract = DecisionContract(authority)
    base = JobStore(value["dsn"], policy.schema, Path(value["artifact_root"]))
    store = JobStore(base._dsn, base.schema, base.artifact_root, decision_validator=contract,
        evidence_policy=cli_store(base).evidence_policy, principal_provider=synthetic_principal,
        runtime_identity=(policy, "authority"), content_access=ContentAccess(**value["content_access"]))
    engine = CliWorker(store, contract, supervisor_client=SupervisorClient(**value["supervisor"]),
        attestation_store=ExecutionAttestationStore(store, {value["key_id"]: bytes.fromhex(value["public_key"])}),
        timeout_seconds=10, lease_seconds=20, synthetic_smoke=True)
    return AuthorityServer(engine, role_policy=policy, **value["settings"])
