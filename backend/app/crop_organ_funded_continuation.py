"""Both material points and current-state resume; crop-organ-funded-continuation-v1.md."""
from copy import deepcopy
from dataclasses import dataclass,field
from fractions import Fraction
from functools import wraps
from hashlib import sha256
import json
from math import isfinite,ulp
from pathlib import Path

from . import crop_stem_root_funded_leaf_point as leaf
from . import crop_leaf_funded_birth_continuation as legacy

stem=leaf.stem
parent=leaf.resume
short=leaf.short
numeric=leaf.numeric
arithmetic=leaf.arithmetic
POINTS={'leaf':leaf,'internode':stem}
SCHEMAS={'leaf':'stem-root-funded-leaf-point-input-v1','internode':'stem-root-funded-internode-point-input-v1'}
VERSION='individual-organ-funded-continuation-research-v1'
CONTEXT_VERSION='funded-individual-organ-context-v1'
CHECKPOINT_VERSION='funded-individual-organ-checkpoint-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES=2*1024**2
MAX_CHECKPOINT_BYTES=parent.MAX_CHECKPOINT_BYTES
_TOKEN=object()
FLOW_UNITS={**dict.fromkeys(('structural_carbon','growth_respiration','buffer_debit'),leaf.MASS),
            'capacity_in':numeric.CAPACITY,'sensible_in':numeric.ENERGY}
ROOT_CP_FIELDS={'version','context_sha256','step_index','output_cursor','output_prefix_sha256','last_confirmed',
                'integrated_transfers','balance_residuals','balance_budgets'}
CP_FIELDS=ROOT_CP_FIELDS|{'segment_step_index','event_sequence','phase','at_elapsed_seconds_exact',
    'segment_integrated_transfers','point_history_sha256','point_totals','global_balance_residuals',
    'global_balance_budgets','scope','G0_G4','time_kind','redistribution_authorized'}


class OrganContinuationHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise OrganContinuationHold(reason)


def _public(fn):
    @wraps(fn)
    def checked(*args,**kwargs):
        try:return fn(*args,**kwargs)
        except OrganContinuationHold:raise
        except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:
            raise OrganContinuationHold(str(error))from None
    return checked


def _canonical(v):
    raw=parent._canonical(v);_need(len(raw)<=MAX_BYTES,'CAPACITY_HOLD: 2MiB organ context/response required');return raw


def _hash(v):return sha256(_canonical(v)).hexdigest()


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256,'CODE_HOLD: original mixed organ continuation required')
    leaf._fence();legacy._fence()


def _pins():
    return {**leaf._pins(),'backend/app/crop_leaf_funded_birth_continuation.py':legacy.CODE_SHA256,
            'backend/app/crop_organ_funded_continuation.py':CODE_SHA256}


def _exact(index,dt):
    value=Fraction.from_float(dt)*index
    return {'numerator':str(value.numerator),'denominator':str(value.denominator),'unit':'s'}


def _identity(root):
    _fence()
    for profile in root._profiles:
        _need(sha256(profile.raw_bytes).hexdigest()==profile.sha256 and dict(profile.values)==
              {k:float(v['value'])for k,v in json.loads(profile.raw_bytes)['parameters'].items()},'PROFILE_HOLD: original profile bytes/values required')
    return {'version':VERSION,'code_sha256':CODE_SHA256,'source_code_sha256':_pins(),'root_identity':parent._identity(root._profiles)}


@dataclass(frozen=True)
class Context:
    _root:parent.Context=field(repr=False)
    _directories:tuple=field(repr=False)
    _selection:bytes=field(repr=False)
    _program:bytes=field(repr=False)
    _seed:bytes=field(repr=False)
    _history:bytes=field(repr=False)
    _manifest:bytes=field(repr=False)
    root_sha256:str
    _token:object=field(repr=False)

    @property
    def manifest(self):return json.loads(self._manifest)
    @property
    def program(self):return json.loads(self._program)
    @property
    def point_history(self):return json.loads(self._history)


def _bind(root,directories,selection):
    arithmetic._closed(selection,{'crop_root_sha256','stem_root_sha256','stem_start_index','binding_declaration'})
    cd,sd,access=directories
    return leaf.binding.bind_initial_stem_carbon(root,cd,sd,access,crop_root_sha256=selection['crop_root_sha256'],
        stem_root_sha256=selection['stem_root_sha256'],stem_start_index=selection['stem_start_index'],declaration=selection['binding_declaration'])


def _source(context):
    _need(_identity(context._root)==context.manifest['identity'],'PROFILE_HOLD: original current code/profile/environment required')
    binding=_bind(context._root,context._directories,json.loads(context._selection))
    _need(_hash(binding)==context.manifest['initial_binding_sha256'],'SOURCE_HOLD: original current initial binding required')
    return binding


def _root_bases(p,seed):
    n=len(p['leaves']);y=seed['state']
    return {'leaf':[{'leaf_id':row['leaf_id'],'step_index':0,'thermal_age':y[106+i],
        'carbon':y[106+2*n+i],'air_temperature_integral':0.}for i,row in enumerate(p['leaves'])],
        'stem_root':[{'compartment_id':row['compartment_id'],'kind':row['kind'],'step_index':0,
            'carbon':y[106+3*n+i]}for i,row in enumerate(p['stem_root_compartments'])]}


