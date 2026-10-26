from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from fractions import Fraction

import pytest

from app import crop_funded_complete_prefix as model
from test_crop_funded_fractional_stem_binding import prepared as binding_prepared,declaration
from test_crop_funded_event_time import sources,profiles,ACCESS,TOLERANCE
from test_crop_funded_fractional_continuation import adoption


def frac(value):return Fraction(int(value['numerator']),int(value['denominator']))


def flows(frame):
    cp=frame['evidence']['checkpoint']
    if cp is None:return frame['lifetime_integrated_transfers']
    return cp['lifetime_integrated_transfers']if frame['evidence']['kind']=='fractional_checkpoint'else cp['integrated_transfers']


def snapshot(frame):return frame['snapshot']if frame['evidence']['checkpoint']is None else frame['evidence']['checkpoint']['last_confirmed']


def segment(context,checkpoints):return {'context':context,'checkpoints':checkpoints,'initial_bindings':declaration(context)}


def finish(context,checkpoint):
    values=[checkpoint]
    while frac(values[-1].value['at']['elapsed_seconds_exact'])<512:
        run=model.crop.advance_chunk(context,values[-1],1);assert run['hold']is None;values.append(run['checkpoint'])
    return values


@pytest.fixture(scope='module')
def prepared(binding_prepared):
    context=binding_prepared[1];checkpoints=finish(context,model.crop.start(context))
    appended={}
    for index in [0,1,len(checkpoints)-1]:
        cp=checkpoints[index];value=adoption(context,cp,'complete-'+str(index))
        value['events'][0]['attachment_internode_id']=binding_prepared[-1]['internode_id']
        ctx=model.crop.adopt_births(context,cp,value);values=finish(ctx,model.crop.start(ctx))
        appended[index]=[segment(context,checkpoints[:index+1]),segment(ctx,values)]
    return {'one':[segment(context,checkpoints)],'appended':appended}


def test_actual_original_source_dense_before_after_and_complete_horizon(prepared):
    s=prepared['one'];result=model.bind_complete_trajectory(s);frames=result['frames'];context=s[0]['context'];data=context.value
    left=data['source']['candidate']['source_root_certificate']['source_bracket']['left_frame_index']
    assert result['status']=='completed_software_fixture'and len(frames)==69 and [f['output_cursor']for f in frames]==list(range(1,70))
    assert frames[0]['at']['elapsed_seconds_exact']=={'numerator':'0','denominator':'1','unit':'s'}
    assert [len(f['leaves'])for f in frames[:2]]==[3,4]
    for i,frame in enumerate(frames[:left+1]):
        assert frame['evidence']['kind']=='original_funded_checkpoint'and frame['evidence']['source_frame_index']==i
        cp=frame['evidence']['checkpoint'];assert snapshot(frame)['state']==cp['last_confirmed']['state']
        assert frame['evidence']['checkpoint_sha256']==sha256(model.crop._canonical(cp)).hexdigest()
        assert len(frame['shoot']['internodes'])==3 and frame['shoot']['birth']is None
    before,after=frames[left+1:left+3]
    assert before['phase']=='before_birth'and before['evidence']['kind']=='checked_dense_candidate'
    assert before['evidence']['checkpoint']is None and before['evidence']['checkpoint_sha256']is None
    assert snapshot(before)['state']==data['source']['candidate']['dense_candidate']['state']
    assert before['at']==after['at']and before['shoot']==after['shoot']and len(before['leaves'])==5 and len(after['leaves'])==6
    assert before['leaves']==after['leaves'][:5]
    assert flows(before)=={k:v for k,v in flows(after).items()if not k.startswith('leaf_5_')}
    assert all('lifetime_integrated_transfers'not in f and 'ledgers'not in f for f in frames if f['evidence']['checkpoint']is not None)
    assert all('snapshot'not in f for f in frames if f['evidence']['checkpoint']is not None)
    assert all('area'not in leaf and 'thermal_age'not in leaf and 'carbohydrate'not in leaf for f in frames for leaf in f['leaves'])
    assert frac(after['shoot']['internodes'][-1]['age_exact'])==0
    assert frac(frames[-1]['at']['elapsed_seconds_exact'])==512 and result['current_checkpoint_RHS_evaluations']==34
    assert result['basis']['G0_G4']=='not_assessed'and result['sample_scalars']<=32768


