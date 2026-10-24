"""Export immutable synthetic lifecycle frames with three separate source grants."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
from app.content_access import ContentAccess
from app.crop_leaf_lifecycle_artifact_reader import read_leaf_lifecycle_manifest, read_leaf_lifecycle_frame, MAX
from app.crop_morphology_artifact_io import MorphologyBlobStore, _need
from app.crop_morphology_artifact_reader import _canonical

SOURCE_FILES = {'root.json': 'artifact_sha256', 'input.json': 'appearance_program_sha256',
    'management.json': 'management_program_sha256', 'preparation.json': 'preparation_sha256',
    'initial-state.json': 'initial_state_sha256', 'stem-root.json': 'stem_artifact_sha256', 'stem-input.json': 'stem_program_sha256'}
REFERENCES = tuple(field for field in SOURCE_FILES.values() if field != 'artifact_sha256')


def _grants(root):
    _need(all(root['source_rights'][source][grant] is True
              for source in ['appearance', 'management', 'stem'] for grant in ['use', 'display', 'redistribute']),
          'RIGHTS_HOLD: appearance, management and stem redistribution grants required')


def _output_identity(output):
    s = output.lstat()
    _need(stat.S_ISDIR(s.st_mode) and s.st_uid == os.getuid() and s.st_gid == os.getgid() and not s.st_mode & 0o022,
          'STORAGE_HOLD: owned public directory without group or other writes required')
    return s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid


def _written(output, written, identity):
    _need(_output_identity(output) == identity and {p.name for p in output.iterdir()} == {d['path'] for d in written},
          'STORAGE_HOLD: public directory or file list changed')
    for descriptor in written:
        fd = os.open(output/descriptor['path'], os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as handle:
            s = os.fstat(handle.fileno())
            _need(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_uid == os.getuid() and not s.st_mode & 0o022,
                  'STORAGE_HOLD: owned public file required')
            raw = handle.read(MAX + 1)
        _need(len(raw) == descriptor['bytes'] and sha256(raw).hexdigest() == descriptor['sha256'],
              'HASH_HOLD: written public bytes differ')


def _publish_index(output, raw):
    _need(0 < len(raw) <= MAX, 'CAPACITY_HOLD: bounded public index required')
    temporary = output/'.index.pending'
    with temporary.open('xb') as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, output/'index.json')


def export(directory, root_sha256, output):
    directory, output = Path(directory), Path(output)
    _need(directory.resolve() != output.resolve() and directory.resolve() not in output.resolve().parents,
          'STORAGE_HOLD: public output must be outside immutable source')
    access = ContentAccess(os.getuid(), os.getgid())
    root = read_leaf_lifecycle_manifest(directory, access, root_sha256); _grants(root)
    output.mkdir(mode=0o750); identity = _output_identity(output); written = []; frames = []; sources = []
    def write(name, raw):
        _need(type(raw) is bytes and 0 < len(raw) <= MAX, 'CAPACITY_HOLD: bounded public bytes required')
        (output/name).write_bytes(raw)
        descriptor = {'path': name, 'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)}
        written.append(descriptor); return descriptor
    for index, sample in enumerate(root['samples']):
        frame = read_leaf_lifecycle_frame(directory, access, root_sha256, index=index)
        frames.append({**{k: sample[k] for k in ['index', 'at', 'result_sha256', 'input_state_sha256', 'state_sha256', 'input_sha256', 'stem_result_sha256']},
                       **write(f'frame-{index}.json', _canonical(frame))})
    references = {'artifact_sha256': root_sha256, **{k: root[k] for k in REFERENCES}}
    with MorphologyBlobStore(directory, access) as store:
        for name, field in SOURCE_FILES.items(): sources.append(write(name, store.get(references[field], maximum=MAX)))
    public = {'schema_version': 'leaf-lifecycle-public-fixture-v1',
        **{k: root[k] for k in ['scope', 'claim_scope', 'gates', 'time_kind', 'parameter_scope', 'model_versions', 'display_policy']},
        **references, 'source_rights': root['source_rights'], 'sources': sources, 'frames': frames}
    raw = _canonical(public); _written(output, written, identity)
    latest = read_leaf_lifecycle_manifest(directory, access, root_sha256); _grants(latest)
    _need(_canonical(latest) == _canonical(root), 'HASH_HOLD: export source changed before publication')
    _written(output, written, identity); _publish_index(output, raw)
    return {'artifact_sha256': root_sha256, 'index_sha256': sha256(raw).hexdigest(), 'frames': len(frames), 'public_files': len(written) + 1}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('directory', type=Path)
    parser.add_argument('root_sha256'); parser.add_argument('output', type=Path)
    args = parser.parse_args(); print(json.dumps(export(args.directory, args.root_sha256, args.output), sort_keys=True))