def _input(v,kind,initial_sha,floor,dt,*,context_sha=None,checkpoint_sha=None,at=None):
    _need(type(kind)is str and kind in POINTS,'SCOPE_HOLD: explicit leaf/internode point kind required')
    arithmetic._closed(v,leaf.FIELDS)
    _need(v['schema_version']==SCHEMAS[kind]and v['origin']=='synthetic'and v['policy']==POINTS[kind].POLICY,
          'POLICY_HOLD: original point schema and policy required')
    for name in ('input_id','reviewer'):short.stock.part._id(v[name])
    for name in ('context_sha256','checkpoint_sha256','initial_binding_sha256'):_need(parent._digest(v[name]),'HASH_HOLD: original point digest required')
    _need(v['initial_binding_sha256']==initial_sha,'SOURCE_HOLD: original initial binding digest required')
    if context_sha is not None:_need(v['context_sha256']==context_sha and v['checkpoint_sha256']==checkpoint_sha,'HASH_HOLD: actual current context/CP required')
    seconds=arithmetic.clock._seconds(v['at_elapsed_seconds_exact']);step=seconds/Fraction.from_float(dt)
    _need(step.denominator==1 and (at is None or seconds==at),'TIME_HOLD: original-grid exact point coordinate required')
    _need(arithmetic._quantity(v['model_floor_area'],'m2_floor')==floor['value'],'BASIS_HOLD: original model floor required')
    stem._rights(v['rights']);_need(type(v['events'])is list and v['events'],'EVENT_HOLD: explicit nonempty point events required')
    return int(step)


def _stem_declaration(item,declared):
    arithmetic._closed(item,{'compartment_id','kind',*short.STOCK_FIELDS});arithmetic._closed(declared,set(item))
    short.stock.part._id(item['compartment_id'])
    _need(item['kind']==declared['kind']=='internode'and item['compartment_id']==declared['compartment_id'],'CONTEXT_HOLD: original new internode required')
    for name,unit in short.STOCK_FIELDS.items():
        legacy._captured_quantity(item[name],unit)
        _need(item[name]['value']==arithmetic._quantity(declared[name],unit),'CONTEXT_HOLD: original compartment declaration required')
    _need(item['initial_carbon']['value']>0 and item['sink_weight']['value']>=0 and item['carbon_removal']['value']>=0,'CONTEXT_HOLD: valid captured internode required')


def _receipt(receipt,event,item,kind):
    if kind=='internode':
        _need(receipt=={'event_id':event['event_id'],'parent_internode_id':event['parent_internode_id'],
              'compartment_id':item['compartment_id'],'initial_carbon':item['initial_carbon']},'CONTEXT_HOLD: original internode receipt required');return
    arithmetic._closed(receipt,{'event_id','parent_internode_id','initialization','capacity_in','sensible_in'})
    _need(receipt['event_id']==event['event_id']and receipt['parent_internode_id']==event['parent_internode_id'],'CONTEXT_HOLD: original leaf receipt parent required')
    legacy._captured_quantity(receipt['capacity_in'],numeric.CAPACITY);legacy._captured_quantity(receipt['sensible_in'],numeric.ENERGY)
    init=receipt['initialization'];state=init['state'];area=arithmetic.resume.short.old.leaf_area
    arithmetic._closed(state,{'model_version','origin','thermal_age_basis','normalization','leaf_id','curve','curve_sha256','age_exact','area','anchor'})
    anchor=state['anchor'];arithmetic._closed(anchor,{'leaf_id','age_exact','curve_sha256','requested_area','canonical_area'})
    _need(state['model_version']==area.MODEL_VERSION and state['origin']=='synthetic'and state['normalization']==area.NORMALIZATION
        and state['thermal_age_basis']=='since_leaf_emergence'and state['leaf_id']==anchor['leaf_id']==item['leaf_id']
        and state['curve']==item['curve']and state['curve_sha256']==anchor['curve_sha256']==area._digest({'rate_model_version':short.old.expansion.MODEL_VERSION,'curve':item['curve']})
        and state['age_exact']==anchor['age_exact']=={'numerator':'0','denominator':'1','unit':'degC_day'},'CONTEXT_HOLD: original new leaf clock/curve required')
    for row in [state['area'],anchor['requested_area'],anchor['canonical_area']]:legacy._captured_quantity(row,'m2')
    _need(state['area']==anchor['canonical_area']and state['area']['value']>0 and anchor['requested_area']==item['initial_area']
        and init==area._envelope(state,{'operation':'initialize','input_id':item['leaf_id'],'state':state}),'CONTEXT_HOLD: original canonical initialization receipt required')


def _history_units(record):
    arithmetic._closed(record['point_flows'],FLOW_UNITS)
    for name,unit in FLOW_UNITS.items():legacy._captured_quantity(record['point_flows'][name],unit)
    _need(all(record['point_flows'][name]['value']>0 for name in ('structural_carbon','growth_respiration','buffer_debit')),'CONTEXT_HOLD: positive recorded material point required')
    kind=record['kind'];count=len(record['new_items']);leaf_kind=kind=='leaf'
    _need((record['point_flows']['capacity_in']['value']>0 if leaf_kind else record['point_flows']['capacity_in']['value']==record['point_flows']['sensible_in']['value']==0),
          'CONTEXT_HOLD: original point heat/capacity scope required')
    units=dict.fromkeys(('buffer','new_stock','whole_carbon'),leaf.MASS)
    if leaf_kind:units.update(sensible=numeric.ENERGY,capacity=numeric.CAPACITY)
    units.update({('new_leaf_'if leaf_kind else'new_internode_')+str(i):leaf.MASS for i in range(count)})
    arithmetic._closed(record['balances'],units)
    for name,unit in units.items():
        row=record['balances'][name];arithmetic._closed(row,{'residual','budget'})
        for quantity in row.values():legacy._captured_quantity(quantity,unit)
        _need(row['budget']['value']>=0 and abs(row['residual']['value'])<=row['budget']['value'],'CONTEXT_HOLD: recorded point budget required')
    _need(type(record['air_temperature_integral'])is float and isfinite(record['air_temperature_integral']),'CONTEXT_HOLD: recorded air integral required')


