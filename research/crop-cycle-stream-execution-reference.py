"""Real RHS execution/restore evidence; own synthetic inputs, no farm adoption."""
from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app import crop_cycle_continuation as short
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from app import crop_plant_startup_integration as physical
from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters

PROFILE_PATHS = {
    'growth_profile':'fixtures/crop-growth-reference-parameters-v1.json',
    'cohort_profile':'fixtures/crop-fruit-cohort-reference-parameters-v1.json',
    'transport_profile':'fixtures/crop-fruit-transport-reference-parameters-v1.json',
}


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(path):return sha256(Path(path).read_bytes()).hexdigest()


def profiles():
    return {k:cls((ROOT/PROFILE_PATHS[k]).read_bytes()) for k,cls in (
        ('growth_profile',ReferenceParameters),('cohort_profile',ReferenceFruitCohortParameters),
        ('transport_profile',ReferenceFruitTransportParameters))}


def cases():
    return json.loads((ROOT/'fixtures/crop-plant-startup-integration-reference-v1.json').read_bytes())['cases']


def long_program(*,late_hold=False):
    source = cases(); p = deepcopy(next(c['program'] for c in source if c['case_id']=='empty-entry'))
    event_source = next(c['program'] for c in source if c['case_id']=='full-removal-reentry')['events']
    start = physical._utc(p['segments'][0]['start']); template = deepcopy(p['segments'][0])
    p['segments'] = []
    for i in range(300):
        segment = deepcopy(template)
        segment['start'] = physical._stamp(start+timedelta(seconds=i*300))
        segment['end'] = physical._stamp(start+timedelta(seconds=(i+1)*300))
        p['segments'].append(segment)
    p['output_times'] = sorted({physical._stamp(start+timedelta(seconds=i*3600)) for i in range(26)}
                             | {physical._stamp(start+timedelta(seconds=38400))})
    p['events'] = []
    for offset,index in ((0,0),(385,0),(38400,1),(38407,0),(90000,2)):
        event = deepcopy(event_source[index]);event['at'] = physical._stamp(start+timedelta(seconds=offset))
        p['events'].append(event)
    p['solver']['max_step_seconds'] = 60 if late_hold else 8
    p['solver']['max_steps'] = 20000
    if late_hold:p['events'][-1]['removals']['values']['leaf']['value'] = 1e9
    return p


def write_packet(path,program,params):
    program = deepcopy(program);anchors = program.pop('output_times')
    return inputs.write_input_packet(path,**program,anchors=anchors,outputs=anchors,
                                    **params,program_id='own-synthetic-rhs-restore-v1')


def finish(ctx,checkpoint,quota=97,transitions=128):
    samples = [];events = [];chunks = 0;max_bytes = 0
    while True:
        result = engine.advance_chunk(ctx,checkpoint,{'max_steps':quota,'max_transitions':transitions})
        samples.extend(result['samples']);events.extend(result['events']);chunks += 1
        if result['status'] != 'yielded':break
        raw = engine.checkpoint_bytes(ctx,result['checkpoint']);max_bytes = max(max_bytes,len(raw))
        checkpoint = engine.restore_checkpoint(ctx,raw)
    return {**result,'samples':samples,'events':events},chunks,max_bytes


