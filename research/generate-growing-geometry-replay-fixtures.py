"""Reproduce the six original, explicitly shareable synthetic web fixtures.

Writes a new private base directory; only its public/ subtree and generated
TypeScript register are candidates for repository adoption after verification.
"""
import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app import crop_growing_geometry_continuation as model
from app.crop_growing_geometry_artifact_producer import produce_growing_geometry_artifact
from app.crop_growing_geometry_artifact_reader import ROOT_CONSTANTS
from app.crop_morphology_artifact_reader import _canonical
from app.content_access import ContentAccess


def generate(output):
    declaration = json.loads((ROOT/'fixtures/crop-growing-geometry-web-declaration-v1.json').read_bytes())
    source = (ROOT/'fixtures'/declaration['source_fixture']).read_bytes()
    assert sha256(source).hexdigest() == declaration['source_fixture_sha256']
    profiles = {name: kind((ROOT/'fixtures'/file).read_bytes()) for name, kind, file in (
        ('growth_profile', model.short.joint.carbon.source.ReferenceParameters, 'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile', model.short.joint.carbon.fruit.ReferenceFruitCohortParameters, 'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile', model.short.joint.carbon.transport.ReferenceFruitTransportParameters, 'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile', model.short.joint.exchange.ReferenceParameters, 'crop-canopy-exchange-reference-parameters-v1.json'))}
    spec = importlib.util.spec_from_file_location('growing_export', ROOT/'research/export-growing-geometry-replay.py')
    exporter = importlib.util.module_from_spec(spec); spec.loader.exec_module(exporter)
    output = Path(output); output.mkdir(mode=0o700); (output/'blobs').mkdir(); (output/'public').mkdir()
    scenarios = {}
    for case in json.loads(source)['cases']:
        program = case['program']; name = case['case_id']
        inputs = {'schema_version': 'growing-geometry-artifact-input-v1', 'input_id': program['input_id'], 'origin': 'synthetic',
            'program': program, **{k: declaration[k] for k in ('rights', 'time_origin_utc', 'step_seconds', 'step_count')}}
        directory = output/'blobs'/name
        root = produce_growing_geometry_artifact(directory, ContentAccess(os.getuid(), os.getgid()), inputs_raw=_canonical(inputs), **profiles)
        result = exporter.export(directory, root, output/'public'/name)
        scenarios[name] = {k: result[k] for k in ('artifact_sha256', 'index_sha256', 'frames')}
    register = {**ROOT_CONSTANTS, 'scenarios': scenarios}
    (output/'growingGeometryReplayFixture.ts').write_text('export const GROWING_GEOMETRY_FIXTURE = '+json.dumps(register, ensure_ascii=False, indent=2)+' as const;\n')
    return register


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('output', type=Path)
    print(json.dumps(generate(parser.parse_args().output), sort_keys=True))
