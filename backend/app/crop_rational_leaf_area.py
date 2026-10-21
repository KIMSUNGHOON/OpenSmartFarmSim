"""Leaf-specific exact air clock bound to an explicit canonical area state.

Only unit parsers are shared with the internode clock. No internode state
or age is converted into a leaf. See crop-rational-leaf-area-v1.md.
"""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import re

from . import crop_leaf_area as area
from .crop_morphology_thermal_clock import MorphologyClockHold, parse_whole_second_utc, thermal_age_fraction
from .crop_rational_morphology_clock import RationalMorphologyClockHold, _seconds, _temperature, _age_record


MODEL_VERSION = 'leaf-rational-air-area-state-research-v1'
CLOCK_VERSION = 'leaf-rational-air-thermal-clock-research-v1'
CLOCK_KEYS = {'origin','age_basis','temperature_basis','leaf_id','time_origin_utc',
              'emerged_elapsed_seconds_exact','at_elapsed_seconds_exact','base_temperature','age_exact'}


class RationalLeafAreaHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise RationalLeafAreaHold(reason)


def _identifier(value):
    _need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',value),
          'INPUT_HOLD: bounded ASCII identifier required')


def _digest(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _flags(version,identity):
    return {'model_version':version,'scope':'software_research_only','claim_scope':'synthetic_crop_math_only',
            'gates':'not_assessed','input_sha256':_digest({'model_version':version,**identity})}


def normalize_leaf_thermal_clock_state(*, state):
    _need(type(state) is dict and set(state)==CLOCK_KEYS,'INPUT_HOLD: closed leaf clock required')
    _need(state['origin']=='synthetic' and state['age_basis']=='since_leaf_emergence'
          and state['temperature_basis']=='indoor_air_piecewise_constant','INPUT_HOLD: explicit synthetic leaf air clock required')
    _identifier(state['leaf_id'])
    try:
        birth,at=(_seconds(state[k]) for k in ('emerged_elapsed_seconds_exact','at_elapsed_seconds_exact'))
        parse_whole_second_utc(state['time_origin_utc']);age=thermal_age_fraction(state['age_exact'])
        base=_temperature(state['base_temperature'])
    except (RationalMorphologyClockHold,MorphologyClockHold) as exc:
        raise RationalLeafAreaHold(str(exc)) from None
    _need(at>=birth and (at!=birth or age==0),'TIME_HOLD: leaf birth/checkpoint age mismatch')
    return {**state,'emerged_elapsed_seconds_exact':dict(state['emerged_elapsed_seconds_exact']),
        'at_elapsed_seconds_exact':dict(state['at_elapsed_seconds_exact']),'age_exact':dict(state['age_exact']),
        'base_temperature':{'value':base,'unit':'degC'}}


def advance_leaf_thermal_clock(*, inputs):
    _need(type(inputs) is dict and set(inputs)=={'input_id','state','segments'},'INPUT_HOLD: closed leaf clock advance required')
    _identifier(inputs['input_id']);state=normalize_leaf_thermal_clock_state(state=inputs['state'])
    segments=inputs['segments']
    _need(type(segments) is list and 1<=len(segments)<=512,'CAPACITY_HOLD: bounded nonempty leaf forcing required')
    try:
        at=_seconds(state['at_elapsed_seconds_exact']);age=thermal_age_fraction(state['age_exact'])
        base=Fraction.from_float(state['base_temperature']['value']);normalized=[]
        for segment in segments:
            _need(type(segment) is dict and set(segment)=={'start_elapsed_seconds_exact','end_elapsed_seconds_exact','air_temperature'},
                  'INPUT_HOLD: closed exact air segment required')
            start,end=(_seconds(segment[k]) for k in ('start_elapsed_seconds_exact','end_elapsed_seconds_exact'))
            _need(start==at and end>start,'TIME_HOLD: contiguous forward leaf forcing required')
            temperature=_temperature(segment['air_temperature']);difference=Fraction.from_float(temperature)-base
            _need(difference>=0,'THERMAL_DOMAIN_HOLD: air below explicit base unsupported')
            age+=difference*(end-start)/86400;_age_record(age);at=end
            normalized.append({'start_elapsed_seconds_exact':dict(segment['start_elapsed_seconds_exact']),
                'end_elapsed_seconds_exact':dict(segment['end_elapsed_seconds_exact']),
                'air_temperature':{'value':temperature,'unit':'degC'}})
        checkpoint={**state,'at_elapsed_seconds_exact':dict(normalized[-1]['end_elapsed_seconds_exact']),
                    'age_exact':_age_record(age)}
    except (RationalMorphologyClockHold,MorphologyClockHold) as exc:
        raise RationalLeafAreaHold(str(exc)) from None
    return {**_flags(CLOCK_VERSION,{'inputs':{'input_id':inputs['input_id'],'state':state,'segments':normalized}}),
            'checkpoint':checkpoint}


def initialize_rational_leaf_area(*, inputs):
    _need(type(inputs) is dict and set(inputs)=={'input_id','clock_state','curve','normalization','initial_area'},
          'INPUT_HOLD: explicit closed leaf clock/area initialization required')
    _identifier(inputs['input_id']);clock=normalize_leaf_thermal_clock_state(state=inputs['clock_state'])
    try:
        initialized=area.initialize_leaf_area(inputs={'input_id':inputs['input_id'],'origin':'synthetic',
            'thermal_age_basis':'since_leaf_emergence','normalization':inputs['normalization'],
            'leaf_id':clock['leaf_id'],'age_exact':clock['age_exact'],'curve':inputs['curve'],
            'initial_area':inputs['initial_area']})
    except area.LeafAreaHold as exc:
        raise RationalLeafAreaHold(str(exc)) from None
    state={'model_version':MODEL_VERSION,'clock_state':clock,'area_state':initialized['state'],'clock_anchor':deepcopy(clock)}
    return {**_flags(MODEL_VERSION,{'operation':'initialize','input_id':inputs['input_id'],'state':state}),'state':state}


def normalize_rational_leaf_area_state(*, state):
    _need(type(state) is dict and set(state)=={'model_version','clock_state','area_state','clock_anchor'}
          and state['model_version']==MODEL_VERSION,'STATE_HOLD: closed supported rational leaf area state required')
    clock=normalize_leaf_thermal_clock_state(state=state['clock_state'])
    anchor=normalize_leaf_thermal_clock_state(state=state['clock_anchor'])
    try:
        current=area.normalize_leaf_area_state(state=state['area_state'])
        age,initial_age=(thermal_age_fraction(c['age_exact']) for c in (clock,anchor))
        at,initial_at=(_seconds(c['at_elapsed_seconds_exact']) for c in (clock,anchor))
    except (area.LeafAreaHold,MorphologyClockHold,RationalMorphologyClockHold) as exc:
        raise RationalLeafAreaHold(str(exc)) from None
    constants=set(clock)-{'at_elapsed_seconds_exact','age_exact'}
    _need(all(clock[k]==anchor[k] for k in constants),'STATE_HOLD: leaf clock identity changed')
    _need(clock['leaf_id']==current['leaf_id'] and clock['age_exact']==current['age_exact']
          and anchor['age_exact']==current['anchor']['age_exact'],'STATE_HOLD: leaf clock/area anchor mismatch')
    _need(at>=initial_at and age>=initial_age and (at!=initial_at or age==initial_age),
          'STATE_HOLD: initial clock after current leaf checkpoint')
    return {'model_version':MODEL_VERSION,'clock_state':clock,'area_state':current,'clock_anchor':anchor}


def advance_rational_leaf_area(*, inputs):
    _need(type(inputs) is dict and set(inputs)=={'input_id','state','segments'},'INPUT_HOLD: closed rational leaf advance required')
    _identifier(inputs['input_id']);state=normalize_rational_leaf_area_state(state=inputs['state'])
    clock=advance_leaf_thermal_clock(inputs={'input_id':inputs['input_id'],'state':state['clock_state'],'segments':inputs['segments']})
    try:
        advanced=area.advance_leaf_area(inputs={'input_id':inputs['input_id'],'state':state['area_state'],
            'end_age_exact':clock['checkpoint']['age_exact']})
    except area.LeafAreaHold as exc:
        raise RationalLeafAreaHold(str(exc)) from None
    current={**state,'clock_state':clock['checkpoint'],'area_state':advanced['state']}
    return {**_flags(MODEL_VERSION,{'operation':'advance','state':state,
        'clock_input_sha256':clock['input_sha256'],'area_input_sha256':advanced['input_sha256']}),
        'state':current,'area_change':advanced['area_change'],'clock_input_sha256':clock['input_sha256'],
        'area_input_sha256':advanced['input_sha256']}
