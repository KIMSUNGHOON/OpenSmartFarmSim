"""Create separate owned numerical QA graphs without changing existing source rights."""
import argparse
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app import crop_funded_event_state as candidate
from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from app.content_access import ContentAccess
from app.crop_morphology_artifact_reader import _canonical


def generate(output):
    raw = (ROOT/'fixtures/crop-funded-event-state-fixtures-v2.json').read_bytes()
    declaration = json.loads(raw)
    assert all(declaration['rights'][k] is True for k in ('use', 'display', 'redistribute'))
    sources = {}
    for name, descriptor in declaration['sources'].items():
        data = (ROOT/descriptor['path']).read_bytes()
        assert sha256(data).hexdigest() == descriptor['sha256']
        sources[name] = json.loads(data)
    output = Path(output)
    output.mkdir(mode=0o750)
    (output/'leaves').mkdir(mode=0o750)
    access = ContentAccess(os.getuid(), os.getgid())
    stem = deepcopy(sources['stem'])
    stem['rights'] = deepcopy(declaration['rights'])
    stem['program_id'] = 'own-funded-event-state-stem'
    stem['output_times'] = declaration['stem_output_times']
    stem['segments'][0]['end_utc'] = stem['output_times'][-1]
    stem_root = produce_rational_morphology_artifact(output/'stem', access, program_raw=_canonical(stem))
    profiles = {name: kind((ROOT/'fixtures'/file).read_bytes()) for name, kind, file in (
        ('growth_profile', candidate.event.Growth, 'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile', candidate.event.Cohort, 'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile', candidate.event.Transport, 'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile', candidate.event.Exchange, 'crop-canopy-exchange-reference-parameters-v1.json'))}
    spec = importlib.util.spec_from_file_location('owned_leaf_generator', ROOT/'research/generate-leaf-funded-birth-replay-fixtures.py')
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    birth = json.loads((ROOT/'fixtures/crop-leaf-funded-birth-web-declaration-v1.json').read_bytes())
    config = {**birth, **{k: deepcopy(declaration[k]) for k in ('rights', 'time_origin_utc', 'step_seconds', 'step_count', 'birth_steps')}}
    cases = []
    for index in declaration['case_indices']:
        inputs = generator.inputs_for(deepcopy(sources['leaf']['cases'][index]['program']), config, profiles)
        root = produce_funded_leaf_artifact(output/'leaves'/str(index), access, inputs_raw=_canonical(inputs), **profiles)
        cases.append({'case_index': index, 'leaf_root_sha256': root, 'stem_start_index': 0})
    register = {'declaration_sha256': sha256(raw).hexdigest(), 'stem_root_sha256': stem_root,
                'cases': cases, 'G0_G4': 'not_assessed'}
    (output/'register.json').write_bytes(_canonical(register))
    return register


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    print(json.dumps(generate(parser.parse_args().output), sort_keys=True))
