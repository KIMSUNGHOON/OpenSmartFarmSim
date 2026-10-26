"""Produce fresh own-public boundary packets with the accepted numerical engine."""
import argparse
from copy import deepcopy
from fractions import Fraction
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app import crop_leaf_funded_birth_continuation as model
from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
from app.crop_morphology_artifact_reader import _canonical
from app.content_access import ContentAccess


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def batch(program, declaration, profiles, count):
    dt = declaration['step_seconds']; steps = declaration['step_count']
    root = model.parent.prepare_context(program=program, step_seconds=dt, step_count=steps, **profiles)
    cp = model.parent.start(root); events = []
    for index in range(count):
        leaf = deepcopy(program['leaves'][0]); leaf.update(leaf_id=f'n{index}',
            thermal_age={'value': 0., 'unit': 'degC_day'},
            initial_area=model.short.old.leaf_area._area_at(Fraction(0), leaf['curve']),
            **{key: deepcopy(declaration['new_leaf_values'][key]) for key in ('initial_carbon','sink_weight','carbon_removal')})
        events.append({'event_id': f'e{index}', 'attachment_internode_id': f's{index}',
            'incoming_temperature': deepcopy(declaration['new_leaf_values']['incoming_temperature']), 'leaf': leaf})
    point = {'schema_version': 'leaf-funded-birth-point-input-v1', 'input_id': 'public-boundary-point',
        'origin': 'synthetic', 'policy': model.point.POLICY, 'context_sha256': root.root_sha256,
        'checkpoint_sha256': cp.sha256, 'at_elapsed_seconds_exact': model._exact(0, float(dt)),
        'model_floor_area': deepcopy(program['model_floor_area']), 'events': events}
    return {'schema_version': 'funded-leaf-artifact-input-v1', 'input_id': program['input_id'], 'origin': 'synthetic',
        'program': program, 'births': [{'step_index': 0, 'point_inputs': point}],
        'rights': deepcopy(declaration['rights']), **{k: declaration[k] for k in ('time_origin_utc','step_seconds','step_count')}}


def generate(output):
    from hashlib import sha256
    generator = load('funded_generator', ROOT/'research/generate-leaf-funded-birth-replay-fixtures.py')
    exporter = load('funded_exporter', ROOT/'research/export-leaf-funded-birth-replay.py')
    declaration_raw = (ROOT/'fixtures/crop-leaf-funded-birth-web-declaration-v1.json').read_bytes()
    declaration = json.loads(declaration_raw)
    assert all(declaration['rights'][k] is True for k in ('use','display','redistribute'))
    source_raw = (ROOT/declaration['source_reference']).read_bytes(); assert sha256(source_raw).hexdigest() == declaration['source_sha256']
    program = json.loads(source_raw)['cases'][0]['program']; stock = model.parent.short.old.joint
    profiles = {name: kind((ROOT/'fixtures'/file).read_bytes()) for name, kind, file in (
        ('growth_profile', stock.carbon.source.ReferenceParameters, 'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile', stock.carbon.fruit.ReferenceFruitCohortParameters, 'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile', stock.carbon.transport.ReferenceFruitTransportParameters, 'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile', stock.exchange.ReferenceParameters, 'crop-canopy-exchange-reference-parameters-v1.json'))}
    output = Path(output); output.mkdir(mode=0o750); (output/'blobs').mkdir(mode=0o750); (output/'public').mkdir(mode=0o750)
    result = {}
    for name in ('minimum','maximum','fractional','same-time'):
        p = deepcopy(program); d = deepcopy(declaration)
        if name in ('minimum','maximum'):
            d.update(step_seconds=1., step_count=1)
            if name == 'minimum':
                # Software boundary: retain the declared first leaf and the same initial canopy temperature.
                share = p['leaves'][0]['initial_area']['value']/sum(x['initial_area']['value'] for x in p['leaves'])
                p['scenario']['climate_state']['canopy_sensible_energy']['value'] *= share
                p['leaves'] = p['leaves'][:1]
            inputs = batch(p, d, profiles, 1 if name == 'minimum' else 509)
        else:
            d.update(step_seconds=1/3, step_count=3, birth_steps=[1,3] if name == 'fractional' else [1,1,3])
            inputs = generator.inputs_for(p, d, profiles)
        directory = output/'blobs'/name
        root = produce_funded_leaf_artifact(directory, ContentAccess(os.getuid(), os.getgid()), inputs_raw=_canonical(inputs), **profiles)
        result[name] = exporter.export(directory, root, output/'public'/name)
    raw = _canonical({'declaration_sha256': sha256(declaration_raw).hexdigest(), 'scenarios': result})
    (output/'boundaries.json').write_bytes(raw)
    return json.loads(raw)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('output', type=Path)
    print(json.dumps(generate(parser.parse_args().output), sort_keys=True))
