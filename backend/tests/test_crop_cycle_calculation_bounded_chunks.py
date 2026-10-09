"""Actual calculations with bounded original-grid chunks; no field-data claims."""
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
import os

import pytest

from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_context as engine
from app import crop_cycle_calculation_server_custody as custody
from test_crop_cycle_artifact import CASES, NOTICE, PROFILES, program
from test_crop_cycle_calculation_artifact import context, rows
from test_crop_cycle_calculation_context import finish as pure_finish
from test_crop_cycle_calculation_server_custody import (
    KEY, journal_setup, open_journal, close_journal,
)

BIG = {'max_steps': 10000, 'max_transitions': 4096}


def dense(kind):
    value = program('night-smooth')
    start = engine.physical._utc(value['segments'][0]['start'])
    times = [engine.physical._stamp(start + timedelta(seconds=i*20)) for i in range(181)]
    if kind in ('outputs', 'both'): value['output_times'] = times
    if kind in ('events', 'both'):
        template = program('full-removal-reentry')['events'][0]['removals']
        template['values']['leaf']['value'] = 0
        template['values']['fruit_fraction'] = [dict(q, value=0) for q in template['values']['fruit_fraction']]
        value['events'] = [{'at': at, 'removals': {**deepcopy(template), 'input_id': f'owned-dense-{i}'}}
                           for i, at in enumerate(times)]
    return value


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['case_id'])
def test_actual_writer_accepts_larger_request_without_changing_original_values(tmp_path, case, monkeypatch):
    ctx, _ = context(tmp_path, case['program'])
    expected = engine.physical.integrate_plant_startup(**case['program'], **PROFILES)
    before = len(os.listdir('/proc/self/fd'))
    requested = deepcopy(BIG)
    with ctx:
        with artifact.create_writer(tmp_path/'result', ctx, notice_raw=NOTICE) as writer:
            while writer.advance(requested)['status'] == 'yielded': pass
            receipt = writer.finalize()
        assert requested == BIG
        monkeypatch.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('read ran RHS'))
        with artifact.open_artifact(tmp_path/'result', receipt['artifact_sha256'], ctx, notice_raw=NOTICE) as reader:
            for kind in ('samples', 'events'): assert rows(reader, kind) == expected[kind]
            for key in ('status', 'steps', 'planned_steps'): assert reader.summary[key] == expected[key]
        assert len(ctx._cache) <= 2 and len(ctx.reader._cache) <= 4
    assert len(os.listdir('/proc/self/fd')) == before-1


@pytest.mark.parametrize('kind', ['outputs', 'events', 'both'])
@pytest.mark.parametrize('start_budget', [None, {'max_steps': 1, 'max_transitions': 2},
                                       {'max_steps': 10000, 'max_transitions': 3}])
def test_dense_boundaries_are_capped_before_rhs_and_replayed_once(tmp_path, kind, start_budget, monkeypatch):
    ctx, _ = context(tmp_path, dense(kind))
    with ctx:
        expected = pure_finish(ctx, 17, 31)
        actual_advance = engine.advance_chunk
        budgets = []
        def checked(context, cp, budget):
            index = min(cp['boundary_cursor']+128, context.boundary_count)-1
            row = engine._boundary(context, index)
            cap = row['steps']+index+1-cp['sequence']
            assert 1 <= budget['max_transitions'] <= min(4096, cap)
            result = actual_advance(context, cp, budget)
            assert all(len(result[k]) <= 128 for k in ('samples', 'events'))
            budgets.append(deepcopy(budget))
            return result
        with artifact.create_writer(tmp_path/'result', ctx, notice_raw=NOTICE) as writer:
            if start_budget is not None: writer.advance(start_budget)
            monkeypatch.setattr(engine, 'advance_chunk', checked)
            while writer.advance(BIG)['status'] == 'yielded': pass
            receipt = writer.finalize()
        assert budgets and budgets[0]['max_transitions'] < 4096
        monkeypatch.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('read RHS'))
        with artifact.open_artifact(tmp_path/'result', receipt['artifact_sha256'], ctx, notice_raw=NOTICE) as reader:
            for kind in ('samples', 'events'): assert rows(reader, kind) == expected[kind]
            lineage = {'parent_sha256', 'checkpoint_sha256'}
            assert {k:v for k,v in reader.summary['checkpoint'].items() if k not in lineage} == {
                k:v for k,v in expected['checkpoint'].items() if k not in lineage}


