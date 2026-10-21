"""Validate an explicit leaf population against the original stored stem frame."""
from copy import deepcopy
from hashlib import sha256

from . import crop_leaf_population as population
from .crop_declared_leaf_births import DeclaredLeafBirthHold,_bounded
from .crop_morphology_artifact_io import MorphologyArtifactHold
from .crop_morphology_artifact_reader import _utc
from .crop_rational_morphology_artifact_reader import read_rational_morphology_frame
from .crop_rational_morphology_clock import _seconds


MODEL_VERSION='stored-leaf-stem-attachment-binding-research-v1'


class LeafStemBindingHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:
        raise LeafStemBindingHold(reason)


def bind_leaf_population_to_stored_stem(directory,access,root_sha256,*,index,population_state):
    try:
        state=population.normalize_leaf_population_state(state=population_state)
        stem=read_rational_morphology_frame(directory,access,root_sha256,index=index)
        delta=_utc(stem['at'])-_utc(stem['time_origin_utc']);elapsed=delta.days*86400+delta.seconds
        _need(state['time_origin_utc']==stem['time_origin_utc'] and _seconds(state['at_elapsed_seconds_exact'])==elapsed,
              'TIME_HOLD: leaf population and original stem clock differ')
        parents={item['internode_id']:item for item in stem['internodes']}
        current=[(item['attachment_internode_id'],item['state']) for item in state['initial_inventory_state']['leaves']]
        current.extend((item['declaration']['attachment_internode_id'],item['state']) for item in state['new_leaves'])
        leaves=[]
        for attachment,leaf_state in current:
            clock=leaf_state['clock_state'];birth=_seconds(clock['emerged_elapsed_seconds_exact'])
            _need(attachment in parents,'ATTACHMENT_HOLD: leaf parent absent from original stored frame')
            _need(_seconds(parents[attachment]['emerged_elapsed_seconds_exact'])<=birth<=elapsed,
                  'ATTACHMENT_HOLD: leaf precedes its original parent stem')
            leaves.append({'leaf_id':clock['leaf_id'],'attachment_internode_id':attachment,
                'emerged_elapsed_seconds_exact':deepcopy(clock['emerged_elapsed_seconds_exact']),
                'age_exact':deepcopy(clock['age_exact']),'area':deepcopy(leaf_state['area_state']['area'])})
        result={'model_version':MODEL_VERSION,'scope':'software_research_only','claim_scope':'synthetic_crop_math_only','gates':'not_assessed',
            'population_state_sha256':sha256(_bounded(state)).hexdigest(),'stem_artifact_sha256':root_sha256,
            'stem_result_sha256':stem['result_sha256'],'at':stem['at'],'time_origin_utc':state['time_origin_utc'],
            'at_elapsed_seconds_exact':deepcopy(state['at_elapsed_seconds_exact']),'tracked_leaf_count':len(leaves),
            'tracked_leaf_area':population.inventory._sum(item['area']['value'] for item in leaves),'leaves':leaves,'stem':stem}
        _bounded(result);return result
    except (population.LeafPopulationHold,DeclaredLeafBirthHold,MorphologyArtifactHold,population.inventory.LeafInventoryHold) as exc:
        raise LeafStemBindingHold(str(exc)) from None