def _transition(before_program,program,before,after,record):
    fields={'step_index','elapsed_seconds','state','derived','curve_residuals','curve_invariant_changes'}
    arithmetic._closed(before,fields);arithmetic._closed(after,fields)
    n0=len(before_program['leaves']);n=len(program['leaves']);old=before['state'];state=after['state']
    _need(type(old)is list and len(old)==106+3*n0+len(before_program['stem_root_compartments'])
        and all(type(v)is float and isfinite(v)for v in old),'CONTEXT_HOLD: finite original pre-point state required')
    flow=record['point_flows'];buffer=arithmetic._rounded(Fraction.from_float(old[0])-Fraction.from_float(flow['buffer_debit']['value']))
    _need(buffer>0 and buffer!=old[0],'CONTEXT_HOLD: captured positive funded buffer required')
    masses=[item['initial_carbon']['value']for item in record['new_items']]
    if record['kind']=='internode':expected=[buffer,*old[1:],*masses]
    else:
        base=list(old[:106]);base[0]=buffer
        base[103]=arithmetic._rounded(Fraction.from_float(old[103])+Fraction.from_float(flow['sensible_in']['value']))
        areas=[item['initialization']['state']['area']['value']for item in record['birth_receipts']]
        expected=[*base,*old[106:106+n0],*([0.]*len(masses)),*old[106+n0:106+2*n0],*areas,
            *old[106+2*n0:106+3*n0],*masses,*old[106+3*n0:]]
    _need(_canonical(state)==_canonical(expected),'CONTEXT_HOLD: captured point must preserve original state and declared new inventory')
    for key in ('curve_residuals','curve_invariant_changes'):
        _need(len(after[key])==n and after[key]==[*before[key],*(numeric._q(0.,'m2')for _ in range(n-n0))],
            'CONTEXT_HOLD: captured point must preserve original leaf D0')


def _capture(root,directories,selection,initial_sha,result,kind,anchors,bases,history):
    p=result['after_program'];before=result['before_checkpoint'];count=len(result['inputs']['events']);key='leaves'if kind=='leaf'else'stem_root_compartments'
    record={'kind':kind,'point_model_version':result['model_version'],'inputs':deepcopy(result['inputs']),
        'calculation_sha256':result['calculation_sha256'],'after_sample_sha256':_hash(result['after_sample']),
        'new_items':deepcopy(p[key][-count:]),'birth_receipts':deepcopy(result['birth_receipts']),
        'point_flows':{name:deepcopy(result['point_flows'].get(name,numeric._q(0.,unit)))for name,unit in FLOW_UNITS.items()},
        'balances':deepcopy(result['balances']),'air_temperature_integral':before['integrated_transfers']['indoor_air_temperature_time']['value']}
    history=[*deepcopy(history),record];bases=deepcopy(bases)
    for item in record['new_items']:
        if kind=='leaf':bases['leaf'].append({'leaf_id':item['leaf_id'],'step_index':before['step_index'],'thermal_age':0.,
            'carbon':item['initial_carbon']['value'],'air_temperature_integral':record['air_temperature_integral']})
        else:bases['stem_root'].append({'compartment_id':item['compartment_id'],'kind':'internode','step_index':before['step_index'],'carbon':item['initial_carbon']['value']})
    seed={'last_confirmed':deepcopy(result['after_sample']),'before_checkpoint':deepcopy(before),
        'anchors':deepcopy(result.get('after_anchors',anchors)),'birth_bases':bases,
        'base_transfers':{name:deepcopy(before['integrated_transfers'].get(name,numeric._q(0.,unit)))for name,unit in short._flux_units(p).items()}}
    parts={'program':_canonical(p),'seed':_canonical(seed),'history':_canonical(history),'selection':_canonical(selection)}
    manifest={'version':CONTEXT_VERSION,'identity':_identity(root),'root_context_sha256':root.root_sha256,
        'redistribution_authorized':result['redistribution_authorized'],
        'initial_binding_sha256':initial_sha,'parent_context_sha256':result['context_sha256'],'parent_checkpoint_sha256':result['checkpoint_sha256'],
        **{name+'_sha256':sha256(raw).hexdigest()for name,raw in parts.items()},
        'numerical':{**root.manifest['numerical'],'event_global_step_index':before['step_index']},'state_layout':short._layout(p)}
    ctx=Context(root,directories,parts['selection'],parts['program'],parts['seed'],parts['history'],_canonical(manifest),_hash(manifest),_TOKEN)
    _context(ctx);context_bytes(ctx);return ctx


