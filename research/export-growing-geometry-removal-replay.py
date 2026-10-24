"""Export saved removal phases, original references and notices.

No growth, continuation or producer imports. This exports research fixtures,
not a farm Run or a new rights decision about the referenced publications.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
from app.content_access import ContentAccess
from app.crop_growing_geometry_removal_artifact_reader import read_removal_manifest, read_removal_frame, ROOT_CONSTANTS, MAX
from app.crop_morphology_artifact_io import MorphologyBlobStore, _need
from app.crop_morphology_artifact_reader import _canonical

CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


def _grants(m):
    _need(all(m['source_rights'][key] is True for key in ('use', 'display', 'redistribute')),
        'RIGHTS_HOLD: own input use/display/redistribute grants required')


def _output_identity(output):
    s = output.lstat()
    _need(stat.S_ISDIR(s.st_mode) and s.st_uid == os.getuid() and s.st_gid == os.getgid()
        and not s.st_mode & 0o022, 'STORAGE_HOLD: owned output without group/other writes required')
    return s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid


def _write(output, name, raw):
    _need(type(raw) is bytes and 0 < len(raw) <= MAX, 'CAPACITY_HOLD: bounded export file required')
    fd = os.open(output/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o640)
    with os.fdopen(fd, 'wb') as f: f.write(raw); f.flush(); os.fsync(f.fileno())
    return {'path': name, 'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)}


def _written(output, written, identity):
    _need(_output_identity(output) == identity and {p.name for p in output.iterdir()} == {d['path'] for d in written},
        'STORAGE_HOLD: output identity or file set changed')
    for d in written:
        fd = os.open(output/d['path'], os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as f:
            s = os.fstat(f.fileno())
            _need(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_uid == os.getuid()
                and s.st_gid == os.getgid() and not s.st_mode & 0o022, 'STORAGE_HOLD: owned output file required')
            raw = f.read(MAX+1)
        _need(len(raw) == d['bytes'] and sha256(raw).hexdigest() == d['sha256'], 'HASH_HOLD: written bytes differ')


def _publish_index(output, raw):
    _write(output, '.index.pending', raw)
    os.replace(output/'.index.pending', output/'index.json')


def export(directory, root_sha256, output):
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256, 'CODE_HOLD: exporter source changed after import')
    directory, output = Path(directory), Path(output)
    source, target = directory.resolve(), output.resolve()
    _need(output.is_absolute() and not output.is_symlink() and output.absolute() == target
        and source != target and source not in target.parents and target not in source.parents,
        'STORAGE_HOLD: new nonsymlink output outside source and its ancestors required')
    access = ContentAccess(os.getuid(), os.getgid())
    m = read_removal_manifest(directory, access, root_sha256); _grants(m)
    output.mkdir(mode=0o750); identity = _output_identity(output)
    written = []; sources = []; frames = []; checkpoints = []
    def write(name, raw):
        d = _write(output, name, raw); written.append(d); return d
    with MorphologyBlobStore(directory, access) as store:
        sources.append({'role': 'root', **write('root.json', store.get(root_sha256, maximum=MAX))})
        for role, source_descriptor in m['sources'].items():
            name = 'NOTICE.txt' if role == 'license_notice' else f'source-{role}.json'
            sources.append({'role': role, **write(name, store.get(source_descriptor['sha256'], maximum=MAX))})
        for i, sample in enumerate(m['samples']):
            frame = read_removal_frame(directory, access, root_sha256, index=i)
            checkpoints.append({**sample, **write(f'checkpoint-{i}.json', store.get(sample['checkpoint_sha256'], maximum=256*1024))})
            frames.append({**{key: frame[key] for key in ('index', 'global_step_index', 'phase', 'at', 'parent_context_sha256', 'post_context_sha256', 'point_calculation_sha256', 'checkpoint_sha256', 'sample_sha256', 'state_sha256')},
                **write(f'frame-{i}.json', _canonical(frame))})
    public = {**ROOT_CONSTANTS, 'schema_version': 'growing-geometry-removal-public-fixture-v1', 'artifact_sha256': root_sha256,
        'input_id': m['input_id'], 'source_rights': m['source_rights'], 'exporter_sha256': CODE_SHA256,
        'sources': sources, 'checkpoints': checkpoints, 'frames': frames}
    raw = _canonical(public); _need(len(raw) <= MAX, 'CAPACITY_HOLD: bounded public index required')
    _written(output, written, identity)
    latest = read_removal_manifest(directory, access, root_sha256); _grants(latest)
    _need(_canonical(latest) == _canonical(m), 'HASH_HOLD: original export source changed')
    _written(output, written, identity)
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256, 'CODE_HOLD: exporter source changed before publication')
    _publish_index(output, raw)
    return {'artifact_sha256': root_sha256, 'index_sha256': sha256(raw).hexdigest(), 'frames': len(frames), 'public_files': len(written)+1}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('directory', type=Path); parser.add_argument('root_sha256'); parser.add_argument('output', type=Path)
    args = parser.parse_args(); print(json.dumps(export(args.directory, args.root_sha256, args.output), sort_keys=True))
