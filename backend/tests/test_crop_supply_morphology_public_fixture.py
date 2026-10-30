"""A newly declared own fixture; existing false grants are never rewritten."""
from copy import deepcopy

import pytest

from test_crop_leaf_carbon_stock_artifact import inputs as private_inputs
from test_crop_supply_morphology_repeat import (
    profiles, prepared, pending, calculated, adopted, trajectory,
    post_pending, post_calculated, successor, repeat_root,
)


def test_public_source_is_new_and_does_not_change_private_template():
    from supply_morphology_public_fixture import public_inputs
    original = private_inputs(1, dt=.125, count=1)
    before = deepcopy(original)
    public = public_inputs(1, dt=.125, count=1)
    assert original == before and original['rights']['redistribute'] is False
    assert public['rights']['redistribute'] is True
    assert public['rights']['declaration_id'] != original['rights']['declaration_id']
    assert public['rights']['revision'] != original['rights']['revision']
    assert public['program'] == original['program']
    assert public['rights']['ownership_asserted'] is True
    public['program']['input_id'] = 'caller-mutation'
    assert private_inputs(1, dt=.125, count=1) == before


@pytest.fixture(scope='module')
def current(tmp_path_factory, profiles):
    from supply_morphology_public_fixture import make_public_current
    return make_public_current(tmp_path_factory.mktemp('new-own-public-supply'), profiles)


def test_actual_public_bridge_retains_genuine_state_and_all_three_grants(repeat_root):
    from app import crop_supply_morphology_repeat_resume as model
    from app import crop_supply_morphology_repeat_context as owner
    context, origin, _, _ = repeat_root
    data = model._context(context)
    mixed = context._origin._origin._origin._source._source
    binding = model.source.stock._source(mixed)
    assert set(binding['source_rights']) == {'crop', 'stem', 'declaration'}
    assert all(grant['redistribute'] is True for grant in binding['source_rights'].values())
    assert data['seed']['redistribution_authorized'] is True
    checkpoint = model.start(context)
    assert checkpoint.value['last_confirmed'] == origin.value['seed']['initial_sample']
    assert owner.context_bytes(context) == context._raw
    assert checkpoint.value['redistribution_authorized'] is True
