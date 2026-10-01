"""Actual SCRAM completed-evidence reading; synthetic records and signing keys."""

from copy import copy, deepcopy
from hashlib import sha256
from pathlib import Path
import json
import sys
from uuid import UUID, uuid4

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.break_even_verification_worker import BreakEvenVerificationWorker
from app.break_even_verified_result import BreakEvenVerifiedResultService
from app.jobs import canonical_input_bytes
from test_break_even_verification import (verification_setup, result_api, complete,
    calculation_setup, plan_api, login_database, login_scope, PROFILE)

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


@pytest.fixture
def completed_verification(verification_setup):
    service, parent, principal = verification_setup
    accepted = service.submit('tenant-1', parent)
    worker = BreakEvenVerificationWorker(service.jobs, service.store, tenant_id='tenant-1')
    assert worker.run_once(str(accepted.job_id)).state == 'succeeded'
    return BreakEvenVerifiedResultService(service.jobs, service.store), accepted.job_id, parent, principal


def test_actual_completed_result_reads_without_arithmetic_or_write_scopes(completed_verification, monkeypatch):
    from app.break_even import BreakEvenService
    from app.economics import EconomicLedger
    from app.market_scenario import MarketScenarioService
    reader, identity, parent, principal = completed_verification
    expected = reader.authority.read_job_result('tenant-1', UUID(parent))
    for scope in ('simulation_execute', 'break_even_write', 'market_candidate_write', 'market_source_write'):
        principal['scopes'].discard(scope)
    def forbidden(*_, **__): raise RuntimeError('arithmetic must stay in the worker')
    monkeypatch.setattr(BreakEvenService, 'scan', forbidden)
    monkeypatch.setattr(EconomicLedger, 'calculate', forbidden)
    monkeypatch.setattr(MarketScenarioService, 'calculate_pinned', forbidden)
    monkeypatch.setattr(reader.store, 'get_break_even_read', forbidden)
    candidates = reader.store._source
    source = candidates._source._source
    counts = {'candidate': 0, 'source': 0}
    def counted(label, original):
        def connect():
            counts[label] += 1
            return original()
        return connect
    monkeypatch.setattr(candidates, 'connect', counted('candidate', candidates.connect))
    monkeypatch.setattr(source, 'connect', counted('source', source.connect))
    actual = reader.read_job_result('tenant-1', identity)
    assert actual == expected and actual.assessment_status == 'hold'
    assert len(actual.trials) == 2 and isinstance(actual.trials[0].target_value_krw, str)
    assert counts == {'candidate': 1, 'source': 0}
    resumed = BreakEvenVerifiedResultService(reader.jobs, reader.store)
    assert resumed.read_job_result('tenant-1', identity) == actual


def test_pending_wrong_model_unknown_and_other_tenant_are_withheld(verification_setup):
    service, parent, _ = verification_setup
    accepted = service.submit('tenant-1', parent)
    reader = BreakEvenVerifiedResultService(service.jobs, service.store)
    assert reader.read_job_result('tenant-1', accepted.job_id) is None
    assert reader.read_job_result('tenant-1', UUID(parent)) is None
    assert reader.read_job_result('tenant-1', uuid4()) is None
    with pytest.raises(PermissionError): reader.read_job_result('tenant-2', accepted.job_id)


def test_receipt_and_publication_tampering_cannot_authorize_results(completed_verification, monkeypatch):
    reader, identity, _, _ = completed_verification
    receipt = json.loads(reader.jobs.read_artifact('tenant-1', identity))
    publication = reader.jobs.get_publication('tenant-1', identity)
    for field, value in [('plan_id', 'other'), ('calculation_job_id', str(uuid4())),
            ('assessment_status', 'pass'), ('verification_input_sha256', 'a'*64),
            ('calculation_receipt_sha256', 'b'*64), ('result_sha256', 'c'*64),
            ('code_sha256', 'd'*64), ('trial_count', 256), ('evidence_size', True),
            ('evidence_size', 1048577), ('evidence_sha256', '../private'), ('extra', 'private')]:
        raw = canonical_input_bytes(receipt | {field: value})
        changed = deepcopy(publication)
        changed.update(artifact_size=len(raw), artifact_sha256=sha256(raw).hexdigest())
        changed['manifest']['artifact_sha256'] = sha256(raw).hexdigest()
        with monkeypatch.context() as patch:
            patch.setattr(reader.jobs, 'read_artifact', lambda *_: raw)
            patch.setattr(reader.jobs, 'get_publication', lambda *_: changed)
            with pytest.raises((ValueError, RuntimeError)): reader.read_job_result('tenant-1', identity)
    for field, value in [('attempt', 999), ('decision_id', 'forged'),
            ('manifest', {}), ('artifact_size', 4097), ('artifact_sha256', 'e'*64)]:
        with monkeypatch.context() as patch:
            patch.setattr(reader.jobs, 'get_publication', lambda *_: publication | {field: value})
            with pytest.raises(RuntimeError): reader.read_job_result('tenant-1', identity)


