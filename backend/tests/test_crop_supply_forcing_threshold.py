"""A genuine pending interval, exact root bounds, source fences and no adoption."""
from copy import deepcopy
from decimal import Decimal,localcontext
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_supply_forcing_threshold as model
from app import crop_supply_forcing_owner as owner
from app import crop_supply_forcing_interval as kernel
from app import crop_supply_season as base
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_supply_season import source,q,x,canonical
from test_crop_supply_forcing_owner import origin,setup_owner

TOLERANCE=q(Fraction(1,10**6))


@pytest.fixture(scope='module')
def pending(origin,tmp_path_factory):
    path=tmp_path_factory.mktemp('forcing-threshold')
    ws,definition,document=setup_owner(origin,path,end=536)
    start=owner.open_season(origin['source_ref'],definition,ws)
    result=owner.advance(start,base.AdvanceRequest(q(536),step_budget=10))
    assert result.status=='awaiting_material',result.hold
    assert x(result.handle.current['at']['elapsed_seconds_exact'])==520
    return {'workspace':ws,'definition':definition,'document':document,'start':start,'result':result}


def stored_page(pending):
    return json.loads((pending['workspace'].archive_directory/pending['result'].pending['page_sha256']).read_bytes())


def locate(pending,**kwargs):
    return model.locate_threshold(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,**kwargs)


def test_pending_is_replayed_once_without_history_RHS_or_writes(pending,monkeypatch):
    evaluate=base.stage.evaluate;calls=[]
    def count(*args,**kwargs):calls.append(1);return evaluate(*args,**kwargs)
    monkeypatch.setattr(base.stage,'evaluate',count)
    monkeypatch.setattr(MorphologyBlobStore,'put',lambda *a,**k:pytest.fail('locator wrote a blob'))
    result=locate(pending)
    assert result['status']=='root_located',result.get('hold')
    assert len(calls)==5
    assert result['progress']['past_confirmed_intervals_reintegrated']==0
    assert result['progress']['pending_current_validation_RHS_evaluations']==1
    assert result['progress']['pending_new_RHS_evaluations']==4
    assert result['effective_rights']['redistribute']is False
    assert result['checkpoint_issued']is result['history_committed']is result['material_consumed']is False
    assert result['order']['after_active_forcing_edge']is True
    assert result['order']['next_forcing_relation']=='absent'


def test_independent_decimal_root_and_rounding_difference(pending):
    result=locate(pending);assert result['status']=='root_located',result.get('hold')
    page=stored_page(pending);trace=page['result']['interval'];n=pending['result'].handle.current['numeric']
    with localcontext()as ctx:
        ctx.prec=2200
        def dec(v):
            f=x(v);return Decimal(f.numerator)/Decimal(f.denominator)
        left=dec(trace['left_elapsed_seconds_exact']);dt=dec(trace['step_seconds_exact'])
        a,b,c,d=(Decimal.from_float(row['state'][104])for row in trace['stages'])
        tb=Decimal.from_float(pending['result'].handle.basis['arithmetic_basis']['shoot_base_temperature'])
        age=dec(n['schedule']['age_exact']);threshold=dec(n['schedule']['next_threshold_exact'])
        coefficients=(age-threshold,dt*(a-tb)/86400,dt*(-3*a/2+b+c-d/2)/86400,dt*2*(a-b-c+d)/(3*86400))
        def value(theta):return sum(v*theta**i for i,v in enumerate(coefficients))
        lower,upper=Decimal(0),Decimal(1)
        for _ in range(180):
            middle=(lower+upper)/2
            if value(middle)<0:lower=middle
            else:upper=middle
        root=result['root'];lo=dec(root['lower_elapsed_seconds_exact']);hi=dec(root['upper_elapsed_seconds_exact'])
        assert lo < left+lower*dt <= left+upper*dt <= hi
        assert hi-lo <= dec(TOLERANCE)
        assert abs(value((lo-left)/dt)-dec(root['lower_thermal_residual_exact']))<Decimal('1e-2000')
        assert abs(value((hi-left)/dt)-dec(root['upper_thermal_residual_exact']))<Decimal('1e-2000')
        delta=sum(coefficients)-(dec(page['result']['pending']['right_age_exact'])-threshold)
        assert abs(delta-dec(result['ideal_cubic_minus_accumulated_endpoint_age_exact']))<Decimal('1e-2000')


