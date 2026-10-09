"""25h synthetic equations, signed pending-event state and fresh Python exec."""
from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'));sys.path.insert(0,str(ROOT/'backend/tests'))
from app import crop_cycle_server_custody as custody
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from test_crop_cycle_server_custody import open_journal,close_journal
from test_crop_cycle_artifact import PROFILES

spec=importlib.util.spec_from_file_location('independent_stream_reference',ROOT/'research/crop-cycle-stream-execution-reference.py')
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
SOURCE=Path(__file__).resolve()


def replay(journal):
    before=perf_counter();progress=journal.inspect();records={};pages=[];counts={'rhs':0,'advance':0}
    saved=engine.short._Evaluator.rhs,engine.advance_chunk
    def forbid(key):
        def stopped(*args,**kwargs):counts[key]+=1;raise AssertionError('crop computation in stored read')
        return stopped
    engine.short._Evaluator.rhs=forbid('rhs');engine.advance_chunk=forbid('advance')
    try:
        for kind,limit in (('samples',7),('events',2)):
            rows=[];offset=0
            while True:
                tick=perf_counter();page=journal.page(progress,kind,offset,limit)
                size=len(custody._canonical(page));assert size<=2*1024*1024
                pages.append({'kind':kind,'start':offset,'records':len(page['records']),
                    'bytes':size,'seconds':perf_counter()-tick})
                rows.extend(page['records']);offset=page['next']
                if offset==page['total']:break
            records[kind]=rows
    finally:engine.short._Evaluator.rhs,engine.advance_chunk=saved
    assert counts=={'rhs':0,'advance':0}
    return {'progress':progress.decode(),**records},{'seconds':perf_counter()-before,'pages':pages,'read_computation_calls':counts}


