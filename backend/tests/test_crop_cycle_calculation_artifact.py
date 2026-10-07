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
from test_crop_cycle_calculation_context import packet, finish as calculate_only

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
        pure = calculate_only(ctx, 17, 31)
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
                assert summary[key] == pure[key]
            assert summary['checkpoint'] == pure['checkpoint']
            assert summary['manifest'] == pure['manifest']
            for kind in ('samples', 'events'):
                assert rows(reader, kind) == expected[kind]
                assert rows(reader, kind) == pure[kind]
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


def test_unhashable_page_kind_is_typed_and_closes_reader(tmp_path):
    ctx, _ = context(tmp_path)
    with ctx:
        with artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE) as writer:
            receipt = finish(writer)
        reader = artifact.open_artifact(tmp_path / 'result', receipt['artifact_sha256'], ctx, notice_raw=NOTICE)
        with pytest.raises(artifact.CalculationArtifactHold): reader.page([], 0, 1)
        assert reader.closed and not ctx.reader.closed


def test_changed_context_profile_closes_borrowed_invalid_context(tmp_path):
    ctx, _ = context(tmp_path)
    with ctx:
        writer = artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE)
        before = (tmp_path / 'result/HEAD').read_bytes()
        object.__setattr__(ctx, 'growth_profile', object())
        with pytest.raises(artifact.CalculationArtifactHold): writer.advance(BUDGET)
        assert writer.closed and ctx.reader.closed
        assert (tmp_path / 'result/HEAD').read_bytes() == before


@pytest.fixture
def completed(tmp_path):
    ctx, _ = context(tmp_path, program('full-removal-reentry'))
    with ctx:
        path = tmp_path / 'result'
        with artifact.create_writer(path, ctx, notice_raw=NOTICE) as writer:
            receipt = finish(writer)
        yield path, ctx, receipt


def put_blob(path, value):
    raw = artifact._canonical(value); digest = sha256(raw).hexdigest()
    target = path / (digest + '.json')
    if target.exists(): assert target.read_bytes() == raw
    else: target.write_bytes(raw)
    return digest


def rehash_terminal(path, receipt, change):
    root = json.loads((path / (receipt['artifact_sha256'] + '.json')).read_bytes())
    old = root['commits'][-1]
    chunk = json.loads((path / (old + '.json')).read_bytes())
    change(chunk, root, path)
    digest = put_blob(path, chunk)
    if digest != old: root['commits'][root['commits'].index(old)] = digest
    root_sha = put_blob(path, root)
    head = json.loads((path / 'HEAD').read_bytes())
    head.update(artifact_sha256=root_sha, latest_commit_sha256=digest)
    (path / 'HEAD').chmod(0o600); (path / 'HEAD').write_bytes(artifact._canonical(head))
    return root_sha


@pytest.mark.parametrize('kind', ['counter-type', 'parent', 'prefix', 'clock', 'balance', 'budget',
    'sample-count', 'sample-time', 'sample-lai', 'event-removal', 'result-shape', 'root-status', 'root-order'])
def test_rehashed_semantic_tampering_is_rejected_without_rhs(completed, kind, monkeypatch):
    path, ctx, receipt = completed
    def change(chunk, root, path):
        if kind == 'counter-type': chunk['result']['event_start'] = 0.0
        if kind in ('parent', 'prefix', 'clock', 'balance'):
            cp = chunk['result']['checkpoint']
            if kind == 'parent': cp['parent_sha256'] = '0' * 64
            if kind == 'prefix': cp['output_prefix_sha256'] = '0' * 64
            if kind == 'clock': cp['clock']['prefix']['numerator'] = '1'
            if kind == 'balance': cp['y'][0] += 100
            engine._seal(cp)
        if kind == 'budget': chunk['budget']['max_steps'] = True
        if kind == 'sample-count': chunk['pages']['samples'][0]['count'] += 1
        if kind == 'sample-time': chunk['pages']['samples'][0]['first_at'] = '2025-01-01T00:00:00Z'
        if kind in ('sample-lai', 'event-removal'):
            category = 'samples' if kind == 'sample-lai' else 'events'
            descriptor = chunk['pages'][category][0]
            values = json.loads((path / (descriptor['sha256'] + '.json')).read_bytes())
            if kind == 'sample-lai': values[0]['lai']['value'] += 1
            else: values[0]['removed']['leaf']['value'] += 1
            descriptor['sha256'] = put_blob(path, values)
        if kind == 'result-shape': chunk['result'] = None
        if kind == 'root-status': root['status'] = 'hold'
        if kind == 'root-order': root['commits'].reverse()
    root = rehash_terminal(path, receipt, change)
    monkeypatch.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('tamper read RHS'))
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(artifact.CalculationArtifactHold):
        artifact.open_artifact(path, root, ctx, notice_raw=NOTICE)
    assert len(os.listdir('/proc/self/fd')) == before and not ctx.reader.closed


