"""Existing leaves and explicitly declared births, with separate immutable anchors."""
from copy import deepcopy
from hashlib import sha256

from . import crop_declared_leaf_births as births
from . import crop_leaf_inventory as inventory
from . import crop_rational_leaf_area as leaf
from .crop_rational_morphology_clock import RationalMorphologyClockHold,_seconds


MODEL_VERSION='declared-leaf-population-research-v1'
STATE_KEYS={'model_version','time_origin_utc','at_elapsed_seconds_exact','initial_inventory_state','new_leaves','birth_inventory'}


class LeafPopulationHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:
        raise LeafPopulationHold(reason)


def _digest(value):
    return sha256(births._bounded(value)).hexdigest()


def _declared_initialization(event,origin):
    _need(type(event) is dict and set(event)==births.EVENT_KEYS,'STATE_HOLD: closed population birth declaration required')
    leaf._identifier(event['leaf_id']);leaf._identifier(event['attachment_internode_id'])
    clock={'origin':'synthetic','age_basis':'since_leaf_emergence','temperature_basis':'indoor_air_piecewise_constant',
        'leaf_id':event['leaf_id'],'time_origin_utc':origin,'emerged_elapsed_seconds_exact':deepcopy(event['emerged_elapsed_seconds_exact']),
        'at_elapsed_seconds_exact':deepcopy(event['emerged_elapsed_seconds_exact']),'base_temperature':deepcopy(event['base_temperature']),
        'age_exact':{'numerator':'0','denominator':'1','unit':'degC_day'}}
    return leaf.initialize_rational_leaf_area(inputs={'input_id':'population-declaration-validation','clock_state':clock,
        'curve':event['curve'],'normalization':event['normalization'],'initial_area':event['initial_area']})['state']


def _normalize(state):
    births._bounded(state)
    _need(type(state) is dict and set(state)==STATE_KEYS and state['model_version']==MODEL_VERSION,
          'STATE_HOLD: closed supported leaf population required')
    current=inventory.normalize_leaf_inventory_state(state=state['initial_inventory_state'])
    at=_seconds(state['at_elapsed_seconds_exact']);origin=state['time_origin_utc']
    _need(current['time_origin_utc']==origin and current['at_elapsed_seconds_exact']==state['at_elapsed_seconds_exact'],
          'STATE_HOLD: initial leaf inventory and population scope differ')
    declared=state['new_leaves'];_need(type(declared) is list and len(current['leaves'])+len(declared)<=512,
                                    'CAPACITY_HOLD: 1-512 total population leaves required')
    initial_at=_seconds(current['initial_inventory']['at_elapsed_seconds_exact']);previous=initial_at
    seen={item['state']['clock_state']['leaf_id'] for item in current['leaves']};records=[]
    for item in declared:
        _need(type(item) is dict and set(item)=={'declaration','declaration_sha256','state'},'STATE_HOLD: closed population leaf record required')
        declaration=item['declaration'];_need(item['declaration_sha256']==_digest(declaration),'STATE_HOLD: original birth declaration changed')
        initial=_declared_initialization(declaration,origin);expected_clock=initial['clock_anchor'];identifier=expected_clock['leaf_id']
        birth=_seconds(expected_clock['emerged_elapsed_seconds_exact'])
        _need(initial_at<birth<=at and birth>=previous,'STATE_HOLD: ordered new leaves after initial inventory required');previous=birth
        _need(identifier not in seen,'STATE_HOLD: duplicate population leaf ID');seen.add(identifier)
        normalized=leaf.normalize_rational_leaf_area_state(state=item['state'])
        _need(normalized['clock_anchor']==expected_clock and normalized['clock_state']['at_elapsed_seconds_exact']==state['at_elapsed_seconds_exact']
              and normalized['area_state']['anchor']==initial['area_state']['anchor']
              and normalized['area_state']['curve']==initial['area_state']['curve'],
              'STATE_HOLD: current leaf and original declaration anchor differ')
        records.append({'declaration':deepcopy(declaration),'declaration_sha256':item['declaration_sha256'],'state':normalized})
    expected_inventory=[{'leaf_id':q['declaration']['leaf_id'],'declaration_sha256':q['declaration_sha256']} for q in records]
    _need(type(state['birth_inventory']) is list and state['birth_inventory']==expected_inventory,
          'STATE_HOLD: declared birth inventory and current leaves differ')
    result={'model_version':MODEL_VERSION,'time_origin_utc':origin,'at_elapsed_seconds_exact':deepcopy(state['at_elapsed_seconds_exact']),
            'initial_inventory_state':current,'new_leaves':records,'birth_inventory':expected_inventory}
    births._bounded(result);inventory._sum(item['area_state']['area']['value'] for item in
        [*(q['state'] for q in current['leaves']),*(q['state'] for q in records)])
    return result


