"""Fixed independent source values, signed transfers and explicit numerical holds."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
from math import nextafter
from pathlib import Path

import pytest

from app import crop_canopy_exchange as model

ROOT = Path(__file__).resolve().parents[2]
RAW = (ROOT/'fixtures/crop-canopy-exchange-reference-parameters-v1.json').read_bytes()
CASES = json.loads((ROOT/'fixtures/crop-canopy-exchange-reference-cases-v1.json').read_bytes())['cases']


@pytest.fixture(scope='module')
def profile():
    return model.ReferenceParameters(RAW)


@pytest.fixture
def forcing():
    return deepcopy(CASES[0]['forcing'])


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
def test_fixed_independent_decimal_reference_and_energy_ownership(profile, case):
    original = deepcopy(case['forcing'])
    value = model.calculate_exchange(forcing=case['forcing'], profile=profile)
    diagnostics = value['diagnostics']
    found = {'saturation_pressure':diagnostics['canopy_saturation_pressure']['value'],
        'vapor_difference':diagnostics['canopy_minus_air_vapor_pressure']['value'],
        'coefficient':diagnostics['vapor_transfer_coefficient']['value'],
        **{k:q['value'] for k,q in value['exchange'].items()}}
    for name, expected in case['expected_decimal'].items():
        assert found[name] == pytest.approx(float(expected), rel=2e-14, abs=0)
    assert case['forcing'] == original
    e,h,le = (value['exchange'][name]['value'] for name in ('water_vapor','sensible_heat','latent_heat'))
    assert value['local_transfers'] == {
        'water':{'canopy':{'value':-e,'unit':model.WATER_UNIT},'air_vapor':{'value':e,'unit':model.WATER_UNIT}},
        'sensible':{'canopy':{'value':-h,'unit':model.HEAT_UNIT},'air_sensible':{'value':h,'unit':model.HEAT_UNIT}},
        'latent':{'canopy':{'value':-le,'unit':model.HEAT_UNIT},'air_vapor_energy':{'value':le,'unit':model.HEAT_UNIT}}}
    assert all(q['value'] == 0 for q in value['local_transfer_residuals'].values())
    assert value['scope'] == 'software_research_only' and value['claim_scope'] == 'synthetic_exchange_math_only'
    assert value['G0_G4'] == 'not_assessed' and value['profile_sha256'] == sha256(RAW).hexdigest()


def test_reverse_exchange_is_signed_and_not_renamed_as_harvest_or_water_use(profile):
    value = model.calculate_exchange(forcing=CASES[1]['forcing'], profile=profile)
    assert all(value['exchange'][k]['value'] < 0 for k in ('water_vapor','sensible_heat','latent_heat'))
    assert set(value['exchange']) == {'water_vapor','sensible_heat','latent_heat','canopy_total_heat_outflow'}


def test_area_density_resistance_and_sensible_direction(profile, forcing):
    original = model.calculate_exchange(forcing=forcing, profile=profile)['exchange']
    forcing['values']['leaf_area_index']['value'] *= 2
    doubled = model.calculate_exchange(forcing=forcing, profile=profile)['exchange']
    assert all(doubled[k]['value'] == pytest.approx(2*q['value'],rel=2e-14) for k,q in original.items())
    forcing['values']['air_capacity_density']['value'] *= 2
    dense = model.calculate_exchange(forcing=forcing, profile=profile)['exchange']
    assert dense['water_vapor']['value'] == pytest.approx(2*doubled['water_vapor']['value'],rel=2e-14)
    assert dense['sensible_heat'] == doubled['sensible_heat']
    forcing['values']['canopy_vapor_resistance']['value'] *= 100
    resistant = model.calculate_exchange(forcing=forcing, profile=profile)['exchange']
    assert 0 < resistant['water_vapor']['value'] < dense['water_vapor']['value']
    assert resistant['sensible_heat'] == dense['sensible_heat']
    forcing['values']['air_temperature']['value'] = 22
    reverse_heat = model.calculate_exchange(forcing=forcing, profile=profile)['exchange']
    assert reverse_heat['sensible_heat']['value'] == -resistant['sensible_heat']['value']
    assert reverse_heat['water_vapor'] == resistant['water_vapor']


def test_empty_canopy_has_zero_flux_without_a_small_leaf_replacement(profile, forcing):
    forcing['values']['leaf_area_index']['value'] = 0
    forcing['values']['canopy_vapor_resistance']['value'] = 1e308
    value = model.calculate_exchange(forcing=forcing, profile=profile)
    assert all(q['value'] == 0 for q in value['exchange'].values())
    assert value['forcing']['values']['leaf_area_index']['value'] == 0


def test_canonical_input_replay_and_parameter_immutability(profile, forcing):
    original = model.calculate_exchange(forcing=forcing, profile=profile)
    rearranged = {key:forcing[key] for key in reversed(forcing)}
    rearranged['values'] = dict(reversed(list(forcing['values'].items())))
    assert model.calculate_exchange(forcing=rearranged, profile=profile) == original
    forcing['input_id'] += '-new'
    assert model.calculate_exchange(forcing=forcing, profile=profile)['input_sha256'] != original['input_sha256']
    with pytest.raises(TypeError):profile.values['latent_heat'] = 1
    with pytest.raises(FrozenInstanceError):profile.sha256 = '0'*64


@pytest.mark.parametrize('name', model.INPUT_UNITS)
def test_units_nonfinite_negative_and_nonnumeric_are_rejected(profile, forcing, name):
    row = forcing['values'][name]
    row['unit'] = 'wrong'
    with pytest.raises(model.CanopyExchangeHold,match='UNIT_HOLD'):model.calculate_exchange(forcing=forcing,profile=profile)
    row['unit'] = model.INPUT_UNITS[name]
    for bad in (True, '1', None, -1, float('nan'), float('inf'), -float('inf'), 10**400):
        row['value'] = bad
        with pytest.raises(model.CanopyExchangeHold):model.calculate_exchange(forcing=forcing,profile=profile)


@pytest.mark.parametrize('name', ('canopy_temperature','air_temperature'))
def test_project_temperature_endpoints_and_adjacent_outside_values(profile, forcing, name):
    for allowed in (10,34):
        forcing['values'][name]['value'] = allowed
        model.calculate_exchange(forcing=forcing,profile=profile)
    for outside in (nextafter(10,-float('inf')),nextafter(34,float('inf'))):
        forcing['values'][name]['value'] = outside
        with pytest.raises(model.CanopyExchangeHold,match='temperature'):model.calculate_exchange(forcing=forcing,profile=profile)


@pytest.mark.parametrize('mutation', ('extra','missing','extra_quantity','quantity_key','origin','empty_id'))
def test_closed_research_input(profile, forcing, mutation):
    if mutation == 'extra':forcing['other'] = 1
    elif mutation == 'missing':del forcing['values']['air_temperature']
    elif mutation == 'extra_quantity':forcing['values']['other'] = {'value':1,'unit':'1'}
    elif mutation == 'quantity_key':forcing['values']['air_temperature']['origin'] = 'invented'
    elif mutation == 'origin':forcing['origin'] = 'measured_approved'
    else:forcing['input_id'] = ' '
    with pytest.raises(model.CanopyExchangeHold,match='INPUT_HOLD'):model.calculate_exchange(forcing=forcing,profile=profile)


@pytest.mark.parametrize('name', ('air_capacity_density','canopy_vapor_resistance'))
def test_no_silent_density_or_resistance_default(profile, forcing, name):
    forcing['values'][name]['value'] = 0
    with pytest.raises(model.CanopyExchangeHold,match='positive'):model.calculate_exchange(forcing=forcing,profile=profile)


@pytest.mark.parametrize('raw', (None, 'not bytes', b'', RAW+b' ', RAW.replace(b'2450000.0',b'2450001.0')))
def test_unreviewed_profile_bytes_rejected(raw):
    with pytest.raises(model.CanopyExchangeHold,match='PROFILE_HOLD'):model.ReferenceParameters(raw)


@pytest.mark.parametrize('changes', ({'leaf_area_index':5e-324}, {'air_capacity_density':5e-324},
    {'air_capacity_density':1e308}, {'canopy_vapor_resistance':1e308},
    {'leaf_area_index':1e308,'air_capacity_density':1e-304,'air_vapor_pressure':1e308}))
def test_intermediate_overflow_and_underflow_hold_without_clipping(profile, forcing, changes):
    for name,value in changes.items():forcing['values'][name]['value'] = value
    with pytest.raises(model.CanopyExchangeHold,match='NUMERIC_HOLD'):model.calculate_exchange(forcing=forcing,profile=profile)
