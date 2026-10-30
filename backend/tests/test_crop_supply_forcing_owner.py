"""Genuine source, fixed forcing plan, durable phases and owner recovery."""
from copy import deepcopy
from datetime import datetime,timezone
from fractions import Fraction
import json

import pytest

from app import crop_supply_season as base
from app import crop_supply_forcing_interval as kernel
from app import crop_supply_forcing_owner as owner
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_supply_season import source, setup, q, x, canonical, SOURCE
from test_crop_supply_forcing_interval import span


@pytest.fixture(scope='module')
def origin(source,tmp_path_factory):
    path=tmp_path_factory.mktemp('forcing-owner-source')
    ws,definition,_,_,_=setup(source,path)
    start=base.open_season(base.SourceRef(SOURCE,36),definition,ws)
    first=base.advance(start,base.AdvanceRequest(q(520)))
    last=base.advance(first.handle,base.AdvanceRequest(q(520)))
    assert first.status=='yielded'and last.status=='completed'
    with base._session(definition,ws)as s:profiles=s.profiles
    return {'workspace':ws,'source_ref':owner.SourceRef(definition,first.handle.cursor_sha256),
            'basis':first.handle.basis,'before':first.handle.current,'constant520':last.handle.current,'profiles':profiles}


def setup_owner(origin,tmp_path,*,edge=Fraction(1025,2),end=520):
    workspace=owner.Workspace(origin['workspace'],tmp_path/'forcing-cas',origin['workspace'].access)
    now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    spans=[span(origin,512,edge),span(origin,edge,end,changed=True)]
    records=[]
    for value in spans:
        units={f'{block}.{k}':v['unit']for block in ('forcing','fruit_entry')for k,v in value[block].items()}
        provenance={'product_id':value['input_id'],'source_url':'urn:opensmartfarmsim:self-authored-software-fixture',
                    'observed_at':None,'published_at':None,'available_at':now,'retrieved_at':now,'vintage':'own','revision':'1',
                    'units':units,'qc':'software_fixture_only','raw_sha256':base._hash(value),'reviewer':'software-test-fixture-author'}
        records.append({'span':value,'rights':{'use':True,'display':True,'redistribute':True},'provenance':provenance})
    d={'schema_version':'supply-forcing-definition-v1','source':vars(origin['source_ref']),
       'code_sha256':owner.CODE_SHA256,'kernel_code_sha256':kernel.CODE_SHA256,
       'partition':'original_grid_and_declared_forcing_edges_v1','stop_at':q(end),'spans':records,
       'rights':{'use':True,'display':True,'redistribute':True},**base.FLAGS}
    with MorphologyBlobStore(workspace.archive_directory,workspace.access,write=True)as store:definition=store.put(canonical(d),maximum=base.PAGE_MAX)
    return workspace,definition,d


def test_source_open_uses_genuine_data_and_inherits_private_result(origin,tmp_path,monkeypatch):
    ws,definition,_=setup_owner(origin,tmp_path)
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('source admission evaluated growth'))
    monkeypatch.setattr(kernel,'advance_interval',lambda *a,**k:pytest.fail('source admission ran interval'))
    handle=owner.open_season(origin['source_ref'],definition,ws)
    assert handle.current['numeric']==origin['before']
    assert handle.current['phase']=='source_before_forcing'
    assert handle.current['effective_rights']=={'use':True,'display':True,'redistribute':False}
    assert handle.basis['arithmetic_basis']==origin['basis']


def test_fixed_partition_phases_equal_real_kernel_result(origin,tmp_path):
    ws,definition,d=setup_owner(origin,tmp_path)
    start=owner.open_season(origin['source_ref'],definition,ws)
    result=owner.advance(start,base.AdvanceRequest(q(520),step_budget=2))
    assert result.status=='completed',result.hold
    assert [v['phase']for v in result.emitted]==['forcing_after','forcing_before','forcing_after','declared_end']
    assert [x(v['at']['elapsed_seconds_exact'])for v in result.emitted]==[512,Fraction(1025,2),Fraction(1025,2),520]
    first=kernel.advance_interval(basis=origin['basis'],current=origin['before'],profiles=origin['profiles'],span=d['spans'][0]['span'],end=q(Fraction(1025,2)))
    expected=kernel.advance_interval(basis=origin['basis'],current=first['current'],profiles=origin['profiles'],span=d['spans'][1]['span'],end=q(520))
    assert result.handle.current['numeric']==expected['current']
    assert result.handle.current['integration_count']==2
    assert result.handle.current['output_cursor']==origin['before']['output_cursor']+4
    assert result.handle.current['effective_rights']['redistribute']is False


