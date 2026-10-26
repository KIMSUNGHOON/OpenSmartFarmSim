"""New owned epoch test runs, never reclassifying existing private artifacts."""
import argparse
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app import crop_leaf_funded_birth_continuation as model
from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from app.crop_morphology_artifact_reader import _canonical
from app.content_access import ContentAccess


def generate(output):
    raw=(ROOT/'fixtures/crop-funded-shoot-epoch-fixtures-v1.json').read_bytes();d=json.loads(raw)
    assert all(d['rights'][k]is True for k in ('use','display','redistribute'))
    data={}
    for name,source in d['sources'].items():
        value=(ROOT/source['path']).read_bytes();assert sha256(value).hexdigest()==source['sha256'];data[name]=json.loads(value)
    output=Path(output);output.mkdir(mode=0o750);(output/'leaves').mkdir(mode=0o750)
    stem=data['stem'];stem['rights']=deepcopy(d['rights']);stem['program_id']='own-funded-shoot-history-v1'
    stem['output_times']=d['stem_output_times'];stem['segments'][0]['end_utc']=stem['output_times'][-1]
    access=ContentAccess(os.getuid(),os.getgid());stem_root=produce_rational_morphology_artifact(output/'stem',access,program_raw=_canonical(stem))
    joint=model.parent.short.old.joint
    profiles={name:kind((ROOT/'fixtures'/path).read_bytes())for name,kind,path in (
        ('growth_profile',joint.carbon.source.ReferenceParameters,'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile',joint.carbon.fruit.ReferenceFruitCohortParameters,'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile',joint.carbon.transport.ReferenceFruitTransportParameters,'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile',joint.exchange.ReferenceParameters,'crop-canopy-exchange-reference-parameters-v1.json'))}
    spec=importlib.util.spec_from_file_location('owned_funded_generator',ROOT/'research/generate-leaf-funded-birth-replay-fixtures.py')
    generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
    birth=json.loads((ROOT/'fixtures/crop-leaf-funded-birth-web-declaration-v1.json').read_bytes());cases=[]
    for case in d['cases']:
        declaration={**deepcopy(birth),'rights':deepcopy(d['rights']),'time_origin_utc':case['simulation_origin_utc'],
            'step_seconds':case['step_seconds'],'step_count':case['step_count'],'birth_steps':[0,case['step_count']//2]}
        inputs=generator.inputs_for(deepcopy(data['leaf']['cases'][case['case_index']]['program']),declaration,profiles)
        root=produce_funded_leaf_artifact(output/'leaves'/case['label'],access,inputs_raw=_canonical(inputs),**profiles)
        cases.append({**case,'leaf_root_sha256':root})
    register={'declaration_sha256':sha256(raw).hexdigest(),'stem_root_sha256':stem_root,'cases':cases,'G0_G4':'not_assessed'}
    (output/'register.json').write_bytes(_canonical(register));return register


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    print(json.dumps(generate(parser.parse_args().output),sort_keys=True))
