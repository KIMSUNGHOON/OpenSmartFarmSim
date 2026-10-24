from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json

import pytest

from app import crop_growing_geometry_post_removal_context as model
from app import crop_growing_geometry_leaf_removal_point as point
from app import crop_growing_geometry_continuation as parent
from test_growing_geometry_leaf_removal_point import samples,profiles,declaration


def capture(ctx,cp,indices=(0,)):
    return model.prepare_context(parent_context=ctx,raw_parent_checkpoint=cp._raw,
        expected_parent_sha256=cp.sha256,inputs=declaration(ctx,cp,indices))


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('position',range(3))
@pytest.mark.parametrize('indices',[(0,),(0,2)])
def test_capture_preserves_source_state_original_anchors_and_ledgers(samples,case,position,indices):
    ctx,points=samples[case];cp=points[position];current=capture(ctx,cp,indices);stored=model.snapshot(current)
    saved=stored.value;original=cp.value;result=current.point_result;keep=result['after']['original_leaf_indices']
    assert saved['phase']=='after_removal_before_next_step'and saved['segment_step_index']==0
    assert saved['original_global_step_index']==original['step_index']
    assert saved['at_elapsed_seconds_exact']==result['at_elapsed_seconds_exact']
    assert saved['last_confirmed']['state']==result['after']['state']
    assert saved['last_confirmed']['elapsed_seconds']==original['last_confirmed']['elapsed_seconds']
    for key,value in result['after'].items():
        if key in ('leaf_area_index','canopy_temperature'):assert saved['last_confirmed']['derived'][key]==value
    assert saved['last_confirmed']['derived']['canopy_capacity']==result['after']['capacity']
    seed=json.loads(ctx._seed);assert saved['original_curve_invariant']==seed['evaluation']['curve_residuals']
    assert saved['active_original_curve_invariant']==[seed['evaluation']['curve_residuals'][i]for i in keep]
    assert saved['original_initial_area_receipts']==seed['initial_area_receipts']
    assert saved['original_interval_transfers']==original['integrated_transfers']
    assert saved['point_outflows']==result['point_outflows']
    assert saved['removed_last_states']==result['removed_last_states']
    assert all(q['value']==0 for q in saved['segment_integrated_transfers'].values())
    assert list(saved['segment_integrated_transfers'])==sorted(parent.short.FLUX_UNITS)
    normalized=json.loads(ctx._program)
    assert current.active_program=={**normalized,'leaves':[normalized['leaves'][i]for i in keep]}
    assert current.manifest['state_layout']['leaf_ids']==result['after']['leaf_ids']
    assert current.manifest['numerical']['remaining_steps']==16-original['step_index']
    assert current.manifest['parent_checkpoint_sha256']==cp.sha256
    assert current.manifest['point_calculation_sha256']==result['calculation_sha256']
    raw=model.checkpoint_bytes(current,stored)
    assert model.restore_checkpoint(current,raw,expected_sha256=stored.sha256).value==saved
    assert capture(ctx,cp,indices).root_sha256==current.root_sha256


def test_reads_never_reapply_point_normalize_or_evaluate(samples,monkeypatch):
    ctx,points=samples[0];current=capture(ctx,points[1]);stored=model.snapshot(current);raw=stored._raw
    def forbidden(*a,**k):raise AssertionError('snapshot/restore cannot calculate or advance')
    for owner,name in [(point,'apply_removals'),(parent,'restore_checkpoint'),(parent,'prepare_context'),
        (parent,'start'),(parent,'advance_chunk'),(parent.short,'_prepare'),(parent.short,'_evaluate'),(parent.short,'integrate')]:
        monkeypatch.setattr(owner,name,forbidden)
    assert model.snapshot(current)._raw==raw
    assert model.checkpoint_bytes(current,stored)==raw
    assert model.restore_checkpoint(current,raw,expected_sha256=stored.sha256)._raw==raw


