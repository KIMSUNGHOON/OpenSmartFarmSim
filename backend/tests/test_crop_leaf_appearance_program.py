from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from app.crop_leaf_appearance_program import DISPLAY_POLICY, LeafAppearanceProgramHold, parse_leaf_appearance_program
from app import crop_leaf_appearance_preparation as preparation
from app.crop_leaf_appearance_preparation import LeafAppearancePreparationHold, prepare_leaf_appearance_program
from app import crop_leaf_population as population
from app import crop_leaf_population_artifact_producer as producer
from app import crop_leaf_population_artifact_reader as reader
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_stored_shoot_leaf_birth_inputs import (
    source, inputs as birth_inputs, canonical, exact, fraction, snapshot, reference_area, LEAF_PROGRAM,
    STEM_PROGRAM, produce, zero_base_program,
)


def program():
    p = birth_inputs()
    return {'schema_version': 'leaf-appearance-software-program-v1', 'origin': 'synthetic',
        'program_id': 'owned-appearance-probe',
        'rights': {**deepcopy(LEAF_PROGRAM['rights']), 'declaration_id': 'owned-appearance-probe', 'revision': 'r1'},
        'stem': deepcopy(LEAF_PROGRAM['stem']),
        'initialization': {'input_id': 'appearance-initial', 'initial_inventory': deepcopy(LEAF_PROGRAM['initialization'])},
        'policy': p['policy'], 'leaf_profile': p['leaf_profile'], 'display_policy': deepcopy(DISPLAY_POLICY)}


def prepare(source, p=None):
    return prepare_leaf_appearance_program(source[0], source[1], program_raw=canonical(program() if p is None else p))


def test_complete_program_initial_bindings_generated_declarations_and_repeat(source):
    p = program(); original = deepcopy(p); before = snapshot(source[0]); raw = canonical(p)
    assert parse_leaf_appearance_program(program_raw=raw) == p
    result = prepare(source, p)
    assert result['model_version'] == 'leaf-appearance-program-preparation-research-v1'
    assert result['scope'] == 'software_research_only' and result['gates'] == 'not_assessed'
    assert result['source_program_sha256'] == sha256(raw).hexdigest() and result['source_program_bytes'] == len(raw)
    assert [item['sequence'] for item in result['initial_bindings']] == [0, 1, 2]
    assert [item['leaf_id'] for item in result['initial_bindings']] == ['declared-leaf-0', 'declared-leaf-1', 'declared-leaf-2']
    generated = result['generated_program']
    assert generated['schema_version'] == 'leaf-population-software-program-v1'
    assert generated['initialization'] == p['initialization'] and generated['rights'] == p['rights']
    assert generated['display_policy'] == reader.POPULATION_DISPLAY_POLICY
    assert len(generated['births']) == 2 and generated['births'] == result['derivation']['leaf_inputs']['births']
    assert result['generated_program_sha256'] == sha256(canonical(generated)).hexdigest()
    assert result['initial_state_sha256'] == sha256(canonical(population.initialize_leaf_population(inputs=p['initialization'])['state'])).hexdigest()
    assert len(result['code_sha256']) == 32
    assert prepare(source, p) == result and p == original and snapshot(source[0]) == before
    result['generated_program']['initialization']['input_id'] = 'changed'
    assert p == original


def test_explicit_mixed_initial_phase_has_no_leaf_at_generative_position(source):
    p = program(); p['policy']['first_generative_sequence'] = 1
    leaves = p['initialization']['initial_inventory']['leaves']; leaves.pop(1)
    result = prepare(source, p)
    assert [(item['sequence'], item['kind'], item['leaf_id']) for item in result['initial_bindings']] == [
        (0, 'vegetative', 'declared-leaf-0'), (1, 'generative', None), (2, 'vegetative', 'declared-leaf-2')]
    assert [item['sequence'] for item in result['derivation']['events'] if item['leaf_id'] is not None] == [3, 5]


