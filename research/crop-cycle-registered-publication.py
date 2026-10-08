"""Declare a separate private DB key and publish only a completed owned calculation."""
import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import secrets

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('owned_publication_supervisor',ROOT/'research/crop-cycle-registered-supervisor.py')
supervisor=importlib.util.module_from_spec(spec);spec.loader.exec_module(supervisor)
runtime=supervisor.runtime
from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore

VERSION='owned-registered-terminal-publication-v1'
SCOPE='owned_synthetic_completed_calculation_publication_only'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
FIELDS={'version','scope','code_sha256','supervision_directory','supervision_sha256','DB_key_file',
        'DB_key_sha256','source_sha256','input_root_sha256','plan'}


def sources():
    reference=ROOT/'research/artifacts/crop-cycle-calculation-registered-supervisor-control-reference-20261008.json'
    pins=json.loads(reference.read_bytes())['source_sha256']
    if any(sha256((ROOT/name).read_bytes()).hexdigest()!=value for name,value in pins.items()):
        raise ValueError('accepted supervision sources changed')
    paths=(Path(__file__),ROOT/'contracts/crop-cycle-calculation-registered-terminal-publication-v1.md',reference)
    return {**pins,**{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in paths}}


def declare(directory,*,supervision_directory,supervision_sha256):
    parent,manifest=supervisor.verified(supervision_directory,supervision_sha256)
    server,raw=runtime.load_runtime(manifest['config'],manifest['config_sha256'])
    if any(p.is_dir() for p in Path(server.directory).iterdir()):raise ValueError('declaration required before first calculation')
    with server.input_resolver(manifest['input_root_sha256'],authority=server.binding.input_authority) as context:
        server.binding.prepare('tenant-1',raw,context)
        plan={'steps':context.planned_steps,'counts':{'samples':context.reader.plan['counts']['outputs'],
                                                   'events':context.reader.plan['counts']['events']}}
    directory=Path(directory).absolute();directory.mkdir(mode=0o700);supervisor.directory(directory)
    key=secrets.token_bytes(32)
    while key==server.integrity_key:key=secrets.token_bytes(32)
    key_path=directory/'DB-key.private';runtime.write_private(key_path,key)
    value={'version':VERSION,'scope':SCOPE,'code_sha256':CODE_SHA256,'supervision_directory':str(parent),
        'supervision_sha256':supervision_sha256,'DB_key_file':str(key_path),'DB_key_sha256':sha256(key).hexdigest(),
        'source_sha256':sources(),'input_root_sha256':manifest['input_root_sha256'],'plan':plan}
    path=directory/'publication.json';checksum=supervisor.immutable(path,value)
    return path,checksum


def validated(path,expected):
    try:
        raw,value=supervisor.read_json(path)
        if (sha256(raw).hexdigest()!=expected or type(value) is not dict or set(value)!=FIELDS
            or value['version']!=VERSION or value['scope']!=SCOPE or value['code_sha256']!=CODE_SHA256
            or sha256(Path(__file__).read_bytes()).hexdigest()!=CODE_SHA256 or value['source_sha256']!=sources()):
            raise ValueError()
        _,manifest=supervisor.verified(value['supervision_directory'],value['supervision_sha256'])
        if value['input_root_sha256']!=manifest['input_root_sha256']:raise ValueError()
        plan=value['plan']
        if (type(plan) is not dict or set(plan)!={'steps','counts'} or type(plan['steps']) is not int
            or not 1<=plan['steps']<=40000000 or type(plan['counts']) is not dict
            or set(plan['counts'])!={'samples','events'}
            or any(type(n) is not int or not 0<=n<=runtime.engine.inputs.MAX_RECORDS for n in plan['counts'].values())):
            raise ValueError()
        key=runtime.private_bytes(value['DB_key_file'])
        config=supervisor.configuration(manifest['config'],manifest['config_sha256'])
        if (len(key)!=32 or sha256(key).hexdigest()!=value['DB_key_sha256']
            or key==runtime.private_bytes(config['keys']['server'])):raise ValueError()
        return value,manifest,key
    except Exception:raise ValueError('owned publication declaration unavailable') from None


def assemble(value,manifest,key):
    server,raw=runtime.load_runtime(manifest['config'],manifest['config_sha256'])
    return value,manifest,server,raw,key


def load_declaration(path,expected):return assemble(*validated(path,expected))


def publish(path,expected,output):
    path=Path(path).absolute();output=runtime.operator_config._path(str(Path(output).absolute()))
    if output.parent!=path.parent or output.exists():raise ValueError('new private publication result required')
    descriptors=len(os.listdir('/proc/self/fd'))
    value,manifest,server,raw,key=load_declaration(path,expected)
    parent=Path(value['supervision_directory']);supervisor.history(parent,value['supervision_sha256'])
    attempts=sorted(parent.glob('attempt-*.receipt.json'))
    if not attempts:raise ValueError('actual completed calculation receipt required')
    _,receipt=supervisor.read_json(attempts[-1]);result=receipt.get('result') or {};progress=result.get('progress') or {}
    if (receipt['worker_returncode']!=0 or receipt['outcome']!='recorded' or progress.get('status')!='completed'
        or progress.get('steps')!=value['plan']['steps'] or progress.get('planned_steps')!=value['plan']['steps']
        or progress.get('counts')!=value['plan']['counts'] or result.get('config_sha256')!=manifest['config_sha256']
        or result.get('deadline_ns')!=manifest['deadline_ns']):raise ValueError('original complete plan required')
    rhs=runtime.engine.short._Evaluator.rhs
    def forbidden(*a,**k):raise AssertionError('publication ran RHS')
    runtime.engine.short._Evaluator.rhs=forbidden
    try:
        with server.binding.jobs.connect() as conn:
            assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
        store=CalculationCycleCropResultStore(server,integrity_key=key)
        if json.loads(server.inspect('tenant-1',raw))!=progress:raise ValueError('current completed calculation required')
        record=store.put('tenant-1',raw);farm=json.loads(raw)['farm']
        if store.get('tenant-1',record['result_id'],farm)!=record:raise ValueError('original published record required')
        current,original_manifest,current_key=validated(path,expected)
        if current!=value or original_manifest!=manifest or current_key!=key:raise ValueError('final original declaration required')
        assert server.input_resolver.last.reader.closed and not server.input_resolver.last._cache
        assert len(os.listdir('/proc/self/fd'))==descriptors
        observation={'version':VERSION,'scope':SCOPE,'gates':'not_assessed','worker':supervisor.identity(os.getpid()),
            'publication_sha256':expected,'supervision_sha256':value['supervision_sha256'],
            'config_sha256':manifest['config_sha256'],'deadline_ns':manifest['deadline_ns'],
            'result_id':record['result_id'],'payload_sha256':record['payload_sha256'],
            'recorded_at':record['recorded_at'].isoformat(),'progress':progress,'RHS_calls':0,
            'actual_scram_used_password':True,'FD_before_after':[descriptors,descriptors],'actual_crop_Runs':0}
        supervisor.immutable(output,observation)
        return observation
    finally:runtime.engine.short._Evaluator.rhs=rhs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--declaration',type=Path,required=True);parser.add_argument('--sha256',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    observation=publish(args.declaration,args.sha256,args.output)
    runtime.emit({k:observation[k] for k in ('version','scope','result_id','RHS_calls','worker','gates')})


if __name__=='__main__':
    try:main()
    except Exception as exc:
        runtime.emit({'stage':'error','error_class':type(exc).__name__});raise SystemExit(71)
