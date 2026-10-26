from copy import deepcopy
from hashlib import sha256
from fractions import Fraction

import pytest

from app import crop_funded_fractional_continuation as model
from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
from test_crop_leaf_funded_birth_artifact import calculated_inputs, profiles
from test_crop_leaf_carbon_stock_artifact import encoded, ACCESS
from test_crop_funded_event_time import sources, TOLERANCE
from test_crop_funded_fractional_birth_point import contexts as point_contexts, inputs as point_inputs


@pytest.fixture(scope='module')
def prepared(point_contexts, sources, profiles, tmp_path_factory):
    result = {name: model.prepare_context(point_context=ctx, inputs=point_inputs(ctx)) for name, ctx in point_contexts.items()}
    directory = tmp_path_factory.mktemp('fractional-long-source')/'leaf'
    v, _ = calculated_inputs(profiles, steps=(0,16), dt=8, count=64)
    v['time_origin_utc'] = '2026-10-01T07:00:00Z'
    root = produce_funded_leaf_artifact(directory, ACCESS, inputs_raw=encoded(v), **profiles)
    context = model.birth.prepare_fractional_birth_context(directory,sources[0]/'stem',ACCESS,
        leaf_root_sha256=root,stem_root_sha256=sources[1],stem_start_index=0,bracket_index=0,
        time_tolerance_seconds_exact=TOLERANCE)
    result['long'] = model.prepare_context(point_context=context, inputs=point_inputs(context))
    return result


def frac(row): return Fraction(int(row['numerator']),int(row['denominator']))


def adoption(context, checkpoint, suffix, count=1):
    p = context.value['program']; events = []
    for i in range(count):
        leaf = deepcopy(p['leaves'][0]); leaf.update(leaf_id=f'resume-leaf-{suffix}-{i}',
            thermal_age={'value':0.,'unit':'degC_day'},initial_area=model.short.old.leaf_area._area_at(Fraction(0),leaf['curve']),
            initial_carbon={'value':.25,'unit':model.birth.point.MASS})
        events.append({'event_id':f'resume-event-{suffix}-{i}','attachment_internode_id':f'declared-{suffix}-{i}',
            'incoming_temperature':{'value':22.,'unit':'degC'},'leaf':leaf})
    return {'schema_version':'fractional-continuation-birth-input-v1','input_id':'continued-point-'+suffix,
        'origin':'synthetic','policy':model.birth.point.POLICY,'context_sha256':context.sha256,
        'checkpoint_sha256':checkpoint.sha256,'at_elapsed_seconds_exact':deepcopy(checkpoint.value['at']['elapsed_seconds_exact']),
        'model_floor_area':deepcopy(p['model_floor_area']),'events':events}


