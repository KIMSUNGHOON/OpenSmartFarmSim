"""Compiled product SDK reads an unpaused owned synthetic worker over verified TLS."""
from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import subprocess
import threading
import time

import pytest

from test_crop_climate_joint_prefix_runtime import (
    prefix_native, native, execution_config, joint_config, private_config, store,
    tls_files, login_database, original_login_scope, login_scope, authoring,
    farm_setup, setup, profiles, database_cleanup, LOGIN, TOKEN, consumer,
    progress, current, public, fd_inventory, http_identity, unpaused_consumer, proofs)


# The guarded runner extracts this literal and compiles it with the installed Vite.
SDK_ENTRY = r'''
import { readFileSync,writeFileSync } from 'node:fs';
import { dirname,join } from 'node:path';
import { createHash } from 'node:crypto';
import { createApi,ApiError } from '__API_MODULE__';
import { jointExecutionResultLookup } from '__EXECUTION_MODULE__';
const directory=dirname(process.argv[2]!);
const input=JSON.parse(readFileSync(process.argv[2]!,'utf8'));
const digest=(value:string|Uint8Array)=>createHash('sha256').update(value).digest('hex');
const requests:unknown[]=[];
function save(name:string,value:string|Uint8Array){writeFileSync(join(directory,name),value,{flag:'wx',mode:0o400});}
function bits(value:unknown,path='$',out:Record<string,string>={}):Record<string,string>{
 if(typeof value==='number'){const buffer=Buffer.alloc(8);buffer.writeDoubleBE(value);out[path]=buffer.toString('hex');}
 else if(Array.isArray(value))value.forEach((v,i)=>bits(v,path+'/'+i,out));
 else if(value!==null && typeof value==='object')for(const [k,v] of Object.entries(value))bits(v,path+'/'+k,out);
 return out;
}
async function main(){
 if(!/^https:\/\/127\.0\.0\.1:\d+$/.test(input.origin))throw Error('origin');
 const fetcher:typeof fetch=async(path,init)=>{
  const start=performance.now(),response=await fetch(new URL(String(path),input.origin),init);
  const raw=new Uint8Array(await response.clone().arrayBuffer());
  if(raw.byteLength>2*1024*1024)throw Error('capture size');
  save('reply.wire',raw);
  requests.push({method:init?.method,status:response.status,bytes:raw.byteLength,sha256:digest(raw),
   seconds:(performance.now()-start)/1000,no_store:response.headers.get('cache-control')==='no-store'});
  return response;
 };
 const api=createApi(input.token,fetcher);let result:unknown;
 if(input.operation==='submit')result=await api.submitJointCropClimateExecution(input.request);
 else if(input.operation==='prefix')result=await api.jointCropClimatePrefix(input.lookup);
 else if(input.operation==='page')result=await api.jointCropClimatePrefixPage(input.lookup,input.selector,input.query,{summary:input.summary});
 else if(input.operation==='progress')result=await api.jointCropClimateExecution(input.lookup);
 else if(input.operation==='cancel')result=await api.cancelJointCropClimateExecution(input.job_id);
 else if(input.operation==='stored'){
  const selection=jointExecutionResultLookup(input.progress);if(selection===null)throw Error('result unavailable');
  result=await api.jointCropClimateSummary(selection);
 }else throw Error('operation');
 const raw=JSON.stringify(result);save('result.private.json',raw);save('number-bits.private.json',JSON.stringify(bits(result)));
 console.log(JSON.stringify({operation:input.operation,result_sha256:digest(raw),requests}));
}
main().catch(error=>{
 const value={code:error instanceof ApiError?error.code:'native_client_rejected',status:error instanceof ApiError?error.status:null,requests};
 save('error.private.json',JSON.stringify(value));console.log(JSON.stringify(value));process.exitCode=1;
});
'''


@contextmanager
def serve(runtime):
    server = runtime.service.server(); before = fd_inventory()
    thread = threading.Thread(target=server.run, daemon=True); thread.start()
    deadline = time.monotonic()+10
    try:
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline
            time.sleep(.01)
        yield 'https://127.0.0.1:'+str(server.servers[0].sockets[0].getsockname()[1])
    finally:
        server.should_exit = True; thread.join(15)
        assert not thread.is_alive() and fd_inventory() == before


def number_bits(value, path='$', output=None):
    if output is None: output = {}
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        output[path] = struct.pack('>d', float(value)).hex()
    elif isinstance(value, list):
        for index, item in enumerate(value): number_bits(item, path+'/'+str(index), output)
    elif isinstance(value, dict):
        for key, item in value.items(): number_bits(item, path+'/'+key, output)
    return output


