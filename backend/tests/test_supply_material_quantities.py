"""Original material state and independent exact quantity oracles; no crop run."""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import os

import pytest

from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore
from app import crop_supply_material_quantities as quantities

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'web/public/supply-material-replay/own-public-v1'
ARTIFACT='b4640f0532420a0deaa0cf82f840a548517f075a46059687acbd5c88caf11cae'
MASS,NUMBER='mg_CH2O/m2_floor','fruits_equivalent/m2_floor'
UNITS={'terminal_carbon':MASS,'terminal_number':NUMBER,
       **dict.fromkeys(['sensible','latent','incoming_heat','outgoing_heat','canopy_external','air_external'],'J/m2_floor'),
       **dict.fromkeys(['vapor','external_vapor'],'kg_water/m2_floor')}

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def exact(q):return Fraction(int(q['numerator']),int(q['denominator']))
def decimal(q):return Decimal(q['numerator'])/Decimal(q['denominator'])

@pytest.fixture(scope='module')
def original(tmp_path_factory):
    index=json.loads((PUBLIC/'index.json').read_bytes());assert index['artifact_sha256']==ARTIFACT
    access=ContentAccess(os.getuid(),os.getgid());directory=tmp_path_factory.mktemp('material-quantities')/'cas'
    with MorphologyBlobStore(directory,access,write=True)as store:
        for d in index['blobs']:
            raw=(PUBLIC/d['path']).read_bytes();assert len(raw)==d['bytes']and sha256(raw).hexdigest()==d['sha256']
            assert store.put(raw,maximum=2*1024**2)==d['sha256']
    frames=[json.loads((PUBLIC/f'frame-{i}.json').read_bytes())['frame']for i in range(4)]
    return directory,access,frames,json.loads((PUBLIC/'root.json').read_bytes())

def read(original,**window):return quantities.read_material_quantity_window(original[0],original[1],ARTIFACT,**window)

def test_all_original_stocks_counters_and_references_are_source_bound(original):
    result=read(original);assert len(result['frames'])==4 and len(result['intervals'])==3
    assert result['source']['artifact_sha256']==ARTIFACT
    assert result['source']['code_sha256']==original[3]['code_sha256']
    assert result['source']['effective_rights']==original[3]['effective_rights']
    assert result['model_floor_area']==original[2][0]['model_floor_area']
    with localcontext()as context:
        context.prec=250
        for source,row in zip(original[2],result['frames'],strict=True):
            assert row['at']==source['at']and row['phase']==source['phase']
            assert row['reference']['index']==source['index']
            for name in ['source_sha256','source_cursor_sha256','event_sequence','state_kind']:assert row['reference'][name]==source[name]
            assert row['reference']['frame_sha256']==sha256(canonical(source)).hexdigest()
            assert row['reference']['state_sha256']==sha256(canonical(source['snapshot']['state'])).hexdigest()
            assert row['fruit_carbohydrate']=={'values':source['snapshot']['state'][3:53],'unit':MASS}
            assert row['fruit_number']=={'values':source['snapshot']['state'][53:103],'unit':NUMBER}
            assert decimal(row['carbohydrate_stock_exact'])==sum(map(Decimal.from_float,source['snapshot']['state'][3:53]),Decimal(0))
            assert decimal(row['number_stock_exact'])==sum(map(Decimal.from_float,source['snapshot']['state'][53:103]),Decimal(0))
            assert row['cumulative_exact']=={k:source['lifetime_transfers_exact'][k]for k in UNITS}
    assert result['G0_G4']=='not_assessed'and result['R2']=='not_approved'
    assert result['claim_scope']=='stored_synthetic_material_quantities_only'

def test_exact_interval_differences_telescope_and_keep_signed_resources(original):
    result=read(original)
    for left,right,row in zip(original[2],original[2][1:],result['intervals']):
        dt=exact(right['at']['elapsed_seconds_exact'])-exact(left['at']['elapsed_seconds_exact'])
        assert exact(row['elapsed_seconds_exact'])==dt
        assert row['kind']==('zero_duration_material_boundary'if dt==0 else'stored_model_interval')
        for name,unit in UNITS.items():
            expected=exact(right['lifetime_transfers_exact'][name])-exact(left['lifetime_transfers_exact'][name])
            assert row['flows_exact'][name]['unit']==unit and exact(row['flows_exact'][name])==expected
    for name in UNITS:
        expected=exact(original[2][-1]['lifetime_transfers_exact'][name])-exact(original[2][0]['lifetime_transfers_exact'][name])
        assert exact(result['totals_exact'][name])==expected==sum((exact(r['flows_exact'][name])for r in result['intervals']),Fraction(0))
    assert exact(result['totals_exact']['external_vapor'])<0
    assert result['intervals'][0]['kind']=='zero_duration_material_boundary'
    assert all(exact(v)==0 for v in result['intervals'][0]['flows_exact'].values())