@pytest.mark.parametrize('kind', ['hash', 'symlink', 'fifo', 'oversize', 'missing', 'utf8', 'duplicates'])
def test_bad_root_files_are_typed_and_close_fd(completed, kind):
    path, ctx, receipt = completed; digest = receipt['artifact_sha256']
    target = path / (digest + '.json')
    if kind == 'hash': target.chmod(0o600); target.write_bytes(b'{}')
    if kind == 'symlink': target.unlink(); target.symlink_to(path / 'HEAD')
    if kind == 'fifo': target.unlink(); os.mkfifo(target)
    if kind == 'oversize':
        target.chmod(0o600)
        with target.open('wb') as f: f.truncate(artifact.LIMITS['root_bytes'] + 1)
    if kind == 'missing': target.unlink()
    if kind in ('utf8', 'duplicates'):
        raw = b'\xff' if kind == 'utf8' else b'{"x":1,"x":2}'
        digest = sha256(raw).hexdigest(); (path / (digest + '.json')).write_bytes(raw)
        head = json.loads((path / 'HEAD').read_bytes()); head['artifact_sha256'] = digest
        (path / 'HEAD').chmod(0o600); (path / 'HEAD').write_bytes(artifact._canonical(head))
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(artifact.CalculationArtifactHold): artifact.open_artifact(path, digest, ctx, notice_raw=NOTICE)
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('kind,start,limit', [('samples', True, 1), ('samples', -1, 1), ('samples', 999, 1),
    ('samples', 0, 65), ('events', 0, 9), ('events', 0, True), ('unknown', 0, 1), (None, 0, 1)])
def test_cursor_failures_close_reader_and_end_page_is_empty(completed, kind, start, limit):
    path, ctx, receipt = completed
    reader = artifact.open_artifact(path, receipt['artifact_sha256'], ctx, notice_raw=NOTICE)
    with pytest.raises(artifact.CalculationArtifactHold): reader.page(kind, start, limit)
    assert reader.closed
    with artifact.open_artifact(path, receipt['artifact_sha256'], ctx, notice_raw=NOTICE) as reader:
        end = reader.page('samples', reader.summary['counts']['samples'], 64)
        assert end['records'] == [] and end['next'] == end['total']
    with pytest.raises(artifact.CalculationArtifactHold): reader.summary


def test_selected_blob_is_rehashed_and_returned_values_are_isolated(completed):
    path, ctx, receipt = completed
    reader = artifact.open_artifact(path, receipt['artifact_sha256'], ctx, notice_raw=NOTICE)
    first = reader.page('samples', 0, 1); first['records'][0]['state']['buffer']['value'] = 999
    assert reader.page('samples', 0, 1)['records'][0]['state']['buffer']['value'] != 999
    assert len(reader._page_cache) == 2 and len(reader._page_cache[1]) <= 128
    target = path / (reader._index['samples'][0]['sha256'] + '.json')
    target.chmod(0o600); target.write_bytes(b'[]')
    with pytest.raises(artifact.CalculationArtifactHold, match='HASH_HOLD'): reader.page('samples', 0, 1)
    assert reader.closed and reader._page_cache is None


@pytest.mark.parametrize('kind', ['orphan-bytes', 'nonregular-orphan', 'commit-count'])
def test_original_resource_limits_fail_before_rhs(tmp_path, kind, monkeypatch):
    ctx, _ = context(tmp_path)
    with ctx:
        writer = artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE)
        head = (tmp_path / 'result/HEAD').read_bytes()
        if kind == 'orphan-bytes':
            with (tmp_path / 'result/orphan.tmp').open('wb') as f:
                f.truncate(artifact.LIMITS['directory_bytes'] + 1)
        elif kind == 'nonregular-orphan': os.mkfifo(tmp_path / 'result/orphan.tmp')
        else: writer._hashes = ['synthetic-count-boundary'] * artifact.LIMITS['commits']
        monkeypatch.setattr(engine, 'advance_chunk', lambda *a, **k: pytest.fail('resource hold started RHS'))
        with pytest.raises(artifact.CalculationArtifactHold): writer.advance(BUDGET)
        assert writer.closed and (tmp_path / 'result/HEAD').read_bytes() == head
        assert artifact.LIMITS == old_artifact.LIMITS


