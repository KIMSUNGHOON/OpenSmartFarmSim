from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_organ_funded_continuation as model
from test_crop_stem_root_initial_binding import stored,profiles
from test_crop_stem_root_funded_leaf_point import setup as leaf_setup
from test_crop_stem_root_funded_internode_point import setup as stem_setup

SOURCE_KEYS=('crop_directory','stem_directory','access','crop_root_sha256','stem_root_sha256','stem_start_index','binding_declaration')


@pytest.fixture(scope='module')
def roots(stored,profiles):
    return [(model.parent.prepare_context(program=row[0].program,step_seconds=.125,step_count=4,**profiles),*row[1:])for row in stored]


def prepared(row,kind='leaf',cut=0):
    kw=(leaf_setup if kind=='leaf'else stem_setup)(row,cut,count=1)
    ctx=model.prepare_context(parent_context=kw['context'],raw_parent_checkpoint=kw['raw_checkpoint'],expected_parent_sha256=kw['expected_sha256'],
        kind=kind,inputs=kw['inputs'],**{k:kw[k]for k in SOURCE_KEYS})
    return ctx,kw


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('kind',['leaf','internode'])
@pytest.mark.parametrize('cut',[0,2,4])
def test_adopted_context_matches_actual_point_and_preserves_current_prefix_and_birth_baselines(roots,case,kind,cut):
    ctx,kw=prepared(roots[case],kind,cut);module=model.POINTS[kind]
    point=(module.apply_leaf_births if kind=='leaf'else module.apply_internode_births)(**kw)
    p,seed,m=model._context(ctx)
    assert p==point['after_program']and seed['last_confirmed']==point['after_sample']and seed['before_checkpoint']==point['before_checkpoint']
    assert m['numerical']['event_global_step_index']==cut and len(ctx.point_history)==1
    assert ctx.point_history[0]['kind']==kind and ctx.point_history[0]['birth_receipts']==point['birth_receipts']
    cp=model.start(ctx);assert cp.value['step_index']==cut and cp.value['event_sequence']==1 and cp.value['phase']=='after_birth'
    for name,value in point['before_checkpoint']['integrated_transfers'].items():assert cp.value['integrated_transfers'][name]==value
    assert all(abs(row['value'])<=cp.value['global_balance_budgets'][name]['value']for name,row in cp.value['global_balance_residuals'].items())


@pytest.mark.parametrize('kind',['leaf','internode'])
@pytest.mark.parametrize('case',range(6))
def test_real_resume_current_state_preserves_time_and_all_ledgers(roots,kind,case):
    ctx,kw=prepared(roots[case],kind,2);cp=model.start(ctx);out=model.advance_chunk(ctx,cp,2)
    assert out['status']=='completed',out.get('hold')
    assert out['step_index']==4 and [s['elapsed_seconds']for s in out['samples']]==[.375,.5]
    assert out['checkpoint_validation_stage_evaluations']==1 and out['attempted_new_stage_evaluations']==8
    assert all(abs(row['value'])<=out['global_balance_budgets'][name]['value']for name,row in out['global_balance_residuals'].items())
    raw=model.checkpoint_bytes(ctx,out['checkpoint']);restored=model.restore_checkpoint(ctx,raw,expected_sha256=sha256(raw).hexdigest());assert model.checkpoint_bytes(ctx,restored)==raw
    with pytest.raises(model.OrganContinuationHold,match='COMPLETED_HOLD'):model.advance_chunk(ctx,restored,1)


def next_inputs(ctx,cp,kind,kw,suffix='second'):
    v=deepcopy((leaf_setup if kind=='leaf'else stem_setup)((ctx._root,*[kw[k]for k in ('crop_directory','stem_directory','crop_root_sha256','stem_root_sha256','stem_start_index')]),count=1)['inputs'])
    v.update(context_sha256=ctx.root_sha256,checkpoint_sha256=cp.sha256,at_elapsed_seconds_exact=cp.value['at_elapsed_seconds_exact'])
    v['events'][0]['event_id']=suffix+'-event'
    key='leaf'if kind=='leaf'else'compartment';id_key='leaf_id'if kind=='leaf'else'compartment_id'
    v['events'][0][key][id_key]=suffix+'-'+kind
    if ctx.point_history[-1]['kind']=='internode':v['events'][0]['parent_internode_id']=ctx.program['stem_root_compartments'][-1]['compartment_id']
    return v


