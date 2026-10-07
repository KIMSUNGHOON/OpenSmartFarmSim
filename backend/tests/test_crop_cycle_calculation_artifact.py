from copy import deepcopy
from hashlib import sha256
import json
import os

import pytest

from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_context as engine
from app import crop_cycle_artifact as old_artifact
from app import crop_plant_startup_integration as physical
from test_crop_cycle_artifact import CASES, PROFILES, NOTICE, program
from test_crop_cycle_calculation_context import packet

BUDGET = {'max_steps': 17, 'max_transitions': 31}


def context(tmp_path, value=None):
    directory, root, server, raw = packet(tmp_path, value)
    return engine.open_calculation_context(directory, root, raw, authority=server), server


def finish(writer):
    while writer.advance(BUDGET)['status'] == 'yielded':
        pass
    return writer.finalize()


def rows(reader, kind):
    values, offset = [], 0
    while True:
        page = reader.page(kind, offset, 2)
        assert len(artifact._canonical(page)) <= artifact.LIMITS['page_bytes']
        values.extend(page['records']); offset = page['next']
        if offset == page['total']:
            return values


@pytest.fixture(scope='module')
def originals():
    return {case['case_id']: physical.integrate_plant_startup(**case['program'], **PROFILES) for case in CASES}


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['case_id'])
def test_writer_reader_exact_original_payload_and_read_rhs_zero(tmp_path, case, originals, monkeypatch):
    ctx, _ = context(tmp_path, case['program'])
    before = len(os.listdir('/proc/self/fd'))
    with ctx:
        with artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE) as writer:
            receipt = finish(writer)
            assert writer.finalize() == receipt
        assert not ctx.reader.closed
        def forbidden(*args, **kwargs):
            pytest.fail('read evaluated crop equations')
        monkeypatch.setattr(engine, 'advance_chunk', forbidden)
        monkeypatch.setattr(engine.short._Evaluator, 'rhs', forbidden)
        monkeypatch.setattr(physical, 'integrate_plant_startup', forbidden)
        with artifact.open_artifact(tmp_path / 'result', receipt['artifact_sha256'], ctx, notice_raw=NOTICE) as reader:
            expected = originals[case['case_id']]; summary = reader.summary
            for key in ('status', 'scope', 'steps', 'planned_steps'):
                assert summary[key] == expected[key]
            for kind in ('samples', 'events'):
                assert rows(reader, kind) == expected[kind]
            assert receipt['artifact_id'].startswith('crop-cycle-verified-artifact-v1:')
            assert summary['checkpoint']['version'] == engine.CHECKPOINT_VERSION
            summary['counts']['samples'] = 999
            assert reader.summary['counts']['samples'] == len(expected['samples'])
        assert not ctx.reader.closed
    assert len(os.listdir('/proc/self/fd')) == before - 1
    assert not any(p.name.endswith('.tmp') for p in (tmp_path / 'result').iterdir())


@pytest.mark.parametrize('kind', ['entry', 'pre-onset', 'carbon-without-number', 'underflow', 't0-event', 'event', 'fractional'])
def test_holds_and_empty_confirmed_past_match_original(tmp_path, kind, monkeypatch):
    value = program('full-removal-reentry' if kind in ('t0-event', 'event') else 'night-smooth' if kind == 'fractional' else 'empty-entry')
    initial = value['initial_state']['values']
    if kind == 'entry': value['segments'][0]['fruit_entry']['values']['fruit_number_inflow']['value'] = 100
    if kind == 'pre-onset': initial['temperature_sum']['value'] = 0
    if kind == 'carbon-without-number': initial['fruit_carbohydrate'][0]['value'] = 1
    if kind == 'underflow': initial['stem_root']['value'] = 5e-324
    if kind in ('t0-event', 'event'): value['events'][0 if kind == 't0-event' else 1]['removals']['values']['leaf']['value'] = 1e6
    if kind == 'fractional':
        initial['buffer']['value'] = 1; value['output_times'] = [value['output_times'][0], value['output_times'][-1]]
        value['solver']['max_step_seconds'] = 3599
    expected = physical.integrate_plant_startup(**value, **PROFILES)
    ctx, _ = context(tmp_path, value)
    with ctx:
        with artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE) as writer:
            receipt = finish(writer)
        monkeypatch.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('read RHS'))
        with artifact.open_artifact(tmp_path / 'result', receipt['artifact_sha256'], ctx, notice_raw=NOTICE) as reader:
            actual = {**reader.summary, 'samples': rows(reader, 'samples'), 'events': rows(reader, 'events')}
            for key in ('status', 'scope', 'steps', 'planned_steps', 'hold', 'last_confirmed', 'samples', 'events'):
                assert actual[key] == expected[key]
            assert actual['checkpoint'] is None