def test_owner_full_split_same_pending_page_and_location(pending):
    start=pending['start'];first=owner.advance(start,base.AdvanceRequest(q(536),step_budget=1))
    second=owner.advance(first.handle,base.AdvanceRequest(q(536),step_budget=10))
    assert second.status=='awaiting_material'
    assert second.handle.cursor_sha256==pending['result'].handle.cursor_sha256
    assert second.pending['page_sha256']==pending['result'].pending['page_sha256']
    a=locate(pending);b=model.locate_threshold(second.handle,second.pending['page_sha256'],TOLERANCE)
    assert a==b


def test_root_is_proved_before_next_forcing_edge(origin,tmp_path):
    ws,definition,_=setup_owner(origin,tmp_path,edge=528,end=536)
    start=owner.open_season(origin['source_ref'],definition,ws)
    pending=owner.advance(start,base.AdvanceRequest(q(536),step_budget=10))
    assert pending.status=='hold'and pending.hold.startswith('ORDER_HOLD:')
    result=model.locate_threshold(pending.handle,pending.pending['page_sha256'],TOLERANCE)
    assert result['status']=='root_located',result.get('hold')
    assert result['order']['next_forcing_relation']=='strictly_before'
    assert x(result['root']['upper_elapsed_seconds_exact'])<528
    assert result['material_consumed']is False


@pytest.mark.parametrize('change',['previous_cursor','definition','trace','status'])
def test_pending_page_must_match_actual_cursor_and_replayed_kernel(pending,change):
    value=stored_page(pending)
    if change=='previous_cursor':value['previous_cursor_sha256']='0'*64
    if change=='definition':value['definition_sha256']='0'*64
    if change=='trace':value['result']['interval']['stages'][1]['state'][104]+=1.0
    if change=='status':value['result']['status']='interval_ready'
    with MorphologyBlobStore(pending['workspace'].archive_directory,pending['workspace'].access,write=True)as store:
        reference=store.put(canonical(value),maximum=base.PAGE_MAX)
    result=model.locate_threshold(pending['result'].handle,reference,TOLERANCE)
    assert result['status']=='hold'and result['root']is None
    assert result['checkpoint_issued']is result['material_consumed']is False


@pytest.mark.parametrize('tolerance',[q(0),q(-1),q(9),q(1,'degC_day'),True])
def test_invalid_tolerance_rejected_before_pending_RHS(pending,tolerance,monkeypatch):
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('invalid tolerance reached RHS'))
    result=model.locate_threshold(pending['result'].handle,pending['result'].pending['page_sha256'],tolerance)
    assert result['status']=='hold'and result['root']is None


def test_precision_limit_and_cancel_preserve_source(pending,monkeypatch):
    result=model.locate_threshold(pending['result'].handle,pending['result'].pending['page_sha256'],q(Fraction(1,2**200)))
    assert result['status']=='hold'and result['hold'].startswith('PRECISION_HOLD:')
    assert result['progress']['bisections']==128
    real=model.event._value;cancel={'now':False}
    def value(coefficients,theta):
        result=real(coefficients,theta)
        if theta==Fraction(1,2):cancel['now']=True
        return result
    monkeypatch.setattr(model.event,'_value',value)
    cancelled=locate(pending,cancelled=lambda:cancel['now'])
    assert cancelled['status']=='hold'and cancelled['hold'].startswith('CANCELLED_HOLD:')
    assert cancelled['root']is None and cancelled['historical_cursor_sha256']==pending['result'].handle.cursor_sha256


