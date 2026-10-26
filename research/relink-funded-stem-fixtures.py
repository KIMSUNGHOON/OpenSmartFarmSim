"""Create new owned attachment versions; preserve all original model quantities."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app import crop_leaf_funded_birth_continuation as model
from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
from app.crop_morphology_artifact_reader import _canonical
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore, MAX_BLOB_BYTES
from app.crop_rational_morphology_artifact_reader import read_rational_morphology_manifest


def copy_stem_source(source, output, access, root_sha256):
    manifest=read_rational_morphology_manifest(source,access,root_sha256)
    with MorphologyBlobStore(source,access)as original, MorphologyBlobStore(output,access,write=True)as target:
        for path in Path(source).iterdir():
            raw=original.get(path.name,maximum=MAX_BLOB_BYTES)
            assert target.put(raw,maximum=MAX_BLOB_BYTES)==path.name
    assert read_rational_morphology_manifest(output,access,root_sha256)==manifest


def relink_inputs(inputs, parent_ids, profiles):
    result=deepcopy(inputs);root=model.parent.prepare_context(program=result['program'],
        step_seconds=result['step_seconds'],step_count=result['step_count'],**profiles)
    assert len(parent_ids)==len(result['births'])
    context=None;cp=model.parent.start(root);index=0
    for step in range(result['step_count']+1):
        if step:
            engine=model if context is not None else model.parent
            run=engine.advance_chunk(context if context is not None else root,cp,1)
            assert run['hold']is None;cp=run['checkpoint']
        while index<len(result['births'])and result['births'][index]['step_index']==step:
            point=result['births'][index]['point_inputs'];assert len(point['events'])==1
            point['events'][0]['attachment_internode_id']=parent_ids[index]
            point['context_sha256']=context.root_sha256 if context is not None else root.root_sha256
            point['checkpoint_sha256']=cp.sha256
            engine=model if context is not None else model.parent
            raw=engine.checkpoint_bytes(context if context is not None else root,cp)
            if context is None:
                context=model.prepare_context(parent_context=root,raw_parent_checkpoint=raw,expected_parent_sha256=cp.sha256,inputs=point)
            else:
                context=model.adopt_births(context=context,raw_checkpoint=raw,expected_sha256=cp.sha256,inputs=point)
            cp=model.start(context);index+=1
    assert index==len(result['births'])
    stripped=deepcopy(result)
    for before,after in zip(inputs['births'],stripped['births'],strict=True):
        a,b=before['point_inputs'],after['point_inputs']
        for key in ['context_sha256','checkpoint_sha256']:b[key]=a[key]
        b['events'][0]['attachment_internode_id']=a['events'][0]['attachment_internode_id']
    assert stripped==inputs
    return result


def generate(source, output):
    source,output=Path(source),Path(output);decl_raw=(ROOT/'fixtures/crop-funded-fractional-stem-bindings-v1.json').read_bytes();decl=json.loads(decl_raw)
    register=json.loads((source/'register.json').read_bytes());assert register['declaration_sha256']==decl['source_declaration_sha256']
    output.mkdir(mode=0o750);(output/'leaves').mkdir(mode=0o750);access=ContentAccess(os.getuid(),os.getegid())
    assert register['stem_root_sha256']==decl['source_stem_root_sha256']
    copy_stem_source(source/'stem',output/'stem',access,register['stem_root_sha256'])
    from app import crop_funded_event_state as candidate
    profiles={name:kind((ROOT/'fixtures'/file).read_bytes())for name,kind,file in (
        ('growth_profile',candidate.event.Growth,'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile',candidate.event.Cohort,'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile',candidate.event.Transport,'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile',candidate.event.Exchange,'crop-canopy-exchange-reference-parameters-v1.json'))}
    cases=[]
    for item in register['cases']:
        directory=source/'leaves'/str(item['case_index']);manifest=json.loads((directory/item['leaf_root_sha256']).read_bytes())
        raw=(directory/manifest['sources']['inputs']['sha256']).read_bytes();original=json.loads(raw)
        assert original['rights']['redistribute']is True
        inputs=relink_inputs(original,decl['original_point_parent_ids'],profiles);inputs['rights']=deepcopy(decl['rights'])
        root=produce_funded_leaf_artifact(output/'leaves'/str(item['case_index']),access,inputs_raw=_canonical(inputs),**profiles)
        cases.append({**item,'leaf_root_sha256':root,'previous_leaf_root_sha256':item['leaf_root_sha256'],'previous_inputs_sha256':sha256(raw).hexdigest()})
    result={**register,'declaration_sha256':sha256(decl_raw).hexdigest(),'previous_declaration_sha256':register['declaration_sha256'],'cases':cases}
    (output/'register.json').write_bytes(_canonical(result));return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    print(json.dumps(generate(args.source,args.output),sort_keys=True))
