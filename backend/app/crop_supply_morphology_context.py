"""Genuine immutable post-point Context and seed checkpoint, without grid advance."""
from copy import deepcopy
from dataclasses import dataclass,field
from fractions import Fraction
from functools import wraps
from hashlib import sha256
from pathlib import Path
import json

from . import crop_supply_morphology_context_proofs as proofs

point=proofs.point
resume=point.resume
source=point.source
F,Q,X=resume.F,resume.Q,resume.X
VERSION='supply-morphology-post-point-context-research-v1'
CONTEXT_VERSION='supply-morphology-post-point-context-v1'
CHECKPOINT_VERSION='supply-morphology-post-point-seed-checkpoint-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES=2*1024**2
MAX_CP=512*1024
_TOKEN=object()


class SupplyContextHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise SupplyContextHold(reason)


def _public(fn):
    @wraps(fn)
    def checked(*args,**kw):
        try:return fn(*args,**kw)
        except SupplyContextHold:raise
        except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:raise SupplyContextHold(str(error))from None
    return checked


def _pins():
    pins={**point._pins(),'backend/app/crop_supply_morphology_context.py':CODE_SHA256,'backend/app/crop_supply_morphology_context_proofs.py':proofs.CODE_SHA256}
    root=Path(__file__).resolve().parents[2]
    _need(all(sha256((root/name).read_bytes()).hexdigest()==v for name,v in pins.items()),'CODE_HOLD: original newborn owner/proof code required');return pins


def _canonical(value,maximum=MAX_BYTES):return resume._canonical(value,maximum)
def _hash(value):return sha256(_canonical(value)).hexdigest()


@dataclass(frozen=True,eq=False)
class Context:
    _origin:resume.Context=field(repr=False)
    _point:bytes=field(repr=False)
    _raw:bytes=field(repr=False)
    root_sha256:str
    _token:object=field(repr=False)
    @property
    def value(self):return json.loads(self._raw)


@dataclass(frozen=True)
class Checkpoint:
    _raw:bytes=field(repr=False)
    sha256:str
    context_sha256:str
    _token:object=field(repr=False)
    @property
    def value(self):return json.loads(self._raw)


def _prefix(previous,sample,event_sequence,phase,point_sha):
    return _hash({'previous_output_prefix_sha256':previous,'sample_sha256':_hash(sample),'event_sequence':event_sequence,'phase':phase,'material_point_sha256':point_sha,'version':VERSION})


