"""Research only: recheck unchanged bytes against original preflight evidence."""
from functools import lru_cache
from hashlib import sha256
import hmac
import importlib.util
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION='own-crop-input-witness-experiment-v1'
DOMAIN=b'own-input-QC-reuse-experiment-v1\0'
MAX_WITNESS_BYTES=1024*1024
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def need(condition):
    if not condition:raise ValueError('owned input witness unavailable')


@lru_cache(maxsize=1)
def driver():
    path=ROOT/'research/crop-cycle-full-rhs-reference.py'
    spec=importlib.util.spec_from_file_location('owned_witness_original_driver',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def spec(path,digest,profiles,notice):
    need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256)
    return driver().read_spec(path,digest,profiles,notice)


def key_bytes(key):need(type(key) is bytes and 32<=len(key)<=4096)


def context_record(context):
    driver().engine._require_context(context)
    index=[{'cursor':None if p.cursor is None else json.loads(p.cursor),
        'previous':p.previous,'steps':p.steps} for p in context.index]
    result={'manifest':context.manifest,'initial':json.loads(context._initial),
        'initial_clock':json.loads(context._initial_clock),'seed':list(context.seed),
        'start_at':context.start_at,'planned_steps':context.planned_steps,
        'boundary_count':context.boundary_count,'segment_count':context.segment_count,
        'context_sha256':context.root_sha256,'plan':context.reader.plan,'index':index}
    need(sha256(driver().inputs._canonical(index)).hexdigest()==result['manifest']['grid_index_sha256'])
    return result


def certify(path,digest,profiles,notice,*,key):
    key_bytes(key);original=driver();experiment=spec(path,digest,profiles,notice)
    with original.inputs.open_input_packet(Path(path)/'inputs',experiment['input_root_sha256'],**profiles) as reader:
        need(reader.plan==experiment['plan'])
        context=original.engine.prepare_context(reader,**profiles)
        payload={'version':VERSION,'scope':'input_QC_reuse_experiment_only','gates':'not_assessed',
            'witness_code_sha256':CODE_SHA256,'spec_sha256':digest,
            'input_root_sha256':reader.root_sha256,'context':context_record(context)}
    raw=original.inputs._canonical(payload)
    envelope=original.inputs._canonical({'payload':payload,
        'hmac_sha256':hmac.new(key,DOMAIN+raw,'sha256').hexdigest()})
    need(len(envelope)<=MAX_WITNESS_BYTES);return envelope


def verify(path,digest,profiles,notice,raw,*,key):
    key_bytes(key);need(type(raw) is bytes and 0<len(raw)<=MAX_WITNESS_BYTES)
    original=driver();inputs=original.inputs;experiment=spec(path,digest,profiles,notice)
    value=inputs._json(raw)
    need(type(value) is dict and set(value)=={'payload','hmac_sha256'} and inputs._digest(value['hmac_sha256']))
    payload=value['payload'];need(type(payload) is dict and set(payload)=={
        'version','scope','gates','witness_code_sha256','spec_sha256','input_root_sha256','context'})
    need(hmac.compare_digest(value['hmac_sha256'],hmac.new(key,DOMAIN+inputs._canonical(payload),'sha256').hexdigest()))
    need(payload['version']==VERSION and payload['scope']=='input_QC_reuse_experiment_only'
        and payload['gates']=='not_assessed' and payload['witness_code_sha256']==CODE_SHA256
        and payload['spec_sha256']==digest and payload['input_root_sha256']==experiment['input_root_sha256'])
    context=payload['context'];need(type(context) is dict and set(context)=={
        'manifest','initial','initial_clock','seed','start_at','planned_steps','boundary_count',
        'segment_count','context_sha256','plan','index'})
    need(context['plan']==experiment['plan'] and context['planned_steps']==experiment['plan']['planned_steps']
        and context['manifest']['input_root_sha256']==payload['input_root_sha256']
        and inputs._hash(context['manifest'])==context['context_sha256']
        and inputs._hash(context['index'])==context['manifest']['grid_index_sha256'])
    fd=None
    try:
        fd=os.open(Path(path)/'inputs',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        root_raw=inputs._read(fd,'root.json',inputs.MAX_ROOT_BYTES)
        need(sha256(root_raw).hexdigest()==payload['input_root_sha256'])
        root=inputs._json(root_raw)
        names={block['sha256'] for stream in root['streams'].values() for block in stream['blocks']}
        need(set(os.listdir(fd))=={'root.json',*(name+'.json' for name in names)})
        total=len(root_raw)
        for name in sorted(names):
            current=inputs._read(fd,name+'.json',inputs.MAX_BLOCK_BYTES)
            need(sha256(current).hexdigest()==name);total+=len(current)
            need(total<=inputs.MAX_PACKET_BYTES)
        need(total==experiment['plan']['packet_referenced_bytes'])
    except OSError as exc:raise ValueError('owned input witness storage unavailable') from exc
    finally:
        if fd is not None:os.close(fd)
    return {'version':VERSION,'context':context,'current_blob_bytes_match':True,
        'referenced_bytes':total,'unique_blob_count':len(names),'rights_or_gate_approval':False,
        'scope':'input_QC_reuse_experiment_only','witness_sha256':sha256(raw).hexdigest()}
