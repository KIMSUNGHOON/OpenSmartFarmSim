"""Independent gross-flow and signed-energy cases; strict inventory holds."""
from copy import deepcopy
from hashlib import sha256
import json
from math import fsum, nextafter
from pathlib import Path

import pytest

from app import crop_canopy_energy_transport as model
from app.crop_growth_rates import CropRateHold, ReferenceParameters

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads((ROOT/'fixtures/crop-canopy-energy-transport-reference-cases-v1.json').read_bytes())
FLOWS, EVENTS = REFERENCE['transport_cases'], REFERENCE['event_cases']


@pytest.fixture(scope='module')
def profile():
    return ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes())


def flat_transport(result):
    keys = ('leaf_area_index','canopy_capacity','canopy_sensible_energy','leaf_net_rate',
        'material_temperature_rate','storage_rate_from_chain_rule')
    return {**{k:result[k]['value'] for k in keys},
        **{'capacity_'+k:q['value'] for k,q in result['capacity_rates'].items()},
        **{'energy_'+k:q['value'] for k,q in result['energy_flows'].items()}}


def flat_event(result):
    return {**{side+'_'+k:q['value'] for side in ('before','after') for k,q in result[side].items()},
        'outgoing_sensible_energy':result['outgoing_sensible_energy']['value']}


def compare(actual, expected):
    assert set(actual) == set(expected)
    for name,value in expected.items():
        assert actual[name] == pytest.approx(float(value),rel=3e-13,
            abs=2e-13 if 'canopy_temperature' in name or float(value)==0 else 0), name


@pytest.mark.parametrize('case',FLOWS,ids=lambda c:c['case_id'])
def test_independent_gross_capacity_energy_and_temperature(profile,case):
    original = deepcopy(case['forcing'])
    result = model.calculate_transport(forcing=case['forcing'],profile=profile)
    compare(flat_transport(result),case['expected_decimal'])
    assert case['forcing'] == original
    assert result['scope'] == 'software_research_only'
    assert result['claim_scope'] == 'synthetic_canopy_capacity_inventory_only'
    assert result['G0_G4'] == 'not_assessed'
    assert result['profile_sha256'] == REFERENCE['profile_sha256']
    assert result['code_sha256'] == sha256((ROOT/'backend/app/crop_canopy_energy_transport.py').read_bytes()).hexdigest()
    flows = [q['value'] for q in result['energy_flows'].values()]
    assert abs(result['balance_residuals']['material_energy']['value']) <= 3e-13*fsum(map(abs,flows))
    assert result['capacity_rates']['net']['unit'] == 'J/m2_floor/K/s'
    assert result['material_temperature_rate']['unit'] == 'K/s'


@pytest.mark.parametrize('case',EVENTS,ids=lambda c:c['case_id'])
def test_independent_partial_or_zero_event_preserves_temperature_and_energy(profile,case):
    original = deepcopy(case['event'])
    result = model.calculate_leaf_removal(event=case['event'],profile=profile)
    compare(flat_event(result),case['expected_decimal'])
    assert case['event'] == original
    before,after,outgoing = result['before'],result['after'],result['outgoing_sensible_energy']['value']
    ub,ua = (side['canopy_sensible_energy']['value'] for side in (before,after))
    assert abs(fsum((ub,-ua,-outgoing))) <= 3e-13*fsum(map(abs,(ub,ua,outgoing)))
    assert abs(result['balance_residuals']['event_capacity_energy']['value']) <= 3e-13*fsum(map(abs,(ub,ua,outgoing)))
    assert abs(result['balance_residuals']['temperature']['value']) <= 2e-13
    assert result['G0_G4'] == 'not_assessed'


def test_net_zero_gross_turnover_changes_temperature_and_cannot_be_net_lai_only(profile):
    result = model.calculate_transport(forcing=FLOWS[6]['forcing'],profile=profile)
    assert result['leaf_net_rate']['value'] == result['capacity_rates']['net']['value'] == 0
    assert result['capacity_rates']['allocation']['value'] > 0
    assert result['material_temperature_rate']['value'] < 0
    assert result['energy_flows']['net']['value'] < 0
    assert max(result['capacity_rates']['net']['value'],0) == 0  # Net-only adapter loses the nonzero inflow.


