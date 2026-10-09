"""Software fixture factory: private test key/login, one registered synthetic ID."""

import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.planning_events import PlanningAuthority, PlanningEventStore
from app.planning_roles import PlanningLoginPolicy
from app.planning_rpc import PlanningServer


def create():
    value = json.loads(Path(os.environ["OSSF_PLANNING_FIXTURE_CONFIG"]).read_bytes())
    policy = PlanningLoginPolicy(**value["policy"])
    tenant = value["settings"]["tenant_id"]
    store = PlanningEventStore(value["dsn"], policy.schema, runtime_identity=(policy, "authority"),
        principal_provider=lambda: {"authenticated": True, "tenant_id": tenant,
                                    "scopes": ("planning_event_issue",)})
    key = Ed25519PrivateKey.from_private_bytes(Path(value["private_key_file"]).read_bytes())
    authority = PlanningAuthority(store, value["key_id"], key)
    snapshot = value["snapshot"]
    def resolve(request_tenant, snapshot_id):
        return snapshot if request_tenant == snapshot["tenant_id"] and snapshot_id == snapshot["snapshot_id"] else None
    return PlanningServer(authority, resolve, **value["settings"])