def _context(context):
    _need(type(context)is Context and context._token is _TOKEN,'CONTEXT_HOLD: prepared mixed organ context required');_fence()
    original,root_seed,root_manifest=parent._context(context._root)
    parts=(context._program,context._seed,context._history,context._selection,context._manifest)
    _need(all(type(v)is bytes for v in parts)and sum(map(len,parts))<=MAX_BYTES,'CAPACITY_HOLD: bounded immutable organ context required')
    p,seed,history,selection,m=map(json.loads,parts)
    arithmetic._closed(m,{'version','identity','root_context_sha256','initial_binding_sha256','parent_context_sha256','parent_checkpoint_sha256','redistribution_authorized',
        'program_sha256','seed_sha256','history_sha256','selection_sha256','numerical','state_layout'})
    arithmetic._closed(seed,{'last_confirmed','before_checkpoint','anchors','birth_bases','base_transfers'})
    _need(_canonical(m)==context._manifest and _hash(m)==context.root_sha256 and m['identity']==_identity(context._root)
        and m['version']==CONTEXT_VERSION and m['root_context_sha256']==context._root.root_sha256,'CONTEXT_HOLD: original identity/root required')
    for name,raw in zip(('program','seed','history','selection'),parts[:4],strict=True):
        _need(sha256(raw).hexdigest()==m[name+'_sha256']and _canonical(json.loads(raw))==raw,'CONTEXT_HOLD: original captured '+name+' required')
    _need(type(history)is list and 1<=len(history)<=1024,'CONTEXT_HOLD: bounded nonempty history required')
    expected=deepcopy(original);bases=_root_bases(original,root_seed);anchors=deepcopy(root_seed['evaluation']['curve_residuals']);previous=0;seen=set();before_program=None
    for position,record in enumerate(history):
        arithmetic._closed(record,{'kind','point_model_version','inputs','calculation_sha256','after_sample_sha256','new_items','birth_receipts','point_flows','balances','air_temperature_integral'})
        kind=record['kind'];v=record['inputs'];step=_input(v,kind,m['initial_binding_sha256'],original['model_floor_area'],root_manifest['numerical']['step_seconds'])
        _need(previous<=step<=root_manifest['numerical']['step_count'],'TIME_HOLD: ordered root-grid points required');previous=step
        _need(record['point_model_version']==(POINTS[kind].VERSION if position==0 else VERSION+':material-point')
            and parent._digest(record['calculation_sha256'])and parent._digest(record['after_sample_sha256']),'CONTEXT_HOLD: original point version/hashes required')
        if position==0:_need(v['context_sha256']==context._root.root_sha256,'CONTEXT_HOLD: first point root required')
        items=record['new_items'];_need(type(items)is list and items and len(items)==len(v['events'])==len(record['birth_receipts']),'CONTEXT_HOLD: complete recorded point inventory required');_history_units(record)
        before_program=deepcopy(expected);parents={row['compartment_id']for row in expected['stem_root_compartments']if row['kind']=='internode'}
        target='leaves'if kind=='leaf'else'stem_root_compartments';id_key='leaf_id'if kind=='leaf'else'compartment_id';ids={row[id_key]for row in expected[target]}
        for event,item,receipt in zip(v['events'],items,record['birth_receipts'],strict=True):
            arithmetic._closed(event,{'event_id','parent_internode_id','incoming_temperature','leaf'}if kind=='leaf'else{'event_id','parent_internode_id','compartment'})
            for name in ('event_id','parent_internode_id'):short.stock.part._id(event[name])
            _need(event['event_id']not in seen and event['parent_internode_id']in parents and item[id_key]not in ids,'EVENT_HOLD: actual parent and unique appended event/organ required')
            seen.add(event['event_id']);ids.add(item[id_key])
            if kind=='leaf':
                legacy._leaf_declaration(item,event['leaf']);numeric._temperature(arithmetic._quantity(event['incoming_temperature'],'degC'))
                bases['leaf'].append({'leaf_id':item['leaf_id'],'step_index':step,'thermal_age':0.,'carbon':item['initial_carbon']['value'],'air_temperature_integral':record['air_temperature_integral']});anchors.append(numeric._q(0.,'m2'))
            else:
                _stem_declaration(item,event['compartment']);bases['stem_root'].append({'compartment_id':item['compartment_id'],'kind':'internode','step_index':step,'carbon':item['initial_carbon']['value']})
            _receipt(receipt,event,item,kind)
        expected[target].extend(items)
        _need(len(expected['leaves'])<=512 and len(expected['stem_root_compartments'])<=512,'CAPACITY_HOLD: both bounded inventories required')
    _need(_canonical(p)==_canonical(expected)and seed['birth_bases']==bases and seed['anchors']==anchors,'CONTEXT_HOLD: original ordered program/birth baselines/anchors required')
    before,after=seed['before_checkpoint'],seed['last_confirmed'];arithmetic._closed(before,ROOT_CP_FIELDS if len(history)==1 else CP_FIELDS)
    _need(before['version']==(parent.CHECKPOINT_VERSION if len(history)==1 else CHECKPOINT_VERSION)
        and _hash(before)==m['parent_checkpoint_sha256']and before['context_sha256']==m['parent_context_sha256']==history[-1]['inputs']['context_sha256'],
        'CONTEXT_HOLD: actual parent checkpoint required')
    _need(type(after['step_index'])is int and type(after['elapsed_seconds'])is float and type(after['state'])is list
        and len(after['state'])==106+3*len(p['leaves'])+len(p['stem_root_compartments'])and all(type(v)is float and isfinite(v)for v in after['state']),
        'CONTEXT_HOLD: finite captured state required')
    _need(_hash(after)==history[-1]['after_sample_sha256']and after['step_index']==before['step_index']==previous
        and after['elapsed_seconds']==before['last_confirmed']['elapsed_seconds']and m['parent_checkpoint_sha256']==history[-1]['inputs']['checkpoint_sha256'],
        'CONTEXT_HOLD: original captured point time/hash required')
    _need(before['last_confirmed']['step_index']==previous and after['elapsed_seconds']==previous*root_manifest['numerical']['step_seconds'],
        'CONTEXT_HOLD: actual captured step and elapsed required')
    _transition(before_program,p,before['last_confirmed'],after,history[-1])
    _need(m['numerical']=={**root_manifest['numerical'],'event_global_step_index':previous}and m['state_layout']==short._layout(p),'CONTEXT_HOLD: original grid/layout required')
    _need(set(before['integrated_transfers'])==set(short._flux_units(before_program)),'CONTEXT_HOLD: complete original continuous prefix required')
    totals={name:before['integrated_transfers'].get(name,numeric._q(0.,unit))for name,unit in short._flux_units(p).items()}
    _need(_canonical(seed['base_transfers'])==_canonical(totals),'CONTEXT_HOLD: original continuous prefix values required')
    for name,unit in short._flux_units(p).items():legacy._captured_quantity(seed['base_transfers'][name],unit)
    remaining=root_manifest['numerical']['step_count']-previous
    _need((remaining+1)*(len(after['state'])+2*len(p['leaves'])+9)<=32768,'CAPACITY_HOLD: remaining sample scalar budget exceeded')
    source=_source(context)
    _need(type(m['redistribution_authorized'])is bool and m['redistribution_authorized']==
        (source['redistribution_authorized']and all(row['inputs']['rights']['redistribute']for row in history)),
        'RIGHTS_HOLD: original combined source/history redistribution rights required')
    _fence();return p,seed,m


