from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from app import crop_growing_geometry_continuation as model
from app import crop_growing_geometry_climate as short
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT=Path(__file__).resolve().parents[2]
CASES=json.loads((ROOT/'fixtures/crop-growing-geometry-climate-reference-v1.json').read_bytes())['cases']


@pytest.fixture(scope='module')
def profiles():
    return {name:kind((ROOT/'fixtures'/file).read_bytes())for name,kind,file in (
        ('growth_profile',Growth,'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile',Cohort,'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile',Transport,'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile',Exchange,'crop-canopy-exchange-reference-parameters-v1.json'))}


@pytest.fixture(scope='module')
def contexts(profiles):
    return [model.prepare_context(program=case['program'],step_seconds=2,step_count=16,**profiles)for case in CASES]


@pytest.fixture(scope='module')
def whole(profiles):return [short.integrate(program=case['program'],step_seconds=2,step_count=16,**profiles)for case in CASES]


def collect(ctx,budget,restore=True):
    cp=model.start(ctx);samples=[cp.value['last_confirmed']];chunks=[]
    while cp.value['step_index']<ctx.manifest['numerical']['step_count']:
        if restore:cp=model.restore_checkpoint(ctx,model.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256)
        result=model.advance_chunk(ctx,cp,budget);assert result['status']!='hold',result['hold']
        samples.extend(result['samples']);chunks.append(result);cp=result['checkpoint']
    return cp,samples,chunks


@pytest.mark.parametrize('case_index',range(6))
@pytest.mark.parametrize('budget',[1,3,128])
def test_all_reference_programs_match_whole_and_other_chunk_groupings(contexts,whole,case_index,budget):
    ctx=contexts[case_index];cp,samples,chunks=collect(ctx,budget);expected=whole[case_index]
    assert samples==expected['samples']
    for name in ('integrated_transfers','balance_residuals','balance_budgets'):assert cp.value[name]==expected[name]
    one,_,_=collect(ctx,128,False)
    assert cp.sha256==one.sha256 and model.checkpoint_bytes(ctx,cp)==model.checkpoint_bytes(ctx,one)
    cursor=1
    for chunk in chunks:
        assert chunk['output_start']==cursor;cursor+=len(chunk['samples'])
        assert chunk['checkpoint_validation_stage_evaluations']==1
        assert chunk['attempted_new_stage_evaluations']==4*len(chunk['samples'])
        assert chunk['scope']=='software_research_only'and chunk['G0_G4']=='not_assessed'


@pytest.mark.parametrize('case_index',range(6))
@pytest.mark.parametrize('cut',range(1,16))
def test_every_single_cut_preserves_all_samples_and_final_bytes(contexts,whole,cut,case_index):
    ctx=contexts[case_index];start=model.start(ctx);first=model.advance_chunk(ctx,start,cut)
    restored=model.restore_checkpoint(ctx,model.checkpoint_bytes(ctx,first['checkpoint']),expected_sha256=first['checkpoint'].sha256)
    last=model.advance_chunk(ctx,restored,128)
    assert [start.value['last_confirmed'],*first['samples'],*last['samples']]==whole[case_index]['samples']
    one=model.advance_chunk(ctx,start,128)
    assert last['checkpoint'].sha256==one['checkpoint'].sha256


def test_restore_and_advance_never_reinitialize_current_area(contexts,whole,monkeypatch):
    ctx=contexts[0];part=model.advance_chunk(ctx,model.start(ctx),9);cp=part['checkpoint']
    raw=model.checkpoint_bytes(ctx,cp);saved=deepcopy(cp.value)
    def forbidden(*args,**kwargs):raise AssertionError('no new initial normalization or monolithic integration')
    monkeypatch.setattr(short,'_prepare',forbidden);monkeypatch.setattr(short,'integrate',forbidden)
    restored=model.restore_checkpoint(ctx,raw,expected_sha256=cp.sha256)
    assert restored.value==saved
    final=model.advance_chunk(ctx,restored,128)
    assert final['last_confirmed']==whole[0]['samples'][-1]


def test_initial_and_completed_checkpoints_roundtrip_but_completion_cannot_advance(contexts):
    ctx=contexts[0];initial=model.start(ctx);complete,_,_=collect(ctx,128)
    for cp in (initial,complete):
        raw=model.checkpoint_bytes(ctx,cp)
        assert model.restore_checkpoint(ctx,raw,expected_sha256=cp.sha256).value==cp.value
    with pytest.raises(model.ContinuationRejected,match='COMPLETED_HOLD'):model.advance_chunk(ctx,complete,1)


