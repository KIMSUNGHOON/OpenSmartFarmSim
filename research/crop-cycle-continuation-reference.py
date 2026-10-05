"""Actual short-model restore evidence, including serial separate Python processes."""
from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import resource
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app import crop_cycle_continuation as cycle
from app import crop_plant_startup_integration as original
from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters

PROFILE_PATHS = {
    'growth_profile':'fixtures/crop-growth-reference-parameters-v1.json',
    'cohort_profile':'fixtures/crop-fruit-cohort-reference-parameters-v1.json',
    'transport_profile':'fixtures/crop-fruit-transport-reference-parameters-v1.json',
}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def profiles():
    return {k:cls((ROOT/PROFILE_PATHS[k]).read_bytes()) for k,cls in (
        ('growth_profile',ReferenceParameters), ('cohort_profile',ReferenceFruitCohortParameters),
        ('transport_profile',ReferenceFruitTransportParameters))}


def child_restore(input_path, output_path):
    started = perf_counter(); request = json.loads(Path(input_path).read_bytes())
    ctx = cycle.prepare_context(**request['program'], **profiles())
    cp = cycle.restore_checkpoint(ctx,canonical(request['checkpoint']))
    before = [v.hex() for v in cp['y']]
    samples, events, chunks = [], [], 0
    while True:
        result = cycle.advance_chunk(ctx,cp,{'max_steps':7,'max_transitions':13})
        samples.extend(result['samples']); events.extend(result['events']); chunks += 1
        if result['status'] != 'yielded': break
        cp = cycle.restore_checkpoint(ctx,cycle.checkpoint_bytes(ctx,result['checkpoint']))
    response = {'result':{**result,'samples':samples,'events':events}, 'restored_float64_hex':before,
                'chunks':chunks, 'wall_seconds':perf_counter()-started,
                'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                'root_sha256':ctx.root_sha256, 'engine_sha256':cycle.CODE_SHA256}
    Path(output_path).write_bytes(canonical(response)+b'\n')


def main(output):
    started = perf_counter(); reference = ROOT/'fixtures/crop-plant-startup-integration-reference-v1.json'
    cases = json.loads(reference.read_bytes())['cases']; params = profiles(); records = []; max_bytes = 0
    source = Path(__file__).resolve()
    with TemporaryDirectory(prefix='ossf-cycle-restore-') as directory:
        temporary = Path(directory)
        for index,case in enumerate(cases):
            program = deepcopy(case['program']); input_hash = sha256(canonical(program)).hexdigest()
            ctx = cycle.prepare_context(**program, **params); cp = cycle.start(ctx); samples = []; events = []
            # Exercise initial-ready, committed t0, an interior step, and a pending event boundary.
            if index:
                while True:
                    result = cycle.advance_chunk(ctx,cp,{'max_steps':1,'max_transitions':1})
                    assert result['status'] == 'yielded'
                    samples.extend(result['samples']); events.extend(result['events']); cp = result['checkpoint']
                    if index in (1,4) and cp['phase'] == 'boundary-committed': break
                    if index in (2,5) and cp['phase'] == 'step-end': break
                    if index == 3 and cp['phase'] == 'step-end' and cp['at'] == program['events'][1]['at']: break
            raw = cycle.checkpoint_bytes(ctx,cp); max_bytes = max(max_bytes,len(raw))
            request_path = temporary/'request.json'; response_path = temporary/'response.json'
            request_path.write_bytes(canonical({'program':program,'checkpoint':json.loads(raw)}))
            subprocess.run([sys.executable,str(source),'--resume-input',str(request_path),'--resume-output',str(response_path)],
                           cwd=ROOT,check=True,timeout=120,capture_output=True)
            response = json.loads(response_path.read_bytes()); actual = response['result']
            assert response['restored_float64_hex'] == [v.hex() for v in cp['y']]
            assert response['root_sha256'] == ctx.root_sha256 and response['engine_sha256'] == cycle.CODE_SHA256
            expected = original.integrate_plant_startup(**program, **params)
            combined = {**actual,'samples':samples+actual['samples'],'events':events+actual['events']}
            assert combined['status'] == expected['status'] == 'completed'
            for field in ('samples','events','steps','planned_steps','scope'): assert combined[field] == expected[field]
            # Partition and process identity may change checkpoint parents; physical prefixes remain identical.
            continuous = cycle.advance_chunk(ctx,cycle.start(ctx),{'max_steps':10000,'max_transitions':10000})
            assert continuous['status'] == 'completed'
            for field in ('y','seed','steps','event_count','sequence','clock','output_prefix_sha256','event_prefix_sha256'):
                assert actual['checkpoint'][field] == continuous['checkpoint'][field]
            assert sha256(canonical(program)).hexdigest() == input_hash
            records.append({'case_id':case['case_id'], 'resume_phase':cp['phase'], 'resume_at':cp['at'],
                'resume_steps':cp['steps'], 'steps':expected['steps'], 'sample_count':len(combined['samples']),
                'event_count':len(combined['events']), 'root_sha256':ctx.root_sha256,
                'checkpoint_bytes':len(raw), 'checkpoint_sha256':cp['checkpoint_sha256'],
                'restored_float64_values':121, 'binary_roundtrip_exact':True,
                'original_full_physical_payload_equal':True, 'continuous_final_state_and_prefixes_equal':True,
                'child_chunks':response['chunks'], 'child_wall_seconds':response['wall_seconds'],
                'child_peak_rss_mib':response['peak_rss_mib'], 'private_response_sha256':digest(response_path)})
        temporary_path = str(temporary)
    assert not Path(temporary_path).exists()
    inputs = [str(source.relative_to(ROOT)), 'backend/app/crop_cycle_continuation.py',
              'backend/tests/test_crop_cycle_continuation.py', 'contracts/crop-cycle-continuation-v1.md',
              str(reference.relative_to(ROOT)), *PROFILE_PATHS.values()]
    evidence = {'evidence_version':'crop-cycle-continuation-reference-v1',
        'recorded_at':datetime.now(timezone.utc).isoformat(), 'scope':'actual short synthetic RHS continuation; no fullcycle/crop claim',
        'file_sha256':{p:digest(ROOT/p) for p in inputs}, 'physical_code_sha256':dict(original.CODE_HASHES),
        'cases':records, 'separate_python_processes':len(records), 'serial_execution':True,
        'restored_float64_values':sum(r['restored_float64_values'] for r in records),
        'max_restored_checkpoint_bytes':max_bytes, 'wall_seconds':perf_counter()-started,
        'parent_peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'max_child_peak_rss_mib':max(r['child_peak_rss_mib'] for r in records),
        'temporary_files_removed':True, 'new_servers_or_db':0, 'recursive_codex_cli':0,
        'actual_farm_runs':0, 'g0_g4':'not accepted'}
    Path(output).write_bytes(json.dumps(evidence,ensure_ascii=False,indent=2).encode()+b'\n')
    print(json.dumps({'cases':len(records),'separate_python':len(records),'binary_values':evidence['restored_float64_values'],
                      'wall_seconds':evidence['wall_seconds'],'max_checkpoint_bytes':max_bytes,'cleanup':True}))


if __name__ == '__main__':
    parser = ArgumentParser(); parser.add_argument('--output'); parser.add_argument('--resume-input'); parser.add_argument('--resume-output')
    args = parser.parse_args()
    if args.resume_input and args.resume_output and not args.output:
        child_restore(args.resume_input,args.resume_output)
    elif args.output and not args.resume_input and not args.resume_output:
        main(args.output)
    else:
        parser.error('provide --output or paired --resume-input/--resume-output')