def change_input(ctx):
    target = ctx._directory / 'root.json'
    target.chmod(0o600); target.write_bytes(target.read_bytes() + b' '); target.chmod(0o400)


@pytest.mark.parametrize('when', ['rhs', 'before-head', 'after-head'])
def test_input_changes_during_computation_or_publication_prevent_return(tmp_path, when, monkeypatch):
    ctx, _ = context(tmp_path)
    with ctx:
        writer = artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE)
        before = (tmp_path / 'result/HEAD').read_bytes()
        if when == 'rhs':
            rhs = engine.short._Evaluator.rhs; changed = []
            def mutate(*args, **kwargs):
                value = rhs(*args, **kwargs)
                if not changed: changed.append(True); change_input(ctx)
                return value
            monkeypatch.setattr(engine.short._Evaluator, 'rhs', mutate)
        elif when == 'before-head':
            pages = writer._pages
            def mutate(values):
                value = pages(values); change_input(ctx); return value
            monkeypatch.setattr(writer, '_pages', mutate)
        else:
            publish = writer._publish_head
            def mutate(value): publish(value); change_input(ctx)
            monkeypatch.setattr(writer, '_publish_head', mutate)
        with pytest.raises(artifact.CalculationArtifactHold): writer.advance(BUDGET)
        assert writer.closed and ctx.reader.closed
        current = (tmp_path / 'result/HEAD').read_bytes()
        if when == 'after-head': assert current != before and json.loads(current)['commit_count'] == 1
        else: assert current == before


def test_input_change_during_page_projection_prevents_return(completed, monkeypatch):
    path, ctx, receipt = completed
    reader = artifact.open_artifact(path, receipt['artifact_sha256'], ctx, notice_raw=NOTICE)
    blob = reader._blob
    def mutate(*args):
        value = blob(*args); change_input(ctx); return value
    monkeypatch.setattr(reader, '_blob', mutate)
    with pytest.raises(artifact.CalculationArtifactHold): reader.page('samples', 0, 1)
    assert reader.closed and ctx.reader.closed and reader._page_cache is None


def test_failed_create_return_removes_only_its_owned_new_directory(tmp_path, monkeypatch):
    ctx, _ = context(tmp_path)
    with ctx:
        publish = artifact.ArtifactWriter._publish_head
        def mutate(self, value): publish(self, value); change_input(ctx)
        monkeypatch.setattr(artifact.ArtifactWriter, '_publish_head', mutate)
        before = len(os.listdir('/proc/self/fd'))
        with pytest.raises(artifact.CalculationArtifactHold): artifact.create_writer(tmp_path / 'result', ctx, notice_raw=NOTICE)
        assert not (tmp_path / 'result').exists() and ctx.reader.closed
        assert len(os.listdir('/proc/self/fd')) == before - 1


def test_lock_stale_head_notice_code_and_existing_directory_rejections(tmp_path, monkeypatch):
    ctx, _ = context(tmp_path)
    with ctx:
        path = tmp_path / 'result'
        with artifact.create_writer(path, ctx, notice_raw=NOTICE) as writer:
            old = writer.head_sha256
            with pytest.raises(artifact.CalculationArtifactHold, match='exclusive'):
                artifact.open_writer(path, old, ctx, notice_raw=NOTICE)
            writer.advance(BUDGET); head = writer.head_sha256
        with pytest.raises(artifact.CalculationArtifactHold): artifact.create_writer(path, ctx, notice_raw=NOTICE)
        assert (path / 'HEAD').exists()
        with pytest.raises(artifact.CalculationArtifactHold, match='HEAD'): artifact.open_writer(path, old, ctx, notice_raw=NOTICE)
        with pytest.raises(artifact.CalculationArtifactHold, match='NOTICE'): artifact.open_writer(path, head, ctx, notice_raw=b'wrong')
        with monkeypatch.context() as m:
            m.setattr(artifact, 'CODE_SHA256', '0' * 64)
            with pytest.raises(artifact.CalculationArtifactHold, match='CODE_HOLD'):
                artifact.open_writer(path, head, ctx, notice_raw=NOTICE)
        with artifact.open_writer(path, head, ctx, notice_raw=NOTICE): pass
        assert not ctx.reader.closed