def test_private_evidence_corruption_or_incomplete_candidates_withholds_result(completed_verification, monkeypatch):
    reader, identity, _, _ = completed_verification
    receipt = json.loads(reader.jobs.read_artifact('tenant-1', identity))
    raw = reader.jobs._read_private_evidence('tenant-1',
        {'sha256': receipt['evidence_sha256'], 'size': receipt['evidence_size']})
    with monkeypatch.context() as patch:
        patch.setattr(reader.jobs, '_read_private_evidence', lambda *_: raw+b' ')
        with pytest.raises(RuntimeError): reader.read_job_result('tenant-1', identity)
    incomplete = json.loads(raw)
    incomplete['reads'] = [item for item in incomplete['reads'] if item['method'] != 'get_market_candidate']
    evidence = json.dumps(incomplete, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    changed_receipt = receipt | {'evidence_sha256': sha256(evidence).hexdigest(), 'evidence_size': len(evidence)}
    artifact = canonical_input_bytes(changed_receipt)
    publication = deepcopy(reader.jobs.get_publication('tenant-1', identity))
    publication.update(artifact_sha256=sha256(artifact).hexdigest(), artifact_size=len(artifact))
    publication['manifest']['artifact_sha256'] = sha256(artifact).hexdigest()
    actual_publication = reader.jobs.get_publication
    actual_artifact = reader.jobs.read_artifact
    with monkeypatch.context() as patch:
        patch.setattr(reader.jobs, 'get_publication', lambda tenant, current:
            publication if current == identity else actual_publication(tenant, current))
        patch.setattr(reader.jobs, 'read_artifact', lambda tenant, current:
            artifact if current == identity else actual_artifact(tenant, current))
        patch.setattr(reader.jobs, '_read_private_evidence', lambda *_: evidence)
        with pytest.raises(RuntimeError, match='coverage'): reader.read_job_result('tenant-1', identity)


@pytest.mark.parametrize('fault', ['scope', 'source', 'bytes', 'grant'])
def test_current_dependency_and_access_changes_withhold_result(completed_verification, login_scope, monkeypatch, fault):
    reader, identity, _, principal = completed_verification
    base, policy, _ = login_scope
    candidates = reader.store._source
    source = candidates._source._source
    original = source._read_in_transaction
    calls = []
    def change(*args, **kwargs):
        value = original(*args, **kwargs)
        if not calls:
            calls.append(True)
            if fault == 'scope': principal['scopes'].remove('market_source_read')
            elif fault == 'source': reader.store._source = copy(candidates)
            elif fault == 'bytes': return value | {'unrecorded': 'change'}
            else:
                with base.connect() as conn:
                    conn.execute(sql.SQL('GRANT DELETE ON {}.market_source_records TO {}')
                        .format(sql.Identifier(policy.schema), sql.Identifier(policy.roles['authority'])))
        return value
    try:
        monkeypatch.setattr(source, '_read_in_transaction', change)
        with pytest.raises((PermissionError, RuntimeError, ValueError)):
            reader.read_job_result('tenant-1', identity)
        assert calls
    finally:
        reader.store._source = candidates
        principal['scopes'].add('market_source_read')
        if fault == 'grant':
            with base.connect() as conn:
                conn.execute(sql.SQL('REVOKE DELETE ON {}.market_source_records FROM {}')
                    .format(sql.Identifier(policy.schema), sql.Identifier(policy.roles['authority'])))


def test_current_implementation_change_withholds_completed_evidence(completed_verification, monkeypatch):
    from app.break_even_verification import BreakEvenVerificationService
    reader, identity, _, _ = completed_verification
    original = BreakEvenVerificationService._digests
    calls = []
    def changed():
        calls.append(True)
        return original() if len(calls) == 1 else ('f'*64, 'a'*64)
    monkeypatch.setattr(BreakEvenVerificationService, '_digests', staticmethod(changed))
    with pytest.raises(RuntimeError): reader.read_job_result('tenant-1', identity)
