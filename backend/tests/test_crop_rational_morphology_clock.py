from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path

import pytest

from app.crop_rational_morphology_clock import (
    advance_rational_internode_thermal_clock, normalize_rational_internode_clock_state,
    RationalMorphologyClockHold,
)
from app.crop_morphology_thermal_clock import advance_internode_thermal_clock
from app.crop_shoot_timeline import advance_shoot_event_timeline
from app.crop_internode_length import calculate_internode_length_point


def q(n=0,d=1,unit='s'):
    f=Fraction(n,d)
    return {'numerator':str(f.numerator),'denominator':str(f.denominator),'unit':unit}


def state(*,birth=None,at=None,age=None,base=0):
    return {'origin':'synthetic','age_basis':'since_internode_emergence',
        'temperature_basis':'indoor_air_piecewise_constant','internode_id':'synthetic-rational-node',
        'time_origin_utc':'2026-10-01T00:00:00Z','emerged_elapsed_seconds_exact':birth or q(),
        'at_elapsed_seconds_exact':at or q(),'age_exact':age or q(unit='degC_day'),
        'base_temperature':{'value':base,'unit':'degC'}}


def segment(start,end,temperature):
    return {'start_elapsed_seconds_exact':start,'end_elapsed_seconds_exact':end,
            'air_temperature':{'value':temperature,'unit':'degC'}}


# Expected fractions are independent manual C·seconds divided by 86400.
CASES=[
 ('one-third-birth',state(birth=q(1,3),at=q(1,3)),[segment(q(1,3),q(1),1)],q(1,129600,'degC_day')),
 ('two-temperatures',state(birth=q(1,3),at=q(1,3)),[segment(q(1,3),q(1,2),1),segment(q(1,2),q(1),3)],q(1,51840,'degC_day')),
 ('large-instant-difference',state(birth=q(2**56*3+1,3),at=q(2**56*3+1,3),base=5),
  [segment(q(2**56*3+1,3),q(2**56*3+2,3),20)],q(1,17280,'degC_day')),
 ('tiny-positive-age',state(),[segment(q(),q(1,10**400),1)],q(1,86400*10**400,'degC_day')),
 ('binary64-temperatures',state(base=.05),[segment(q(),q(1),.1)],q(3602879701896397,72057594037927936*86400,'degC_day')),
 ('stationary',state(at=q(1,3),age=q(5,7,'degC_day'),base=5),[segment(q(1,3),q(100,3),5)],q(5,7,'degC_day')),
 ('explicit-checkpoint',state(at=q(1,3),age=q(5,7,'degC_day'),base=5),[segment(q(1,3),q(10,21),10)],q(86401,120960,'degC_day')),
 ('whole-day',state(base=5),[segment(q(),q(43200),20),segment(q(43200),q(86400),15)],q(25,2,'degC_day')),
]


@pytest.mark.parametrize('name,current,segments,expected',CASES,ids=[c[0] for c in CASES])
def test_manual_independent_rational_clocks(name,current,segments,expected):
    inputs={'input_id':name,'state':deepcopy(current),'segments':deepcopy(segments)};before=deepcopy(inputs)
    r=advance_rational_internode_thermal_clock(inputs=inputs)
    assert r['checkpoint']['age_exact']==expected
    assert r['checkpoint']['at_elapsed_seconds_exact']==segments[-1]['end_elapsed_seconds_exact']
    assert r['checkpoint']['emerged_elapsed_seconds_exact']==current['emerged_elapsed_seconds_exact']
    assert r['scope']=='software_research_only' and r['gates']=='not_assessed'
    assert r['claim_scope']=='synthetic_crop_math_only' and len(r['input_sha256'])==64
    assert 'utc_whole_second' not in r and 'emerged_at' not in r['checkpoint']
    assert inputs==before and advance_rational_internode_thermal_clock(inputs=inputs)==r


def test_split_resume_and_whole_second_reference_keep_exact_age():
    _,current,segments,_=CASES[1]
    whole=advance_rational_internode_thermal_clock(inputs={'input_id':'whole','state':current,'segments':segments})
    first=advance_rational_internode_thermal_clock(inputs={'input_id':'first','state':current,'segments':segments[:1]})
    second=advance_rational_internode_thermal_clock(inputs={'input_id':'second','state':first['checkpoint'],'segments':segments[1:]})
    assert second['checkpoint']==whole['checkpoint']
    _,current,segments,expected=CASES[-1]
    rational=advance_rational_internode_thermal_clock(inputs={'input_id':'new','state':current,'segments':segments})
    old=advance_internode_thermal_clock(inputs={'input_id':'old','state':{
        'origin':'synthetic','age_basis':'since_internode_emergence','temperature_basis':'indoor_air_piecewise_constant',
        'internode_id':current['internode_id'],'emerged_at':current['time_origin_utc'],'at':current['time_origin_utc'],
        'age_exact':q(unit='degC_day'),'base_temperature':current['base_temperature']},'segments':[
            {'start_utc':'2026-10-01T00:00:00Z','end_utc':'2026-10-01T12:00:00Z','air_temperature':{'value':20,'unit':'degC'}},
            {'start_utc':'2026-10-01T12:00:00Z','end_utc':'2026-10-02T00:00:00Z','air_temperature':{'value':15,'unit':'degC'}}]})
    assert rational['checkpoint']['age_exact']==old['checkpoint']['age_exact']==expected