@_public
def prepare_context(*,parent_context,raw_parent_checkpoint,expected_parent_sha256,kind,inputs,crop_directory,stem_directory,access,
                    crop_root_sha256,stem_root_sha256,stem_start_index,binding_declaration):
    _need(type(kind)is str and kind in POINTS,'SCOPE_HOLD: leaf/internode point required')
    original,seed,_=parent._context(parent_context)
    selection={'crop_root_sha256':crop_root_sha256,'stem_root_sha256':stem_root_sha256,'stem_start_index':stem_start_index,'binding_declaration':binding_declaration}
    directories=(Path(crop_directory),Path(stem_directory),access);fn=leaf.apply_leaf_births if kind=='leaf'else stem.apply_internode_births
    result=fn(parent_context,raw_parent_checkpoint,expected_parent_sha256,*directories,**selection,inputs=inputs)
    return _capture(parent_context,directories,selection,result['initial_binding_sha256'],result,kind,seed['evaluation']['curve_residuals'],_root_bases(original,seed),[])


@_public
def context_bytes(context):
    p,seed,m=_context(context)
    return _canonical({'program':p,'seed':seed,'history':context.point_history,'selection':json.loads(context._selection),'manifest':m})


def _parse(raw,expected_sha256,limit):
    _need(type(raw)is bytes and 0<len(raw)<=limit and parent._digest(expected_sha256)and sha256(raw).hexdigest()==expected_sha256,'CHECKPOINT_HOLD: trusted bounded raw SHA required')
    def pairs(items):
        result={}
        for name,value in items:_need(name not in result,'CHECKPOINT_HOLD: duplicate JSON key');result[name]=value
        return result
    def constant(v):raise OrganContinuationHold('CHECKPOINT_HOLD: nonfinite JSON constant')
    value=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
    _need(_canonical(value)==raw,'CHECKPOINT_HOLD: canonical bytes required');return value


@_public
def restore_context(*,root_context,raw_bytes,expected_sha256,crop_directory,stem_directory,access):
    v=_parse(raw_bytes,expected_sha256,MAX_BYTES);arithmetic._closed(v,{'program','seed','history','selection','manifest'})
    ctx=Context(root_context,(Path(crop_directory),Path(stem_directory),access),_canonical(v['selection']),_canonical(v['program']),_canonical(v['seed']),_canonical(v['history']),_canonical(v['manifest']),_hash(v['manifest']),_TOKEN)
    _context(ctx);return ctx


def _point_totals(context):
    history=context.point_history
    result={name:numeric._q(arithmetic._rounded(sum((Fraction.from_float(row['point_flows'][name]['value'])for row in history),Fraction(0))),unit)for name,unit in FLOW_UNITS.items()}
    for kind,label in [('leaf','leaf_structural_carbon'),('internode','stem_structural_carbon')]:
        result[label]=numeric._q(arithmetic._rounded(sum((Fraction.from_float(row['point_flows']['structural_carbon']['value'])for row in history if row['kind']==kind),Fraction(0))),leaf.MASS)
    return result


def _lifetime(p,seed,totals):
    return {name:numeric._q(numeric._sum(seed['base_transfers'][name]['value'],value),unit)for(name,unit),value in zip(short._flux_units(p).items(),totals,strict=True)}


def _segment_balances(context,p,seed,state,totals,sample,local):
    first=seed['last_confirmed'];initial=first['state'];dt=context.manifest['numerical']['step_seconds'];latent=context._root._profiles[-1].values['latent_heat']
    views=[{'joint':{'derived':item['derived']}}for item in (first,sample)]
    residuals,budgets=short.old._balances(p,short._project(p,initial),short._project(p,state),totals[:21],*views,local,local*dt,latent)
    n=len(p['leaves']);m=len(p['stem_root_compartments']);rows=[]
    for label,start,count,flow in [('leaf',106+2*n,n,21),('stem_root',106+3*n,m,21+3*n)]:
        for i in range(count):
            a,b=initial[start+i],state[start+i];G,M,R=totals[flow+3*i:flow+3*i+3];rows.append((label+'_carbon_'+str(i),a,b,(numeric._sum(b,-a),-G,M,R)))
    a,b=(short.stock._sum(y[106+3*n:])for y in (initial,state));G,M,R=(numeric._sum(*totals[21+3*n+k::3])for k in range(3))
    rows.append(('stem_root_carbon',a,b,(numeric._sum(b,-a),-G,M,R)))
    for name,a,b,terms in rows:
        residual=numeric._sum(*terms);budget=numeric._multiply(64*(local+1),ulp(max(abs(a),abs(b),numeric._sum(*map(abs,terms)))))
        _need(abs(residual)<=budget,'BALANCE_HOLD: '+name);residuals[name]=numeric._q(residual,leaf.MASS);budgets[name]=numeric._q(budget,leaf.MASS)
    return residuals,budgets