def child_restore(input_path,output_path):
    started = perf_counter();request = json.loads(Path(input_path).read_bytes());params = profiles()
    with inputs.open_input_packet(request['packet'],request['input_root_sha256'],**params) as reader:
        ctx = engine.prepare_context(reader,**params)
        checkpoint = engine.restore_checkpoint(ctx,canonical(request['checkpoint']))
        before = [v.hex() for v in checkpoint['y']]
        result,chunks,max_bytes = finish(ctx,checkpoint)
        response = {'result':result,'restored_float64_hex':before,'chunks':chunks,'max_checkpoint_bytes':max_bytes,
                    'root_sha256':ctx.root_sha256,'engine_sha256':engine.CODE_SHA256,
                    'grid_index_pages':len(ctx.index),'last_grid_window_records':len(ctx._cache['grid'][1]),
                    'input_cache_records':sum(len(v[1]) for v in reader._cache.values()),
                    'wall_seconds':perf_counter()-started,
                    'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    Path(output_path).write_bytes(canonical(response)+b'\n')


def independent_control_flow(program,params):
    """Whole-program loop using the frozen rates; no new driver/cursor/index."""
    program = deepcopy(program)
    block = physical.legacy._block
    program['initial_state'] = block(program['initial_state'],physical.legacy.coupled.PLANT_UNITS,physical.ARRAY_UNITS)
    for segment in program['segments']:
        for key,units in (('forcing',physical.plant.FORCING_UNITS),
                          ('removals',physical.legacy.coupled.REMOVAL_UNITS),
                          ('fruit_entry',physical.legacy.coupled.ENTRY_UNITS)):
            segment[key] = block(segment[key],units)
        segment['relative_growth_rate'] = block(segment['relative_growth_rate'],{}, {'fruit_relative_growth_rate':'1/s'})
    for event in program['events']:
        event['removals'] = block(event['removals'],
            {'leaf':physical.plant.MASS_UNIT,'stem_root':physical.plant.MASS_UNIT},{'fruit_fraction':'1'})
    initial = program['initial_state']['values']
    seed = [float(initial[k]['value']) for k in physical.PLANT]+[
        float(q['value']) for k in physical.ARRAY_UNITS for q in initial[k]]+[0.0]*16
    clocks = [];prefix = Fraction.from_float(seed[4])
    for s in program['segments']:
        a,b = physical._utc(s['start']),physical._utc(s['end'])
        slope = Fraction.from_float(float(s['forcing']['values']['canopy_temperature']['value']))/Fraction.from_float(params['growth_profile'].values['seconds_per_day'])
        clocks.append((a,prefix,slope));prefix += slope*int((b-a).total_seconds())
    evaluator = short._Evaluator(SimpleNamespace(program=program,clocks=clocks,seed=seed,**params))
    boundaries = sorted({physical._utc(t) for t in program['output_times']}
                        | {physical._utc(s['end']) for s in program['segments']}
                        | {physical._utc(e['at']) for e in program['events']})
    planned = sum((int((b-a).total_seconds())+program['solver']['max_step_seconds']-1)//program['solver']['max_step_seconds']
                  for a,b in zip(boundaries,boundaries[1:]))
    pulses = {physical._utc(e['at']):e for e in program['events']};outputs = set(program['output_times'])
    at = boundaries[0];y = list(seed);active = 0;steps = 0;event_count = 0;samples = [];events = []
    prefixes = {'output_prefix_sha256':short._hash([]),'event_prefix_sha256':short._hash([]),
                'output_cursor':0,'event_cursor':0};last_confirmed = None;hold = None
    try:
        for boundary in boundaries:
            while at < boundary:
                h = min(program['solver']['max_step_seconds'],int((boundary-at).total_seconds()))
                half = at+timedelta(seconds=h/2);end = at+timedelta(seconds=h)
                k1 = evaluator.rhs(y,at,active,'rk4-k1')
                k2 = evaluator.rhs([v+h*d/2 for v,d in zip(y,k1,strict=True)],half,active,'rk4-k2')
                k3 = evaluator.rhs([v+h*d/2 for v,d in zip(y,k2,strict=True)],half,active,'rk4-k3')
                k4 = evaluator.rhs([v+h*d for v,d in zip(y,k3,strict=True)],end,active,'rk4-k4')
                candidate = physical._advance(y,(k1,k2,k3,k4),h,end)
                candidate = evaluator.clock(candidate,end,active,'step-end')
                evaluator.rhs(candidate,end,active,'step-end')
                snapshot = evaluator.snapshot(candidate,end,steps+event_count+1)
                y,at = candidate,end;steps += 1;last_confirmed = {**snapshot,'phase':'step-end'}
            if active+1 < len(program['segments']) and at == physical._utc(program['segments'][active]['end']):active += 1
            physical._guard(y,at,'boundary');event = pulses.get(at);candidate,removed = evaluator.remove_event(y,event,at)
            phase = 'boundary-after-event' if event else 'boundary'
            evaluator.rhs(candidate,at,active,phase)
            snapshot = evaluator.snapshot(candidate,at,steps+event_count+bool(event))
            if event:
                record = {'at':physical._stamp(at),'input_id':event['removals']['input_id'],
                          'before':physical._state(y),'after':physical._state(candidate),'removed':removed}
                events.append(record);short._prefix(prefixes,'event_prefix_sha256','event_cursor',record);event_count += 1
            y = candidate;last_confirmed = {**snapshot,'phase':phase}
            if physical._stamp(at) in outputs:
                samples.append(snapshot);short._prefix(prefixes,'output_prefix_sha256','output_cursor',snapshot)
    except physical._EvaluationHold as exc:
        hold = {'at':physical._stamp(exc.at),'phase':exc.phase,'reason':exc.reason}
    result = {'status':'hold' if hold else 'completed','scope':'software_research_only',
              'samples':samples,'events':events,'steps':steps,'planned_steps':planned}
    if hold:result.update(hold=hold,last_confirmed=last_confirmed)
    return result,{'y':y,'seed':seed,'steps':steps,'event_count':event_count,
                   'output_prefix_sha256':prefixes['output_prefix_sha256'],
                   'event_prefix_sha256':prefixes['event_prefix_sha256']}


def main(output):
    started = perf_counter();params = profiles();records = [];max_bytes = 0
    source = Path(__file__).resolve();descriptors_before = len(os.listdir('/proc/self/fd'))
    with TemporaryDirectory(prefix='ossf-cycle-stream-rhs-') as directory:
        temporary = Path(directory)
        for index,case in enumerate(cases()):
            print('short-process',case['case_id'],flush=True)
            program = deepcopy(case['program']);packet_path = temporary/('packet-'+str(index))
            receipt = write_packet(packet_path,program,params)
            with inputs.open_input_packet(packet_path,receipt['root_sha256'],**params) as reader:
                ctx = engine.prepare_context(reader,**params);cp = engine.start(ctx);samples = [];events = []
                if index:
                    while True:
                        step = engine.advance_chunk(ctx,cp,{'max_steps':1,'max_transitions':1})
                        assert step['status']=='yielded'
                        samples.extend(step['samples']);events.extend(step['events']);cp = step['checkpoint']
                        if index in (1,4) and cp['phase']=='boundary-committed':break
                        if index in (2,5) and cp['phase']=='step-end':break
                        if index==3 and cp['phase']=='step-end' and cp['at']==program['events'][1]['at']:break
                request = temporary/'request.json';response = temporary/'response.json'
                raw = engine.checkpoint_bytes(ctx,cp);max_bytes = max(max_bytes,len(raw))
                request.write_bytes(canonical({'packet':str(packet_path),'input_root_sha256':receipt['root_sha256'],'checkpoint':json.loads(raw)}))
                subprocess.run([sys.executable,str(source),'--resume-input',str(request),'--resume-output',str(response)],
                               cwd=ROOT,check=True,timeout=180,capture_output=True)
                child = json.loads(response.read_bytes());actual = child['result']
                assert child['restored_float64_hex']==[v.hex() for v in cp['y']]
                assert child['root_sha256']==ctx.root_sha256 and child['engine_sha256']==engine.CODE_SHA256
                expected = physical.integrate_plant_startup(**program,**params)
                combined = {**actual,'samples':samples+actual['samples'],'events':events+actual['events']}
                for field in ('status','scope','samples','events','steps','planned_steps'):
                    assert canonical(combined[field])==canonical(expected[field]),field
                records.append({'case_id':case['case_id'],'resume_phase':cp['phase'],'resume_at':cp['at'],
                    'resume_steps':cp['steps'],'steps':expected['steps'],'sample_count':len(combined['samples']),
                    'event_count':len(combined['events']),'binary_roundtrip_exact':True,'restored_float64_values':121,
                    'original_full_physical_payload_equal':True,'child_wall_seconds':child['wall_seconds'],
                    'child_peak_rss_mib':child['peak_rss_mib'],'private_response_sha256':digest(response)})
        print('long-independent-control-flow start',flush=True)
        program = long_program();input_hash = sha256(canonical(program)).hexdigest()
        baseline_started = perf_counter();expected,final = independent_control_flow(program,params)
        assert expected['status']=='completed',expected.get('hold')
        baseline_seconds = perf_counter()-baseline_started
        print('long-independent-control-flow completed',expected['steps'],flush=True)
        packet_path = temporary/'long-packet';receipt = write_packet(packet_path,program,params)
        parent_started = perf_counter()
        with inputs.open_input_packet(packet_path,receipt['root_sha256'],**params) as reader:
            ctx = engine.prepare_context(reader,**params);cp = engine.start(ctx);samples = [];events = [];parent_chunks = 0
            # 128 original 300-second intervals with ceil(300/8)=38 steps each.
            while cp['steps'] < 4864:
                result = engine.advance_chunk(ctx,cp,{'max_steps':min(997,4864-cp['steps']),'max_transitions':10000})
                assert result['status']=='yielded',result.get('hold')
                samples.extend(result['samples']);events.extend(result['events']);parent_chunks += 1
                cp = engine.restore_checkpoint(ctx,engine.checkpoint_bytes(ctx,result['checkpoint']))
                print('long-parent confirmed',cp['steps'],cp['at'],flush=True)
            assert cp['phase']=='step-end' and cp['at']==program['events'][2]['at'] and cp['active_segment']==127
            assert cp['event_count']==2 and cp['seed']==engine.start(ctx)['seed']
            raw = engine.checkpoint_bytes(ctx,cp);max_bytes = max(max_bytes,len(raw))
            request.write_bytes(canonical({'packet':str(packet_path),'input_root_sha256':receipt['root_sha256'],'checkpoint':json.loads(raw)}))
            subprocess.run([sys.executable,str(source),'--resume-input',str(request),'--resume-output',str(response)],
                           cwd=ROOT,check=True,timeout=600,capture_output=True)
            child = json.loads(response.read_bytes());actual = child['result']
            assert child['restored_float64_hex']==[v.hex() for v in cp['y']]
            assert child['root_sha256']==ctx.root_sha256 and child['engine_sha256']==engine.CODE_SHA256
            combined = {**actual,'samples':samples+actual['samples'],'events':events+actual['events']}
            for field in ('status','scope','samples','events','steps','planned_steps'):
                assert canonical(combined[field])==canonical(expected[field]),field
            for field in final:assert canonical(actual['checkpoint'][field])==canonical(final[field]),field
            for field in ('y','seed'):
                assert [v.hex() for v in actual['checkpoint'][field]]==[v.hex() for v in final[field]],field
            assert actual['steps']>10000 and (physical._utc(actual['checkpoint']['at'])-physical._utc(ctx.start_at)).total_seconds()>86400
            assert sha256(canonical(program)).hexdigest()==input_hash
            long_record = {'period_seconds':90000,'forcing_intervals':300,'boundaries':ctx.boundary_count,
                'steps':actual['steps'],'sample_count':len(combined['samples']),'event_count':len(combined['events']),
                'independent_control_flow_and_canonical_full_physical_payload_equal':True,
                'final_seed_and_prefixes_equal':True,'final_vector_and_seed_float64_hex_equal':True,
                'resume_at':cp['at'],'resume_phase':cp['phase'],'resume_steps':cp['steps'],'resume_active_segment':cp['active_segment'],
                'restored_float64_values':121,'binary_roundtrip_exact':True,'grid_index_pages':len(ctx.index),
                'child_last_grid_window_records':child['last_grid_window_records'],'child_input_cache_records':child['input_cache_records'],
                'parent_chunks':parent_chunks,'child_chunks':child['chunks'],'max_checkpoint_bytes':max(len(raw),child['max_checkpoint_bytes']),
                'input_program_sha256':input_hash,'input_root_sha256':receipt['root_sha256'],'packet_bytes':receipt['packet_bytes'],
                'independent_control_flow_wall_seconds':baseline_seconds,'stream_parent_and_child_wall_seconds':perf_counter()-parent_started,
                'child_wall_seconds':child['wall_seconds'],'child_peak_rss_mib':child['peak_rss_mib'],
                'private_response_sha256':digest(response)}
        print('long-process completed',long_record['steps'],flush=True)
        hold_program = long_program(late_hold=True)
        expected_hold,_ = independent_control_flow(hold_program,params)
        hold_packet = temporary/'hold-packet';hold_receipt = write_packet(hold_packet,hold_program,params)
        with inputs.open_input_packet(hold_packet,hold_receipt['root_sha256'],**params) as reader:
            hold_ctx = engine.prepare_context(reader,**params)
            actual_hold,hold_chunks,_ = finish(hold_ctx,engine.start(hold_ctx),97,128)
            for field in ('status','scope','samples','events','steps','planned_steps','hold','last_confirmed'):
                assert canonical(actual_hold[field])==canonical(expected_hold[field]),field
            assert actual_hold['checkpoint'] is None and actual_hold['hold']['at']==hold_program['events'][-1]['at']
            assert actual_hold['status']=='hold' and actual_hold['steps']==1502
            hold_record = {'period_seconds':90000,'steps':actual_hold['steps'],'chunks':hold_chunks,
                'hold':actual_hold['hold'],'last_confirmed_at':actual_hold['last_confirmed']['at'],
                'last_confirmed_phase':actual_hold['last_confirmed']['phase'],'checkpoint_is_none':True,
                'independent_whole_payload_equal':True,'past_sample_count':len(actual_hold['samples']),
                'committed_event_count':len(actual_hold['events'])}
        temporary_path = str(temporary)
    assert not Path(temporary_path).exists()
    assert len(os.listdir('/proc/self/fd'))==descriptors_before
    evidence = {'evidence_version':'crop-cycle-stream-execution-reference-v1',
        'recorded_at':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'scope':'software_research_only',
        'cli_requirement':'gpt-6.1-sol/xhigh; current CLI session; no recursive invocation',
        'engine_version':engine.VERSION,'physical_code_sha256':physical.CODE_HASHES,
        'six_short_programs':records,'long_actual_rhs':long_record,'long_late_event_hold':hold_record,
        'separate_python_processes':7,'restored_float64_values':7*121,'short_steps':sum(r['steps'] for r in records),
        'max_short_selected_checkpoint_bytes':max_bytes,'wall_seconds':perf_counter()-started,
        'parent_peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'cleanup':{'temporary_packet_and_responses_removed':True,'parent_fd_count_preserved':True,
                   'owned_child_processes_terminal':True,'servers_started':0,'databases_started':0},
        'file_sha256':{p:digest(ROOT/p) for p in (
            str(source.relative_to(ROOT)),'backend/app/crop_cycle_stream_execution.py',
            'backend/tests/test_crop_cycle_stream_execution.py','contracts/crop-cycle-stream-execution-v1.md',
            'fixtures/crop-plant-startup-integration-reference-v1.json',*PROFILE_PATHS.values())},
        'not_run':['actual farm/cultivar/full-cycle inputs','166-day/1,440,002-step actual RHS burden',
                   'durable cycle artifact/current rights/API/3D','fresh kg/resource/economics','G0-G4 adoption/validation']}
    Path(output).write_bytes(json.dumps(evidence,ensure_ascii=False,indent=2,allow_nan=False).encode()+b'\n')
    print(json.dumps({'wall_seconds':evidence['wall_seconds'],'parent_peak_rss_mib':evidence['parent_peak_rss_mib'],
                      'long_steps':long_record['steps'],'hold_steps':hold_record['steps'],'processes':7}),flush=True)


if __name__=='__main__':
    parser = ArgumentParser();parser.add_argument('--output');parser.add_argument('--resume-input');parser.add_argument('--resume-output')
    args = parser.parse_args()
    if args.resume_input:child_restore(args.resume_input,args.resume_output)
    else:main(args.output)
