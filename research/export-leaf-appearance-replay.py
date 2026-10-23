"""Export immutable synthetic appearance provenance with both redistribution grants."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
from app.content_access import ContentAccess
from app.crop_leaf_appearance_artifact_reader import read_leaf_appearance_manifest, read_leaf_appearance_frame
from app.crop_leaf_appearance_program import MAX
from app.crop_rational_morphology_artifact_reader import read_rational_morphology_manifest
from app.crop_morphology_artifact_io import MorphologyBlobStore, _need
from app.crop_morphology_artifact_reader import _canonical


def _grants(root, stem):
    _need(root['program_rights']['redistribute'] is True and stem['program_rights']['redistribute'] is True,
          'RIGHTS_HOLD: source and stem redistribution grants required')


def _publish_index(output, raw):
    _need(len(raw) <= MAX, 'CAPACITY_HOLD: bounded public index required')
    temporary = output/'.index.pending'
    with temporary.open('xb') as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, output/'index.json')


def export(directory, root_sha256, output):
    directory, output = Path(directory), Path(output)
    _need(directory.resolve() != output.resolve() and directory.resolve() not in output.resolve().parents,
          'STORAGE_HOLD: public output must be outside immutable source')
    access = ContentAccess(os.getuid(), os.getgid())
    root = read_leaf_appearance_manifest(directory, access, root_sha256)
    stem = read_rational_morphology_manifest(directory, access, root['stem_artifact_sha256']); _grants(root, stem)
    output.mkdir(mode=0o750); written = []; frames = []
    def write(name, raw):
        _need(type(raw) is bytes and 0 < len(raw) <= MAX, 'CAPACITY_HOLD: bounded public bytes required')
        (output/name).write_bytes(raw)
        written.append({'path': name, 'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)})
    for index in range(root['sample_count']):
        frame = read_leaf_appearance_frame(directory, access, root_sha256, index=index)
        raw = _canonical(frame); name = f'frame-{index}.json'; write(name, raw)
        frames.append({'index': index, 'at': frame['at'], **written[-1], 'result_sha256': frame['result_sha256'],
            'binding_sha256': frame['binding_sha256'], 'stem_result_sha256': frame['stem']['result_sha256']})
    sources = {'root.json': root_sha256, 'input.json': root['source_program_sha256'],
        'preparation.json': root['preparation_sha256'], 'generated-input.json': root['generated_program_sha256'],
        'population-root.json': root['population_artifact_sha256'], 'stem-root.json': root['stem_artifact_sha256'],
        'stem-input.json': root['stem_program_sha256']}
    with MorphologyBlobStore(directory, access) as store:
        for name, digest in sources.items(): write(name, store.get(digest, maximum=MAX))
    latest = read_leaf_appearance_manifest(directory, access, root_sha256)
    latest_stem = read_rational_morphology_manifest(directory, access, root['stem_artifact_sha256']); _grants(latest, latest_stem)
    _need(_canonical(latest) == _canonical(root) and _canonical(latest_stem) == _canonical(stem),
          'HASH_HOLD: export source changed before publication')
    for descriptor in written:
        with (output/descriptor['path']).open('rb') as handle: raw = handle.read(MAX+1)
        _need(len(raw) == descriptor['bytes'] and sha256(raw).hexdigest() == descriptor['sha256'],
              'HASH_HOLD: written public bytes differ')
    public = {'schema_version': 'leaf-appearance-public-fixture-v1',
        **{key: root[key] for key in ('scope', 'claim_scope', 'gates', 'model_versions', 'display_policy')},
        'artifact_sha256': root_sha256,
        **{key: root[key] for key in ('source_program_sha256', 'preparation_sha256', 'generated_program_sha256',
            'population_artifact_sha256', 'stem_artifact_sha256', 'stem_program_sha256')},
        'rights': root['program_rights'], 'stem_rights': stem['program_rights'], 'frames': frames}
    raw = _canonical(public); _publish_index(output, raw)
    return {'artifact_sha256': root_sha256, 'index_sha256': sha256(raw).hexdigest(),
        'frames': len(frames), 'public_files': len(written)+1}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('directory', type=Path)
    parser.add_argument('root_sha256'); parser.add_argument('output', type=Path)
    args = parser.parse_args(); print(json.dumps(export(args.directory, args.root_sha256, args.output), sort_keys=True))
