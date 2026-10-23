"""Independent current SCRAM leaf job replay; no numerical imports or persistent writes."""
from copy import deepcopy
from hashlib import sha256
import builtins
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import psycopg
from app import crop_leaf_population_signed_artifact as model
from app.content_access import ContentAccess
from app import crop_leaf_population_execution as execution
from app import crop_leaf_population_execution_query as query
from app.job_store import JobStore
from leaf_population_farm_fresh import parent_services,LeafRights,snapshot
from morphology_farm_fresh import counts


def main():
    p=json.loads(Path(sys.argv[1]).read_bytes());parent,binding,parent_review=parent_services(p);leaf=p['leaf'];config=p['leaf_signed']
    review=deepcopy(leaf['review'])
    inputs=model.farms.evidence.LeafPopulationInputEvidenceAuthority(integrity_key=Path(leaf['key_file']).read_bytes(),
        issuer_id=leaf['issuer_id'],key_id=leaf['key_id'],review_resolver=lambda _:deepcopy(review),stem_input_authority=binding.input_authority)
    farm=model.farms.LeafPopulationFarmBinding(parent,inputs,input_rights=LeafRights())
    authority=model.LeafPopulationArtifactAuthority(farm,directory=Path(config['directory']),
        access=ContentAccess(os.getuid(),os.getgid()),integrity_key=Path(config['key_file']).read_bytes(),
        issuer_id=config['issuer_id'],key_id=config['key_id'])
    class Resolver:
        version=p['leaf_execution']['resolver_version']
        def __call__(self,tenant,reference):
            if tenant!=p['principal']['tenant_id']:raise PermissionError('foreign leaf input')
            return {k:Path(v).read_bytes() for k,v in leaf['packet_files'].items()}
    service=execution.LeafPopulationExecutionService(authority,input_resolver=Resolver())
    current=query.LeafPopulationExecutionQuery(service);job_id=p['leaf_execution']['job_id']
    forbidden={'app.'+n for n in ('crop_leaf_expansion','crop_leaf_area_change','crop_leaf_area','crop_rational_leaf_area',
        'crop_leaf_inventory','crop_declared_leaf_births','crop_leaf_population','crop_leaf_stem_binding',
        'crop_leaf_population_artifact_producer','crop_leaf_artifact_producer','crop_leaf_population_signed_producer',
        'crop_internode_elongation','crop_internode_length','crop_internode_length_change','crop_morphology_thermal_clock',
        'crop_rational_morphology_clock','crop_rational_internode_length','crop_rational_new_internodes',
        'crop_rational_shoot_inventory','crop_shoot_inventory','crop_shoot_timeline','crop_phytomer_emergence',
        'crop_rational_morphology_artifact_producer','crop_morphology_signed_producer','crop_morphology_execution_worker','crop_leaf_population_execution_worker')}
    assert not forbidden.intersection(sys.modules);imports=[]
    class NoGrowth:
        def find_spec(self,fullname,*args,**kwargs):
            if fullname in forbidden:imports.append(fullname);raise AssertionError('signed query imported growth')
    sys.meta_path.insert(0,NoGrowth())
    calls={k:0 for k in ('submit','publish','record_decision','_insert_publication','_event','_durable_content','_durable_artifact',
        'artifact.put','subprocess.run','subprocess.Popen','os.write_open','builtins.write_open','io.write_open')}
    def forbidden_call(name):
        def fail(*args,**kwargs):calls[name]+=1;raise AssertionError('signed query crossed readonly boundary')
        return fail
    for name in ('submit','publish','record_decision','_insert_publication','_event','_durable_content','_durable_artifact'):
        setattr(JobStore,name,forbidden_call(name))
    model.MorphologyBlobStore.put=forbidden_call('artifact.put')
    subprocess.run=forbidden_call('subprocess.run');subprocess.Popen=forbidden_call('subprocess.Popen')
    original_os_open=os.open
    def readonly_os_open(path,flags,*args,**kwargs):
        if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return forbidden_call('os.write_open')()
        return original_os_open(path,flags,*args,**kwargs)
    os.open=readonly_os_open
    def readonly_open(original,name):
        def open_file(file,mode='r',*args,**kwargs):
            if any(flag in mode for flag in 'wax+'):return forbidden_call(name)()
            return original(file,mode,*args,**kwargs)
        return open_file
    builtins.open=readonly_open(builtins.open,'builtins.write_open');io.open=readonly_open(io.open,'io.write_open')
    writes=[];execute=psycopg.Cursor.execute
    def readonly_execute(self,statement,*args,**kwargs):
        text=statement if type(statement) is str else statement.as_string(self.connection)
        if re.match(r'^\s*(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|COPY|CALL|DO)\b',text,re.I):
            writes.append(text.split()[0]);raise AssertionError('signed query persistent SQL write')
        return execute(self,statement,*args,**kwargs)
    psycopg.Cursor.execute=readonly_execute
    before=counts(binding);old_parent=snapshot(parent.service.authority.directory);old_leaf=snapshot(authority.directory)
    fd_before=len(os.listdir('/proc/self/fd'))
    with farm.jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    dto=current.read('tenant-1',job_id,view='replay')
    replay={**dto['result'],'frames':dto['replay']['frames'],'manifest':dto['replay']['manifest']['manifest']}
    assert replay['calculated_at']==config['calculated_at'] and replay['numerical_root_sha256']==config['root_sha256']
    assert replay['parent_result_sha256']==config['parent_result_sha256'] and len(replay['frames'])==12
    frame_hashes=[]
    for index,frame in enumerate(replay['frames']):
        raw=(Path(p['root'])/f'web/public/leaf-population-replay/frame-{index}.json').read_bytes()
        assert model.reader._canonical(frame)==raw;frame_hashes.append(sha256(raw).hexdigest())
    manifest=current.read('tenant-1',job_id,view='manifest')['manifest']
    assert manifest['manifest']==replay['manifest'] and manifest['calculated_at']==replay['calculated_at']
    for index in (0,11):
        value=current.read('tenant-1',job_id,view='frame',index=index)['frame']
        assert value['frame']==replay['frames'][index] and value['frame_sha256']==frame_hashes[index]
        assert value['calculated_at']==replay['calculated_at']
    status=current.read('tenant-1',job_id)
    assert status['result']==dto['result'] and status['job']['state']=='succeeded'
    for changed in (review,parent_review):
        changed['status']='revoked'
        try:current.read('tenant-1',job_id)
        except query.LeafPopulationExecutionQueryHold:pass
        else:raise AssertionError('revoked input retained signed result')
        changed['status']='accepted_for_software_validation'
    assert old_parent==snapshot(parent.service.authority.directory) and old_leaf==snapshot(authority.directory)
    assert before==counts(binding) and fd_before==len(os.listdir('/proc/self/fd'))
    assert not imports and not forbidden.intersection(sys.modules) and not any(calls.values()) and not writes
    assert not any(n in sys.modules for n in ('pytest','app.api','test_market_signed_hold_integration'))
    print(json.dumps({'actual_SCRAM':True,'job_id':job_id,'result_sha256':config['result_sha256'],'root_sha256':replay['numerical_root_sha256'],
        'calculated_at':replay['calculated_at'],'parent_result_sha256':replay['parent_result_sha256'],
        'original_frame_sha256':frame_hashes,'leaf_and_parent_review_revocation_rejected':True,
        'fresh_valid_modes':['status','manifest','frame','replay'],'fresh_valid_frame_indices':[0,11],
        'growth_import_attempts':imports,'calls':calls,'persistent_SQL_write_calls':writes,
        'FD_before_after':[fd_before,len(os.listdir('/proc/self/fd'))],'original_parent_files':len(old_parent),
        'original_leaf_files':len(old_leaf),'counts_before_after':[before,counts(binding)],'seed_pytest_HTTP_app_imports':0,
        'actual_farm_Runs':0,'G0_G4':'not_assessed'}))


if __name__=='__main__':main()