@pytest.mark.parametrize('first,second',[('leaf','internode'),('internode','leaf'),('leaf','leaf'),('internode','internode')])
def test_two_point_kinds_and_same_time_order_keep_history_and_reject_global_event_reuse(roots,first,second):
    ctx,kw=prepared(roots[0],first,0);cp=model.advance_chunk(ctx,model.start(ctx),2)['checkpoint'];v=next_inputs(ctx,cp,second,kw)
    adopted=model.adopt_births(context=ctx,raw_checkpoint=model.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256,kind=second,inputs=v)
    new=model.start(adopted);assert len(adopted.point_history)==2 and new.value['step_index']==2 and new.value['event_sequence']==2
    assert new.value['output_cursor']==cp.value['output_cursor']+1 and new.value['output_prefix_sha256']!=cp.value['output_prefix_sha256']
    out=model.advance_chunk(adopted,new,2);assert out['status']=='completed',out.get('hold')
    repeated=deepcopy(v);repeated.update(context_sha256=adopted.root_sha256,checkpoint_sha256=new.sha256)
    with pytest.raises(model.OrganContinuationHold,match='EVENT_HOLD'):model.adopt_births(context=adopted,raw_checkpoint=model.checkpoint_bytes(adopted,new),expected_sha256=new.sha256,kind=second,inputs=repeated)


def snapshot(kw,raw):
    return model.restore_context(root_context=kw['context'],raw_bytes=raw,expected_sha256=sha256(raw).hexdigest(),
        **{k:kw[k]for k in ('crop_directory','stem_directory','access')})


def rehash_snapshot(value):
    for name in ('program','seed','history','selection'):value['manifest'][name+'_sha256']=sha256(model._canonical(value[name])).hexdigest()
    return model._canonical(value)


@pytest.mark.parametrize('kind,index_name',[(k,i)for k in ('leaf','internode')for i in ('buffer','oldstock','newstock')]+[('leaf',i)for i in ('old_age','new_age','new_area','canopy_energy')])
def test_altered_captured_point_state_is_rejected_without_replaying_point(roots,kind,index_name):
    ctx,kw=prepared(roots[0],kind);value=json.loads(model.context_bytes(ctx));n=len(ctx.program['leaves']);n0=len(kw['context'].program['leaves'])
    index={'buffer':0,'oldstock':106+3*n,'newstock':106+2*n+n0 if kind=='leaf'else len(value['seed']['last_confirmed']['state'])-1,
        'old_age':106,'new_age':106+n0,'new_area':106+n+n0,'canopy_energy':103}[index_name]
    value['seed']['last_confirmed']['state'][index]+=.01
    value['history'][-1]['after_sample_sha256']=sha256(model._canonical(value['seed']['last_confirmed'])).hexdigest()
    with pytest.raises(model.OrganContinuationHold,match='CONTEXT_HOLD'):snapshot(kw,rehash_snapshot(value))


def test_source_false_rights_remain_explicit_in_context_checkpoint_and_response(roots):
    ctx,kw=prepared(roots[0]);assert ctx.manifest['redistribution_authorized']is False
    cp=model.start(ctx);assert cp.value['redistribution_authorized']is False
    out=model.advance_chunk(ctx,cp,1);assert out['redistribution_authorized']is False


@pytest.fixture(scope='module')
def base_context(roots):return prepared(roots[0],'leaf',1)


def test_profile_changed_at_endpoint_withholds_unconfirmed_checkpoint(base_context,monkeypatch):
    from types import MappingProxyType
    ctx,kw=base_context;cp=model.start(ctx);evaluate=model.short._evaluate;calls=[];profile=ctx._root._profiles[0];original=profile.values
    def changed(*a,**k):
        result=evaluate(*a,**k);calls.append(1)
        if len(calls)==5:object.__setattr__(profile,'values',MappingProxyType({**dict(original),'cLeafG':.4}))
        return result
    monkeypatch.setattr(model.short,'_evaluate',changed)
    try:
        out=model.advance_chunk(ctx,cp,1);assert out['status']=='hold'and out['checkpoint']is None
        assert out['last_confirmed']==cp.value['last_confirmed']and out['output_prefix_sha256']==cp.value['output_prefix_sha256']
    finally:object.__setattr__(profile,'values',original)


@pytest.fixture(scope='module')
def full_cases(roots):
    cases={}
    for case in range(6):
        for kind in ('leaf','internode'):
            ctx,kw=prepared(roots[case],kind);start=model.start(ctx);out=model.advance_chunk(ctx,start,4)
            assert out['status']=='completed',out.get('hold');cases[case,kind]=(ctx,kw,start,out)
    return cases


