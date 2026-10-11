"""Independent scalar references and the actual instantaneous joint interface."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

from app import crop_greenhouse_ventilation as model
from app import crop_climate_joint_rhs as joint
from app.crop_canopy_exchange import ReferenceParameters as Exchange
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT/'fixtures/crop-greenhouse-ventilation-reference-cases-v1.json'
DOCUMENT = json.loads(FIXTURE.read_bytes())
CASES = DOCUMENT['cases']


@pytest.fixture(scope='module')
def profile():
    return Exchange((ROOT/'fixtures/crop-canopy-exchange-reference-parameters-v1.json').read_bytes())


def run(s, profile):
    return model.calculate_ventilation(scenario=s, profile=profile)


def scalars(r):
    return {**{k: q['value'] for k, q in r['derived'].items()},
        **{k: q['value'] for k, q in r['forcing_contribution'].items()},
        'latent_energy': r['local_transfers']['latent_energy']['air']['value'],
        'reduced_energy_to_air': r['reduced_energy_to_air']['value']}


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['case_id'])
def test_independent_decimal_values_replay_identity_and_no_input_mutation(case, profile):
    before = deepcopy(case['scenario'])
    r = run(case['scenario'], profile)
    assert run(case['scenario'], profile) == r
    assert case['scenario'] == before
    actual = scalars(r)
    assert set(actual) == set(case['expected_decimal'])
    for key, text in case['expected_decimal'].items():
        expected = float(text)
        assert actual[key] == pytest.approx(expected, rel=2e-14, abs=0), key
        if expected == 0:
            assert actual[key] == 0
    assert r['model_version'] == model.VERSION
    assert r['code_sha256'] == sha256((ROOT/'backend/app/crop_greenhouse_ventilation.py').read_bytes()).hexdigest()
    for key in ('profile_sha256', 'source_sha256', 'notice_sha256'):
        assert r[key] == DOCUMENT[key]
    for key in ('input_sha256', 'policy_sha256'):
        assert len(r[key]) == 64
    assert r['G0_G4'] == 'not_assessed'
    assert r['time_coordinate'] == 'instantaneous_no_state_advance'
    assert r['claim_scope'] == 'synthetic_prescribed_ventilation_math_only'


def test_independent_generator_reproduces_fixture_without_app_imports():
    path = ROOT/'research/crop-greenhouse-ventilation-reference.py'
    spec = importlib.util.spec_from_file_location('ventilation_reference', path)
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    assert reference.document() == DOCUMENT
    raw = (json.dumps(reference.document(), indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    assert raw == FIXTURE.read_bytes()
    assert DOCUMENT['generator_sha256'] == sha256(path.read_bytes()).hexdigest()
    assert DOCUMENT['decimal_precision'] == 80
    assert DOCUMENT['comparison'] == {'relative': 2e-14, 'absolute': 0, 'expected_zero': 'exact'}


def test_signed_transfers_zero_flow_and_no_latent_sensible_credit(profile):
    cold, warm = (run(c['scenario'], profile) for c in CASES[:2])
    for key in ('air_external_sensible_heat', 'air_external_vapor'):
        assert cold['forcing_contribution'][key]['value'] < 0
        assert warm['forcing_contribution'][key]['value'] > 0
    for c in CASES:
        r = run(c['scenario'], profile)
        for key, pair in r['local_transfers'].items():
            assert pair['air']['value'] == -pair['outdoor']['value']
            assert pair['air']['unit'] == pair['outdoor']['unit']
            assert r['local_transfer_residuals'][key]['value'] == 0
    zero = run(CASES[2]['scenario'], profile)
    assert all(q['value'] == 0 for q in zero['forcing_contribution'].values())
    same_t = run(CASES[4]['scenario'], profile)
    assert same_t['forcing_contribution']['air_external_sensible_heat']['value'] == 0
    assert same_t['local_transfers']['latent_energy']['air']['value'] != 0
    assert same_t['reduced_energy_to_air'] == same_t['local_transfers']['latent_energy']['air']


def test_flow_scaling_and_mass_volume_concentration(profile):
    s = deepcopy(CASES[0]['scenario'])
    first = run(s, profile)
    s['forcing']['volume_exchange_per_floor_area']['value'] *= 2
    second = run(s, profile)
    for key in first['forcing_contribution']:
        assert second['forcing_contribution'][key]['value'] == pytest.approx(
            2*first['forcing_contribution'][key]['value'], rel=2e-14, abs=0)
    s['parameters']['air_volume_per_floor_area']['value'] *= 2
    s['state']['air_vapor_mass']['value'] *= 2
    equivalent = run(s, profile)
    assert equivalent['forcing_contribution'] == second['forcing_contribution']
    assert equivalent['input_sha256'] != second['input_sha256']


def test_original_pressure_temperature_source_form_only_at_declared_source_constant(profile):
    s = deepcopy(CASES[-1]['scenario'])
    for constant, equivalent in ((8314/18, True), (461.5, False)):
        s['parameters']['vapor_gas_constant']['value'] = constant
        state, p, f = (s[name] for name in ('state', 'parameters', 'forcing'))
        pin = state['air_vapor_mass']['value']/p['air_volume_per_floor_area']['value']*constant*(
            state['air_temperature']['value']+273.15)
        outward_source = (18/8314)*f['volume_exchange_per_floor_area']['value']*(
            pin/(state['air_temperature']['value']+273.15)-f['outdoor_vapor_pressure']['value']/(
                f['outdoor_air_temperature']['value']+273.15))
        actual = run(s, profile)['forcing_contribution']['air_external_vapor']['value']
        if equivalent:
            assert actual == pytest.approx(-outward_source, rel=2e-14, abs=0)
        else:
            assert abs(actual+outward_source) > abs(actual)*1e-5


BAD_VALUES = [('state', 'air_temperature', -273.15), ('forcing', 'outdoor_air_temperature', -274),
    ('state', 'air_temperature', 1e308), ('state', 'air_vapor_mass', -1),
    ('forcing', 'outdoor_vapor_pressure', -1), ('forcing', 'volume_exchange_per_floor_area', -1),
    *[(block, key, value) for block, key in [('parameters', 'air_volume_per_floor_area'),
        ('parameters', 'air_capacity_density'), ('parameters', 'vapor_gas_constant')]
        for value in (0, -1)],
    *[('forcing', 'volume_exchange_per_floor_area', value) for value in (True, '0.1', None,
        float('nan'), float('inf'), float('-inf'), 10**400)]]


@pytest.mark.parametrize('block,key,value', BAD_VALUES)
def test_invalid_explicit_quantities_hold(profile, block, key, value):
    s = deepcopy(CASES[0]['scenario'])
    s[block][key]['value'] = value
    with pytest.raises(model.VentilationHold):
        run(s, profile)


@pytest.mark.parametrize('fault', ['top_extra', 'top_missing', 'extra_quantity', 'missing_quantity',
    'quantity_extra', 'quantity_missing', 'quantity_type', 'block_type', 'unit', 'origin', 'id', 'profile'])
def test_closed_schema_units_and_pinned_profile_hold(profile, fault):
    s = deepcopy(CASES[0]['scenario'])
    if fault == 'top_extra': s['unexpected'] = 0
    if fault == 'top_missing': del s['state']
    if fault == 'extra_quantity': s['forcing']['ACH'] = {'value': 2, 'unit': '1/h'}
    if fault == 'missing_quantity': del s['forcing']['outdoor_vapor_pressure']
    if fault == 'quantity_extra': s['state']['air_temperature']['default'] = 24
    if fault == 'quantity_missing': del s['state']['air_temperature']['unit']
    if fault == 'quantity_type': s['state']['air_temperature'] = 24
    if fault == 'block_type': s['state'] = []
    if fault == 'unit': s['forcing']['volume_exchange_per_floor_area']['unit'] = '1/h'
    if fault == 'origin': s['origin'] = 'farm_observation'
    if fault == 'id': s['input_id'] = ' '
    if fault == 'profile': profile = object()
    with pytest.raises(model.VentilationHold):
        run(s, profile)


@pytest.mark.parametrize('changes', [
    [('state', 'air_vapor_mass', 1e-300), ('parameters', 'air_volume_per_floor_area', 1e300)],
    [('state', 'air_vapor_mass', 1e300), ('parameters', 'air_volume_per_floor_area', 1e-300)],
    [('parameters', 'vapor_gas_constant', 1e308)],
    [('forcing', 'outdoor_vapor_pressure', 1e-300), ('parameters', 'vapor_gas_constant', 1e300)],
    [('parameters', 'air_capacity_density', 1e-300), ('forcing', 'volume_exchange_per_floor_area', 1e-300)],
    [('state', 'air_vapor_mass', 0), ('forcing', 'outdoor_vapor_pressure', 1e-200),
        ('forcing', 'volume_exchange_per_floor_area', 1e-300)],
    [('parameters', 'air_capacity_density', 1e308)],
    [('parameters', 'air_capacity_density', 25000), ('forcing', 'volume_exchange_per_floor_area', 1e300),
        ('forcing', 'outdoor_air_temperature', 28), ('forcing', 'outdoor_vapor_pressure', 5_600_000)]])
def test_nonrepresentable_operations_hold(profile, changes):
    s = deepcopy(CASES[0]['scenario'])
    for block, key, value in changes:
        s[block][key]['value'] = value
    with pytest.raises(model.VentilationHold, match='NUMERIC_HOLD'):
        run(s, profile)


def test_same_trial_forcings_compose_with_actual_joint_rhs_without_latent_double_credit(profile):
    profiles = {key: kind((ROOT/'fixtures'/filename).read_bytes()) for key, kind, filename in (
        ('growth_profile', Growth, 'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile', Cohort, 'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile', Transport, 'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile', Exchange, 'crop-canopy-exchange-reference-parameters-v1.json'))}
    s = deepcopy(json.loads((ROOT/'fixtures/crop-climate-joint-rhs-reference-cases-v1.json').read_bytes())['cases'][0]['scenario'])
    first = joint.evaluate_rhs(scenario=s, **profiles)
    boundary = deepcopy(CASES[0]['scenario'])
    boundary['state'] = deepcopy({key: s['climate_state'][key] for key in model.STATE_UNITS})
    boundary['parameters'] = deepcopy({key: s['parameters'][key] for key in model.PARAMETER_UNITS})
    v = run(boundary, profile)
    for key, q in v['forcing_contribution'].items():
        s['forcing'][key]['value'] += q['value']
    second = joint.evaluate_rhs(scenario=s, **profiles)
    for key, q in second['balance_residuals'].items():
        assert abs(q['value']) <= second['balance_budgets'][key]['value']
    actual_t = second['derivatives']['climate']['air_temperature']['value']-first['derivatives']['climate']['air_temperature']['value']
    actual_v = second['derivatives']['climate']['air_vapor_mass']['value']-first['derivatives']['climate']['air_vapor_mass']['value']
    assert actual_t == pytest.approx(v['forcing_contribution']['air_external_sensible_heat']['value']/
        first['derived']['air_capacity']['value'], rel=2e-14, abs=2e-16)
    assert actual_v == pytest.approx(v['forcing_contribution']['air_external_vapor']['value'], rel=2e-14, abs=2e-20)
    assert second['crop'] == first['crop']
    assert second['exchange'] == first['exchange']
    assert second['derivatives']['plant'] == first['derivatives']['plant']
    assert second['derivatives']['climate']['canopy_sensible_energy'] == first['derivatives']['climate']['canopy_sensible_energy']
