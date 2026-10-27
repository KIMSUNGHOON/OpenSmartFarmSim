from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from types import MappingProxyType
import json,weakref,gc

import pytest

from app import crop_organ_repeat as model
from app import crop_organ_repeat_proofs as proofs
from test_crop_organ_repeat import adopt, row, inputs, pending, short_event_context, captured, candidates, crossings, contexts, roots, stored, profiles, TOLERANCE


@pytest.fixture(scope='module')
def initial(row):return adopt(row)


@pytest.mark.parametrize('kind',['program','schedule','global_budget','sample','origin','receipt','extra'])
def test_rehashed_context_and_source_changes_reject(initial,kind):
    value=initial.value
    if kind=='program':value['seed']['program']['leaves'][0]['leaf_id']+='-forged'
    elif kind=='schedule':value['seed']['schedule']['next_sequence']+=1
    elif kind=='global_budget':value['seed']['global_ledgers']['carbohydrate']['budget_exact']['numerator']+='0'
    elif kind=='sample':value['initial_sample']['state'][0]+=1
    elif kind=='origin':value['origin_context_sha256']='0'*64
    elif kind=='receipt':value['receipt_sha256'][0]='0'*64
    else:value['extra']=True
    raw=model._canonical(value)
    with pytest.raises(model.RepeatHold):model.restore_context(initial._origin,raw,expected_sha256=sha256(raw).hexdigest(),receipt_bytes=model.proof_bytes(initial))


@pytest.mark.parametrize('kind',['state','program','cost','budget','event','dense'])
def test_rehashed_material_receipt_cannot_change_adopted_meaning(initial,kind):
    receipt=json.loads(model.proof_bytes(initial)[0]);value=initial.value
    if kind=='state':receipt['after_state'][0]+=1
    elif kind=='program':receipt['after_program']['leaves'][-1]['leaf_id']+='-forged'
    elif kind=='cost':receipt['flow_components']['internode']['buffer_debit']['value']+=1
    elif kind=='budget':receipt['point_balances']['whole_carbohydrate']['budget_exact']['numerator']+='0'
    elif kind=='event':receipt['source_event']['sequence']+=1
    else:receipt['before_candidate']['dense_candidate']['state'][0]+=1
    receipt['calculation_sha256']=model.stock._hash({k:v for k,v in receipt.items()if k!='calculation_sha256'})
    encoded=model._canonical(receipt);value['receipt_sha256']=[sha256(encoded).hexdigest()];raw=model._canonical(value)
    with pytest.raises(model.RepeatHold):model.restore_context(initial._origin,raw,expected_sha256=sha256(raw).hexdigest(),receipt_bytes=(encoded,))