def test_independent_validator_rejects_a_budget_above_current_boundary_cap(tmp_path):
    ctx, _ = context(tmp_path, dense('both'))
    with ctx:
        cp = engine.start(ctx)
        result = engine.advance_chunk(ctx, cp, {'max_steps': 10000, 'max_transitions': 255})
        meta = {k:v for k,v in result.items() if k not in ('manifest', 'samples', 'events')}
        records = {k:result[k] for k in ('samples', 'events')}
        assert len(records['samples']) == len(records['events']) == 128
        with pytest.raises(artifact.CalculationArtifactHold, match='RESOURCE_HOLD'):
            artifact._validate_delta(ctx, cp, meta, records, BIG)


def test_writer_rejects_engine_ignoring_record_cap_without_selecting_head(tmp_path, monkeypatch):
    ctx, _ = context(tmp_path, dense('both'))
    with ctx:
        writer = artifact.create_writer(tmp_path/'result', ctx, notice_raw=NOTICE)
        before = (tmp_path/'result/HEAD').read_bytes()
        advance = engine.advance_chunk
        monkeypatch.setattr(engine, 'advance_chunk', lambda context, cp, budget: advance(context, cp, BIG))
        with pytest.raises(artifact.CalculationArtifactHold, match='RESOURCE_HOLD'):
            writer.advance(BIG)
        assert writer.closed and (tmp_path/'result/HEAD').read_bytes() == before


def test_signed_server_uses_distinct_v3_policy_and_larger_request(journal_setup, monkeypatch):
    assert custody.VERSION == 'crop-cycle-verified-server-custody-v3'
    assert custody.INTENT_VERSION == 'crop-cycle-verified-server-intent-v3'
    assert custody.PROOF_VERSION == 'crop-cycle-verified-server-head-v3'
    request = json.loads(journal_setup[3])
    old_identity = sha256(b'ossf-crop-cycle-verified-server-identity-v2\0'+custody._canonical({
        'tenant_id': 'own-tenant', 'study_id': request['study_id'], 'revision': request['revision']})).hexdigest()
    assert journal_setup[1].name != old_identity
    journal = open_journal(journal_setup)
    try:
        done = journal.advance(BIG)
        assert json.loads(done)['status'] == 'completed'
        monkeypatch.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('retry RHS'))
        assert journal.advance(BIG) == done
    finally: close_journal(journal)
    fresh = open_journal(journal_setup, create=False)
    try: assert fresh.inspect() == done
    finally: close_journal(fresh)


@pytest.mark.parametrize('old_version', [1, 2])
def test_previous_private_domains_cannot_resume_as_current(journal_setup, monkeypatch, old_version):
    journal = open_journal(journal_setup)
    try: progress = json.loads(journal.inspect())
    finally: close_journal(journal)
    path = journal_setup[1]/'proofs'/(progress['head_sha256']+'.json')
    payload = json.loads(path.read_bytes())['payload']
    payload['version'] = f'crop-cycle-verified-server-head-v{old_version}'
    raw = custody._signed(payload, KEY, f'ossf-crop-cycle-verified-server-head-v{old_version}\0'.encode())
    path.chmod(0o600); path.write_bytes(raw); path.chmod(0o400)
    before = (journal_setup[1]/'artifact/HEAD').read_bytes()
    monkeypatch.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('old proof RHS'))
    with pytest.raises(custody.CalculationCustodyHold): open_journal(journal_setup, create=False)
    assert (journal_setup[1]/'artifact/HEAD').read_bytes() == before