def test_program_properties_and_checkpoint_values_are_detached(contexts):
    ctx=contexts[0];cp=model.start(ctx);saved=cp.value
    p=ctx.program;p['leaves'][0]['initial_area']['value']=0
    manifest=ctx.manifest;manifest['numerical']['step_count']=999
    value=cp.value;value['last_confirmed']['state'][111]=0
    assert cp.value==saved and ctx.program==CASES[0]['program']and ctx.manifest['numerical']['step_count']==16


def encoded(payload):return json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


@pytest.mark.parametrize('change',[
    lambda p:p.update(extra=1),lambda p:p.update(version='wrong'),lambda p:p.update(context_sha256='a'*64),
    lambda p:p.update(step_index=True),lambda p:p.update(step_index=-1),lambda p:p.update(output_cursor=0),
    lambda p:p.update(output_prefix_sha256='X'*64),
    lambda p:p['last_confirmed'].update(elapsed_seconds=99),
    lambda p:p['last_confirmed']['state'].pop(),lambda p:p['last_confirmed']['state'].__setitem__(0,1),
    lambda p:p['last_confirmed']['state'].__setitem__(111,0.0),
    lambda p:p['last_confirmed']['derived']['leaf_area_index'].update(value=99),
    lambda p:p['last_confirmed']['curve_invariant_changes'][0].update(value=1),
    lambda p:p['integrated_transfers']['sensible'].update(unit='W/m2_floor'),
    lambda p:p['integrated_transfers']['vapor'].update(value=True),
    lambda p:p['balance_budgets']['carbohydrate'].update(value=1e100)])
def test_changed_closed_checkpoint_shape_state_units_and_derived_are_rejected(contexts,change,monkeypatch):
    ctx=contexts[0];cp=model.advance_chunk(ctx,model.start(ctx),5)['checkpoint'];value=cp.value;change(value);raw=encoded(value)
    def forbidden(*args,**kwargs):raise AssertionError('invalid checkpoint must not advance a step')
    monkeypatch.setattr(short,'_advance',forbidden)
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,raw,expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('kind',['digest','spaces','duplicate','NaN','Infinity','overflow','utf8','size'])
def test_external_bytes_digest_and_canonical_json_fences(contexts,kind):
    ctx=contexts[0];cp=model.start(ctx);raw=model.checkpoint_bytes(ctx,cp);expected=cp.sha256
    if kind=='digest':expected='0'*64
    elif kind=='spaces':raw=json.dumps(cp.value).encode()
    elif kind=='duplicate':raw=b'{"version":"wrong",'+raw[1:]
    elif kind in ('NaN','Infinity','overflow'):raw=b'{"bad":'+{'NaN':b'NaN','Infinity':b'Infinity','overflow':b'1e999'}[kind]+b'}'
    elif kind=='utf8':raw=b'\xff'
    else:raw=b' '*(256*1024+1)
    if kind!='digest':expected=sha256(raw).hexdigest()
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,raw,expected_sha256=expected)


@pytest.mark.parametrize('budget',[0,-1,129,True,1.5,'1'])
def test_step_budget_requires_bounded_integer(contexts,budget):
    ctx=contexts[0]
    with pytest.raises(model.ContinuationRejected,match='BUDGET_HOLD'):model.advance_chunk(ctx,model.start(ctx),budget)


def test_context_profile_code_and_mixed_checkpoint_fences(contexts,monkeypatch):
    ctx=contexts[0];cp=model.start(ctx)
    with pytest.raises(model.ContinuationRejected):model.checkpoint_bytes(contexts[1],cp)
    with pytest.raises(model.ContinuationRejected):model.start(replace(ctx,_profiles=(object(),)*4))
    with pytest.raises(model.ContinuationRejected):model.start(replace(ctx,_token=object()))
    with pytest.raises(model.ContinuationRejected):model.checkpoint_bytes(ctx,replace(cp,_token=object()))
    monkeypatch.setattr(model,'CODE_SHA256','a'*64)
    with pytest.raises(model.ContinuationRejected):model.start(ctx)


