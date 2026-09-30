"""Opt-in real Codex CLI review of a self-authored synthetic farm version."""

import json
import os
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.calculation_assessment import CalculationAssessmentService
from app.cli_worker import CliWorker
from app.farm_authored_review import FarmAuthoredReviewService
from app.market_result_store import MarketResultStore
from app.owned_cli_contracts import OwnedCliContractRouter
from app.owned_collection_review import OwnedCollectionReviewService
from app.owned_fixture_collection import CollectionService
from test_farm_authoring_storage import authoring, request
from test_farm_authored_review import self_authored_evidence_policy
from login_database import login_database, login_scope


if os.environ.get('OSSF_REAL_AUTHORED_CLI_SMOKE') == '1':
    @pytest.mark.parametrize('login_scope', [{'market_calculation': True,
        'market_source_storage': True, 'thermal_scenario_storage': True,
        'break_even_calculation': True}], indirect=True)
    def test_real_cli_self_authored_farm_review(authoring, login_scope):
        author, body, principal = authoring
        principal['scopes'].add('collection_review_create')
        registration = author.submit('tenant-1', request(body))
        review = FarmAuthoredReviewService(author)
        submitted = review.submit('tenant-1', body['farm']['scenario_id'],
            body['farm']['scenario_revision'], registration.scenario_sha256,
            'real-authored-review')
        replay = author.replay
        jobs = replay.jobs
        runs = replay.thermal.runs
        results = MarketResultStore(jobs._dsn, jobs.schema, replay.candidates,
            principal_provider=jobs.principal_provider,
            runtime_identity=jobs.runtime_identity)
        assessment = CalculationAssessmentService(jobs, runs, results,
            replay.thermal, replay)
        owned_review = OwnedCollectionReviewService(
            CollectionService(jobs, replay.owned_research.registry), runs)
        router = OwnedCliContractRouter(replay.owned_research, owned_review,
            assessment, lambda *_: None, review)
        jobs.decision_validator = router
        jobs.evidence_policy = self_authored_evidence_policy
        worker = CliWorker(jobs, router,
            cli_path=Path(os.environ['OSSF_REAL_CLI_PATH']),
            codex_home=Path(os.environ['OSSF_REAL_CODEX_HOME']),
            timeout_seconds=600, lease_seconds=660, synthetic_smoke=True)

        lease = jobs.claim(660, allowed_stages=('collection_review',),
            tenant_id='tenant-1', job_id=str(submitted['job_id']))
        assert lease is not None
        worked = worker._run_claimed(lease)
        assert worked.state == 'succeeded' and worked.capture_id and worked.decision_id, (
            worked.state, worked.reason_code)
        invocation = jobs.get_invocation('tenant-1', submitted['job_id'], worked.attempt)
        assert (invocation['execution_kind'], invocation['model'],
                invocation['reasoning_effort']) == ('codex_cli', 'gpt-6-sol', 'xhigh')
        with jobs.connect() as conn:
            capture = conn.execute(sql.SQL('''
                SELECT jsonl_sha256, final_output_sha256, exit_code,
                       termination_reason, usage FROM {}
                WHERE tenant_id=%s AND job_id=%s AND attempt=%s
            ''').format(jobs._table('attempt_cli_captures')),
                ('tenant-1', submitted['job_id'], worked.attempt)).fetchone()
        assert capture['jsonl_sha256'] and capture['final_output_sha256']
        assert capture['exit_code'] == 0 and capture['termination_reason'] == 'completed'
        assert capture['usage']['input_tokens'] > 0
        assert jobs.get_job('tenant-1', submitted['job_id'])['state'] == 'succeeded'
        assert jobs.get_publication('tenant-1', submitted['job_id']) is not None
        stored = jobs.read_artifact('tenant-1', submitted['job_id'])
        assert json.loads(stored)['registration_sha256'] == registration.scenario_sha256
        print(json.dumps({'stage': 'collection_review',
            'job_id': str(submitted['job_id']), 'attempt': worked.attempt,
            'capture_id': str(worked.capture_id),
            'decision_id': str(worked.decision_id),
            'jsonl_sha256': capture['jsonl_sha256'],
            'final_output_sha256': capture['final_output_sha256'],
            'usage': capture['usage']}, sort_keys=True))
