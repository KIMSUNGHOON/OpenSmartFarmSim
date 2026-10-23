"""Fresh current SCRAM leaf binding; no seeds, worker, growth or persistent writes."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys

import psycopg
from app import crop_leaf_appearance_farm_binding as model
from app import crop_morphology_signed_artifact as signed
from app import crop_morphology_execution as execution
from app.content_access import ContentAccess
from morphology_farm_fresh import (RuntimeLoginPolicy,JobStore,MarketSourceStore,ThermalRunStore,MarketHoldStore,
    _MarketSources,MarketCandidateStore,ResearchRegistry,OwnedResearchService,OwnedFixtureRegistry,
    FarmReplayScenarioService,ThermalScenarioStore,FarmAuthoringService,context_verifier,Rights,counts)


class LeafRights:
    policy_version='owned-leaf-appearance-input-rights-test-v1'
    def __call__(self,tenant,declaration,source,use):
        return tenant=='tenant-1' and declaration['schema_version']==model.RIGHTS_VERSION \
            and declaration['input_source_sha256']==source and use in ('research_calculation','research_display')


def parent_services(p):
    policy=RuntimeLoginPolicy(**p['policy']);identity=(policy,'authority');principal=p['principal']
    principal['scopes']=set(principal['scopes']);provider=lambda:principal
    kw={'runtime_identity':identity,'principal_provider':provider};dsn=p['dsn'];schema=policy.schema
    jobs=JobStore(dsn,schema,Path(p['artifacts']),audit_runtime_grants=True,**kw)
    sources=MarketSourceStore(dsn,schema,**kw)
    runs=ThermalRunStore(dsn,schema,gate_key=b'synthetic-gate-key-32-bytes-long!',release_verifier=lambda *_:None,
        context_verifier=context_verifier,**kw)
    holds=MarketHoldStore(dsn,schema,context_store=runs,scope_resolver=lambda *_:dict(p['scope']),
        signing_key=b'synthetic-market-hold-key-32bytes!!',**kw)
    candidates=MarketCandidateStore(dsn,schema,_MarketSources(sources,holds,principal_provider=provider),**kw)
    registry=ResearchRegistry(p['registry_raw'].encode(),p['registry_sha256'])
    owned=OwnedResearchService(jobs,runs,registry,OwnedFixtureRegistry(Path(p['root'])),{next(iter(registry._scopes)):'context-1'})
    replay=FarmReplayScenarioService(jobs,ThermalScenarioStore(runs,holds),candidates,registry,owned_research=owned)
    review=deepcopy(p['review'])
    authority=signed.farms.evidence.MorphologyInputEvidenceAuthority(integrity_key=Path(p['input_key_file']).read_bytes(),
        issuer_id=p['issuer_id'],key_id=p['key_id'],review_resolver=lambda _:deepcopy(review))
    binding=signed.farms.MorphologyFarmBinding(FarmAuthoringService(replay),authority,input_rights=Rights())
    config=p['signed']
    parent=signed.MorphologyArtifactAuthority(binding,directory=Path(config['directory']),access=ContentAccess(os.getuid(),os.getgid()),
        integrity_key=Path(config['key_file']).read_bytes(),issuer_id=config['issuer_id'],key_id=config['key_id'])
    class Resolver:
        version=p['execution']['resolver_version']
        def __call__(self,tenant,reference):
            if tenant!=principal['tenant_id']:raise PermissionError('foreign input')
            return {k:Path(v).read_bytes() for k,v in p['packet_files'].items()}
    service=execution.MorphologyExecutionService(parent,input_resolver=Resolver())
    return model.parent_reads.MorphologyExecutionQuery(service),binding,review


def snapshot(directory):
    result={}
    for f in directory.iterdir():
        s=f.stat();result[f.name]=[s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,
            s.st_mtime_ns,s.st_ctime_ns,sha256(f.read_bytes()).hexdigest()]
    return result


def main():
    p=json.loads(Path(sys.argv[1]).read_bytes());parent,binding,parent_review=parent_services(p);leaf=p['leaf']
    review=deepcopy(leaf['review']);authority=model.evidence.LeafAppearanceInputEvidenceAuthority(
        integrity_key=Path(leaf['key_file']).read_bytes(),issuer_id=leaf['issuer_id'],key_id=leaf['key_id'],
        review_resolver=lambda _:deepcopy(review),stem_input_authority=binding.input_authority)
    service=model.LeafAppearanceFarmBinding(parent,authority,input_rights=LeafRights())
    packet={k:Path(v).read_bytes() for k,v in leaf['packet_files'].items()};body=model.farms.documents._canonical(leaf['body'])
    expected=Path(leaf['binding_file']).read_bytes()
    forbidden={'app.'+n for n in ('crop_leaf_expansion','crop_leaf_area_change','crop_leaf_area','crop_rational_leaf_area',
        'crop_leaf_inventory','crop_declared_leaf_births','crop_leaf_population','crop_leaf_stem_binding',
        'crop_leaf_population_artifact_producer','crop_leaf_artifact_producer','crop_internode_elongation',
        'crop_internode_length','crop_internode_length_change','crop_morphology_thermal_clock',
        'crop_rational_morphology_clock','crop_rational_internode_length','crop_rational_new_internodes',
        'crop_rational_shoot_inventory','crop_shoot_inventory','crop_shoot_timeline','crop_phytomer_emergence',
        'crop_rational_morphology_artifact_producer','crop_morphology_signed_producer','crop_morphology_execution_worker',
        'crop_phytomer_kind','crop_stored_shoot_leaf_birth_inputs','crop_leaf_appearance_preparation','crop_leaf_appearance_artifact_producer')}
    assert not forbidden.intersection(sys.modules);imports=[]
    class NoGrowth:
        def find_spec(self,fullname,*args,**kwargs):
            if fullname in forbidden:imports.append(fullname);raise AssertionError('fresh imported growth')
    sys.meta_path.insert(0,NoGrowth());calls={k:0 for k in ('submit','publish','record_decision','_insert_publication','_event','_durable_content')}
    for name in calls:
        def blocked(*args,_name=name,**kwargs):calls[_name]+=1;raise AssertionError('fresh wrote a job')
        setattr(JobStore,name,blocked)
    sql_writes=[];execute=psycopg.Cursor.execute
    def readonly_execute(self,statement,*args,**kwargs):
        raw=statement if type(statement) is str else statement.as_string(self.connection)
        if re.match(r'^\s*(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|COPY|CALL|DO)\b',raw,re.I):
            sql_writes.append(raw.split()[0]);raise AssertionError('fresh persistent SQL write')
        return execute(self,statement,*args,**kwargs)
    psycopg.Cursor.execute=readonly_execute
    before=counts(binding);originals=snapshot(parent.service.authority.directory);fd_before=len(os.listdir('/proc/self/fd'))
    with service.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    actual=service.current('tenant-1',body,expected,**packet);assert actual==expected
    for changed in (review,parent_review):
        changed['status']='revoked'
        try:service.current('tenant-1',body,expected,**packet)
        except model.LeafAppearanceFarmBindingHold:pass
        else:raise AssertionError('fresh revoked source accepted')
        changed['status']='accepted_for_software_validation'
    assert before==counts(binding) and originals==snapshot(parent.service.authority.directory)
    assert fd_before==len(os.listdir('/proc/self/fd')) and not any(calls.values()) and not sql_writes and not imports
    assert not forbidden.intersection(sys.modules) and not any(n in sys.modules for n in ('pytest','app.api','test_market_signed_hold_integration'))
    value=json.loads(actual)
    print(json.dumps({'actual_SCRAM':True,'binding_sha256':sha256(actual).hexdigest(),'original_binding_bytes':True,
        'parent_job_id':value['parent']['job_id'],'parent_result_sha256':value['parent']['result_sha256'],
        'policy_sha256':value['input']['policy_sha256'],'variable_count':value['input']['variable_count'],
        'parent_root_sha256':value['parent']['numerical_root_sha256'],'parent_calculated_at':value['parent']['calculated_at'],
        'leaf_and_parent_revocation_rejected':True,'growth_import_attempts':imports,'job_write_calls':calls,
        'persistent_SQL_write_calls':sql_writes,'FD_before_after':[fd_before,len(os.listdir('/proc/self/fd'))],
        'original_signed_files_preserved':len(originals),'seed_pytest_HTTP_app_imports':0,'counts_before_after':[before,counts(binding)],
        'actual_farm_Runs':0,'G0_G4':'not_assessed'}))


if __name__=='__main__':main()
