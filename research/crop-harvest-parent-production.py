"""Existing normal crop producer followed by durable private authority backup."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
VERSION='owned-crop-parent-production-v1'


def module(name):
    spec=importlib.util.spec_from_file_location('parent_production_'+name,ROOT/'research'/name)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


coordinator=module('crop-cycle-registered-full-path.py')
backup=module('crop-harvest-parent-backup.py')
runtime=coordinator.runtime;supervisor=coordinator.supervisor;publisher=coordinator.publisher
need=coordinator.need;canonical=coordinator.canonical


def selected_read(path,digest,context):
    """Bounded representative current query; whole-row comparison happens before publication."""
    value=backup.checked(path,digest);service=backup.current_query(path,digest,context)
    args=('tenant-1',value['original_record']['result_id'],value['farm'])
    before=len(os.listdir('/proc/self/fd'));metadata=service.read(*args);record=metadata['record']
    need(record['payload_sha256']==value['original_record']['payload_sha256'])
    packet=json.loads(record['payload_raw']);counts=packet['policies']['server_progress']['counts'];pages={}
    for label,kind,start,limit in (('samples-first','samples',0,min(64,counts['samples'])),
            ('samples-last','samples',max(0,counts['samples']-1),1),('events','events',0,8)):
        result=service.read(*args,kind=kind,start=start,limit=limit);page=result['page']
        need(result['record']==record and page['total']==counts[kind])
        if kind=='events':need(page['next']==page['total'])
        pages[label]={'start':start,'next':page['next'],'total':page['total'],'count':len(page['records']),
            'rows_sha256':sha256(b''.join(canonical(row)+b'\n' for row in page['records'])).hexdigest()}
    with service.store.jobs.connect() as conn:
        need(conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256')
    need(len(os.listdir('/proc/self/fd'))==before)
    return {'record':{'result_id':record['result_id'],'payload_sha256':record['payload_sha256'],
                'recorded_at':record['recorded_at'].isoformat()},'identity':metadata['identity'],
        'status':metadata['terminal']['status'],'counts':counts,'representative_pages':pages,
        'actual_host_SCRAM':True,'read_RHS_publication_proof_issue_calls':0}


def produce(server,raw,*,prepared,reference_file,reference_sha256,evidence,work,admin_dsn,binary):
    from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
    from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
    initial=coordinator.checked(*prepared)
    config,config_sha=runtime.export_runtime(server,raw,work/'private-runtime')
    pg_files=list(Path(os.environ['TMPDIR']).glob('ossf-login-pg-*/data/postmaster.pid'));need(len(pg_files)==1)
    pg={'process':supervisor.identity(int(pg_files[0].read_text().splitlines()[0])),'data_directory':str(pg_files[0].parent)}
    supervised=work/'supervised';wall=int(coordinator.remaining(initial))-1;need(wall>0)
    initialized=supervisor.initialize(supervised,config=config,config_sha256=config_sha,
        max_steps=10000,max_transitions=4096,wall_seconds=wall,owned_pg=pg)
    need(initialized['manifest']['deadline_ns']<=initial['deadline_ns'])
    declaration,declaration_sha=publisher.declare(work/'publication',supervision_directory=supervised,
        supervision_sha256=initialized['supervision_sha256'])
    _,decl=supervisor.read_json(declaration)
    execution={'version':coordinator.VERSION,'preparation_file':str(prepared[0]),'preparation_sha256':prepared[1],
        'preparation_deadline_ns':initial['deadline_ns'],'config_sha256':config_sha,
        'publication_file':str(declaration),'publication_sha256':declaration_sha,
        'reference_file':str(reference_file),'reference_sha256':reference_sha256,'plan':decl['plan'],
        'farm':json.loads(raw)['farm'],'input_root_sha256':json.loads(raw)['input']['root_sha256']}
    execution_path=evidence/'execution.json';execution_sha=supervisor.immutable(execution_path,execution)
    coordinator.execution(execution_path,execution_sha)
    computed=supervisor.run(supervised,expected_sha256=initialized['supervision_sha256'],max_chunks=16384)
    need(computed['outcome']=='recorded' and computed['worker_returncode']==0
         and computed['result']['progress']['status']=='completed')
    comparison_path=evidence/'comparison.result.json'
    compared=coordinator.child([sys.executable,str(ROOT/'research/crop-cycle-registered-full-path.py'),
        '--compare','--execution',str(execution_path),'--sha256',execution_sha,'--output',str(comparison_path)],
        name='comparison',prepared=prepared,evidence=evidence)
    comparison=json.loads(runtime.private_bytes(comparison_path));need(comparison['execution_sha256']==execution_sha)
    if initial['scope']=='owned_full166':
        previous=json.loads((ROOT/'research/artifacts/crop-cycle-calculation-full166-same-db-completed-reference-20261008.json').read_bytes())
        need(comparison['comparison']['candidate_row_sha256']==previous['observation']['comparison_counts_hashes']['candidate_row_sha256'])
    output=declaration.parent/'publication.result.json'
    published=coordinator.child([sys.executable,str(ROOT/'research/crop-cycle-registered-publication.py'),
        '--declaration',str(declaration),'--sha256',declaration_sha,'--output',str(output)],
        name='publication',prepared=prepared,evidence=evidence)
    _,_,server,raw,db_key=publisher.load_declaration(declaration,declaration_sha)
    farm=json.loads(raw)['farm'];publication=json.loads(runtime.private_bytes(output))
    record=CalculationCycleCropResultStore(server,integrity_key=db_key).get('tenant-1',publication['result_id'],farm)
    result_key=os.urandom(32);document=json.loads(runtime.private_bytes(config))
    issuer=CalculationResultEvidenceAuthority(server.binding.input_authority,integrity_key=result_key,
        issuer_id='owned-parent-backup-result',key_id='result-v1')
    progress=computed['result']['progress'];artifact=server.directory/runtime.custody._intent_id('tenant-1',json.loads(raw))/'artifact'
    proof=issuer.issue(artifact,progress['artifact_sha256'],Path(document['input']['directory']),
        document['input']['root_sha256'],runtime.private_bytes(document['input']['evidence_file']))
    path,digest=backup.backup(evidence/'backup',admin_dsn=admin_dsn,owned_data=pg['data_directory'],binary=binary,
        config=config,config_sha256=config_sha,db_key=db_key,result_key=result_key,result_proof=proof,record=record,farm=farm)
    with backup.readonly_guard():selected=selected_read(path,digest,{'config':config,'config_sha256':config_sha})
    coordinator.checked(*prepared)
    return {'version':VERSION,'scope':initial['scope'],'backup':str(path),'backup_sha256':digest,
        'config':str(config),'config_sha256':config_sha,'current_query':selected,
        'compute_progress':progress,'compute_actual_exit':computed['worker_returncode'],
        'compute_actual_RHS_calls':computed['result']['actual_RHS_calls'],
        'comparison_command':compared,'publication_command':published,
        'comparison':{k:v for k,v in comparison.items() if k!='comparison'},
        'comparison_counts_hashes':{k:v for k,v in comparison['comparison'].items() if k!='preview'},
        'original_preparation_deadline_ns':initial['deadline_ns'],'actual_crop_Runs':0,'G0_G4':'not_assessed'}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup',type=Path,required=True);parser.add_argument('--sha256',required=True)
    parser.add_argument('--restore-directory',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with backup.readonly_guard():
        with backup.restored(args.backup,args.sha256,args.restore_directory) as context:
            value=selected_read(args.backup,args.sha256,context)
    need(not (args.restore_directory/'data/postmaster.pid').exists())
    backup.write(args.output,canonical(value))
