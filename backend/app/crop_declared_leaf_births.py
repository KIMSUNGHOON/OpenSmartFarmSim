"""Explicit synthetic leaf births advanced only through post-birth forcing."""
from hashlib import sha256
import json
from math import fsum,isfinite

from . import crop_rational_leaf_area as leaf
from .crop_morphology_thermal_clock import MorphologyClockHold,parse_whole_second_utc
from .crop_rational_morphology_clock import RationalMorphologyClockHold,_seconds,_temperature


MODEL_VERSION='declared-leaf-births-research-v1'
MAX_BYTES=2*1024**2
EVENT_KEYS={'leaf_id','attachment_internode_id','emerged_elapsed_seconds_exact',
            'base_temperature','curve','normalization','initial_area'}


class DeclaredLeafBirthHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:
        raise DeclaredLeafBirthHold(reason)


def _bounded(value):
    try:
        raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    except (TypeError,ValueError,OverflowError,RecursionError):
        raise DeclaredLeafBirthHold('INPUT_HOLD: finite JSON payload required') from None
    _need(len(raw)<=MAX_BYTES,'CAPACITY_HOLD: declared birth payload exceeds 2MiB')
    return raw


def _record(value):
    return {'numerator':str(value.numerator),'denominator':str(value.denominator),'unit':'s'}


def _forcing(segments):
    _need(type(segments) is list and 1<=len(segments)<=512,'CAPACITY_HOLD: 1-512 air segments required')
    normalized=[];previous=None
    for segment in segments:
        _need(type(segment) is dict and set(segment)=={'start_elapsed_seconds_exact','end_elapsed_seconds_exact','air_temperature'},
              'INPUT_HOLD: closed declared-birth air segment required')
        start,end=(_seconds(segment[k]) for k in ('start_elapsed_seconds_exact','end_elapsed_seconds_exact'))
        _need(end>start and (previous is None or start==previous),'TIME_HOLD: contiguous forward birth forcing required')
        temperature=_temperature(segment['air_temperature']);previous=end
        normalized.append({'start_elapsed_seconds_exact':_record(start),'end_elapsed_seconds_exact':_record(end),
                           'air_temperature':{'value':temperature,'unit':'degC'}})
    return normalized


def create_declared_leaves(*,inputs):
    raw=_bounded(inputs)
    _need(type(inputs) is dict and set(inputs)=={'input_id','origin','time_origin_utc','segments','births'}
          and inputs['origin']=='synthetic','INPUT_HOLD: closed explicit synthetic leaf births required')
    try:
        leaf._identifier(inputs['input_id']);parse_whole_second_utc(inputs['time_origin_utc'])
        forcing=_forcing(inputs['segments']);start=_seconds(forcing[0]['start_elapsed_seconds_exact'])
        end=_seconds(forcing[-1]['end_elapsed_seconds_exact']);supplied=inputs['births']
        _need(type(supplied) is list and len(supplied)<=512,'CAPACITY_HOLD: 0-512 declared births required')
        previous=start;seen=set();records=[];record_bytes=0
        for event in supplied:
            _need(type(event) is dict and set(event)==EVENT_KEYS,'INPUT_HOLD: closed declared leaf birth required')
            identifier=event['leaf_id'];leaf._identifier(identifier);leaf._identifier(event['attachment_internode_id'])
            birth=_seconds(event['emerged_elapsed_seconds_exact'])
            _need(start<birth<=end and birth>=previous,'TIME_HOLD: ordered births in (start,end] required')
            _need(identifier not in seen,'INPUT_HOLD: duplicate declared birth leaf ID');seen.add(identifier);previous=birth
            clock={'origin':'synthetic','age_basis':'since_leaf_emergence','temperature_basis':'indoor_air_piecewise_constant',
                'leaf_id':identifier,'time_origin_utc':inputs['time_origin_utc'],'emerged_elapsed_seconds_exact':_record(birth),
                'at_elapsed_seconds_exact':_record(birth),'base_temperature':event['base_temperature'],
                'age_exact':{'numerator':'0','denominator':'1','unit':'degC_day'}}
            initialized=leaf.initialize_rational_leaf_area(inputs={'input_id':inputs['input_id'],'clock_state':clock,
                'curve':event['curve'],'normalization':event['normalization'],'initial_area':event['initial_area']})
            state=initialized['state'];advanced_hash=None
            remaining=[{**segment,'start_elapsed_seconds_exact':_record(max(birth,_seconds(segment['start_elapsed_seconds_exact'])))}
                       for segment in forcing if _seconds(segment['end_elapsed_seconds_exact'])>birth]
            if remaining:
                advanced=leaf.advance_rational_leaf_area(inputs={'input_id':inputs['input_id'],'state':state,'segments':remaining})
                state=advanced['state'];advanced_hash=advanced['input_sha256']
            record={'attachment_internode_id':event['attachment_internode_id'],'state':state,
                'initialization_input_sha256':initialized['input_sha256'],'advancement_input_sha256':advanced_hash}
            record_bytes+=len(_bounded(record));_need(record_bytes<=MAX_BYTES,'CAPACITY_HOLD: new leaf records exceed 2MiB')
            records.append(record)
        try:
            total=fsum(item['state']['area_state']['area']['value'] for item in records)
        except OverflowError:
            raise DeclaredLeafBirthHold('NUMERIC_HOLD: new leaf area sum overflow') from None
        _need(isfinite(total) and total>=0,'NUMERIC_HOLD: finite new leaf area sum required')
    except (leaf.RationalLeafAreaHold,RationalMorphologyClockHold,MorphologyClockHold) as exc:
        raise DeclaredLeafBirthHold(str(exc)) from None
    result={'model_version':MODEL_VERSION,'scope':'software_research_only','claim_scope':'synthetic_crop_math_only',
        'gates':'not_assessed','input_sha256':sha256(MODEL_VERSION.encode()+b'\n'+raw).hexdigest(),
        'time_origin_utc':inputs['time_origin_utc'],'start_elapsed_seconds_exact':_record(start),
        'end_elapsed_seconds_exact':_record(end),'new_leaves':records,'new_leaf_area':{'value':total,'unit':'m2'}}
    _bounded(result);return result