def test_public_input_checks_are_bounded_per_operation_not_per_commit(tmp_path, monkeypatch):
    ctx, server = context(tmp_path, program('full-removal-reentry'))
    verify, calls = server.verify, []
    def checked(*args, **kwargs):
        calls.append('verify'); return verify(*args, **kwargs)
    monkeypatch.setattr(server, 'verify', checked)
    monkeypatch.setattr(engine.inputs, 'open_input_packet', lambda *a, **k: pytest.fail('full parser'))
    monkeypatch.setattr(engine.legacy, 'prepare_context', lambda *a, **k: pytest.fail('full prepare'))
    with ctx:
        writer = artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE)
        assert len(calls) == 3
        while True:
            before = len(calls); status = writer.advance(BUDGET)['status']
            assert len(calls) - before == 5
            if status != 'yielded': break
        head = writer.head_sha256; writer.close()
        before = len(calls)
        writer = artifact.open_writer(tmp_path / 'result', head, ctx, notice_raw=NOTICE)
        assert len(calls) - before == 2
        before = len(calls); receipt = writer.finalize()
        assert len(calls) - before == 3
        writer.close(); before = len(calls)
        reader = artifact.open_artifact(tmp_path / 'result', receipt['artifact_sha256'], ctx, notice_raw=NOTICE)
        assert len(calls) - before == 2
        before = len(calls); reader.summary
        assert len(calls) - before == 2
        before = len(calls); reader.page('samples', 0, 1)
        assert len(calls) - before == 2
        reader.close(); assert not ctx.reader.closed


@pytest.mark.parametrize('change', ['root', 'blob', 'writable', 'directory-mode', 'symlink', 'key'])
def test_current_input_failure_closes_writer_without_publishing(tmp_path, change):
    ctx, server = context(tmp_path)
    with ctx:
        writer = artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE)
        before = (tmp_path / 'result/HEAD').read_bytes()
        target = ctx._directory / 'root.json' if change == 'root' else next(p for p in ctx._directory.iterdir() if p.name != 'root.json')
        if change in ('root', 'blob'):
            target.chmod(0o600); target.write_bytes(target.read_bytes() + b' '); target.chmod(0o400)
        elif change == 'writable': target.chmod(0o600)
        elif change == 'directory-mode': ctx._directory.chmod(0o755)
        elif change == 'symlink':
            outside = tmp_path / 'outside'; outside.write_bytes(target.read_bytes()); target.unlink(); target.symlink_to(outside)
        else: server.integrity_key = b'changed-owned-synthetic-server-key!'
        with pytest.raises(artifact.CalculationArtifactHold): writer.advance(BUDGET)
        assert writer.closed and ctx.reader.closed
        assert (tmp_path / 'result/HEAD').read_bytes() == before


def test_pending_event_resume_keeps_exact_checkpoint_and_single_event(tmp_path):
    value = program('full-removal-reentry'); ctx, _ = context(tmp_path, value)
    with ctx:
        with artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE) as writer:
            while writer._checkpoint['at'] != value['events'][1]['at']:
                writer.advance({'max_steps': 1, 'max_transitions': 1})
            assert writer._checkpoint['phase'] == 'step-end'
            before = deepcopy(writer._checkpoint); head = writer.head_sha256
        with artifact.open_writer(tmp_path / 'result', head, ctx, notice_raw=NOTICE) as writer:
            assert writer._checkpoint == before
            receipt = finish(writer)
        with artifact.open_artifact(tmp_path / 'result', receipt['artifact_sha256'], ctx, notice_raw=NOTICE) as reader:
            assert rows(reader, 'events') == physical.integrate_plant_startup(**value, **PROFILES)['events']


@pytest.mark.parametrize('when', ['before-head', 'after-head'])
def test_head_publication_failure_closes_and_resumes_actual_prefix(tmp_path, when, monkeypatch):
    ctx, _ = context(tmp_path)
    with ctx:
        writer = artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE)
        before = deepcopy(writer._checkpoint); publish = writer._publish_head
        def changed(value):
            if when == 'after-head': publish(value)
            raise OSError('owned injected publication failure')
        monkeypatch.setattr(writer, '_publish_head', changed)
        with pytest.raises(artifact.CalculationArtifactHold):
            writer.advance({'max_steps': 1, 'max_transitions': 1})
        assert writer.closed
        head = sha256((tmp_path / 'result/HEAD').read_bytes()).hexdigest()
        with artifact.open_writer(tmp_path / 'result', head, ctx, notice_raw=NOTICE) as resumed:
            if when == 'before-head': assert resumed._checkpoint == before
            else: assert resumed._checkpoint['boundary_cursor'] == 1
            receipt = finish(resumed)
        with artifact.open_artifact(tmp_path / 'result', receipt['artifact_sha256'], ctx, notice_raw=NOTICE) as reader:
            assert reader.summary['status'] == 'completed'


@pytest.mark.parametrize('budget', [{}, None, {'max_steps': True, 'max_transitions': 1}, {'max_steps': 1, 'max_transitions': 129}])
def test_invalid_budget_rejects_before_rhs_and_closes_handle(tmp_path, budget, monkeypatch):
    ctx, _ = context(tmp_path)
    with ctx:
        writer = artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE)
        before = (tmp_path / 'result/HEAD').read_bytes()
        monkeypatch.setattr(engine, 'advance_chunk', lambda *a, **k: pytest.fail('RHS started'))
        with pytest.raises(artifact.CalculationArtifactHold): writer.advance(budget)
        assert writer.closed and not ctx.reader.closed
        assert (tmp_path / 'result/HEAD').read_bytes() == before


def test_changed_limits_and_cross_version_context_are_rejected(tmp_path, monkeypatch):
    ctx, _ = context(tmp_path)
    with ctx:
        with pytest.raises(old_artifact.CycleArtifactRejected): old_artifact.create_writer(tmp_path / 'old', ctx, notice_raw=NOTICE)
        assert not (tmp_path / 'old').exists()
        monkeypatch.setitem(artifact.LIMITS, 'directory_bytes', 999999999)
        with pytest.raises(artifact.CalculationArtifactHold): artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE)
        assert not (tmp_path / 'result').exists()
