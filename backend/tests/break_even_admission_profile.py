"""Explicit admission profiler; two synthetic trials do not prove capacity."""

import cProfile
import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import pstats
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_api_break_even_plan import build_plan_api, post, login_database, login_scope, tls_files, PROFILE

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


def profile_summary(profile, elapsed, *, status, trial_count):
    stats = pstats.Stats(profile)
    rows = []
    for (filename, line, name), (primitive, total, own, cumulative, _) in stats.stats.items():
        if '/backend/app/' not in filename and '/psycopg/' not in filename:
            continue
        rows.append({'module': Path(filename).name, 'line': line, 'function': name,
            'primitive_calls': primitive, 'total_calls': total,
            'own_seconds': own, 'cumulative_seconds': cumulative})
    rows.sort(key=lambda item: item['cumulative_seconds'], reverse=True)
    return {'status': status, 'trial_count': trial_count,
        'profiled_component_seconds': elapsed,
        'scope': 'synthetic_diagnostic_only', 'top_functions': rows[:25]}


def test_profile_actual_admission_without_changing_validation(login_scope):
    app, service, body, _ = build_plan_api(login_scope, [20, 32])
    profile = cProfile.Profile()
    started = time.perf_counter()
    status, accepted = profile.runcall(post, app, body)
    elapsed = time.perf_counter() - started
    assert status == 202 and accepted['trial_count'] == 2
    assert accepted['intent_job']['state'] == 'queued'
    assert service.store.get_break_even_read('tenant-1', accepted['plan_id']) is None
    print('break_even_admission_profile=' + json.dumps(profile_summary(profile,
        elapsed, status=status, trial_count=2)), flush=True)


def test_profile_standard_bearer_admission(login_scope, tls_files):
    from app.api_runtime import ApiRuntime
    from app.api_break_even_verification import VERIFICATION_SCOPES
    from app.break_even_plan_submission import PLAN_SUBMISSION_SCOPES
    from app.http_identity import BearerRegistry, BearerGrant, token_digest
    from app.market_source_store import MarketSourceStore
    from test_api_runtime import config, dependencies
    from test_http_identity import request
    _, service, body, _ = build_plan_api(login_scope, [20, 32])
    scope = service.store._source._source._holds._scope_resolver()
    token = b'synthetic-protected-admission-profile-' + b'p' * 32
    now = datetime.now(timezone.utc)
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-1',
        frozenset(PLAN_SUBMISSION_SCOPES) | frozenset(VERIFICATION_SCOPES),
        now - timedelta(seconds=1), now + timedelta(hours=1)),))
    cert, key, _ = tls_files
    jobs = service.jobs
    factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key),
        dependencies(bearer_registry=registry, market_source_factory=factory,
            market_scope_resolver=lambda *_: dict(scope)))
    profile = cProfile.Profile()
    started = time.perf_counter()
    status, accepted, _ = profile.runcall(asyncio.run, request(runtime.service.app,
        path='/v1/break-even-plans', method='POST',
        headers=[(b'content-type', b'application/json'), (b'authorization', b'Bearer ' + token)],
        body=json.dumps(body).encode()))
    elapsed = time.perf_counter() - started
    assert status == 202 and accepted['trial_count'] == 2
    result = profile_summary(profile, elapsed, status=status, trial_count=2)
    result['identity_functions'] = [{'function': name, 'calls': total,
        'own_seconds': own, 'cumulative_seconds': cumulative}
        for (filename, _, name), (_, total, own, cumulative, _) in pstats.Stats(profile).stats.items()
        if filename.endswith('/app/http_identity.py')]
    print('break_even_protected_admission_profile=' + json.dumps(result), flush=True)
