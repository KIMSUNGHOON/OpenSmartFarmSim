"""Actual immutable crop writes, separate-process resume/read and crash evidence."""
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
sys.path.insert(0,str(ROOT/'backend'))
from app import crop_cycle_artifact as artifact
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from app import crop_plant_startup_integration as physical

spec=importlib.util.spec_from_file_location('stream_reference',ROOT/'research/crop-cycle-stream-execution-reference.py')
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
NOTICE=(ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()
SOURCE=Path(__file__).resolve()


def canonical(value):return artifact._canonical(value)
def digest(path):return sha256(Path(path).read_bytes()).hexdigest()


def finish(writer):
    while writer.advance({'max_steps':997,'max_transitions':128})['status']=='yielded':pass
    return writer.finalize()


def replay(path,receipt,context):
    before=perf_counter();pages=[];records={};counts={'rhs':0,'advance':0,'original_integrator':0}
    saved=(engine.short._Evaluator.rhs,engine.advance_chunk,physical.integrate_plant_startup)
    def forbid(key):
        def failure(*args,**kwargs):counts[key]+=1;raise AssertionError('RHS/advance/integrator in artifact read')
        return failure
    engine.short._Evaluator.rhs=forbid('rhs');engine.advance_chunk=forbid('advance')
    physical.integrate_plant_startup=forbid('original_integrator')
    try:
        with artifact.open_artifact(path,receipt['artifact_sha256'],context,notice_raw=NOTICE) as reader:
            summary=reader.summary
            for kind in ('samples','events'):
                rows=[];offset=0
                while True:
                    tick=perf_counter();page=reader.page(kind,offset,3 if kind=='samples' else 2)
                    size=len(canonical(page));assert size<=artifact.LIMITS['page_bytes']
                    pages.append({'kind':kind,'start':offset,'count':len(page['records']),
                                  'response_bytes':size,'wall_seconds':perf_counter()-tick})
                    rows.extend(page['records']);offset=page['next']
                    if offset==page['total']:break
                records[kind]=rows
            selected=reader.page('samples',max(0,summary['counts']['samples']//2),1)
            assert selected['records']==records['samples'][selected['start']:selected['next']]
            cache_records=0 if reader._page_cache is None else len(reader._page_cache[1])
            referenced=reader._referenced_bytes
    finally:
        engine.short._Evaluator.rhs,engine.advance_chunk,physical.integrate_plant_startup=saved
    assert not any(counts.values())
    return {'summary':summary,**records}, {'wall_seconds':perf_counter()-before,'pages':pages,
        'read_calculation_calls':counts,'last_page_cache_records':cache_records,'referenced_bytes':referenced}


def child(request_path,response_path):
    started=perf_counter();request=json.loads(Path(request_path).read_bytes());params=reference.profiles()
    with inputs.open_input_packet(request['input_directory'],request['input_root_sha256'],**params) as reader:
        context=engine.prepare_context(reader,**params)
        if request['operation']=='crash':
            with artifact.open_writer(request['artifact_directory'],request['head_sha256'],context,notice_raw=NOTICE) as writer:
                publish=writer._publish_head
                def crash(head):
                    if request['crash_at']=='before-head':os._exit(73)
                    publish(head);os._exit(74)
                writer._publish_head=crash
                writer.advance({'max_steps':1,'max_transitions':1})
            raise AssertionError('crash not triggered')
        with artifact.open_writer(request['artifact_directory'],request['head_sha256'],context,notice_raw=NOTICE) as writer:
            restored=[v.hex() for v in writer._checkpoint['y']]
            restored_phase=writer._checkpoint['phase'];restored_at=writer._checkpoint['at']
            receipt=finish(writer)
        result,reading=replay(request['artifact_directory'],receipt,context)
        response={'receipt':receipt,'result':result,'restored_float64_hex':restored,
                  'restored_phase':restored_phase,'restored_at':restored_at,'reading':reading,
                  'wall_seconds':perf_counter()-started,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    Path(response_path).write_bytes(canonical(response)+b'\n')


def run_child(temporary,request,*,crash=False):
    request_path=temporary/'request.json';response_path=temporary/'response.json'
    request_path.write_bytes(canonical(request))
    result=subprocess.run([sys.executable,str(SOURCE),'--request',str(request_path),'--response',str(response_path)],
                          cwd=ROOT,capture_output=True,timeout=600)
    if crash:
        assert result.returncode==(73 if request['crash_at']=='before-head' else 74),result.stderr.decode()
        return result.returncode
    assert result.returncode==0,result.stderr.decode()
    return json.loads(response_path.read_bytes()),digest(response_path)


def request(input_path,input_root,artifact_path,head,operation='resume'):
    return {'operation':operation,'input_directory':str(input_path),'input_root_sha256':input_root,
            'artifact_directory':str(artifact_path),'head_sha256':head}


def compare(result,expected):
    actual={**result['summary'],'samples':result['samples'],'events':result['events']}
    fields=['status','scope','steps','planned_steps','samples','events']
    if expected['status']=='hold':fields+=['hold','last_confirmed']
    for key in fields:assert canonical(actual[key])==canonical(expected[key]),key


def main(output):
    started=perf_counter();params=reference.profiles();short_records=[];crashes=[]
    fd_before=len(os.listdir('/proc/self/fd'));max_checkpoint=0;max_read_page=0;all_children=[]
    with TemporaryDirectory(prefix='ossf-cycle-artifact-proof-') as directory:
        temporary=Path(directory)
        for index,case in enumerate(reference.cases()):
            print('short-artifact',case['case_id'],flush=True)
            program=deepcopy(case['program']);input_path=temporary/('input-'+str(index));path=temporary/('result-'+str(index))
            input_receipt=reference.write_packet(input_path,program,params)
            with inputs.open_input_packet(input_path,input_receipt['root_sha256'],**params) as reader:
                context=engine.prepare_context(reader,**params)
                with artifact.create_writer(path,context,notice_raw=NOTICE) as writer:
                    if index:
                        while True:
                            step=writer.advance({'max_steps':1,'max_transitions':1});assert step['status']=='yielded'
                            cp=writer._checkpoint
                            if index in (1,4) and cp['phase']=='boundary-committed':break
                            if index in (2,5) and cp['phase']=='step-end':break
                            if index==3 and cp['phase']=='step-end' and cp['at']==program['events'][1]['at']:break
                    cp=deepcopy(writer._checkpoint);head=writer.head_sha256
                    max_checkpoint=max(max_checkpoint,len(engine.checkpoint_bytes(context,cp)))
                response,response_hash=run_child(temporary,request(input_path,input_receipt['root_sha256'],path,head))
                assert response['restored_float64_hex']==[v.hex() for v in cp['y']]
                expected=physical.integrate_plant_startup(**program,**params);compare(response['result'],expected)
                all_children.append(response['peak_rss_mib'])
                max_read_page=max(max_read_page,max(p['response_bytes'] for p in response['reading']['pages']))
                short_records.append({'case_id':case['case_id'],'resume_at':cp['at'],'resume_phase':cp['phase'],
                    'resume_steps':cp['steps'],'restored_float64_values':121,'binary_restore_exact':True,
                    'canonical_original_payload_equal':True,'steps':expected['steps'],'sample_count':len(expected['samples']),
                    'event_count':len(expected['events']),'commit_count':response['receipt']['commit_count'],
                    'artifact_sha256':response['receipt']['artifact_sha256'],'reading':response['reading'],
                    'child_wall_seconds':response['wall_seconds'],'child_peak_rss_mib':response['peak_rss_mib'],
                    'private_response_sha256':response_hash})
        print('long-independent start',flush=True)
        program=reference.long_program();tick=perf_counter();expected,final=reference.independent_control_flow(program,params)
        assert expected['status']=='completed';baseline_seconds=perf_counter()-tick
        print('long-independent complete',expected['steps'],flush=True)
        input_path=temporary/'long-input';path=temporary/'long-result'
        input_receipt=reference.write_packet(input_path,program,params);tick=perf_counter()
        with inputs.open_input_packet(input_path,input_receipt['root_sha256'],**params) as reader:
            context=engine.prepare_context(reader,**params)
            with artifact.create_writer(path,context,notice_raw=NOTICE) as writer:
                while writer._checkpoint['steps']<4864:
                    remaining=4864-writer._checkpoint['steps']
                    result=writer.advance({'max_steps':min(997,remaining),'max_transitions':128})
                    assert result['status']=='yielded'
                cp=deepcopy(writer._checkpoint);head=writer.head_sha256
                assert cp['phase']=='step-end' and cp['at']==program['events'][2]['at'] and cp['active_segment']==127
                print('long-pending checkpoint saved',cp['steps'],cp['at'],len(writer._hashes),flush=True)
            response,response_hash=run_child(temporary,request(input_path,input_receipt['root_sha256'],path,head))
            assert response['restored_float64_hex']==[v.hex() for v in cp['y']]
            compare(response['result'],expected)
            summary=response['result']['summary']
            for key in final:assert canonical(summary['checkpoint'][key])==canonical(final[key]),key
            assert [v.hex() for v in summary['checkpoint']['y']]==[v.hex() for v in final['y']]
            all_children.append(response['peak_rss_mib'])
            max_read_page=max(max_read_page,max(p['response_bytes'] for p in response['reading']['pages']))
            files=list(path.iterdir());storage_bytes=sum(p.stat().st_size for p in files)
            long_record={'period_seconds':90000,'forcing_intervals':300,'steps':summary['steps'],'sample_count':len(expected['samples']),
                'event_count':len(expected['events']),'commit_count':summary['commit_count'],'resume_steps':cp['steps'],
                'resume_phase':cp['phase'],'resume_at':cp['at'],'resume_active_segment':cp['active_segment'],
                'restored_float64_values':121,'binary_restore_exact':True,'canonical_independent_full_payload_equal':True,
                'final_vector_float64_hex_and_prefixes_equal':True,'artifact_sha256':response['receipt']['artifact_sha256'],
                'storage_bytes':storage_bytes,'files':len(files),'no_remaining_temporary_files':not any(p.name.endswith('.tmp') for p in files),
                'independent_control_flow_wall_seconds':baseline_seconds,'writer_parent_and_child_wall_seconds':perf_counter()-tick,
                'child_wall_seconds':response['wall_seconds'],'child_peak_rss_mib':response['peak_rss_mib'],
                'reading':response['reading'],'private_response_sha256':response_hash}
        print('long-artifact complete',long_record['steps'],long_record['storage_bytes'],flush=True)
        for mode in ('before-head','after-head'):
            p=deepcopy(reference.cases()[3]['program']);input_path=temporary/('crash-input-'+mode);path=temporary/('crash-result-'+mode)
            input_receipt=reference.write_packet(input_path,p,params)
            with inputs.open_input_packet(input_path,input_receipt['root_sha256'],**params) as reader:
                context=engine.prepare_context(reader,**params)
                with artifact.create_writer(path,context,notice_raw=NOTICE) as writer:head=writer.head_sha256
                code=run_child(temporary,{**request(input_path,input_receipt['root_sha256'],path,head,'crash'),'crash_at':mode},crash=True)
                with artifact._Files(path) as files:new_head,new_hash=files._head()
                assert new_head['commit_count']==(0 if mode=='before-head' else 1)
                assert (new_hash==head)==(mode=='before-head')
                with artifact.open_writer(path,new_hash,context,notice_raw=NOTICE) as writer:
                    assert writer._checkpoint['phase']==('initial-ready' if mode=='before-head' else 'boundary-committed')
                    receipt=finish(writer)
                actual,reading=replay(path,receipt,context);expected=physical.integrate_plant_startup(**p,**params);compare(actual,expected)
                crashes.append({'crash_at':mode,'actual_child_exit_code':code,'commits_after_crash':new_head['commit_count'],
                    'last_committed_prefix_restored':True,'canonical_original_payload_equal':True,
                    'read_calculation_calls':reading['read_calculation_calls'],'artifact_sha256':receipt['artifact_sha256']})
        temporary_path=str(temporary)
    assert not Path(temporary_path).exists() and len(os.listdir('/proc/self/fd'))==fd_before
    evidence={'evidence_version':'crop-cycle-artifact-reference-v1',
        'recorded_at':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'scope':'software_research_only',
        'six_short_programs':short_records,'long_actual_rhs_artifact':long_record,'actual_process_crashes':crashes,
        'separate_resume_read_processes':7,'separate_crash_processes':2,'restored_float64_values':847,
        'max_selected_checkpoint_bytes':max_checkpoint,'max_observed_read_page_bytes':max_read_page,
        'wall_seconds':perf_counter()-started,'parent_peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'child_max_peak_rss_mib':max(all_children),'artifact_code_sha256':artifact.CODE_SHA256,
        'file_sha256':{p:digest(ROOT/p) for p in (str(SOURCE.relative_to(ROOT)),
            'backend/app/crop_cycle_artifact.py','backend/tests/test_crop_cycle_artifact.py','contracts/crop-cycle-artifact-v1.md',
            'research/crop-cycle-stream-execution-reference.py','fixtures/crop-plant-startup-integration-reference-v1.json',
            'LICENSES/GreenLight-BSD-3-Clause-Clear.txt',*reference.PROFILE_PATHS.values())},
        'cleanup':{'owned_temp_input_artifact_response_files_removed':True,'parent_fd_count_preserved':True,
            'children_terminal':True,'servers_started':0,'databases_started':0},
        'not_run':['actual host power loss/storage durability','full166day/1440002step burden',
            'farm/current rights/HMAC/DB/API/3D cycle linkage','actual cultivar/initial/management/forcing adoption',
            'freshkg/resources/economics/G0-G4 validation']}
    Path(output).write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:evidence[k] for k in ('wall_seconds','parent_peak_rss_mib','child_max_peak_rss_mib','max_observed_read_page_bytes')}),flush=True)


if __name__=='__main__':
    parser=ArgumentParser();parser.add_argument('--output');parser.add_argument('--request');parser.add_argument('--response')
    args=parser.parse_args()
    if args.request:child(args.request,args.response)
    else:main(args.output)
