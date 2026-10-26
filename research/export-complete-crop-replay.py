"""Export trusted complete research copies without loading plant equations."""
import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app import crop_complete_artifact_reader as reader
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore,_need

CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
WRITER_PATH=Path(__file__).with_name('export-leaf-funded-birth-replay.py')
_spec=importlib.util.spec_from_file_location('complete_crop_export_writer',WRITER_PATH)
writer=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(writer)
_Output=writer._Output


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256,'CODE_HOLD: original complete exporter required')
    writer._fence()


def _grants(packet):
    basis=packet['basis']
    for grants in (*basis['source_rights'].values(),basis['initial_bindings']['rights']):
        _need(all(grants[key]is True for key in ('ownership_asserted','access','store','use','transform','display','redistribute')),
              'RIGHTS_HOLD: source and initial-link public grants required')


def export(directory,root_sha256,output):
    _fence();directory,output=Path(directory),Path(output);source,target=directory.resolve(),output.resolve()
    _need(output.is_absolute()and not output.is_symlink()and output.absolute()==target
          and source!=target and source not in target.parents and target not in source.parents,
          'STORAGE_HOLD: new nonsymlink output outside source/ancestors required')
    access=ContentAccess(os.getuid(),os.getegid());written=[];blobs=[];frames=[]
    with MorphologyBlobStore(directory,access)as store:
        manifest,packet,raws=reader._load(store,root_sha256);_grants(packet);reader._fence(store,manifest,raws)
        _need(all(len(raw)<=reader.MAX for raw in raws.values()),'CAPACITY_HOLD: public blob exceeds individual export cap')
        with _Output(output)as target_dir:
            def write(name,raw):
                descriptor=target_dir.write(name,raw);written.append(descriptor);return descriptor
            for digest,raw in sorted(raws.items()):
                name='root.json'if digest==root_sha256 else'NOTICE.txt'if digest==reader.leaf.stock.NOTICE_SHA else'blob-'+digest+'.json'
                blobs.append(write(name,raw))
            by_hash={d['sha256']:d for d in blobs}
            for index,frame in enumerate(packet['frames']):
                dto={'schema_version':'complete-crop-public-frame-v1','artifact_sha256':root_sha256,'index':index,'frame':frame}
                frames.append({**reader.frame_descriptor(index,frame),**write(f'frame-{index}.json',reader._canonical(dto))})
            public={**reader.FLAGS,'schema_version':'complete-crop-public-fixture-v1','artifact_sha256':root_sha256,
                'code_sha256':manifest['code_sha256'],'exporter_sha256':CODE_SHA256,'output_writer_sha256':writer.CODE_SHA256,
                'basis':packet['basis'],'root':by_hash[root_sha256],'packet':by_hash[manifest['packet']['sha256']],
                'notice':by_hash[reader.leaf.stock.NOTICE_SHA],'blobs':blobs,'frames':frames,'sample_scalars':packet['sample_scalars']}
            raw=reader._canonical(public);_need(len(raw)<=reader.MAX,'CAPACITY_HOLD: bounded complete public index required')
            target_dir.verify(written)
            latest,current,current_raws=reader._load(store,root_sha256);_grants(current)
            _need(current_raws==raws and latest==manifest and current==packet,'SOURCE_HOLD: original complete artifact changed')
            reader._fence(store,manifest,raws);target_dir.verify(written);_fence();target_dir.publish(raw)
    return {'artifact_sha256':root_sha256,'index_sha256':sha256(raw).hexdigest(),'frames':len(frames),'public_files':len(written)+1}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);parser.add_argument('root_sha256');parser.add_argument('output',type=Path)
    args=parser.parse_args();print(json.dumps(export(args.directory,args.root_sha256,args.output),sort_keys=True))
