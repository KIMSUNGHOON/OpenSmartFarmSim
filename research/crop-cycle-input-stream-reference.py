"""Large synthetic input/clock/grid reader evidence; no RHS or crop Run."""
from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from fractions import Fraction
from hashlib import sha256
import heapq
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app import crop_cycle_input_stream as stream
from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters

COUNT=48000
SECONDS=300
TEMPERATURES=(.1,.3,20.1)
PROFILE_FILES={'growth_profile':'fixtures/crop-growth-reference-parameters-v1.json',
 'cohort_profile':'fixtures/crop-fruit-cohort-reference-parameters-v1.json',
 'transport_profile':'fixtures/crop-fruit-transport-reference-parameters-v1.json'}


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def file_hash(path):return sha256(Path(path).read_bytes()).hexdigest()
def stamp(at):return at.isoformat().replace('+00:00','Z')
def chain(previous,row):return sha256(bytes.fromhex(previous)+canonical(row)).hexdigest()


def profiles():
    return {k:cls((ROOT/PROFILE_FILES[k]).read_bytes()) for k,cls in (
        ('growth_profile',ReferenceParameters),('cohort_profile',ReferenceFruitCohortParameters),
        ('transport_profile',ReferenceFruitTransportParameters))}


def normalize_quantities(value):
    if type(value) is dict:
        if set(value)=={'value','unit'}:return {'value':float(value['value']),'unit':value['unit']}
        return {k:normalize_quantities(v) for k,v in value.items()}
    if type(value) is list:return [normalize_quantities(v) for v in value]
    return value