def test_equal_temperature_entry_and_current_temperature_losses_keep_material_temperature(profile):
    same,maintenance,removal = [model.calculate_transport(forcing=FLOWS[i]['forcing'],profile=profile) for i in (1,4,5)]
    assert all(r['material_temperature_rate']['value'] == 0 for r in (same,maintenance,removal))
    assert same['energy_flows']['incoming']['value'] > 0
    assert maintenance['energy_flows']['maintenance_outgoing']['value'] > 0
    assert removal['energy_flows']['removal_outgoing']['value'] > 0


def test_reference_shift_preserves_temperature_rates_with_signed_energy_flows(profile):
    first = model.calculate_transport(forcing=FLOWS[2]['forcing'],profile=profile)
    for case in FLOWS[7:]:
        delta = case['forcing']['values']['reference_temperature']['value']
        shifted = model.calculate_transport(forcing=case['forcing'],profile=profile)
        assert shifted['capacity_rates'] == first['capacity_rates']
        assert shifted['canopy_capacity'] == first['canopy_capacity']
        assert shifted['material_temperature_rate'] == first['material_temperature_rate']
        assert shifted['canopy_sensible_energy']['value'] == pytest.approx(
            first['canopy_sensible_energy']['value']-delta*first['canopy_capacity']['value'],rel=3e-13)
        assert shifted['energy_flows']['net']['value'] == pytest.approx(
            first['energy_flows']['net']['value']-delta*first['capacity_rates']['net']['value'],rel=3e-13)
    above = model.calculate_transport(forcing=FLOWS[8]['forcing'],profile=profile)
    assert above['canopy_sensible_energy']['value'] < 0
    assert above['energy_flows']['maintenance_outgoing']['value'] < 0
    assert above['energy_flows']['removal_outgoing']['value'] < 0


def test_event_reference_shift_and_negative_export_are_not_clamped(profile):
    results = [model.calculate_leaf_removal(event=case['event'],profile=profile) for case in EVENTS[:3]]
    first = results[0]
    for case,result in zip(EVENTS[1:3],results[1:]):
        delta = case['event']['values']['reference_temperature']['value']
        for side in ('before','after'):
            assert result[side]['canopy_temperature']['value'] == pytest.approx(first[side]['canopy_temperature']['value'],abs=2e-13)
            assert result[side]['canopy_sensible_energy']['value'] == pytest.approx(
                first[side]['canopy_sensible_energy']['value']-delta*first[side]['canopy_capacity']['value'],rel=3e-13)
    assert results[2]['outgoing_sensible_energy']['value'] < 0
    assert results[2]['after']['canopy_sensible_energy']['value'] < 0
    assert first['after']['canopy_sensible_energy'] != first['before']['canopy_sensible_energy']
    wrong_temperature = first['before']['canopy_sensible_energy']['value']/first['after']['canopy_capacity']['value']
    assert wrong_temperature != first['after']['canopy_temperature']['value']


def test_zero_removal_is_identity_and_zero_energy_partial_is_allowed(profile):
    zero = model.calculate_leaf_removal(event=EVENTS[3]['event'],profile=profile)
    assert zero['before'] == zero['after']
    assert zero['outgoing_sensible_energy']['value'] == 0
    partial = model.calculate_leaf_removal(event=EVENTS[4]['event'],profile=profile)
    assert partial['before']['canopy_sensible_energy']['value'] == partial['after']['canopy_sensible_energy']['value'] == 0
    assert partial['after']['leaf_carbohydrate']['value'] < partial['before']['leaf_carbohydrate']['value']


