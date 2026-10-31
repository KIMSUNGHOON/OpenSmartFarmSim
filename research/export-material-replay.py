"""Export a source-bound material window without importing growth equations."""
import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app import crop_supply_material_artifact_reader as reader
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore,_need

CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_PUBLIC_BYTES=64*1024**2
WRITER_PATH=Path(__file__).with_name('export-leaf-funded-birth-replay.py')
_spec=importlib.util.spec_from_file_location('material_replay_fixed_fd_writer',WRITER_PATH)
writer=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(writer)


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256,'CODE_HOLD: original loaded material exporter required');writer._fence()


def _grants(manifest):
    _need(all(manifest['effective_rights'][k]is True for k in ['use','display','redistribute']),
        'RIGHTS_HOLD: explicit original use/display/redistribution required')


def export(directory,root_sha256,output):
    _fence();directory,output=Path(directory),Path(output);source,target=directory.resolve(),output.resolve()
    _need(output.is_absolute()and not output.is_symlink()and output.absolute()==target
        and source!=target and source not in target.parents and target not in source.parents,
        'STORAGE_HOLD: new nonsymlink output outside source and ancestors required')
    access=ContentAccess(os.getuid(),os.getgid());written=[];blobs=[];descriptors=[];total=0
    with MorphologyBlobStore(directory,access)as store:
        manifest,frames,raws=reader._load(store,root_sha256);_grants(manifest);reader._fence(store,manifest,raws)
        with writer._Output(output)as destination:
            def write(name,raw):
                nonlocal total
                _need(len(raw)<=reader.MAX and total+len(raw)<=MAX_PUBLIC_BYTES,'CAPACITY_HOLD: bounded public material export required')
                d=destination.write(name,raw);total+=len(raw);written.append(d);return d
            for h,(raw,_)in sorted(raws.items()):
                name='root.json'if h==root_sha256 else'NOTICE.txt'if h==manifest['notice']['sha256']else'blob-'+h+'.json'
                blobs.append(write(name,raw))
            by_hash={v['sha256']:v for v in blobs}
            for i,frame in enumerate(frames):
                value={'schema_version':'supply-material-public-frame-v1','artifact_sha256':root_sha256,'index':i,'frame':frame}
                descriptors.append({**reader.frame_descriptor(frame),**write(f'frame-{i}.json',reader.raw(value))})
            index={**reader.FLAGS,'schema_version':'supply-material-public-fixture-v1','artifact_sha256':root_sha256,
                'code_sha256':manifest['code_sha256'],'exporter_sha256':CODE_SHA256,'output_writer_sha256':writer.CODE_SHA256,
                'effective_rights':manifest['effective_rights'],'window':manifest['window'],'terminal':manifest['terminal'],
                'root':by_hash[root_sha256],'notice':by_hash[manifest['notice']['sha256']],'blobs':blobs,'frames':descriptors,
                'sample_scalars':sum(len(f['snapshot']['state'])for f in frames)}
            raw=reader.raw(index);_need(len(raw)<=reader.MAX and total+len(raw)<=MAX_PUBLIC_BYTES,'CAPACITY_HOLD: bounded final public index required')
            destination.verify(written);latest,current,current_raws=reader._load(store,root_sha256);_grants(latest)
            _need(latest==manifest and current==frames and current_raws==raws,'SOURCE_HOLD: original source bytes/identity/frames required')
            reader._fence(store,manifest,raws);destination.verify(written);_fence();destination.publish(raw)
    return {'artifact_sha256':root_sha256,'index_sha256':sha256(raw).hexdigest(),'frames':len(frames),'public_files':len(written)+1}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('root_sha256');p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(export(a.directory,a.root_sha256,a.output),sort_keys=True))
