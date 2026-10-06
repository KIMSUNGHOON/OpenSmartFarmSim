"""Execute owned synthetic inputs through the original retained artifact writer."""
from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import sys
from time import perf_counter,process_time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from app import crop_cycle_artifact as artifact

VERSION='crop-cycle-full-rhs-experiment-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
PROFILE_RECEIPT='research/artifacts/crop-cycle-burden-profile-reference-20261006.json'
PROFILE_RECEIPT_SHA256='f2688eb02d1b79440bec37c7f9c19093cdeeec224dfe4f12d39661ef6d54b120'
MAX_WALL_SECONDS=21600
MAX_PROCESS_RESIDENT_BYTES=256*1024*1024
BUDGET={'max_steps':10000,'max_transitions':128}


def utc_now():return datetime.now(timezone.utc)


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def dependencies():
    raw=(ROOT/PROFILE_RECEIPT).read_bytes()
    if sha256(raw).hexdigest()!=PROFILE_RECEIPT_SHA256:raise ValueError('profile receipt changed')
    receipt=json.loads(raw)
    pins={**receipt['source_sha256'],**receipt['frozen_current49_sha256']}
    if any(sha256((ROOT/path).read_bytes()).hexdigest()!=digest for path,digest in pins.items()):
        raise ValueError('original execution dependencies changed')
    return pins


def profile():return load_module('original_cycle_cost_profile',ROOT/'research/crop-cycle-burden-profile.py')


def immutable(path,value):
    raw=inputs._canonical(value)
    with Path(path).open('xb') as handle:
        handle.write(raw);handle.flush();os.fchmod(handle.fileno(),0o400);os.fsync(handle.fileno())
    return sha256(raw).hexdigest()


def prepare_experiment(path,*,program,intervals,interval_seconds,profiles,notice_raw,
                       wall_seconds=MAX_WALL_SECONDS,budget=None):
    if type(wall_seconds) is not int or not 1<=wall_seconds<=MAX_WALL_SECONDS:
        raise ValueError('bounded integer global wall budget required')
    budget=dict(BUDGET) if budget is None else deepcopy(budget)
    artifact._budget(budget)
    if sha256(Path(__file__).read_bytes()).hexdigest()!=CODE_SHA256:raise ValueError('runner source changed')
    pins=dependencies();observer=profile();observer._budgets([budget],transitions=128)
    if type(notice_raw) is not bytes or sha256(notice_raw).hexdigest()!=artifact.samples.NOTICE_SHA256:
        raise ValueError('original notice required')
    path=Path(path);started=utc_now();tick=perf_counter();path.mkdir(mode=0o700)
    try:
        shape=observer.profile_shape(path/'inputs',program,intervals=intervals,
            interval_seconds=interval_seconds,profiles=profiles)
        with inputs.open_input_packet(path/'inputs',shape['input_root_sha256'],**profiles) as reader:
            context=engine.prepare_context(reader,**profiles)
            with artifact.create_writer(path/'artifact',context,notice_raw=notice_raw) as writer:
                head=writer.head_sha256
        for file in (path/'inputs').iterdir():file.chmod(0o400)
        spec={'version':VERSION,'scope':'own_synthetic_numeric_experiment_only','gates':'not_assessed',
            'driver_sha256':CODE_SHA256,'dependency_sha256':pins,'python_version':platform.python_version(),
            'notice_sha256':sha256(notice_raw).hexdigest(),'profile_sha256':inputs._profiles(**profiles),
            'input_root_sha256':shape['input_root_sha256'],'source_program_sha256':shape['source_program_sha256'],
            'plan':shape['plan'],'intervals':intervals,'interval_seconds':interval_seconds,
            'initial_head_sha256':head,'artifact_budget':budget,'artifact_limits':dict(artifact.LIMITS),
            'started_at_utc':started.isoformat(),'deadline_at_utc':(started+timedelta(seconds=wall_seconds)).isoformat(),
            'global_wall_seconds':wall_seconds,'process_resident_limit_bytes':MAX_PROCESS_RESIDENT_BYTES,
            'preparation_wall_seconds':perf_counter()-tick}
        digest=immutable(path/'experiment.json',spec)
        return {'spec_sha256':digest,'spec':spec,'input_root_sha256':shape['input_root_sha256']}
    except BaseException:
        shutil.rmtree(path)
        raise