def test_normalization_and_leap_day_origin_preserve_explicit_clock():
    s=state(base=5);s['time_origin_utc']='2028-02-29T23:59:59Z'
    normalized=normalize_rational_internode_clock_state(state=s)
    assert normalized['base_temperature']=={'value':5.0,'unit':'degC'}
    assert normalized['time_origin_utc']==s['time_origin_utc'] and s['base_temperature']['value']==5
    p={'input_id':'normalization','state':s,'segments':[segment(q(),q(1,3),10)]}
    a=advance_rational_internode_thermal_clock(inputs=p)
    p['state']['base_temperature']['value']=5.0;p['segments'][0]['air_temperature']['value']=10.0
    assert advance_rational_internode_thermal_clock(inputs=p)==a


@pytest.mark.parametrize('change',['origin','basis','temperature-basis','id','origin-time','birth-after-current','age-at-birth',
    'time-unit','time-numerator','time-denominator','unreduced','leading-zero','too-long','age-unit','extra',
    'gap','overlap','zero-span','temperature-unit','below-base','bool-temperature','nonfinite'])
def test_bad_clock_or_forcing_is_held(change):
    p={'input_id':'bad','state':state(),'segments':[segment(q(),q(1),10)]};s=p['state'];seg=p['segments'][0]
    if change=='origin':s['origin']='observed'
    elif change=='basis':s['age_basis']='since_shoot_development_origin'
    elif change=='temperature-basis':s['temperature_basis']='canopy'
    elif change=='id':s['internode_id']=''
    elif change=='origin-time':s['time_origin_utc']='2026-02-30T00:00:00Z'
    elif change=='birth-after-current':s['emerged_elapsed_seconds_exact']=q(1)
    elif change=='age-at-birth':s['age_exact']=q(1,1,'degC_day')
    elif change=='time-unit':s['at_elapsed_seconds_exact']['unit']='degC_day'
    elif change=='time-numerator':s['at_elapsed_seconds_exact']['numerator']='-1'
    elif change=='time-denominator':s['at_elapsed_seconds_exact']['denominator']='0'
    elif change=='unreduced':s['at_elapsed_seconds_exact'].update(numerator='2',denominator='2')
    elif change=='leading-zero':s['at_elapsed_seconds_exact']['numerator']='00'
    elif change=='too-long':s['at_elapsed_seconds_exact']['numerator']='1'*1025
    elif change=='age-unit':s['age_exact']['unit']='s'
    elif change=='extra':s['emerged_at']='2026-10-01T00:00:00Z'
    elif change=='gap':seg['start_elapsed_seconds_exact']=q(1,3)
    elif change=='overlap':s['at_elapsed_seconds_exact']=q(1,3)
    elif change=='zero-span':seg['end_elapsed_seconds_exact']=q()
    elif change=='temperature-unit':seg['air_temperature']['unit']='K'
    elif change=='below-base':seg['air_temperature']['value']=-1
    elif change=='bool-temperature':seg['air_temperature']['value']=True
    else:seg['air_temperature']['value']=float('inf')
    with pytest.raises(RationalMorphologyClockHold):advance_rational_internode_thermal_clock(inputs=p)


def test_segment_and_generated_age_capacity_are_atomic_holds():
    for segments in [[],[segment(q(),q(1),1)]*513,[segment(q(),q(10**1000),1e308)]]:
        with pytest.raises(RationalMorphologyClockHold,match='CAPACITY_HOLD'):
            advance_rational_internode_thermal_clock(inputs={'input_id':'capacity','state':state(),'segments':segments})


def test_existing_fractional_emergence_events_keep_exact_remaining_age_into_length_point():
    r=Path(__file__).resolve().parents[2]
    timeline_case=json.loads((r/'fixtures/crop-shoot-timeline-reference-v1.json').read_bytes())['cases'][3]
    timeline=advance_shoot_event_timeline(inputs=timeline_case['inputs'])
    curve=json.loads((r/'fixtures/crop-internode-length-state-reference-v1.json').read_bytes())['cases'][0]['inputs']['curve']
    expected_ages=[q(1,43200,'degC_day'),q(1,86400,'degC_day'),q(unit='degC_day')]
    assert len(timeline['events'])==3
    for event,expected in zip(timeline['events'],expected_ages,strict=True):
        birth=event['elapsed_seconds_exact'];clock=state(birth=birth,at=birth)
        if birth!=q(1):
            assert event['utc_whole_second'] is None
            checkpoint=advance_rational_internode_thermal_clock(inputs={'input_id':'event-to-clock',
                'state':clock,'segments':[segment(birth,q(1),3)]})['checkpoint']
        else:checkpoint=normalize_rational_internode_clock_state(state=clock)
        assert checkpoint['age_exact']==expected
        point=calculate_internode_length_point(inputs={'input_id':'clock-to-point','origin':'synthetic',
            'thermal_age_basis':'since_internode_emergence','age_exact':checkpoint['age_exact'],'curve':curve})
        with localcontext() as ctx:
            ctx.prec=800
            a=Decimal(expected['numerator'])/Decimal(expected['denominator'])
            m,k,tm=(Decimal.from_float(float(curve['values'][key]['value'])) for key in
                    ('maximum_length','steepness','inflection_age'))
            value=m/(1+(-k*(a-tm)).exp())
        assert point['length']['value']==pytest.approx(float(value),rel=1e-12,abs=0)
