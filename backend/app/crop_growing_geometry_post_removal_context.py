"""Immutable event handoff; growing-geometry-post-removal-context-v1.md."""
from copy import deepcopy
from dataclasses import dataclass,field
from hashlib import sha256
import json
from pathlib import Path

from . import crop_growing_geometry_leaf_removal_point as point

parent=point.resume
VERSION='growing-geometry-post-removal-context-research-v1'
CHECKPOINT_VERSION='growing-geometry-post-removal-snapshot-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_CONTEXT_BYTES=2*1024**2
MAX_CHECKPOINT_BYTES=256*1024
SEED_FIELDS={'last_confirmed','active_original_curve_invariant','original_curve_invariant',
    'original_initial_area_receipts','original_interval_transfers','point_outflows','removed_last_states','segment_integrated_transfers'}
_TOKEN=object()


class PostRemovalContextHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise PostRemovalContextHold(reason)


def _canonical(value):return parent._canonical(value)
def _hash(value):return sha256(_canonical(value)).hexdigest()


def _identity(original):
    return {'model_version':VERSION,'code_sha256':CODE_SHA256,'point_version':point.VERSION,
        'point_code_sha256':point.CODE_SHA256,'parent_identity':parent._identity(original._profiles),
        'state_schema':CHECKPOINT_VERSION}


@dataclass(frozen=True)
class Context:
    _parent:parent.Context=field(repr=False)
    _parent_checkpoint:bytes=field(repr=False)
    _point:bytes=field(repr=False)
    _program:bytes=field(repr=False)
    _seed:bytes=field(repr=False)
    _manifest:bytes=field(repr=False)
    root_sha256:str
    _token:object=field(repr=False)

    @property
    def manifest(self):return json.loads(self._manifest)

    @property
    def active_program(self):return json.loads(self._program)

    @property
    def point_result(self):return json.loads(self._point)


@dataclass(frozen=True)
class Checkpoint:
    _raw:bytes=field(repr=False)
    sha256:str
    context_sha256:str
    _token:object=field(repr=False)

    @property
    def value(self):return json.loads(self._raw)


def _translate(error):
    if isinstance(error,PostRemovalContextHold):return error
    known=(parent.ContinuationRejected,point.LeafRemovalPointHold,parent.short.GrowingGeometryHold,
        parent.short.joint.ExplicitLaiClimateHold,parent.short.numeric.CanopyEnergyHold,
        parent.short.leaf_area.LeafAreaHold,parent.short.expansion.LeafExpansionHold,
        parent.short.leaf_area.LeafAreaChangeHold)
    return PostRemovalContextHold(str(error)if isinstance(error,known)else'CONTEXT_HOLD: invalid post-removal context')


def _zeros():return {name:parent.short.numeric._q(0.0,unit)for name,unit in parent.short.FLUX_UNITS.items()}


