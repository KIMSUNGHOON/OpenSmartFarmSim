"""Current original bytes and reviews must precede any downstream farm binding."""
from copy import deepcopy
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_greenhouse_solar_input_evidence as model
import test_crop_greenhouse_solar_time as reference

profiles=reference.profiles
KEY=b'owned-joint-input-evidence-test-key-32!'
FRESH_PYTHONPATH=os.pathsep.join((str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)))


def quantity_units(value,prefix=''):
    if type(value) is dict and set(value)=={'value','unit'}:return {prefix:value['unit']}
    if type(value) is list and value and all(type(v) is dict and set(v)=={'value','unit'} for v in value):
        assert len({v['unit'] for v in value})==1
        return {prefix:value[0]['unit']}
    pairs=value.items() if type(value) is dict else enumerate(value) if type(value) is list else []
    return {k:u for name,child in pairs for k,u in quantity_units(child,(prefix+'.' if prefix else '')+str(name)).items()}


def owned_provenance(source):
    from app.provenance import SourceRecord
    values={k:v for k,v in source.items() if k not in ('version','provenance')}
    units={**quantity_units(values),'step_seconds':'s','step_count':'1'}
    reviewer,evidence='owned-test-reviewer','owned-software-review-v1'
    data={'schema_version':'1','scope':{'provider':'self-authored-synthetic','product_id':'solar-contract-case',
        'product_version':'v1','source_url':'https://example.invalid/owned-solar-contract-inputs','station_or_grid_id':None},
        'revision_id':'synthetic-v1','request_details':[], 'observed_at':'2026-10-01T00:00:00Z',
        'published_at':'2026-10-02T00:00:00Z','available_at':'2026-10-02T00:00:00Z',
        'retrieved_at':'2026-10-03T00:00:00Z','valid_from':None,'valid_to':None,
        'variables':[{'name':k,'original_unit':u,'time_semantics':'instant','interval_start':None,'interval_end':None,
            'provider_qc_status':'not_supplied','provider_qc_value':None} for k,u in sorted(units.items())],
        'project_checks':[{'variable':k,'name':'initial_software_contract','version':model.QC_VERSION,
            'status':'passed','evidence_id':evidence,'reviewer':reviewer} for k in sorted(units)],
        'rights':[{'action':k,'status':'allowed','evidence_id':evidence,'reviewer':reviewer}
            for k in ('access','store','transform','display','redistribute')],
        'raw_sha256':sha256(model._canonical(values)).hexdigest(),'synthetic':True,
        'synthetic_author':'owned-test-author','synthetic_method':'self-authored constant input software case',
        'source_reviewer':reviewer,'source_evidence_id':evidence}
    # Independent content identity, using the shared SourceRecord canonical metadata contract.
    canonical=json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return SourceRecord.model_validate_json(model._canonical({**data,'record_id':sha256(canonical).hexdigest()})).model_dump(mode='json')


def packet(directory,profiles,case=None,origin=None):
    case=reference.reference.CASES[6] if case is None else case
    origin=reference.origin() if origin is None else origin
    directory.mkdir(mode=0o700)
    source={'version':model.SOURCE_VERSION,**{k:case[k] for k in ('scenario','solar','ventilation','events','output_steps','step_seconds','step_count')},
        'time_origin':origin}
    source['provenance']=owned_provenance(source)
    raw=model._canonical(source);root=sha256(raw).hexdigest()
    original={'source.json':raw,'notice.txt':model._SOURCES['notice'].read_bytes(),
        **{name+'.json':profiles[name+'_profile'].raw_bytes for name in model.continuation.PROFILE_NAMES}}
    for name,data in original.items():
        p=directory/name;p.write_bytes(data);p.chmod(0o400)
    binding=model.clock.prepare_binding(reference.reference.context(profiles,case),origin=origin)
    review={'evidence_id':'owned-software-review-v1','reviewer_id':'owned-test-reviewer','decision_id':'owned-decision-v1',
        'source_sha256':root,'status':'accepted_for_software_validation','scope':model.SCOPE}
    return directory,root,binding,review


def authority(review,**kw):
    return model.SolarInputEvidenceAuthority(integrity_key=kw.get('key',KEY),issuer_id=kw.get('issuer','owned-test'),
        key_id=kw.get('key_id','owned-key-v1'),review_resolver=kw.get('resolver',lambda _:deepcopy(review)))


