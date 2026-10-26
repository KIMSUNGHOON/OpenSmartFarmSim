"""Create new own-public synthetic runs; never open or reclassify private packets."""
import argparse
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app import crop_leaf_funded_birth_continuation as model
from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
from app.crop_leaf_funded_birth_artifact_reader import ROOT_CONSTANTS
from app.content_access import ContentAccess
from app.crop_morphology_artifact_reader import _canonical


def inputs_for(program, declaration, profiles):
    root = model.parent.prepare_context(program=program, step_seconds=declaration['step_seconds'],
                                         step_count=declaration['step_count'], **profiles)
    context = None; cp = model.parent.start(root); births = []
    for step in range(declaration['step_count']+1):
        if step:
            engine = model if context is not None else model.parent
            result = engine.advance_chunk(context if context is not None else root, cp, 1)
            if result['status'] == 'hold': raise ValueError('fixture prefix held: '+str(result['hold']))
            cp = result['checkpoint']
        for _ in range(declaration['birth_steps'].count(step)):
            index = len(births); leaf = deepcopy(program['leaves'][0])
            leaf.update(leaf_id=f'public-funded-leaf-{index}', thermal_age={'value': 0., 'unit': 'degC_day'},
                initial_area=model.short.old.leaf_area._area_at(Fraction(0), leaf['curve']),
                **{key: deepcopy(declaration['new_leaf_values'][key]) for key in ('initial_carbon', 'sink_weight', 'carbon_removal')})
            point = {'schema_version': 'leaf-funded-birth-point-input-v1', 'input_id': f'own-public-funding-{index}',
                'origin': 'synthetic', 'policy': model.point.POLICY,
                'context_sha256': context.root_sha256 if context is not None else root.root_sha256,
                'checkpoint_sha256': cp.sha256, 'at_elapsed_seconds_exact': model._exact(step, float(declaration['step_seconds'])),
                'model_floor_area': deepcopy(program['model_floor_area']), 'events': [{'event_id': f'public-funding-{index}',
                'attachment_internode_id': f'public-declared-internode-{index}',
                'incoming_temperature': deepcopy(declaration['new_leaf_values']['incoming_temperature']), 'leaf': leaf}]}
            engine = model if context is not None else model.parent
            raw = engine.checkpoint_bytes(context if context is not None else root, cp)
            births.append({'step_index': step, 'point_inputs': point})
            if context is None:
                context = model.prepare_context(parent_context=root, raw_parent_checkpoint=raw,
                                                 expected_parent_sha256=cp.sha256, inputs=point)
            else:
                context = model.adopt_births(context=context, raw_checkpoint=raw, expected_sha256=cp.sha256, inputs=point)
            cp = model.start(context)
    return {'schema_version': 'funded-leaf-artifact-input-v1', 'input_id': program['input_id'], 'origin': 'synthetic',
        'program': program, 'births': births, 'rights': deepcopy(declaration['rights']),
        **{key: declaration[key] for key in ('time_origin_utc', 'step_seconds', 'step_count')}}


def generate(output):
    declaration_raw = (ROOT/'fixtures/crop-leaf-funded-birth-web-declaration-v1.json').read_bytes()
    declaration = json.loads(declaration_raw)
    if declaration['rights']['redistribute'] is not True: raise ValueError('new explicit public declaration required')
    source_raw = (ROOT/declaration['source_reference']).read_bytes()
    if sha256(source_raw).hexdigest() != declaration['source_sha256']: raise ValueError('original owned fixture source required')
    source = json.loads(source_raw)
    output = Path(output); output.mkdir(mode=0o750)
    (output/'blobs').mkdir(mode=0o750); (output/'public').mkdir(mode=0o750)
    stock = model.parent.short.old.joint
    profiles = {name: kind((ROOT/'fixtures'/file).read_bytes()) for name, kind, file in (
        ('growth_profile', stock.carbon.source.ReferenceParameters, 'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile', stock.carbon.fruit.ReferenceFruitCohortParameters, 'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile', stock.carbon.transport.ReferenceFruitTransportParameters, 'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile', stock.exchange.ReferenceParameters, 'crop-canopy-exchange-reference-parameters-v1.json'))}
    spec = importlib.util.spec_from_file_location('funded_leaf_export', ROOT/'research/export-leaf-funded-birth-replay.py')
    exporter = importlib.util.module_from_spec(spec); spec.loader.exec_module(exporter)
    scenarios = {}
    for case in source['cases']:
        if case['case_id'] not in declaration['cases']: continue
        name = case['case_id']; inputs = inputs_for(deepcopy(case['program']), declaration, profiles)
        directory = output/'blobs'/name
        root = produce_funded_leaf_artifact(directory, ContentAccess(os.getuid(), os.getgid()), inputs_raw=_canonical(inputs), **profiles)
        scenarios[name] = exporter.export(directory, root, output/'public'/name)
    if set(scenarios) != set(declaration['cases']): raise ValueError('complete own fixture case set required')
    first = json.loads((output/'public'/next(iter(scenarios))/'root.json').read_bytes())
    register = {**ROOT_CONSTANTS, 'scenarios': scenarios, 'declaration_sha256': sha256(declaration_raw).hexdigest(),
                'code_sha256': first['code_sha256'], 'exporter_sha256': exporter.CODE_SHA256}
    (output/'fundedLeafReplayFixture.json').write_bytes(_canonical(register))
    return register


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('output', type=Path)
    args = parser.parse_args(); print(json.dumps(generate(args.output), sort_keys=True))