def read_spec(path,expected,profiles,notice):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:raw=inputs._read(fd,'experiment.json',1024*1024)
    finally:os.close(fd)
    if sha256(raw).hexdigest()!=expected:raise ValueError('original experiment manifest required')
    spec=inputs._json(raw)
    if inputs._canonical(spec)!=raw:raise ValueError('canonical experiment manifest required')
    keys={'version','scope','gates','driver_sha256','dependency_sha256','python_version','notice_sha256',
        'profile_sha256','input_root_sha256','source_program_sha256','plan','intervals','interval_seconds',
        'initial_head_sha256','artifact_budget','artifact_limits','started_at_utc','deadline_at_utc',
        'global_wall_seconds','process_resident_limit_bytes','preparation_wall_seconds'}
    if type(spec) is not dict or set(spec)!=keys:raise ValueError('closed experiment manifest required')
    begin=datetime.fromisoformat(spec['started_at_utc']);deadline=datetime.fromisoformat(spec['deadline_at_utc'])
    if (type(spec['global_wall_seconds']) is not int or not 1<=spec['global_wall_seconds']<=MAX_WALL_SECONDS
        or begin.utcoffset()!=timedelta(0) or deadline.utcoffset()!=timedelta(0)
        or deadline-begin!=timedelta(seconds=spec['global_wall_seconds'])):
        raise ValueError('original bounded execution deadline required')
    if (spec['version']!=VERSION or spec['scope']!='own_synthetic_numeric_experiment_only'
        or spec['gates']!='not_assessed' or spec['driver_sha256']!=CODE_SHA256
        or sha256(Path(__file__).read_bytes()).hexdigest()!=CODE_SHA256
        or spec['dependency_sha256']!=dependencies() or spec['python_version']!=platform.python_version()
        or spec['profile_sha256']!=inputs._profiles(**profiles)
        or spec['notice_sha256']!=sha256(notice).hexdigest()
        or spec['artifact_limits']!=artifact.LIMITS or spec['process_resident_limit_bytes']!=MAX_PROCESS_RESIDENT_BYTES):
        raise ValueError('original experiment code/profile/notice/budgets changed')
    artifact._budget(spec['artifact_budget'])
    return spec