def test_domain_hold_preserves_last_confirmed_sample_and_no_checkpoint(profiles):
    p=deepcopy(CASES[0]['program']);p['scenario']['forcing']['canopy_external_heat']['value']=1e7
    ctx=model.prepare_context(program=p,step_seconds=8,step_count=4,**profiles);cp=model.start(ctx)
    result=model.advance_chunk(ctx,cp,2)
    assert result['status']=='hold'and result['checkpoint']is None
    assert result['last_confirmed']==cp.value['last_confirmed']and result['samples']==[]
    assert result['hold']['step_index']==1 and result['hold']['stage']=='k2'


def test_external_crash_is_not_converted_to_normal_hold(contexts,monkeypatch):
    ctx=contexts[0];cp=model.start(ctx)
    def crash(*args,**kwargs):raise RuntimeError('explicit crash')
    monkeypatch.setattr(short,'_advance',crash)
    with pytest.raises(RuntimeError,match='explicit crash'):model.advance_chunk(ctx,cp,1)


@pytest.mark.parametrize('dt,count',[(0,1),(True,1),(1,True),(1,0),(1,4097),(601,1),(.01,4096)])
def test_prepare_rejects_step_and_sample_budget_before_joint_evaluation(dt,count,profiles,monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('invalid budget must not evaluate a joint stage')
    monkeypatch.setattr(short,'_evaluate',forbidden)
    with pytest.raises(model.ContinuationRejected):model.prepare_context(program=CASES[0]['program'],step_seconds=dt,step_count=count,**profiles)


@pytest.mark.parametrize('name',['growth_profile','cohort_profile','transport_profile','exchange_profile'])
def test_prepare_requires_pinned_profile_types(name,profiles):
    with pytest.raises(model.ContinuationRejected):model.prepare_context(program=CASES[0]['program'],step_seconds=2,step_count=16,**{**profiles,name:object()})


@pytest.mark.parametrize('count',[1,512])
def test_large_companion_checkpoint_size_and_original_leaf_order(count,profiles):
    p=deepcopy(CASES[0]['program']);leaf=p['leaves'][0]
    p['leaves']=[{**deepcopy(leaf),'leaf_id':f'checkpoint-leaf-{i}'}for i in range(count)]
    p['model_floor_area']['value']=count*.25/1.33
    ctx=model.prepare_context(program=p,step_seconds=2,step_count=1,**profiles);cp=model.start(ctx)
    raw=model.checkpoint_bytes(ctx,cp);restored=model.restore_checkpoint(ctx,raw,expected_sha256=cp.sha256)
    assert restored.value==cp.value and len(raw)<=256*1024
    assert len(restored.value['last_confirmed']['state'])==108+2*count
    assert ctx.manifest['state_layout']['leaf_ids']==[f'checkpoint-leaf-{i}'for i in range(count)]


def test_changed_request_and_environment_are_rejected(contexts,monkeypatch):
    ctx=contexts[0]
    with pytest.raises(model.ContinuationRejected):model.start(replace(ctx,_request=b'{}'))
    monkeypatch.setattr(model.platform,'python_version',lambda:'different-python')
    with pytest.raises(model.ContinuationRejected,match='changed code/profile/environment'):model.start(ctx)


def test_checkpoint_capacity_hold_keeps_reason_and_uncommitted_endpoint(contexts,monkeypatch):
    ctx=contexts[0];cp=model.start(ctx);original=model._seal
    def bounded(context,payload):
        if payload['step_index']>0:raise model.ContinuationRejected('CAPACITY_HOLD: injected checkpoint byte limit')
        return original(context,payload)
    monkeypatch.setattr(model,'_seal',bounded)
    result=model.advance_chunk(ctx,cp,1)
    assert result['status']=='hold'and result['checkpoint']is None and result['samples']==[]
    assert result['last_confirmed']==cp.value['last_confirmed']and result['hold']['reason'].startswith('CAPACITY_HOLD:')


def test_late_domain_hold_matches_original_last_confirmed_state(profiles):
    p=deepcopy(CASES[0]['program']);p['scenario']['forcing']['canopy_external_heat']['value']=2000
    ctx=model.prepare_context(program=p,step_seconds=4,step_count=8,**profiles)
    result=model.advance_chunk(ctx,model.start(ctx),128)
    with pytest.raises(short.GrowingGeometryHold)as caught:short.integrate(program=p,step_seconds=4,step_count=8,**profiles)
    assert result['status']=='hold'and result['checkpoint']is None and result['samples']
    assert result['last_confirmed']==caught.value.last_confirmed_sample
    assert result['steps']==len(result['samples'])==caught.value.last_confirmed_sample['step_index']