def _context(context):
    try:
        _need(type(context)is Context and context._token is _TOKEN,'CONTEXT_HOLD: prepared post-removal context required')
        parts={name:getattr(context,'_'+name)for name in ('parent_checkpoint','point','program','seed')}
        _need(all(type(v)is bytes for v in (*parts.values(),context._manifest))
            and sum(map(len,(*parts.values(),context._manifest)))<=MAX_CONTEXT_BYTES,
            'CAPACITY_HOLD: bounded immutable context bytes required')
        original,old_seed,old_manifest=parent._context(context._parent)
        m=context.manifest
        _need(_canonical(m)==context._manifest and _hash(m)==context.root_sha256
            and m['identity']==_identity(context._parent),'CONTEXT_HOLD: changed identity/code/profile/environment')
        _need(m['parent_context_sha256']==context._parent.root_sha256,'CONTEXT_HOLD: different original context')
        values={}
        for name,raw in parts.items():
            _need(sha256(raw).hexdigest()==m[name+'_sha256'],'CONTEXT_HOLD: changed '+name+' bytes')
            values[name]=json.loads(raw)
            _need(_canonical(values[name])==raw,'CONTEXT_HOLD: noncanonical context part')
        result=values['point'];cp=values['parent_checkpoint'];p=values['program'];seed=values['seed']
        _need(set(seed)==SEED_FIELDS and set(m)=={'identity','parent_context_sha256','original_request_sha256',
            'original_program_sha256','original_seed_sha256','point_input_sha256','point_calculation_sha256',
            *(name+'_sha256'for name in parts),'at_elapsed_seconds_exact','original_leaf_indices','numerical','state_layout'},
            'CONTEXT_HOLD: closed manifest and captured seed required')
        _need(all(m['original_'+name+'_sha256']==old_manifest[name+'_sha256']for name in ('request','program','seed'))
            and m['point_input_sha256']==result['input_sha256']==_hash(result['inputs'])
            and result['original_program_sha256']==old_manifest['program_sha256']
            and result['original_seed_sha256']==old_manifest['seed_sha256']
            and result['parent_identity']==old_manifest['identity'],'CONTEXT_HOLD: changed original source bindings')
        _need(result['model_version']==point.VERSION and result['code_sha256']==point.CODE_SHA256
            and result['context_sha256']==context._parent.root_sha256
            and result['checkpoint_sha256']==m['parent_checkpoint_sha256']
            and result['calculation_sha256']==m['point_calculation_sha256']
            and _hash({k:v for k,v in result.items()if k!='calculation_sha256'})==result['calculation_sha256'],
            'CONTEXT_HOLD: changed original point identity')
        keep=result['after']['original_leaf_indices']
        _need(type(keep)is list and 1<=len(keep)<len(original['leaves'])
            and all(type(i)is int and 0<=i<len(original['leaves'])for i in keep)
            and keep==sorted(set(keep)),'CONTEXT_HOLD: original ordered leaf mapping required')
        expected_program={**original,'leaves':[original['leaves'][i]for i in keep]}
        _need(p==expected_program and result['after']['leaf_ids']==[original['leaves'][i]['leaf_id']for i in keep],
            'CONTEXT_HOLD: changed original leaf program or mapping')
        sample=seed['last_confirmed'];old_sample=cp['last_confirmed']
        _need(cp['context_sha256']==context._parent.root_sha256 and result['before']==old_sample
            and sample['step_index']==old_sample['step_index']and sample['elapsed_seconds']==old_sample['elapsed_seconds']
            and sample['state']==result['after']['state'],'CONTEXT_HOLD: changed event coordinate or current state')
        for name,source in (('leaf_area_index','leaf_area_index'),('canopy_capacity','capacity'),('canopy_temperature','canopy_temperature')):
            _need(sample['derived'][name]==result['after'][source],'CONTEXT_HOLD: changed current derived quantity')
        _need(seed['original_curve_invariant']==old_seed['evaluation']['curve_residuals']
            and seed['active_original_curve_invariant']==[old_seed['evaluation']['curve_residuals'][i]for i in keep]
            and seed['original_initial_area_receipts']==old_seed['initial_area_receipts'],
            'CONTEXT_HOLD: original area anchors and receipts required')
        _need(all(sample[name]==[old_sample[name][i]for i in keep]for name in ('curve_residuals','curve_invariant_changes')),
            'CONTEXT_HOLD: current area was reset')
        _need(seed['original_interval_transfers']==cp['integrated_transfers']==result['original_interval_transfers']
            and seed['point_outflows']==result['point_outflows']and seed['removed_last_states']==result['removed_last_states']
            and seed['segment_integrated_transfers']==_zeros(),'CONTEXT_HOLD: original/point/segment ledgers differ')
        numerical={**old_manifest['numerical'],'event_global_step_index':cp['step_index'],
            'remaining_steps':old_manifest['numerical']['step_count']-cp['step_index']}
        layout={**old_manifest['state_layout'],'leaf_ids':result['after']['leaf_ids']}
        _need(m['numerical']==numerical and m['state_layout']==layout
            and m['original_leaf_indices']==keep and m['at_elapsed_seconds_exact']==result['at_elapsed_seconds_exact'],
            'CONTEXT_HOLD: changed numerical scope/layout/time')
        return p,seed,m
    except(ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError)as error:
        raise _translate(error)from None