def _global_balances(context,p,seed,state,lifetime,sample,segment_budgets,index):
    original,root_seed,_=parent._context(context._root);initial=root_seed['state'];n0=len(original['leaves']);n=len(p['leaves'])
    first=short._view(root_seed['evaluation'])['joint']['derived'];last=sample['derived'];ca=first['air_capacity']['value'];latent=context._root._profiles[-1].values['latent_heat']
    _need(ca==last['air_capacity']['value'],'BALANCE_HOLD: original air capacity required')
    t={k:v['value']for k,v in lifetime.items()};points=_point_totals(context);point_value=lambda name:points[name]['value']
    carbon=(state[0],*state[3:53],*state[106+2*n:],-initial[0],*(-v for v in initial[3:53]),*(-v for v in initial[106+2*n0:]),-t['photosynthesis'],
        *(t[k]for k in ('growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit','removal_leaf','removal_stem','terminal_carbon')),point_value('growth_respiration'))
    number=(*state[53:103],*(-v for v in initial[53:103]),-t['entry_number'],t['terminal_number'])
    du=(state[103],-initial[103]);da=numeric._multiply(ca,numeric._sum(state[104],-initial[104]));dw=numeric._sum(state[105],-initial[105])
    sensible=(*du,-t['canopy_external'],t['sensible'],t['latent'],-t['incoming_heat'],t['outgoing_heat'],-point_value('sensible_in'))
    air=(da,-t['air_external'],-t['sensible']);vapor=(state[105],-initial[105],-t['vapor'],-t['external_vapor'])
    capacity=(last['canopy_capacity']['value'],-first['canopy_capacity']['value'],-t['capacity_in'],t['capacity_out'],-point_value('capacity_in'))
    reduced=(*du,da,numeric._multiply(latent,dw),-t['canopy_external'],-t['air_external'],-numeric._multiply(latent,t['external_vapor']),-t['incoming_heat'],t['outgoing_heat'],-point_value('sensible_in'))
    rows={'carbohydrate':(carbon,leaf.MASS,'whole_carbon'),'number':(number,'fruits_equivalent/m2_floor',None),
        'canopy_sensible':(sensible,numeric.ENERGY,'sensible'),'air_sensible':(air,numeric.ENERGY,None),'vapor':(vapor,'kg_water/m2_floor',None),
        'area_capacity':(capacity,numeric.CAPACITY,'capacity'),'reduced_energy':(reduced,numeric.ENERGY,'sensible')}
    dt=context.manifest['numerical']['step_seconds']
    for i,base in enumerate(seed['birth_bases']['leaf']):
        duration=numeric._multiply(index-base['step_index'],dt)
        rows['leaf_age_'+str(i)]=((state[106+i],-base['thermal_age'],-numeric._divide(t['indoor_air_temperature_time'],86400),numeric._divide(base['air_temperature_integral'],86400),
            numeric._divide(numeric._multiply(p['leaves'][i]['base_temperature']['value'],duration),86400)),'degC_day',None)
        rows['leaf_carbon_'+str(i)]=((state[106+2*n+i],-base['carbon'],-t[f'leaf_{i}_inflow'],t[f'leaf_{i}_maintenance'],t[f'leaf_{i}_removal']),leaf.MASS,None)
    for i,base in enumerate(seed['birth_bases']['stem_root']):
        rows['stem_root_carbon_'+str(i)]=((state[106+3*n+i],-base['carbon'],-t[f'stem_root_{i}_inflow'],t[f'stem_root_{i}_maintenance'],t[f'stem_root_{i}_removal']),leaf.MASS,None)
    rows['stem_root_carbon']=((*(state[106+3*n:]),*(-v for v in initial[106+3*n0:]),
        -numeric._sum(*(t[f'stem_root_{i}_inflow']for i in range(len(p['stem_root_compartments'])))),
        numeric._sum(*(t[f'stem_root_{i}_maintenance']for i in range(len(p['stem_root_compartments'])))),
        numeric._sum(*(t[f'stem_root_{i}_removal']for i in range(len(p['stem_root_compartments'])))),-point_value('stem_structural_carbon')),leaf.MASS,'new_stock')
    before=seed['before_checkpoint'];prior=before.get('global_balance_budgets',before['balance_budgets']);last_point=context.point_history[-1];point_budgets=last_point['balances'];residuals={};budgets={}
    for name,(terms,unit,event_key)in rows.items():
        if name=='stem_root_carbon'and last_point['kind']!='internode':event_key=None
        aggregation=numeric._multiply(64,ulp(numeric._sum(*map(abs,terms))))
        budget=numeric._sum(prior.get(name,numeric._q(0.,unit))['value'],segment_budgets[name]['value'],aggregation,
            point_budgets.get(event_key,{'budget':{'value':0.}})['budget']['value'])
        residual=numeric._sum(*terms);_need(abs(residual)<=budget,'GLOBAL_BALANCE_HOLD: '+name)
        residuals[name]=numeric._q(residual,unit);budgets[name]=numeric._q(budget,unit)
    return residuals,budgets


@dataclass(frozen=True)
class Checkpoint:
    _raw: bytes = field(repr=False)
    sha256: str
    context_sha256: str
    _token: object = field(repr=False)

    @property
    def value(self): return json.loads(self._raw)


def _seal(context, payload):
    _fence(); _source(context)
    raw = _canonical(payload)
    _need(len(raw) <= MAX_CHECKPOINT_BYTES, 'CAPACITY_HOLD: 512KiB mixed organ checkpoint required')
    return Checkpoint(raw, sha256(raw).hexdigest(), context.root_sha256, _TOKEN)


