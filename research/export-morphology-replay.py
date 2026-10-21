"""Export already stored, explicitly redistributable synthetic research frames."""
import argparse
from hashlib import sha256
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore
from app.crop_morphology_artifact_reader import read_morphology_frame, read_morphology_manifest
from app.thermal_run_store import _canonical


def export(directory, root_sha256, output):
    access = ContentAccess(os.getuid(), os.getgid())
    root = read_morphology_manifest(directory, access, root_sha256)
    if root['program_rights']['redistribute'] is not True:
        raise ValueError('RIGHTS_HOLD: public fixture requires redistribution right')
    output.mkdir(mode=0o750)
    frames = []
    for index, descriptor in enumerate(root['samples']):
        raw = _canonical(read_morphology_frame(directory, access, root_sha256, index=index))
        name = f'frame-{index}.json'
        (output / name).write_bytes(raw)
        frames.append({'index': index, 'at': descriptor['at'], 'path': name,
                       'sha256': sha256(raw).hexdigest(), 'bytes': len(raw),
                       'result_sha256': descriptor['result_sha256']})
    (output / 'root.json').write_bytes(_canonical(root))
    with MorphologyBlobStore(directory, access) as store:
        (output / 'input.json').write_bytes(store.get(root['program_sha256'], maximum=16 * 1024**2))
    index_raw = _canonical({'schema_version': 'morphology-public-fixture-v1',
        'scope': root['scope'], 'claim_scope': root['claim_scope'], 'gates': root['gates'],
        'artifact_sha256': root_sha256, 'program_sha256': root['program_sha256'],
        'frames': frames, 'model_versions': root['model_versions'],
        'rights': root['program_rights'], 'equation_reference': root['equation_reference']})
    (output / 'index.json').write_bytes(index_raw)
    return {'artifact_sha256': root_sha256, 'index_sha256': sha256(index_raw).hexdigest(),
            'frames': len(frames), 'public_files': len(list(output.iterdir()))}


if __name__ == '__main__':
    import json
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('artifact_directory', type=Path)
    p.add_argument('root_sha256')
    p.add_argument('output', type=Path)
    args = p.parse_args()
    print(json.dumps(export(args.artifact_directory, args.root_sha256, args.output), sort_keys=True))