def test_full_split_and_cold_equal_same_final_cursor_without_past_RHS(origin,tmp_path,monkeypatch):
    ws,definition,_=setup_owner(origin,tmp_path)
    start=owner.open_season(origin['source_ref'],definition,ws)
    full=owner.advance(start,base.AdvanceRequest(q(520),step_budget=2))
    first=owner.advance(start,base.AdvanceRequest(q(520),step_budget=1))
    assert first.status=='yielded'and first.handle.current['phase']=='forcing_after'
    assert x(first.handle.current['at']['elapsed_seconds_exact'])==Fraction(1025,2)
    with monkeypatch.context()as patch:
        patch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('past RHS during cold'))
        patch.setattr(kernel,'advance_interval',lambda *a,**k:pytest.fail('past interval during cold'))
        cold=owner.open_season(owner.CursorRef(first.handle.cursor_sha256),definition,ws)
    last=owner.advance(cold,base.AdvanceRequest(q(520),step_budget=1))
    assert full.status==last.status=='completed'
    assert full.handle.current==last.handle.current
    assert full.handle.cursor_sha256==last.handle.cursor_sha256


def test_aligned_edge_keeps_stocks_and_consumes_no_material(origin,tmp_path):
    ws,definition,_=setup_owner(origin,tmp_path,edge=520,end=522)
    start=owner.open_season(origin['source_ref'],definition,ws)
    first=owner.advance(start,base.AdvanceRequest(q(520),step_budget=1))
    assert first.status=='yielded'and first.handle.current['phase']=='forcing_after'
    assert first.handle.current['numeric']['last_confirmed']['state']==origin['constant520']['last_confirmed']['state']
    assert first.handle.current['numeric']['point_totals_exact']==origin['before']['point_totals_exact']
    last=owner.advance(first.handle,base.AdvanceRequest(q(522)))
    assert last.status=='completed'
    assert last.handle.current['integration_count']==2


def store_definition(ws,value):
    with MorphologyBlobStore(ws.archive_directory,ws.access,write=True)as store:
        return store.put(canonical(value),maximum=base.PAGE_MAX)


def test_missing_source_definition_is_rejected_as_invalid_record(origin,tmp_path):
    ws,_,d=setup_owner(origin,tmp_path);d.pop('source')
    definition=store_definition(ws,d)
    with pytest.raises(ValueError):owner.open_season(origin['source_ref'],definition,ws)


def test_interval_wall_budget_uses_remaining_owner_time(origin,tmp_path,monkeypatch):
    ws,definition,_=setup_owner(origin,tmp_path)
    start=owner.open_season(origin['source_ref'],definition,ws)
    advance=kernel.advance_interval;seen=[]
    def wrapped(**kwargs):
        seen.append(kwargs['wall_seconds']);return advance(**kwargs)
    monkeypatch.setattr(kernel,'advance_interval',wrapped)
    result=owner.advance(start,base.AdvanceRequest(q(520),step_budget=2,wall_seconds=60))
    assert result.status=='completed',result.hold
    assert seen and all(1 <= v < 60 for v in seen)


@pytest.mark.parametrize('change,reason',[
    ('gap','COVERAGE_HOLD:'),('overlap','COVERAGE_HOLD:'),('missing_end','COVERAGE_HOLD:'),
    ('unit','UNIT_HOLD:'),('raw_hash','SOURCE_HOLD:'),('use','RIGHTS_HOLD:'),('code','CODE_HOLD:'),
])
def test_bad_plan_rights_units_and_provenance_refused_before_RHS(origin,tmp_path,monkeypatch,change,reason):
    ws,_,d=setup_owner(origin,tmp_path)
    if change=='gap':d['spans'][1]['span']['start']=q(513)
    if change=='overlap':d['spans'][1]['span']['start']=q(512)
    if change=='missing_end':d['stop_at']=q(522)
    if change=='unit':d['spans'][1]['span']['forcing']['co2']['unit']='percent'
    if change=='raw_hash':d['spans'][1]['provenance']['raw_sha256']='0'*64
    if change=='use':d['spans'][1]['rights']['use']=False
    if change=='code':d['code_sha256']='0'*64
    if change in ('gap','overlap'):
        d['spans'][1]['provenance']['raw_sha256']=base._hash(d['spans'][1]['span'])
    definition=store_definition(ws,d)
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('invalid plan ran RHS'))
    with pytest.raises(ValueError,match=reason):owner.open_season(origin['source_ref'],definition,ws)


