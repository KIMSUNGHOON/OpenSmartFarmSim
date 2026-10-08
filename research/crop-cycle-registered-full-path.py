"""One owned DB lifecycle with a preparation deadline and bounded reference comparison."""
from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
VERSION='owned-registered-full-path-preparation-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def module(name):
    spec=importlib.util.spec_from_file_location('owned_full_path_'+name,ROOT/'research'/('crop-cycle-registered-'+name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


publisher=module('publication');runtime=publisher.runtime;supervisor=publisher.supervisor
canonical=runtime.engine.inputs._canonical


def need(condition,message='owned full path unavailable'):
    if not condition:raise ValueError(message)


def sources():
    reference=ROOT/'research/artifacts/crop-cycle-calculation-registered-replay-resource-reference-20261008.json'
    pins=json.loads(reference.read_bytes())['source_sha256']
    need(all(sha256((ROOT/name).read_bytes()).hexdigest()==value for name,value in pins.items()),'accepted resource sources changed')
    paths=[Path(__file__),reference,ROOT/'contracts/crop-cycle-calculation-full166-same-db-preparation-v1.md',
           ROOT/'backend/tests/test_crop_cycle_registered_full_path.py',ROOT/'backend/tests/crop_cycle_registered_full_path_smoke.py']
    need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256)
    return {**pins,**{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in paths}}


def remaining(value):return supervisor.remaining(value)


def begin(directory,*,wall_seconds,scope):
    started=time.time_ns();monotonic=time.monotonic_ns()
    need(scope in ('owned_small','owned_full166') and type(wall_seconds) is int
         and 1<=wall_seconds<=(600 if scope=='owned_small' else 32400),'bounded preparation budget required')
    directory=Path(directory).absolute();directory.mkdir(mode=0o700);supervisor.directory(directory)
    disks={'durable_free_bytes':shutil.disk_usage(directory).free,'temporary_free_bytes':shutil.disk_usage(os.environ.get('TMPDIR','/tmp')).free}
    need(min(disks.values())>=2*1024**3,'two GiB in both storage spaces required')
    memory=next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
    value={'version':VERSION,'scope':scope,'gates':'not_assessed','started_ns':started,'started_monotonic_ns':monotonic,
        'wall_ns':wall_seconds*10**9,'deadline_ns':started+wall_seconds*10**9,
        'started_at_utc':datetime.fromtimestamp(started/1e9,timezone.utc).isoformat(),
        'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'source_sha256':sources(),
        'primary_RSS_limit_bytes':512*1024**2,'pipeline_RSS_limit_bytes':1024**3,'preflight':{**disks,'MemAvailable_bytes':memory}}
    path=directory/'preparation.json';digest=supervisor.immutable(path,value)
    checked(path,digest)
    return path,digest


def checked(path,digest):
    raw,value=supervisor.read_json(Path(path))
    need(sha256(raw).hexdigest()==digest and value['version']==VERSION and value['gates']=='not_assessed')
    need(value['source_sha256']==sources(),'original preparation sources required')
    need(remaining(value)>0,'original preparation deadline expired')
    return value


def shift(at,days):
    return (datetime.fromisoformat(at.replace('Z','+00:00'))+timedelta(days=days)).isoformat().replace('+00:00','Z')


def compare_checkpoint(original,candidate,*,offset_days):
    original=deepcopy(original)
    original['at']=shift(original['at'],offset_days)
    original['clock']['segment_start']=shift(original['clock']['segment_start'],offset_days)
    excluded={'version','root_sha256','checkpoint_sha256','parent_sha256','output_prefix_sha256','event_prefix_sha256'}
    need({k:v for k,v in original.items() if k not in excluded}=={k:v for k,v in candidate.items() if k not in excluded},
         'original checkpoint semantics mismatch')


def compare_rows(original,candidate,*,counts,offset_days,check):
    need(type(offset_days) is int and offset_days in (0,273))
    need(set(counts)=={'samples','events'} and all(type(v) is int and v>=0 for v in counts.values()))
    preview={};hashes={};candidate_hashes={};pages={}
    for kind,limit in (('samples',64),('events',8)):
        kept=[];left_hash=sha256();right_hash=sha256();offset=0;number=0
        while offset<counts[kind] or number==0:
            check();size=min(limit,counts[kind]-offset) or 1
            left=original.page(kind,offset,size);right=candidate.page(kind,offset,size)
            for page in (left,right):
                need(page['kind']==kind and page['total']==counts[kind] and page['start']==offset
                     and page['next']==offset+len(page['records']) and len(page['records'])<=size
                     and (page['next']>offset or counts[kind]==0),'original complete page sequence required')
            need(left['next']==right['next'],'original matching page boundaries required')
            for before,after in zip(left['records'],right['records'],strict=True):
                left_hash.update(canonical(before)+b'\n');expected=deepcopy(before);expected['at']=shift(expected['at'],offset_days)
                need(canonical(expected)==canonical(after),'original row mismatch')
                right_hash.update(canonical(after)+b'\n')
                if len(kept)<limit:kept.append(after)
            offset=right['next'];number+=1
        need(offset==counts[kind]);preview[kind]=kept;hashes[kind]=left_hash.hexdigest();candidate_hashes[kind]=right_hash.hexdigest();pages[kind]=number
    original.recheck();candidate.recheck();check()
    return {'counts':counts,'pages':pages,'preview':preview,'original_row_sha256':hashes,
            'candidate_row_sha256':candidate_hashes,'offset_days':offset_days,'all_rows_compared':True}


def execution(path,digest):
    raw,value=supervisor.read_json(Path(path));need(sha256(raw).hexdigest()==digest and value['version']==VERSION)
    checked(value['preparation_file'],value['preparation_sha256'])
    need(supervisor.digest(Path(value['reference_file']))==value['reference_sha256'])
    declaration,manifest,key=publisher.validated(value['publication_file'],value['publication_sha256'])
    need(manifest['deadline_ns']<=value['preparation_deadline_ns'])
    need(declaration['plan']==value['plan'] and manifest['config_sha256']==value['config_sha256'])
    return value


def child(argv,*,name,prepared,evidence):
    path,digest=prepared;value=checked(path,digest);log=evidence/(name+'.log')
    started=time.monotonic();process=None;identity=None;reason=None;signals=[]
    try:
        with log.open('xb') as stream:
            os.fchmod(stream.fileno(),0o600)
            try:
                process=subprocess.Popen(['/usr/bin/nice','-n','19',*argv],cwd=ROOT/'backend',stdout=stream,
                    stderr=subprocess.STDOUT,start_new_session=True)
                identity=supervisor.identity(process.pid)
                while process.poll() is None:
                    if remaining(value)<=0:reason='preparation_deadline'
                    elif os.fstat(stream.fileno()).st_size>1024**2:reason='log_limit'
                    if reason:signals.extend(supervisor.stop(process,identity));break
                    time.sleep(.1)
                process.wait()
            finally:
                if process is not None and process.poll() is None:signals.extend(supervisor.stop(process,identity))
                stream.flush();os.fsync(stream.fileno())
    finally:
        if log.exists():log.chmod(0o400)
        receipt={'argv':['/usr/bin/nice','-n','19',*argv],'worker':identity,'actual_exit_code':process.returncode if process else None,
            'preparation_sha256':digest,'preparation_deadline_ns':value['deadline_ns'],'reason':reason,'signals':signals,
            'wall_seconds':time.monotonic()-started,'log_sha256':supervisor.digest(log) if log.exists() else None}
        supervisor.immutable(evidence/(name+'.command.json'),receipt)
    need(receipt['actual_exit_code']==0 and reason is None,'owned child failed or expired')
    checked(path,digest)
    return receipt


@contextmanager
def reference_reader(value):
    if value['kind']=='owned_small_legacy_reference':
        need(value['offset_days']==0 and value['counts']['samples']<=64 and value['counts']['events']<=8)
        class Small:
            def page(self,kind,start,limit):
                rows=value['rows'][kind][start:start+limit]
                return {'kind':kind,'start':start,'next':start+len(rows),'total':len(value['rows'][kind]),'records':rows}
            def recheck(self):pass
        yield Small(),value['checkpoint']
        return
    need(value['kind']=='owned_original166' and value['offset_days']==273
         and value['counts']=={'samples':47809,'events':5} and value['steps']==1816704)
    need(value['input_root_sha256']=='ab24eda4d763d7fe3faff1ae3c7c2f84fbec030af71a494bf284fef1f2cdcd98'
         and value['artifact_sha256']=='15b609576243c73b67a4947b5affc2db14047787e4851064b3aabeafd3d0286d')
    from app.crop_cycle_result_read_context import open_result_read_context
    from test_crop_cycle_result_evidence import authority
    proofs=[]
    for name in ('input','result'):
        path=Path(value[name+'_evidence_file']);need(supervisor.digest(path)==value[name+'_evidence_sha256'])
        fd=runtime.custody.job_store._open_directory_nofollow(path.parent)
        try:proofs.append(runtime.custody._read(fd,path.name,8*1024**2))
        finally:os.close(fd)
    directory=Path(value['artifact_directory']);root_raw=(directory/(value['artifact_sha256']+'.json')).read_bytes()
    need(sha256(root_raw).hexdigest()==value['artifact_sha256']);root=json.loads(root_raw)
    need(len(root['commits'])==14567)
    final=root['commits'][-1];raw=(directory/(final+'.json')).read_bytes();need(sha256(raw).hexdigest()==final)
    checkpoint=json.loads(raw)['result']['checkpoint']
    with open_result_read_context(directory,value['artifact_sha256'],Path(value['input_directory']),value['input_root_sha256'],
            *proofs,authority=authority()) as reader:
        yield reader,checkpoint
    need(reader.closed and not reader._cache)


def compare_calculation(path,digest,output):
    value=execution(path,digest);declaration,manifest,server,raw,_=publisher.load_declaration(value['publication_file'],value['publication_sha256'])
    supervised=Path(declaration['supervision_directory']);supervisor.history(supervised,declaration['supervision_sha256'])
    _,receipt=supervisor.read_json(sorted(supervised.glob('attempt-*.receipt.json'))[-1])
    progress=receipt['result']['progress'];need(receipt['outcome']=='recorded' and receipt['worker_returncode']==0)
    need(progress['status']=='completed' and progress['steps']==value['plan']['steps'] and progress['counts']==value['plan']['counts'])
    reference=json.loads(runtime.private_bytes(value['reference_file']))
    need(reference['counts']==progress['counts'] and reference['steps']==progress['steps'])
    if reference['kind']=='owned_original166':
        need(manifest['input_root_sha256']=='05a58cc9092682f663bb3e2f827003f51ec8a778f746bb429126a663e841fc04')
    from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
    from app.crop_cycle_calculation_result_read_context import open_calculation_result_read_context
    import secrets
    descriptors=len(os.listdir('/proc/self/fd'));original_rhs=runtime.engine.short._Evaluator.rhs
    def forbidden(*a,**k):raise AssertionError('reference comparison ran RHS')
    runtime.engine.short._Evaluator.rhs=forbidden
    try:
        need(json.loads(server.inspect('tenant-1',raw))==progress)
        with server._open('tenant-1',raw,False) as journal:
            checkpoint=deepcopy(journal.writer._checkpoint)
        document=json.loads(runtime.private_bytes(manifest['config']));inputs=Path(document['input']['directory'])
        artifact=Path(server.directory)/runtime.custody._intent_id('tenant-1',json.loads(raw))/'artifact'
        input_proof=runtime.private_bytes(document['input']['evidence_file'])
        issuer=CalculationResultEvidenceAuthority(server.binding.input_authority,integrity_key=secrets.token_bytes(32),
            issuer_id='owned-full-path-comparison',key_id='comparison-v1')
        proof=issuer.issue(artifact,progress['artifact_sha256'],inputs,manifest['input_root_sha256'],input_proof)
        with reference_reader(reference) as (original,expected_checkpoint):
            compare_checkpoint(expected_checkpoint,checkpoint,offset_days=reference['offset_days'])
            with open_calculation_result_read_context(artifact,progress['artifact_sha256'],inputs,manifest['input_root_sha256'],
                    input_proof,proof,authority=issuer) as candidate:
                comparison=compare_rows(original,candidate,counts=progress['counts'],offset_days=reference['offset_days'],
                    check=lambda:checked(value['preparation_file'],value['preparation_sha256']))
            need(candidate.closed and not candidate._cache)
        if 'row_sha256' in reference:need(comparison['original_row_sha256']==reference['row_sha256'])
        need(json.loads(server.inspect('tenant-1',raw))==progress)
        need(len(os.listdir('/proc/self/fd'))==descriptors)
        execution(path,digest)
        supervisor.immutable(output,{'version':VERSION,'execution_sha256':digest,'comparison':comparison,
            'checkpoint_all_semantics_equal':True,'checkpoint_state_count':len(checkpoint['y']),
            'RHS_calls':0,'FD_before_after':[descriptors,descriptors],'worker':supervisor.identity(os.getpid())})
    finally:runtime.engine.short._Evaluator.rhs=original_rhs


def run(server,raw,*,prepared,reference_file,reference_sha256,evidence,tmp_path,private_config,request,monkeypatch):
    preparation_file,preparation_sha256=prepared;original=checked(*prepared)
    config,config_sha256=runtime.export_runtime(server,raw,tmp_path/'private-runtime')
    pg_files=list(Path(os.environ['TMPDIR']).glob('ossf-login-pg-*/data/postmaster.pid'));need(len(pg_files)==1)
    pg={'process':supervisor.identity(int(pg_files[0].read_text().splitlines()[0])),'data_directory':str(pg_files[0].parent)}
    supervised=tmp_path/'supervised';wall=int(remaining(original))-1;need(wall>0)
    initialized=supervisor.initialize(supervised,config=config,config_sha256=config_sha256,
        max_steps=10000,max_transitions=4096,wall_seconds=wall,owned_pg=pg)
    need(initialized['manifest']['deadline_ns']<=original['deadline_ns'])
    declaration,declaration_sha256=publisher.declare(tmp_path/'publication',supervision_directory=supervised,
        supervision_sha256=initialized['supervision_sha256'])
    _,decl=supervisor.read_json(declaration)
    value={'version':VERSION,'preparation_file':str(preparation_file),'preparation_sha256':preparation_sha256,
        'preparation_deadline_ns':original['deadline_ns'],'config_sha256':config_sha256,
        'publication_file':str(declaration),'publication_sha256':declaration_sha256,
        'reference_file':str(reference_file),'reference_sha256':reference_sha256,'plan':decl['plan'],
        'farm':json.loads(raw)['farm'],'input_root_sha256':json.loads(raw)['input']['root_sha256']}
    path=evidence/'execution.json';digest=supervisor.immutable(path,value);execution(path,digest)
    computed=supervisor.run(supervised,expected_sha256=initialized['supervision_sha256'],max_chunks=16384)
    need(computed['outcome']=='recorded' and computed['worker_returncode']==0 and computed['result']['progress']['status']=='completed')
    execution(path,digest)
    output=evidence/'comparison.result.json'
    compared=child([sys.executable,str(Path(__file__)), '--compare','--execution',str(path),'--sha256',digest,'--output',str(output)],
        name='comparison',prepared=prepared,evidence=evidence)
    comparison=json.loads(runtime.private_bytes(output));need(comparison['execution_sha256']==digest)
    execution(path,digest)
    published_output=declaration.parent/'full-path-publication.result.json'
    published=child([sys.executable,str(ROOT/'research/crop-cycle-registered-publication.py'),
        '--declaration',str(declaration),'--sha256',declaration_sha256,'--output',str(published_output)],
        name='publication',prepared=prepared,evidence=evidence)
    result=json.loads(runtime.private_bytes(published_output));runtime.write_private(evidence/published_output.name,published_output.read_bytes())
    execution(path,digest)
    consumer=module('replay')
    report=consumer.replay(publisher,declaration,declaration_sha256,result,expected=comparison['comparison']['preview'],
        private_config=private_config,request=request,monkeypatch=monkeypatch,tmp_path=tmp_path)
    checked(*prepared)
    archive=evidence/'supervisor-original-attempts';archive.mkdir(mode=0o700)
    for target in supervised.iterdir():
        if target.name!='worker.lock':runtime.write_private(archive/target.name,target.read_bytes())
    return {'version':VERSION,'scope':original['scope'],'preparation_deadline_ns':original['deadline_ns'],
        'inner_supervision_deadline_ns':initialized['manifest']['deadline_ns'],'execution_sha256':digest,
        'comparison_result_sha256':supervisor.digest(output),'comparison_command':compared,'publication_command':published,
        'compute_progress':computed['result']['progress'],'compute_worker':computed['worker'],
        'compute_actual_exit':computed['worker_returncode'],'all_original_rows_checkpoint_compared_before_publication':True,
        'preview_retained_samples_events':{k:len(v) for k,v in comparison['comparison']['preview'].items()},
        'comparison':{k:v for k,v in comparison.items() if k!='comparison'},
        'comparison_counts_hashes':{k:v for k,v in comparison['comparison'].items() if k!='preview'},
        'replay':report,'G0_G4':'not_assessed','actual_crop_Runs':0}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--begin',action='store_true');mode.add_argument('--compare',action='store_true')
    parser.add_argument('--directory',type=Path);parser.add_argument('--wall-seconds',type=int);parser.add_argument('--scope')
    parser.add_argument('--execution',type=Path);parser.add_argument('--sha256');parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.begin:
        if args.directory is None or args.wall_seconds is None or args.scope is None:parser.error('explicit preparation required')
        path,digest=begin(args.directory,wall_seconds=args.wall_seconds,scope=args.scope)
        print(json.dumps({'preparation_file':str(path),'preparation_sha256':digest}),flush=True)
    else:
        if args.execution is None or args.sha256 is None or args.output is None:parser.error('explicit comparison required')
        compare_calculation(args.execution,args.sha256,args.output)
