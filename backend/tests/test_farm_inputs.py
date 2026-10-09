"""Explicit user intent; no measured crop, rights authority or forecast."""

from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.farm_inputs import FarmInputs, canonical_farm_inputs, validate_economic_scope
from app.economic_contracts import EconomicScenario
from app.economics import canonical_scenario_sha256
from app.thermal_run_store import snapshot_id_for
from test_economics import base, opening_lot


ROOT = Path(__file__).resolve().parents[2]
AT = '2026-09-28T00:00:00Z'


def sources():
    return tuple((ROOT/'fixtures'/name).read_bytes() for name in (
        'manifest-v2.json', 'synthetic-weather-v1.json', 'synthetic-thermal-parameters-v1.json'))


def evidence(input_id):
    return dict(input_id=input_id, revision='r1', source_ref='self-authored-contract-test',
                origin='user', evidence_level='assumed', available_at=AT)


def number(value, unit, input_id):
    return dict(value=format(Decimal(str(value)), 'f'), unit=unit, **evidence(input_id))


def example():
    thermal = json.loads(sources()[2])
    economic = EconomicScenario.model_validate(base())
    fields = ('floor_area', 'indoor_volume', 'effective_heat_capacity', 'dry_air_mass',
              'envelope_conductance', 'absorbed_solar_fraction')
    facility = {name: number(thermal['parameters'][name]['value'],
                            thermal['parameters'][name]['unit'], name) for name in fields}
    facility.update(zone_id='zone-1', facility_type='single_zone_greenhouse',
                    tenure='unknown', decision_basis='existing_facility_crop_change',
                    provenance=evidence('facility-intent'),
                    cultivable_area=number('80', 'm²', 'cultivable-area'))
    return dict(schema_version='farm-inputs-v1', scenario_id='farm-1', scenario_revision='r1',
        research_job_id='00000000-0000-4000-8000-000000000001',
        snapshot_id=snapshot_id_for(*sources()), decision_context_id='context-1',
        decision_at=AT, market_context={'kind':'unavailable','hold_report_id':'hold-1'},
        goal_id='historical-thermal-replay', period_start='2026-10-01', period_end='2026-11-30',
        economic=dict(scenario_id=economic.scenario_id, revision=economic.scenario_revision,
                      sha256=canonical_scenario_sha256(economic), candidate_id='a'*64),
        facility=facility,
        initial_state={name:number(row['value'], row['unit'], 'initial-'+name)
                       for name,row in thermal['initial_state'].items()},
        heater=dict(capacity=number('500','W_th','capacity'),
                    setpoint=number('293','K','setpoint'),
                    available=dict(value=True, **evidence('heater-available')),
                    mode='indirect_sensible', capacity_basis='delivered_thermal_power',
                    control_version='thermal-indirect-sensible-end-target-v1',
                    efficiency_status='unavailable', metering_status='unavailable'),
        forcing=[dict(start=row['start_utc'],end=row['end_utc'],
                      **{name:number(item['value'],item['unit'],f'forcing-{index}-{name}')
                         for name,item in row['assumed_forcing'].items()})
                 for index,row in enumerate(thermal['intervals'])],
        crops=[dict(crop_id='crop-1', batch_id='batch-1', species='synthetic-species-intent',
                    variety='unspecified-user-intent', profile_status='unavailable',
                    provenance=evidence('crop-intent-1'),
                    area=number('80','m²','crop-area-1'),
                    occupancy=dict(start='2026-10-01T00:00:00Z',end='2026-10-25T00:00:00Z'),
                    release_at='2026-10-26T00:00:00Z',
                    harvest_window=dict(start='2026-10-14T00:00:00Z',end='2026-10-16T00:00:00Z'),
                    sales_window=dict(start='2026-10-15T00:00:00Z',end='2026-10-18T00:00:00Z'),
                    collection_window=dict(start='2026-10-15T00:00:00Z',end='2026-10-24T00:00:00Z'),
                    grades=['grade-1'],channels=['direct'])],
        objective='conditional_operating_margin',
        constraints=dict(capex_ceiling=number('1000','KRW','capex-ceiling'),
                         minimum_cash=number('0','KRW','minimum-cash')))


def parse(value):
    return FarmInputs.model_validate_json(json.dumps(value))


def test_explicit_farm_document_canonicalizes_and_revision_changes_hash():
    raw = canonical_farm_inputs(parse(example()))
    assert raw == canonical_farm_inputs(parse(dict(reversed(list(example().items())))))
    altered = example()
    altered['facility']['floor_area']['value'] = '101'
    assert sha256(raw).digest() != sha256(canonical_farm_inputs(parse(altered))).digest()
    assert json.loads(raw)['heater']['efficiency_status'] == 'unavailable'


@pytest.mark.parametrize('path,value', [
    (('facility','floor_area','unit'),'m³'),
    (('facility','indoor_volume','value'),'0'),
    (('facility','absorbed_solar_fraction','value'),'1.01'),
    (('initial_state','temperature','value'),293.0),
    (('initial_state','humidity_ratio','value'),'-1'),
    (('heater','capacity','value'),'-1'),
    (('heater','efficiency_status'),'verified'),
    (('facility','floor_area','available_at'),'2026-09-29T00:00:00Z'),
    (('constraints','minimum_cash','unit'),'kg'),
    (('heater','available','value'),1),
    (('facility','floor_area','value'),'1e2'),
    (('facility','floor_area','value'),'NaN'),
    (('facility','provenance','origin'),'measured'),
])
def test_invalid_quantities_and_unearned_evidence_rejected(path,value):
    document=example()
    target=document
    for key in path[:-1]:
        target=target[key]
    target[path[-1]]=value
    with pytest.raises(ValidationError):
        parse(document)