def test_generated_program_actual_stored_12_frames_47_independent_areas(source, tmp_path):
    p = program(); prepared = prepare(source, p); directory = tmp_path/'generated-population'
    raw = canonical(prepared['generated_program'])
    root = producer.produce_leaf_population_artifact(directory, source[1], stem_directory=source[0], program_raw=raw)
    manifest = reader.read_leaf_population_manifest(directory, source[1], root)
    assert manifest['program_sha256'] == prepared['generated_program_sha256']
    assert manifest['initial_state_sha256'] == prepared['initial_state_sha256']
    initial = p['initialization']['initial_inventory']['leaves']
    references = {item['initialization']['clock_state']['leaf_id']: (Fraction(0), item['initialization']) for item in initial}
    for event, birth_age in zip(prepared['generated_program']['births'], [Fraction(5), Fraction(15)], strict=True):
        references[event['leaf_id']] = (birth_age, p['leaf_profile'])
    areas = 0; counts = []
    for index in range(12):
        frame = reader.read_leaf_population_frame(directory, source[1], root, index=index)
        end_age = Fraction(17*(index+1), 12); counts.append(frame['tracked_leaf_count'])
        for item in frame['leaves']:
            birth_age, profile = references[item['leaf_id']]; age = end_age-birth_age
            assert item['age_exact'] == exact(age, 'degC_day')
            assert item['area']['value'] == pytest.approx(reference_area(age, profile), rel=1e-12, abs=0)
            areas += 1
    assert counts == [3,3,3,4,4,4,4,4,4,4,5,5] and areas == 47
    assert len(list(directory.iterdir())) == 40


@pytest.mark.parametrize('change', ['missing', 'duplicate-parent', 'order', 'unknown-parent', 'generative',
    'origin', 'at', 'birth', 'initial-base', 'future-ID-collision', 'profile-initial-area'])
def test_initial_policy_identity_and_supported_clock_scope(source, change):
    p = program(); initial = p['initialization']['initial_inventory']; leaves = initial['leaves']
    if change == 'missing': leaves.pop()
    elif change == 'duplicate-parent': leaves[1]['attachment_internode_id'] = leaves[0]['attachment_internode_id']
    elif change == 'order': leaves.reverse()
    elif change == 'unknown-parent': leaves[0]['attachment_internode_id'] = 'untracked-parent'
    elif change == 'generative': p['policy']['first_generative_sequence'] = 1
    elif change == 'origin':
        initial['time_origin_utc'] = '2026-10-02T00:00:00Z'
        for item in leaves: item['initialization']['clock_state']['time_origin_utc'] = initial['time_origin_utc']
    elif change == 'at':
        initial['at_elapsed_seconds_exact'] = exact(1)
        for item in leaves: item['initialization']['clock_state']['at_elapsed_seconds_exact'] = exact(1)
    elif change == 'birth': leaves[0]['initialization']['clock_state']['emerged_elapsed_seconds_exact'] = exact(1)
    elif change == 'initial-base': leaves[0]['initialization']['clock_state']['base_temperature']['value'] = 23
    elif change == 'profile-initial-area': p['leaf_profile']['initial_area']['value'] *= 2
    else:
        identifier = prepare(source)['generated_program']['births'][0]['leaf_id']
        leaves[0]['initialization']['clock_state']['leaf_id'] = identifier
    original = deepcopy(p)
    with pytest.raises(LeafAppearancePreparationHold): prepare(source, p)
    assert p == original


@pytest.mark.parametrize('field', ['ownership_asserted','access','store','use','transform','display'])
def test_required_source_rights_are_not_inferred(field):
    p = program(); p['rights'][field] = False
    with pytest.raises(LeafAppearanceProgramHold): parse_leaf_appearance_program(program_raw=canonical(p))


def test_no_redistribution_grant_is_needed_for_internal_preparation(source):
    p = program(); p['rights']['redistribute'] = False
    result = prepare(source, p)
    assert result['generated_program']['rights']['redistribute'] is False


@pytest.mark.parametrize('change', ['missing-policy','implicit-births','profile-extra','policy-bool','display',
    'origin','missing-first','noncanonical','nonfinite','budget','bool-display','missing-profile','empty-initial'])
def test_closed_input_scope_and_explicit_policy(change):
    p = program()
    if change == 'missing-policy': del p['policy']
    elif change == 'implicit-births': p['births'] = []
    elif change == 'profile-extra': p['leaf_profile']['rank_fit'] = 'unverified'
    elif change == 'policy-bool': p['policy']['first_generative_sequence'] = True
    elif change == 'display': p['display_policy']['leaf_count'] = 'predicted'
    elif change == 'origin': p['origin'] = 'observed'
    elif change == 'missing-first': del p['policy']['first_generative_sequence']
    elif change == 'bool-display': p['display_policy']['petiole_rachis_area_excluded'] = 1
    elif change == 'missing-profile': del p['leaf_profile']
    elif change == 'empty-initial': p['initialization']['initial_inventory']['leaves'] = []
    elif change == 'nonfinite': p['leaf_profile']['initial_area']['value'] = float('inf')
    elif change == 'budget': p['program_id'] = 'x'*(2*1024**2)
    raw = json.dumps(p).encode() if change in ('noncanonical','nonfinite') else canonical(p)
    with pytest.raises(LeafAppearanceProgramHold): parse_leaf_appearance_program(program_raw=raw)