@pytest.mark.parametrize('first,last',[(0,0),(1,1),(0,1),(1,3),(2,3)])
def test_actual_inclusive_windows_and_single_frame(original,first,last):
    result=read(original,first_frame=first,last_frame=last)
    assert [f['reference']['index']for f in result['frames']]==list(range(first,last+1))
    assert len(result['intervals'])==last-first
    assert result['window']=={'first_frame':first,'last_frame':last,'start_at':original[2][first]['at'],'end_at':original[2][last]['at']}
    for name in UNITS:assert exact(result['totals_exact'][name])==exact(original[2][last]['lifetime_transfers_exact'][name])-exact(original[2][first]['lifetime_transfers_exact'][name])

@pytest.mark.parametrize('window',[
    {'first_frame':True},{'first_frame':-1},{'first_frame':4},{'first_frame':None},{'first_frame':'0'},
    {'last_frame':False},{'last_frame':4},{'last_frame':1.0},{'first_frame':2,'last_frame':1},
])
def test_invalid_window_does_not_select_another_state(original,window):
    with pytest.raises(quantities.MaterialQuantityHold):read(original,**window)

@pytest.mark.parametrize('change',['order','unit','boolean','negative','nonfinite','missing','carbon_without_number','terminal_negative','resource_unit'])
def test_stock_or_lifetime_semantics_cannot_override_the_source_frame(original,change):
    f=deepcopy(original[2][0])
    if change=='order':f['state_layout']['original']['cohort_arrays'].reverse()
    if change=='unit':f['state_layout']['original']['units']['cohort_arrays']['fruit_number']='fruits'
    if change=='boolean':f['snapshot']['state'][3]=True
    if change=='negative':f['snapshot']['state'][3]=-1.0
    if change=='nonfinite':f['snapshot']['state'][3]=float('inf')
    if change=='missing':f['snapshot']['state']=f['snapshot']['state'][:102]
    if change=='carbon_without_number':f['snapshot']['state'][3]=1.0;f['snapshot']['state'][53]=0.0
    if change=='terminal_negative':f['lifetime_transfers_exact']['terminal_carbon']={'numerator':'-1','denominator':'1','unit':MASS}
    if change=='resource_unit':f['lifetime_transfers_exact']['incoming_heat']['unit']='kWh'
    with pytest.raises(ValueError):quantities._frame(f)

@pytest.mark.parametrize('change',['origin','reverse_time','wrong_phase','sequence','counter_jump','stock_jump','nonadjacent','terminal_decrease'])
def test_boundaries_and_intervals_reject_false_time_point_or_counter_changes(original,change):
    left,right=map(quantities._frame,original[2][:2])
    if change=='origin':right['at']['time_origin_utc']='2026-10-02T07:00:00Z'
    if change=='reverse_time':right['at']['elapsed_seconds_exact']={'numerator':'1','denominator':'1','unit':'s'}
    if change=='wrong_phase':right['phase']='original_grid_endpoint'
    if change=='sequence':right['reference']['event_sequence']=True
    if change=='counter_jump':right['cumulative_exact']['incoming_heat']={'numerator':'0','denominator':'1','unit':'J/m2_floor'}
    if change=='stock_jump':right['fruit_number']['values'][0]+=1.0
    if change=='nonadjacent':right['reference']['index']=3
    if change=='terminal_decrease':right['cumulative_exact']['terminal_number']={'numerator':'0','denominator':'1','unit':NUMBER}
    with pytest.raises(ValueError):quantities._interval(left,right)

def test_copies_and_selected_rights_are_not_a_cross_request_cache(original):
    one=read(original,first_frame=1,last_frame=3);expected=deepcopy(one)
    one['frames'][0]['fruit_carbohydrate']['values'][0]=999.;one['source']['effective_rights']['display']=False
    one['totals_exact']['external_vapor']['numerator']='999'
    assert read(original,first_frame=1,last_frame=3)==expected

@pytest.mark.parametrize('permission',['use','display'])
def test_current_embedded_grant_must_allow_the_quantity_projection(original,monkeypatch,permission):
    load=quantities.reader._load
    def changed(*args,**kwargs):
        m,frames,raws=load(*args,**kwargs);m['effective_rights'][permission]=False;return m,frames,raws
    monkeypatch.setattr(quantities.reader,'_load',changed)
    with pytest.raises(quantities.MaterialQuantityHold):read(original)

def test_source_drift_after_validation_is_held_and_no_store_file_is_added(original,monkeypatch):
    path=original[0]/ARTIFACT;raw=path.read_bytes();names={p.name for p in original[0].iterdir()};project=quantities._frame;changed=False
    def drift(*args,**kwargs):
        nonlocal changed
        result=project(*args,**kwargs)
        if not changed:changed=True;path.write_bytes(raw+b' ')
        return result
    monkeypatch.setattr(quantities,'_frame',drift)
    try:
        with pytest.raises(quantities.MaterialQuantityHold):read(original)
        assert changed and {p.name for p in original[0].iterdir()}==names
    finally:path.write_bytes(raw)

