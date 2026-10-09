"""A jointly rechecked copy of the original immutable result facts."""
import json
import os

import pytest

from app import crop_cycle_calculation_result_read_context as query
from test_crop_cycle_calculation_result_evidence import authority, case


def prepared(tmp_path, held=False):
    args, _, _ = case(tmp_path, held=held)
    issuer = authority()
    return args + (issuer.issue(*args),), issuer


@pytest.mark.parametrize('held', [False, True])
def test_facts_equal_original_properties_and_are_independent_copies(tmp_path, held):
    args, issuer = prepared(tmp_path, held)
    before = len(os.listdir('/proc/self/fd'))
    with query.open_calculation_result_read_context(*args, authority=issuer) as reader:
        expected = {'summary': reader.summary, 'context': reader.context_record, 'identity': reader.identity}
        facts = reader.facts()
        assert facts == expected
        facts['summary']['counts']['samples'] = -1
        facts['context']['seed'][0] += 1
        facts['identity']['scope'] = 'changed'
        assert reader.facts() == expected
        assert reader.rights_or_gate_approval is False
    assert reader.closed and not reader._cache
    assert len(os.listdir('/proc/self/fd')) == before


def test_facts_verify_whole_current_snapshot_once(tmp_path, monkeypatch):
    args, issuer = prepared(tmp_path)
    with query.open_calculation_result_read_context(*args, authority=issuer) as reader:
        snapshots = []
        original = query.evidence._snapshot

        def counted(*values):
            result = original(*values)
            snapshots.append(result)
            return result

        monkeypatch.setattr(query.evidence, '_snapshot', counted)
        result = reader.facts()
        assert result['summary']['counts']['samples'] >= 1
        assert len(snapshots) == 1


@pytest.mark.parametrize('change', ['input', 'HEAD', 'page', 'authority'])
def test_facts_reject_current_change_and_close(tmp_path, change):
    args, issuer = prepared(tmp_path)
    before = len(os.listdir('/proc/self/fd'))
    reader = query.open_calculation_result_read_context(*args, authority=issuer)
    if change == 'authority':
        issuer.integrity_key = b'changed-result-authority-key-00000000'
    else:
        payload = json.loads(args[-1])['payload']
        target = args[2] / 'root.json' if change == 'input' else args[0] / (
            'HEAD' if change == 'HEAD' else payload['index']['samples'][0]['sha256'] + '.json')
        target.chmod(0o600)
        target.write_bytes(target.read_bytes() + b' ')
        target.chmod(0o400)
    with pytest.raises(query.CalculationResultReadContextHold):
        reader.facts()
    assert reader.closed and not reader._cache
    assert len(os.listdir('/proc/self/fd')) == before


def test_facts_reject_input_change_during_copy_before_return(tmp_path, monkeypatch):
    args, issuer = prepared(tmp_path)
    before = len(os.listdir('/proc/self/fd'))
    reader = query.open_calculation_result_read_context(*args, authority=issuer)
    original = query.inputs._json
    changed = []

    def mutate(raw, *values, **options):
        result = original(raw, *values, **options)
        if raw == reader._summary_raw and not changed:
            target = args[2] / 'root.json'
            target.chmod(0o600)
            target.write_bytes(target.read_bytes() + b' ')
            target.chmod(0o400)
            changed.append(True)
        return result

    monkeypatch.setattr(query.inputs, '_json', mutate)
    with pytest.raises(query.CalculationResultReadContextHold):
        reader.facts()
    assert changed and reader.closed and not reader._cache
    assert len(os.listdir('/proc/self/fd')) == before