def _derive(origin,result,point_sha):
    data=proofs.validate(origin,result);before=result['before_candidate'];cp=before['source_prefix'];event=result['source_event']
    timeline=data['source_data']['point']['before_candidate']['source_root_certificate']['source_timeline'];threshold=X(event['threshold_exact']);spacing=X(timeline['phyllochron_exact']);age=X(before['dense_candidate']['shoot_age_exact'])
    _need(spacing>0 and threshold<=age<threshold+spacing,'SCHEDULE_HOLD: exactly first pending source event required')
    schedule={'consumed_event_id':event['source_event_id'],'consumed_sequence':event['sequence'],'consumed_threshold_exact':deepcopy(event['threshold_exact']),
        'next_sequence':event['sequence']+1,'next_threshold_exact':Q(threshold+spacing,'degC_day'),'age_exact':deepcopy(before['dense_candidate']['shoot_age_exact']),
        'source_schedule_id':timeline['schedule_id'],'policy':'compatible_first_source_event_once_no_threshold_snap','age_basis':'numerical_air_integral_not_physical_emergence'}
    numerical=deepcopy(data['source_data']['captured']['original_numerical']);dt=F(numerical['step_seconds']);count=numerical['step_count'];at=X(result['at']['elapsed_seconds_exact']);completed=int(at//dt)
    _need(0<=completed<=count and at<=dt*count,'HORIZON_HOLD: original grid and horizon required')
    next_at=dt*(completed+1)if completed<count else None;program=result['after_program'];organs=result['after_organs'];units=resume.books.flux_units(program,organs)
    _need(len(program['leaves'])<=512 and len(program['stem_root_compartments'])<=512 and (count-completed+1)*(len(result['after_state'])+len(units)+2*(len(organs['leaves'])+len(organs['internodes']))+8)<=32768,
        'CAPACITY_HOLD: original inventory/scalar limits required')
    physical=result['post_point_lifetime_transfers_exact_preview'];old_geometry=before['dense_candidate']['pending_branch_transfers_exact']
    lifetime={k:deepcopy(physical[k])if k in physical else deepcopy(old_geometry[k])if k in old_geometry else Q(Fraction(0),unit)for k,unit in units.items()}
    sample={'at':deepcopy(result['at']),'state':deepcopy(result['after_state']),'derived':deepcopy(result['after_derived'])}
    dense={k:deepcopy(before['dense_candidate'][k])for k in ['at','state','derived']};sequence=cp['event_sequence']+1
    prefix_before=_prefix(cp['output_prefix_sha256'],dense,cp['event_sequence'],'fractional_before_compatible_material_point',point_sha)
    prefix=_prefix(prefix_before,sample,sequence,'fractional_after_compatible_material_point',point_sha)
    seed={'program':deepcopy(program),'organs':deepcopy(organs),'costs':deepcopy(result['after_costs']),'state_layout':deepcopy(result['after_state_layout']),
        'initial_sample':sample,'birth_bases':deepcopy(result['after_birth_baselines']),'lifetime_transfers_exact':lifetime,'point_totals_exact':deepcopy(result['post_point_point_totals_exact_preview']),
        'global_ledgers':deepcopy(result['post_point_global_ledgers_preview']),'schedule':schedule,'event_sequence':sequence,'output_cursor':cp['output_cursor']+2,'output_prefix_sha256':prefix,
        'before_material_prefix_sha256':prefix_before,'source_output_prefix_sha256':cp['output_prefix_sha256'],'original_numerical':numerical,
        'original_grid_position':{'completed_grid_index':completed,'at_original_grid':at==dt*completed,'next_grid_index':completed+1 if next_at is not None else None,
            'next_grid_elapsed_seconds_exact':Q(next_at,'s')if next_at is not None else None,'remaining_to_next_grid_seconds_exact':Q(next_at-at if next_at is not None else Fraction(0),'s')},
        'transfer_origins':{'physical':'original_root','geometry':'original_supply_law_branch_excluding_material_seed_classification'},'redistribution_authorized':result['redistribution_authorized']}
    descriptor={'version':CONTEXT_VERSION,'model_version':VERSION,'source_code_sha256':_pins(),'origin_context_sha256':origin.root_sha256,'point_sha256':point_sha,
        'seed':seed,'scope':'software_research_only','G0_G4':'not_assessed'}
    return descriptor,data


def _fence(context,data):
    _need(type(context)is Context and context._token is _TOKEN and _hash(data['descriptor'])==context.root_sha256
        and _canonical(data['descriptor'])==context._raw and sha256(context._point).hexdigest()==data['descriptor']['point_sha256']
        and _canonical(data['point'])==context._point and data['descriptor']['source_code_sha256']==_pins()
        and context._origin.root_sha256==data['descriptor']['origin_context_sha256'],'CONTEXT_HOLD: unchanged genuine owner/source/proof required')
    resume._fence(context._origin,data['origin_data'])
    seed=data['descriptor']['seed']
    _need(data['seed']==seed and all(data[k]==seed[k]for k in ['program','organs','costs','state_layout','birth_bases']),'SOURCE_HOLD: unchanged owned seed projection required')
    profiles=source.stock.parent._profiles(context._origin._source._source._root)
    _need(set(profiles)==set(data['profiles'])and all(type(v)is type(data['profiles'][k])and vars(v)==vars(data['profiles'][k])for k,v in profiles.items()),'PROFILE_HOLD: actual complete current profiles required')


def _context(context):
    _need(type(context)is Context and context._token is _TOKEN and type(context._raw)is bytes and type(context._point)is bytes
        and 0<len(context._raw)+len(context._point)<=MAX_BYTES,'CONTEXT_HOLD: genuine bounded newborn Context/proof required')
    h=resume._parse(context._raw,context.root_sha256);result=resume._parse(context._point,h['point_sha256']);expected,origin_data=_derive(context._origin,result,h['point_sha256'])
    _need(h==expected,'CONTEXT_HOLD: exact captured point/source-derived seed required')
    data={'descriptor':h,'point':result,'origin_data':origin_data,'seed':h['seed'],'profiles':origin_data['profiles'],**{k:h['seed'][k]for k in ['program','organs','costs','state_layout','birth_bases']}}
    _fence(context,data);return data


def _issue(origin,result):
    raw_point=_canonical(result);descriptor,data=_derive(origin,result,sha256(raw_point).hexdigest());raw=_canonical(descriptor)
    _need(len(raw)+len(raw_point)<=MAX_BYTES,'CAPACITY_HOLD: bounded complete Context/proof required')
    context=Context(origin,raw_point,raw,sha256(raw).hexdigest(),_TOKEN);_context(context);return context


@_public
def prepare_context(origin,raw_checkpoint,*,expected_sha256,time_tolerance_seconds_exact,inputs):
    raw_inputs=_canonical(inputs,point.MAX_INPUT_BYTES);tolerance=deepcopy(time_tolerance_seconds_exact)
    result=point.apply_fractional_material_point(origin,raw_checkpoint,expected_sha256=expected_sha256,time_tolerance_seconds_exact=time_tolerance_seconds_exact,inputs=inputs)
    context=_issue(origin,result)
    _need(_canonical(inputs,point.MAX_INPUT_BYTES)==raw_inputs and time_tolerance_seconds_exact==tolerance,
        'INPUT_HOLD: caller inputs changed after material capture')
    return context


@_public
def restore_context(origin,raw_bytes,*,expected_sha256,point_bytes):
    context=Context(origin,point_bytes,raw_bytes,expected_sha256,_TOKEN);_context(context);return context


@_public
def context_bytes(context):_context(context);return context._raw


@_public
def point_bytes(context):_context(context);return context._point


def _seed_checkpoint(context,data):
    s=data['seed'];units=resume.books.flux_units(s['program'],s['organs'])
    return {'version':CHECKPOINT_VERSION,'model_version':VERSION,'source_code_sha256':_pins(),'context_sha256':context.root_sha256,
        'origin_context_sha256':context._origin.root_sha256,'point_sha256':data['descriptor']['point_sha256'],'at':deepcopy(s['initial_sample']['at']),
        'phase':'fractional_after_compatible_material_point','branch_steps':0,'grid_index':s['original_grid_position']['completed_grid_index'],
        'event_sequence':s['event_sequence'],'schedule':deepcopy(s['schedule']),'last_confirmed':deepcopy(s['initial_sample']),
        'branch_integrated_transfers':{k:resume.numeric._q(0.,unit)for k,unit in units.items()},'lifetime_transfers_exact':deepcopy(s['lifetime_transfers_exact']),
        'point_totals_exact':deepcopy(s['point_totals_exact']),'branch_ledgers':{k:{'residual_exact':Q(Fraction(0),row['residual_exact']['unit']),
            'budget_exact':Q(Fraction(0),row['budget_exact']['unit'])}for k,row in s['global_ledgers'].items()},'global_ledgers':deepcopy(s['global_ledgers']),
        'output_cursor':s['output_cursor'],'output_prefix_sha256':s['output_prefix_sha256'],'transfer_origins':deepcopy(s['transfer_origins']),
        'scope':'software_research_only','G0_G4':'not_assessed','redistribution_authorized':s['redistribution_authorized']}


def _seal(context,data,payload):
    raw=_canonical(payload,MAX_CP);_fence(context,data);return Checkpoint(raw,sha256(raw).hexdigest(),context.root_sha256,_TOKEN)


@_public
def start(context):
    data=_context(context);return _seal(context,data,_seed_checkpoint(context,data))


@_public
def checkpoint_bytes(context,checkpoint):
    data=_context(context)
    _need(type(checkpoint)is Checkpoint and checkpoint._token is _TOKEN and checkpoint.context_sha256==context.root_sha256,'CHECKPOINT_HOLD: genuine owned seed CP required')
    payload=resume._parse(checkpoint._raw,checkpoint.sha256,MAX_CP)
    _need(payload==_seed_checkpoint(context,data),'CHECKPOINT_HOLD: unchanged actual material seed CP required');_fence(context,data);return checkpoint._raw


@_public
def restore_checkpoint(context,raw_bytes,*,expected_sha256):
    data=_context(context);payload=resume._parse(raw_bytes,expected_sha256,MAX_CP)
    _need(payload==_seed_checkpoint(context,data),'CHECKPOINT_HOLD: original material seed CP required')
    state=payload['last_confirmed']['state'];snapshot=_canonical({'program':data['program'],'state':state,'organs':data['organs'],'costs':data['costs']})
    _fence(context,data);rhs=point.core.stage.evaluate(data['program'],state,data['organs'],data['costs'],data['profiles'])
    _need(snapshot==_canonical({'program':data['program'],'state':state,'organs':data['organs'],'costs':data['costs']})and rhs==data['point']['after_stage'],
        'CHECKPOINT_HOLD: one actual current new-stage validation required')
    _fence(context,data);return _seal(context,data,payload)