def _build(context, p, seed, m, sample, totals, prefix):
    index = sample['step_index']; local = index-m['numerical']['event_global_step_index']
    lifetime = _lifetime(p, seed, totals)
    residuals, budgets = _segment_balances(context, p, seed, sample['state'], totals, sample, local)
    gr, gb = _global_balances(context, p, seed, sample['state'], lifetime, sample, budgets, index)
    return {'version': CHECKPOINT_VERSION, 'context_sha256': context.root_sha256,
            'step_index': index, 'segment_step_index': local, 'event_sequence': len(context.point_history),
            'phase': 'after_birth' if local == 0 else 'funded_birth_interval',
            'at_elapsed_seconds_exact': _exact(index, m['numerical']['step_seconds']),
            'last_confirmed': deepcopy(sample), 'output_cursor': seed['before_checkpoint']['output_cursor']+1+local,
            'output_prefix_sha256': prefix, 'integrated_transfers': lifetime,
            'segment_integrated_transfers': {name: numeric._q(v, unit) for (name, unit), v in
                zip(short._flux_units(p).items(), totals, strict=True)},
            'point_history_sha256': m['history_sha256'], 'point_totals': _point_totals(context),
            'balance_residuals': residuals, 'balance_budgets': budgets,
            'global_balance_residuals': gr, 'global_balance_budgets': gb,
            'scope': 'software_research_only', 'G0_G4': 'not_assessed','time_kind':'synthetic_model_clock_not_observation',
            'redistribution_authorized':m['redistribution_authorized']}


def _prefix(previous, sample, sequence, phase):
    return _hash({'previous': previous, 'sample': sample, 'event_sequence': sequence, 'phase': phase})


def _initial(context, p, seed, m):
    sample = seed['last_confirmed']
    prefix = _prefix(seed['before_checkpoint']['output_prefix_sha256'], sample, len(context.point_history), 'after_birth')
    return _build(context, p, seed, m, sample, (0.,)*len(short._flux_units(p)), prefix)


@_public
def start(context):
    p, seed, m = _context(context)
    return _seal(context, _initial(context, p, seed, m))


@_public
def checkpoint_bytes(context, checkpoint):
    _context(context)
    _need(type(checkpoint) is Checkpoint and checkpoint._token is _TOKEN and checkpoint.context_sha256 == context.root_sha256
          and type(checkpoint._raw) is bytes and 0 < len(checkpoint._raw) <= MAX_CHECKPOINT_BYTES
          and sha256(checkpoint._raw).hexdigest() == checkpoint.sha256, 'CHECKPOINT_HOLD: immutable matching funded checkpoint required')
    return checkpoint._raw


def _validate(context, payload, p, seed, m):
    initial = _initial(context, p, seed, m)
    _need(type(payload) is dict and set(payload) == set(initial), 'CHECKPOINT_HOLD: closed funded checkpoint required')
    static = {'version', 'context_sha256', 'event_sequence', 'point_history_sha256', 'point_totals', 'scope', 'G0_G4'}
    _need(_canonical({k: payload[k] for k in static}) == _canonical({k: initial[k] for k in static}),
          'CHECKPOINT_HOLD: changed funded source/point identity')
    index = payload['step_index']; local = payload['segment_step_index']; event = m['numerical']['event_global_step_index']
    _need(type(index) is int and type(local) is int and 0 <= local <= m['numerical']['step_count']-event
          and index == event+local and type(payload['output_cursor']) is int
          and payload['output_cursor'] == initial['output_cursor']+local and parent._digest(payload['output_prefix_sha256']),
          'CHECKPOINT_HOLD: original global index/cursor/prefix required')
    _need(payload['at_elapsed_seconds_exact'] == _exact(index, m['numerical']['step_seconds'])
          and payload['phase'] == ('after_birth' if local == 0 else 'funded_birth_interval'), 'TIME_HOLD: current exact coordinate/phase required')
    sample = payload['last_confirmed']
    _need(type(sample) is dict and set(sample) == set(seed['last_confirmed']), 'CHECKPOINT_HOLD: closed current sample required')
    state = sample['state']
    _need(type(state) is list and len(state) == len(seed['last_confirmed']['state'])
          and all(type(v) is float and isfinite(v) for v in state), 'CHECKPOINT_HOLD: finite float64 state required')
    rows = payload['segment_integrated_transfers']; units = short._flux_units(p)
    _need(type(rows) is dict and set(rows) == set(units), 'CHECKPOINT_HOLD: closed segment transfers required')
    for name, unit in units.items():
        row = rows[name]
        _need(type(row) is dict and set(row) == {'value', 'unit'} and row['unit'] == unit
              and type(row['value']) is float and isfinite(row['value']), 'CHECKPOINT_HOLD: finite float64 transfer/unit required')
    totals = tuple(rows[name]['value'] for name in units)
    rates, current = short._evaluate(p, tuple(state), parent._profiles(context._root))
    expected = short._sample(index, m['numerical']['step_seconds'], state, current, seed['anchors'])
    built = _build(context, p, seed, m, expected, totals, payload['output_prefix_sha256'])
    _need(_canonical(payload) == _canonical(built), 'CHECKPOINT_HOLD: stale current sample/derived/ledgers')
    if local == 0:
        _need(_canonical(payload) == _canonical(initial), 'CHECKPOINT_HOLD: original birth snapshot required')
    return tuple(state), totals, rates, current


@_public
def restore_checkpoint(context, raw_bytes, *, expected_sha256):
    p, seed, m = _context(context)
    payload = _parse(raw_bytes, expected_sha256, MAX_CHECKPOINT_BYTES)
    _validate(context, payload, p, seed, m)
    return _seal(context, payload)


