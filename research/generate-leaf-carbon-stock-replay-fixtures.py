"""Reproduce the six original, explicitly shareable synthetic web fixtures.

Writes a new private base directory; only its public/ subtree and generated
TypeScript register are candidates for repository adoption after verification.
"""
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
from app import crop_leaf_carbon_stock_continuation as model
from app.crop_leaf_carbon_stock_artifact_producer import produce_leaf_carbon_stock_artifact
from app.crop_leaf_carbon_stock_artifact_reader import ROOT_CONSTANTS
from app.crop_morphology_artifact_reader import _canonical
from app.content_access import ContentAccess


def generate(output, *, boundaries_only=False):
    declaration = json.loads((ROOT/'fixtures/crop-leaf-carbon-stock-web-declaration-v1.json').read_bytes())
    source = (ROOT/'fixtures'/declaration['source_fixture']).read_bytes()
    assert sha256(source).hexdigest() == declaration['source_fixture_sha256']
    profiles = {name: kind((ROOT/'fixtures'/file).read_bytes()) for name, kind, file in (
        ('growth_profile', model.short.old.joint.carbon.source.ReferenceParameters, 'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile', model.short.old.joint.carbon.fruit.ReferenceFruitCohortParameters, 'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile', model.short.old.joint.carbon.transport.ReferenceFruitTransportParameters, 'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile', model.short.old.joint.exchange.ReferenceParameters, 'crop-canopy-exchange-reference-parameters-v1.json'))}
    spec = importlib.util.spec_from_file_location('leaf_stock_export', ROOT/'research/export-leaf-carbon-stock-replay.py')
    exporter = importlib.util.module_from_spec(spec); spec.loader.exec_module(exporter)
    output = Path(output); output.mkdir(mode=0o700); (output/'blobs').mkdir(); (output/'public').mkdir()
    scenarios = {}
    cases = json.loads(source)['cases']
    if boundaries_only:
        base = cases[0]['program']; cases = []
        total = sum(leaf['initial_carbon']['value'] for leaf in base['leaves'])
        for count in (1, 512):
            p = deepcopy(base); name = f'stock-boundary-{count}'
            p['input_id'] = p['scenario']['input_id'] = name
            p['leaves'] = [{**deepcopy(base['leaves'][0]), 'leaf_id': f'bounded-stock-{i}',
                'initial_carbon': {'value': total/count, 'unit': 'mg_CH2O/m2_floor'},
                'sink_weight': {'value': float(i % 7) if count > 1 else 1., 'unit': '1'}} for i in range(count)]
            p['model_floor_area']['value'] = count*.25/1.33
            cases.append({'case_id': name, 'program': p})
        p = deepcopy(base); p['input_id'] = p['scenario']['input_id'] = 'stock-boundary-fractional'
        cases.append({'case_id': 'stock-boundary-fractional', 'program': p})
    for case in cases:
        program = case['program']; name = case['case_id']
        inputs = {'schema_version': 'leaf-carbon-stock-artifact-input-v1', 'input_id': program['input_id'], 'origin': 'synthetic',
            'program': program, 'rights': declaration['cases'][next(iter(declaration['cases'])) if boundaries_only else name]['rights'], **{k: declaration[k] for k in ('time_origin_utc', 'step_seconds', 'step_count')}}
        if boundaries_only:
            inputs.update(step_seconds=1/3 if name.endswith('fractional') else .125,
                step_count=3 if name.endswith('fractional') else 1)
        directory = output/'blobs'/name
        root = produce_leaf_carbon_stock_artifact(directory, ContentAccess(os.getuid(), os.getgid()), inputs_raw=_canonical(inputs), **profiles)
        result = exporter.export(directory, root, output/'public'/name)
        scenarios[name] = {**{k: result[k] for k in ('artifact_sha256', 'index_sha256', 'frames')},
            'leaf_curve_sha256': {leaf['leaf_id']: leaf['curve_sha256'] for leaf in json.loads((output/'public'/name/'frame-0.json').read_bytes())['leaves']}}
    first = json.loads((output/'public'/next(iter(scenarios))/'root.json').read_bytes())
    context = json.loads((output/'public'/next(iter(scenarios))/'source-context.json').read_bytes())
    index = json.loads((output/'public'/next(iter(scenarios))/'index.json').read_bytes())
    register = {**ROOT_CONSTANTS, 'scenarios': scenarios, 'code_sha256': first['code_sha256'],
        'engine_identity': context['identity'], 'notice_sha256': first['sources']['license_notice']['sha256'],
        'exporter_sha256': index['exporter_sha256']}
    (output/'leafCarbonStockReplayFixture.ts').write_text('export const LEAF_CARBON_STOCK_FIXTURE = '+json.dumps(register, ensure_ascii=False, indent=2)+' as const;\n')
    return register


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('output', type=Path)
    parser.add_argument('--boundaries-only', action='store_true')
    args = parser.parse_args()
    print(json.dumps(generate(args.output, boundaries_only=args.boundaries_only), sort_keys=True))