GROUPS=[(4,),(1,3),(2,2),(3,1),(1,1,2),(1,2,1),(2,1,1),(1,1,1,1)]
@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('kind',['leaf','internode'])
@pytest.mark.parametrize('grouping',GROUPS)
def test_all_four_step_partitions_preserve_samples_ledgers_and_final_bytes(full_cases,case,kind,grouping):
    ctx,kw,cp,whole=full_cases[case,kind];samples=[]
    for count in grouping:
        result=model.advance_chunk(ctx,cp,count);assert result['checkpoint']is not None,result.get('hold')
        samples.extend(result['samples']);cp=result['checkpoint']
    assert samples==whole['samples']and model.checkpoint_bytes(ctx,cp)==model.checkpoint_bytes(ctx,whole['checkpoint'])


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('first,second',[('leaf','internode'),('internode','leaf')])
@pytest.mark.parametrize('first_groups,second_groups',[((2,),(2,)),((1,1),(2,)),((2,),(1,1)),((1,1),(1,1))])
def test_two_point_plan_is_independent_of_chunk_boundaries(roots,case,first,second,first_groups,second_groups):
    ctx,kw=prepared(roots[case],first);cp=model.start(ctx)
    def execute(groups1,groups2):
        current=cp
        for count in groups1:current=model.advance_chunk(ctx,current,count)['checkpoint']
        v=next_inputs(ctx,current,second,kw)
        nxt=model.adopt_births(context=ctx,raw_checkpoint=model.checkpoint_bytes(ctx,current),expected_sha256=current.sha256,kind=second,inputs=v)
        end=model.start(nxt)
        for count in groups2:end=model.advance_chunk(nxt,end,count)['checkpoint']
        return model.context_bytes(nxt),model.checkpoint_bytes(nxt,end)
    assert execute(first_groups,second_groups)==execute((2,),(2,))


@pytest.mark.parametrize('change',[
    lambda v:v['manifest'].update(extra=1),lambda v:v['seed'].update(extra=1),lambda v:v['program'].update(extra=1),
    lambda v:v['selection'].update(extra=1),lambda v:v['history'][0].update(extra=1),
    lambda v:v['history'][0]['new_items'][0]['thermal_age'].update(unit='s'),
    lambda v:v['history'][0]['point_flows']['structural_carbon'].update(unit='g_DM/plant'),
    lambda v:v['history'][0]['balances']['whole_carbon']['budget'].update(value=-1.),
    lambda v:v['history'][0]['birth_receipts'][0]['capacity_in'].update(unit='W'),
    lambda v:v['history'][0]['birth_receipts'][0]['initialization']['state']['age_exact'].update(numerator='1'),
    lambda v:v['seed']['anchors'][0].update(unit='m2_floor'),lambda v:v['seed']['birth_bases']['stem_root'][0].update(carbon=999.),
    lambda v:v['seed']['base_transfers']['photosynthesis'].update(unit='g_DM'),
    lambda v:v['manifest'].update(redistribution_authorized=True),
    lambda v:v['selection']['binding_declaration']['rights'].update(use=False),
    lambda v:v['manifest']['numerical'].update(step_count=999),lambda v:v['manifest'].update(root_context_sha256='0'*64),
    lambda v:v['history'][0]['inputs'].update(origin='observed')])
def test_self_rehashed_context_still_rejects_closed_units_sources_scope_and_receipt_faults(base_context,change):
    ctx,kw=base_context;v=json.loads(model.context_bytes(ctx));change(v)
    with pytest.raises(model.OrganContinuationHold):snapshot(kw,rehash_snapshot(v))


def test_context_restore_start_and_bytes_do_not_replay_points_RHS_or_area(base_context,monkeypatch):
    import socket,subprocess,psycopg,os
    ctx,kw=base_context;raw=model.context_bytes(ctx);cp=model.start(ctx);blob=model.checkpoint_bytes(ctx,cp)
    def forbidden(*a,**k):raise AssertionError('no context replay/initialization/external I/O')
    for owner,name in [(model.short,'_evaluate'),(model.short,'_prepare'),(model.short,'integrate'),(model.leaf,'_jump'),(model.stem,'_jump'),
        (model.arithmetic,'_fund'),(model.arithmetic,'_new_leaf'),(model.short.old.leaf_area,'initialize_leaf_area'),
        (model.short.old.leaf_area,'normalize_leaf_area_state'),(model.short.old.leaf_area,'_area_at'),(socket,'socket'),(subprocess,'Popen'),(psycopg,'connect')]:monkeypatch.setattr(owner,name,forbidden)
    original=os.open
    def readonly(path,flags,*a,**k):
        if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return forbidden()
        return original(path,flags,*a,**k)
    monkeypatch.setattr(os,'open',readonly)
    restored=snapshot(kw,raw);assert model.context_bytes(restored)==raw and model.checkpoint_bytes(restored,model.start(restored))==blob


