"""Attribute original input validation costs over an unchanged owned packet."""
from argparse import ArgumentParser
from contextlib import contextmanager
from datetime import datetime,timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import resource
from time import perf_counter,process_time

ROOT=Path(__file__).resolve().parents[1]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


@contextmanager
def rhs_guard(costs,engine):
    owner=engine.short._Evaluator;original=owner.rhs
    owner.rhs=costs.wrap(original,'rhs')
    try:yield
    finally:owner.rhs=original


def measure(driver,path,spec,profiles,*,instrumented):
    inputs=driver.inputs;engine=driver.engine;costs=driver.profile().Costs()
    phase=None;io={};original_read=inputs._read
    def read(*args,**kwargs):
        raw=original_read(*args,**kwargs)
        value=io.setdefault(phase,{'root_reads':0,'blob_reads':0,'read_bytes':0,'max_read_bytes':0})
        value['root_reads' if args[1]=='root.json' else 'blob_reads']+=1
        value['read_bytes']+=len(raw);value['max_read_bytes']=max(value['max_read_bytes'],len(raw))
        return raw
    targets=[(inputs,name,'input.'+name) for name in ('_read','_json','_normalise','_canonical','_chain')]
    targets.extend((inputs.InputPacket,name,'input.'+name) for name in ('_load','_next_boundary','_validate_cursor'))
    targets.append((inputs.physical,'_utc','time.UTC.parse'))
    tick=perf_counter();cpu=process_time();descriptors=len(os.listdir('/proc/self/fd'))
    if instrumented:inputs._read=read
    try:
        observer=costs.observe(extra=targets) if instrumented else rhs_guard(costs,engine)
        with observer:
            phase='open_input'
            with costs.measure('phase.open_input'):
                reader=inputs.open_input_packet(path/'inputs',spec['input_root_sha256'],**profiles)
            with reader:
                assert reader.plan==spec['plan']
                phase='prepare_context'
                with costs.measure('phase.prepare_context'):
                    context=engine.prepare_context(reader,**profiles)
                semantic={'manifest':context.manifest,'initial':json.loads(context._initial),
                    'initial_clock':json.loads(context._initial_clock),'seed':list(context.seed),
                    'start_at':context.start_at,'planned_steps':context.planned_steps,
                    'boundary_count':context.boundary_count,'segment_count':context.segment_count,
                    'context_sha256':context.root_sha256,'plan':reader.plan}
                assert context.manifest['input_root_sha256']==spec['input_root_sha256']
                assert context.planned_steps==spec['plan']['planned_steps']
        assert costs.values.get('rhs',{}).get('calls',0)==0
    finally:inputs._read=original_read
    result={'instrumented':instrumented,'wall_seconds':perf_counter()-tick,'cpu_seconds':process_time()-cpu,
        'semantic_sha256':sha256(inputs._canonical(semantic)).hexdigest(),'semantic':semantic,
        'costs':costs.values,'observed_read_io':io,'observed_rhs_calls':costs.values.get('rhs',{}).get('calls',0),
        'descriptors_before':descriptors,'descriptors_after':len(os.listdir('/proc/self/fd'))}
    assert result['descriptors_before']==result['descriptors_after']
    print(json.dumps({'phase':'input_cost_observation','instrumented':instrumented,
        'wall_seconds':result['wall_seconds'],'rhs_calls':result['observed_rhs_calls']}),flush=True)
    return result


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--spec-sha256',required=True)
    parser.add_argument('--cli-context',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('new own observation output required')
    cli=json.loads(args.cli_context.read_bytes())
    assert cli['model']=='gpt-6.1-sol' and cli['effort']=='xhigh' and cli['recursive_cli_invocations']==0
    driver=module('owned_full_rhs_driver',ROOT/'research/crop-cycle-full-rhs-reference.py')
    reference_path=ROOT/'research/crop-cycle-stream-execution-reference.py'
    reference=module('owned_stream_reference',reference_path);profiles=reference.profiles()
    spec=driver.read_spec(args.run,args.spec_sha256,profiles,(ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes())
    pins={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),reference_path)}
    runs=[measure(driver,args.run,spec,profiles,instrumented=v) for v in (False,True)]
    assert runs[0]['semantic_sha256']==runs[1]['semantic_sha256'] and runs[0]['semantic']==runs[1]['semantic']
    assert pins=={p:sha256((ROOT/p).read_bytes()).hexdigest() for p in pins}
    driver.read_spec(args.run,args.spec_sha256,profiles,(ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes())
    result={'evidence_version':'crop-cycle-input-validation-cost-v1','recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'original_full_input_preflight_and_context_cost_only','gates':'not_assessed','actual_cli_context':cli,
        'source_sha256':pins,'frozen_dependency_sha256':spec['dependency_sha256'],
        'full_rhs_driver_sha256':spec['driver_sha256'],'spec_sha256':args.spec_sha256,
        'input_root_sha256':spec['input_root_sha256'],'runs':runs,'same_original_context_and_plan':True,
        'effective_nice':os.getpriority(os.PRIO_PROCESS,0),'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        'measurement_scope':'inclusive costs overlap; exclusive excludes observed direct children only; wrappers add overhead',
        'baseline_scope':'original input/context with RHS guard only; no detailed input wrappers',
        'cache_condition':'not controlled; previous preflight and byte-hash observation; baseline precedes instrumentation',
        'concurrency':'existing nice10 full166 integration remains live; this short read-only process nice15',
        'measurement_excludes':['farm/current rights/DB','artifact validation','public API/HTTPS/3D'],
        'input_or_artifact_modified':False,'whole_validation_or_API_accepted':False}
    driver.immutable(args.output,result)
    print(json.dumps({'phase':'input_cost_observation_complete','same_original_context_and_plan':True}),flush=True)


if __name__=='__main__':main()
