from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

from app import crop_leaf_carbon_removal as model
from app import crop_leaf_lifecycle as lifecycle
from app import crop_leaf_population as population
from test_crop_climate_joint_management import profiles, STAGES
from test_crop_leaf_lifecycle import event
from test_crop_stored_shoot_leaf_birth_inputs import LEAF_PROGRAM, canonical, exact


def case(profiles, *, removed=(0,), at=Fraction(0), masses=(500, 10000, 14500), floor=0.5):
    initial = deepcopy(LEAF_PROGRAM['initialization']); initial['at_elapsed_seconds_exact'] = exact(at)
    for declaration, mass in zip(initial['leaves'], masses, strict=True):
        leaf = declaration['initialization']; leaf['clock_state']['at_elapsed_seconds_exact'] = exact(at)
        area = profiles['growth_profile'].values['sla'] * mass
        leaf['curve']['values']['maximum_area']['value'] = 2 * area
        leaf['curve']['values']['inflection_age']['value'] = 0
        leaf['initial_area']['value'] = area
    state = population.initialize_leaf_population(inputs={'input_id': 'paired-leaf-init', 'initial_inventory': initial})['state']
    ids = [d['initialization']['clock_state']['leaf_id'] for d in initial['leaves']]
    removals = [event(ids[i], at, 'explicit-remove-' + str(i)) for i in removed]
    state = lifecycle.initialize_leaf_lifecycle(inputs={'input_id': 'paired-lifecycle-init', 'population_state': state,
                                                       'births': [], 'removals': removals})['state']
    joint = {'time_origin_utc': initial['time_origin_utc'], 'at_elapsed_seconds_exact': exact(at),
             'scenario': deepcopy(STAGES[0]['scenario'])}
    old_carbon = joint['scenario']['plant_state']['leaf']['value']
    joint['scenario']['plant_state']['leaf']['value'] = float(sum(map(Fraction, masses)) / Fraction(floor))
    joint['scenario']['climate_state']['canopy_sensible_energy']['value'] *= joint['scenario']['plant_state']['leaf']['value'] / old_carbon
    return {'schema_version': 'leaf-carbon-removal-input-v1', 'input_id': 'paired-event', 'origin': 'synthetic',
            'case_id': 'declared-paired-case', 'shoot_id': 'declared-paired-shoot', 'lifecycle_state': state,
            'joint_state': joint, 'event_ids': [r['event_id'] for r in removals],
            'mass_basis': {'schema_version': 'explicit-leaf-carbon-basis-v1', 'case_id': 'declared-paired-case',
                'shoot_id': 'declared-paired-shoot', 'origin': 'synthetic', 'evidence_level': 'assumed',
                'evidence_id': 'own-masses-declared-before-area-fixture',
                'lifecycle_state_sha256': sha256(canonical(state)).hexdigest(),
                'joint_state_sha256': sha256(canonical(joint)).hexdigest(),
                'floor_area': {'value': floor, 'unit': 'm2_floor'},
                'leaf_carbohydrate': [{'leaf_id': identifier, 'carbohydrate': {'value': mass, 'unit': 'mg_CH2O'}}
                                      for identifier, mass in zip(ids, masses, strict=True)]}}


def run(profiles, value):
    return model.apply_leaf_carbon_removals(inputs=value, **profiles)


def repin(value):
    for key in ('lifecycle_state', 'joint_state'):
        value['mass_basis'][key + '_sha256'] = sha256(canonical(value[key])).hexdigest()