@pytest.mark.parametrize('after', [1, 2])
def test_late_code_drift_refuses_preparation(source, monkeypatch, after):
    original = preparation._code_pins; calls = []
    def changed():
        value = original(); calls.append(1)
        if len(calls) > after: value[next(iter(value))] = '0'*64
        return value
    monkeypatch.setattr(preparation, '_code_pins', changed)
    with pytest.raises(LeafAppearancePreparationHold, match='CODE_HOLD'): prepare(source)


def test_parent_source_code_pin_must_match_current_dependency(source, tmp_path):
    directory = tmp_path/'different-code'; shutil.copytree(source[0], directory)
    manifest = json.loads((directory/source[2]).read_bytes()); manifest['code_sha256'][next(iter(manifest['code_sha256']))] = '0'*64
    with MorphologyBlobStore(directory, source[1], write=True) as store: root = store.put(canonical(manifest), maximum=128*1024)
    p = program(); p['stem']['artifact_sha256'] = root
    with pytest.raises(LeafAppearancePreparationHold, match='CODE_HOLD'): prepare((directory, source[1], root), p)


def test_late_middle_source_blob_change_is_not_deferred_to_producer(source, tmp_path, monkeypatch):
    directory = tmp_path/'late-middle'; shutil.copytree(source[0], directory)
    manifest = json.loads((directory/source[2]).read_bytes()); original = preparation.derive.build_leaf_birth_inputs_from_stored_shoot
    def late(*args, **kwargs):
        result = original(*args, **kwargs)
        file = directory/manifest['samples'][5]['result_sha256']; file.write_bytes(file.read_bytes()+b' ')
        return result
    monkeypatch.setattr(preparation.derive, 'build_leaf_birth_inputs_from_stored_shoot', late)
    with pytest.raises(LeafAppearancePreparationHold, match='HASH_HOLD'): prepare((directory, source[1], source[2]))


def test_preparation_never_advances_or_writes_or_launches_CLI(source, monkeypatch):
    from app import crop_declared_leaf_births as births, crop_rational_leaf_area as leaf
    from app import crop_rational_shoot_inventory as shoot
    from app.job_store import JobStore
    import psycopg
    calls = []
    def forbidden(*args, **kwargs): calls.append(1); raise AssertionError('preparation crossed execution boundary')
    for module, name in [(population,'advance_leaf_population'),(births,'create_declared_leaves'),
        (leaf,'advance_rational_leaf_area'),(shoot,'advance_rational_shoot_internode_inventory'),
        (producer,'produce_leaf_population_artifact'),(MorphologyBlobStore,'put'),(JobStore,'connect'),
        (psycopg,'connect'),(subprocess,'run'),(subprocess,'Popen')]: monkeypatch.setattr(module,name,forbidden)
    original_open = os.open
    def readonly(path, flags, *args, **kwargs):
        if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND): return forbidden()
        return original_open(path,flags,*args,**kwargs)
    monkeypatch.setattr(os,'open',readonly)
    assert len(prepare(source)['generated_program']['births']) == 2 and calls == []