def issue(server,p):return server.issue(p[0],p[1],binding=p[2],review_id=p[3]['evidence_id'])
def verify(server,p,raw,**kw):return server.verify(p[0],kw.get('source',p[1]),raw,
    expected_context_sha256=kw.get('context',p[2]._context.root_sha256),expected_binding_sha256=kw.get('binding',p[2].sha256))


@pytest.fixture
def prepared(tmp_path,profiles):return packet(tmp_path/'inputs',profiles)


@pytest.mark.parametrize('index',range(11))
def test_original_program_and_time_preserved_issue_one_composition_then_verify_zero(profiles,tmp_path,monkeypatch,index):
    p=packet(tmp_path/'inputs',profiles,reference.reference.CASES[index]);server=authority(p[3]);calls=[]
    original=model.joint.evaluate_rhs
    def rhs(**kw):calls.append('initial');return original(**kw)
    monkeypatch.setattr(model.joint,'evaluate_rhs',rhs)
    vent_calls=[];ventilation=model.continuation.driver.stage.solar_rhs.vent
    original_vent=ventilation.calculate_ventilation
    def boundary(**kw):vent_calls.append('initial');return original_vent(**kw)
    monkeypatch.setattr(ventilation,'calculate_ventilation',boundary)
    optical_calls={'solar':0,'PAR':0,'NIR':0}
    solar=model.continuation.driver.stage.solar_rhs
    for module,name,key in ((solar,'evaluate_rhs','solar'),(solar.par.radiation,'calculate_par','PAR'),(solar.nir,'calculate_nir','NIR')):
        optical_previous=getattr(module,name)
        def counted(_original=optical_previous,_key=key,**kw):
            optical_calls[_key]+=1;return _original(**kw)
        monkeypatch.setattr(module,name,counted)
    for target,name in ((model.continuation,'start'),(model.continuation,'advance_chunk'),(model.continuation,'restore_checkpoint'),
        (model.continuation.driver.stage,'integrate'),(model.continuation.driver.previous.management,'apply_management')):
        monkeypatch.setattr(target,name,lambda *a,**kw:pytest.fail('issue advanced time or management'))
    before=len(os.listdir('/proc/self/fd'));raw=issue(server,p);assert calls==['initial'] and vent_calls==['initial']
    assert optical_calls=={'solar':1,'PAR':1,'NIR':1}
    reference.forbid_numerics(monkeypatch)
    monkeypatch.setattr(model.continuation,'prepare_context',lambda **kw:pytest.fail('verification rebuilt context'))
    monkeypatch.setattr(model.clock,'prepare_binding',lambda *a,**kw:pytest.fail('verification rebuilt UTC binding'))
    receipt=verify(server,p,raw);assert receipt.record==model._record(p[2],json.loads((p[0]/'source.json').read_bytes())['provenance'])
    assert receipt.evidence_sha256==sha256(raw).hexdigest() and not receipt.rights_or_gate_approval
    assert receipt.referenced_bytes==sum(f.stat().st_size for f in p[0].iterdir())
    copied=receipt.record;copied['program']['scenario']['plant_state']['leaf']['value']=0
    assert copied!=receipt.record and len(os.listdir('/proc/self/fd'))==before
    assert KEY not in raw and json.loads(raw)['payload']['G0_G4']=='not_assessed'