@pytest.mark.parametrize('removed', [(0,), (1,), (0, 1), (1, 2)])
@pytest.mark.parametrize('at', [Fraction(0), Fraction(1, 3)])
def test_independent_instantaneous_mass_capacity_energy_and_exact_time(profiles, removed, at):
    value = case(profiles, removed=removed, at=at); before = deepcopy(value); result = run(profiles, value)
    assert value == before and run(profiles, value) == result
    transition = result['transition']; old = before['joint_state']['scenario']; new = transition['after']['scenario']
    with localcontext() as context:
        context.prec = 90
        dec = Decimal.from_float; floor = dec(float(before['mass_basis']['floor_area']['value']))
        mass = sum(Decimal(before['mass_basis']['leaf_carbohydrate'][i]['carbohydrate']['value']) for i in removed) / floor
        leaf0 = dec(float(old['plant_state']['leaf']['value'])); leaf1 = leaf0 - mass
        sla = dec(profiles['growth_profile'].values['sla']); cap = dec(float(old['parameters']['leaf_heat_capacity']['value']))
        energy0 = dec(float(old['climate_state']['canopy_sensible_energy']['value']))
        expected = {'leaf': leaf1, 'capacity': leaf1*sla*cap, 'removed_capacity': mass*sla*cap,
                    'energy': energy0*leaf1/leaf0, 'removed_energy': energy0*mass/leaf0}
    assert result['removed_carbohydrate']['value'] == float(mass)
    assert new['plant_state']['leaf']['value'] == float(expected['leaf'])
    assert transition['after']['derived']['canopy_capacity']['value'] == pytest.approx(float(expected['capacity']), rel=5e-14)
    assert transition['removed']['canopy_capacity']['value'] == pytest.approx(float(expected['removed_capacity']), rel=5e-14)
    assert new['climate_state']['canopy_sensible_energy']['value'] == pytest.approx(float(expected['energy']), rel=5e-14)
    assert transition['removed']['canopy_sensible_energy']['value'] == pytest.approx(float(expected['removed_energy']), rel=5e-14)
    for key in ('buffer', 'stem_root', 'temperature_filtered_24h', 'temperature_sum'):
        assert new['plant_state'][key] == old['plant_state'][key]
    assert new['cohort_state'] == old['cohort_state']
    for key in ('air_temperature', 'air_vapor_mass'): assert new['climate_state'][key] == old['climate_state'][key]
    assert result['at_elapsed_seconds_exact'] == exact(at)
    assert result['lifecycle_state'] == before['lifecycle_state']
    assert result['G0_G4'] == 'not_assessed' and result['claim_scope'] == 'synthetic_leaf_carbon_removal_math_only'
    for key, q in transition['balance_residuals'].items(): assert abs(q['value']) <= transition['balance_budgets'][key]['value']
    for phase, q in result['area_residuals'].items(): assert abs(q['value']) <= result['area_budgets'][phase]['value']


@pytest.mark.parametrize('change', [
    lambda p: p.update(extra=True), lambda p: p.update(origin='reference_observation'),
    lambda p: p['mass_basis'].update(evidence_level='measured'),
    lambda p: p['mass_basis'].update(shoot_id='another-shoot'),
    lambda p: p['mass_basis'].update(lifecycle_state_sha256='0'*64),
    lambda p: p['mass_basis'].update(joint_state_sha256='0'*64),
    lambda p: p['mass_basis']['floor_area'].update(value=0),
    lambda p: p['mass_basis']['floor_area'].update(value=True),
    lambda p: p['mass_basis']['floor_area'].update(unit='m2_leaf'),
    lambda p: p['mass_basis']['leaf_carbohydrate'][0]['carbohydrate'].update(unit='mg_DM'),
    lambda p: p['mass_basis']['leaf_carbohydrate'][0]['carbohydrate'].update(value=float('nan')),
    lambda p: p['mass_basis']['leaf_carbohydrate'][0]['carbohydrate'].update(value=-1),
    lambda p: p['mass_basis']['leaf_carbohydrate'][0]['carbohydrate'].update(value=0),
    lambda p: p['mass_basis']['leaf_carbohydrate'].pop(),
    lambda p: p['mass_basis']['leaf_carbohydrate'].reverse(),
    lambda p: p['event_ids'].append(p['event_ids'][0]),
    lambda p: p['event_ids'].clear(), lambda p: p.update(event_ids=['unrelated-event']),
    lambda p: p['joint_state'].update(at_elapsed_seconds_exact=exact(Fraction(1, 3))),
    lambda p: p['joint_state'].update(time_origin_utc='2026-10-02T00:00:00Z')])
def test_closed_scope_provenance_units_inventory_and_exact_time_hold(profiles, change):
    value = case(profiles); change(value)
    with pytest.raises(model.LeafCarbonRemovalHold): run(profiles, value)


def test_continuous_and_instantaneous_removal_are_not_silently_combined(profiles):
    value = case(profiles); value['joint_state']['scenario']['removals']['leaf']['value'] = 1; repin(value)
    with pytest.raises(model.LeafCarbonRemovalHold, match='DUPLICATE_REMOVAL_HOLD'): run(profiles, value)


def test_unrelated_geometric_and_carbon_states_are_held_without_rescaling(profiles):
    value = case(profiles)
    value['mass_basis']['floor_area']['value'] = 1
    value['joint_state']['scenario']['plant_state']['leaf']['value'] /= 2
    value['joint_state']['scenario']['climate_state']['canopy_sensible_energy']['value'] /= 2; repin(value)
    # Same mass/floor and area/floor remain consistent; changing just a mass does not.
    assert run(profiles, value)['transition']['after']['scenario']['plant_state']['leaf']['value'] > 0
    value['mass_basis']['leaf_carbohydrate'][0]['carbohydrate']['value'] *= 2
    with pytest.raises(model.LeafCarbonRemovalHold, match='MASS_BALANCE_HOLD'): run(profiles, value)


def test_same_event_on_after_state_cannot_reuse_original_mass_basis(profiles):
    value = case(profiles); result = run(profiles, value)
    value['joint_state']['scenario'] = result['transition']['after']['scenario']
    with pytest.raises(model.LeafCarbonRemovalHold, match='HASH_HOLD'): run(profiles, value)