def child(request_path):
    tick=perf_counter();r=json.loads(Path(request_path).read_bytes())
    with inputs.open_input_packet(r['input'],r['input_root_sha256'],**PROFILES) as reader:
        context=engine.prepare_context(reader,**PROFILES)
        setup=(Path(r['root']),Path(r['where']),context,r['request'].encode(),r['binding'].encode())
        journal=open_journal(setup,create=False)
        try:
            checkpoint=deepcopy(journal.writer._checkpoint)
            while json.loads(journal.advance({'max_steps':997,'max_transitions':128}))['status']=='yielded':pass
            result,reading=replay(journal)
            response={'result':result,'reading':reading,'restored_checkpoint':checkpoint,
                'final_checkpoint':journal.writer._checkpoint,'wall_seconds':perf_counter()-tick,
                'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
        finally:close_journal(journal)
    Path(r['response']).write_bytes(custody._canonical(response))


def main():
    before=perf_counter();fds=len(os.listdir('/proc/self/fd'));program=reference.long_program()
    print('independent25h-start',flush=True)
    tick=perf_counter();expected,final=reference.independent_control_flow(program,PROFILES)
    independent_seconds=perf_counter()-tick;assert expected['status']=='completed' and expected['steps']==11400
    print('independent25h-complete',expected['steps'],flush=True)
    with TemporaryDirectory(prefix='ossf-signed-cycle-reference-') as temp:
        temporary=Path(temp);input_path=temporary/'input';receipt=reference.write_packet(input_path,program,PROFILES)
        root=temporary/'server';root.mkdir(mode=0o700)
        request={'study_id':'own-study','revision':'r1','input':{'root_sha256':receipt['root_sha256']}}
        raw=custody._canonical(request);binding=custody._canonical({'scope':'unregistered_synthetic_file_test','request':request})
        where=root/custody._intent_id('own-tenant',request);where.mkdir(mode=0o700)
        tick=perf_counter()
        with inputs.open_input_packet(input_path,receipt['root_sha256'],**PROFILES) as reader:
            context=engine.prepare_context(reader,**PROFILES);journal=open_journal((root,where,context,raw,binding))
            try:
                while journal.writer._checkpoint['steps']<4864:
                    remaining=4864-journal.writer._checkpoint['steps']
                    assert json.loads(journal.advance({'max_steps':min(997,remaining),'max_transitions':128}))['status']=='yielded'
                checkpoint=deepcopy(journal.writer._checkpoint)
                assert checkpoint['phase']=='step-end' and checkpoint['at']==program['events'][2]['at']
                assert checkpoint['active_segment']==127
            finally:close_journal(journal)
        print('signed-pending-event',checkpoint['at'],checkpoint['steps'],flush=True)
        response_path=temporary/'response.json';request_path=temporary/'request.json'
        request_path.write_bytes(custody._canonical({'input':str(input_path),'input_root_sha256':receipt['root_sha256'],
            'root':str(root),'where':str(where),'request':raw.decode(),'binding':binding.decode(),'response':str(response_path)}))
        completed=subprocess.run([sys.executable,str(SOURCE),'--child',str(request_path)],cwd=ROOT,capture_output=True,timeout=600)
        assert completed.returncode==0,completed.stderr[-2000:].decode()
        response=json.loads(response_path.read_bytes());response_hash=sha256(response_path.read_bytes()).hexdigest()
        assert custody._canonical(response['restored_checkpoint'])==custody._canonical(checkpoint)
        assert [v.hex() for v in response['restored_checkpoint']['y']]==[v.hex() for v in checkpoint['y']]
        for kind in ('samples','events'):
            assert reference.canonical(response['result'][kind])==reference.canonical(expected[kind])
        for k in final:assert reference.canonical(response['final_checkpoint'][k])==reference.canonical(final[k]),k
        assert [v.hex() for v in response['final_checkpoint']['y']]==[v.hex() for v in final['y']]
        progress=json.loads(response['result']['progress'])
        assert progress['steps']==progress['planned_steps']==11400 and progress['status']=='completed'
        assert progress['counts']=={'samples':len(expected['samples']),'events':len(expected['events'])}
        files=[p for p in where.rglob('*') if p.is_file()]
        assert not any(p.name.endswith('.tmp') for p in files)
        scope={'version':'crop-cycle-server-custody-long-reference-v1','recorded_at_utc':datetime.now(timezone.utc).isoformat(),
            'scope':'unregistered_synthetic_signed_files_only','period_seconds':90000,'forcing_intervals':300,
            'actual_steps':11400,'pending_event_resume_steps':4864,'pending_event_at':checkpoint['at'],
            'restored_checkpoint_bytes_exact':True,'restored_float64_count':121,
            'final_checkpoint_and_vector_exact':True,'canonical_independent_samples_events_equal':True,
            'progress':progress,'signed_intent_total_bytes':sum(p.stat().st_size for p in files),
            'signed_intent_file_count':len(files),'reading':response['reading'],
            'independent_seconds':independent_seconds,'writer_parent_and_exec_seconds':perf_counter()-tick,
            'child_wall_seconds':response['wall_seconds'],'child_peak_rss_mib':response['peak_rss_mib'],
            'private_child_response_sha256':response_hash,'code_sha256':custody.CODE_SHA256,
            'source_sha256':sha256(SOURCE.read_bytes()).hexdigest(),
            'actual_registered_farm_current_rights_not_claimed_here':True,'crop_rows_and_runs_created':0,
            'not_accepted':['actual cultivar/initial/management/forcing','G0-G4','166day crop burden','DB/API/3D/economics']}
    assert not temporary.exists() and len(os.listdir('/proc/self/fd'))==fds
    scope.update(total_wall_seconds=perf_counter()-before,parent_peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        cleanup={'private_directory_removed':True,'fd_count_preserved':True,'child_exit_code':0,'servers_or_databases_started':0})
    Path('/tmp/ossf-cycle-server-long-reference-20261005.json').write_bytes(custody._canonical(scope)+b'\n')
    print(json.dumps({k:scope[k] for k in ('actual_steps','signed_intent_total_bytes','signed_intent_file_count','total_wall_seconds','parent_peak_rss_mib')}),flush=True)


if __name__=='__main__':
    parser=ArgumentParser();parser.add_argument('--child',type=Path);args=parser.parse_args()
    if args.child:child(args.child)
    else:main()