def test_budget_yield_before_switch_restarts_without_changing_partition(origin,tmp_path):
    ws,definition,_=setup_owner(origin,tmp_path)
    start=owner.open_season(origin['source_ref'],definition,ws)
    first=owner.advance(start,base.AdvanceRequest(q(520),step_budget=2,record_budget=2))
    assert first.status=='yielded'and first.handle.current['phase']=='forcing_before'
    assert x(first.handle.current['at']['elapsed_seconds_exact'])==Fraction(1025,2)
    cold=owner.open_season(owner.CursorRef(first.handle.cursor_sha256),definition,ws)
    last=owner.advance(cold,base.AdvanceRequest(q(520),step_budget=2))
    full=owner.advance(start,base.AdvanceRequest(q(520),step_budget=2))
    assert last.status==full.status=='completed'
    assert last.handle.cursor_sha256==full.handle.cursor_sha256


def test_selection_cannot_add_an_undeclared_integration_boundary(origin,tmp_path):
    ws,definition,_=setup_owner(origin,tmp_path)
    start=owner.open_season(origin['source_ref'],definition,ws)
    result=owner.advance(start,base.AdvanceRequest(q(513),step_budget=2))
    assert result.status=='hold'and result.hold.startswith('TIME_HOLD:')
    assert result.handle.cursor_sha256==start.cursor_sha256
    assert result.progress['RHS_quota_reserved']==0


@pytest.mark.parametrize('edge,expected',[(Fraction(1025,2),'awaiting_material'),(528,'hold')])
def test_pending_material_and_unresolved_forcing_order_do_not_consume(origin,tmp_path,edge,expected):
    ws,definition,_=setup_owner(origin,tmp_path,edge=edge,end=536)
    start=owner.open_season(origin['source_ref'],definition,ws)
    result=owner.advance(start,base.AdvanceRequest(q(536),step_budget=10))
    assert result.status==expected,result.hold
    assert x(result.handle.current['at']['elapsed_seconds_exact'])==520
    assert result.pending['schedule_consumed']is False
    assert result.handle.current['numeric']['event_sequence']==origin['before']['event_sequence']
    if expected=='hold':assert result.hold.startswith('ORDER_HOLD:')


def test_missing_page_and_corrupt_current_refuse_cold_restore(origin,tmp_path):
    ws,definition,_=setup_owner(origin,tmp_path)
    start=owner.open_season(origin['source_ref'],definition,ws)
    result=owner.advance(start,base.AdvanceRequest(q(520),step_budget=2))
    cursor=json.loads(result.handle._cursor);path=ws.archive_directory/cursor['current_sha256'];original=path.read_bytes()
    path.write_bytes(original+b' ')
    with pytest.raises(ValueError):owner.open_season(owner.CursorRef(result.handle.cursor_sha256),definition,ws)
    path.write_bytes(original);(ws.archive_directory/cursor['history_page_sha256']).unlink()
    with pytest.raises((OSError,ValueError)):owner.open_season(owner.CursorRef(result.handle.cursor_sha256),definition,ws)


def test_cancel_and_publication_failure_keep_previous_confirmed_cursor(origin,tmp_path,monkeypatch):
    ws,definition,_=setup_owner(origin,tmp_path)
    start=owner.open_season(origin['source_ref'],definition,ws)
    cancelled=owner.advance(start,base.AdvanceRequest(q(520),cancelled=lambda:True))
    assert cancelled.status=='hold'and cancelled.hold.startswith('CANCELLED_HOLD:')
    assert cancelled.handle.cursor_sha256==start.cursor_sha256
    put=MorphologyBlobStore.put
    def fail(store,raw,**kwargs):
        value=json.loads(raw)
        if value.get('schema_version')=='supply-forcing-owner-cursor-v1'and value['previous_cursor_sha256']is not None:
            raise OSError(28,'private path')
        return put(store,raw,**kwargs)
    monkeypatch.setattr(MorphologyBlobStore,'put',fail)
    result=owner.advance(start,base.AdvanceRequest(q(520)))
    assert result.status=='hold'and result.hold.startswith('STORAGE_HOLD:')and 'private path'not in result.hold
    assert result.failed_stage=='publication'and result.handle.cursor_sha256==start.cursor_sha256


