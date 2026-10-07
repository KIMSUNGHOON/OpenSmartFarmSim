"""Real crop equations through a separate verified calculation factory."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_cycle_calculation_context as candidate
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as legacy
from app import crop_cycle_artifact as artifact
from app import crop_cycle_input_read_context as read_context
from app import crop_plant_startup_integration as physical
from test_crop_cycle_input_evidence import authority, KEY
from test_crop_cycle_artifact import CASES, PROFILES, NOTICE
from test_crop_cycle_input_stream import write


def packet(tmp_path, program=None):
    directory = tmp_path / 'inputs'
    root = write(directory, program)['root_sha256']
    for path in directory.iterdir():
        path.chmod(0o400)
    server = authority()
    return directory, root, server, server.issue(directory, root)


def finish(context, quota=7, transitions=13, checkpoint=None):
    cp = checkpoint if checkpoint is not None else candidate.start(context)
    output_offset, event_offset = cp['output_cursor'], cp['event_cursor']
    samples, events = [], []
    while True:
        result = candidate.advance_chunk(context, cp, {'max_steps': quota, 'max_transitions': transitions})
        assert result['output_start'] == output_offset + len(samples)
        assert result['event_start'] == event_offset + len(events)
        samples.extend(result['samples']); events.extend(result['events'])
        if result['status'] != 'yielded':
            return {**result, 'samples': samples, 'events': events}
        cp = candidate.restore_checkpoint(context, candidate.checkpoint_bytes(context, result['checkpoint']))


@pytest.mark.parametrize('quota,transitions', [(1, 1), (7, 13), (10000, 10000)])
@pytest.mark.parametrize('case', CASES, ids=lambda c: c['case_id'])
def test_actual_equations_and_all_original_physical_outputs_without_full_reprepare(tmp_path, case, quota, transitions, monkeypatch):
    program = deepcopy(case['program'])
    expected = physical.integrate_plant_startup(**program, **PROFILES)
    directory, root, server, raw = packet(tmp_path, program)
    old_manifest = json.loads(raw)['payload']['context']['manifest']
    before = len(os.listdir('/proc/self/fd'))
    def forbidden(*a, **k):
        pytest.fail('repeated full input parser/context preparation')
    monkeypatch.setattr(inputs, 'open_input_packet', forbidden)
    monkeypatch.setattr(legacy, 'prepare_context', forbidden)
    with candidate.open_calculation_context(directory, root, raw, authority=server) as context:
        manifest = context.manifest
        assert manifest['engine_version'] == candidate.VERSION
        assert manifest['code_sha256']['stream_execution'] == candidate.CODE_SHA256
        assert manifest['code_sha256'] == {**old_manifest['code_sha256'], 'stream_execution': candidate.CODE_SHA256}
        assert set(manifest) == set(old_manifest) | {'input_validation'}
        assert set(manifest['input_validation']) == {'version', 'evidence_sha256', 'validated_context_sha256',
            'validation_engine_version', 'validation_code_sha256', 'input_evidence_code_sha256',
            'input_evidence_dependency_sha256'}
        for key in old_manifest:
            if key not in ('engine_version', 'code_sha256'):
                assert manifest[key] == old_manifest[key]
        assert manifest['input_validation']['validated_context_sha256'] == json.loads(raw)['payload']['context']['context_sha256']
        assert context.rights_or_gate_approval is False
        result = finish(context, quota, transitions)
        for field in ('status', 'scope', 'samples', 'events', 'steps', 'planned_steps'):
            assert result[field] == expected[field]
        assert result['checkpoint']['version'] == candidate.CHECKPOINT_VERSION
        assert result['checkpoint']['boundary_cursor'] == context.boundary_count
        assert result['checkpoint']['sequence'] == result['steps'] + context.boundary_count
        assert len(context.reader._cache) <= 4 and len(context._cache) <= 2
        with pytest.raises(legacy.CycleStreamExecutionRejected):
            legacy.start(context)
        with pytest.raises(artifact.CycleArtifactRejected):
            artifact.create_writer(tmp_path / 'old-artifact', context, notice_raw=NOTICE)
    assert not (tmp_path / 'old-artifact').exists()
    assert len(os.listdir('/proc/self/fd')) == before
    assert context.reader.closed and not context.reader._cache and not context._cache


@pytest.mark.parametrize('kind', ['entry', 'pre-onset', 'carbon-without-number', 'underflow', 'event'])
def test_original_numerical_hold_and_confirmed_past(tmp_path, kind):
    program = deepcopy(next(c['program'] for c in CASES if c['case_id'] == (
        'full-removal-reentry' if kind == 'event' else 'empty-entry')))
    initial = program['initial_state']['values']
    if kind == 'entry':
        program['segments'][0]['fruit_entry']['values']['fruit_number_inflow']['value'] = 100
    elif kind == 'pre-onset':
        initial['temperature_sum']['value'] = 0
    elif kind == 'carbon-without-number':
        initial['fruit_carbohydrate'][0]['value'] = 1
    elif kind == 'underflow':
        initial['stem_root']['value'] = 5e-324
    else:
        program['events'][1]['removals']['values']['leaf']['value'] = 1e6
    expected = physical.integrate_plant_startup(**program, **PROFILES)
    directory, root, server, raw = packet(tmp_path, program)
    with candidate.open_calculation_context(directory, root, raw, authority=server) as context:
        actual = finish(context, 1, 1)
        for field in ('status', 'hold', 'samples', 'events', 'steps', 'planned_steps', 'last_confirmed'):
            assert actual[field] == expected[field]
        assert actual['checkpoint'] is None


@pytest.mark.parametrize('change', ['blob', 'root', 'missing', 'extra', 'writable', 'replace-directory',
    'file-symlink', 'directory-symlink', 'hardlink', 'directory-mode'])
def test_changes_after_open_prevent_return_and_close_owned_descriptors(tmp_path, change):
    directory, root, server, raw = packet(tmp_path)
    before = len(os.listdir('/proc/self/fd'))
    context = candidate.open_calculation_context(directory, root, raw, authority=server)
    cp = candidate.start(context)
    target = next(p for p in directory.iterdir() if p.name != 'root.json')
    if change == 'root':
        target = directory / 'root.json'
    if change in ('blob', 'root'):
        target.chmod(0o600); target.write_bytes(target.read_bytes() + b' '); target.chmod(0o400)
    elif change == 'missing':
        target.unlink()
    elif change == 'extra':
        (directory / 'extra.json').write_bytes(b'[]')
    elif change == 'writable':
        target.chmod(0o600)
    elif change == 'file-symlink':
        outside = tmp_path / 'outside'; outside.write_bytes(target.read_bytes())
        target.unlink(); target.symlink_to(outside)
    elif change == 'directory-symlink':
        directory.rename(tmp_path / 'old-inputs'); directory.symlink_to(tmp_path / 'old-inputs', target_is_directory=True)
    elif change == 'hardlink':
        os.link(target, tmp_path / 'extra-link')
    elif change == 'directory-mode':
        directory.chmod(0o755)
    else:
        directory.rename(tmp_path / 'old-inputs'); directory.mkdir(mode=0o700)
        for source in (tmp_path / 'old-inputs').iterdir():
            dest = directory / source.name; dest.write_bytes(source.read_bytes()); dest.chmod(0o400)
    with pytest.raises(candidate.CalculationContextHold):
        candidate.advance_chunk(context, cp, {'max_steps': 1, 'max_transitions': 1})
    assert context.reader.closed and len(os.listdir('/proc/self/fd')) == before


def test_owner_mismatch_is_a_calculation_hold_and_closes_context(tmp_path, monkeypatch):
    directory, root, server, raw = packet(tmp_path)
    before = len(os.listdir('/proc/self/fd'))
    context = candidate.open_calculation_context(directory, root, raw, authority=server)
    owner = os.geteuid()
    monkeypatch.setattr(os, 'geteuid', lambda: owner + 1)
    with pytest.raises(candidate.CalculationContextHold):
        candidate.start(context)
    assert context.reader.closed and len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('position', ['initial', 't0-committed', 'internal-step', 'pending-event'])
def test_fresh_python_restores_exact_checkpoint_and_remaining_chain(tmp_path, position):
    program = deepcopy(next(c['program'] for c in CASES if c['case_id'] == 'full-removal-reentry'))
    directory, root, server, raw = packet(tmp_path, program)
    with candidate.open_calculation_context(directory, root, raw, authority=server) as context:
        cp = candidate.start(context)
        if position != 'initial':
            cp = candidate.advance_chunk(context, cp, {'max_steps': 1, 'max_transitions': 1})['checkpoint']
        if position == 'internal-step':
            cp = candidate.advance_chunk(context, cp, {'max_steps': 1, 'max_transitions': 1})['checkpoint']
        if position == 'pending-event':
            for _ in range(10000):
                if cp['at'] == program['events'][1]['at'] and cp['phase'] == 'step-end':
                    break
                cp = candidate.advance_chunk(context, cp, {'max_steps': 1, 'max_transitions': 1})['checkpoint']
            else:
                pytest.fail('original management boundary not reached')
        cp_raw = candidate.checkpoint_bytes(context, cp)
        expected = finish(context, checkpoint=cp)
    for name, data in [('key', KEY), ('proof', raw), ('checkpoint', cp_raw)]:
        path = tmp_path / name; path.write_bytes(data); path.chmod(0o400)
    output = tmp_path / 'fresh-python-result.json'
    script = Path(__file__).resolve().parents[2] / 'research/crop-cycle-calculation-context-reference.py'
    child = subprocess.run([sys.executable, str(script), '--directory', str(directory), '--root', root,
        '--evidence', str(tmp_path / 'proof'), '--key', str(tmp_path / 'key'), '--issuer', 'owned-server-test',
        '--key-id', 'test-key-v1', '--checkpoint', str(tmp_path / 'checkpoint'), '--output', str(output)],
        capture_output=True, timeout=60)
    assert child.returncode == 0, child.stderr.decode()
    value = json.loads(output.read_bytes())
    assert value['pid'] != os.getpid()
    assert value['restored_checkpoint'] == cp
    assert value['result'] == expected
    assert value['fd_before'] == value['fd_after']


def test_original_and_read_only_contexts_cannot_calculate_or_migrate(tmp_path):
    directory, root, server, raw = packet(tmp_path)
    with inputs.open_input_packet(directory, root, **PROFILES) as reader:
        old = legacy.prepare_context(reader, **PROFILES)
        checkpoint = legacy.checkpoint_bytes(old, legacy.start(old))
        with pytest.raises(candidate.CalculationContextHold):
            candidate.start(old)
    with read_context.open_input_read_context(directory, root, raw, authority=server) as view:
        with pytest.raises(candidate.CalculationContextHold):
            candidate.start(view)
    with candidate.open_calculation_context(directory, root, raw, authority=server) as context:
        with pytest.raises(candidate.CalculationContextHold):
            candidate.restore_checkpoint(context, checkpoint)


def test_original_checkpoint_state_clock_and_counters_match_under_same_budgets(tmp_path):
    program = deepcopy(next(c['program'] for c in CASES if c['case_id'] == 'full-removal-reentry'))
    directory, root, server, raw = packet(tmp_path, program)
    identity_fields = {'version', 'root_sha256', 'parent_sha256', 'checkpoint_sha256'}
    def compare(old, new):
        assert {k: v for k, v in old.items() if k not in identity_fields} == {
            k: v for k, v in new.items() if k not in identity_fields}
    with inputs.open_input_packet(directory, root, **PROFILES) as reader:
        old_context = legacy.prepare_context(reader, **PROFILES)
        with candidate.open_calculation_context(directory, root, raw, authority=server) as new_context:
            old, new = legacy.start(old_context), candidate.start(new_context)
            compare(old, new)
            for budget in ({'max_steps': 1, 'max_transitions': 1}, {'max_steps': 7, 'max_transitions': 13},
                           {'max_steps': 10000, 'max_transitions': 10000}):
                before = legacy.advance_chunk(old_context, old, budget)
                after = candidate.advance_chunk(new_context, new, budget)
                for key in ('status', 'scope', 'steps', 'planned_steps', 'output_start', 'event_start', 'samples', 'events'):
                    assert before[key] == after[key]
                old, new = before['checkpoint'], after['checkpoint']
                compare(old, new)
            assert before['status'] == after['status'] == 'completed'


def test_one_operation_has_two_full_byte_checks_and_no_nested_reprepare(tmp_path, monkeypatch):
    directory, root, server, raw = packet(tmp_path)
    original = server.verify
    calls = []
    def verify(*a, **k):
        calls.append('verify')
        return original(*a, **k)
    monkeypatch.setattr(server, 'verify', verify)
    with candidate.open_calculation_context(directory, root, raw, authority=server) as context:
        assert len(calls) == 2
        cp = candidate.start(context)
        assert len(calls) == 4
        result = candidate.advance_chunk(context, cp, {'max_steps': 1, 'max_transitions': 1})
        assert len(calls) == 6
        encoded = candidate.checkpoint_bytes(context, result['checkpoint'])
        assert len(calls) == 8
        assert candidate.restore_checkpoint(context, encoded) == result['checkpoint']
        assert len(calls) == 10


def test_input_changed_during_actual_rhs_is_not_returned_as_success(tmp_path, monkeypatch):
    directory, root, server, raw = packet(tmp_path)
    before = len(os.listdir('/proc/self/fd'))
    context = candidate.open_calculation_context(directory, root, raw, authority=server)
    cp = candidate.start(context)
    cp = candidate.advance_chunk(context, cp, {'max_steps': 1, 'max_transitions': 1})['checkpoint']
    original = legacy.short._Evaluator.rhs
    def changed(self, *a, **k):
        target = directory / 'root.json'
        target.chmod(0o600); target.write_bytes(target.read_bytes() + b' '); target.chmod(0o400)
        return original(self, *a, **k)
    monkeypatch.setattr(legacy.short._Evaluator, 'rhs', changed)
    with pytest.raises(candidate.CalculationContextHold):
        candidate.advance_chunk(context, cp, {'max_steps': 1, 'max_transitions': 1})
    assert context.reader.closed and len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('change', ['raw-suffix', 'root', 'key', 'issuer', 'authority-type'])
def test_failed_factory_never_leaves_descriptors(tmp_path, change):
    directory, root, server, raw = packet(tmp_path)
    if change == 'raw-suffix':
        raw += b'\n'
    elif change == 'root':
        root = '0' * 64
    elif change == 'key':
        server = authority(key=b'other-owned-synthetic-key-32-bytes!')
    elif change == 'issuer':
        server = authority(issuer='other-owned-issuer')
    else:
        server = {}
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(candidate.CalculationContextHold):
        candidate.open_calculation_context(directory, root, raw, authority=server)
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('change', ['calculation-source', 'dependency-source', 'key', 'notice'])
def test_changed_code_or_authority_configuration_cannot_reuse_context(tmp_path, monkeypatch, change):
    directory, root, server, raw = packet(tmp_path)
    before = len(os.listdir('/proc/self/fd'))
    context = candidate.open_calculation_context(directory, root, raw, authority=server)
    if change.endswith('source'):
        source = tmp_path / 'changed-source.py'; source.write_text('owned changed source')
        monkeypatch.setattr(candidate if change == 'calculation-source' else legacy, '__file__', str(source))
    elif change == 'key':
        server.integrity_key = b'other-owned-synthetic-key-32-bytes!'
    else:
        server.notice_raw += b'\n'
    with pytest.raises(candidate.CalculationContextHold):
        candidate.start(context)
    assert context.reader.closed and len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('change', ['checksum', 'seed', 'clock', 'counter', 'version', 'root'])
def test_rehashed_inconsistent_checkpoint_is_rejected(tmp_path, change):
    directory, root, server, raw = packet(tmp_path)
    with candidate.open_calculation_context(directory, root, raw, authority=server) as context:
        cp = candidate.start(context)
        cp = candidate.advance_chunk(context, cp, {'max_steps': 1, 'max_transitions': 2})['checkpoint']
        if change == 'checksum':
            cp['checkpoint_sha256'] = '0' * 64
        else:
            if change == 'seed':
                cp['seed'][0] += 1.0
            elif change == 'clock':
                cp['clock']['prefix']['numerator'] = '999'
            elif change == 'counter':
                cp['steps'] += 1
            elif change == 'version':
                cp['version'] = legacy.CHECKPOINT_VERSION
            else:
                cp['root_sha256'] = '0' * 64
            legacy._seal(cp)
        with pytest.raises(candidate.CalculationContextHold):
            candidate.restore_checkpoint(context, inputs._canonical(cp))
