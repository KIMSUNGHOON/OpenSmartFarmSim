"""Export trusted supply-limited research copies without loading growth equations."""
import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app import crop_supply_morphology_artifact_reader as reader
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore, _need

CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_PUBLIC_BYTES = 64 * 1024**2
WRITER_PATH = Path(__file__).with_name('export-leaf-funded-birth-replay.py')
_spec = importlib.util.spec_from_file_location('supply_morphology_export_writer', WRITER_PATH)
writer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(writer)


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256,
          'CODE_HOLD: original loaded supply exporter required')
    writer._fence()


def _grants(manifest):
    _need(manifest['redistribution_authorized'] is True,
          'RIGHTS_HOLD: current source/material redistribution must be authorized')
    for grants in manifest['source_rights'].values():
        _need(all(grants[key] is True for key in ('ownership_asserted','access','store','use','transform','display','redistribute')),
              'RIGHTS_HOLD: explicit source and initial-declaration public grants required')


def export(directory, root_sha256, output):
    _fence()
    directory, output = Path(directory), Path(output)
    source, target = directory.resolve(), output.resolve()
    _need(output.is_absolute() and not output.is_symlink() and output.absolute() == target
          and source != target and source not in target.parents and target not in source.parents,
          'STORAGE_HOLD: new nonsymlink output outside source and ancestors required')
    access = ContentAccess(os.getuid(), os.getegid())
    written, blobs, descriptors = [], [], []
    written_bytes = 0
    with MorphologyBlobStore(directory, access) as store:
        manifest, frames, raws = reader._load(store, root_sha256)
        _grants(manifest)
        reader._fence(store, manifest, raws)
        _need(all(len(raw) <= reader.MAX for raw, _ in raws.values()),
              'CAPACITY_HOLD: public blob exceeds individual export cap')
        with writer._Output(output) as destination:
            def write(name, raw):
                nonlocal written_bytes
                _need(written_bytes + len(raw) <= MAX_PUBLIC_BYTES,
                      'CAPACITY_HOLD: bounded aggregate public export required')
                descriptor = destination.write(name, raw)
                written_bytes += len(raw)
                written.append(descriptor)
                return descriptor
            for digest, (raw, _) in sorted(raws.items()):
                name = 'root.json' if digest == root_sha256 else 'NOTICE.txt' if digest == reader.carbon.NOTICE_SHA else 'blob-' + digest + '.json'
                blobs.append(write(name, raw))
            by_hash = {descriptor['sha256']:descriptor for descriptor in blobs}
            for index, frame in enumerate(frames):
                dto = {'schema_version':'supply-morphology-public-frame-v1', 'artifact_sha256':root_sha256,
                       'index':index, 'frame':frame}
                descriptors.append({**reader.frame_descriptor(frame),
                    **write(f'frame-{index}.json', reader._canonical(dto))})
            public = {**reader.FLAGS, 'schema_version':'supply-morphology-public-fixture-v1',
                'artifact_sha256':root_sha256, 'code_sha256':manifest['code_sha256'],
                'exporter_sha256':CODE_SHA256, 'output_writer_sha256':writer.CODE_SHA256,
                'source_rights':manifest['source_rights'], 'redistribution_authorized':True,
                'terminal':manifest['terminal'], 'root':by_hash[root_sha256],
                'notice':by_hash[reader.carbon.NOTICE_SHA], 'blobs':blobs, 'frames':descriptors,
                'sample_scalars':sum(len(frame['snapshot']['state']) for frame in frames)}
            raw = reader._canonical(public)
            _need(len(raw) <= reader.MAX and written_bytes + len(raw) <= MAX_PUBLIC_BYTES,
                  'CAPACITY_HOLD: bounded public index and aggregate export required')
            destination.verify(written)
            latest, current, current_raws = reader._load(store, root_sha256)
            _grants(latest)
            _need(latest == manifest and current == frames and current_raws == raws,
                  'SOURCE_HOLD: original source identity, bytes and frames required before publication')
            reader._fence(store, manifest, raws)
            destination.verify(written)
            _fence()
            destination.publish(raw)
    return {'artifact_sha256':root_sha256, 'index_sha256':sha256(raw).hexdigest(),
            'frames':len(frames), 'public_files':len(written)+1}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('root_sha256')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.directory, args.root_sha256, args.output), sort_keys=True))
