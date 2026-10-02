"""Explicit admission profiler; two synthetic trials do not prove capacity."""

import cProfile
import json
from pathlib import Path
import pstats
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_api_break_even_plan import build_plan_api, post, login_database, login_scope, PROFILE

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