@pytest.mark.parametrize('kind',['state','time','schedule','cursor','prefix','seed','flow','budget','version'])
def test_rehashed_checkpoint_changes_reject_even_with_warm_context(initial,kind):
    value=model.start(initial).value
    if kind=='state':value['last_confirmed']['state'][0]+=1
    elif kind=='time':value['at']['elapsed_seconds_exact']['numerator']+='0'
    elif kind=='schedule':value['schedule']['next_sequence']+=1
    elif kind=='cursor':value['output_cursor']+=1
    elif kind=='prefix':value['output_prefix_sha256']='0'*64
    elif kind=='seed':value['source_seed_sha256']='0'*64
    elif kind=='flow':value['branch_integrated_transfers']['photosynthesis']['unit']='g_DM/plant'
    elif kind=='budget':value['global_ledgers']['carbohydrate']['budget_exact']['numerator']+='0'
    else:value['version']=model.legacy.CHECKPOINT_VERSION
    raw=model._canonical(value)
    with pytest.raises(model.RepeatHold):model.restore_checkpoint(initial,raw,expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('kind',['context','CP','proof_total','receipt','event_count','mutable_proof'])
def test_limits_are_enforced_before_rhs(initial,monkeypatch,kind):
    raw=model.context_bytes(initial);receipt=model.proof_bytes(initial);cp=model.start(initial);cpraw=model.checkpoint_bytes(initial,cp)
    def forbidden(*args,**kw):raise AssertionError('invalid bound must not calculate')
    monkeypatch.setattr(model.stock.short,'_evaluate',forbidden)
    if kind=='context':monkeypatch.setattr(model,'MAX_BYTES',len(raw)-1)
    elif kind=='CP':monkeypatch.setattr(model,'MAX_CHECKPOINT_BYTES',len(cpraw)-1)
    elif kind=='proof_total':monkeypatch.setattr(model,'MAX_PROOF_BYTES',sum(map(len,receipt))-1)
    elif kind=='receipt':monkeypatch.setattr(model,'MAX_BYTES',len(receipt[0])-1)
    elif kind=='event_count':monkeypatch.setattr(model,'MAX_EVENTS',0)
    else:receipt=(bytearray(receipt[0]),)
    with pytest.raises(model.RepeatHold):
        if kind=='CP':model.restore_checkpoint(initial,cpraw,expected_sha256=cp.sha256)
        else:model.restore_context(initial._origin,raw,expected_sha256=initial.root_sha256,receipt_bytes=receipt)


@pytest.mark.parametrize('stage',[1,2,3,4])
def test_failed_second_interval_exposes_only_first_confirmed_prefix(initial,monkeypatch,stage):
    cp=model.start(initial);first=model.advance_chunk(initial,cp,1);evaluate=model.stock.short._evaluate;calls=[]
    def failed(*args,**kw):
        calls.append(1)
        if len(calls)==5+stage:raise ValueError('DOMAIN_HOLD: explicit repeat stage failure')
        return evaluate(*args,**kw)
    monkeypatch.setattr(model.stock.short,'_evaluate',failed)
    result=model.advance_chunk(initial,cp,3)
    assert result['status']=='hold'and result['checkpoint']is None and result['samples']==first['samples']and result['last_confirmed']==first['last_confirmed']
    assert result['new_RHS_evaluations']==4+stage and len(calls)==5+stage


@pytest.mark.parametrize('kind',['profile','rights','code','context','runtime'])
def test_current_source_fences_remain_active_with_warm_validation(initial,monkeypatch,kind):
    model.context_bytes(initial);cp=model.start(initial);evaluate=model.stock.short._evaluate;calls=[]
    profile=initial._source._root._profiles[0];original=profile.values;raw=initial._raw
    binding=model.stock.leaf.binding.bind_initial_stem_carbon
    def changed_binding(*args,**kw):
        result=binding(*args,**kw)
        if kind=='rights'and len(calls)>=5:result['source_rights']['stem']['display']=False
        return result
    def changed(*args,**kw):
        calls.append(1)
        if kind=='runtime'and len(calls)==5:raise RuntimeError('unexpected repeat failure')
        result=evaluate(*args,**kw)
        if len(calls)==5:
            if kind=='profile':
                values=dict(original);key=next(iter(values));values[key]+=.001;object.__setattr__(profile,'values',MappingProxyType(values))
            elif kind=='code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
            elif kind=='context':object.__setattr__(initial,'_raw',b'{}')
        return result
    monkeypatch.setattr(model.stock.short,'_evaluate',changed);monkeypatch.setattr(model.stock.leaf.binding,'bind_initial_stem_carbon',changed_binding)
    try:
        with pytest.raises(RuntimeError if kind=='runtime'else model.RepeatHold):model.advance_chunk(initial,cp,1)
    finally:
        object.__setattr__(profile,'values',original);object.__setattr__(initial,'_raw',raw)


def test_immutable_verification_is_reused_but_new_restored_handles_get_full_algebra(initial,monkeypatch):
    calls=[];validate=proofs.validate
    def counted(*args,**kw):calls.append(1);return validate(*args,**kw)
    monkeypatch.setattr(proofs,'validate',counted)
    restored=model.restore_context(initial._origin,model.context_bytes(initial),expected_sha256=initial.root_sha256,receipt_bytes=model.proof_bytes(initial))
    assert len(calls)==len(initial._receipts)
    for _ in range(3):model.context_bytes(restored);model.start(restored)
    assert len(calls)==len(initial._receipts)
    reference=weakref.ref(restored);del restored;gc.collect();assert reference()is None


def test_advanced_raw_checkpoint_restores_current_only_and_resumes_identically(initial,monkeypatch):
    current=model.advance_chunk(initial,model.start(initial),3)['checkpoint'];assert current is not None
    raw=model.checkpoint_bytes(initial,current);expected=model.advance_chunk(initial,current,1)['checkpoint'];assert expected is not None
    evaluate=model.stock.short._evaluate;calls=[]
    def counted(*args,**kw):calls.append(1);return evaluate(*args,**kw)
    def forbidden(*args,**kw):raise AssertionError('advanced restore must not replay prior points or initialize organs')
    for owner,name in [(model.material.stem,'_jump'),(model.material.leaf,'_jump'),
            (model.stock.short.old.leaf_area,'initialize_leaf_area'),(model.stock,'adopt_births')]:monkeypatch.setattr(owner,name,forbidden)
    monkeypatch.setattr(model.stock.short,'_evaluate',counted)
    restored=model.restore_checkpoint(initial,raw,expected_sha256=current.sha256)
    assert model.checkpoint_bytes(initial,restored)==raw and calls==[1]
    continued=model.advance_chunk(initial,restored,1)['checkpoint'];assert continued is not None
    assert len(calls)==6 and model.checkpoint_bytes(initial,continued)==model.checkpoint_bytes(initial,expected)


def test_all_four_endpoint_partitions_keep_identical_remainder_samples_flows_books_and_bytes(initial):
    expected=model.advance_chunk(initial,model.start(initial),4);assert expected['checkpoint']is not None
    for mask in range(8):
        parts=[];previous=0
        for cut in range(1,4):
            if mask & (1 << (cut-1)):parts.append(cut-previous);previous=cut
        parts.append(4-previous);cp=model.start(initial);samples=[];intervals=[]
        for count in parts:
            out=model.advance_chunk(initial,cp,count);assert out['checkpoint']is not None
            cp=out['checkpoint'];samples.extend(out['samples']);intervals.extend(out['intervals'])
        assert samples==expected['samples']and intervals==expected['intervals']
        assert model.checkpoint_bytes(initial,cp)==model.checkpoint_bytes(initial,expected['checkpoint'])