def invoke(root, origin, c, operation, *, trust=True, allowed_errors=(), **fields):
    directory = root/str(len(list(root.iterdir()))); directory.mkdir(mode=0o700)
    path = directory/'client-input.private.json'
    with path.open('x') as f:
        os.fchmod(f.fileno(), 0o600)
        json.dump({'origin': origin, 'token': TOKEN.decode(), 'operation': operation, **fields}, f)
    env = {**os.environ}
    for key in ('NODE_EXTRA_CA_CERTS', 'NODE_TLS_REJECT_UNAUTHORIZED', 'NODE_OPTIONS'): env.pop(key, None)
    if trust: env['NODE_EXTRA_CA_CERTS'] = str(c.config.certificate)
    bundle = Path(os.environ['OSSF_JOINT_PREFIX_CLIENT_BUNDLE']); assert bundle.is_file()
    start = time.monotonic()
    child = subprocess.run(['node', '--max-old-space-size=96', str(bundle), str(path)],
        env=env, capture_output=True, timeout=45)
    assert len(child.stdout)+len(child.stderr) < 65536
    metadata = json.loads(child.stdout)
    metadata.update(actual_exit=child.returncode, wall_seconds=time.monotonic()-start,
        bundle_sha256=sha256(bundle.read_bytes()).hexdigest())
    if child.returncode:
        assert child.returncode == 1 and metadata['code'] in allowed_errors, metadata
        assert all(q['no_store'] for q in metadata['requests'])
        return None, metadata, None
    assert child.stderr == b'', child.stderr.decode()
    raw = (directory/'reply.wire').read_bytes()
    value = json.loads((directory/'result.private.json').read_bytes())
    original = json.loads(raw)
    assert value == original and all(q['no_store'] for q in metadata['requests'])
    numbers = json.loads((directory/'number-bits.private.json').read_bytes())
    assert numbers == number_bits(original)
    metadata.update(binary64_values_preserved=len(numbers), original_values_and_UTC_preserved=True)
    return value, metadata, raw