def prepare_context(*,parent_context,raw_parent_checkpoint,expected_parent_sha256,inputs):
    try:
        result=point.apply_removals(context=parent_context,raw_checkpoint=raw_parent_checkpoint,
            expected_sha256=expected_parent_sha256,inputs=inputs)
        original,old_seed,old_manifest=parent._context(parent_context)
        cp=json.loads(raw_parent_checkpoint);keep=result['after']['original_leaf_indices']
        p={**original,'leaves':[original['leaves'][i]for i in keep]};state=tuple(result['after']['state'])
        _,evaluated=parent.short._evaluate(p,state,parent._profiles(parent_context))
        d0=[old_seed['evaluation']['curve_residuals'][i]for i in keep]
        sample=parent.short._sample(cp['step_index'],old_manifest['numerical']['step_seconds'],state,evaluated,d0)
        seed={'last_confirmed':sample,'active_original_curve_invariant':deepcopy(d0),
            'original_curve_invariant':deepcopy(old_seed['evaluation']['curve_residuals']),
            'original_initial_area_receipts':deepcopy(old_seed['initial_area_receipts']),
            'original_interval_transfers':deepcopy(cp['integrated_transfers']),
            'point_outflows':deepcopy(result['point_outflows']),'removed_last_states':deepcopy(result['removed_last_states']),
            'segment_integrated_transfers':_zeros()}
        parts={'parent_checkpoint':raw_parent_checkpoint,'point':_canonical(result),'program':_canonical(p),'seed':_canonical(seed)}
        manifest={'identity':_identity(parent_context),'parent_context_sha256':parent_context.root_sha256,
            'original_request_sha256':old_manifest['request_sha256'],'original_program_sha256':old_manifest['program_sha256'],
            'original_seed_sha256':old_manifest['seed_sha256'],'point_input_sha256':result['input_sha256'],
            'point_calculation_sha256':result['calculation_sha256'],
            **{name+'_sha256':sha256(raw).hexdigest()for name,raw in parts.items()},
            'at_elapsed_seconds_exact':deepcopy(result['at_elapsed_seconds_exact']),'original_leaf_indices':keep,
            'numerical':{**old_manifest['numerical'],'event_global_step_index':cp['step_index'],
                'remaining_steps':old_manifest['numerical']['step_count']-cp['step_index']},
            'state_layout':{**old_manifest['state_layout'],'leaf_ids':result['after']['leaf_ids']}}
        raw_manifest=_canonical(manifest)
        current=Context(parent_context,parts['parent_checkpoint'],parts['point'],parts['program'],parts['seed'],
            raw_manifest,sha256(raw_manifest).hexdigest(),_TOKEN)
        _,captured,m=_context(current);_initial_bytes(current,captured,m)
        return current
    except(ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError)as error:
        raise _translate(error)from None


def _initial_bytes(context,seed,manifest):
    value={'version':CHECKPOINT_VERSION,'context_sha256':context.root_sha256,
        'phase':'after_removal_before_next_step','segment_step_index':0,
        'original_global_step_index':manifest['numerical']['event_global_step_index'],
        'at_elapsed_seconds_exact':deepcopy(manifest['at_elapsed_seconds_exact']),**deepcopy(seed),
        'scope':'software_research_only','claim_scope':'synthetic_post_removal_context_only','G0_G4':'not_assessed'}
    raw=_canonical(value);_need(len(raw)<=MAX_CHECKPOINT_BYTES,'CAPACITY_HOLD: 256KiB checkpoint required');return raw


def snapshot(context):
    _,seed,m=_context(context);raw=_initial_bytes(context,seed,m)
    return Checkpoint(raw,sha256(raw).hexdigest(),context.root_sha256,_TOKEN)


def checkpoint_bytes(context,checkpoint):
    _,seed,m=_context(context)
    _need(type(checkpoint)is Checkpoint and checkpoint._token is _TOKEN
        and checkpoint.context_sha256==context.root_sha256 and type(checkpoint._raw)is bytes
        and len(checkpoint._raw)<=MAX_CHECKPOINT_BYTES and sha256(checkpoint._raw).hexdigest()==checkpoint.sha256
        and checkpoint._raw==_initial_bytes(context,seed,m),'CHECKPOINT_HOLD: original immutable snapshot required')
    return checkpoint._raw


def restore_checkpoint(context,raw_bytes,*,expected_sha256):
    _,seed,m=_context(context)
    _need(type(raw_bytes)is bytes and 0<len(raw_bytes)<=MAX_CHECKPOINT_BYTES and parent._digest(expected_sha256)
        and sha256(raw_bytes).hexdigest()==expected_sha256,'CHECKPOINT_HOLD: trusted original bytes/digest required')
    _need(raw_bytes==_initial_bytes(context,seed,m),'CHECKPOINT_HOLD: changed event snapshot')
    return Checkpoint(raw_bytes,expected_sha256,context.root_sha256,_TOKEN)
