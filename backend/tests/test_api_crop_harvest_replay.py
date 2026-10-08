from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import api_crop_harvest_replay as public
from app import crop_harvest_current_query as current
from test_crop_harvest_current_query import forbid_all_reads_math
from test_crop_harvest import save_native

REFERENCE=Path(__file__).resolve().parents[2]/'research/artifacts/crop-harvest-current-query-implementation-reference-20261008.json'
REFERENCE_SHA='3e845e6add86acf1c5cb25b0c104a4df90c33aeb3554ea90164148d41f3f3cbe'


@pytest.fixture
def source():
    raw=REFERENCE.read_bytes();assert sha256(raw).hexdigest()==REFERENCE_SHA
    evidence=json.loads(raw)['actual_registered_query_evidence'];saved=evidence['registered_record']
    record={'result_id':saved['result_id'],'payload_raw':saved['payload_raw_utf8'].encode(),
        'payload_sha256':saved['payload_sha256'],'recorded_at':datetime.fromisoformat(saved['recorded_at'])}
    return {'record':record,'summary':evidence['summary'],'page':{'start':0,'next':6,'total':6,'records':evidence['rows']},
        'identity':evidence['identity']}


def project(source):return public.project_harvest_result(source,view='records',limit=64)


def test_saved_SCRAM_summary_and_all_rows_keep_values_without_math(source,monkeypatch):
    forbid_all_reads_math(monkeypatch);before=deepcopy(source);fd=len(os.listdir('/proc/self/fd'))
    full=project(source);decoded=json.loads(public._public_bytes(full))
    assert decoded['page']['records']==source['page']['records']
    assert decoded['reference']['source']==source['summary']['source']
    assert decoded['reference']['parent_result_id']==source['summary']['source']['result_id']
    assert decoded['reference']['row_chain_sha256']==source['summary']['row_chain_sha256']
    assert decoded['result_id']==source['record']['result_id'] and decoded['recorded_at']==source['record']['recorded_at'].astimezone(timezone.utc).isoformat().replace('+00:00','Z')
    summary_source={**source,'page':None};summary=public.project_harvest_result(summary_source).model_dump(mode='json')
    assert summary['summary']==source['summary'] and summary['page'] is None
    assert summary['reference']==decoded['reference'] and summary['reference']['gates']=='not_assessed'
    assert summary['reference']['rights_or_gate_approval'] is False
    assert summary['reference']['projection_code_sha256']==public.CODE_SHA256
    assert source==before and len(os.listdir('/proc/self/fd'))==fd
    excluded={'tenant_id','integrity_signature','payload_raw','payload_raw_utf8','registered_by','directory','dsn','key','rights'}
    def check(value):
        if isinstance(value,dict):
            assert not excluded&set(value)
            for v in value.values():check(v)
        elif isinstance(value,list):
            for v in value:check(v)
    check(decoded);check(summary)
    responses={}
    for name,value in [('summary',public.project_harvest_result(summary_source)),('records',full)]:
        raw=public._public_bytes(value)
        responses[name]={'bytes':len(raw),'sha256':sha256(raw).hexdigest(),'raw_utf8':raw.decode()}
    save_native('public-harvest-projection.json',{'scope':'owned_recorded_actual_SCRAM_values_not_new_DB',
        'source_receipt_sha256':REFERENCE_SHA,'source_result_id':source['record']['result_id'],
        'source_payload_sha256':source['record']['payload_sha256'],'responses':responses,'preserved_rows':6,
        'RHS_calls':0,'harvest_regeneration_calls':0,'registration_calls':0,'new_proof_calls':0,
        'FD_before_after':[fd,fd],'input_unchanged':True,'private_fields_excluded':True,'gates':'not_assessed'})


def test_split_and_empty_end_pages_preserve_original_order(source):
    rows=source['page']['records'];seen=[];responses=[]
    for start in (0,3,6):
        selected={**source,'page':{'start':start,'next':min(start+3,6),'total':6,'records':rows[start:start+3]}}
        projected=public.project_harvest_result(selected,view='records',limit=3)
        raw=public._public_bytes(projected);responses.append({'bytes':len(raw),'sha256':sha256(raw).hexdigest(),'raw_utf8':raw.decode()})
        value=projected.model_dump(mode='json')
        assert value['summary'] is None and value['page']['next_offset']==(3 if start==0 else None)
        seen.extend(value['page']['records'])
    assert seen==rows
    save_native('public-harvest-split.json',{'full_split_equal':True,'rows':len(seen),'responses':responses})