def test_same_total_carbon_with_wrong_leaf_distribution_is_held_after_candidate(profiles):
    value = case(profiles); rows = value['mass_basis']['leaf_carbohydrate']
    rows[0]['carbohydrate']['value'] += 500; rows[1]['carbohydrate']['value'] -= 500
    before = deepcopy(value)
    with pytest.raises(model.LeafCarbonRemovalHold, match='CANOPY_HOLD'): run(profiles, value)
    assert value == before


def test_original_stored_leaf_geometry_does_not_approve_unrelated_aggregate_mass(profiles):
    value = case(profiles)
    root = Path(__file__).resolve().parents[2]
    value['lifecycle_state'] = json.loads((root/'web/public/leaf-lifecycle-replay/with-removal/initial-state.json').read_bytes())
    value['event_ids'] = ['owned-initial-removal']; repin(value)
    with pytest.raises(model.LeafCarbonRemovalHold, match='CANOPY_HOLD'): run(profiles, value)


def test_past_removed_leaf_is_not_deducted_again_at_current_event(profiles):
    value = case(profiles, removed=(0, 1)); old = value['lifecycle_state']; source = old['existing_inventory_state']['source_population']
    declarations = deepcopy(old['removal_declarations']); declarations[1]['at_elapsed_seconds_exact'] = exact(1)
    state = lifecycle.initialize_leaf_lifecycle(inputs={'input_id': 'past-removal-init', 'population_state': source,
        'births': [], 'removals': declarations})['state']
    state = lifecycle.advance_leaf_lifecycle(inputs={'input_id': 'reach-current-event', 'state': state,
        'segments': [{'start_elapsed_seconds_exact': exact(0), 'end_elapsed_seconds_exact': exact(1),
                      'air_temperature': {'value': 5, 'unit': 'degC'}}]})['state']
    value['lifecycle_state'] = state; value['joint_state']['at_elapsed_seconds_exact'] = exact(1)
    value['joint_state']['scenario']['plant_state']['leaf']['value'] = 49000
    value['event_ids'] = [declarations[1]['event_id']]; value['mass_basis']['leaf_carbohydrate'].pop(0); repin(value)
    result = run(profiles, value)
    assert result['removed_carbohydrate']['value'] == 20000
    assert result['transition']['after']['scenario']['plant_state']['leaf']['value'] == 29000


def test_full_leaf_removal_keeps_existing_empty_canopy_hold(profiles):
    value = case(profiles, removed=(0, 1, 2)); before = deepcopy(value)
    with pytest.raises(model.LeafCarbonRemovalHold): run(profiles, value)
    assert value == before


def test_positive_explicit_mass_cannot_vanish_during_floor_conversion(profiles):
    value = case(profiles)
    value['mass_basis']['floor_area']['value'] = sys.float_info.max
    for row in value['mass_basis']['leaf_carbohydrate']: row['carbohydrate']['value'] = sys.float_info.min
    value['joint_state']['scenario']['plant_state']['leaf']['value'] = 0; repin(value)
    with pytest.raises(model.LeafCarbonRemovalHold, match='NUMERIC_HOLD'): run(profiles, value)


@pytest.mark.parametrize('index', range(8))
def test_existing_stage_domains_and_signed_or_zero_energy_remain_supported(profiles, index):
    value = case(profiles); value['joint_state']['scenario'] = deepcopy(STAGES[index]['scenario']); repin(value)
    result = run(profiles, value); transition = result['transition']
    before = value['joint_state']['scenario']['climate_state']['canopy_sensible_energy']['value']
    after = transition['after']['scenario']['climate_state']['canopy_sensible_energy']['value']
    assert after == pytest.approx(before * 0.98, rel=5e-14, abs=0)
    assert transition['after']['derived']['canopy_temperature']['value'] == pytest.approx(
        transition['before']['derived']['canopy_temperature']['value'], rel=0, abs=2e-13)


def test_one_shared_management_two_rhs_no_lifecycle_advance_or_integration(profiles, monkeypatch):
    value = case(profiles); counts = {'management': 0, 'rhs': 0}
    original = model.management.apply_management; rhs = model.management.joint.evaluate_rhs
    def managed(**kwargs): counts['management'] += 1; return original(**kwargs)
    def stage(**kwargs): counts['rhs'] += 1; return rhs(**kwargs)
    def forbidden(**kwargs): raise AssertionError('no lifecycle advance')
    monkeypatch.setattr(model.management, 'apply_management', managed)
    monkeypatch.setattr(model.management.joint, 'evaluate_rhs', stage)
    monkeypatch.setattr(lifecycle, 'advance_leaf_lifecycle', forbidden)
    assert run(profiles, value)['removed_carbohydrate']['value'] > 0
    assert counts == {'management': 1, 'rhs': 2}