@_public
def adopt_births(*,context,raw_checkpoint,expected_sha256,kind,inputs):
    p,seed,m=_context(context);cp=restore_checkpoint(context,raw_checkpoint,expected_sha256=expected_sha256)
    raw=_canonical(inputs);v=json.loads(raw);at=Fraction.from_float(m['numerical']['step_seconds'])*cp.value['step_index']
    _input(v,kind,m['initial_binding_sha256'],p['model_floor_area'],m['numerical']['step_seconds'],context_sha=context.root_sha256,checkpoint_sha=cp.sha256,at=at)
    seen={event['event_id']for record in context.point_history for event in record['inputs']['events']}
    _need(all(type(event)is dict and event.get('event_id')not in seen for event in v['events']),'EVENT_HOLD: previously funded event cannot be debited again')
    profiles=parent._profiles(context._root);state=cp.value['last_confirmed']['state']
    jump=leaf._jump(p,state,profiles,v['events'],seed['anchors'])if kind=='leaf'else stem._jump(p,state,profiles,v['events'])
    anchors=jump.get('anchors',seed['anchors']);sample=short._sample(cp.value['step_index'],m['numerical']['step_seconds'],jump['state'],jump['evaluation'],anchors)
    flows={name:numeric._q(value,leaf.MASS)for name,value in [('structural_carbon',jump['structural']),('growth_respiration',jump['respiration']),('buffer_debit',jump['debit'])]}
    flows.update(capacity_in=numeric._q(jump.get('capacity',0.),numeric.CAPACITY),sensible_in=numeric._q(jump.get('energy',0.),numeric.ENERGY))
    result={'model_version':VERSION+':material-point','context_sha256':context.root_sha256,'checkpoint_sha256':cp.sha256,'inputs':v,
        'redistribution_authorized':m['redistribution_authorized']and v['rights']['redistribute'],
        'before_checkpoint':cp.value,'after_program':jump['program'],'after_sample':sample,'after_anchors':anchors,
        'birth_receipts':jump['receipts'],'point_flows':flows,'balances':jump['balances'],'kind':kind,'code_sha256':CODE_SHA256}
    result['calculation_sha256']=_hash(result)
    return _capture(context._root,context._directories,json.loads(context._selection),m['initial_binding_sha256'],result,kind,anchors,seed['birth_bases'],context.point_history)


@_public
def advance_chunk(context, checkpoint, step_budget):
    _need(type(step_budget) is int and 1 <= step_budget <= 128, 'BUDGET_HOLD: 1..128 integer steps required')
    p, seed, m = _context(context)
    payload = json.loads(checkpoint_bytes(context, checkpoint))
    state, totals, rates, current = _validate(context, payload, p, seed, m)
    begin = payload['step_index']; count = m['numerical']['step_count']; dt = m['numerical']['step_seconds']
    _need(begin < count, 'COMPLETED_HOLD: no funded interval step remains')
    flux = short._flux(p, state, current); samples = []; attempts = 0; held = None; sealed = checkpoint
    index = begin; phase = 'ready'
    try:
        for index in range(begin+1, min(count, begin+step_budget)+1):
            phase = 'k2'; y2 = short._advance(state, rates, dt/2); attempts += 1
            k2, r2 = short._evaluate(p, y2, parent._profiles(context._root))
            phase = 'k3'; y3 = short._advance(state, k2, dt/2); attempts += 1
            k3, r3 = short._evaluate(p, y3, parent._profiles(context._root))
            phase = 'k4'; y4 = short._advance(state, k3, dt); attempts += 1
            k4, r4 = short._evaluate(p, y4, parent._profiles(context._root))
            phase = 'endpoint'; candidate = short._advance(state, short._weighted(rates, k2, k3, k4), dt)
            cumulative = short._advance(totals, short._weighted(flux, short._flux(p, y2, r2), short._flux(p, y3, r3), short._flux(p, y4, r4)), dt)
            attempts += 1
            new_rates, evaluated = short._evaluate(p, candidate, parent._profiles(context._root))
            sample = short._sample(index, dt, candidate, evaluated, seed['anchors'])
            phase = 'endpoint_balance'
            new_payload = _build(context, p, seed, m, sample, cumulative,
                _prefix(payload['output_prefix_sha256'], sample, len(context.point_history), 'funded_birth_interval'))
            phase = 'checkpoint'; candidate_cp = _seal(context, new_payload)
            state, totals, rates, current = candidate, cumulative, new_rates, evaluated
            flux = short._flux(p, state, current); payload = new_payload; sealed = candidate_cp; samples.append(sample)
        phase='source_fence'; _source(context); _fence()
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, ZeroDivisionError, RecursionError) as error:
        held = {'step_index': index, 'at_elapsed_seconds_exact': _exact(index, dt), 'stage': phase,
                'reason': str(error) if isinstance(error, ValueError) else 'INPUT_HOLD: funded interval arithmetic'}
        sealed = None
    result = {'status': 'hold' if held else 'completed' if payload['step_index'] == count else 'yielded',
              'manifest': m, 'context_sha256': context.root_sha256, 'samples': samples, 'hold': held, 'checkpoint': sealed,
              **{name: deepcopy(payload[name]) for name in ('step_index', 'phase', 'last_confirmed', 'integrated_transfers',
                  'segment_integrated_transfers', 'point_totals', 'balance_residuals', 'balance_budgets',
                  'global_balance_residuals', 'global_balance_budgets', 'output_cursor', 'output_prefix_sha256')},
              'checkpoint_validation_stage_evaluations': 1, 'attempted_new_stage_evaluations': attempts,
              'confirmed_new_steps': payload['step_index']-begin, 'scope': 'software_research_only',
              'claim_scope': 'synthetic_mixed_organ_funded_continuation_only', 'G0_G4': 'not_assessed','time_kind':'synthetic_model_clock_not_observation',
              'redistribution_authorized':m['redistribution_authorized']}
    _canonical({k: v for k, v in result.items() if k != 'checkpoint'})
    return result