MUTATIONS=[
    ('top','private_path','/owned/private'),('record','integrity_signature','owned-secret'),
    ('record','payload_sha256','0'*64),('record','result_id','foreign'),('record','recorded_at',datetime(2026,10,1)),
    ('identity','code_sha256','0'*64),('identity','approved',True),('identity','rights_or_gate_approval',True),
    ('identity','rights_or_gate_approval',0),('summary','directory','/owned/private'),
    ('summary.source','payload_sha256','0'*64),('summary','row_count',7),('summary','row_chain_sha256','0'*64),
    ('summary','allocation_sha256','0'*64),('summary','code_sha256','0'*64),
    ('summary.allocation_parameters','approved',True),('summary.allocation_parameters.rules.0.fraction','unit','percent'),
    ('summary.observation_comparisons.0.observation','approved',True),
    ('summary.observation_comparisons.0','status','incomplete_selected_window'),
    ('page','directory','/owned/private'),('page','start',False),('page','next',5),('page','total',7),
    ('row','approved',True),('removal.source','artifact_sha256','0'*64),('row','mass_row_sha256','0'*64),
    ('row','allocation_sha256','0'*64),('row','rights_or_gate_approval',True),('row','rights_or_gate_approval',0),
    ('mass','farm','foreign'),('mass','removal_sha256','0'*64),('mass','code_sha256','0'*64),
    ('mass.fresh_matter','unit','kg_FW/m2_crop'),('mass.fresh_matter','value',True),
    ('mass.fresh_matter','value',-1),('mass.fresh_matter','value',float('inf')),
    ('mass.parameters','sha256','0'*64),('removal','leaf',{'value':100,'unit':'mg_CH2O/m2_floor'}),
    ('removal','kind','model_terminal_outflow'),('removal.position','event',True),
    ('removal','start_at','2026-02-30T00:00:00Z'),('removal','start_at','2026-10-01T00:00:00.1Z'),
    ('row.allocations.0.fraction','value','0.9'),('row.allocations.0','purpose','disposal'),
    ('exact','denominator','0'),('exact','numerator','01'),('exact','secret','owned-secret'),('quantity','value',1),
]


@pytest.mark.parametrize('path,key,value',MUTATIONS)
def test_mixed_unknown_or_invalid_values_hold(source,path,key,value):
    row=source['page']['records'][0];mass=row['mass'];removal=mass['removal']
    q=row['unassigned']['quantities']['fresh_matter']
    roots={**source,'top':source,'row':row,'mass':mass,'removal':removal,'quantity':q,'exact':q['exact']}
    keys=path.split('.');target=roots[keys[0]]
    for part in keys[1:]:target=target[int(part)] if isinstance(target,list) else target[part]
    target[key]=deepcopy(value)
    with pytest.raises(public.HarvestProjectionHold):project(source)


@pytest.mark.parametrize('case',['cohort-length','duplicate-row','noncanonical','negative','underflow','empty-group'])
def test_vector_partition_and_rational_boundaries_hold(source,case):
    row=source['page']['records'][0];q=row['unassigned']['quantities']['fresh_matter']
    if case=='cohort-length':row['mass']['removal']['cohorts']['fruit_number'].pop()
    elif case=='duplicate-row':source['page']['records'][1]=deepcopy(row)
    elif case=='noncanonical':q.update(value=1,exact={'numerator':'2','denominator':'2'})
    elif case=='negative':q.update(value=-1,exact={'numerator':'-1','denominator':'1'})
    elif case=='underflow':q.update(value=0,exact={'numerator':'1','denominator':'1'+'0'*1000})
    else:source['summary']['totals_by_kind_and_purpose']['model_terminal_outflow']['disposal']['quantities']['number'].update(value=1,exact={'numerator':'1','denominator':'1'})
    with pytest.raises(public.HarvestProjectionHold):project(source)


@pytest.mark.parametrize('view,limit',[('unknown',64),('records',None),('records',True),('records',0),('records',65),('summary',64)])
def test_invalid_view_or_page_limit_holds(source,view,limit):
    with pytest.raises(public.HarvestProjectionHold):public.project_harvest_result(source,view=view,limit=limit)


def test_public_bytes_enforce_whole_response_bound(source):
    value=project(source);row=value.page.records[0]
    replacement=row.mass.removal.position.model_copy(update={'input_id':'x'*public.MAX_RESPONSE_BYTES})
    mass=row.mass.model_copy(update={'removal':row.mass.removal.model_copy(update={'position':replacement})})
    value.page.records[0]=row.model_copy(update={'mass':mass})
    with pytest.raises(public.HarvestProjectionHold):public._public_bytes(value)


def test_signed_observation_difference_and_incomplete_are_explicit(source):
    observation=deepcopy(source['summary']['observation_comparisons'][0]['observation']);observation['fresh_matter']['value']=0
    q={'value':.5,'unit':'kg_FW/m2_floor','exact':{'numerator':'1','denominator':'2'}}
    diff={'value':-.5,'unit':'kg_FW/m2_floor','exact':{'numerator':'-1','denominator':'2'}}
    value={'observation':observation,'status':'compared_synthetic_fixture','modeled_fresh_matter':q,'observed_minus_modeled':diff}
    assert public.Comparison.model_validate(value).model_dump(mode='json')==value
    value.update(status='incomplete_selected_window',modeled_fresh_matter=None,observed_minus_modeled=None)
    assert public.Comparison.model_validate(value).model_dump(mode='json')==value