def test_prepare_uses_point_once_and_only_two_current_rhs_evaluations(samples,monkeypatch):
    ctx,points=samples[0];calls={'point':0,'rhs':0};old_point=point.apply_removals;old_rhs=parent.short._evaluate
    def observed_point(*a,**k):calls['point']+=1;return old_point(*a,**k)
    def observed_rhs(*a,**k):calls['rhs']+=1;return old_rhs(*a,**k)
    def forbidden(*a,**k):raise AssertionError('cannot normalize or advance')
    monkeypatch.setattr(point,'apply_removals',observed_point);monkeypatch.setattr(parent.short,'_evaluate',observed_rhs)
    for owner,name in [(parent,'prepare_context'),(parent,'start'),(parent,'advance_chunk'),(parent.short,'_prepare'),(parent.short,'integrate')]:monkeypatch.setattr(owner,name,forbidden)
    current=capture(ctx,points[1]);stored=model.snapshot(current)
    model.restore_checkpoint(current,stored._raw,expected_sha256=stored.sha256)
    assert calls=={'point':1,'rhs':2}


@pytest.mark.parametrize('mutation',[
    lambda x:x.update(phase='before_removal'),lambda x:x.update(segment_step_index=1),
    lambda x:x.update(original_global_step_index=0),lambda x:x.update(context_sha256='0'*64),
    lambda x:x['last_confirmed']['state'].__setitem__(-1,1),
    lambda x:x['last_confirmed']['derived']['leaf_area_index'].update(unit='mg_CH2O'),
    lambda x:x['at_elapsed_seconds_exact'].update(numerator='1'),
    lambda x:x['active_original_curve_invariant'][0].update(value=1),
    lambda x:x['point_outflows']['carbohydrate'].update(value=0),
    lambda x:x['original_interval_transfers']['photosynthesis'].update(value=0),
    lambda x:x['segment_integrated_transfers']['photosynthesis'].update(value=1),
    lambda x:x['removed_last_states'].clear(),lambda x:x.update(extra=True),
])
def test_rehashed_changed_checkpoint_is_rejected(samples,mutation):
    ctx,points=samples[0];current=capture(ctx,points[1]);stored=model.snapshot(current);value=stored.value
    mutation(value);raw=parent._canonical(value)
    with pytest.raises(model.PostRemovalContextHold):model.restore_checkpoint(current,raw,expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('part',['_program','_seed','_point','_parent_checkpoint','_manifest'])
def test_immutable_context_part_changes_are_rejected(samples,part):
    ctx,points=samples[0];current=capture(ctx,points[1]);bad=replace(current,**{part:getattr(current,part)+b' '})
    with pytest.raises(model.PostRemovalContextHold):model.snapshot(bad)


def test_json_views_are_copies_and_models_cannot_be_interchanged(samples):
    ctx,points=samples[0];current=capture(ctx,points[1]);stored=model.snapshot(current);raw=stored._raw
    current.active_program['leaves'].clear();current.manifest['numerical']['remaining_steps']=999
    current.point_result['after']['state'].clear();stored.value['point_outflows'].clear()
    assert model.snapshot(current)._raw==raw
    with pytest.raises(parent.ContinuationRejected):parent.restore_checkpoint(ctx,raw,expected_sha256=stored.sha256)
    with pytest.raises(model.PostRemovalContextHold):model.snapshot(ctx)
    with pytest.raises(model.PostRemovalContextHold):model.checkpoint_bytes(current,points[1])


def test_checkpoint_bytes_cannot_override_current_handle_integrity(samples):
    ctx,points=samples[0];current=capture(ctx,points[1]);stored=model.snapshot(current)
    changed=stored._raw+b' ';bad=replace(stored,_raw=changed,sha256=sha256(changed).hexdigest())
    with pytest.raises(model.PostRemovalContextHold):model.checkpoint_bytes(current,bad)
    with pytest.raises(model.PostRemovalContextHold):model.restore_checkpoint(current,stored._raw,expected_sha256='0'*64)


@pytest.mark.parametrize('fault',['code','point_code','parent_code','profile','environment','token','oversize','other_parent'])
def test_identity_scope_and_capacity_are_enforced(samples,monkeypatch,fault):
    ctx,points=samples[0];current=capture(ctx,points[1])
    if fault=='code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    if fault=='point_code':monkeypatch.setattr(point,'CODE_SHA256','0'*64)
    if fault=='parent_code':monkeypatch.setattr(parent,'CODE_SHA256','0'*64)
    if fault=='profile':current=replace(current,_parent=replace(ctx,_profiles=tuple(reversed(ctx._profiles))))
    if fault=='environment':monkeypatch.setattr(parent.platform,'machine',lambda:'different-machine')
    if fault=='token':current=replace(current,_token=object())
    if fault=='oversize':current=replace(current,_seed=b' '*(2*1024**2))
    if fault=='other_parent':current=replace(current,_parent=samples[1][0])
    with pytest.raises(model.PostRemovalContextHold):model.snapshot(current)


def test_current_area_is_not_snapped_to_canonical_curve(samples):
    ctx,points=samples[0];cp=points[1];current=capture(ctx,cp);stored=model.snapshot(current)
    keep=current.point_result['after']['original_leaf_indices'];old=cp.value['last_confirmed']['state']
    areas=stored.value['last_confirmed']['state'][108+len(keep):]
    assert areas==[old[111+i]for i in keep]
    assert stored.value['last_confirmed']['curve_invariant_changes']==[
        cp.value['last_confirmed']['curve_invariant_changes'][i]for i in keep]


@pytest.mark.parametrize('field',['original_request_sha256','original_program_sha256','original_seed_sha256','point_input_sha256'])
def test_rehashed_context_cannot_relabel_original_sources(samples,field):
    ctx,points=samples[0];current=capture(ctx,points[1]);m=current.manifest;m[field]='0'*64
    raw=parent._canonical(m);changed=replace(current,_manifest=raw,root_sha256=sha256(raw).hexdigest())
    with pytest.raises(model.PostRemovalContextHold,match='source bindings'):model.snapshot(changed)


def test_rehashed_seed_cannot_override_checkpoint_metadata(samples):
    ctx,points=samples[0];current=capture(ctx,points[1]);seed=json.loads(current._seed);seed['phase']='invented'
    raw=parent._canonical(seed);m=current.manifest;m['seed_sha256']=sha256(raw).hexdigest();manifest=parent._canonical(m)
    changed=replace(current,_seed=raw,_manifest=manifest,root_sha256=sha256(manifest).hexdigest())
    with pytest.raises(model.PostRemovalContextHold,match='closed manifest'):model.snapshot(changed)


@pytest.mark.parametrize('error_type',[parent.short.GrowingGeometryHold,parent.short.joint.ExplicitLaiClimateHold])
def test_post_removal_rhs_failure_does_not_create_partial_context(samples,monkeypatch,error_type):
    ctx,points=samples[0];cp=points[1];original=parent.short._evaluate;calls=0;saved=cp._raw
    def failure(*a,**k):
        nonlocal calls
        calls+=1
        if calls==2:raise error_type('POST_EVENT_DOMAIN_HOLD')
        return original(*a,**k)
    monkeypatch.setattr(parent.short,'_evaluate',failure)
    with pytest.raises(model.PostRemovalContextHold,match='POST_EVENT_DOMAIN_HOLD'):capture(ctx,cp)
    assert calls==2 and cp._raw==saved


@pytest.mark.parametrize('raw',[b'',b'{}',b'{"x":1,"x":2}',b'{"x":NaN}',b' '* (256*1024+1)])
def test_external_raw_checkpoint_formats_are_rejected(samples,raw):
    ctx,points=samples[0];current=capture(ctx,points[1])
    with pytest.raises(model.PostRemovalContextHold):model.restore_checkpoint(current,raw,expected_sha256=sha256(raw).hexdigest())


def test_own_checkpoint_from_another_context_is_rejected(samples):
    ctx,points=samples[0];one=capture(ctx,points[0]);other=capture(ctx,points[1]);stored=model.snapshot(other)
    with pytest.raises(model.PostRemovalContextHold):model.checkpoint_bytes(one,stored)
    with pytest.raises(model.PostRemovalContextHold):model.restore_checkpoint(one,stored._raw,expected_sha256=stored.sha256)


@pytest.mark.parametrize('limit',['MAX_CONTEXT_BYTES','MAX_CHECKPOINT_BYTES'])
def test_capture_capacity_failure_keeps_original_state(samples,monkeypatch,limit):
    ctx,points=samples[0];cp=points[1];old=cp._raw;monkeypatch.setattr(model,limit,128)
    with pytest.raises(model.PostRemovalContextHold,match='CAPACITY_HOLD'):capture(ctx,cp)
    assert cp._raw==old