def evidence(name, value):
    root = os.environ.get('OSSF_JOINT_PREFIX_SDK_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400)
            json.dump(value, f, sort_keys=True); f.flush(); os.fsync(f.fileno())


@LOGIN
@pytest.mark.parametrize('setup,expected', [(None, 'completed'), ('hold', 'hold')], indirect=['setup'])
def test_compiled_sdk_unpaused_prefix_to_original_terminal(prefix_native, tmp_path, monkeypatch, expected):
    c = prefix_native; rt = c.prefix_runtime; root = tmp_path/'sdk'; root.mkdir(mode=0o700)
    replies = []; captured = []; accepted = 0; pages = []; calls = {}
    serialize = public._public_bytes
    def record(model):
        raw = serialize(model); captured.append(raw); return raw
    monkeypatch.setattr(public, '_public_bytes', record)
    pack, factory = unpaused_consumer(c, tmp_path)
    try:
        with serve(rt) as origin:
            _, proof, _ = invoke(root, origin, c, 'prefix', trust=False,
                allowed_errors=('network_unresolved',), lookup={'job_id': '11111111-1111-4111-8111-111111111111', 'farm': json.loads(c.raw)['farm']})
            assert proof['actual_exit'] == 1; replies.append(proof)
            admitted, proof, _ = invoke(root, origin, c, 'submit', request=json.loads(c.raw)); replies.append(proof)
            job = admitted['job_id']; lookup = {'job_id': job, 'farm': json.loads(c.raw)['farm']}
            assert job not in pack.read_text()+factory.read_text() and not (tmp_path/'block').exists()
            with monkeypatch.context() as patch:
                calls = progress.forbid(patch)
                queued, proof, raw = invoke(root, origin, c, 'prefix', lookup=lookup); replies.append(proof)
                assert queued['prefix_status'] == 'none' and raw == captured[-1] and not any(calls.values())
            with consumer.legacy.process_consumer(tmp_path, 'joint_operator:build') as (process, events, errors):
                deadline = time.monotonic()+240
                with monkeypatch.context() as patch:
                    calls = progress.forbid(patch)
                    while True:
                        assert time.monotonic() < deadline and process.poll() is None
                        value, proof, raw = invoke(root, origin, c, 'prefix', lookup=lookup,
                            allowed_errors=('server_unavailable',)); replies.append(proof)
                        if value is None: continue
                        assert raw == captured[-1]
                        if value['prefix_status'] == 'closed': break
                        if value['prefix_status'] == 'accepted':
                            accepted += 1; ref = value['reference']
                            for kind in ('samples', 'events'):
                                page, proof, raw = invoke(root, origin, c, 'page', lookup=lookup,
                                    selector=ref['selector'], summary=value, query={'kind': kind, 'start': 0, 'limit': 64 if kind == 'samples' else 8},
                                    allowed_errors=('server_unavailable', 'intent_conflict')); replies.append(proof)
                                if page is not None:
                                    assert raw == captured[-1] and page['reference'] == ref
                                    pages.append({'kind': kind, 'rows': len(page['page']['records']),
                                        'selector': ref['selector'], 'sha256': sha256(raw).hexdigest()})
                        time.sleep(.1)
                    assert not any(calls.values())
                consumer.legacy.wait_for(lambda: bool(list(tmp_path.glob('attempt-*.private.json'))), process, timeout=30)
            attempts = proofs(tmp_path)
            assert process.returncode == 0 and errors == [''] and len(attempts) == 1
            assert attempts[0]['state'] == ('succeeded' if expected == 'completed' else 'hold')
            assert accepted > 0 and any(p['kind'] == 'samples' and p['rows'] > 0 for p in pages)
            with monkeypatch.context() as patch:
                calls = progress.forbid(patch)
                final, proof, _ = invoke(root, origin, c, 'progress', lookup=lookup); replies.append(proof)
                assert final['result']['status'] == expected
                saved, proof, raw = invoke(root, origin, c, 'stored', progress=final); replies.append(proof)
                expected_raw = current.JointCropClimateCurrentQuery(c.worker.results).read(
                    'tenant-1', final['result']['result_id'], lookup['farm'], view='summary')
                assert raw == expected_raw and saved == json.loads(expected_raw) and not any(calls.values())
            assert events[-1]['event'] == 'stopped'
        assert http_identity.current_principal() is None
        evidence('sdk-'+expected, {'actual_scram': True, 'verified_TLS_and_untrusted_CA_rejected': True,
            'compiled_product_SDK': True, 'test_pause': False, 'chunk_budget': 8,
            'running_accepted_count': accepted, 'pages': pages, 'attempts': attempts,
            'original_terminal_bytes': True, 'read_calls': calls, 'process_exit': process.returncode,
            'requests': replies, 'events': events, 'G0_G4': 'not_assessed', 'actual_crop_Runs': 0})
    finally:
        pack.unlink(); (tmp_path/'proof.private.json').unlink()


@LOGIN
def test_compiled_sdk_rights_and_unpaused_cancel(prefix_native, tmp_path, monkeypatch):
    c = prefix_native; root = tmp_path/'sdk'; root.mkdir(mode=0o700); replies = []
    pack, factory = unpaused_consumer(c, tmp_path)
    try:
        with serve(c.prefix_runtime) as origin:
            admitted, proof, _ = invoke(root, origin, c, 'submit', request=json.loads(c.raw)); replies.append(proof)
            job = admitted['job_id']; lookup = {'job_id': job, 'farm': json.loads(c.raw)['farm']}
            with consumer.legacy.process_consumer(tmp_path, 'joint_operator:build') as (process, events, errors):
                consumer.legacy.wait_for(lambda: c.worker.jobs.get_job('tenant-1', job)['state'] == 'simulating', process, timeout=30)
                c.value[-1].allowed = False
                with monkeypatch.context() as patch:
                    calls = progress.forbid(patch)
                    value, proof, _ = invoke(root, origin, c, 'prefix', lookup=lookup, allowed_errors=('invalid_request',))
                    assert value is None and proof['status'] == 422 and not any(calls.values()); replies.append(proof)
                canceled, proof, _ = invoke(root, origin, c, 'cancel', job_id=job); replies.append(proof)
                assert canceled['cancel_accepted'] and canceled['cancel_requested']
                consumer.legacy.wait_for(lambda: bool(list(tmp_path.glob('attempt-*.private.json'))), process, timeout=90)
            assert process.returncode == 0 and errors == [''] and proofs(tmp_path)[-1]['state'] == 'canceled'
            c.value[-1].allowed = True
            with monkeypatch.context() as patch:
                calls = progress.forbid(patch)
                closed, proof, _ = invoke(root, origin, c, 'prefix', lookup=lookup); replies.append(proof)
                assert closed['prefix_status'] == 'closed' and closed['reference'] is None and not any(calls.values())
                final, proof, _ = invoke(root, origin, c, 'progress', lookup=lookup); replies.append(proof)
                assert final['job']['state'] == 'canceled' and final['result'] is None
            consumer.reference.no_published_result(c.worker, job)
        evidence('sdk-cancel', {'actual_scram': True, 'verified_TLS': True, 'compiled_product_SDK': True,
            'test_pause': False, 'worker_acknowledged': True, 'rights_422': True, 'no_result_published': True,
            'process_exit': process.returncode, 'attempts': proofs(tmp_path), 'read_calls': calls,
            'requests': replies, 'events': events, 'G0_G4': 'not_assessed', 'actual_crop_Runs': 0})
    finally:
        pack.unlink(); (tmp_path/'proof.private.json').unlink()