def current_head(path):
    fd=os.open(Path(path)/'artifact',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:raw=inputs._read(fd,'HEAD',8192)
    finally:os.close(fd)
    return sha256(raw).hexdigest()


def peak_bytes():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024


def resident_bytes():
    return int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')


def execute(path,*,expected_spec_sha256,profiles,notice_raw,max_chunks=None,progress=None):
    if max_chunks is not None and (type(max_chunks) is not int or not 1<=max_chunks<=artifact.LIMITS['commits']):
        raise ValueError('bounded explicit operator chunk pause required')
    path=Path(path);spec=read_spec(path,expected_spec_sha256,profiles,notice_raw)
    started=perf_counter();cpu=process_time();descriptors=len(os.listdir('/proc/self/fd'))
    costs=profile().Costs();chunks=0;reason=None;receipt=None;max_resident=0;storage_rejection=None
    with costs.observe():
        with inputs.open_input_packet(path/'inputs',spec['input_root_sha256'],**profiles) as source:
            if source.plan!=spec['plan']:raise ValueError('original input plan changed')
            context=engine.prepare_context(source,**profiles)
            with artifact.open_writer(path/'artifact',current_head(path),context,notice_raw=notice_raw) as writer:
                restored=deepcopy(writer._checkpoint)
                commits_at_entry=len(writer._hashes)
                while writer._summary is None or writer._summary['status']=='yielded':
                    if utc_now()>=datetime.fromisoformat(spec['deadline_at_utc']):reason='GLOBAL_WALL_BUDGET';break
                    max_resident=max(max_resident,resident_bytes())
                    if max_resident>spec['process_resident_limit_bytes']:reason='PROCESS_RESIDENT_BUDGET';break
                    if max_chunks is not None and chunks>=max_chunks:reason='OPERATOR_CHUNK_PAUSE';break
                    size,files=writer._usage()
                    try:writer.advance(spec['artifact_budget'])
                    except artifact.CycleArtifactRejected as exc:
                        if not str(exc).startswith('RESOURCE_HOLD:'):raise
                        storage_rejection=str(exc);reason='ORIGINAL_STORAGE_BUDGET';break
                    chunks+=1
                    if progress is not None:progress({'chunks_this_call':chunks,'steps':writer._summary['steps'],
                        'at':writer._checkpoint['at'] if writer._checkpoint else writer._summary['hold']['at'],
                        'storage_bytes_before_chunk':size,'files_before_chunk':files,
                        'wall_seconds':perf_counter()-started,'max_observed_active_rss_bytes':max_resident})
                if storage_rejection is None:
                    if reason is None:
                        try:receipt=writer.finalize()
                        except artifact.CycleArtifactRejected as exc:
                            if not str(exc).startswith('RESOURCE_HOLD:'):raise
                            storage_rejection=str(exc);reason='ORIGINAL_STORAGE_BUDGET'
                    if storage_rejection is None:
                        checkpoint=deepcopy(writer._checkpoint);summary=deepcopy(writer._summary)
                        head=writer.head_sha256;size,files=writer._usage();commits=len(writer._hashes)
            if storage_rejection is not None:
                with artifact.open_writer(path/'artifact',current_head(path),context,notice_raw=notice_raw) as recovered:
                    checkpoint=deepcopy(recovered._checkpoint);summary=deepcopy(recovered._summary)
                    head=recovered.head_sha256;size,files=recovered._usage();commits=len(recovered._hashes)
            rhs_before=costs.values.get('rhs',{}).get('calls',0)
            hashes={};counts={};max_page_bytes=0;terminal=None
            if receipt is not None:
                with artifact.open_artifact(path/'artifact',receipt['artifact_sha256'],context,notice_raw=notice_raw) as reader:
                    terminal=reader.summary
                    for kind,limit in (('samples',64),('events',8)):
                        digest=sha256();offset=count=0
                        while True:
                            page=reader.page(kind,offset,limit);max_page_bytes=max(max_page_bytes,len(inputs._canonical(page)))
                            for row in page['records']:digest.update(inputs._canonical(row)+b'\n')
                            count+=len(page['records'])
                            if page['next']==page['total']:break
                            if page['next']<=offset:raise AssertionError('original page did not advance')
                            offset=page['next']
                        hashes[kind]=digest.hexdigest();counts[kind]=count
                if summary['status']=='completed' and (summary['steps']!=source.plan['planned_steps']
                    or counts!={'samples':source.plan['counts']['outputs'],'events':source.plan['counts']['events']}):
                    raise AssertionError('completed source-shape execution incomplete')
            read_rhs=costs.values.get('rhs',{}).get('calls',0)-rhs_before
    if read_rhs:raise AssertionError('original artifact read executed RHS')
    result={'version':VERSION,'scope':spec['scope'],'gates':'not_assessed',
        'spec_sha256':expected_spec_sha256,'input_root_sha256':spec['input_root_sha256'],'driver_sha256':CODE_SHA256,
        'recorded_at_utc':utc_now().isoformat(),'effective_nice':os.getpriority(os.PRIO_PROCESS,0),
        'status':'incomplete' if reason else summary['status'],'reason':reason,'storage_rejection':storage_rejection,
        'artifact_status':'yielded' if summary is None else summary['status'],
        'artifact_sha256':None if receipt is None else receipt['artifact_sha256'],'head_sha256':head,
        'steps':0 if summary is None else summary['steps'],'planned_steps':spec['plan']['planned_steps'],
        'restored_checkpoint':restored,'committed_checkpoint':checkpoint,'terminal':terminal,
        'commit_count':commits,'successful_advance_returns':chunks,'commits_persisted_this_call':commits-commits_at_entry,
        'chunks_this_call':chunks,'storage_bytes':size,'file_count':files,
        'actual_rhs_calls':costs.values.get('rhs',{}).get('calls',0),'read_rhs_calls':read_rhs,
        'samples_sha256':hashes.get('samples'),'events_sha256':hashes.get('events'),
        'sample_count':counts.get('samples'),'event_count':counts.get('events'),'max_page_bytes':max_page_bytes,
        'full166day_math_completed':reason is None and summary['status']=='completed'
            and spec['intervals']==47808 and spec['interval_seconds']==300
            and spec['input_root_sha256']==json.loads((ROOT/PROFILE_RECEIPT).read_bytes())['measurements']['own166day_shape_plan']['input_root_sha256'],
        'global_deadline_at_utc':spec['deadline_at_utc'],'wall_seconds':perf_counter()-started,
        'cpu_seconds':process_time()-cpu,'process_peak_rss_bytes':peak_bytes(),'max_observed_active_rss_bytes':max_resident,
        'descriptors_before':descriptors,'descriptors_after':len(os.listdir('/proc/self/fd'))}
    return result


def main():
    parser=ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--new-run',type=Path);mode.add_argument('--resume-run',type=Path)
    parser.add_argument('--spec-sha256');parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--intervals',type=int,default=47808)
    parser.add_argument('--max-chunks',type=int)
    args=parser.parse_args()
    if args.output.exists():parser.error('a new own observation file is required')
    if args.resume_run is not None and args.spec_sha256 is None:parser.error('resume requires original spec SHA')
    if args.new_run is not None and args.spec_sha256 is not None:parser.error('new run generates its original spec SHA')
    reference=load_module('owned_stream_reference',ROOT/'research/crop-cycle-stream-execution-reference.py')
    profiles=reference.profiles();notice=(ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()
    if args.new_run is not None:
        prepared=prepare_experiment(args.new_run,program=reference.long_program(),intervals=args.intervals,
            interval_seconds=300,profiles=profiles,notice_raw=notice)
        path=args.new_run;expected=prepared['spec_sha256']
    else:path=args.resume_run;expected=args.spec_sha256
    print(json.dumps({'phase':'execute_original_retained_writer','spec_sha256':expected,
        'driver_sha256':CODE_SHA256,'gates':'not_assessed'}),flush=True)
    def progress(value):
        if value['chunks_this_call']==1 or value['chunks_this_call']%32==0:
            print(json.dumps({'phase':'actual_RHS',**value}),flush=True)
    result=execute(path,expected_spec_sha256=expected,profiles=profiles,notice_raw=notice,
        max_chunks=args.max_chunks,progress=progress)
    immutable(args.output,result)
    print(json.dumps({k:result[k] for k in ('status','reason','steps','planned_steps','actual_rhs_calls',
        'sample_count','event_count','wall_seconds','full166day_math_completed')}),flush=True)


if __name__=='__main__':main()
