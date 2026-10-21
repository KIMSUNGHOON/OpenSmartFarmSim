"""Declared existing leaves, stable references and tracked area totals only."""
from copy import deepcopy
from hashlib import sha256
import json
from math import fsum, isfinite
import re

from . import crop_rational_leaf_area as leaf
from .crop_morphology_thermal_clock import MorphologyClockHold, parse_whole_second_utc
from .crop_rational_morphology_clock import RationalMorphologyClockHold, _seconds


MODEL_VERSION = 'declared-leaf-inventory-research-v1'
MAX_BYTES = 2*1024**2
STATE_KEYS = {'model_version','origin','time_origin_utc','at_elapsed_seconds_exact','initial_inventory','leaves'}


class LeafInventoryHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise LeafInventoryHold(reason)


def _identifier(value):
    _need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',value),
          'INPUT_HOLD: bounded ASCII identifier required')


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def _bounded(value):
    raw=_canonical(value)
    _need(len(raw)<=MAX_BYTES,'CAPACITY_HOLD: declared leaf payload exceeds 2MiB')
    return raw


def _scope(origin,at):
    try:
        parse_whole_second_utc(origin)
        return _seconds(at)
    except (MorphologyClockHold,RationalMorphologyClockHold) as exc:
        raise LeafInventoryHold(str(exc)) from None


def _sum(values):
    try:
        value=fsum(values)
    except OverflowError:
        raise LeafInventoryHold('NUMERIC_HOLD: tracked area sum overflow') from None
    _need(isfinite(value) and value>=0,'NUMERIC_HOLD: finite tracked area required')
    return {'value':value,'unit':'m2'}


def normalize_leaf_inventory_state(*, state):
    _need(type(state) is dict and set(state)==STATE_KEYS and state['model_version']==MODEL_VERSION
          and state['origin']=='synthetic','STATE_HOLD: closed synthetic declared inventory required')
    at=_scope(state['time_origin_utc'],state['at_elapsed_seconds_exact'])
    supplied=state['leaves'];_need(type(supplied) is list and 1<=len(supplied)<=512,'CAPACITY_HOLD: 1-512 declared leaves required')
    initial=state['initial_inventory']
    _need(type(initial) is dict and set(initial)=={'at_elapsed_seconds_exact','leaf_attachments'},'STATE_HOLD: closed initial inventory required')
    initial_at=_scope(state['time_origin_utc'],initial['at_elapsed_seconds_exact'])
    _need(initial_at<=at,'STATE_HOLD: initial inventory after current checkpoint')
    normalized=[];identities=[];seen=set();size=0
    for item in supplied:
        _need(type(item) is dict and set(item)=={'attachment_internode_id','state'},'STATE_HOLD: closed declared leaf record required')
        _identifier(item['attachment_internode_id'])
        try:
            current=leaf.normalize_rational_leaf_area_state(state=item['state'])
        except leaf.RationalLeafAreaHold as exc:
            raise LeafInventoryHold(str(exc)) from None
        clock=current['clock_state'];identifier=clock['leaf_id']
        _need(identifier not in seen,'STATE_HOLD: duplicate declared leaf ID');seen.add(identifier)
        _need(clock['time_origin_utc']==state['time_origin_utc'] and clock['at_elapsed_seconds_exact']==state['at_elapsed_seconds_exact']
              and current['clock_anchor']['at_elapsed_seconds_exact']==initial['at_elapsed_seconds_exact'],
              'STATE_HOLD: declared leaf clock scope mismatch')
        record={'attachment_internode_id':item['attachment_internode_id'],'state':current}
        size+=len(_canonical(record));_need(size<=MAX_BYTES,'CAPACITY_HOLD: declared leaf records exceed 2MiB')
        normalized.append(record);identities.append({'leaf_id':identifier,'attachment_internode_id':item['attachment_internode_id']})
    _need(type(initial['leaf_attachments']) is list and initial['leaf_attachments']==identities,
          'STATE_HOLD: declared initial leaf identities/order/references changed')
    result={'model_version':MODEL_VERSION,'origin':'synthetic','time_origin_utc':state['time_origin_utc'],
        'at_elapsed_seconds_exact':dict(state['at_elapsed_seconds_exact']),'leaves':normalized,
        'initial_inventory':{'at_elapsed_seconds_exact':dict(initial['at_elapsed_seconds_exact']),'leaf_attachments':identities}}
    _bounded(result);_sum(item['state']['area_state']['area']['value'] for item in normalized)
    return result