def test_parser_fresh_process_has_no_growth_imports_DB_CLI_or_writes(tmp_path):
    file = tmp_path/'source.json'; file.write_bytes(canonical(program()))
    script = '''
import importlib.abc,json,os,sys
from pathlib import Path
import psycopg,subprocess
blocked={'app.crop_phytomer_kind','app.crop_leaf_population','app.crop_leaf_inventory','app.crop_rational_leaf_area',
    'app.crop_leaf_area','app.crop_leaf_expansion','app.crop_stored_shoot_leaf_birth_inputs','app.crop_leaf_appearance_preparation'}
class Forbid(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname in blocked:raise AssertionError('growth import '+fullname)
sys.meta_path.insert(0,Forbid())
from app.job_store import JobStore
def forbidden(*a,**kw):raise AssertionError('parser crossed IO boundary')
JobStore.connect=psycopg.connect=subprocess.run=subprocess.Popen=forbidden
original=os.open
def readonly(path,flags,*a,**kw):
    if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return forbidden()
    return original(path,flags,*a,**kw)
os.open=readonly
from app.crop_leaf_appearance_program import parse_leaf_appearance_program
value=parse_leaf_appearance_program(program_raw=Path(sys.argv[1]).read_bytes())
assert not blocked.intersection(sys.modules)
print(json.dumps({'passed':True,'program_id':value['program_id'],'growth_imports':0,'DB_CLI_writes':0}))
'''
    env = {**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1]), 'PYTHONDONTWRITEBYTECODE': '1'}
    result = subprocess.run([sys.executable,'-B','-c',script,str(file)],env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {'passed':True,'program_id':'owned-appearance-probe','growth_imports':0,'DB_CLI_writes':0}


@pytest.mark.parametrize('field', ['artifact_sha256', 'program_sha256'])
def test_original_parent_references_must_match_real_source(source, field):
    p = program(); p['stem'][field] = '0'*64
    assert parse_leaf_appearance_program(program_raw=canonical(p)) == p
    with pytest.raises(LeafAppearancePreparationHold): prepare(source, p)


def test_maximum_program_ID_does_not_require_an_overlong_derived_ID(source):
    p = program(); p['program_id'] = 'x'*200
    result = prepare(source, p)
    assert result['generated_program']['program_id'] == p['program_id']
    assert len(result['derivation']['leaf_inputs']['input_id']) == 64


@pytest.fixture(scope='module')
def resumed_source(source, tmp_path_factory):
    manifest = json.loads((source[0]/source[2]).read_bytes())
    state = json.loads((source[0]/manifest['samples'][0]['result_sha256']).read_bytes())['state']
    p = deepcopy(STEM_PROGRAM); p['initial_state'] = state
    p['segments'][0]['start_utc'] = state['timeline_state']['at']; p['output_times'] = p['output_times'][1:]
    return produce(tmp_path_factory.mktemp('resumed-appearance-parent')/'blobs', p)


def resumed_program(source):
    p = program(); manifest = json.loads((source[0]/source[2]).read_bytes())
    p['stem'] = {'artifact_sha256': source[2], 'program_sha256': manifest['program_sha256']}
    initial = p['initialization']['initial_inventory']; initial['at_elapsed_seconds_exact'] = exact(7200)
    for item in initial['leaves']:
        q = item['initialization']; q['clock_state']['at_elapsed_seconds_exact'] = exact(7200)
        q['clock_state']['age_exact'] = exact(Fraction(17, 12), 'degC_day')
        q['initial_area']['value'] = reference_area(Fraction(17, 12), q)
    return p


def test_initial_leaf_can_have_a_separate_explicit_thermal_clock(resumed_source):
    p = resumed_program(resumed_source); q = p['initialization']['initial_inventory']['leaves'][0]['initialization']
    q['clock_state']['base_temperature']['value'] = 10; q['clock_state']['age_exact'] = exact(1, 'degC_day')
    q['initial_area']['value'] = reference_area(Fraction(1), q)
    result = prepare(resumed_source, p)
    assert result['generated_program']['initialization'] == p['initialization']
    assert result['derivation']['start_elapsed_seconds_exact'] == exact(7200)


def test_different_initial_birth_is_rejected_even_when_each_clock_is_valid(resumed_source):
    p = resumed_program(resumed_source)
    p['initialization']['initial_inventory']['leaves'][0]['initialization']['clock_state']['emerged_elapsed_seconds_exact'] = exact(1)
    assert parse_leaf_appearance_program(program_raw=canonical(p)) == p
    population.initialize_leaf_population(inputs=p['initialization'])
    with pytest.raises(LeafAppearancePreparationHold, match='INITIAL_BINDING_HOLD'): prepare(resumed_source, p)


def test_actual_512_leaf_program_stays_within_total_population_and_payload_budgets(tmp_path):
    parent = zero_base_program(); timeline = parent['initial_state']['timeline_state']
    timeline['next_threshold_exact'] = timeline['phyllochron_exact'] = exact(Fraction(1, 509), 'degC_day')
    parent['segments'] = [{'start_utc': timeline['started_at'], 'end_utc': '2026-10-02T00:00:00Z',
        'air_temperature': {'value': 1, 'unit': 'degC'}}]
    parent['output_times'] = ['2026-10-02T00:00:00Z']; source = produce(tmp_path/'capacity-parent', parent)
    manifest = json.loads((source[0]/source[2]).read_bytes()); p = program()
    p['stem'] = {'artifact_sha256': source[2], 'program_sha256': manifest['program_sha256']}
    p['policy']['first_generative_sequence'] = 2**31-1; p['leaf_profile']['base_temperature']['value'] = 0
    for item in p['initialization']['initial_inventory']['leaves']:
        item['initialization']['clock_state']['base_temperature']['value'] = 0
    result = prepare(source, p)
    assert len(result['initial_bindings']) == 3 and len(result['generated_program']['births']) == 509
    assert len(canonical(result)) <= 2*1024**2
