"""Execution-contract evidence; no new model continuation or farm Run acceptance."""
from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from hashlib import sha256
import itertools
import json
from math import isfinite
from pathlib import Path
import resource
import struct
import sys
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app import crop_plant_startup_integration as model
from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters

VERSION='crop-cycle-execution-reference-v1'

def stamp(at):return at.isoformat().replace('+00:00','Z')
def instant(value):return datetime.fromisoformat(value.replace('Z','+00:00'))
def hash_file(path):return sha256(Path(path).read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def independent_grid(program):
    # Reconstruct by full steps plus one remainder, without the product while/min loop.
    points=sorted({instant(t) for t in program['output_times']} |
        {instant(s['end']) for s in program['segments']} | {instant(e['at']) for e in program['events']})
    h=program['solver']['max_step_seconds'];trace=[]
    for begin,end in zip(points,points[1:]):
        seconds=int((end-begin).total_seconds());whole,remainder=divmod(seconds,h)
        trace.extend((stamp(begin+timedelta(seconds=i*h)),h) for i in range(1,whole+1))
        if remainder:trace.append((stamp(end),remainder))
    return trace,points

def rk4_linear(lengths):
    # Scalar y'=y demonstration only; this is not an agricultural model/coefficient.
    y=1.0
    for h in lengths:
        k1=y;k2=y+h*k1/2;k3=y+h*k2/2;k4=y+h*k3
        y+=h*(k1+2*k2+2*k3+k4)/6
    return y

def scalar_trace(boundaries,h):
    result=[]
    for a,b in zip(boundaries,boundaries[1:]):
        q,r=divmod(b-a,h);result.extend([h]*q)
        if r:result.append(r)
    return result

def clock_counterexample():
    # Synthetic clock only: show why rounded prefix is not exact Fraction lineage.
    for initial,temp,a,b in itertools.product([.1,.3,1.], [.1,.2,20.17,21.23], [1,7,60,300], [1,7,60,300]):
        seed=Fraction.from_float(initial);slope=Fraction.from_float(temp)/86400
        prefix=seed+slope*a
        original=float(seed+slope*(a+b));rounded_restart=float(Fraction.from_float(float(prefix))+slope*b)
        if original!=rounded_restart:
            encoded=json.loads(canonical({'numerator':str(prefix.numerator),'denominator':str(prefix.denominator)}))
            restored=Fraction(int(encoded['numerator']),int(encoded['denominator']))
            assert restored==prefix and float(restored+slope*b)==original
            return {'scope':'synthetic_exact_clock_not_crop_parameters','initial':initial,'temperature':temp,
                'first_seconds':a,'remaining_seconds':b,'original_float_hex':original.hex(),
                'rounded_restart_float_hex':rounded_restart.hex(),'exact_prefix_recovery_equal':True,
                'prefix_numerator':str(prefix.numerator),'prefix_denominator':str(prefix.denominator)}
    raise AssertionError('no synthetic clock counterexample found')

def main(output):
    t0=perf_counter();reference=ROOT/'fixtures/crop-plant-startup-integration-reference-v1.json'
    cases=json.loads(reference.read_bytes())['cases']
    profiles={
        'growth_profile':ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()),
        'cohort_profile':ReferenceFruitCohortParameters((ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
        'transport_profile':ReferenceFruitTransportParameters((ROOT/'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes())}
    records=[];vectors=0;values_checked=0;partition_trials=0
    for case in cases:
        program=deepcopy(case['program']);before=canonical(program);trace=[];event_guards=[]
        original_advance=model._advance;original_guard=model._guard
        def observe_advance(y,rates,h,at):
            value=original_advance(y,rates,h,at);trace.append((stamp(at),h));return value
        def observe_guard(y,at,phase):
            value=original_guard(y,at,phase)
            if phase=='boundary-after-event':event_guards.append(stamp(at))
            return value
        model._advance=observe_advance;model._guard=observe_guard
        try:result=model.integrate_plant_startup(**program,**profiles)
        finally:model._advance=original_advance;model._guard=original_guard
        expected,points=independent_grid(program)
        assert result['status']=='completed' and trace==expected
        assert len(trace)==result['steps']==result['planned_steps'] and canonical(program)==before
        assert event_guards==[e['at'] for e in program['events']]
        assert [row['at'] for row in result['samples']]==program['output_times']
        # Partition the already fixed sequence. This proves grid grouping only, not driver restart.
        for quota in [1,2,7,64,10000]:
            resumed=[step for i in range(0,len(expected),quota) for step in expected[i:i+quota]]
            assert resumed==trace;partition_trials+=1
        for row in result['samples']:
            vector=[row['state'][k]['value'] for k in model.PLANT]
            vector += [q['value'] for key in model.ARRAY_UNITS for q in row['state'][key]]
            vector += [row['cumulative'][k]['value'] for k in model.FLUX]
            assert len(vector)==121 and all(type(v) is float and isfinite(v) for v in vector)
            restored=json.loads(canonical(vector))
            assert [struct.pack('!d',v) for v in restored]==[struct.pack('!d',v) for v in vector]
            vectors+=1;values_checked+=len(vector)
        records.append({'case':case['case_id'],'steps':len(trace),'trace':trace,'original_boundaries':[stamp(p) for p in points],
            'events_at':event_guards,'samples':len(result['samples']),'actual_result_sha256':result['result_sha256'],
            'trace_sha256':sha256(canonical(trace)).hexdigest(),'program_sha256':sha256(before).hexdigest()})
    base=scalar_trace([0,10,20],7);inserted=scalar_trace([0,5,10,20],7)
    exact_grouped=scalar_trace([0,10],7)+scalar_trace([10,20],7)
    assert base==exact_grouped and rk4_linear(base)==rk4_linear(exact_grouped)
    assert base!=inserted and rk4_linear(base)!=rk4_linear(inserted)
    scalar={'scope':'scalar_y_prime_y_only_not_crop_continuation','original_steps':base,'added_chunk_boundary_steps':inserted,
        'original_final_hex':rk4_linear(base).hex(),'added_boundary_final_hex':rk4_linear(inserted).hex(),
        'grouping_existing_boundary_preserves_float':True}
    clock=clock_counterexample()
    paths=[Path(__file__).relative_to(ROOT).as_posix(),'backend/app/crop_plant_startup_integration.py',
        'backend/app/crop_plant_cohort_integration.py','fixtures/crop-plant-startup-integration-reference-v1.json',
        'fixtures/crop-growth-reference-parameters-v1.json','fixtures/crop-fruit-cohort-reference-parameters-v1.json',
        'fixtures/crop-fruit-transport-reference-parameters-v1.json','contracts/crop-cycle-execution-v1.md']
    data={'evidence_version':VERSION,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'scope':'execution-contract source grid and representation evidence only; no new model restart acceptance',
        'file_sha256':{p:hash_file(ROOT/p) for p in paths},'actual_original_solver_cases':records,
        'partition_grid_trials':partition_trials,'serialized_vectors':vectors,'serialized_float64_values':values_checked,
        'all_float64_roundtrips_exact':True,'additional_boundary_counterexample':scalar,'fraction_clock_counterexample':clock,
        'wall_seconds':perf_counter()-t0,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'model_continuation_tested':False,'crop_growth_accuracy_validated':False,'actual_crop_runs':0,
        'independent_domestic_datasets':0,'g0_g4':'not accepted','new_db_or_server_started':0}
    output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:data[k] for k in ['evidence_version','partition_grid_trials','serialized_vectors','serialized_float64_values','wall_seconds','peak_rss_mib','model_continuation_tested']}))

if __name__=='__main__':
    parser=ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    main(args.output)