@pytest.mark.parametrize('name',['leaf','root-leaf','long'])
def test_real_fractional_seed_remainder_cursor_births_and_both_ledger_scopes(prepared,name):
    context=prepared[name];data=context.value;cp=model.start(context);before=cp.value
    at=frac(before['at']['elapsed_seconds_exact']);dt=Fraction.from_float(data['original']['grid_step_seconds'])
    assert at.denominator>1 and before['phase']=='after_birth' and before['segment_steps']==0
    assert before['output_cursor']==data['original']['left_checkpoint']['output_cursor']+2
    assert before['last_confirmed']==data['seed']['sample'] and before['last_confirmed']['state'][107+len(data['program']['leaves'])-1]==0.
    result=model.advance_chunk(context,cp,1);assert result['hold']is None and len(result['samples'])==1
    after=result['checkpoint'].value
    assert frac(after['at']['elapsed_seconds_exact'])==dt*(int(at//dt)+1)
    assert after['segment_steps']==after['branch_steps']==1 and after['phase']=='grid_endpoint'
    assert after['output_cursor']==before['output_cursor']+1 and after['output_prefix_sha256']!=before['output_prefix_sha256']
    assert result['new_RHS_evaluations']==4 and result['checkpoint_validation_RHS_evaluations']==1
    for prefix in ('branch','global'):
        for key,quantity in after[prefix+'_balance_residuals'].items():
            assert abs(quantity['value'])<=after[prefix+'_balance_budgets'][key]['value']
    assert after['lifetime_point_transfers']==before['lifetime_point_transfers']
    assert context.value==data


def test_all_chunk_groupings_and_restored_current_CPs_have_identical_final_bytes(prepared):
    context=prepared['long'];outputs=[]
    for groups in ([128],[1]*33,[2,3,7,21],[3,4,5,8,13]):
        cp=model.start(context)
        for budget in groups:
            result=model.advance_chunk(context,cp,budget);assert result['hold']is None;cp=result['checkpoint']
            raw=model.checkpoint_bytes(context,cp)
            cp=model.restore_checkpoint(context,raw,expected_sha256=sha256(raw).hexdigest())
        assert result['status']=='completed' and frac(cp.value['at']['elapsed_seconds_exact'])==512
        outputs.append(cp._raw)
    assert len(set(outputs))==1
    with pytest.raises(model.FractionalContinuationHold,match='horizon exhausted'):
        model.advance_chunk(context,cp,1)


def test_context_restore_has_no_RHS_point_initialization_or_past_advance(prepared,monkeypatch):
    context=prepared['long'];raw=model.context_bytes(context)
    def forbidden(*a,**k):raise AssertionError('frozen context restoration has no model work')
    for owner,name in ((model.short,'_evaluate'),(model.birth.point,'_new_leaf'),
        (model.short.old.leaf_area,'initialize_leaf_area'),(model.old,'advance_chunk'),
        (model.old.parent,'prepare_context'),(model.old.parent,'advance_chunk')):
        monkeypatch.setattr(owner,name,forbidden)
    restored=model.restore_context(context._leaf_directory,context._stem_directory,context._access,
        raw_bytes=raw,expected_sha256=sha256(raw).hexdigest())
    assert restored._raw==raw and restored.sha256==context.sha256


def test_CP_restore_evaluates_only_current_RHS_once(prepared,monkeypatch):
    context=prepared['long'];cp=model.advance_chunk(context,model.start(context),2)['checkpoint'];raw=cp._raw
    evaluate=model.short._evaluate;calls=[]
    def counted(*a,**k):calls.append(1);return evaluate(*a,**k)
    monkeypatch.setattr(model.short,'_evaluate',counted)
    restored=model.restore_checkpoint(context,raw,expected_sha256=sha256(raw).hexdigest())
    assert restored._raw==raw and calls==[1]


@pytest.mark.parametrize('kind',['origin','at-extra'])
def test_continued_checkpoint_keeps_closed_original_UTC_origin(prepared,kind):
    context=prepared['long'];cp=model.advance_chunk(context,model.start(context),1)['checkpoint'];value=cp.value
    if kind=='origin':value['at']['time_origin_utc']='2026-10-02T07:00:00Z'
    else:value['at']['extra']=True
    raw=model._canonical(value)
    with pytest.raises(model.FractionalContinuationHold):model.restore_checkpoint(context,raw,expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('change',[
    lambda v:v.update(segment_steps=True),lambda v:v.update(phase='root_interval'),
    lambda v:v.update(output_cursor=v['output_cursor']+1),lambda v:v.update(context_sha256='0'*64),
    lambda v:v.update(event_sequence=v['event_sequence']+1),lambda v:v.update(extra=1),
    lambda v:v['at']['elapsed_seconds_exact'].update(numerator='1'),
    lambda v:v['last_confirmed']['state'].pop(),lambda v:v['last_confirmed']['state'].__setitem__(0,True),
    lambda v:v['last_confirmed']['state'].__setitem__(0,v['last_confirmed']['state'][0]+1),
    lambda v:v['segment_integrated_transfers']['photosynthesis'].update(value=v['segment_integrated_transfers']['photosynthesis']['value']+1),
    lambda v:v['global_balance_budgets']['carbohydrate'].update(value=1e20),
    lambda v:v['lifetime_point_transfers']['growth_respiration'].update(value=99.),
])
def test_rehashed_malformed_current_CP_rejects(prepared,change):
    context=prepared['long'];cp=model.start(context);value=deepcopy(cp.value);change(value);raw=model._canonical(value)
    with pytest.raises(model.FractionalContinuationHold):model.restore_checkpoint(context,raw,expected_sha256=sha256(raw).hexdigest())
    assert model.start(context)._raw==cp._raw


@pytest.mark.parametrize('kind',['wrong-hash','noncanonical','code','original','zero-prefix','source-index','profile','size'])
def test_external_context_digest_version_source_and_limits(prepared,monkeypatch,kind):
    context=prepared['long'];data=context.value;raw=context._raw;expected=context.sha256
    if kind=='wrong-hash':expected='0'*64
    elif kind=='noncanonical':raw=raw+b' ';expected=sha256(raw).hexdigest()
    elif kind=='size':monkeypatch.setattr(model,'MAX_CONTEXT_BYTES',32)
    else:
        if kind=='code':data['code_sha256'][next(iter(data['code_sha256']))]='0'*64
        elif kind=='original':data['original']['root_sample']['state'][0]+=1
        elif kind=='source-index':data['source']['candidate']['source_root_certificate']['source_bracket']['left_frame_index']=10**9
        elif kind=='profile':data['source']['profile_sha256']['growth_profile']='0'*64
        else:data['seed']['branch_base_transfers']['photosynthesis']['value']=1.
        raw=model._canonical(data);expected=sha256(raw).hexdigest()
    with pytest.raises(model.FractionalContinuationHold):
        model.restore_context(context._leaf_directory,context._stem_directory,context._access,raw_bytes=raw,expected_sha256=expected)


@pytest.mark.parametrize('place',[0,1,5,33])
def test_same_time_mid_and_horizon_points_preserve_continuous_prefix_and_reject_repeat(prepared,place):
    context=prepared['long'];cp=model.start(context)
    if place:cp=model.advance_chunk(context,cp,place)['checkpoint']
    old=cp.value;v=adoption(context,cp,'next-'+str(place),2);new=model.adopt_births(context,cp,v);next_cp=model.start(new);after=next_cp.value
    assert after['at']==old['at'] and after['phase']=='after_birth' and after['segment_steps']==0
    assert after['branch_steps']==old['branch_steps'] and after['output_cursor']==old['output_cursor']+1
    assert after['event_sequence']==old['event_sequence']+1
    for name,row in old['branch_integrated_transfers'].items():assert after['branch_integrated_transfers'][name]==row
    for name,row in old['lifetime_integrated_transfers'].items():assert after['lifetime_integrated_transfers'][name]==row
    assert model.adopt_births(context,cp,v)._raw==new._raw
    repeat=adoption(new,next_cp,'next-'+str(place),2)
    with pytest.raises(model.FractionalContinuationHold,match='EVENT_HOLD'):model.adopt_births(new,next_cp,repeat)
    if place<33:
        final=model.advance_chunk(new,next_cp,128);assert final['status']=='completed'
    else:
        with pytest.raises(model.FractionalContinuationHold,match='horizon exhausted'):model.advance_chunk(new,next_cp,1)


def test_multiple_new_contexts_carry_all_birth_bases_and_restore_without_replay(prepared):
    ctx=prepared['long'];cp=model.start(ctx)
    for i in range(3):
        if i:cp=model.advance_chunk(ctx,cp,1)['checkpoint']
        ctx=model.adopt_births(ctx,cp,adoption(ctx,cp,str(i)));cp=model.start(ctx)
        raw=model.context_bytes(ctx);ctx=model.restore_context(ctx._leaf_directory,ctx._stem_directory,ctx._access,raw_bytes=raw,expected_sha256=sha256(raw).hexdigest())
        cp=model.restore_checkpoint(ctx,cp._raw,expected_sha256=cp.sha256)
    result=model.advance_chunk(ctx,cp,128);assert result['status']=='completed'
    assert len(ctx.value['records'])==4 and len(ctx.value['program']['leaves'])==9


def test_failure_returns_only_confirmed_prefix_counts_failed_RHS_and_keeps_original_CP(prepared,monkeypatch):
    ctx=prepared['long'];cp=model.start(ctx);before=cp._raw;expected=model.advance_chunk(ctx,cp,1)['checkpoint'].value
    evaluate=model.short._evaluate;calls=[]
    def failing(*a,**k):
        calls.append(1)
        if len(calls)==7:raise ValueError('DOMAIN_HOLD: injected next k3')
        return evaluate(*a,**k)
    monkeypatch.setattr(model.short,'_evaluate',failing)
    result=model.advance_chunk(ctx,cp,4)
    assert result['status']=='hold' and result['checkpoint']is None and result['hold']['stage']=='k3'
    assert result['last_confirmed']==expected and len(result['samples'])==1 and result['new_RHS_evaluations']==6
    assert cp._raw==before


@pytest.mark.parametrize('budget',[0,129,True,1.5])
def test_invalid_chunk_budgets(prepared,budget):
    with pytest.raises(model.FractionalContinuationHold):model.advance_chunk(prepared['long'],model.start(prepared['long']),budget)


def test_no_old_grid_operator_history_reprepare_DB_CLI_network_or_writes(prepared,monkeypatch):
    import os,socket,subprocess,psycopg
    context=prepared['long'];cp=model.start(context)
    def forbidden(*a,**k):raise AssertionError('no past work, writes or fake old-grid context')
    for owner,name in ((model.old,'advance_chunk'),(model.old.parent,'prepare_context'),(model.old.parent,'advance_chunk'),
        (model.birth.point,'_apply_current'),(model.birth.point,'apply_births'),(subprocess,'Popen'),(socket,'socket'),(psycopg,'connect')):
        monkeypatch.setattr(owner,name,forbidden)
    opened=os.open
    def readonly(path,flags,*a,**k):
        if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return forbidden()
        return opened(path,flags,*a,**k)
    monkeypatch.setattr(os,'open',readonly)
    assert model.advance_chunk(context,cp,1)['status']=='yielded'