def test_missing_constraints_and_constructed_model_are_revalidated():
    document=example()
    del document['constraints']['minimum_cash']
    with pytest.raises(ValidationError):
        parse(document)
    farm=parse(example())
    altered=farm.model_copy(update={'objective':'forecast_best_crop'})
    with pytest.raises(ValidationError):
        canonical_farm_inputs(altered)


def test_record_id_revision_cannot_represent_two_values():
    document=example()
    document['facility']['cultivable_area']['input_id']='floor_area'
    with pytest.raises(ValidationError,match='record'):
        parse(document)


def test_simultaneous_area_and_cleanup_reservations_use_exact_decimals():
    document=example()
    other=deepcopy(document['crops'][0])
    other.update(crop_id='crop-2',batch_id='batch-2',provenance=evidence('crop-intent-2'))
    other['area']=number('0.000000000000000000000000000001','m²','crop-area-2')
    document['crops'].append(other)
    with pytest.raises(ValidationError,match='area'):
        parse(document)
    other['occupancy']=dict(start='2026-10-26T00:00:00Z',end='2026-11-20T00:00:00Z')
    other['release_at']='2026-11-21T00:00:00Z'
    other['harvest_window']=dict(start='2026-11-14T00:00:00Z',end='2026-11-16T00:00:00Z')
    other['sales_window']=dict(start='2026-11-15T00:00:00Z',end='2026-11-18T00:00:00Z')
    other['collection_window']=dict(start='2026-11-15T00:00:00Z',end='2026-11-24T00:00:00Z')
    parse(document)
    other['occupancy']['start']='2026-10-25T12:00:00Z'
    with pytest.raises(ValidationError,match='area'):
        parse(document)


def test_economic_scope_checks_actual_pin_tenant_and_crop_event_windows():
    farm=parse(example())
    economic=EconomicScenario.model_validate(base())
    validate_economic_scope(farm,economic,'tenant-1')
    with pytest.raises(ValueError):
        validate_economic_scope(farm,economic,'another-tenant')
    for field,value in [('period_end','2026-12-01'),('decision_at','2026-09-27T00:00:00Z')]:
        altered=example()
        altered[field]=value
        with pytest.raises(ValueError):
            validate_economic_scope(parse(altered),economic,'tenant-1')
    altered=example()
    altered['economic']['sha256']='b'*64
    with pytest.raises(ValueError):
        validate_economic_scope(parse(altered),economic,'tenant-1')
    for field,window in (
        ('harvest_window',dict(start='2026-10-14T00:00:00Z',end='2026-10-15T00:00:00Z')),
        ('sales_window',dict(start='2026-10-15T00:00:00Z',end='2026-10-15T02:00:00Z')),
        ('collection_window',dict(start='2026-10-21T00:00:00Z',end='2026-10-23T00:00:00Z')),
    ):
        altered=example()
        altered['crops'][0][field]=window
        scoped=parse(altered)
        with pytest.raises(ValueError):
            validate_economic_scope(scoped,economic,'tenant-1')


def test_missing_planting_for_new_harvest_does_not_invent_a_crop():
    document=example()
    document['crops']=[]
    with pytest.raises(ValueError,match='batch'):
        validate_economic_scope(parse(document),EconomicScenario.model_validate(base()),'tenant-1')


def test_grade_and_channel_must_be_declared_and_calendar_is_half_open():
    for name in ('grades','channels'):
        document=example()
        document['crops'][0][name]=['different']
        with pytest.raises(ValueError,match='scope'):
            validate_economic_scope(parse(document),EconomicScenario.model_validate(base()),'tenant-1')
    document=example()
    document['crops'][0]['harvest_window']['end']='2026-10-15T00:00:00Z'
    with pytest.raises(ValueError,match='calendar'):
        validate_economic_scope(parse(document),EconomicScenario.model_validate(base()),'tenant-1')


def test_nullable_constraints_stay_unknown_and_negative_minimum_cash_is_explicit():
    document=example()
    document['constraints']=dict(capex_ceiling=None,minimum_cash=None)
    assert json.loads(canonical_farm_inputs(parse(document)))['constraints']['minimum_cash'] is None
    document['constraints']['minimum_cash']=number('-10','KRW','minimum-cash')
    assert parse(document).constraints.minimum_cash.amount == Decimal('-10')


def test_duplicate_crop_and_non_utc_calendar_rejected():
    document=example()
    document['crops'].append(deepcopy(document['crops'][0]))
    with pytest.raises(ValueError,match='duplicate'):
        parse(document)
    document=example()
    document['crops'][0]['release_at']='2026-10-26T09:00:00+09:00'
    with pytest.raises(ValueError,match='UTC'):
        parse(document)


def test_opening_inventory_does_not_require_inventing_a_current_planting():
    economic=EconomicScenario.model_validate(base(harvests=(),packouts=(),culls=(),
        opening_inventory=(opening_lot(),)))
    document=example()
    document['crops']=[]
    document['economic']['sha256']=canonical_scenario_sha256(economic)
    validate_economic_scope(parse(document),economic,'tenant-1')
    altered=economic.model_copy(update={'opening_inventory':()})
    document['economic']['sha256']=canonical_scenario_sha256(altered)
    with pytest.raises(ValueError,match='batch'):
        validate_economic_scope(parse(document),altered,'tenant-1')


def test_area_calculation_does_not_inherit_callers_decimal_context():
    with localcontext() as context:
        context.prec=6
        context.Emax=9
        context.Emin=-9
        test_simultaneous_area_and_cleanup_reservations_use_exact_decimals()
