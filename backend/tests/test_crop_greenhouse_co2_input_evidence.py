"""Current raw inputs bind all CO2 rows without calculation during verification."""
from copy import deepcopy
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest
from app import crop_greenhouse_co2_input_evidence as model
from app import crop_greenhouse_co2_continuation as c
from app import crop_greenhouse_co2_time as clock
import test_crop_greenhouse_co2_continuation as producer
import test_crop_greenhouse_co2_time as times

profiles=producer.profiles
KEY=b'owned-co2-input-evidence-test-key-32!'
FRESH_PYTHONPATH=producer.FRESH_PYTHONPATH


def quantity_units(value,prefix=''):
    if type(value) is dict and set(value)=={'value','unit'}:return {prefix:value['unit']}
    if type(value) is list and value and all(type(v) is dict and set(v)=={'value','unit'} for v in value):
        assert len({v['unit'] for v in value})==1
        return {prefix:value[0]['unit']}
    pairs=value.items() if type(value) is dict else enumerate(value) if type(value) is list else []
    return {k:u for name,child in pairs for k,u in quantity_units(child,(prefix+'.' if prefix else '')+str(name)).items()}


def series_units(source):
    result={}
    for key,unit in quantity_units({k:v for k,v in source.items() if k not in ('version','provenance')}).items():
        path=re.sub(r'^(forcing_program|events)\.\d+\.',r'\1.*.',key)
        assert path not in result or result[path]==unit
        result[path]=unit
    return {**result,'step_seconds':'s','step_count':'1'}


def owned_provenance(source):
    from app.provenance import SourceRecord
    units=series_units(source);reviewer,evidence='owned-test-reviewer','owned-software-review-v1'
    data={'schema_version':'1','scope':{'provider':'self-authored-synthetic','product_id':'co2-contract-case',
        'product_version':'v1','source_url':'https://example.invalid/owned-co2-contract-inputs','station_or_grid_id':None},
        'revision_id':'synthetic-v1','request_details':[], 'observed_at':'2026-10-01T00:00:00Z',
        'published_at':'2026-10-02T00:00:00Z','available_at':'2026-10-02T00:00:00Z',
        'retrieved_at':'2026-10-03T00:00:00Z','valid_from':None,'valid_to':None,
        'variables':[{'name':k,'original_unit':u,'time_semantics':'instant','interval_start':None,'interval_end':None,
            'provider_qc_status':'not_supplied','provider_qc_value':None} for k,u in sorted(units.items())],
        'project_checks':[{'variable':k,'name':'initial_and_packet_schema_software_contract','version':model.QC_VERSION,
            'status':'passed','evidence_id':evidence,'reviewer':reviewer} for k in sorted(units)],
        'rights':[{'action':k,'status':'allowed','evidence_id':evidence,'reviewer':reviewer}
            for k in ('access','store','transform','display','redistribute')],
        'raw_sha256':sha256(model._canonical({k:source[k] for k in model.PROGRAM_FIELDS})).hexdigest(),'synthetic':True,
        'synthetic_author':'owned-test-author','synthetic_method':'self-authored synthetic software case',
        'source_reviewer':reviewer,'source_evidence_id':evidence}
    canonical=json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return SourceRecord.model_validate_json(model._canonical({**data,'record_id':sha256(canonical).hexdigest()})).model_dump(mode='json')


def packet(directory,profiles,case=None):
    case=producer.reference.BY_ID['weather-multiple'] if case is None else case
    directory.mkdir(mode=0o700)
    source={'version':model.SOURCE_VERSION,**{k:case[k] for k in model.PROGRAM_FIELDS if k!='time_origin'},
        'time_origin':times.origin()}
    source['provenance']=owned_provenance(source)
    raw=model._canonical(source);root=sha256(raw).hexdigest()
    original={'source.json':raw,'notice.txt':model._SOURCES['notice'].read_bytes(),
        **{name+'.json':profiles[name+'_profile'].raw_bytes for name in c.PROFILE_NAMES}}
    for name,data in original.items():
        target=directory/name;target.write_bytes(data);target.chmod(0o400)
    binding=clock.prepare_binding(producer.context(c,profiles,case),origin=times.origin())
    review={'evidence_id':'owned-software-review-v1','reviewer_id':'owned-test-reviewer','decision_id':'owned-decision-v1',
        'source_sha256':root,'status':'accepted_for_software_validation','scope':model.SCOPE}
    return directory,root,binding,review


