"""Exact declared periods and real stored-source binding; synthetic QA only."""
from datetime import datetime,timedelta,timezone
from copy import deepcopy
from decimal import localcontext
from fractions import Fraction
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys

import pytest

from login_database import login_database,login_scope
from test_economic_batch_calculation import PROFILE
from test_supply_material_quantities import original,ARTIFACT


ROOT=Path(__file__).resolve().parents[2]
PRODUCT_HOLDS=['farm_current_custody_unverified','resource_cost_declaration_unregistered',
    'window_cost_allocation_not_established']


def raw(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def document():
    return {'schema_version':'supply-material-resource-cost-scope-request-v1',
        'declaration':{'declaration_id':'resource-declaration','revision':'r1','origin':'user',
            'evidence_level':'assumed','relation':'independent_user_assumption','source_ref':'self-authored-resource-scope',
            'assumption_scope':'scenario-1','available_at':'2026-10-01T00:00:00Z'},
        'material':{'root_sha256':'a'*64,'projection_code_sha256':'b'*64,'quantity_sha256':'c'*64,'first_frame':2,'last_frame':3},
        'economic':{'job_id':'10000000-0000-4000-8000-000000000001','input_sha256':'d'*64,
            'artifact_sha256':'e'*64,'trace_id':'f'*64,'publication_id':'20000000-0000-4000-8000-000000000002'},
        'costs':[{'category':'variable','cost_id':'electricity','cost_sha256':'1'*64,
            'quantity_input':{'input_id':'electricity-q','revision':'r1'},
            'unit_cost_input':{'input_id':'electricity-price','revision':'r1'},'resource_kind':'electricity',
            'period':{'kind':'billing','boundary':'half_open','calendar':'Asia/Seoul',
                'start_at':'2026-10-01T00:00:00.000001+09:00','end_at':'2026-11-01T00:00:00+09:00'},
            'included_items':['declared-energy-item'],'excluded_items':['tax'],'unknown_items':['demand-charge']} ]}


def test_closed_declaration_parses_without_an_economic_or_material_publisher():
    module=feature();value=document()
    assert type(module.MaterialCostScopeRequest.model_validate_json(raw(value)))is module.MaterialCostScopeRequest
    provenance=module.MaterialSourceProvenance.model_validate_json(raw({'source_ref':'unknown-publication',
        'metadata_sha256':'2'*64,'published_at':None,'available_at':None}))
    assert provenance.model_dump(mode='json')['published_at']is None


@pytest.mark.parametrize('fault',['extra','origin','evidence','relation','kind','period_kind','boundary','calendar',
    'naive','too_precise','reverse','empty_items','duplicate_items','overlapping_items','duplicate_cost','bool_frame',
    'reverse_frames','uppercase_sha','noncanonical_uuid'])
def test_closed_declaration_rejects_missing_meaning_or_ambiguous_types(fault):
    module=feature();value=document();cost=value['costs'][0];period=cost['period']
    if fault=='extra':value['tenant_id']='foreign'
    elif fault=='origin':value['declaration']['origin']='official'
    elif fault=='evidence':value['declaration']['evidence_level']='measured'
    elif fault=='relation':value['declaration']['relation']='derived_from_model'
    elif fault=='kind':cost.pop('resource_kind')
    elif fault=='period_kind':period['kind']='occurrence'
    elif fault=='boundary':period['boundary']='closed'
    elif fault=='calendar':period['calendar']='UTC'
    elif fault=='naive':period['start_at']='2026-10-01T00:00:00'
    elif fault=='too_precise':period['start_at']='2026-10-01T00:00:00.0000001Z'
    elif fault=='reverse':period['start_at']=period['end_at']
    elif fault=='empty_items':cost['included_items']=[]
    elif fault=='duplicate_items':cost['included_items']*=2
    elif fault=='overlapping_items':cost['unknown_items']=cost['included_items'].copy()
    elif fault=='duplicate_cost':value['costs']*=2
    elif fault=='bool_frame':value['material']['first_frame']=True
    elif fault=='reverse_frames':value['material']['first_frame']=4
    elif fault=='uppercase_sha':value['economic']['artifact_sha256']='A'*64
    else:value['economic']['job_id']='10000000000040008000000000000001'
    with pytest.raises(ValueError):module.MaterialCostScopeRequest.model_validate_json(raw(value))


def test_closed_declaration_bounds_costs_labels_and_names():
    module=feature()
    for field in ('costs','items','name'):
        value=document()
        if field=='costs':
            value['costs']=[{**deepcopy(value['costs'][0]),'cost_id':'cost-'+str(i)}for i in range(129)]
        elif field=='items':value['costs'][0]['included_items']=['item-'+str(i)for i in range(33)]
        else:value['declaration']['declaration_id']=' '+('d'*199)
        with pytest.raises(ValueError):module.MaterialCostScopeRequest.model_validate_json(raw(value))


@pytest.fixture
def current_cost(login_scope,monkeypatch):
    from app.economic_production_batches import BatchEconomicScenario
    import test_economic_batch_calculation as sources
    from test_economic_production_batches import scenario
    from test_economic_cost_query import ready
    data=scenario().model_dump();seed=data['variable_costs'][0]
    def cost(name,unit,quantity='2',paid='20'):
        value=deepcopy(seed);value['id']=name
        value['quantity'].update(input_id=name+'-q',unit=unit,value=quantity)
        value['unit_cost'].update(input_id=name+'-price',unit={'kWh_e':'KRW/kWh_e','L':'KRW/L','kg':'KRW/kg'}[unit],value='10')
        if paid is None:value.update(payment=None,paid_at=None)
        else:value['payment'].update(input_id=name+'-paid',value=paid)
        return value
    data['variable_costs']=(cost('electricity','kWh_e'),cost('fuel','L',paid=None),
        cost('water','L',quantity='0',paid='0'),cost('tiny-electricity','kWh_e',quantity='0.0000000000000000000000001',paid=None),
        cost('other-kg','kg'))
    selected=BatchEconomicScenario.model_validate(data)
    with monkeypatch.context()as patch:
        patch.setattr(sources,'scenario',lambda:selected)
        values,query=ready(login_scope)
    stored=query.read('tenant-1',str(values[9]['job_id']));assert stored is not None
    return values,query,stored,json.loads(stored.raw)


def request_for(original,current_cost,*,first=2,last=3,selected=None,start=None,end=None,kind='billing'):
    from app import crop_supply_material_quantities as quantities
    values,query,stored,envelope=current_cost;scenario=values[5]
    quantity=quantities.read_material_quantity_window(original[0],original[1],ARTIFACT,first_frame=first,last_frame=last)
    value=document();value['declaration']['available_at']=scenario.decision_at.isoformat()
    value['material']={'root_sha256':ARTIFACT,'projection_code_sha256':quantity['projection_code_sha256'],
        'quantity_sha256':sha256(quantities.reader.raw(quantity)).hexdigest(),'first_frame':first,'last_frame':last}
    value['economic']={'job_id':str(values[9]['job_id']),'input_sha256':envelope['input_sha256'],
        'artifact_sha256':sha256(stored.raw).hexdigest(),'trace_id':stored.result.trace_id,
        'publication_id':str(stored.publication_id)}
    lines={line['cost']['id']:line for line in envelope['result']['lines']};declarations=[]
    for cost_id,resource in selected or [('electricity','electricity'),('fuel','fuel'),('water','water')]:
        line=lines[cost_id];cost=line['cost'];item=deepcopy(document()['costs'][0])
        item.update(category=line['category'],cost_id=cost_id,cost_sha256=sha256(raw(cost)).hexdigest(),
            quantity_input={k:cost['quantity'][k]for k in ('input_id','revision')},
            unit_cost_input={k:cost['unit_cost'][k]for k in ('input_id','revision')},resource_kind=resource)
        item['included_items']=[resource+'-assumed-item']
        item['period'].update(kind=kind,start_at=start or'2026-10-01T07:08:48Z',end_at=end or'2026-10-01T07:08:56Z')
        declarations.append(item)
    value['costs']=declarations
    return value,quantity


def binder_for(original,current_cost,*,published=None,available=None):
    module=feature()
    metadata=ROOT/'research/fixtures/supply-material-quantity-own-20261031.json'
    provenance=module.MaterialSourceProvenance.model_validate_json(raw({'source_ref':'self-authored-material-provenance',
        'metadata_sha256':sha256(metadata.read_bytes()).hexdigest(),'published_at':published,'available_at':available}))
    return module.MaterialCostScopeBinding(original[0],original[1],ARTIFACT,current_cost[1],material_provenance=provenance)


def readonly(monkeypatch):
    import http.client
    import importlib.abc
    import socket
    import subprocess
    from psycopg import Connection
    from app.crop_morphology_artifact_io import MorphologyBlobStore
    from test_economic_cost_query import no_replay
    no_replay(monkeypatch);counts={'SQL_writes':0,'CAS_writes':0,'process':0,'extra_nonDB_network':0,'model_import':0,'model_advance':0}
    execute=Connection.execute
    def measured(conn,*args,**kwargs):
        cursor=execute(conn,*args,**kwargs)
        if(cursor.statusmessage or'').split(' ')[0]in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:
            counts['SQL_writes']+=1;pytest.fail('SQL write during read-only scope binding')
        return cursor
    def deny(name):
        def failed(*args,**kwargs):counts[name]+=1;pytest.fail(name+' during read-only scope binding')
        return failed
    monkeypatch.setattr(Connection,'execute',measured);monkeypatch.setattr(MorphologyBlobStore,'put',deny('CAS_writes'))
    monkeypatch.setattr(subprocess,'Popen',deny('process'));monkeypatch.setattr(socket,'create_connection',deny('extra_nonDB_network'))
    monkeypatch.setattr(socket.socket,'connect',deny('extra_nonDB_network'))
    monkeypatch.setattr(http.client.HTTPConnection,'request',deny('extra_nonDB_network'))
    forbidden={'app.crop_supply_season','app.crop_supply_material_owner','app.crop_supply_material_point',
        'app.crop_supply_material_artifact_producer','app.crop_growth_rates','app.crop_leaf_area'}
    for name in forbidden.intersection(sys.modules):
        loaded=sys.modules[name]
        for entry in ('advance','open_season','apply_material_point','adopt_material','produce_material_artifact','calculate'):
            if callable(getattr(loaded,entry,None)):monkeypatch.setattr(loaded,entry,deny('model_advance'))
    class Guard(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname in forbidden:deny('model_import')()
    monkeypatch.setattr(sys,'meta_path',[Guard(),*sys.meta_path])
    return counts


def unchanged_files(directory):
    return {path.name:(path.stat().st_size,path.stat().st_mtime_ns,sha256(path.read_bytes()).hexdigest())for path in directory.iterdir()}


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_current_published_cost_and_trusted_material_bind_without_allocating_window_cost(original,current_cost,monkeypatch,tmp_path):
    module=feature();values,query,stored,envelope=current_cost
    declaration,quantity=request_for(original,current_cost);binder=binder_for(original,current_cost)
    before=unchanged_files(original[0]);counts=readonly(monkeypatch)
    encoded=binder.prepare('tenant-1',raw(declaration));result=json.loads(encoded)
    assert encoded==raw(result)and 1<=len(encoded)<=2097152
    assert result['schema_version']=='supply-material-resource-cost-scope-binding-v1'
    assert set(result)=={'schema_version','binding_id','scope','claim_scope','tenant_id','request_sha256','declaration',
        'material','economic','costs','unselected_costs','resource_kinds_not_selected','product_holds','as_of_decision',
        'code_sha256','dependency_sha256','G0_G4','R2'}
    assert result['code_sha256']==sha256(Path(module.__file__).read_bytes()).hexdigest()
    assert result['dependency_sha256']=={name:sha256((ROOT/'backend/app'/name).read_bytes()).hexdigest()for name in
        ('crop_supply_material_quantities.py','economic_cost_query.py','economic_batch_query.py','content_access.py')}
    assert result['binding_id']==sha256(raw({k:v for k,v in result.items()if k!='binding_id'})).hexdigest()
    assert result['request_sha256']==sha256(raw(declaration)).hexdigest()and result['declaration']==declaration['declaration']
    assert result['material']['quantity']==quantity and result['material']['quantity_sha256']==declaration['material']['quantity_sha256']
    assert result['material']['temporal_support']['kind']=='interval'and result['material']['temporal_support']['boundary']=='half_open'
    base=envelope['input']['base_input'];trace=envelope['result'];ledger=trace['base_result']['ledger']
    assert result['economic']=={**declaration['economic'],'result_sha256':envelope['result_sha256'],
        'code_sha256':envelope['code_sha256'],'environment_sha256':envelope['environment_sha256'],
        'published_at':stored.published_at.isoformat(),'scenario_id':base['scenario_id'],
        'scenario_revision':base['scenario_revision'],'scenario_sha256':base['scenario_sha256'],
        'scenario_source_job_id':base['scenario_source_job_id'],'decision_at':ledger['decision_at'],
        'period_start':trace['period_start'],'period_end':trace['period_end']}
    original_lines={line['cost']['id']:line for line in envelope['result']['lines']}
    for row,request_line in zip(result['costs'],declaration['costs'],strict=True):
        assert row['reference']==request_line and row['original_line']==original_lines[request_line['cost_id']]
        assert row['amount_scope']=='original_cost_line_only'and row['allocated_window_cost']is None
        assert row['temporal_relation']=={'relation':'equal','coverage':'whole_window'}
        assert row['period_semantics_established']=='billing'and set(row['other_period_kinds_not_established'])=={'purchase','usage'}
    assert [row['cost_id']for row in result['unselected_costs']]==['tiny-electricity','other-kg']
    assert result['resource_kinds_not_selected']==[]and result['product_holds']==PRODUCT_HOLDS
    assert result['as_of_decision']=={'material_published_relation':'unknown','material_available_relation':'unknown','ex_ante_eligibility':'not_established'}
    assert result['scope']=='software_research_only'and result['G0_G4']=='not_assessed'and result['R2']=='not_approved'
    assert binder.prepare('tenant-1',raw(declaration))==encoded
    result['material']['quantity']['frames'][0]['phase']='forged';result['costs'][0]['original_line']['incurred']='999'
    assert binder.prepare('tenant-1',raw(declaration))==encoded
    again=query.read('tenant-1',str(values[9]['job_id']))
    assert again.raw==stored.raw and again.publication_id==stored.publication_id and again.published_at==stored.published_at
    assert unchanged_files(original[0])==before and all(v==0 for v in counts.values())
    proof={'binding_sha256':sha256(encoded).hexdigest(),'binding_bytes':len(encoded),'binding_id':json.loads(encoded)['binding_id'],
        'material_root_sha256':ARTIFACT,'quantity_sha256':declaration['material']['quantity_sha256'],
        'cost_artifact_sha256':sha256(stored.raw).hexdigest(),'trace_id':stored.result.trace_id,
        'publication_id':str(stored.publication_id),'published_at':stored.published_at.isoformat(),
        'actual_trusted_material_and_real_SCRAM_published_cost':True,'cost_execution_scope_present':False,
        'allocated_window_cost':None,'unchanged_first_publication':True,'permitted_PG_reads':True,
        'forbidden_side_effect_counts':counts,'source_files_unchanged':True,'product_holds':PRODUCT_HOLDS,
        'G0_G4':'not_assessed','R2':'not_approved'}
    (tmp_path/'material-cost-binding-v1.json').write_bytes(encoded)
    (tmp_path/'material-cost-original-cost-v1.json').write_bytes(stored.raw)
    (tmp_path/'material-cost-binding-receipt-v1.private.json').write_text(json.dumps(proof,indent=2)+'\n')


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('start,end,relation,coverage',[
    ('2026-10-01T07:08:52Z','2026-10-01T07:09:00Z','overlaps','partial_window'),
    ('2026-10-01T07:08:50Z','2026-10-01T07:08:54Z','contains','partial_window'),
    ('2026-10-01T07:09:00Z','2026-10-01T07:09:04Z','before','no_overlap'),
])
def test_valid_independent_partial_and_disjoint_periods_return_original_costs(original,current_cost,start,end,relation,coverage):
    declaration,_=request_for(original,current_cost,start=start,end=end,kind='usage')
    result=json.loads(binder_for(original,current_cost).prepare('tenant-1',raw(declaration)))
    for row in result['costs']:
        assert row['temporal_relation']=={'relation':relation,'coverage':coverage}
        assert row['allocated_window_cost']is None and row['original_line']['cost']['purpose']=='production'
        assert row['reference']['period']['kind']=='usage'and set(row['other_period_kinds_not_established'])=={'purchase','billing'}


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_equal_time_material_boundary_is_point_and_not_empty_billing(original,current_cost):
    declaration,quantity=request_for(original,current_cost,first=0,last=1,start='2026-10-01T07:08:44Z',end='2026-10-01T07:08:45Z')
    result=json.loads(binder_for(original,current_cost).prepare('tenant-1',raw(declaration)))
    support=result['material']['temporal_support'];assert support['kind']=='point'and support['boundary']=='point'
    assert support['start_utc_exact']==support['end_utc_exact']
    exact=support['start_utc_exact'];instant=Fraction(int(exact['numerator']),int(exact['denominator']))
    epoch=feature()._utc_fraction(datetime(2026,10,1,7,tzinfo=timezone.utc))
    assert instant==epoch+Fraction(274914959,524288)and exact['unit']=='s_since_unix_epoch'
    assert result['material']['quantity']==quantity and [f['phase']for f in quantity['frames']]==['material_before','material_after']
    assert all(row['temporal_relation']=={'relation':'point_inside','coverage':'point_covered'}for row in result['costs'])


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_original_money_NULL_zero_and_scientific_text_survive_ambient_context(original,current_cost):
    declaration,_=request_for(original,current_cost,selected=[('fuel','fuel'),('water','water'),('tiny-electricity','electricity')])
    binder=binder_for(original,current_cost)
    with localcontext()as context:
        context.prec=7;context.capitals=0
        result=json.loads(binder.prepare('tenant-1',raw(declaration)))
    originals={line['cost']['id']:line for line in current_cost[3]['result']['lines']}
    for row in result['costs']:assert row['original_line']==originals[row['reference']['cost_id']]
    unknown,zero,tiny=[row['original_line']for row in result['costs']]
    assert unknown['bank_paid_in_period']is None and unknown['remaining_payable_at_period_end']is None
    assert zero['bank_paid_in_period']=='0'and zero['payment_status']=='declared_bank_payment'
    assert 'E'in tiny['incurred']and 'e'not in tiny['incurred']


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_resource_kind_is_explicit_and_L_or_cost_id_never_infers_it(original,current_cost):
    declaration,_=request_for(original,current_cost,selected=[('fuel','water')],kind='purchase')
    result=json.loads(binder_for(original,current_cost).prepare('tenant-1',raw(declaration)))
    assert result['costs'][0]['reference']['resource_kind']=='water'
    assert result['costs'][0]['original_line']['cost']['id']=='fuel'
    assert result['resource_kinds_not_selected']==['electricity','fuel']
    wrong,_=request_for(original,current_cost,selected=[('other-kg','electricity')])
    with pytest.raises(feature().MaterialCostScopeHold):binder_for(original,current_cost).prepare('tenant-1',raw(wrong))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_every_original_identity_pin_and_declaration_decision_must_match_current_sources(original,current_cost):
    module=feature();declaration,_=request_for(original,current_cost);binder=binder_for(original,current_cost)
    paths=[('material','root_sha256'),('material','projection_code_sha256'),('material','quantity_sha256'),
        ('economic','input_sha256'),('economic','artifact_sha256'),('economic','trace_id'),('economic','publication_id')]
    for section,key in paths:
        value=deepcopy(declaration);value[section][key]='30000000-0000-4000-8000-000000000003'if key=='publication_id'else'0'*64
        with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',raw(value))
    for field in ('cost_id','cost_sha256','category','quantity_input','unit_cost_input'):
        value=deepcopy(declaration);cost=value['costs'][0]
        if field=='cost_id':cost[field]='missing-cost'
        elif field=='cost_sha256':cost[field]='0'*64
        elif field=='category':cost[field]='fixed'
        else:cost[field]['revision']='different-revision'
        with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',raw(value))
    future=deepcopy(declaration);future['declaration']['available_at']='2099-01-01T00:00:00Z'
    with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',raw(future))
    with pytest.raises(PermissionError):binder.prepare('foreign',raw(declaration))
    assert binder.prepare('tenant-1',raw(declaration))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_current_read_scopes_invalidate_previous_binding_and_restore_same_bytes(original,current_cost):
    declaration,_=request_for(original,current_cost);binder=binder_for(original,current_cost);expected=binder.prepare('tenant-1',raw(declaration))
    principal=current_cost[0][4]
    for scope in ('metadata','artifact','economic_batch_source_read','decision_context_read','market_hold_context_read'):
        principal['scopes'].remove(scope)
        try:
            with pytest.raises(PermissionError):binder.prepare('tenant-1',raw(declaration))
        finally:principal['scopes'].add(scope)
        assert binder.prepare('tenant-1',raw(declaration))==expected


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_material_source_change_during_genuine_cost_read_suppresses_binding(original,current_cost,monkeypatch):
    module=feature();declaration,_=request_for(original,current_cost);binder=binder_for(original,current_cost)
    query=current_cost[1];read=query._read_raw;path=original[0]/ARTIFACT;initial=path.read_bytes();changed=[]
    def drift(*args,**kwargs):
        value=read(*args,**kwargs)
        if not changed:changed.append(True);path.write_bytes(initial+b' ')
        return value
    monkeypatch.setattr(query,'_read_raw',drift)
    try:
        with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',raw(declaration))
        assert changed==[True]
    finally:path.write_bytes(initial)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_cost_permission_loss_inside_real_read_never_releases_a_buffer(original,current_cost,monkeypatch):
    declaration,_=request_for(original,current_cost);binder=binder_for(original,current_cost)
    query=current_cost[1];read=query._read_raw;principal=current_cost[0][4];changed=[]
    def revoke(*args,**kwargs):
        value=read(*args,**kwargs)
        if not changed:changed.append(True);principal['scopes'].remove('artifact')
        return value
    monkeypatch.setattr(query,'_read_raw',revoke)
    try:
        with pytest.raises(PermissionError):binder.prepare('tenant-1',raw(declaration))
        assert changed==[True]
    finally:principal['scopes'].add('artifact')


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_current_embedded_material_use_and_display_are_required(original,current_cost,monkeypatch):
    from app import crop_supply_material_quantities as quantities
    module=feature();declaration,_=request_for(original,current_cost);binder=binder_for(original,current_cost);load=quantities.reader._load
    for right in ('use','display'):
        def denied(*args,**kwargs):
            manifest,frames,raws=load(*args,**kwargs);manifest['effective_rights'][right]=False;return manifest,frames,raws
        with monkeypatch.context()as patch:
            patch.setattr(quantities.reader,'_load',denied)
            with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',raw(declaration))
    assert binder.prepare('tenant-1',raw(declaration))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_relation_function_replacement_is_held_without_calling_forgery(original,current_cost,monkeypatch):
    module=feature();declaration,_=request_for(original,current_cost);binder=binder_for(original,current_cost);calls=[]
    def forged(*args):calls.append(True);return {'relation':'equal','coverage':'whole_window'}
    monkeypatch.setattr(module,'_coverage',forged)
    with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',raw(declaration))
    assert calls==[]


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_canonical_request_size_duplicate_keys_and_mutable_binding_inputs_are_closed(original,current_cost):
    module=feature();declaration,_=request_for(original,current_cost);binder=binder_for(original,current_cost);encoded=raw(declaration)
    duplicate=encoded[:-1]+b',"schema_version":"supply-material-resource-cost-scope-request-v1"}'
    for candidate in (encoded+b' ',duplicate,b' '*131073,json.dumps(declaration,indent=2).encode(),encoded.decode()):
        with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',candidate)
    query=current_cost[1];old=query.authority._source
    from app.economic_batch_source_store import EconomicBatchSourceStore
    query.authority._source=EconomicBatchSourceStore(old.dsn,old.schema,principal_provider=query.jobs.principal_provider,runtime_identity=query.jobs.runtime_identity)
    try:
        with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',encoded)
    finally:query.authority._source=old
    assert binder.prepare('tenant-1',encoded)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_separate_declared_provenance_times_are_preserved_without_ex_ante_claim(original,current_cost):
    declaration,_=request_for(original,current_cost);decision=current_cost[0][5].decision_at
    before=(decision-timedelta(microseconds=1)).isoformat();at=decision.isoformat();after=(decision+timedelta(microseconds=1)).isoformat()
    for published,available,expected_pub,expected_available in [(None,None,'unknown','unknown'),
            (before,at,'before_or_at_decision','before_or_at_decision'),(after,after,'after_decision','after_decision')]:
        result=json.loads(binder_for(original,current_cost,published=published,available=available).prepare('tenant-1',raw(declaration)))
        assert result['as_of_decision']=={'material_published_relation':expected_pub,
            'material_available_relation':expected_available,'ex_ante_eligibility':'not_established'}
        assert result['material']['provenance']['published_at']==published
        assert result['material']['provenance']['available_at']==available


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_publication_metadata_change_during_real_query_is_held(original,current_cost,monkeypatch):
    from uuid import UUID
    module=feature();declaration,_=request_for(original,current_cost);binder=binder_for(original,current_cost)
    query=current_cost[1];metadata=query._metadata;seen=[]
    def changed(*args,**kwargs):
        value=metadata(*args,**kwargs)
        if value is None:return value
        seen.append(True)
        if len(seen)==2:
            job,raw_input,selected,publication=value
            publication={**publication,'publication_id':UUID('30000000-0000-4000-8000-000000000003')}
            return job,raw_input,selected,publication
        return value
    monkeypatch.setattr(query,'_metadata',changed)
    with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',raw(declaration))
    assert len(seen)>=2


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_pending_wrong_family_and_foreign_cost_jobs_do_not_become_binding_sources(original,current_cost):
    from test_economic_batch_calculation import request
    module=feature();values,query,stored,envelope=current_cost
    jobs,_,_,_,principal,scenario,_,service,base,_,_=values
    principal['scopes'].add('simulation_execute')
    try:
        pending=service.submit('tenant-1',request(scenario,'scope-pending-cost'))
        old=base.submit('tenant-1',request(scenario,'scope-old-batch'))
    finally:principal['scopes'].remove('simulation_execute')
    declaration,_=request_for(original,current_cost);binder=binder_for(original,current_cost)
    for job in (pending,old):
        candidate=deepcopy(declaration);candidate['economic']['job_id']=str(job['job_id'])
        with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',raw(candidate))
        assert jobs.get_job('tenant-1',job['job_id'])['state']=='queued'
        assert jobs.get_publication('tenant-1',job['job_id'])is None
    assert query.read('tenant-1',str(values[9]['job_id'])).raw==stored.raw


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_constructor_requires_exact_query_access_and_revalidated_closed_provenance(original,current_cost):
    from app.content_access import ContentAccess
    from app.economic_cost_query import EconomicCostResultQuery
    module=feature();query=current_cost[1]
    provenance=module.MaterialSourceProvenance.model_validate_json(raw({'source_ref':'self-authored-provenance',
        'metadata_sha256':'a'*64,'published_at':None,'available_at':None}))
    class QuerySubclass(EconomicCostResultQuery):pass
    class AccessSubclass(ContentAccess):pass
    for access,cost_query,metadata in [(original[1],object(),provenance),
            (original[1],QuerySubclass(query.authority),provenance),
            (AccessSubclass(original[1].owner_uid,original[1].reader_gid),query,provenance),
            (original[1],query,provenance.model_copy(update={'metadata_sha256':'invalid'}))]:
        with pytest.raises(module.MaterialCostScopeHold):
            module.MaterialCostScopeBinding(original[0],access,ARTIFACT,cost_query,material_provenance=metadata)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_current_cost_root_or_provider_replacement_holds_and_restoration_preserves_selection(original,current_cost,tmp_path):
    module=feature();declaration,_=request_for(original,current_cost);binder=binder_for(original,current_cost)
    query=current_cost[1];jobs=query.jobs;expected=binder.prepare('tenant-1',raw(declaration))
    original_root,provider=jobs.artifact_root,jobs.principal_provider
    jobs.artifact_root=tmp_path/'unselected-cost-root'
    try:
        with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',raw(declaration))
    finally:jobs.artifact_root=original_root
    jobs.principal_provider=lambda:provider()
    try:
        with pytest.raises(module.MaterialCostScopeHold):binder.prepare('tenant-1',raw(declaration))
    finally:jobs.principal_provider=provider
    assert binder.prepare('tenant-1',raw(declaration))==expected


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_pointer_lambda_and_provenance_replacement_cannot_bypass_final_binding(original,current_cost,monkeypatch):
    from psycopg import Connection
    module=feature();declaration,_=request_for(original,current_cost);binder=binder_for(original,current_cost)
    baseline=json.loads(binder.prepare('tenant-1',raw(declaration)))
    assert baseline['as_of_decision']=={'material_published_relation':'unknown',
        'material_available_relation':'unknown','ex_ante_eligibility':'not_established'}
    assert baseline['material']['quantity']['source']['artifact_sha256']==ARTIFACT
    assert baseline['economic']['trace_id']==current_cost[2].result.trace_id
    replacement=module.MaterialSourceProvenance.model_validate_json(raw({'source_ref':'late-untrusted-replacement',
        'metadata_sha256':'0'*64,'published_at':'1900-01-01T00:00:00Z','available_at':'1900-01-01T00:00:00Z'}))
    changed=[];forged_calls=[];execute=Connection.execute
    def forged_fixed():
        forged_calls.append(True)
        return binder._fixed
    def changed_during_actual_publication_read(conn,statement,*args,**kwargs):
        cursor=execute(conn,statement,*args,**kwargs)
        text=statement if type(statement)is str else statement.as_string(conn)
        table='"'+current_cost[1].jobs.schema+'"."job_publications"'
        if not changed and text.lstrip().upper().startswith('SELECT * FROM')and table in text:
            changed.append(True)
            binder._pointers=lambda:forged_fixed()
            binder.material_provenance=replacement
        return cursor
    monkeypatch.setattr(Connection,'execute',changed_during_actual_publication_read)
    with pytest.raises(module.MaterialCostScopeHold):
        binder.prepare('tenant-1',raw(declaration))
        assert changed==[True]
    assert changed==[True]and forged_calls==[]


def feature():
    # Import in the test body: a missing new feature is a collected functional RED.
    return import_module('app.crop_supply_material_cost_scope_binding')


@pytest.mark.parametrize('a,b,c,d,relation,coverage',[
    (0,1,2,3,'before','no_overlap'),
    (0,1,1,2,'meets','no_overlap'),
    (0,2,1,3,'overlaps','partial_window'),
    (0,1,0,2,'starts','whole_window'),
    (1,2,0,3,'during','whole_window'),
    (1,2,0,2,'finishes','whole_window'),
    (0,2,0,2,'equal','whole_window'),
    (0,2,1,2,'finished_by','partial_window'),
    (0,3,1,2,'contains','partial_window'),
    (0,2,0,1,'started_by','partial_window'),
    (1,3,0,2,'overlapped_by','partial_window'),
    (1,2,0,1,'met_by','no_overlap'),
    (2,3,0,1,'after','no_overlap'),
])
def test_exact_positive_window_relation_and_coverage(a,b,c,d,relation,coverage):
    assert feature()._coverage(*map(Fraction,(a,b,c,d)))=={'relation':relation,'coverage':coverage}


@pytest.mark.parametrize('point,relation,coverage',[
    (0,'point_before','point_not_covered'),
    (1,'point_at_start','point_covered'),
    (2,'point_inside','point_covered'),
    (3,'point_at_end','point_not_covered'),
    (4,'point_after','point_not_covered'),
])
def test_zero_duration_material_selection_uses_point_semantics(point,relation,coverage):
    at=Fraction(point)
    assert feature()._coverage(at,at,Fraction(1),Fraction(3))=={'relation':relation,'coverage':coverage}


def test_submicrosecond_sides_of_start_and_end_are_not_rounded_to_boundaries():
    module=feature();epsilon=Fraction(1,2**40);left,right=Fraction(1),Fraction(2)
    assert module._coverage(left-epsilon,left+epsilon,left,right)=={'relation':'overlaps','coverage':'partial_window'}
    assert module._coverage(left-epsilon,left-epsilon,left,right)=={'relation':'point_before','coverage':'point_not_covered'}
    assert module._coverage(right-epsilon,right-epsilon,left,right)=={'relation':'point_inside','coverage':'point_covered'}
    assert module._coverage(right,right,left,right)=={'relation':'point_at_end','coverage':'point_not_covered'}


@pytest.mark.parametrize('values',[
    (Fraction(2),Fraction(1),Fraction(0),Fraction(3)),
    (Fraction(0),Fraction(1),Fraction(1),Fraction(1)),
    (Fraction(0),Fraction(1),Fraction(2),Fraction(1)),
    (True,Fraction(1),Fraction(0),Fraction(3)),
    (0.0,Fraction(1),Fraction(0),Fraction(3)),
])
def test_relation_rejects_reversed_empty_declared_or_inexact_inputs(values):
    module=feature()
    with pytest.raises(module.MaterialCostScopeHold):module._coverage(*values)


def test_UTC_fraction_keeps_original_microseconds_across_KST_midnight():
    module=feature();utc=timezone.utc;kst=timezone(timedelta(hours=9))
    boundary=datetime(2026,10,1,15,tzinfo=utc)
    local=datetime(2026,10,2,tzinfo=kst)
    epoch=datetime(1970,1,1,tzinfo=utc);delta=boundary-epoch
    expected=Fraction(delta.days*86400+delta.seconds)
    assert module._utc_fraction(boundary)==module._utc_fraction(local)==expected
    before=boundary-timedelta(microseconds=1);after=boundary+timedelta(microseconds=1)
    assert module._utc_fraction(before)==expected-Fraction(1,1_000_000)
    assert module._utc_fraction(after)==expected+Fraction(1,1_000_000)
    assert before.astimezone(kst).date()!=after.astimezone(kst).date()
    material_at=module._utc_fraction(after)+Fraction(1,3_000_000)
    assert material_at-expected==Fraction(4,3_000_000)


def test_UTC_fraction_handles_pre_epoch_microsecond_without_float_truncation():
    module=feature()
    assert module._utc_fraction(datetime(1969,12,31,23,59,59,999999,tzinfo=timezone.utc))==Fraction(-1,1_000_000)
    with pytest.raises(module.MaterialCostScopeHold):module._utc_fraction(datetime(2026,10,1))
