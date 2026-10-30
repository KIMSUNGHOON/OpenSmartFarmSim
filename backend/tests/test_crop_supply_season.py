"""Actual stored morphology oracle and a new family's numerical continuation."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from app import crop_supply_season as season
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT/'web/public/supply-morphology-replay/own-public-v1'
SOURCE = '84daf00c44a964f904aa0b78e2c64f44c2753ec97641f23566fdfcc349bf4476'


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def q(number,unit='s'):
    number=Fraction(number)
    return {'numerator':str(number.numerator),'denominator':str(number.denominator),'unit':unit}


def x(value):
    return Fraction(int(value['numerator']),int(value['denominator']))


@pytest.fixture(scope='module')
def source(tmp_path_factory):
    directory=tmp_path_factory.mktemp('season-source')/'cas'
    access=ContentAccess(os.getuid(),os.getgid())
    index=json.loads((PUBLIC/'index.json').read_bytes())
    with MorphologyBlobStore(directory,access,write=True)as store:
        for item in index['blobs']:
            raw=(PUBLIC/item['path']).read_bytes()
            assert sha256(raw).hexdigest()==item['sha256']
            store.put(raw,maximum=16*1024**2)
    root=json.loads((PUBLIC/'root.json').read_bytes())
    return directory,access,root


def setup(source,tmp_path,*,frame=36,end=520):
    directory,access,root=source
    ws=season.Workspace(directory,tmp_path/'new-cas',access)
    f=root['frames'][frame]
    context=json.loads((directory/f['context_sha256']).read_bytes())
    cp=json.loads((directory/f['checkpoint_sha256']).read_bytes())
    p=context['descriptor']['seed']['program']
    document={'schema_version':'supply-season-definition-v1','source':{'artifact_sha256':SOURCE,'frame_index':frame},
              'code_sha256':season.CODE_SHA256,'method':context['descriptor']['seed']['original_numerical']['method'],
              'stop_at':q(end),'forcing_span':{'begin':deepcopy(f['at']['elapsed_seconds_exact']),'end':q(end),
              'forcing_and_fruit_entry_sha256':sha256(canonical({k:p['scenario'][k]for k in ('forcing','fruit_entry')})).hexdigest()},
              'rights':{'use':True,'display':True,'redistribute':False},
              'scope':'software_research_only','G0_G4':'not_assessed','R2':'not_approved'}
    with MorphologyBlobStore(ws.archive_directory,access,write=True)as store:
        definition=store.put(canonical(document),maximum=512*1024)
    return ws,definition,document,cp,context


def test_import_preserves_actual_origin_accounts_without_RHS(source,tmp_path,monkeypatch):
    ws,definition,_,cp,context=setup(source,tmp_path)
    def forbidden(*args,**kwargs):raise AssertionError('opening must not evaluate growth')
    monkeypatch.setattr(season.stage,'evaluate',forbidden)
    handle=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    actual=handle.current
    for name in season.NUMERIC_FIELDS:
        assert actual[name]==cp[name],name
    assert actual['schema_version']=='supply-season-current-v1'
    assert handle.basis['seed']==context['descriptor']['seed']
    assert 'receipts'not in handle.basis
    assert len(actual['last_confirmed']['state'])==176
    assert len(actual['global_ledgers'])==124
    assert len(actual['lifetime_transfers_exact'])==185
    assert len(actual['point_totals_exact'])==7
    assert len(canonical(actual))<512*1024


def test_original_504_512_full_oracle_and_real_520(source,tmp_path):
    ws,definition,_,_,_=setup(source,tmp_path)
    original=json.loads((source[0]/source[2]['frames'][37]['checkpoint_sha256']).read_bytes())
    first=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    result=season.advance(first,season.AdvanceRequest(q(520),step_budget=1))
    assert result.status=='yielded'
    current=result.handle.current
    for field in season.NUMERIC_FIELDS:
        if field!='output_prefix_sha256':assert current[field]==original[field],field
    final=season.advance(result.handle,season.AdvanceRequest(q(520),step_budget=1))
    assert final.status=='completed'
    assert x(final.handle.current['at']['elapsed_seconds_exact'])==520
    assert final.handle.current['last_confirmed']['state']!=original['last_confirmed']['state']
    assert final.handle.current['point_totals_exact']==original['point_totals_exact']
    assert all(abs(x(row['residual_exact']))<=x(row['budget_exact'])for row in final.handle.current['global_ledgers'].values())


def test_full_split_and_cold_restore_have_same_current_and_cursor(source,tmp_path,monkeypatch):
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    full=season.advance(start,season.AdvanceRequest(q(520),step_budget=2))
    split=season.advance(start,season.AdvanceRequest(q(520),step_budget=1))
    def forbidden(*args,**kwargs):raise AssertionError('cold restore must not evaluate past RHS')
    with monkeypatch.context()as patch:
        patch.setattr(season.stage,'evaluate',forbidden)
        cold=season.open_season(season.CursorRef(split.handle.cursor_sha256),definition,ws)
    again=season.advance(cold,season.AdvanceRequest(q(520),step_budget=1))
    assert full.status==again.status=='completed'
    assert full.handle.current==again.handle.current
    assert full.handle.cursor_sha256==again.handle.cursor_sha256


def test_actual_pending_528_preserves_520_without_consuming_event(source,tmp_path):
    ws,definition,_,cp,_=setup(source,tmp_path,end=528)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    result=season.advance(start,season.AdvanceRequest(q(528),step_budget=3))
    assert result.status=='awaiting_material'
    assert x(result.handle.current['at']['elapsed_seconds_exact'])==520
    assert result.handle.current['schedule']['next_sequence']==cp['schedule']['next_sequence']
    assert result.pending['left_at']==q(520)and result.pending['right_at']==q(528)
    assert result.pending['schedule_consumed']is False
    assert result.pending['candidate_or_checkpoint_issued']is False


def test_independent_all124_residual_differences_and_185_lifetime_composition(source,tmp_path):
    from decimal import Decimal,localcontext
    ws,definition,_,before,context=setup(source,tmp_path,frame=37)
    start=season.open_season(season.SourceRef(SOURCE,37),definition,ws)
    result=season.advance(start,season.AdvanceRequest(q(520)))
    assert result.status=='completed'
    after=result.handle.current
    seed=context['descriptor']['seed'];p=seed['program'];n=len(p['leaves']);m=len(p['stem_root_compartments']);h=len(seed['organs']['internodes'])
    a,b=([Fraction(v)for v in row['last_confirmed']['state']]for row in (before,after))
    t={k:x(after['lifetime_transfers_exact'][k])-x(before['lifetime_transfers_exact'][k])for k in before['lifetime_transfers_exact']}
    d0,d1=before['last_confirmed']['derived'],after['last_confirmed']['derived'];ca=Fraction(d0['air_capacity']['value'])
    profile=json.loads((source[0]/source[2]['root_inputs']['exchange_profile']['sha256']).read_bytes());lam=Fraction(profile['parameters']['latent_heat']['value'])
    carbon=lambda y:y[0]+sum(y[3:53])+sum(y[106+2*n:106+3*n+m])
    rows={'carbohydrate':carbon(b)-carbon(a)-t['photosynthesis']+sum(t[k]for k in ['growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit','removal_leaf','removal_stem','terminal_carbon']),
          'number':sum(b[53:103])-sum(a[53:103])-t['entry_number']+t['terminal_number'],
          'canopy_sensible':b[103]-a[103]-t['canopy_external']+t['sensible']+t['latent']-t['incoming_heat']+t['outgoing_heat'],
          'air_sensible':ca*(b[104]-a[104])-t['air_external']-t['sensible'],
          'vapor':b[105]-a[105]-t['vapor']-t['external_vapor'],
          'area_capacity':Fraction(d1['canopy_capacity']['value'])-Fraction(d0['canopy_capacity']['value'])-t['capacity_in']+t['capacity_out'],
          'reduced_energy':b[103]-a[103]+ca*(b[104]-a[104])+lam*(b[105]-a[105])-t['canopy_external']-t['air_external']-lam*t['external_vapor']-t['incoming_heat']+t['outgoing_heat']}
    elapsed=x(after['at']['elapsed_seconds_exact'])-x(before['at']['elapsed_seconds_exact'])
    for i,leaf in enumerate(p['leaves']):rows[f'leaf_age_{i}']=b[106+i]-a[106+i]-(t['indoor_air_temperature_time']-Fraction(leaf['base_temperature']['value'])*elapsed)/86400
    for kind,offset,count in [('leaf',106+2*n,n),('stem_root',106+3*n,m)]:
        for i in range(count):rows[f'{kind}_carbon_{i}']=b[offset+i]-a[offset+i]-t[f'{kind}_{i}_inflow']+t[f'{kind}_{i}_maintenance']+t[f'{kind}_{i}_removal']
    rows['stem_root_carbon']=sum(b[106+3*n:106+3*n+m])-sum(a[106+3*n:106+3*n+m])-sum(t[f'stem_root_{i}_inflow']for i in range(m))+sum(t[f'stem_root_{i}_maintenance']+t[f'stem_root_{i}_removal']for i in range(m))
    floor=Fraction(p['model_floor_area']['value']);size=106+3*n+m;indices={v['compartment_id']:i for i,v in enumerate(p['stem_root_compartments'])}
    for kind,organs,offset,unit in [('leaf',seed['organs']['leaves'],106+n,'leaves'),('internode',seed['organs']['internodes'],size+h,'internodes')]:
        for i,organ in enumerate(organs):
            k=f'{kind}_{i}';stock=f'leaf_{i}'if kind=='leaf'else f"stem_root_{indices[organ['compartment_id']]}"
            rows[k+'_geometry']=b[offset+i]-a[offset+i]-t[k+'_realized']
            rows[k+'_partition']=t[k+'_extension']+t[k+'_unmapped']-t[stock+'_inflow']
            rows[k+'_construction']=t[k+'_extension']-Fraction(seed['costs'][unit][i])*t[k+'_realized']/floor
            if kind=='internode':rows[k+'_age']=b[size+i]-a[size+i]-(t['indoor_air_temperature_time']-Fraction(organ['baseline']['base_temperature']['value'])*elapsed)/86400
    assert len(rows)==124 and set(rows)==set(after['global_ledgers'])
    with localcontext()as ctx:
        ctx.prec=2200
        for name,residual in rows.items():
            old=x(before['global_ledgers'][name]['residual_exact']);new=x(after['global_ledgers'][name]['residual_exact'])
            assert residual==new-old,name
            dec=lambda f:Decimal(f.numerator)/Decimal(f.denominator)
            assert abs(dec(new))<=dec(x(after['global_ledgers'][name]['budget_exact'])),name
        for name in t:
            original=x(seed['lifetime_transfers_exact'][name]);accumulator=Fraction(after['branch_integrated_transfers'][name]['value'])
            assert x(after['lifetime_transfers_exact'][name])==original+accumulator,name
    schedule=x(seed['schedule']['age_exact'])+(Fraction(after['branch_integrated_transfers']['indoor_air_temperature_time']['value'])-Fraction(source[2]['shoot_base_temperature'])*(520-x(seed['initial_sample']['at']['elapsed_seconds_exact'])))/86400
    assert x(after['schedule']['age_exact'])==schedule
    for key in ('fruit_carbohydrate','fruit_number'):
        offset=3 if key=='fruit_carbohydrate'else 53
        assert sum(b[offset:offset+50])>=0


@pytest.mark.parametrize('changes',[
    {'step_budget':0},{'step_budget':True},{'rhs_budget':0},{'record_budget':129},{'byte_budget':0},{'wall_seconds':61},
])
def test_invalid_resource_request_has_no_RHS_and_preserves_current(source,tmp_path,monkeypatch,changes):
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    monkeypatch.setattr(season.stage,'evaluate',lambda *a,**k:pytest.fail('invalid budget evaluated RHS'))
    result=season.advance(start,season.AdvanceRequest(q(520),**changes))
    assert result.status=='hold'and result.hold.startswith('BUDGET_HOLD:')
    assert result.handle.cursor_sha256==start.cursor_sha256


@pytest.mark.parametrize('changes',[{'rhs_budget':1},{'byte_budget':1}])
def test_budget_yield_never_publishes_a_partial_interval(source,tmp_path,changes):
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    result=season.advance(start,season.AdvanceRequest(q(520),**changes))
    assert result.status=='yielded'and result.handle.cursor_sha256==start.cursor_sha256
    assert result.progress['records_emitted']==result.progress['bytes_emitted']==0


def test_cancelled_request_and_late_cancel_keep_previous_cursor(source,tmp_path,monkeypatch):
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    cancelled=season.advance(start,season.AdvanceRequest(q(520),cancelled=lambda:True))
    assert cancelled.status=='hold'and cancelled.hold.startswith('CANCELLED_HOLD:')
    assert cancelled.handle.cursor_sha256==start.cursor_sha256
    flag={'cancel':False};original=MorphologyBlobStore.put
    def put(store,raw,**kwargs):
        digest=original(store,raw,**kwargs)
        value=json.loads(raw)
        if value.get('schema_version')=='supply-season-cursor-v1'and value['previous_cursor_sha256']is not None:flag['cancel']=True
        return digest
    monkeypatch.setattr(MorphologyBlobStore,'put',put)
    late=season.advance(start,season.AdvanceRequest(q(520),cancelled=lambda:flag['cancel']))
    assert late.status=='hold'and late.hold.startswith('CANCELLED_HOLD:')
    assert late.handle.cursor_sha256==start.cursor_sha256


def test_numerical_failure_returns_last_confirmed_prefix(source,tmp_path,monkeypatch):
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    evaluate=season.stage.evaluate;calls=0
    def fail(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==6:raise ValueError('STATE_HOLD: injected next-interval failure')
        return evaluate(*args,**kwargs)
    monkeypatch.setattr(season.stage,'evaluate',fail)
    result=season.advance(start,season.AdvanceRequest(q(520),step_budget=2))
    assert result.status=='hold'and result.hold=='STATE_HOLD: injected next-interval failure'
    assert x(result.handle.current['at']['elapsed_seconds_exact'])==512
    assert result.progress['past_intervals_reintegrated']==0


def test_source_change_during_equations_withholds_new_and_old_authorized_result(source,tmp_path,monkeypatch):
    import shutil
    copied=tmp_path/'copied-source';shutil.copytree(source[0],copied)
    ws,definition,_,_,_=setup((copied,source[1],source[2]),tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    target=copied/source[2]['root_inputs']['growth_profile']['sha256'];evaluate=season.stage.evaluate
    def change(*args,**kwargs):
        result=evaluate(*args,**kwargs)
        target.write_bytes(target.read_bytes()+b' ')
        return result
    monkeypatch.setattr(season.stage,'evaluate',change)
    result=season.advance(start,season.AdvanceRequest(q(520)))
    assert result.status=='hold'and result.handle is None and result.authority_hold is not None
    assert result.historical_cursor_sha256==start.cursor_sha256


def test_missing_history_and_substituted_current_are_rejected(source,tmp_path):
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    result=season.advance(start,season.AdvanceRequest(q(520),step_budget=1))
    cursor=json.loads(result.handle._cursor)
    path=ws.archive_directory/cursor['current_sha256'];raw=path.read_bytes();path.write_bytes(raw+b' ')
    with pytest.raises(ValueError,match='HASH_HOLD:'):season.open_season(season.CursorRef(result.handle.cursor_sha256),definition,ws)
    path.write_bytes(raw)
    (ws.archive_directory/cursor['history_page_sha256']).unlink()
    with pytest.raises((OSError,ValueError)):season.open_season(season.CursorRef(result.handle.cursor_sha256),definition,ws)


@pytest.mark.parametrize('change,reason',[
    ('code','CODE_HOLD:'),('rights','RIGHTS_HOLD:'),('forcing','FORCING_HOLD:'),('gap','TIME_HOLD:'),('source','SOURCE_HOLD:'),
])
def test_definition_source_rights_code_and_coverage_checks(source,tmp_path,change,reason):
    ws,_,document,_,_=setup(source,tmp_path)
    if change=='code':document['code_sha256']='0'*64
    if change=='rights':document['rights']['use']=False
    if change=='forcing':document['forcing_span']['forcing_and_fruit_entry_sha256']='0'*64
    if change=='gap':document['forcing_span']['begin']=q(496)
    if change=='source':document['source']['frame_index']=37;document['forcing_span']['begin']=q(512)
    with MorphologyBlobStore(ws.archive_directory,ws.access,write=True)as store:definition=store.put(canonical(document),maximum=512*1024)
    with pytest.raises(ValueError,match=reason):season.open_season(season.SourceRef(SOURCE,36),definition,ws)


def test_fresh_process_cold_restore_has_no_past_RHS_and_resumes(source,tmp_path):
    import subprocess,sys
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    first=season.advance(start,season.AdvanceRequest(q(520),step_budget=1))
    script="""
