"""Build the navigation fix on the existing preview's immutable web source."""
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

BASE = '2aa45fa7bc219a02e6a322ca095b0e726fad82da'
SOURCES = ('src/App.tsx', 'src/CropExecutionWorkspace.tsx',
           'src/JointCropClimateExecution.tsx', 'src/GreenhouseVentilationExecution.tsx')
OLD = "      {view==='crop-execution'&&<Suspense fallback={<p role=\"status\">계산 상태 화면 준비 중…</p>}><CropExecution api={api}/></Suspense>}"
NEW = "      <RetainedWorkspace active={view==='crop-execution'}><CropExecution api={api} active={view==='crop-execution'}/></RetainedWorkspace>"


def pins(directory):
    return {str(p.relative_to(directory)): sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--finalize', action='store_true')
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    directory = args.directory.resolve()
    assert directory != repository and repository not in directory.parents
    if args.finalize:
        proof = json.loads((directory/'provenance.json').read_bytes())
        assert pins(directory/'web'/'src') == proof['prepared_src_sha256']
        delivery = directory/'delivery'
        delivery.mkdir()
        shutil.copytree(directory/'web'/'dist', delivery/'dist')
        proof['built_assets_sha256'] = pins(delivery/'dist')
        proof['build_verified'] = True
        (delivery/'provenance.json').write_text(json.dumps(proof, indent=2)+'\n')
        return
    directory.mkdir()
    archive = subprocess.check_output(['git', 'archive', BASE, 'web'], cwd=repository)
    with tarfile.open(fileobj=BytesIO(archive)) as stream:
        stream.extractall(directory, filter='data')
    web = directory/'web'
    before = pins(web)
    original = (web/'src/App.tsx').read_text()
    assert original.count(OLD) == 1 and (repository/'web/src/App.tsx').read_text().count(NEW) == 1
    (web/'src/App.tsx').write_text(original.replace(OLD, NEW))
    for name in SOURCES[1:]:
        shutil.copyfile(repository/'web'/name, web/name)
    for name in ('package.json', 'package-lock.json',
                 'e2e/connection-entry.spec.ts', 'e2e/connection-fixture.ts'):
        shutil.copyfile(repository/'web'/name, web/name)
    after = pins(web)
    allowed = {*SOURCES, 'package.json', 'package-lock.json',
               'e2e/connection-entry.spec.ts', 'e2e/connection-fixture.ts'}
    changed = {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)}
    assert changed <= allowed and set(SOURCES) <= changed
    assert json.loads((web/'package.json').read_bytes())['devDependencies']['vite'] == '8.3.3'
    proof = {'base_commit': BASE, 'fix_commit': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=repository).decode().strip(),
        'changed_files': sorted(changed), 'baseline_sha256': before,
        'prepared_sha256': after, 'prepared_src_sha256': pins(web/'src'),
        'canonical_source_sha256': {name: sha256((repository/'web'/name).read_bytes()).hexdigest()
                                    for name in SOURCES},
        'App_change': 'Only retain the execution workspace and pass its activity; retain all other frozen App bytes.',
        'new_model_deployed': False, 'G0_G4': 'not_assessed', 'build_verified': False}
    (directory/'provenance.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps({'base_commit': BASE, 'changed_files': sorted(changed)}))


if __name__ == '__main__':
    main()