def authority(review,**kw):
    return model.Co2InputEvidenceAuthority(integrity_key=kw.get('key',KEY),issuer_id=kw.get('issuer','owned-test'),
        key_id=kw.get('key_id','owned-key-v1'),review_resolver=kw.get('resolver',lambda _:deepcopy(review)))


def issue(server,p):return server.issue(p[0],p[1],binding=p[2],review_id=p[3]['evidence_id'])
def verify(server,p,raw,**kw):return server.verify(p[0],kw.get('source',p[1]),raw,
    expected_context_sha256=kw.get('context',p[2]._context.root_sha256),expected_binding_sha256=kw.get('binding',p[2].sha256))


@pytest.fixture
def prepared(tmp_path,profiles):return packet(tmp_path/'inputs',profiles)


@pytest.mark.parametrize('case',producer.CASES,ids=lambda x:x['case_id'])
def test_all_programs_issue_one_composition_and_verify_zero(profiles,tmp_path,monkeypatch,case):
    p=packet(tmp_path/'inputs',profiles,case);server=authority(p[3]);calls={}
    rhs=c.driver.stage.rhs;solar=rhs.solar_rhs
    for target,name in ((rhs,'evaluate_rhs'),(model.joint,'evaluate_rhs'),(solar,'evaluate_rhs'),
        (solar.vent,'calculate_ventilation'),(solar.par.radiation,'calculate_par'),(solar.nir,'calculate_nir'),
        (rhs.gas,'density_to_ppm'),(rhs.net,'calculate_exchange'),(rhs.air,'evaluate_rhs')):
        key=target.__name__;calls[key]=0;previous=getattr(target,name)
        def counted(*a,_key=key,_previous=previous,**kw):calls[_key]+=1;return _previous(*a,**kw)
        monkeypatch.setattr(target,name,counted)
    for target,name in ((c,'start'),(c,'advance_chunk'),(c,'restore_checkpoint'),(c.driver.stage,'integrate'),(c.driver.management,'apply_management')):
        monkeypatch.setattr(target,name,lambda *a,**kw:pytest.fail('issue advanced program'))
    before=len(os.listdir('/proc/self/fd'));raw=issue(server,p)
    assert len(calls)==9 and set(calls.values())=={1}
    times.forbid_numerics(monkeypatch)
    monkeypatch.setattr(c,'prepare_context',lambda **kw:pytest.fail('verify built context'))
    monkeypatch.setattr(clock,'prepare_binding',lambda *a,**kw:pytest.fail('verify built UTC'))
    receipt=verify(server,p,raw);source=json.loads((p[0]/'source.json').read_bytes())
    assert receipt.record==model._record(p[2],source['provenance'])
    assert receipt.record['program']==p[2]._context.program
    assert receipt.record['initial_calculation']==json.loads(p[2]._context._first)
    assert receipt.binding_metadata['provenance']==source['provenance']
    assert receipt.evidence_sha256==sha256(raw).hexdigest() and receipt.rights_or_gate_approval is False
    assert receipt.referenced_bytes==sum(f.stat().st_size for f in p[0].iterdir())
    assert {v['name']:v['original_unit'] for v in source['provenance']['variables']}==series_units(source)==model._variables(source)
    copied=receipt.record;copied['program']['scenario']['plant_state']['leaf']['value']=0
    assert copied!=receipt.record and len(os.listdir('/proc/self/fd'))==before
    assert KEY not in raw and json.loads(raw)['payload']['G0_G4']=='not_assessed'