@pytest.mark.parametrize('startup',(False,True))
def test_existing_crop_gross_leaf_flows_map_to_capacity_without_growth_respiration_debit(profile,startup):
    from app.crop_growth_rates import calculate_rates
    from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
    from app.crop_fruit_transport import ReferenceFruitTransportParameters
    from app.crop_plant_startup_rates import calculate_plant_startup_rates
    if startup:
        source=json.loads((ROOT/'fixtures/crop-plant-startup-reference-cases-v1.json').read_bytes())['cases'][0]
        crop=calculate_plant_startup_rates(**{k:source[k] for k in ('state','cohort_state','forcing','removals','fruit_entry')},
            growth_profile=profile,
            cohort_profile=ReferenceFruitCohortParameters((ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
            transport_profile=ReferenceFruitTransportParameters((ROOT/'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes()))
        maintenance=crop['vegetative_maintenance']['leaf']
    else:
        source=json.loads((ROOT/'fixtures/crop-growth-reference-cases-v1.json').read_bytes())['cases'][0]
        crop=calculate_rates(**{k:source[k] for k in ('state','forcing','removals')},profile=profile)
        maintenance=crop['maintenance_respiration']['leaf']
    block=deepcopy(FLOWS[2]['forcing'])
    block['values'].update({'leaf_carbohydrate':deepcopy(source['state']['values']['leaf']),
        'leaf_allocation':deepcopy(crop['allocation']['leaf']),'leaf_maintenance':deepcopy(maintenance),
        'leaf_removal':deepcopy(source['removals']['values']['leaf']),
        'canopy_temperature':deepcopy(source['forcing']['values']['canopy_temperature'])})
    result=model.calculate_transport(forcing=block,profile=profile)
    assert result['leaf_area_index']==crop['lai']
    assert result['leaf_net_rate']['value']==pytest.approx(crop['derivatives']['leaf']['value'],rel=3e-13)
    assert result['capacity_rates']['net']['value']==pytest.approx(
        1200*profile.values['sla']*crop['derivatives']['leaf']['value'],rel=3e-13)
    assert result['capacity_rates']['maintenance']['value']==pytest.approx(
        1200*profile.values['sla']*maintenance['value'],rel=3e-13)
    assert crop['growth_respiration']['value']>0


@pytest.mark.parametrize('operation,units',(('transport',model.TRANSPORT_UNITS),('event',model.EVENT_UNITS)))
def test_closed_quantities_exact_units_and_numeric_values(profile,operation,units):
    source = FLOWS[0]['forcing'] if operation=='transport' else EVENTS[0]['event']
    def invoke(block):
        if operation=='transport':return model.calculate_transport(forcing=block,profile=profile)
        return model.calculate_leaf_removal(event=block,profile=profile)
    for name,unit in units.items():
        for bad in (True,None,'1',float('nan'),float('inf'),-float('inf'),10**400):
            block=deepcopy(source);block['values'][name]={'value':bad,'unit':unit}
            with pytest.raises(model.CanopyEnergyHold):invoke(block)
        block=deepcopy(source);block['values'][name]['unit']='wrong'
        with pytest.raises(model.CanopyEnergyHold,match='UNIT_HOLD'):invoke(block)
        block=deepcopy(source);block['values'][name]['extra']=1
        with pytest.raises(model.CanopyEnergyHold):invoke(block)
        block=deepcopy(source);del block['values'][name]
        with pytest.raises(model.CanopyEnergyHold):invoke(block)
    for mutation in ('extra','missing','origin','id','long-id','extra-value','values-type'):
        block=deepcopy(source)
        if mutation=='extra':block['extra']=1
        elif mutation=='missing':del block['origin']
        elif mutation=='origin':block['origin']='reference_observation'
        elif mutation=='id':block['input_id']=' '
        elif mutation=='long-id':block['input_id']='x'*201
        elif mutation=='extra-value':block['values']['extra']={'value':1,'unit':'1'}
        else:block['values']=[]
        with pytest.raises(model.CanopyEnergyHold):invoke(block)


@pytest.mark.parametrize('name',('leaf_carbohydrate','leaf_heat_capacity','leaf_allocation','leaf_maintenance','leaf_removal'))
def test_inventory_capacity_and_gross_flow_signs(profile,name):
    block=deepcopy(FLOWS[0]['forcing']);block['values'][name]['value']=-1
    with pytest.raises(model.CanopyEnergyHold):model.calculate_transport(forcing=block,profile=profile)
    block['values'][name]['value']=0
    if name in ('leaf_carbohydrate','leaf_heat_capacity'):
        with pytest.raises(model.CanopyEnergyHold):model.calculate_transport(forcing=block,profile=profile)
    else:model.calculate_transport(forcing=block,profile=profile)


@pytest.mark.parametrize('name',('canopy_temperature','incoming_capacity_temperature'))
def test_temperature_boundaries_and_no_missing_incoming_default(profile,name):
    block=deepcopy(FLOWS[0]['forcing'])
    for value in (10,34):
        block['values'][name]['value']=value;model.calculate_transport(forcing=block,profile=profile)
    for value in (nextafter(10,-float('inf')),nextafter(34,float('inf'))):
        block['values'][name]['value']=value
        with pytest.raises(model.CanopyEnergyHold,match='TEMPERATURE_HOLD'):model.calculate_transport(forcing=block,profile=profile)


@pytest.mark.parametrize('removed,reason',((-1,'EVENT_HOLD'),(75001,'EVENT_HOLD'),(75000,'EMPTY_CANOPY_HOLD'),(1e-20,'NUMERIC_HOLD')))
def test_removal_domain_full_empty_and_rounding_hold_without_mutation(profile,removed,reason):
    block=deepcopy(EVENTS[0]['event']);block['values']['leaf_removed']['value']=removed;before=deepcopy(block)
    with pytest.raises(model.CanopyEnergyHold,match=reason):model.calculate_leaf_removal(event=block,profile=profile)
    assert block==before


@pytest.mark.parametrize('field,value',(('leaf_carbohydrate',0),('canopy_sensible_energy',1e8),
    ('canopy_sensible_energy',5e-324),('leaf_heat_capacity',5e-324),('reference_temperature',1e308)))
def test_event_invalid_or_unrepresentable_thermal_inventory(profile,field,value):
    block=deepcopy(EVENTS[0]['event']);block['values'][field]['value']=value
    with pytest.raises(model.CanopyEnergyHold):model.calculate_leaf_removal(event=block,profile=profile)


@pytest.mark.parametrize('changes',({'leaf_heat_capacity':1e308},{'leaf_carbohydrate':5e-324},
    {'leaf_allocation':5e-324},{'leaf_heat_capacity':5e-324},
    {'reference_temperature':1e308},{'leaf_heat_capacity':1e307,'leaf_carbohydrate':1e8}))
def test_transport_extremes_fail_closed(profile,changes):
    block=deepcopy(FLOWS[2]['forcing'])
    for name,value in changes.items():block['values'][name]['value']=value
    with pytest.raises(model.CanopyEnergyHold,match='NUMERIC_HOLD'):model.calculate_transport(forcing=block,profile=profile)


def test_profile_bytes_are_pinned_and_wrong_profile_type_rejected(profile):
    with pytest.raises(CropRateHold,match='PROFILE_HOLD'):ReferenceParameters(profile.raw_bytes+b' ')
    for wrong in (None,profile.values):
        with pytest.raises(model.CanopyEnergyHold,match='PROFILE_HOLD'):model.calculate_transport(forcing=FLOWS[0]['forcing'],profile=wrong)
        with pytest.raises(model.CanopyEnergyHold,match='PROFILE_HOLD'):model.calculate_leaf_removal(event=EVENTS[0]['event'],profile=wrong)


def test_canonical_identity_depends_on_each_explicit_input_and_operation(profile):
    block=deepcopy(FLOWS[2]['forcing']);original=model.calculate_transport(forcing=block,profile=profile)
    reordered=dict(reversed(list(block.items())));reordered['values']=dict(reversed(list(block['values'].items())))
    assert model.calculate_transport(forcing=reordered,profile=profile)==original
    block['values']['incoming_capacity_temperature']['value']+=1
    changed=model.calculate_transport(forcing=block,profile=profile)
    assert changed['input_sha256']!=original['input_sha256']
    assert changed['calculation_sha256']!=original['calculation_sha256']
    assert changed['profile_sha256']==original['profile_sha256']
