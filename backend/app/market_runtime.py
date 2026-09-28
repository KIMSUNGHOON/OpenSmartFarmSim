"""Bound market connections require exact SCRAM identity and effective grants."""

from .runtime_login import connect_runtime
from .runtime_roles import RuntimeLoginPolicy, RolePolicyHold, audit_runtime_roles


def validate_market_identity(schema, binding, *, calculation=False, break_even=False, source_storage=False):
    if binding is not None and (type(binding) is not tuple or len(binding) != 2 or
            type(binding[0]) is not RuntimeLoginPolicy or binding[0].schema != schema or
            binding[1] != "authority" or (calculation and not binding[0].market_calculation) or
            (break_even and not binding[0].break_even_calculation) or
            (source_storage and not binding[0].market_source_storage)):
        raise ValueError("market runtime identity rejected")


def connect_market(dsn, binding):
    conn = connect_runtime(dsn, *binding)
    try:
        audit_runtime_roles(conn, binding[0])
        conn.commit()
        return conn
    except Exception:
        conn.close()
        raise RolePolicyHold("market_runtime_grants_rejected") from None
