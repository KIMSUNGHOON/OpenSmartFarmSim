"""Hosted test factory only: fake CLI/key and synthetic authority, never production approval."""

from dataclasses import replace
import json
import os
from pathlib import Path

from app.cli_contracts import DecisionContract
from app.cli_supervisor_service import SupervisorServer
from app.content_access import ContentAccess
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy
from test_cli_contracts import resolver


def create():
    value = json.loads(Path(os.environ["OSSF_SUPERVISOR_FIXTURE_CONFIG"]).read_bytes())
    policy = RuntimeLoginPolicy(**value["policy"])
    def authority(job, input_value):
        result = resolver(job, input_value)
        return (replace(result, allow_proceed=True, missing_evidence=(),
                        g3a_candidate_ids=result.candidate_ids, g3b_ok=True)
                if value["proceed"] else result)
    store = JobStore(value["dsn"], policy.schema, Path(value["artifact_root"]),
        decision_validator=DecisionContract(authority), runtime_identity=(policy, "supervisor"),
        content_access=ContentAccess(**value["content_access"]))
    return SupervisorServer(store, **value["settings"])