def rewrite_owned_packet(packet,value):
    metadata={k:v for k,v in value['provenance'].items() if k!='record_id'}
    metadata_bytes=json.dumps(metadata,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    value['provenance']['record_id']=sha256(metadata_bytes).hexdigest()
    raw=model._canonical(value);target=packet[0]/'source.json'
    target.chmod(0o600);target.write_bytes(raw);target.chmod(0o400)
    root=sha256(raw).hexdigest();review={**packet[3],'source_sha256':root}
    return packet[0],root,packet[2],review


@pytest.mark.parametrize('action',('access','store','transform','display','redistribute'))
@pytest.mark.parametrize('status',('denied','unknown'))
def test_rehashed_missing_rights_cannot_be_accepted_for_owned_input(prepared,action,status):
    value=json.loads((prepared[0]/'source.json').read_bytes())
    next(v for v in value['provenance']['rights'] if v['action']==action)['status']=status
    changed=rewrite_owned_packet(prepared,value)
    with pytest.raises(model.SolarInputEvidenceHold):issue(authority(changed[3]),changed)


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
    with pytest.raises(model.SolarInputEvidenceHold):issue(authority(changed[3]),changed)


@pytest.mark.parametrize('field',('solar_rhs','PAR_joint','PAR','NIR','ventilation_joint','provenance'))
def test_solar_and_provenance_code_dependencies_are_current(prepared,tmp_path,monkeypatch,field):
    server=authority(prepared[3]);raw=issue(server,prepared);original=model._SOURCES[field]
    digest=sha256(original.read_bytes()).hexdigest();altered=tmp_path/'changed-dependency';altered.write_bytes(b'changed')
    monkeypatch.setitem(model._SOURCES,field,altered)
    with pytest.raises(model.SolarInputEvidenceHold):verify(server,prepared,raw)
    assert sha256(original.read_bytes()).hexdigest()==digest


@pytest.mark.parametrize('kind',('non-solar','NIR','PAR','spectrum','old-heat','solar-origin','solar-id'))
def test_consistent_rehashed_raw_provenance_does_not_replace_original_binding(prepared,kind):
    value=json.loads((prepared[0]/'source.json').read_bytes())
    if kind=='non-solar':value['scenario']['forcing']['canopy_non_solar_heat']['value']+=1
    elif kind=='NIR':value['solar']['values']['canopy_nir_reflectance']['value']/=2
    elif kind=='PAR':value['solar']['values']['cover_par_transmittance']['value']/=2
    elif kind=='spectrum':value['solar']['values']['solar_par_fraction']['value']=.2
    elif kind=='old-heat':value['scenario']['forcing']['canopy_external_heat']={'value':0,'unit':'W/m2_floor'}
    elif kind=='solar-origin':value['solar']['origin']='measured'
    else:value['solar']['input_id']='different-solar-input'
    value['provenance']=owned_provenance(value);changed=rewrite_owned_packet(prepared,value)
    with pytest.raises(model.SolarInputEvidenceHold):issue(authority(changed[3]),changed)


def test_all_original_quantity_blocks_have_independently_traversed_provenance(prepared):
    value=json.loads((prepared[0]/'source.json').read_bytes());variables=value['provenance']['variables']
    expected={**quantity_units({k:value[k] for k in model.PROGRAM_FIELDS}),'step_seconds':'s','step_count':'1'}
    assert {v['name']:v['original_unit'] for v in variables}==expected
    assert all(any(v['name'].startswith('scenario.'+k+'.') for v in variables)
        for k in ('removals','fruit_entry','relative_growth_rate'))
    receipt=verify(authority(prepared[3]),prepared,issue(authority(prepared[3]),prepared))
    assert receipt.record['provenance']==value['provenance'] and not receipt.rights_or_gate_approval


def test_new_source_revision_needs_new_evidence_and_keeps_original_bytes(prepared,tmp_path):
    import shutil
    original=prepared;raw=issue(authority(original[3]),original);before=(original[0]/'source.json').read_bytes()
    directory=tmp_path/'inputs-v2';shutil.copytree(original[0],directory)
    value=json.loads(before);value['provenance']['revision_id']='synthetic-v2'
    changed=rewrite_owned_packet((directory,*original[1:]),value)
    with pytest.raises(model.SolarInputEvidenceHold):verify(authority(changed[3]),changed,raw)
    new=issue(authority(changed[3]),changed);receipt=verify(authority(changed[3]),changed,new)
    assert receipt.record['provenance']['revision_id']=='synthetic-v2' and changed[1]!=original[1]
    assert (original[0]/'source.json').read_bytes()==before


@pytest.mark.parametrize('direction',('old-to-new','new-to-old'))
def test_original25_evidence_types_and_domains_remain_incompatible(prepared,tmp_path,profiles,direction):
    import test_crop_greenhouse_ventilation_input_evidence as old
    previous=old.packet(tmp_path/'old-inputs',profiles)
    if direction=='old-to-new':
        raw=old.issue(old.authority(previous[3]),previous)
        with pytest.raises(model.SolarInputEvidenceHold):verify(authority(prepared[3]),prepared,raw)
    else:
        raw=issue(authority(prepared[3]),prepared)
        with pytest.raises(old.model.VentilationInputEvidenceHold):old.verify(old.authority(previous[3]),previous,raw)


@pytest.mark.parametrize('status',('completed','hold'))
def test_verified_original_inputs_match_actual_immutable_calculation_file(profiles,tmp_path,monkeypatch,status):
    from app import crop_greenhouse_solar_storage as storage
    case=deepcopy(reference.reference.CASES[6 if status=='completed' else 0])
    if status=='hold':case['scenario']['forcing']['canopy_non_solar_heat']['value']=1e7
    p=packet(tmp_path/'inputs',profiles,case);server=authority(p[3]);raw=issue(server,p)
    c=model.continuation;cp=c.start(p[2]._context);initial=cp;chunks=[]
    while True:
        chunk=c.advance_chunk(p[2]._context,cp,3);chunks.append(chunk);cp=chunk['checkpoint']
        if chunk['status']!='yielded':break
    assert chunks[-1]['status']==status
    reference.forbid_numerics(monkeypatch);receipt=verify(server,p,raw)
    directory=tmp_path/'calculation';directory.mkdir(mode=0o700)
    with storage.create_writer(directory,p[2],initial) as writer:
        for chunk in chunks:writer.append(chunk,expected_chunk_sha256=storage.clock.source_chunk_sha256(p[2]._context,chunk))
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
    with pytest.raises(model.SolarInputEvidenceHold):verify(server,p,raw)
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
    elif kind=='initial-rhs':payload['record']['initial_calculation']['joint_rhs']['scenario']['plant_state']['leaf']['value']+=1
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
    with pytest.raises(model.SolarInputEvidenceHold):verify(server,p,raw,**kw)


@pytest.mark.parametrize('field,value',(('status','revoked'),('scope','G0'),('source_sha256','0'*64),
    ('reviewer_id','different-reviewer'),('decision_id','different-decision'),('evidence_id','different-evidence')))
def test_current_review_changes_revoke_old_receipt(prepared,field,value):
    p=prepared;review=deepcopy(p[3]);server=authority(review);raw=issue(server,p);review[field]=value
    with pytest.raises(model.SolarInputEvidenceHold):verify(server,p,raw)


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
    with pytest.raises(model.SolarInputEvidenceHold,match='^solar input validation evidence unavailable$'):
        issue(server,p) if phase=='issue' else verify(server,p,raw)


@pytest.mark.parametrize('change',('source-unit','source-origin','source-version','time','event','code-path','configuration','profiles'))
def test_invalid_issue_or_changed_authority_is_rejected(prepared,change,tmp_path,monkeypatch):
    p=prepared;server=authority(p[3]);raw=issue(server,p)
    if change in ('source-unit','source-origin','source-version','time','event'):
        target=p[0]/'source.json';v=json.loads(target.read_bytes())
        if change=='source-unit':v['scenario']['plant_state']['leaf']['unit']='wrong'
        elif change=='source-origin':v['scenario']['origin']='measured'
        elif change=='source-version':v['version']='unknown'
        elif change=='time':v['time_origin']['start_at']='2026-10-02T00:00:00Z'
        else:v['events'][0]['event']['values']['fruit_fraction'][0]['value']=2
        target.chmod(0o600);target.write_bytes(model._canonical(v));target.chmod(0o400)
        root=sha256(target.read_bytes()).hexdigest();review={**p[3],'source_sha256':root};p=(p[0],root,p[2],review);server=authority(review)
        with pytest.raises(model.SolarInputEvidenceHold):issue(server,p)
    else:
        if change=='configuration':server.key_id='changed'
        elif change=='code-path':
            changed=tmp_path/'changed.py';changed.write_text('changed');monkeypatch.setattr(model.clock,'__file__',str(changed))
        else:
            changed=tmp_path/'changed-profile';changed.write_bytes(b'changed');monkeypatch.setitem(model._SOURCES,'rhs',changed)
        with pytest.raises(model.SolarInputEvidenceHold):verify(server,p,raw)


def test_fresh_python_verifies_without_context_setup_or_numerics(prepared,tmp_path):
    p=prepared;raw=issue(authority(p[3]),p);receipt=tmp_path/'receipt';receipt.write_bytes(raw)
    pack=tmp_path/'request';pack.write_text(json.dumps({'directory':str(p[0]),'source':p[1],
        'context':p[2]._context.root_sha256,'binding':p[2].sha256,'review':p[3],'receipt':str(receipt)}))
    script='''import json,sys,subprocess
from pathlib import Path
import test_crop_greenhouse_solar_input_evidence as t
m=t.model;p=json.loads(Path(sys.argv[1]).read_bytes());calls=[]
def forbidden(*a,**kw):calls.append(1);raise AssertionError('unexpected physical setup')
for target,name in ((m.continuation,'prepare_context'),(m.continuation,'start'),(m.continuation,'restore_checkpoint'),(m.continuation,'advance_chunk'),(m.joint,'evaluate_rhs'),(m.continuation.driver.stage,'integrate'),(m.continuation.driver.previous.management,'apply_management'),(m.clock,'prepare_binding'),(m.continuation.driver.stage.solar_rhs.vent,'calculate_ventilation')):setattr(target,name,forbidden)
s=m.continuation.driver.stage.solar_rhs
s.evaluate_rhs=s.par.radiation.calculate_par=s.nir.calculate_nir=subprocess.Popen=forbidden
result=t.authority(p['review']).verify(p['directory'],p['source'],Path(p['receipt']).read_bytes(),expected_context_sha256=p['context'],expected_binding_sha256=p['binding'])
print(json.dumps({'context':result.record['context_sha256'],'binding':result.record['binding_sha256'],'calls':len(calls),'gates':result.rights_or_gate_approval}))
'''
    child=subprocess.run([sys.executable,'-B','-c',script,str(pack)],capture_output=True,timeout=20,check=True,
        env=dict(os.environ,PYTHONPATH=FRESH_PYTHONPATH))
    assert json.loads(child.stdout)=={'context':p[2]._context.root_sha256,'binding':p[2].sha256,'calls':0,'gates':False}


def test_current_runtime_environment_change_rejects_old_receipt(prepared,monkeypatch):
    server=authority(prepared[3]);raw=issue(server,prepared)
    monkeypatch.setattr(model.continuation.transport.platform,'python_version',lambda:'different-runtime')
    with pytest.raises(model.SolarInputEvidenceHold):verify(server,prepared,raw)


def test_invalid_initial_rhs_does_not_issue_or_leak_private_failure(prepared,monkeypatch):
    before=len(os.listdir('/proc/self/fd'))
    def fail(**kw):raise model.joint.JointClimateHold('private input detail')
    monkeypatch.setattr(model.joint,'evaluate_rhs',fail)
    with pytest.raises(model.SolarInputEvidenceHold,match='^solar input validation evidence unavailable$'):
        issue(authority(prepared[3]),prepared)
    assert len(os.listdir('/proc/self/fd'))==before


def test_maximum_schedule_receipt_and_closed_source_bounds(profiles,tmp_path):
    case=deepcopy(reference.reference.CASES[6]);event=case['events'][0]['event']
    case.update(step_seconds=.125,step_count=511,output_steps=list(range(512)),events=[])
    for index in range(128):
        changed={**deepcopy(event),'input_id':f'synthetic-evidence-max-{index}'}
        case['events'].append({'step_index':index,'event':changed})
    p=packet(tmp_path/'inputs',profiles,case);server=authority(p[3]);raw=issue(server,p)
    assert len(raw)<=model.MAX_EVIDENCE_BYTES and (p[0]/'source.json').stat().st_size<=model.MAX_SOURCE_BYTES
    result=verify(server,p,raw)
    assert len(result.record['program']['events'])==128 and len(result.record['program']['output_steps'])==512


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
    with pytest.raises(model.SolarInputEvidenceHold):
        issue(authority(review),(directory,root,binding,review))


@pytest.mark.parametrize('change',('weather-origin','weather-missing','weather-extra','weather-unit','weather-invalid-value',
    'weather-valid-value','weather-id','weather-extra-state','calendar-helper','initial-boundary','ledger-schema'))
def test_new_weather_and_initial_boundary_cannot_be_mixed_with_trusted_binding(prepared,change):
    directory,root,binding,review=prepared;server=authority(review);raw=issue(server,prepared)
    if change in ('calendar-helper','initial-boundary','ledger-schema'):
        value=json.loads(raw);record=value['payload']['record']
        if change=='calendar-helper':record['binding']['calendar_helpers_code_sha256']='0'*64
        elif change=='initial-boundary':record['initial_calculation']['outdoor']['input_sha256']='0'*64
        else:record['manifest']['identity']['ledger_schema']='joint-ledgers-v1'
        value['hmac_sha256']=hmac.new(KEY,model.DOMAIN+model._canonical(value['payload']),'sha256').hexdigest()
        with pytest.raises(model.SolarInputEvidenceHold):verify(server,prepared,model._canonical(value))
        return
    target=directory/'source.json';source=json.loads(target.read_bytes());weather=source['ventilation']
    if change=='weather-origin':weather['origin']='measured'
    elif change=='weather-missing':source.pop('ventilation')
    elif change=='weather-extra':weather['unexpected']=1
    elif change=='weather-unit':weather['forcing']['outdoor_air_temperature']['unit']='K'
    elif change=='weather-invalid-value':weather['forcing']['volume_exchange_per_floor_area']['value']=-1
    elif change=='weather-valid-value':weather['forcing']['outdoor_air_temperature']['value']+=1
    elif change=='weather-id':weather['input_id']='other-weather-source'
    else:weather['climate_state']=deepcopy(source['scenario']['climate_state'])
    target.chmod(0o600);target.write_bytes(model._canonical(source));target.chmod(0o400)
    root=sha256(target.read_bytes()).hexdigest();review={**review,'source_sha256':root}
    with pytest.raises(model.SolarInputEvidenceHold):issue(authority(review),(directory,root,binding,review))


@pytest.mark.parametrize('dependency',('stage','base_integration','base_driver','ventilation','continuation_helpers','calendar_helpers'))
def test_new_dependencies_cannot_change_under_existing_evidence(prepared,dependency,tmp_path,monkeypatch):
    raw=issue(authority(prepared[3]),prepared);original=model._SOURCES[dependency];before=sha256(original.read_bytes()).hexdigest()
    changed=tmp_path/'changed.py';changed.write_bytes(b'owned changed dependency')
    monkeypatch.setitem(model._SOURCES,dependency,changed)
    with pytest.raises(model.SolarInputEvidenceHold):verify(authority(prepared[3]),prepared,raw)
    assert sha256(original.read_bytes()).hexdigest()==before


def test_original_other_forcing_and_weather_remain_separate_in_signed_record(prepared):
    raw=issue(authority(prepared[3]),prepared);r=verify(authority(prepared[3]),prepared,raw).record
    source=json.loads((prepared[0]/'source.json').read_bytes());ctx=prepared[2]._context
    assert r['program']==ctx.program and r['initial_calculation']==json.loads(ctx._first)
    assert r['program']['ventilation']==source['ventilation']
    assert r['program']['scenario']['forcing']==source['scenario']['forcing']
    assert {'joint_rhs','PAR_joint','NIR','outdoor','solar','heat_composition'}<=set(r['initial_calculation'])
    assert r['manifest']['identity']['ledger_schema']=='joint-solar-ventilation-ledgers-v1'
    assert r['binding']['calendar_helpers_code_sha256']==model.clock.clock_helpers.CODE_SHA256


@pytest.mark.parametrize('direction',('old-to-new','new-to-old'))
def test_old_and_new_signed_evidence_domains_are_not_interchangeable(prepared,tmp_path,profiles,direction):
    import test_crop_climate_joint_input_evidence as legacy
    old=legacy.packet(tmp_path/'legacy-inputs',profiles)
    if direction=='old-to-new':
        raw=legacy.issue(legacy.authority(old[3]),old)
        with pytest.raises(model.SolarInputEvidenceHold):verify(authority(prepared[3]),prepared,raw)
    else:
        raw=issue(authority(prepared[3]),prepared)
        with pytest.raises(legacy.model.JointInputEvidenceHold):legacy.verify(legacy.authority(old[3]),old,raw)