def test_dense_endpoint_coincidence_keeps_order_hold():
    coefficients=(Fraction(-1),Fraction(1),Fraction(0),Fraction(0))
    root=model._isolate(coefficients,Fraction(8),Fraction(1,10**6),lambda:None,{'bisections':0})
    assert root[1]==1
    result=model._order(Fraction(0),Fraction(8),Fraction(0),Fraction(8),coefficients)
    assert result['next_forcing_relation']=='coincident_dense_endpoint'
    assert result['material_forcing_order_resolved']is False


def test_positive_stage_temperatures_are_insufficient_for_dense_monotonicity():
    coefficients=model.event._thermal_polynomial(tuple(map(Fraction,(6,6,6,100))),Fraction(8),Fraction(5),Fraction(0),Fraction(1,1000))
    with pytest.raises(ValueError,match='MONOTONICITY_HOLD:'):
        model._isolate(coefficients,Fraction(8),Fraction(1,10**6),lambda:None,{'bisections':0})


@pytest.mark.parametrize('change',['source','pending_page'])
def test_late_source_or_pending_page_change_suppresses_root(pending,tmp_path,monkeypatch,change):
    import shutil
    old=pending['workspace'];access=old.access
    source=tmp_path/'source';parent=tmp_path/'parent';archive=tmp_path/'archive'
    shutil.copytree(old.source_workspace.source_directory,source)
    shutil.copytree(old.source_workspace.archive_directory,parent)
    shutil.copytree(old.archive_directory,archive)
    ws=owner.Workspace(base.Workspace(source,parent,access),archive,access)
    original=pending['result'].handle
    handle=owner.open_season(owner.CursorRef(original.cursor_sha256),pending['definition'],ws)
    page_sha=pending['result'].pending['page_sha256']
    target=source/handle.basis['arithmetic_basis']['profile_sha256']['growth_profile']if change=='source'else archive/page_sha
    evaluate=base.stage.evaluate;mutated=[]
    def mutate(*args,**kwargs):
        value=evaluate(*args,**kwargs)
        if not mutated:target.write_bytes(target.read_bytes()+b' ');mutated.append(True)
        return value
    monkeypatch.setattr(base.stage,'evaluate',mutate)
    result=model.locate_threshold(handle,page_sha,TOLERANCE)
    assert result['status']=='hold'and result['root']is None
    assert result['authority_hold']is not None
    assert result['historical_cursor_sha256']==original.cursor_sha256


def test_failed_pending_IO_counts_are_unknown_not_zero(pending,monkeypatch):
    interval=kernel.advance_interval
    def fail(**kwargs):
        result=interval(**kwargs);assert result['status']=='awaiting_material'
        raise OSError(5,'private storage path')
    monkeypatch.setattr(kernel,'advance_interval',fail)
    result=locate(pending)
    assert result['status']=='hold'and result['root']is None
    assert result['progress']['failed_pending_RHS_count_unreported']is True
    assert result['progress']['RHS_quota_reserved']==5
    assert result['hold'].startswith('STORAGE_HOLD:')and 'private storage path'not in result['hold']


def test_wrong_code_and_non_owner_handle_refused_before_RHS(pending,monkeypatch):
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('invalid authority reached RHS'))
    result=model.locate_threshold(object(),pending['result'].pending['page_sha256'],TOLERANCE)
    assert result['status']=='hold'and result['hold'].startswith('CONTEXT_HOLD:')
    assert result['historical_cursor_sha256']is None
    monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    result=locate(pending)
    assert result['status']=='hold'and result['hold'].startswith('CODE_HOLD:')


def test_result_records_admitted_tolerance_when_callers_dict_changes(pending,monkeypatch):
    tolerance=deepcopy(TOLERANCE);advance=kernel.advance_interval
    def change(**kwargs):
        result=advance(**kwargs);tolerance.update(q(Fraction(1,2**200)));return result
    monkeypatch.setattr(kernel,'advance_interval',change)
    result=model.locate_threshold(pending['result'].handle,pending['result'].pending['page_sha256'],tolerance)
    assert result['status']=='root_located',result.get('hold')
    assert tolerance!=TOLERANCE
    assert result['time_tolerance_seconds_exact']==TOLERANCE
    assert x(result['root']['width_seconds_exact'])<=x(result['time_tolerance_seconds_exact'])