def rewrite_owned_packet(p,value):
    metadata={k:v for k,v in value['provenance'].items() if k!='record_id'}
    raw_metadata=json.dumps(metadata,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    value['provenance']['record_id']=sha256(raw_metadata).hexdigest()
    raw=model._canonical(value);target=p[0]/'source.json'
    target.chmod(0o600);target.write_bytes(raw);target.chmod(0o400)
    root=sha256(raw).hexdigest()
    return p[0],root,p[2],{**p[3],'source_sha256':root}


@pytest.mark.parametrize('kind',('missing','extra','unit','bool','basis','origin','index','vector','bool-step','future-value','future-id','time'))
def test_future_rows_cannot_hide_behind_series_metadata_or_original_binding(prepared,kind):
    value=json.loads((prepared[0]/'source.json').read_bytes());row=value['forcing_program'][-1]
    if kind=='missing':row['co2']['forcing'].pop('external_co2_flux')
    elif kind=='extra':row['solar']['values']['unexpected']={'value':0,'unit':'1'}
    elif kind=='unit':row['ventilation']['forcing']['outdoor_air_temperature']['unit']='K'
    elif kind=='bool':row['co2']['parameters']['air_pressure']['value']=True
    elif kind=='basis':row['co2']['basis']='unknown'
    elif kind=='origin':row['co2']['origin']='measured'
    elif kind=='index':row['step_index']=True
    elif kind=='vector':value['events'][-1]['event']['values']['fruit_fraction'].pop()
    elif kind=='bool-step':value['step_seconds']=True
    elif kind=='future-value':row['co2']['forcing']['external_co2_flux']['value']+=1
    elif kind=='future-id':row['co2']['input_id']='other-source'
    else:value['time_origin']['start_at']='2026-10-02T00:00:00Z'
    value['provenance']['raw_sha256']=model._hash({k:value[k] for k in model.PROGRAM_FIELDS})
    changed=rewrite_owned_packet(prepared,value)
    with pytest.raises(model.Co2InputEvidenceHold):issue(authority(changed[3]),changed)


@pytest.mark.parametrize('action',('access','store','transform','display','redistribute'))
@pytest.mark.parametrize('status',('denied','unknown'))
def test_rehashed_missing_rights_cannot_be_accepted_for_owned_input(prepared,action,status):
    value=json.loads((prepared[0]/'source.json').read_bytes())
    next(v for v in value['provenance']['rights'] if v['action']==action)['status']=status
    changed=rewrite_owned_packet(prepared,value)
    with pytest.raises(model.Co2InputEvidenceHold):issue(authority(changed[3]),changed)



@pytest.mark.parametrize('kind',('provenance-missing','real','author','method','observed','published','available',
    'future-retrieval','publication-order','raw-hash','content-id','variable-missing','variable-extra','unit',
    'provider-QC','project-QC','project-version','project-missing','rights-missing','rights-reviewer',
    'source-reviewer','source-evidence','QC-evidence','station','request','unsafe-url'))
def test_provenance_qc_scope_and_time_holds_survive_rehashing(prepared,kind):
    v=json.loads((prepared[0]/'source.json').read_bytes());p=v['provenance']
    if kind=='real':p.update(synthetic=False,synthetic_author=None,synthetic_method=None)
    elif kind=='author':p['synthetic_author']=None
    elif kind=='method':p['synthetic_method']=None
    elif kind in ('observed','published','available'):p[kind+'_at']=None
    elif kind=='future-retrieval':p['retrieved_at']='9999-01-01T00:00:00Z'
    elif kind=='publication-order':p['published_at']='2026-10-03T00:00:00Z'
    elif kind=='raw-hash':p['raw_sha256']='0'*64
    elif kind=='variable-missing':p['variables'].pop()
    elif kind=='variable-extra':p['variables'].append({**p['variables'][0],'name':'untracked'})
    elif kind=='unit':p['variables'][0]['original_unit']='wrong'
    elif kind=='provider-QC':p['variables'][0].update(provider_qc_status='passed',provider_qc_value='not-actually-supplied')
    elif kind=='project-QC':p['project_checks'][0]['status']='unknown'
    elif kind=='project-version':p['project_checks'][0]['version']='unknown'
    elif kind=='project-missing':p['project_checks'].pop()
    elif kind=='rights-missing':p['rights'].pop()
    elif kind=='rights-reviewer':p['rights'][0]['reviewer']='other-reviewer'
    elif kind=='source-reviewer':p['source_reviewer']='other-reviewer'
    elif kind=='source-evidence':p['source_evidence_id']='other-evidence'
    elif kind=='QC-evidence':p['project_checks'][0]['evidence_id']='other-evidence'
    elif kind=='station':p['scope']['station_or_grid_id']='pretend-real-farm'
    elif kind=='request':p['request_details']=[{'name':'token','value':'private'}]
    elif kind=='unsafe-url':p['scope']['source_url']='https://example.invalid/?token=private'
    changed=rewrite_owned_packet(prepared,v)
    if kind in ('provenance-missing','content-id'):
        value=json.loads((changed[0]/'source.json').read_bytes())
        if kind=='provenance-missing':del value['provenance']
        else:value['provenance']['record_id']='0'*64
        target=changed[0]/'source.json';target.chmod(0o600);target.write_bytes(model._canonical(value));target.chmod(0o400)
        root=sha256(target.read_bytes()).hexdigest();changed=(changed[0],root,changed[2],{**changed[3],'source_sha256':root})
    with pytest.raises(model.Co2InputEvidenceHold):issue(authority(changed[3]),changed)



@pytest.mark.parametrize('field',('solar_rhs','PAR_joint','PAR','NIR','ventilation_joint','provenance'))
def test_solar_and_provenance_code_dependencies_are_current(prepared,tmp_path,monkeypatch,field):
    server=authority(prepared[3]);raw=issue(server,prepared);original=model._SOURCES[field]
    digest=sha256(original.read_bytes()).hexdigest();altered=tmp_path/'changed-dependency';altered.write_bytes(b'changed')
    monkeypatch.setitem(model._SOURCES,field,altered)
    with pytest.raises(model.Co2InputEvidenceHold):verify(server,prepared,raw)
    assert sha256(original.read_bytes()).hexdigest()==digest



def test_new_source_revision_needs_new_evidence_and_keeps_original_bytes(prepared,tmp_path):
    import shutil
    original=prepared;raw=issue(authority(original[3]),original);before=(original[0]/'source.json').read_bytes()
    directory=tmp_path/'inputs-v2';shutil.copytree(original[0],directory)
    value=json.loads(before);value['provenance']['revision_id']='synthetic-v2'
    changed=rewrite_owned_packet((directory,*original[1:]),value)
    with pytest.raises(model.Co2InputEvidenceHold):verify(authority(changed[3]),changed,raw)
    new=issue(authority(changed[3]),changed);receipt=verify(authority(changed[3]),changed,new)
    assert receipt.record['provenance']['revision_id']=='synthetic-v2' and changed[1]!=original[1]
    assert (original[0]/'source.json').read_bytes()==before



@pytest.mark.parametrize('kind',('source','growth','cohort','transport','exchange','notice','missing','extra','writable',
    'directory-mode','file-symlink','directory-symlink','ancestor-symlink','hardlink','FIFO','oversize'))
def test_current_source_storage_failures_reject_without_fd_leaks(prepared,tmp_path,kind):
    p=prepared;server=authority(p[3]);raw=issue(server,p);target=p[0]/'source.json';directory=p[0]
    if kind in ('source','growth','cohort','transport','exchange','notice'):
        target=p[0]/('notice.txt' if kind=='notice' else kind+'.json');target.chmod(0o600)
        target.write_bytes(target.read_bytes()+b' ');target.chmod(0o400)
    elif kind=='missing':target.unlink()
    elif kind=='extra':(directory/'extra.json').write_bytes(b'[]')
    elif kind=='writable':target.chmod(0o600)
    elif kind=='directory-mode':directory.chmod(0o755)
    elif kind=='file-symlink':
        outside=tmp_path/'outside';outside.write_bytes(target.read_bytes());target.unlink();target.symlink_to(outside)
    elif kind=='directory-symlink':directory.rename(tmp_path/'original');directory.symlink_to(tmp_path/'original',target_is_directory=True)
    elif kind=='ancestor-symlink':
        parent=tmp_path/'link';parent.symlink_to(tmp_path,target_is_directory=True);p=(parent/'inputs',*p[1:])
    elif kind=='hardlink':os.link(target,tmp_path/'other-link')
    elif kind=='FIFO':target.unlink();os.mkfifo(target,mode=0o400)
    else:target.chmod(0o600);target.write_bytes(b' '*(model.MAX_SOURCE_BYTES+1));target.chmod(0o400)
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(model.Co2InputEvidenceHold):verify(server,p,raw)
    assert len(os.listdir('/proc/self/fd'))==before



@pytest.mark.parametrize('kind',('mac','payload','version','scope','gate','QC','normalization','source-schema','timestamp',
    'seed','initial-rhs','profile','time','environment','extra','duplicate','nonfinite','noncanonical','oversize','context-sha','binding-sha','source-sha',
    'key','issuer','key-id'))
def test_mixed_or_forged_signed_metadata_never_verifies(prepared,kind):
    p=prepared;server=authority(p[3]);raw=issue(server,p);v=json.loads(raw);payload=v['payload'];resign=True;kw={}
    if kind=='mac':v['hmac_sha256']='0'*64;resign=False
    elif kind=='payload':payload['review']['decision_id']='changed';resign=False
    elif kind in ('version','scope','gate','QC','normalization','source-schema','timestamp'):
        key={'gate':'G0_G4','QC':'qc_version','normalization':'normalization_version','source-schema':'source_schema','timestamp':'validated_at'}.get(kind,kind)
        payload[key]='unknown'
    elif kind=='seed':payload['record']['program']['scenario']['plant_state']['leaf']['value']+=1
    elif kind=='initial-rhs':payload['record']['initial_calculation']['solar_rhs']['scenario']['plant_state']['leaf']['value']+=1
    elif kind=='profile':payload['record']['manifest']['identity']['profile_sha256']['growth']='0'*64
    elif kind=='time':payload['record']['binding']['origin']['start_at']='2026-10-02T00:00:00Z'
    elif kind=='environment':payload['record']['manifest']['identity']['python_version']='0.0.0'
    elif kind=='extra':payload['extra']='unknown'
    elif kind=='duplicate':raw=b'{"payload":{},"payload":{}}'
    elif kind=='nonfinite':raw=b'{"payload":NaN}'
    elif kind=='noncanonical':raw=b' '+raw
    elif kind=='oversize':raw=b' '*(model.MAX_EVIDENCE_BYTES+1)
    elif kind.endswith('-sha'):kw[{'context-sha':'context','binding-sha':'binding','source-sha':'source'}[kind]]='0'*64
    elif kind=='key':server=authority(p[3],key=b'other-owned-test-joint-key-32-bytes!')
    elif kind=='issuer':server=authority(p[3],issuer='other-issuer')
    else:server=authority(p[3],key_id='other-key')
    if kind not in ('duplicate','nonfinite','noncanonical','oversize'):
        if resign:v['hmac_sha256']=hmac.new(KEY,model.DOMAIN+model._canonical(payload),'sha256').hexdigest()
        raw=model._canonical(v)
    with pytest.raises(model.Co2InputEvidenceHold):verify(server,p,raw,**kw)



@pytest.mark.parametrize('field,value',(('status','revoked'),('scope','G0'),('source_sha256','0'*64),
    ('reviewer_id','different-reviewer'),('decision_id','different-decision'),('evidence_id','different-evidence')))
def test_current_review_changes_revoke_old_receipt(prepared,field,value):
    p=prepared;review=deepcopy(p[3]);server=authority(review);raw=issue(server,p);review[field]=value
    with pytest.raises(model.Co2InputEvidenceHold):verify(server,p,raw)



@pytest.mark.parametrize('phase',('issue','verify'))
@pytest.mark.parametrize('change',('review','bytes','resolver-error','missing-review'))
def test_review_and_bytes_rechecked_before_return(prepared,phase,change):
    p=prepared;raw=issue(authority(p[3]),p);calls=[]
    def resolver(_):
        calls.append(1);review=deepcopy(p[3])
        if len(calls)==2:
            if change=='review':review['status']='revoked'
            elif change=='bytes':
                target=p[0]/'source.json';target.chmod(0o600);target.write_bytes(target.read_bytes()+b' ');target.chmod(0o400)
            elif change=='resolver-error':raise RuntimeError('private detail must not appear')
            else:return None
        return review
    server=authority(p[3],resolver=resolver)
    with pytest.raises(model.Co2InputEvidenceHold,match='^co2 input validation evidence unavailable$'):
        issue(server,p) if phase=='issue' else verify(server,p,raw)



def test_current_runtime_environment_change_rejects_old_receipt(prepared,monkeypatch):
    server=authority(prepared[3]);raw=issue(server,prepared)
    monkeypatch.setattr(model.continuation.transport.platform,'python_version',lambda:'different-runtime')
    with pytest.raises(model.Co2InputEvidenceHold):verify(server,prepared,raw)



def test_invalid_initial_rhs_does_not_issue_or_leak_private_failure(prepared,monkeypatch):
    before=len(os.listdir('/proc/self/fd'))
    def fail(**kw):raise model.joint.JointClimateHold('private input detail')
    monkeypatch.setattr(model.joint,'evaluate_rhs',fail)
    with pytest.raises(model.Co2InputEvidenceHold,match='^co2 input validation evidence unavailable$'):
        issue(authority(prepared[3]),prepared)
    assert len(os.listdir('/proc/self/fd'))==before



@pytest.mark.parametrize('change',('duplicate','nonfinite','noncanonical','extra','bool-step','bad-time'))
def test_changed_source_digest_does_not_bypass_schema_or_qc(prepared,change):
    directory,_,binding,review=prepared;target=directory/'source.json';v=json.loads(target.read_bytes())
    if change=='duplicate':raw=b'{"version":"one","version":"two"}'
    elif change=='nonfinite':raw=b'{"step_seconds":NaN}'
    elif change=='noncanonical':raw=b' '+target.read_bytes()
    else:
        if change=='extra':v['extra']='unexpected'
        elif change=='bool-step':v['step_seconds']=True
        else:v['time_origin']['start_at']='2026-10-01T00:00:00'
        raw=model._canonical(v)
    target.chmod(0o600);target.write_bytes(raw);target.chmod(0o400)
    root=sha256(raw).hexdigest();review={**review,'source_sha256':root}
    with pytest.raises(model.Co2InputEvidenceHold):
        issue(authority(review),(directory,root,binding,review))



@pytest.mark.parametrize('dependency',('stage','base_integration','base_driver','ventilation','continuation_helpers','calendar_helpers'))
def test_new_dependencies_cannot_change_under_existing_evidence(prepared,dependency,tmp_path,monkeypatch):
    raw=issue(authority(prepared[3]),prepared);original=model._SOURCES[dependency];before=sha256(original.read_bytes()).hexdigest()
    changed=tmp_path/'changed.py';changed.write_bytes(b'owned changed dependency')
    monkeypatch.setitem(model._SOURCES,dependency,changed)
    with pytest.raises(model.Co2InputEvidenceHold):verify(authority(prepared[3]),prepared,raw)
    assert sha256(original.read_bytes()).hexdigest()==before


@pytest.mark.parametrize('field',('co2_rhs','gas','net','air_mass','solar_integration','management_primitives'))
def test_co2_dependencies_cannot_change(prepared,tmp_path,monkeypatch,field):
    server=authority(prepared[3]);raw=issue(server,prepared)
    changed=tmp_path/'changed.py';changed.write_bytes(b'owned changed dependency')
    monkeypatch.setitem(model._SOURCES,field,changed)
    with pytest.raises(model.Co2InputEvidenceHold):verify(server,prepared,raw)


@pytest.mark.parametrize('direction',('old-to-new','new-to-old'))
def test_original_solar_evidence_types_and_domains_remain_incompatible(prepared,tmp_path,profiles,direction):
    import test_crop_greenhouse_solar_input_evidence as old
    previous=old.packet(tmp_path/'old-inputs',profiles)
    if direction=='old-to-new':
        raw=old.issue(old.authority(previous[3]),previous)
        with pytest.raises(model.Co2InputEvidenceHold):verify(authority(prepared[3]),prepared,raw)
    else:
        raw=issue(authority(prepared[3]),prepared)
        with pytest.raises(old.model.SolarInputEvidenceHold):old.verify(old.authority(previous[3]),previous,raw)


@pytest.mark.parametrize('kind',('future-stamp','early-stamp','co2-mass','ledger','journal','source-program'))
def test_resigned_co2_metadata_does_not_replace_source_or_trusted_identity(prepared,kind):
    p=prepared;server=authority(p[3]);value=json.loads(issue(server,p));payload=value['payload'];kw={}
    if kind=='future-stamp':payload['validated_at']='9999-01-01T00:00:00.000000Z'
    elif kind=='early-stamp':payload['validated_at']='2026-10-01T00:00:00.000000Z'
    elif kind=='co2-mass':payload['record']['initial_calculation']['scenario']['climate_state']['air_co2_mass']['value']+=1
    elif kind=='ledger':payload['record']['manifest']['identity']['ledger_schema']='joint-solar-ventilation-ledgers-v1'
    elif kind=='journal':payload['record']['manifest']['identity']['journal_schema']='joint-co2-solar-event-journal-v1'
    else:
        # Rehash the altered program and both enclosing identities; source must still disagree.
        r=payload['record'];r['program']['forcing_program'][-1]['co2']['forcing']['external_co2_flux']['value']+=1
        r['manifest']['program_sha256']=model._hash(r['program'])
        r['context_sha256']=model._hash(r['manifest']);r['binding']['context_sha256']=r['context_sha256']
        r['binding_sha256']=model._hash(r['binding']);kw={'context':r['context_sha256'],'binding':r['binding_sha256']}
    value['hmac_sha256']=hmac.new(KEY,model.DOMAIN+model._canonical(payload),'sha256').hexdigest()
    with pytest.raises(model.Co2InputEvidenceHold):verify(server,p,model._canonical(value),**kw)


@pytest.mark.parametrize('status',('completed','hold'))
def test_verified_inputs_match_real_immutable_calculation_files(profiles,tmp_path,monkeypatch,status):
    from app import crop_greenhouse_co2_storage as storage
    case=deepcopy(producer.reference.BY_ID['weather-multiple'])
    if status=='hold':case['forcing_program'][1]['solar']['values']['outdoor_global_radiation']['value']=-1
    p=packet(tmp_path/'inputs',profiles,case);server=authority(p[3]);raw=issue(server,p)
    cp=c.start(p[2]._context);initial=cp;chunks=[]
    while True:
        chunk=c.advance_chunk(p[2]._context,cp,3);chunks.append(chunk);cp=chunk['checkpoint']
        if chunk['status']!='yielded':break
    assert chunks[-1]['status']==status
    times.forbid_numerics(monkeypatch)
    monkeypatch.setattr(c,'prepare_context',lambda **kw:pytest.fail('reader built context'))
    monkeypatch.setattr(clock,'prepare_binding',lambda *a,**kw:pytest.fail('reader built UTC'))
    receipt=verify(server,p,raw);directory=tmp_path/'calculation';directory.mkdir(mode=0o700)
    with storage.create_writer(directory,p[2],initial) as writer:
        for chunk in chunks:writer.append(chunk,expected_chunk_sha256=clock.source_chunk_sha256(p[2]._context,chunk))
        root=writer.finalize()
    with storage.open_artifact(directory,root) as reader:
        record=receipt.record
        assert reader.summary['status']==status
        assert reader._header['context_sha256']==record['context_sha256']
        assert reader._header['binding_sha256']==record['binding_sha256']
        assert reader._context['program']==record['program']
        assert reader._context['manifest']==record['manifest']
        assert reader._context['initial_rhs']==record['initial_calculation']
        assert reader.summary['last_confirmed']==chunks[-1]['last_confirmed']
        assert not receipt.rights_or_gate_approval


def test_fresh_verification_without_physical_context_time_setup_or_subprocess(prepared,tmp_path):
    p=prepared;receipt=tmp_path/'receipt';receipt.write_bytes(issue(authority(p[3]),p))
    request=tmp_path/'request';request.write_text(json.dumps({'directory':str(p[0]),'source':p[1],
        'context':p[2]._context.root_sha256,'binding':p[2].sha256,'review':p[3],'receipt':str(receipt)}))
    script='''import json,sys,subprocess
from pathlib import Path
from app import crop_greenhouse_co2_input_evidence as m
p=json.loads(Path(sys.argv[1]).read_bytes());calls=[];c=m.continuation;rhs=c.driver.stage.rhs;s=rhs.solar_rhs
def forbidden(*a,**kw):calls.append(1);raise AssertionError('unexpected physical setup')
targets=((c,'prepare_context'),(c,'start'),(c,'advance_chunk'),(c,'restore_checkpoint'),(m.clock,'prepare_binding'),(rhs,'evaluate_rhs'),(m.joint,'evaluate_rhs'),(c.driver.stage,'integrate'),(c.driver.management,'apply_management'),(s,'evaluate_rhs'),(s.vent,'calculate_ventilation'),(s.par.radiation,'calculate_par'),(s.nir,'calculate_nir'),(rhs.gas,'density_to_ppm'),(rhs.net,'calculate_exchange'),(rhs.air,'evaluate_rhs'),(subprocess,'Popen'))
for target,name in targets:setattr(target,name,forbidden)
server=m.Co2InputEvidenceAuthority(integrity_key=b'owned-co2-input-evidence-test-key-32!',issuer_id='owned-test',key_id='owned-key-v1',review_resolver=lambda _:p['review'])
result=server.verify(p['directory'],p['source'],Path(p['receipt']).read_bytes(),expected_context_sha256=p['context'],expected_binding_sha256=p['binding'])
print(json.dumps({'context':result.record['context_sha256'],'binding':result.record['binding_sha256'],'calls':len(calls),'gates':result.rights_or_gate_approval,'forbidden':len(targets)}))
'''
    child=subprocess.run([sys.executable,'-B','-c',script,str(request)],capture_output=True,timeout=20,check=True,
        env=dict(os.environ,PYTHONPATH=FRESH_PYTHONPATH))
    assert json.loads(child.stdout)=={'context':p[2]._context.root_sha256,'binding':p[2].sha256,'calls':0,'gates':False,'forbidden':17}


@pytest.mark.parametrize('distinct',(False,True),ids=('repeated','distinct-ids-and-values'))
def test_maximum_original_rows_outputs_and_events_fit_signed_caps(profiles,tmp_path,distinct):
    case=deepcopy(producer.reference.BY_ID['no-events'])
    case.update(step_seconds=.0625,step_count=512,output_steps=[*range(511),512],events=[])
    force=case['forcing_program'][0]
    case['forcing_program']=[{**deepcopy(force),'step_index':i} for i in case['output_steps']]
    event=deepcopy(producer.reference.BY_ID['multiple']['events'][0]['event'])
    event['values']['leaf']['value']=event['values']['stem_root']['value']=0
    for quantity in event['values']['fruit_fraction']:quantity['value']=0
    case['events']=[{'step_index':i,'event':{**deepcopy(event),'input_id':'max-owned-'+str(i)}} for i in range(128)]
    if distinct:
        for i,row in enumerate(case['forcing_program']):
            for kind in ('solar','ventilation','co2'):row[kind]['input_id']+='-frame-'+str(i)
            row['solar']['values']['outdoor_global_radiation']['value']+=i%20
            row['ventilation']['forcing']['outdoor_air_temperature']['value']+=(i%5)/10
            row['co2']['forcing']['external_co2_flux']['value']+=(i%7)/100
            row['co2']['forcing']['outdoor_co2_density']['value']+=i%7
    before=deepcopy(case);p=packet(tmp_path/'inputs',profiles,case);server=authority(p[3]);raw=issue(server,p)
    result=verify(server,p,raw);source=json.loads((p[0]/'source.json').read_bytes())
    assert source['forcing_program']==before['forcing_program'] and source['events']==before['events']
    assert result.record['program']==p[2]._context.program and case==before
    assert len(source['forcing_program'])==len(source['output_steps'])==512 and len(source['events'])==128
    assert len(source['provenance']['variables'])==48
    assert {v['name']:v['original_unit'] for v in source['provenance']['variables']}==series_units(source)
    assert (p[0]/'source.json').stat().st_size<=1048576 and len(raw)<=2097152
    print(json.dumps({'maximum_distinct':distinct,'source_bytes':(p[0]/'source.json').stat().st_size,
        'signed_evidence_bytes':len(raw),'variables':48,'forcing':512,'events':128,'outputs':512}))


@pytest.mark.parametrize('kind',('missing','extra','bool','basis','empty-id','unit'))
def test_future_schema_rejects_even_when_native_context_matches_all_raw_rows(prepared,profiles,kind):
    value=json.loads((prepared[0]/'source.json').read_bytes());row=value['forcing_program'][-1]
    if kind=='missing':row['co2']['forcing'].pop('external_co2_flux')
    elif kind=='extra':row['solar']['values']['extra']={'value':0,'unit':'1'}
    elif kind=='bool':row['co2']['parameters']['air_pressure']['value']=True
    elif kind=='basis':row['co2']['basis']='unknown'
    elif kind=='empty-id':row['ventilation']['input_id']=''
    else:row['ventilation']['forcing']['outdoor_air_temperature']['unit']='K'
    # Native context validates the initial RHS; this matching future program alone is insufficient QC.
    ctx=c.prepare_context(**{k:value[k] for k in model.PROGRAM_FIELDS if k!='time_origin'},**profiles)
    binding=clock.prepare_binding(ctx,origin=value['time_origin'])
    assert ctx.program['forcing_program'][-1]==row
    value['provenance']['raw_sha256']=model._hash({k:value[k] for k in model.PROGRAM_FIELDS})
    changed=rewrite_owned_packet((prepared[0],prepared[1],binding,prepared[3]),value)
    with pytest.raises(model.Co2InputEvidenceHold):issue(authority(changed[3]),changed)


@pytest.mark.parametrize('field',('revision_id','product_id','product_version'))
def test_missing_source_vintage_or_product_cannot_issue(prepared,field):
    value=json.loads((prepared[0]/'source.json').read_bytes())
    target=value['provenance'] if field=='revision_id' else value['provenance']['scope']
    target.pop(field);changed=rewrite_owned_packet(prepared,value)
    with pytest.raises(model.Co2InputEvidenceHold):issue(authority(changed[3]),changed)


@pytest.mark.parametrize('field',('integrity_key','issuer_id','key_id','review_resolver','module-path'))
def test_authority_and_runtime_module_identity_are_fixed(prepared,tmp_path,monkeypatch,field):
    server=authority(prepared[3]);raw=issue(server,prepared)
    if field=='module-path':
        changed=tmp_path/'co2.py';changed.write_bytes(Path(model.rhs.__file__).read_bytes())
        monkeypatch.setattr(model.rhs,'__file__',str(changed))
    else:setattr(server,field,lambda _:prepared[3] if field=='review_resolver' else 'changed')
    with pytest.raises(model.Co2InputEvidenceHold):verify(server,prepared,raw)