def test_late_source_change_clears_all_current_results(origin,tmp_path,monkeypatch):
    import shutil
    old=origin['workspace'];copy_source=tmp_path/'source';copy_archive=tmp_path/'parent'
    shutil.copytree(old.source_directory,copy_source);shutil.copytree(old.archive_directory,copy_archive)
    copied={**origin,'workspace':base.Workspace(copy_source,copy_archive,old.access)}
    ws,definition,_=setup_owner(copied,tmp_path)
    start=owner.open_season(origin['source_ref'],definition,ws)
    target=copy_source/origin['basis']['profile_sha256']['growth_profile'];evaluate=base.stage.evaluate
    def change(*args,**kwargs):
        value=evaluate(*args,**kwargs);target.write_bytes(target.read_bytes()+b' ');return value
    monkeypatch.setattr(base.stage,'evaluate',change)
    result=owner.advance(start,base.AdvanceRequest(q(520),step_budget=2))
    assert result.status=='hold'and result.handle is None and result.authority_hold is not None
    assert result.emitted==[]and result.historical_cursor_sha256==start.cursor_sha256


def test_fresh_process_restores_fractional_after_phase_and_resumes(origin,tmp_path):
    import subprocess,sys,os
    from test_crop_supply_season import ROOT
    ws,definition,_=setup_owner(origin,tmp_path)
    start=owner.open_season(origin['source_ref'],definition,ws)
    first=owner.advance(start,base.AdvanceRequest(q(520),step_budget=1))
    script="""
import sys,json,os
from pathlib import Path
from app import crop_supply_forcing_owner as m,crop_supply_season as b,crop_supply_forcing_interval as k
from app.content_access import ContentAccess
access=ContentAccess(os.getuid(),os.getgid())
ws=m.Workspace(b.Workspace(Path(sys.argv[1]),Path(sys.argv[2]),access),Path(sys.argv[3]),access)
evaluate=b.stage.evaluate;advance=k.advance_interval
b.stage.evaluate=lambda *a,**v:(_ for _ in ()).throw(AssertionError('past RHS'))
k.advance_interval=lambda *a,**v:(_ for _ in ()).throw(AssertionError('past interval'))
h=m.open_season(m.CursorRef(sys.argv[5]),sys.argv[4],ws)
b.stage.evaluate=evaluate;k.advance_interval=advance
r=m.advance(h,b.AdvanceRequest({'numerator':'520','denominator':'1','unit':'s'}))
assert r.status=='completed',r.hold
print(json.dumps({'cursor':r.handle.cursor_sha256,'current':r.handle.current}))
"""
    args=[sys.executable,'-B','-c',script,str(ws.source_workspace.source_directory),str(ws.source_workspace.archive_directory),str(ws.archive_directory),definition,first.handle.cursor_sha256]
    run=subprocess.run(args,cwd=ROOT/'backend',env={'PATH':os.defpath,'PYTHONPATH':str(ROOT/'backend'),'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True,timeout=60)
    assert run.returncode==0,run.stderr
    child=json.loads(run.stdout);full=owner.advance(start,base.AdvanceRequest(q(520),step_budget=2))
    assert child['cursor']==full.handle.cursor_sha256 and child['current']==full.handle.current


def test_interval_io_failure_does_not_report_unknown_RHS_as_zero(origin,tmp_path,monkeypatch):
    ws,definition,_=setup_owner(origin,tmp_path)
    start=owner.open_season(origin['source_ref'],definition,ws)
    interval=kernel.advance_interval
    def fail_after_evaluation(**kwargs):
        result=interval(**kwargs)
        assert result['status']=='interval_ready'
        raise OSError(5,'private path after RHS')
    monkeypatch.setattr(kernel,'advance_interval',fail_after_evaluation)
    result=owner.advance(start,base.AdvanceRequest(q(520),step_budget=2))
    assert result.status=='hold'and result.hold.startswith('STORAGE_HOLD:')
    assert result.failed_stage=='interval_evaluation'
    assert result.handle.current['phase']=='forcing_after'
    assert x(result.handle.current['at']['elapsed_seconds_exact'])==512
    assert result.progress['failed_interval_RHS_count_unreported']is True
    assert 'private path'not in result.hold


def test_late_forcing_definition_change_clears_current_authority(origin,tmp_path,monkeypatch):
    ws,definition,_=setup_owner(origin,tmp_path)
    start=owner.open_season(origin['source_ref'],definition,ws)
    path=ws.archive_directory/definition;evaluate=base.stage.evaluate
    def change(*args,**kwargs):
        result=evaluate(*args,**kwargs);path.write_bytes(path.read_bytes()+b' ');return result
    monkeypatch.setattr(base.stage,'evaluate',change)
    result=owner.advance(start,base.AdvanceRequest(q(520),step_budget=2))
    assert result.status=='hold'and result.handle is None
    assert result.authority_hold is not None and result.emitted==[]
    assert result.historical_cursor_sha256==start.cursor_sha256