def normalize_leaf_population_state(*,state):
    try:
        return _normalize(state)
    except (births.DeclaredLeafBirthHold,inventory.LeafInventoryHold,leaf.RationalLeafAreaHold,RationalMorphologyClockHold) as exc:
        raise LeafPopulationHold(str(exc)) from None


def _envelope(state,identity,new_count):
    total=inventory._sum(item['area_state']['area']['value'] for item in
        [*(q['state'] for q in state['initial_inventory_state']['leaves']),*(q['state'] for q in state['new_leaves'])])
    result={'model_version':MODEL_VERSION,'scope':'software_research_only','claim_scope':'synthetic_crop_math_only',
        'gates':'not_assessed','input_sha256':_digest({'model_version':MODEL_VERSION,**identity}),'state':state,
        'tracked_leaf_count':len(state['initial_inventory_state']['leaves'])+len(state['new_leaves']),
        'new_leaf_count':new_count,'tracked_leaf_area':total}
    births._bounded(result);return result


def initialize_leaf_population(*,inputs):
    try:
        births._bounded(inputs);_need(type(inputs) is dict and set(inputs)=={'input_id','initial_inventory'},
                                     'INPUT_HOLD: closed leaf population initialization required')
        leaf._identifier(inputs['input_id']);initialized=inventory.initialize_leaf_inventory(inputs=inputs['initial_inventory'])
        state=normalize_leaf_population_state(state={'model_version':MODEL_VERSION,'time_origin_utc':initialized['state']['time_origin_utc'],
            'at_elapsed_seconds_exact':initialized['state']['at_elapsed_seconds_exact'],'initial_inventory_state':initialized['state'],'new_leaves':[],'birth_inventory':[]})
        return _envelope(state,{'operation':'initialize','inputs':inputs},0)
    except (births.DeclaredLeafBirthHold,inventory.LeafInventoryHold,leaf.RationalLeafAreaHold,RationalMorphologyClockHold) as exc:
        raise LeafPopulationHold(str(exc)) from None


def advance_leaf_population(*,inputs):
    try:
        births._bounded(inputs);_need(type(inputs) is dict and set(inputs)=={'input_id','state','segments','births'},
                                     'INPUT_HOLD: closed leaf population advance required')
        leaf._identifier(inputs['input_id']);state=normalize_leaf_population_state(state=inputs['state']);events=inputs['births']
        _need(type(events) is list and len(state['initial_inventory_state']['leaves'])+len(state['new_leaves'])+len(events)<=512,
              'CAPACITY_HOLD: 1-512 total population leaves required')
        initial=inventory.advance_leaf_inventory(inputs={'input_id':inputs['input_id'],'state':state['initial_inventory_state'],'segments':inputs['segments']})
        new=births.create_declared_leaves(inputs={'input_id':inputs['input_id'],'origin':'synthetic','time_origin_utc':state['time_origin_utc'],
                                                'segments':inputs['segments'],'births':events})
        records=[]
        for item in state['new_leaves']:
            advanced=leaf.advance_rational_leaf_area(inputs={'input_id':inputs['input_id'],'state':item['state'],'segments':inputs['segments']})
            records.append({**deepcopy(item),'state':advanced['state']})
        for event,item in zip(events,new['new_leaves']):
            records.append({'declaration':deepcopy(event),'declaration_sha256':_digest(event),'state':item['state']})
        current=normalize_leaf_population_state(state={**state,'at_elapsed_seconds_exact':deepcopy(initial['state']['at_elapsed_seconds_exact']),
            'initial_inventory_state':initial['state'],'new_leaves':records,
            'birth_inventory':[*deepcopy(state['birth_inventory']),*({'leaf_id':event['leaf_id'],'declaration_sha256':_digest(event)} for event in events)]})
        return _envelope(current,{'operation':'advance','inputs':inputs},len(events))
    except (births.DeclaredLeafBirthHold,inventory.LeafInventoryHold,leaf.RationalLeafAreaHold,RationalMorphologyClockHold) as exc:
        raise LeafPopulationHold(str(exc)) from None