def test_owned_source_hold_stays_held_without_projection_regeneration(source,monkeypatch):
    harvest=current.harvest;registry=current.registry;packet=registry._decode(source['record']['payload_raw'])
    held={**packet['source'],'source_status':'hold'};first=source['page']['records'][0]['mass']['parameters']
    mass_profile={k:v for k,v in first.items() if k not in ('sha256','segment','rounding')}
    mass_profile.update(source=held,segments=[first['segment']])
    mass=harvest._mass_parameters(registry._canonical(mass_profile))
    profile=deepcopy(source['summary']['allocation_parameters']);profile.update(source=held,mass_parameter_sha256=mass[1])
    allocation=harvest._allocation_parameters(registry._canonical(profile),mass);rows=[]
    for old in source['page']['records']:
        removed=old['mass']['removal']
        ledger=harvest._row(held,removed['kind'],removed['position'],removed['start_at'],removed['end_at'],
            removed['carbohydrate']['value'],removed['number']['value'],removed['cohorts'])
        rows.append(harvest._allocation_row(harvest._mass_row(ledger,mass),allocation))
    summary=harvest._allocation_totals(rows,allocation)
    owned_root=public._hash({'scope':'owned_source_hold_probe_not_actual_DB','rows':rows,'summary':summary})
    base=registry._base('tenant-1',packet['parent_result_id'],packet['farm'],held,
        {'mass_sha256':mass[1],'allocation_sha256':allocation[1]})
    raw=registry._packet(base,{'artifact_sha256':owned_root,'row_count':6,'row_chain_sha256':summary['row_chain_sha256']})
    metadata=registry._decode(raw);record={**source['record'],'result_id':metadata['result_id'],'payload_raw':raw,'payload_sha256':sha256(raw).hexdigest()}
    identity={'version':current.VERSION,'code_sha256':current.CODE_SHA256,'dependency_sha256':current.DEPENDENCY_SHA256,
        'result_id':record['result_id'],'payload_sha256':record['payload_sha256'],'artifact_sha256':owned_root,
        'parent_source':held,'rights_or_gate_approval':False}
    value={'record':record,'summary':summary,'page':{'start':0,'next':6,'total':6,'records':rows},'identity':identity}
    # All regeneration above constructs an owned probe; the projection is read-only.
    forbid_all_reads_math(monkeypatch)
    projected=project(value).model_dump(mode='json')
    assert projected['reference']['source']['source_status']=='hold'
    assert projected['reference']['gates']=='not_assessed' and projected['reference']['rights_or_gate_approval'] is False
    assert projected['page']['records']==rows
    assert public.project_harvest_result({**value,'page':None}).model_dump(mode='json')['summary']==summary
    raw=public._public_bytes(project(value))
    save_native('public-harvest-hold-probe.json',{'scope':'owned_source_status_hold_probe_not_actual_DB',
        'source_status':'hold','projection_RHS_calls':0,'projection_harvest_regeneration_calls':0,
        'response':{'bytes':len(raw),'sha256':sha256(raw).hexdigest(),'raw_utf8':raw.decode()},'gates':'not_assessed'})


@pytest.mark.parametrize('name',['CODE_SHA256','MAX_RESPONSE_BYTES','MAX_ROWS'])
def test_changed_projection_policy_is_rejected(source,monkeypatch,name):
    monkeypatch.setattr(public,name,'0'*64 if name=='CODE_SHA256' else 1)
    with pytest.raises(public.HarvestProjectionHold):project(source)


def test_each_public_object_has_a_closed_schema():
    schema=public.HarvestReplay.model_json_schema()
    objects=[schema]+[v for v in schema['$defs'].values() if v.get('type')=='object']
    assert len(objects)>30 and all(v['additionalProperties'] is False for v in objects)


def test_fresh_import_opens_no_DB_network_or_extra_FDs():
    script='''import os,json,socket,psycopg
before=len(os.listdir('/proc/self/fd'));calls=[]
def forbidden(*a,**k):
 calls.append(True);raise AssertionError('public import opened DB/network')
psycopg.connect=socket.create_connection=forbidden
from app import api_crop_harvest_replay as public
assert len(os.listdir('/proc/self/fd'))==before and not calls
print(json.dumps({'FD_before_after':[before,before],'DB_network_calls':len(calls),'code_sha256':public.CODE_SHA256,'pid':os.getpid()}))
'''
    child=subprocess.run([sys.executable,'-c',script],capture_output=True,text=True,timeout=30)
    assert child.returncode==0,child.stderr[-2000:]
    value=json.loads(child.stdout);assert value['code_sha256']==public.CODE_SHA256 and value['pid']!=os.getpid()
    save_native('public-harvest-import.json',{'actual_child_exit':child.returncode,'result':value,
        'stdout_sha256':sha256(child.stdout.encode()).hexdigest(),'stderr_sha256':sha256(child.stderr.encode()).hexdigest()})
