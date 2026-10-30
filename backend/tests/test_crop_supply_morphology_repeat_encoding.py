"""Lossless receipt storage tests, with no crop model or field-data claim."""
from copy import deepcopy
import json

import pytest


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def example(with_leaf=True):
    pins = {'backend/app/' + 'source_' * 100: 'a' * 64}
    parent = {'leaves': [{'leaf_id': 'existing-leaf'}],
              'stem_root_compartments': [{'compartment_id': 'existing-internode'}],
              'unchanged': [-0.0, 0.0, 1.0, 1, True, None, '원문 🌱'], 'shared': 'preserved-value-' * 100}
    after = deepcopy(parent)
    after['stem_root_compartments'].append({'compartment_id': 'new-internode'})
    if with_leaf:
        after['leaves'].append({'leaf_id': 'new-leaf'})
    receipt = {'source_code_sha256': deepcopy(pins),
               'before_candidate': {'source_code_sha256': deepcopy(pins),
                                    'source_prefix': {'source_code_sha256': deepcopy(pins)}},
               'after_program': after, 'after_rates': [-0.0, 1.0], 'after_derived': {'value': 1.0},
               'after_stage': {'rates': [-0.0, 1.0], 'derived': {'value': 1.0}},
               'other_evidence': deepcopy(parent['unchanged'])}
    return parent, receipt, pins


@pytest.mark.parametrize('with_leaf', [False, True])
def test_receipt_roundtrip_preserves_exact_canonical_bytes_and_caller_inputs(with_leaf):
    from app import crop_supply_morphology_repeat_encoding as codec
    parent, receipt, pins = example(with_leaf)
    before = canonical([parent, receipt, pins])
    packed = codec.pack(parent, receipt, pins)
    assert canonical(codec.unpack(parent, packed, pins)) == canonical(receipt)
    assert canonical([parent, receipt, pins]) == before
    assert len(canonical(packed)) < len(canonical(receipt))


@pytest.mark.parametrize('mutation', ['extra', 'pins', 'program', 'rates', 'after_stage', 'hidden_pins'])
def test_self_rehashed_storage_cannot_change_the_bound_receipt(mutation):
    from app import crop_supply_morphology_repeat_encoding as codec
    parent, receipt, pins = example()
    packed = codec.pack(parent, receipt, pins)
    if mutation == 'extra':
        packed['unexpected'] = True
    elif mutation == 'pins':
        packed['source_code_set_sha256'] = '0' * 64
    elif mutation == 'program':
        packed['body'][1]['after_program'][1]['stem_root_compartments'][1][1][1]['compartment_id'] = 'foreign'
    elif mutation == 'rates':
        packed['body'][1]['after_rates'][1][0] = 0.0
    elif mutation == 'after_stage':
        packed['body'][1]['after_stage'] = [0, {}]
    else:
        packed['body'][1]['before_candidate'][1]['source_prefix'][1]['source_code_sha256'] = [2, 1, ['missing']]
    changed = json.loads(canonical(packed))
    with pytest.raises(ValueError):
        codec.unpack(parent, changed, pins)


def test_bound_receipt_cannot_use_a_foreign_parent():
    from app import crop_supply_morphology_repeat_encoding as codec
    parent, receipt, pins = example()
    packed = codec.pack(parent, receipt, pins)
    changed = deepcopy(parent)
    changed['shared'] = 'foreign-parent'
    with pytest.raises(ValueError):
        codec.unpack(changed, packed, pins)


def test_repeated_large_references_stop_before_exceeding_expanded_limit():
    from app import crop_supply_morphology_repeat_encoding as codec
    parent, receipt, pins = example()
    packed = codec.pack(parent, receipt, pins)
    parent['shared'] = 'x' * (codec.MAX_BYTES // 8)
    packed['body'] = [1, [[2, 0, ['shared']] for _ in range(9)]]
    with pytest.raises(ValueError, match='expanded receipt'):
        codec.unpack(parent, packed, pins)


def test_equal_json_with_different_object_insertion_order_packs_identically():
    from app import crop_supply_morphology_repeat_encoding as codec
    shared = {'large': 'same-parent-content-' * 20}
    parent = {'zzz': deepcopy(shared), 'aaa': deepcopy(shared)}
    receipt = {'used': deepcopy(shared)}
    pins = {'source': 'a' * 64}
    reordered = {key: parent[key] for key in reversed(list(parent))}
    assert canonical(parent) == canonical(reordered)
    assert canonical(codec.pack(parent, receipt, pins)) == canonical(codec.pack(reordered, receipt, pins))
