"""Explicit maximum-grid SCRAM component check; synthetic assumptions only."""

from pathlib import Path
import json
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_api_break_even_plan import build_plan_api, post, login_database, login_scope, PROFILE

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


def test_actual_256_trial_admission_finishes_within_http_work_budget(login_scope):
    began = time.perf_counter()
    def progress(stage, count):
        print('maximum_grid_setup='+json.dumps({'stage':stage, 'count':count,
            'trial_count':256, 'elapsed_seconds':time.perf_counter()-began}), flush=True)
    app, service, body, _ = build_plan_api(login_scope, list(range(20, 276)), progress=progress)
    assert len(body['trials']) == 256
    start = time.perf_counter()
    status, accepted = post(app, body)
    elapsed = time.perf_counter()-start
    print('maximum_grid_admission='+json.dumps({'status':status, 'trial_count':256,
        'component_seconds':elapsed, 'http_work_budget_seconds':30,
        'scope':'synthetic_software_only'}), flush=True)
    assert status == 202 and accepted['trial_count'] == 256
    assert accepted['intent_job']['state'] == 'queued'
    assert service.store.get_break_even_read('tenant-1', accepted['plan_id']) is None
    if elapsed >= 30:
        import cProfile
        from break_even_admission_profile import profile_summary
        profile = cProfile.Profile()
        diagnostic_start = time.perf_counter()
        retry_status, retry_accepted = profile.runcall(post, app, body)
        diagnostic_elapsed = time.perf_counter() - diagnostic_start
        print('maximum_grid_slow_diagnostic=' + json.dumps(profile_summary(profile,
            diagnostic_elapsed, status=retry_status, trial_count=256)), flush=True)
        assert (retry_status, retry_accepted) == (status, accepted)
    assert elapsed < 30, 'maximum-grid admission exceeds the existing 30-second HTTP work budget'
