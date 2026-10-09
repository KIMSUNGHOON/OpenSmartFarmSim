"""Test-only fresh worker assembly from a private temporary configuration."""

import json
from pathlib import Path

from app.api_market_source import _MarketSources
from app.break_even_store import BreakEvenStore
from app.break_even_verification_worker import BreakEvenVerificationWorker
from app.job_store import JobStore
from app.market_candidate_store import MarketCandidateStore
from app.market_hold_store import MarketHoldStore
from app.market_source_store import MarketSourceStore
from app.runtime_roles import RuntimeLoginPolicy
from app.thermal_run_store import ThermalRunStore
from test_market_hold_store import context_verifier, HOLD_KEY


def build(path):
    data = json.loads(Path(path).read_text())
    policy = RuntimeLoginPolicy(**data['policy'])
    provider = lambda: data['principal']
    kwargs = dict(runtime_identity=(policy, 'authority'), principal_provider=provider)
    jobs = JobStore(data['dsn'], policy.schema, Path(data['artifacts']), audit_runtime_grants=True, **kwargs)
    sources = MarketSourceStore(data['dsn'], policy.schema, **kwargs)
    contexts = ThermalRunStore(data['dsn'], policy.schema, gate_key=b'synthetic-gate-key-32-bytes-long!',
        release_verifier=lambda *_: None, context_verifier=context_verifier, **kwargs)
    holds = MarketHoldStore(data['dsn'], policy.schema, context_store=contexts,
        scope_resolver=lambda *_: data['hold_scope'], signing_key=HOLD_KEY, **kwargs)
    candidates = MarketCandidateStore(data['dsn'], policy.schema,
        _MarketSources(sources, holds, principal_provider=provider), **kwargs)
    store = BreakEvenStore(data['dsn'], policy.schema, candidates, **kwargs)
    return BreakEvenVerificationWorker(jobs, store, tenant_id=data['principal']['tenant_id'])
