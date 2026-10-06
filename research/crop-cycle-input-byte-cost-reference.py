"""Measure owned input byte hashes; this does not implement or replace QC."""
from argparse import ArgumentParser
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


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--spec-sha256',required=True)
    parser.add_argument('--cli-context',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('new own observation file required')
    cli=json.loads(args.cli_context.read_bytes())
    assert cli['model']=='gpt-6.1-sol' and cli['effort']=='xhigh' and cli['recursive_cli_invocations']==0
    driver=module('owned_full_rhs_driver',ROOT/'research/crop-cycle-full-rhs-reference.py')
    reference=module('owned_stream_reference',ROOT/'research/crop-cycle-stream-execution-reference.py')
    profiles=reference.profiles();notice=(ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()
    spec=driver.read_spec(args.run,args.spec_sha256,profiles,notice)
    inputs=driver.inputs;costs=driver.profile().Costs()
    before=len(os.listdir('/proc/self/fd'));tick=perf_counter();cpu=process_time()
    with costs.observe():
        fd=os.open(args.run/'inputs',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            raw=inputs._read(fd,'root.json',inputs.MAX_ROOT_BYTES)
            assert sha256(raw).hexdigest()==spec['input_root_sha256']
            root=inputs._json(raw)
            assert inputs._canonical(root)==raw
            names={block['sha256'] for stream in root['streams'].values() for block in stream['blocks']}
            assert set(os.listdir(fd))=={'root.json',*(digest+'.json' for digest in names)}
            total=len(raw);maximum=len(raw);records=[]
            for expected in sorted(names):
                raw=inputs._read(fd,expected+'.json',inputs.MAX_BLOCK_BYTES)
                actual=sha256(raw).hexdigest();assert actual==expected
                total+=len(raw);maximum=max(maximum,len(raw))
                records.append({'sha256':actual,'bytes':len(raw)})
            assert total==spec['plan']['packet_referenced_bytes']
        finally:os.close(fd)
    wall=perf_counter()-tick;cpu_seconds=process_time()-cpu
    result={'evidence_version':'crop-cycle-input-byte-cost-v1','recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'own_synthetic_raw_byte_hash_cost_only','gates':'not_assessed','actual_cli_context':cli,
        'source_sha256':{str(Path(__file__).relative_to(ROOT)):sha256(Path(__file__).read_bytes()).hexdigest()},
        'frozen_dependency_sha256':spec['dependency_sha256'],
        'full_rhs_driver_sha256':spec['driver_sha256'],'spec_sha256':args.spec_sha256,
        'input_root_sha256':spec['input_root_sha256'],'all_referenced_blob_bytes_match':True,
        'canonical_root_checked':True,'exact_file_inventory_checked':True,'blocks':len(names),
        'total_input_bytes':total,'max_single_raw_read_bytes':maximum,
        'block_inventory_sha256':sha256(inputs._canonical(records)).hexdigest(),
        'wall_seconds':wall,'cpu_seconds':cpu_seconds,'effective_nice':os.getpriority(os.PRIO_PROCESS,0),
        'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        'descriptors_before':before,'descriptors_after':len(os.listdir('/proc/self/fd')),
        'observed_rhs_calls':costs.values.get('rhs',{}).get('calls',0),
        'cache_condition':'not_controlled; this packet previously passed full preflight in the live experiment',
        'measurement_excludes':['block JSON/schema/unit/clock/grid QC','profile/code revalidation time',
            'farm/current rights/DB','artifact math validation','public API/HTTPS/3D'],
        'input_or_artifact_modified':False,'whole_validation_or_API_accepted':False}
    assert result['observed_rhs_calls']==0 and result['descriptors_before']==result['descriptors_after']
    driver.immutable(args.output,result)
    print(json.dumps({k:result[k] for k in ('blocks','total_input_bytes','wall_seconds','cpu_seconds',
        'observed_rhs_calls','descriptors_before','descriptors_after','whole_validation_or_API_accepted')}),flush=True)


if __name__=='__main__':main()
