"""Export only already stored, explicitly redistributable owned research frames."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.content_access import ContentAccess
from app.crop_leaf_artifact_reader import read_leaf_area_manifest,read_leaf_area_frame,MAX,_canonical
from app.crop_rational_morphology_artifact_reader import read_rational_morphology_manifest
from app.crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore


def export(directory,root_sha256,output):
    access=ContentAccess(os.getuid(),os.getgid());root=read_leaf_area_manifest(directory,access,root_sha256)
    stem=read_rational_morphology_manifest(directory,access,root['stem_artifact_sha256'])
    if root['program_rights']['redistribute'] is not True or stem['program_rights']['redistribute'] is not True:
        raise MorphologyArtifactHold('RIGHTS_HOLD: both leaf and stem redistribution rights required')
    output.mkdir(mode=0o750);frames=[]
    for index,d in enumerate(root['samples']):
        raw=_canonical(read_leaf_area_frame(directory,access,root_sha256,index=index));name=f'frame-{index}.json'
        (output/name).write_bytes(raw)
        frames.append({'index':index,'at':d['at'],'path':name,'sha256':sha256(raw).hexdigest(),'bytes':len(raw),
            'result_sha256':d['result_sha256'],'stem_result_sha256':d['stem_result_sha256']})
    (output/'root.json').write_bytes(_canonical(root));(output/'stem-root.json').write_bytes(_canonical(stem))
    with MorphologyBlobStore(directory,access) as store:
        (output/'input.json').write_bytes(store.get(root['program_sha256'],maximum=MAX))
        (output/'stem-input.json').write_bytes(store.get(root['stem_program_sha256'],maximum=16*1024**2))
    index={'schema_version':'leaf-area-public-fixture-v1',**{k:root[k] for k in ('scope','claim_scope','gates','model_versions','display_policy')},
        'artifact_sha256':root_sha256,'program_sha256':root['program_sha256'],'stem_artifact_sha256':root['stem_artifact_sha256'],
        'rights':root['program_rights'],'stem_rights':stem['program_rights'],'frames':frames}
    raw=_canonical(index);(output/'index.json').write_bytes(raw)
    return {'artifact_sha256':root_sha256,'index_sha256':sha256(raw).hexdigest(),'frames':len(frames),'public_files':len(list(output.iterdir()))}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('root_sha256');p.add_argument('output',type=Path);args=p.parse_args()
    print(json.dumps(export(args.directory,args.root_sha256,args.output),sort_keys=True))