@pytest.mark.parametrize('place',[0,1,33])
def test_actual_same_time_mid_and_horizon_new_contexts_are_one_complete_chain(prepared,place):
    result=model.bind_complete_trajectory(prepared['appended'][place]);frames=result['frames']
    assert len(frames)==70 and [f['output_cursor']for f in frames]==list(range(1,71))
    assert len(frames[-1]['leaves'])==7 and frac(frames[-1]['at']['elapsed_seconds_exact'])==512
    points=[i for i,f in enumerate(frames)if f['evidence']['kind']=='fractional_checkpoint'and f['phase']=='after_birth']
    assert len(points)==2;before,after=frames[points[-1]-1:points[-1]+1]
    assert before['at']==after['at']and before['shoot']==after['shoot']and before['leaves']==after['leaves'][:6]
    assert after['event_sequence']==before['event_sequence']+1 and len(result['segment_receipts'])==2


@pytest.mark.parametrize('kind',['empty','missing-seed','gap','reorder','incomplete','repeated-context','later-first','extra-field'])
def test_missing_reordered_unrelated_or_incomplete_history_is_not_complete(prepared,kind):
    base=prepared['one'][0];values=list(base['checkpoints']);s=[segment(base['context'],values)]
    if kind=='empty':s=[]
    elif kind=='missing-seed':s[0]['checkpoints']=values[1:]
    elif kind=='gap':s[0]['checkpoints']=values[:1]+values[2:]
    elif kind=='reorder':s[0]['checkpoints']=values[:1]+[values[2],values[1]]+values[3:]
    elif kind=='incomplete':s[0]['checkpoints']=values[:-1]
    elif kind=='repeated-context':s=s+s
    elif kind=='later-first':s=[prepared['appended'][1][1]]
    elif kind=='extra-field':s[0]['extra']=True
    with pytest.raises(model.CompletePrefixHold):model.bind_complete_trajectory(s)


def test_changed_initial_links_between_true_adopted_contexts_are_held(prepared):
    old,new=prepared['appended'][1];s=[old,{**new,'initial_bindings':deepcopy(new['initial_bindings'])}]
    s[1]['initial_bindings']['initial_attachments'][0]['attachment_internode_id']='synthetic-initial-1'
    with pytest.raises(model.CompletePrefixHold,match='initial bindings cannot change'):model.bind_complete_trajectory(s)


def test_rehashed_current_checkpoint_cannot_break_actual_prefix_chain(prepared):
    item=prepared['one'][0];cp=item['checkpoints'][1];value=cp.value;value['output_prefix_sha256']='0'*64
    raw=model.crop._canonical(value);changed=replace(cp,_raw=raw,sha256=sha256(raw).hexdigest())
    checkpoints=[item['checkpoints'][0],changed,*item['checkpoints'][2:]]
    with pytest.raises(model.CompletePrefixHold,match='PREFIX_HOLD'):model.bind_complete_trajectory([segment(item['context'],checkpoints)])


def test_original_prefix_has_zero_RHS_and_complete_path_only_current_RHS(prepared,monkeypatch):
    import socket,subprocess,psycopg
    s=prepared['one'];ctx=s[0]['context'];evaluate=model.crop.short._evaluate;calls=[]
    def counted(*a,**k):calls.append(1);return evaluate(*a,**k)
    def forbidden(*a,**k):raise AssertionError('past ODE/clock/initialization/external effect prohibited')
    for owner,name in [(model.crop,'advance_chunk'),(model.crop,'adopt_births'),(model.crop.old,'advance_chunk'),
        (model.crop.old.parent,'prepare_context'),(model.crop.old.parent,'advance_chunk'),
        (model.binding.epochs,'project_funded_shoot_from_stored_state'),(model.binding.length,'advance_rational_internode_thermal_clock'),
        (model.binding.length,'initialize_rational_internode_length'),(socket,'socket'),(subprocess,'Popen'),(psycopg,'connect')]:monkeypatch.setattr(owner,name,forbidden)
    monkeypatch.setattr(model.crop.short,'_evaluate',counted)
    prefix=model.bind_original_prefix(ctx,s[0]['initial_bindings']);assert prefix['status']=='confirmed_prefix_only'and calls==[]
    result=model.bind_complete_trajectory(s);assert len(calls)==result['current_checkpoint_RHS_evaluations']==34


def test_complete_output_cap_and_late_code_hold(prepared,monkeypatch):
    monkeypatch.setattr(model,'MAX_BYTES',32)
    with pytest.raises(model.CompletePrefixHold,match='CAPACITY_HOLD'):model.bind_original_prefix(prepared['one'][0]['context'],prepared['one'][0]['initial_bindings'])
    monkeypatch.setattr(model,'MAX_BYTES',2*1024**2);monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    with pytest.raises(model.CompletePrefixHold,match='CODE_HOLD'):model.bind_complete_trajectory(prepared['one'])
