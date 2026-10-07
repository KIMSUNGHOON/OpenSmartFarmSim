"""Calendar versioning keeps synthetic values; no cultivation evidence."""
from datetime import datetime, timedelta
from hashlib import sha256
import importlib.util
import os
from pathlib import Path

import pytest

from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from test_crop_cycle_artifact import PROFILES
from test_crop_cycle_input_stream import program, write


@pytest.fixture
def translation():
    path = Path(__file__).resolve().parents[2]/'research/crop-cycle-calendar-translation.py'
    spec = importlib.util.spec_from_file_location('calendar_translation', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('offset_days', [273, -273])
def test_shift_preserves_every_value_clock_grid_and_actual_rhs(translation, tmp_path, offset_days):
    source, target = tmp_path/'source', tmp_path/'target'
    original = write(source, program())
    before = {p.name: (sha256(p.read_bytes()).hexdigest(), p.stat().st_mode, p.stat().st_ino)
              for p in source.iterdir()}
    descriptors = len(os.listdir('/proc/self/fd'))
    receipt = translation.translate_packet(source, original['root_sha256'], target,
        offset_days=offset_days, program_id='owned-calendar-test-v1', **PROFILES)
    assert receipt['version'] == 'crop-cycle-calendar-translation-v1'
    assert receipt['source_root_sha256'] == original['root_sha256']
    assert receipt['target_root_sha256'] != original['root_sha256']
    assert receipt['offset_seconds'] == offset_days*86400 and receipt['rights_or_gate_approval'] is False
    with inputs.open_input_packet(source, original['root_sha256'], **PROFILES) as old:
        with inputs.open_input_packet(target, receipt['target_root_sha256'], **PROFILES) as new:
            for key in ('initial_state', 'solver', 'profile_sha256', 'normalization_sha256', 'python_version'):
                assert old.manifest[key] == new.manifest[key]
            for kind in inputs.KINDS:
                for index in range(old.manifest['streams'][kind]['count']):
                    a, b = old.record(kind, index), new.record(kind, index)
                    if kind in ('anchors', 'outputs'):
                        assert datetime.fromisoformat(b)-datetime.fromisoformat(a) == timedelta(days=offset_days)
                    else:
                        keys = ('start', 'end') if kind == 'segments' else ('at',)
                        for key in keys:
                            assert datetime.fromisoformat(b.pop(key))-datetime.fromisoformat(a.pop(key)) == timedelta(days=offset_days)
                        assert a == b
                row = receipt['streams'][kind]
                assert row['source_record_chain_sha256'] == row['target_restored_record_chain_sha256']
            contexts = [engine.prepare_context(reader, **PROFILES) for reader in (old, new)]
            assert contexts[0].seed == contexts[1].seed
            outcomes = [engine.advance_chunk(c, engine.start(c), {'max_steps':17,'max_transitions':31})
                        for c in contexts]
            assert outcomes[0]['checkpoint']['y'] == outcomes[1]['checkpoint']['y']
            for key in ('steps','phase','seed','event_cursor','output_cursor'):
                assert outcomes[0]['checkpoint'][key] == outcomes[1]['checkpoint'][key]
            assert old.segment(0)['clock']['prefix'] == new.segment(0)['clock']['prefix']
            assert old.segment(0)['clock']['slope'] == new.segment(0)['clock']['slope']
    assert len(os.listdir('/proc/self/fd')) == descriptors
    assert before == {p.name: (sha256(p.read_bytes()).hexdigest(), p.stat().st_mode, p.stat().st_ino)
                      for p in source.iterdir()}


@pytest.mark.parametrize('days', [True, 0, 1.5, -367, 367, None])
def test_invalid_shift_has_no_output(translation, tmp_path, days):
    with pytest.raises(ValueError):
        translation.translate_packet(tmp_path/'missing', 'a'*64, tmp_path/'target',
            offset_days=days, program_id='owned-calendar-test-v1', **PROFILES)
    assert not (tmp_path/'target').exists()


def test_bad_source_hash_and_existing_destination_preserve_both(translation, tmp_path):
    source, target = tmp_path/'source', tmp_path/'target'
    original = write(source, program())
    with pytest.raises(ValueError):
        translation.translate_packet(source, 'a'*64, target, offset_days=273,
            program_id='owned-calendar-test-v1', **PROFILES)
    assert not target.exists()
    target.mkdir(); (target/'keep').write_bytes(b'existing history')
    with pytest.raises(ValueError):
        translation.translate_packet(source, original['root_sha256'], target, offset_days=273,
            program_id='owned-calendar-test-v1', **PROFILES)
    assert (target/'keep').read_bytes() == b'existing history'