import json,os,sys
from pathlib import Path
from app import crop_supply_season as m
from app.content_access import ContentAccess
ws=m.Workspace(Path(sys.argv[1]),Path(sys.argv[2]),ContentAccess(os.getuid(),os.getgid()))
original=m.stage.evaluate
m.stage.evaluate=lambda *a,**k:(_ for _ in ()).throw(AssertionError('past RHS'))
h=m.open_season(m.CursorRef(sys.argv[4]),sys.argv[3],ws)
m.stage.evaluate=original
result=m.advance(h,m.AdvanceRequest({'numerator':'520','denominator':'1','unit':'s'}))
assert result.status=='completed',result.hold
print(json.dumps({'cursor':result.handle.cursor_sha256,'current':result.handle.current}))
"""
    run=subprocess.run([sys.executable,'-B','-c',script,str(ws.source_directory),str(ws.archive_directory),definition,first.handle.cursor_sha256],
                       cwd=ROOT/'backend',env={'PYTHONPATH':str(ROOT/'backend'),'PYTHONDONTWRITEBYTECODE':'1','PATH':os.defpath},text=True,capture_output=True,timeout=60)
    assert run.returncode==0,run.stderr
    cold=json.loads(run.stdout)
    full=season.advance(start,season.AdvanceRequest(q(520),step_budget=2))
    assert cold['cursor']==full.handle.cursor_sha256 and cold['current']==full.handle.current


def test_cold_current_must_stay_inside_declared_forcing_coverage(source,tmp_path):
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    result=season.advance(start,season.AdvanceRequest(q(520),step_budget=1))
    current=result.handle.current;current['at']['elapsed_seconds_exact']=q(528)
    cursor=json.loads(result.handle._cursor)
    with MorphologyBlobStore(ws.archive_directory,ws.access,write=True)as store:
        cursor['current_sha256']=store.put(canonical(current),maximum=512*1024)
        forged=store.put(canonical(cursor),maximum=512*1024)
    with pytest.raises(ValueError,match='TIME_HOLD:'):
        season.open_season(season.CursorRef(forged),definition,ws)


def test_wrong_family_and_page_claim_flags_cannot_restore(source,tmp_path):
    from dataclasses import replace
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    result=season.advance(replace(start,_token=object()),season.AdvanceRequest(q(520)))
    assert result.status=='hold'and result.handle is None and result.hold.startswith('CONTEXT_HOLD:')
    cursor=json.loads(start._cursor);cursor['G0_G4']='passed'
    with MorphologyBlobStore(ws.archive_directory,ws.access,write=True)as store:fake=store.put(canonical(cursor),maximum=512*1024)
    with pytest.raises(ValueError,match='CONTEXT_HOLD:'):
        season.open_season(season.CursorRef(fake),definition,ws)


def test_material_declaration_is_explicitly_unsupported_and_does_not_consume(source,tmp_path):
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    result=season.advance(start,season.AdvanceRequest(q(520)),material={'invented':'declaration'})
    assert result.status=='hold'and result.hold.startswith('MATERIAL_HOLD:')
    assert result.handle.cursor_sha256==start.cursor_sha256


def test_wall_budget_includes_admission_and_returns_original_cursor(source,tmp_path,monkeypatch):
    from types import SimpleNamespace
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    readings=iter([0.,2.])
    monkeypatch.setattr(season,'time',SimpleNamespace(monotonic=lambda:next(readings)))
    result=season.advance(start,season.AdvanceRequest(q(520),wall_seconds=1))
    assert result.status=='hold'and result.hold.startswith('WALL_HOLD:')
    assert result.handle.cursor_sha256==start.cursor_sha256
    assert result.progress['current_validation_RHS_evaluations']==0


def test_storage_failure_before_cursor_publication_has_explicit_hold_and_original_prefix(source,tmp_path,monkeypatch):
    ws,definition,_,_,_=setup(source,tmp_path)
    start=season.open_season(season.SourceRef(SOURCE,36),definition,ws)
    put=MorphologyBlobStore.put
    def fail(store,raw,**kwargs):
        doc=json.loads(raw)
        if doc.get('schema_version')=='supply-season-cursor-v1'and doc['previous_cursor_sha256']is not None:
            raise OSError(28,'private path must not reach the public hold')
        return put(store,raw,**kwargs)
    monkeypatch.setattr(MorphologyBlobStore,'put',fail)
    result=season.advance(start,season.AdvanceRequest(q(520)))
    assert result.status=='hold'and result.hold.startswith('STORAGE_HOLD:')
    assert 'private path'not in result.hold
    assert result.failed_stage=='publication'
    assert result.handle.cursor_sha256==start.cursor_sha256
    restored=season.open_season(season.CursorRef(start.cursor_sha256),definition,ws)
    assert restored.current==start.current