@pytest.mark.parametrize('change',[
    lambda v:v.update(extra=1),lambda v:v.update(version=model.parent.CHECKPOINT_VERSION),lambda v:v.update(context_sha256='0'*64),
    lambda v:v.update(step_index=True),lambda v:v.update(output_cursor=True),lambda v:v.update(segment_step_index=9),
    lambda v:v.update(event_sequence=99),lambda v:v['at_elapsed_seconds_exact'].update(numerator='9'),
    lambda v:v['last_confirmed']['state'].__setitem__(0,True),lambda v:v['last_confirmed']['state'].__setitem__(-1,-1.),
    lambda v:v['segment_integrated_transfers']['photosynthesis'].update(unit='g_DM'),lambda v:v['integrated_transfers']['photosynthesis'].update(value=999.),
    lambda v:v['point_totals']['growth_respiration'].update(value=999.),lambda v:v.update(redistribution_authorized=True),
    lambda v:v['global_balance_budgets']['stem_root_carbon_0'].update(value=999.)])
def test_self_rehashed_current_checkpoint_fields_state_units_and_ledgers_rejected(base_context,change):
    ctx,kw=base_context;v=model.start(ctx).value;change(v);raw=model._canonical(v)
    with pytest.raises(model.OrganContinuationHold):model.restore_checkpoint(ctx,raw,expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('bad',[b'',b'\xff',b'{}',b'null',b'{"value":NaN}'])
def test_external_context_and_CP_bytes_require_canonical_closed_JSON(base_context,bad):
    ctx,kw=base_context
    with pytest.raises(model.OrganContinuationHold):model.restore_checkpoint(ctx,bad,expected_sha256=sha256(bad).hexdigest())
    with pytest.raises(model.OrganContinuationHold):snapshot(kw,bad)


@pytest.mark.parametrize('budget',[True,0,129,1.5])
def test_step_budget_is_a_bounded_integer(base_context,budget):
    ctx,kw=base_context
    with pytest.raises(model.OrganContinuationHold):model.advance_chunk(ctx,model.start(ctx),budget)


@pytest.mark.parametrize('fail_at',[2,3,4,5,6,9])
def test_trial_RHS_failure_retains_only_last_confirmed_prefix_and_no_checkpoint(base_context,monkeypatch,fail_at):
    ctx,kw=base_context;cp=model.start(ctx);evaluate=model.short._evaluate;calls=[]
    def failing(*a,**k):
        calls.append(1)
        if len(calls)==fail_at:raise ValueError('injected trial failure')
        return evaluate(*a,**k)
    monkeypatch.setattr(model.short,'_evaluate',failing);out=model.advance_chunk(ctx,cp,3)
    confirmed=0 if fail_at<=5 else 1
    assert out['status']=='hold'and out['checkpoint']is None and out['confirmed_new_steps']==confirmed
    assert len(out['samples'])==confirmed and out['last_confirmed']==(out['samples'][-1]if confirmed else cp.value['last_confirmed'])
    if not confirmed:assert out['output_prefix_sha256']==cp.value['output_prefix_sha256']


def test_late_source_change_withholds_candidate_and_runtime_error_is_not_a_normal_hold(base_context,monkeypatch):
    ctx,kw=base_context;cp=model.start(ctx);evaluate=model.short._evaluate;bind=model._bind;calls=[]
    def counted(*a,**k):result=evaluate(*a,**k);calls.append(1);return result
    def changed(*a,**k):
        result=bind(*a,**k)
        if len(calls)>=5:result['source_rights']['stem']['display']=False
        return result
    monkeypatch.setattr(model.short,'_evaluate',counted);monkeypatch.setattr(model,'_bind',changed)
    out=model.advance_chunk(ctx,cp,1);assert out['status']=='hold'and out['checkpoint']is None and out['last_confirmed']==cp.value['last_confirmed']
    calls.clear()
    def unexpected(*a,**k):raise RuntimeError('unexpected operator failure')
    monkeypatch.setattr(model.short,'_evaluate',unexpected)
    with pytest.raises(RuntimeError):model.advance_chunk(ctx,cp,1)


@pytest.mark.parametrize('first,second',[('leaf','internode'),('internode','leaf'),('leaf','leaf'),('internode','internode')])
def test_same_time_cross_kind_points_keep_order_and_distinct_prefix_without_clock_reset(roots,first,second):
    ctx,kw=prepared(roots[0],first);cp=model.start(ctx);v=next_inputs(ctx,cp,second,kw,suffix='same-time')
    nxt=model.adopt_births(context=ctx,raw_checkpoint=model.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256,kind=second,inputs=v);after=model.start(nxt)
    assert cp.value['at_elapsed_seconds_exact']==after.value['at_elapsed_seconds_exact']and cp.value['step_index']==after.value['step_index']==0
    assert cp.value['event_sequence']+1==after.value['event_sequence']==2 and cp.value['output_cursor']+1==after.value['output_cursor']
    assert cp.value['output_prefix_sha256']!=after.value['output_prefix_sha256']and [r['kind']for r in nxt.point_history]==[first,second]
    assert model.advance_chunk(nxt,after,4)['status']=='completed'


@pytest.mark.parametrize('kind',['leaf','internode'])
@pytest.mark.parametrize('dt',[.1,1/3])
def test_non_dyadic_time_chunks_have_identical_final_bytes(stored,profiles,kind,dt):
    row=stored[0];root=model.parent.prepare_context(program=row[0].program,step_seconds=dt,step_count=4,**profiles)
    ctx,kw=prepared((root,*row[1:]),kind,2);cp=model.start(ctx);whole=model.advance_chunk(ctx,cp,2)
    first=model.advance_chunk(ctx,cp,1);second=model.advance_chunk(ctx,first['checkpoint'],1)
    assert whole['status']==second['status']=='completed'and whole['samples']==first['samples']+second['samples']
    assert model.checkpoint_bytes(ctx,whole['checkpoint'])==model.checkpoint_bytes(ctx,second['checkpoint'])


@pytest.mark.parametrize('kind,count,accepted',[('leaf',234,True),('leaf',235,False),('internode',241,True),('internode',242,False)])
def test_remaining_sample_scalar_budget_tracks_new_inventory_without_raising_limit(stored,profiles,kind,count,accepted):
    row=stored[0];root=model.parent.prepare_context(program=row[0].program,step_seconds=.125,step_count=count,**profiles)
    if accepted:
        ctx,kw=prepared((root,*row[1:]),kind);assert model.start(ctx).value['step_index']==0
    else:
        with pytest.raises(model.OrganContinuationHold,match='CAPACITY_HOLD'):prepared((root,*row[1:]),kind)


def test_fixed_parent_checkpoint_handle_cannot_be_used_as_funded_handle(base_context):
    ctx,kw=base_context
    with pytest.raises(model.OrganContinuationHold):model.checkpoint_bytes(ctx,model.parent.start(kw['context']))


@pytest.mark.parametrize('name',['_root','_directories','_selection','_program','_seed','_history','_manifest','root_sha256','_token'])
def test_changed_context_parts_or_wrong_token_are_rejected(base_context,name):
    from dataclasses import replace
    ctx,kw=base_context
    value=object()if name in ('_root','_token')else()if name=='_directories'else'0'*64 if name=='root_sha256'else b'{}'
    with pytest.raises(model.OrganContinuationHold):model.context_bytes(replace(ctx,**{name:value}))


def test_large_owned_leaf_point_context_and_checkpoint_remain_bounded(roots):
    kw=leaf_setup(roots[0],count=125)
    for event in kw['inputs']['events']:event['leaf']['initial_carbon']['value']=.001
    ctx=model.prepare_context(parent_context=kw['context'],raw_parent_checkpoint=kw['raw_checkpoint'],expected_parent_sha256=kw['expected_sha256'],kind='leaf',inputs=kw['inputs'],**{k:kw[k]for k in SOURCE_KEYS})
    assert len(ctx.program['leaves'])==128 and len(model.context_bytes(ctx))<=model.MAX_BYTES
    assert len(model.checkpoint_bytes(ctx,model.start(ctx)))<=model.MAX_CHECKPOINT_BYTES


@pytest.mark.parametrize('kind',['context','checkpoint'])
def test_actual_serialized_size_limits_are_enforced(base_context,monkeypatch,kind):
    ctx,kw=base_context;cp=model.start(ctx);raw=model.checkpoint_bytes(ctx,cp)
    if kind=='context':
        limit=sum(len(getattr(ctx,name))for name in ('_program','_seed','_history','_selection','_manifest'))-1
        monkeypatch.setattr(model,'MAX_BYTES',limit)
        with pytest.raises(model.OrganContinuationHold,match='CAPACITY_HOLD'):model.context_bytes(ctx)
    else:
        monkeypatch.setattr(model,'MAX_CHECKPOINT_BYTES',len(raw)-1)
        with pytest.raises(model.OrganContinuationHold,match='CAPACITY_HOLD'):model.start(ctx)