def _envelope(state,identity):
    value={'model_version':MODEL_VERSION,'scope':'software_research_only','claim_scope':'synthetic_crop_math_only',
        'gates':'not_assessed','input_sha256':sha256(_canonical({'model_version':MODEL_VERSION,**identity})).hexdigest(),
        'state':state,'tracked_leaf_count':len(state['leaves']),
        'tracked_leaf_area':_sum(item['state']['area_state']['area']['value'] for item in state['leaves'])}
    _bounded(value);return value


def initialize_leaf_inventory(*, inputs):
    _need(type(inputs) is dict and set(inputs)=={'input_id','time_origin_utc','at_elapsed_seconds_exact','leaves'},
          'INPUT_HOLD: closed declared inventory initialization required')
    _identifier(inputs['input_id']);_scope(inputs['time_origin_utc'],inputs['at_elapsed_seconds_exact'])
    supplied=inputs['leaves'];_need(type(supplied) is list and 1<=len(supplied)<=512,'CAPACITY_HOLD: 1-512 declared leaves required')
    records=[];identities=[];receipts=[];size=0
    for item in supplied:
        _need(type(item) is dict and set(item)=={'attachment_internode_id','initialization'},'INPUT_HOLD: closed declared leaf initialization required')
        _identifier(item['attachment_internode_id'])
        try:
            initialized=leaf.initialize_rational_leaf_area(inputs=item['initialization'])
        except leaf.RationalLeafAreaHold as exc:
            raise LeafInventoryHold(str(exc)) from None
        record={'attachment_internode_id':item['attachment_internode_id'],'state':initialized['state']}
        size+=len(_canonical(record));_need(size<=MAX_BYTES,'CAPACITY_HOLD: declared leaf records exceed 2MiB')
        records.append(record);identifier=initialized['state']['clock_state']['leaf_id']
        identities.append({'leaf_id':identifier,'attachment_internode_id':item['attachment_internode_id']})
        receipts.append({'leaf_id':identifier,'input_sha256':initialized['input_sha256']})
    state=normalize_leaf_inventory_state(state={'model_version':MODEL_VERSION,'origin':'synthetic',
        'time_origin_utc':inputs['time_origin_utc'],'at_elapsed_seconds_exact':dict(inputs['at_elapsed_seconds_exact']),
        'leaves':records,'initial_inventory':{'at_elapsed_seconds_exact':dict(inputs['at_elapsed_seconds_exact']),
                                           'leaf_attachments':identities}})
    return _envelope(state,{'operation':'initialize','input_id':inputs['input_id'],'state':state,'leaf_inputs':receipts})


def advance_leaf_inventory(*, inputs):
    _need(type(inputs) is dict and set(inputs)=={'input_id','state','segments'},'INPUT_HOLD: closed declared inventory advance required')
    _identifier(inputs['input_id']);state=normalize_leaf_inventory_state(state=inputs['state'])
    records=[];receipts=[];changes=[]
    for item in state['leaves']:
        try:
            advanced=leaf.advance_rational_leaf_area(inputs={'input_id':inputs['input_id'],'state':item['state'],'segments':inputs['segments']})
        except leaf.RationalLeafAreaHold as exc:
            raise LeafInventoryHold(str(exc)) from None
        records.append({'attachment_internode_id':item['attachment_internode_id'],'state':advanced['state']})
        identifier=advanced['state']['clock_state']['leaf_id'];receipts.append({'leaf_id':identifier,'input_sha256':advanced['input_sha256']})
        changes.append({'leaf_id':identifier,'area_change':advanced['area_change']})
    current=normalize_leaf_inventory_state(state={**state,'at_elapsed_seconds_exact':
        dict(records[0]['state']['clock_state']['at_elapsed_seconds_exact']),'leaves':records,
        'initial_inventory':deepcopy(state['initial_inventory'])})
    value=_envelope(current,{'operation':'advance','state':state,'input_id':inputs['input_id'],'leaf_inputs':receipts})
    value.update(leaf_area_changes=changes,tracked_area_change=_sum(item['area_change']['value'] for item in changes))
    _bounded(value);return value