def test_own_code_fences_both_before_and_after_projection(original,monkeypatch):
    code=quantities.CODE_SHA256;monkeypatch.setattr(quantities,'CODE_SHA256','0'*64)
    with pytest.raises(quantities.MaterialQuantityHold):read(original)
    monkeypatch.setattr(quantities,'CODE_SHA256',code);project=quantities._frame
    def drift(*args,**kwargs):
        result=project(*args,**kwargs);monkeypatch.setattr(quantities,'CODE_SHA256','0'*64);return result
    monkeypatch.setattr(quantities,'_frame',drift)
    with pytest.raises(quantities.MaterialQuantityHold):read(original)

def test_response_cap_is_checked_before_any_return(original,monkeypatch):
    monkeypatch.setattr(quantities,'MAX_RESPONSE_BYTES',1024)
    with pytest.raises(quantities.MaterialQuantityHold,match='bounded material quantity response'):read(original)

def test_cold_query_blocks_growth_process_DB_network_and_CAS_writes(original):
    import subprocess,sys
    script=r'''
import importlib.abc,json,os,socket,subprocess,sys
from pathlib import Path
from hashlib import sha256
R=Path(sys.argv[1]);directory=Path(sys.argv[2]);root=sys.argv[3];sys.path.insert(0,str(R/'backend'))
forbidden={'app.crop_supply_season','app.crop_supply_forcing_interval','app.crop_supply_forcing_owner','app.crop_supply_forcing_threshold','app.crop_supply_forcing_threshold_state','app.crop_supply_threshold_state_books','app.crop_supply_material_point','app.crop_supply_material_proof','app.crop_supply_material_owner','app.crop_supply_material_artifact_producer','app.crop_supply_morphology_birth_stage','app.crop_growth_rates','app.crop_leaf_area','app.crop_internode_length'}
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname in forbidden:raise AssertionError('growth/model import: '+fullname)
sys.meta_path.insert(0,Guard())
import psycopg
from app.job_store import JobStore
from app.crop_morphology_artifact_io import MorphologyBlobStore
from app.content_access import ContentAccess
from app import crop_supply_material_quantities as module
calls={'DB':0,'network':0,'CAS_put':0,'process_or_CLI':0}
def fail(name):
 def blocked(*a,**k):calls[name]+=1;raise AssertionError(name+' during cold quantity query')
 return blocked
psycopg.connect=fail('DB');JobStore.connect=fail('DB');socket.socket=fail('network');socket.create_connection=fail('network');MorphologyBlobStore.put=fail('CAS_put');subprocess.Popen=fail('process_or_CLI');os.system=fail('process_or_CLI')
before={p.name:[p.stat().st_size,p.stat().st_mtime_ns,sha256(p.read_bytes()).hexdigest()]for p in directory.iterdir()};fds=len(os.listdir('/proc/self/fd'))
result=module.read_material_quantity_window(directory,ContentAccess(os.getuid(),os.getgid()),root)
after={p.name:[p.stat().st_size,p.stat().st_mtime_ns,sha256(p.read_bytes()).hexdigest()]for p in directory.iterdir()}
assert before==after and len(os.listdir('/proc/self/fd'))==fds and not forbidden.intersection(sys.modules)and all(v==0 for v in calls.values())
print(json.dumps({'result_sha256':sha256(module.reader.raw(result)).hexdigest(),'calls':calls,'forbidden_imports':0,'original_files_unchanged':True,'FD_unchanged':True}))
'''
    child=subprocess.run([sys.executable,'-B','-c',script,str(ROOT),str(original[0]),ARTIFACT],capture_output=True,text=True,timeout=60,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    assert child.returncode==0,child.stderr[-3000:]
    result=json.loads(child.stdout)
    assert result['result_sha256']==sha256(canonical(read(original))).hexdigest()
    assert result['calls']=={'DB':0,'network':0,'CAS_put':0,'process_or_CLI':0}and result['forbidden_imports']==0 and result['original_files_unchanged']and result['FD_unchanged']

def test_public_numeric_fixture_is_the_original_projection_with_explicit_software_scope(original):
    fixture=json.loads((ROOT/'research/fixtures/supply-material-quantity-own-20261031.json').read_bytes())
    result=read(original);raw=canonical(result)
    assert fixture['result']==result and fixture['result_sha256']==sha256(raw).hexdigest()
    assert fixture['canonical_result_bytes']==len(raw)<=2*1024**2
    assert fixture['projection_code_sha256']==quantities.CODE_SHA256
    assert fixture['effective_rights']==result['source']['effective_rights']=={'use':True,'display':True,'redistribute':True}
    assert fixture['scope']=='software_research_only'and fixture['G0_G4']=='not_assessed'and fixture['R2']=='not_approved'
    p=fixture['provenance'];assert p['observed_at']is None and p['qc']=='software_contract_only_not_farm_measurements'
    assert p['raw_sha256']==fixture['result_sha256']and p['source_artifact_sha256']==ARTIFACT
    assert p['available_at']==p['published_at']==p['retrieved_at']and p['reviewer']=='native-gpt-6.1-sol-xhigh'
    notice=ROOT/fixture['notice']['repository_path'];assert sha256(notice.read_bytes()).hexdigest()==fixture['notice']['sha256']