def child_restore(request_path,response_path):
    started=perf_counter();request=json.loads(Path(request_path).read_bytes());before=len(os.listdir('/proc/self/fd'))
    with stream.open_input_packet(request['directory'],request['root_sha256'],**profiles()) as reader:
        cursor=reader.restore_cursor(canonical(request['cursor']));digest=request['prefix'];count=request['prefix_count'];first=None
        while True:
            page=reader.boundary_page(cursor,limit=128)
            for row in page['boundaries']:
                if first is None:first=row['at']
                digest=chain(digest,row);count+=1
            cursor=reader.restore_cursor(reader.cursor_bytes(page['cursor']))
            if page['complete']:break
        response={'boundary_chain_sha256':digest,'boundary_count':count,'first_resumed_at':first,
            'final_cursor':cursor,'wall_seconds':perf_counter()-started,
            'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    response['fd_count_preserved']=len(os.listdir('/proc/self/fd'))==before
    assert response['fd_count_preserved'];Path(response_path).write_bytes(canonical(response)+b'\n')


def main(output):
    started=perf_counter();cases=json.loads((ROOT/'fixtures/crop-plant-startup-integration-reference-v1.json').read_bytes())['cases']
    template=deepcopy(cases[1]['program']);begin=datetime.fromisoformat(template['segments'][0]['start'].replace('Z','+00:00'))
    base=template['segments'][0];params=profiles();event_seconds=(0,385,128*SECONDS+7,COUNT*SECONDS)
    events=[]
    for offset in event_seconds:
        event=deepcopy(cases[3]['program']['events'][0]);event['at']=stamp(begin+timedelta(seconds=offset));events.append(event)
    expected_events={e['at']:normalize_quantities(e) for e in events}
    def segments():
        for i in range(COUNT):
            segment=deepcopy(base);segment['start']=stamp(begin+timedelta(seconds=i*SECONDS))
            segment['end']=stamp(begin+timedelta(seconds=(i+1)*SECONDS))
            segment['forcing']['values']['canopy_temperature']['value']=TEMPERATURES[i%3]
            yield segment
    def times(interval):
        for offset in range(0,COUNT*SECONDS+1,interval):yield stamp(begin+timedelta(seconds=offset))
    before=len(os.listdir('/proc/self/fd'));observed={'max_block_records':0,'max_cached_records':0}
    load=stream.InputPacket._load
    def observe(self,kind,index):
        values=load(self,kind,index);observed['max_block_records']=max(observed['max_block_records'],len(values))
        observed['max_cached_records']=max(observed['max_cached_records'],sum(len(v[1]) for v in self._cache.values()))
        return values
    stream.InputPacket._load=observe
    try:
        with TemporaryDirectory(prefix='ossf-cycle-input-') as directory:
            temporary=Path(directory);packet=temporary/'packet';write_started=perf_counter()
            receipt=stream.write_input_packet(packet,initial_state=template['initial_state'],segments=segments(),events=iter(events),
                anchors=times(3000),outputs=times(9000),solver={**template['solver'],'max_step_seconds':10,'max_steps':2000000},
                program_id='own-synthetic-clock-grid-48000-v1',**params)
            write_seconds=perf_counter()-write_started
            with stream.open_input_packet(packet,receipt['root_sha256'],**params) as reader:
                manifest=reader.manifest;plan=reader.plan;clock_checks=[]
                for index in (0,127,128,129,255,256,2175,COUNT-1):
                    value=reader.segment(index);actual=value['clock']['prefix'];q,r=divmod(index,3)
                    total=Fraction.from_float(float(template['initial_state']['values']['temperature_sum']['value']))
                    total+=(sum(map(Fraction.from_float,TEMPERATURES))*q+sum(map(Fraction.from_float,TEMPERATURES[:r])))*Fraction(SECONDS,86400)
                    restored=Fraction(int(actual['numerator']),int(actual['denominator']))
                    assert restored==total and float(restored).hex()==float(total).hex()
                    assert value['segment']['start']==stamp(begin+timedelta(seconds=index*SECONDS))
                    assert value['segment']['forcing']['values']['canopy_temperature']['value'].hex()==TEMPERATURES[index%3].hex()
                    clock_checks.append({'segment_index':index,'temperature_sum_float_hex':float(total).hex(),'fraction_exact':True})
                cursor=None;prefix=sha256(b'').hexdigest();prefix_count=0
                for _ in range(17):
                    page=reader.boundary_page(cursor,limit=128)
                    for row in page['boundaries']:prefix=chain(prefix,row);prefix_count+=1
                    cursor=reader.restore_cursor(reader.cursor_bytes(page['cursor']))
                cursor_size=len(reader.cursor_bytes(cursor))
            request=temporary/'request.json';response=temporary/'response.json'
            request.write_bytes(canonical({'directory':str(packet),'root_sha256':receipt['root_sha256'],
                'cursor':cursor,'prefix':prefix,'prefix_count':prefix_count}))
            subprocess.run([sys.executable,str(Path(__file__).resolve()),'--resume-input',str(request),'--resume-output',str(response)],
                check=True,cwd=ROOT,capture_output=True,timeout=300)
            child=json.loads(response.read_bytes());expected_chain=sha256(b'').hexdigest();boundary_count=0;planned=0;previous=None;resume_at=None
            for offset in heapq.merge(range(0,COUNT*SECONDS+1,SECONDS),(385,128*SECONDS+7)):
                at=stamp(begin+timedelta(seconds=offset))
                row={'at':at,'forcing_end':offset>0 and offset%SECONDS==0,'anchor':offset%3000==0,
                     'event':expected_events.get(at),'output':offset%9000==0}
                expected_chain=chain(expected_chain,row)
                if previous is not None:
                    whole,remainder=divmod(offset-previous,10);planned+=whole+bool(remainder)
                if boundary_count==prefix_count:resume_at=at
                previous=offset;boundary_count+=1
            assert child['boundary_chain_sha256']==expected_chain and child['boundary_count']==boundary_count
            assert child['first_resumed_at']==resume_at and plan['planned_steps']==planned and plan['boundaries']==boundary_count
            assert child['final_cursor']['positions']==plan['counts']
            actual_bytes=sum(p.stat().st_size for p in packet.iterdir());assert actual_bytes==receipt['packet_bytes']==plan['packet_referenced_bytes']
            max_block_bytes=max(p.stat().st_size for p in packet.iterdir() if p.name!='root.json')
            packet_file_count=sum(1 for _ in packet.iterdir());temporary_path=str(temporary)
    finally:stream.InputPacket._load=load
    assert not Path(temporary_path).exists() and len(os.listdir('/proc/self/fd'))==before
    names=['backend/app/crop_cycle_input_stream.py','backend/tests/test_crop_cycle_input_stream.py',
        'contracts/crop-cycle-input-stream-v1.md','research/crop-cycle-input-stream-reference.py',
        'fixtures/crop-plant-startup-integration-reference-v1.json',*PROFILE_FILES.values()]
    evidence={'evidence_version':'crop-cycle-input-stream-reference-v1','recorded_at':datetime.now(timezone.utc).isoformat(),
        'scope':'large own synthetic input/clock/grid reader and separate Python cursor restore only; no RHS/crop Run',
        'file_sha256':{p:file_hash(ROOT/p) for p in names},'root_sha256':receipt['root_sha256'],
        'calculation_sha256':receipt['calculation_sha256'],'intervals':COUNT,'source_shape_points':COUNT+1,
        'interval_seconds':SECONDS,'period_seconds':COUNT*SECONDS,'plan':plan,'clock_checks':clock_checks,
        'independent_boundary_chain_equal':True,'independent_original_grid_steps_equal':True,'separate_python_processes':1,
        'prefix_boundaries':prefix_count,'cursor_bytes':cursor_size,'child':child,'observed_parent_windows':observed,
        'packet_bytes':actual_bytes,'packet_files':packet_file_count,'max_block_bytes':max_block_bytes,
        'writer_preflight_wall_seconds':write_seconds,'wall_seconds':perf_counter()-started,
        'parent_peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'fd_count_preserved':True,'temporary_directory_removed':True,'new_servers_or_db':0,
        'actual_rhs_executed':False,'actual_crop_runs':0,'g0_g4':'not accepted'}
    Path(output).write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:evidence[k] for k in ('intervals','packet_bytes','wall_seconds','parent_peak_rss_mib','actual_rhs_executed')}))


if __name__=='__main__':
    parser=ArgumentParser();parser.add_argument('--output');parser.add_argument('--resume-input');parser.add_argument('--resume-output');args=parser.parse_args()
    if args.output and not args.resume_input and not args.resume_output:main(args.output)
    elif args.resume_input and args.resume_output and not args.output:child_restore(args.resume_input,args.resume_output)
    else:parser.error('provide --output or paired --resume-input/--resume-output')
