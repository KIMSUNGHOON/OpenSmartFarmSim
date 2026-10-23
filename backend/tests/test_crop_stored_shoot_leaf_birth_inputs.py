from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil

import pytest

from app.crop_stored_shoot_leaf_birth_inputs import LeafBirthInputsHold, build_leaf_birth_inputs_from_stored_shoot
from app import crop_declared_leaf_births as births, crop_leaf_population as population
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from app.crop_rational_morphology_artifact_reader import read_rational_morphology_frame


ROOT = Path(__file__).resolve().parents[2]
STEM_PROGRAM = json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes())
LEAF_PROGRAM = json.loads((ROOT/'fixtures/crop-leaf-area-software-program-v1.json').read_bytes())
FINAL = json.loads((ROOT/'web/public/morphology-rational-replay/frame-11.json').read_bytes())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def exact(value, unit='s'):
    value = Fraction(value)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': unit}


def fraction(value):
    return Fraction(int(value['numerator']), int(value['denominator']))


def inputs(first=4, between=2, base=5):
    prototype = LEAF_PROGRAM['initialization']['leaves'][0]['initialization']
    return {'input_id': 'stored-birth-probe', 'policy': {'origin': 'synthetic',
        'sequence_basis': 'explicit_emergence_schedule', 'policy_id': 'explicit-phase',
        'shoot_id': 'synthetic-shoot', 'schedule_id': 'synthetic-schedule-fractional-second',
        'first_generative_sequence': first, 'vegetative_between_generative': between},
        'leaf_profile': {**{key: deepcopy(prototype[key]) for key in ['curve', 'normalization', 'initial_area']},
            'base_temperature': {'value': base, 'unit': 'degC'}}}


def produce(directory, program):
    access = ContentAccess(os.getuid(), os.getgid())
    root = produce_rational_morphology_artifact(directory, access, program_raw=canonical(program))
    return directory, access, root


@pytest.fixture(scope='module')
def source(tmp_path_factory):
    result = produce(tmp_path_factory.mktemp('original-stored-shoot')/'blobs', STEM_PROGRAM)
    assert result[2] == FINAL['artifact_sha256']
    return result


def zero_base_program():
    p = deepcopy(STEM_PROGRAM); state = p['initial_state']; state['timeline_state']['base_temperature']['value'] = 0
    for node in state['internodes']:
        for clock in [node['length_state']['clock_state'], node['length_state']['anchor']['clock_state']]:
            clock['base_temperature']['value'] = 0
    return p


@pytest.fixture(scope='module')
def fractional_source(tmp_path_factory):
    p = zero_base_program(); t = p['initial_state']['timeline_state']
    t['next_threshold_exact'] = t['phyllochron_exact'] = exact(Fraction(1, 86400), 'degC_day')
    p['segments'] = [{'start_utc': t['started_at'], 'end_utc': '2026-10-01T00:00:03Z',
        'air_temperature': {'value': 3, 'unit': 'degC'}}]
    p['output_times'] = ['2026-10-01T00:00:01Z', '2026-10-01T00:00:02Z', '2026-10-01T00:00:03Z']
    return produce(tmp_path_factory.mktemp('fractional-stored-shoot')/'blobs', p)


def build(source, *, start=-1, end=11, value=None):
    return build_leaf_birth_inputs_from_stored_shoot(*source, start_index=start, end_index=end,
        inputs=inputs() if value is None else value)


def snapshot(directory):
    return {p.name: [p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns,
        sha256(p.read_bytes()).hexdigest()] for p in directory.iterdir()}


def reference_area(age, profile):
    with localcontext() as context:
        context.prec = 100
        values = profile['curve']['values']
        maximum, slope, midpoint = [Decimal.from_float(float(values[key]['value']))
            for key in ['maximum_area', 'steepness', 'inflection_age']]
        age = Decimal(age.numerator)/Decimal(age.denominator)
        return float(maximum/(1+(-slope*(age-midpoint)).exp()))


def test_original_stored_events_exact_times_parent_ids_and_independent_areas(source):
    before = snapshot(source[0]); p = inputs(); original = deepcopy(p)
    result = build(source, value=p)
    assert result['model_version'] == 'stored-shoot-leaf-birth-inputs-research-v1'
    assert result['scope'] == 'software_research_only' and result['claim_scope'] == 'synthetic_crop_math_only'
    assert result['gates'] == 'not_assessed' and result['stem_artifact_sha256'] == source[2]
    assert [(event['sequence'], event['kind']) for event in result['events']] == [
        (3, 'vegetative'), (4, 'generative'), (5, 'vegetative')]
    assert [event['elapsed_seconds_exact'] for event in result['events']] == [
        exact(Fraction(432000, 17)), exact(Fraction(864000, 17)), exact(Fraction(1296000, 17))]
    assert [event['attachment_internode_id'] for event in result['events']] == [
        node['internode_id'] for node in FINAL['internodes'][3:]]
    assert result['events'][1]['leaf_id'] is None
    selected = result['leaf_inputs']; assert len(selected['births']) == 2
    assert [leaf['attachment_internode_id'] for leaf in selected['births']] == [
        FINAL['internodes'][i]['internode_id'] for i in [3, 5]]
    calculated = births.create_declared_leaves(inputs=selected)
    for record, age in zip(calculated['new_leaves'], [Fraction(12), Fraction(2)], strict=True):
        assert record['state']['clock_state']['age_exact'] == exact(age, 'degC_day')
        assert record['state']['area_state']['area']['value'] == pytest.approx(reference_area(age, p['leaf_profile']), rel=1e-12)
    assert build(source, value=p) == result and p == original and snapshot(source[0]) == before
    selected['births'][0]['curve']['values']['maximum_area']['value'] = 99
    assert p == original


def advance_population(state, plan):
    p = plan['leaf_inputs']
    return population.advance_leaf_population(inputs={'input_id': p['input_id'], 'state': state,
        'segments': p['segments'], 'births': p['births']})['state']


@pytest.mark.parametrize('cut', [0, 3, 5, 7, 10])
def test_stored_boundary_split_same_declarations_ids_and_final_population(source, cut):
    whole = build(source); left = build(source, end=cut); right = build(source, start=cut)
    assert left['leaf_inputs']['births']+right['leaf_inputs']['births'] == whole['leaf_inputs']['births']
    assert left['events']+right['events'] == whole['events']
    initial = population.initialize_leaf_population(inputs={'input_id': 'initial',
        'initial_inventory': deepcopy(LEAF_PROGRAM['initialization'])})['state']
    assert advance_population(advance_population(initial, left), right) == advance_population(initial, whole)


def test_fractional_and_exact_end_events_occur_once_and_only_vegetative_positions(fractional_source):
    p = inputs(base=0); before = snapshot(fractional_source[0]); whole = build(fractional_source, end=2, value=p)
    left = build(fractional_source, end=0, value=p); right = build(fractional_source, start=0, end=2, value=p)
    assert left['leaf_inputs']['births']+right['leaf_inputs']['births'] == whole['leaf_inputs']['births']
    expected = [Fraction(1, 3), Fraction(1), Fraction(4, 3), Fraction(2), Fraction(7, 3), Fraction(3)]
    assert [fraction(b['emerged_elapsed_seconds_exact']) for b in whole['leaf_inputs']['births']] == expected
    calculated = births.create_declared_leaves(inputs=whole['leaf_inputs'])
    for record, age in zip(calculated['new_leaves'], [Fraction(n, 86400) for n in [8, 6, 5, 3, 2, 0]], strict=True):
        assert record['state']['clock_state']['age_exact'] == exact(age, 'degC_day')
        assert record['state']['area_state']['area']['value'] == pytest.approx(reference_area(age, p['leaf_profile']), rel=1e-12)
    assert calculated['new_leaves'][-1]['advancement_input_sha256'] is None
    assert snapshot(fractional_source[0]) == before


def test_no_new_events_and_all_generative_do_not_create_leaves(source):
    assert build(source, end=0)['leaf_inputs']['births'] == []
    result = build(source, value=inputs(0, 0))
    assert len(result['events']) == 3 and result['leaf_inputs']['births'] == []
    assert births.create_declared_leaves(inputs=result['leaf_inputs'])['new_leaves'] == []


@pytest.mark.parametrize('change', ['shoot', 'schedule', 'missing-profile', 'extra-profile', 'area', 'unit',
    'curve-origin', 'post-birth-below-base', 'extra-input', 'missing-policy', 'nonfinite'])
def test_unverified_policy_profile_and_domain_hold_without_input_mutation(source, change):
    p = inputs()
    if change == 'shoot': p['policy']['shoot_id'] = 'another-shoot'
    elif change == 'schedule': p['policy']['schedule_id'] = 'another-schedule'
    elif change == 'missing-profile': del p['leaf_profile']['initial_area']
    elif change == 'extra-profile': p['leaf_profile']['rank_fit'] = 'unverified'
    elif change == 'area': p['leaf_profile']['initial_area']['value'] *= 2
    elif change == 'unit': p['leaf_profile']['base_temperature']['unit'] = 'K'
    elif change == 'curve-origin': p['leaf_profile']['curve']['origin'] = 'observed'
    elif change == 'post-birth-below-base': p['leaf_profile']['base_temperature']['value'] = 23
    elif change == 'extra-input': p['implicit_leaf'] = True
    elif change == 'missing-policy': del p['policy']
    else: p['leaf_profile']['initial_area']['value'] = float('inf')
    original = deepcopy(p)
    with pytest.raises(LeafBirthInputsHold): build(source, value=p)
    assert p == original


def test_invalid_unused_profile_is_not_accepted_in_an_empty_interval(source):
    p = inputs(); p['leaf_profile']['initial_area']['value'] *= 2
    with pytest.raises(LeafBirthInputsHold, match='INITIAL_AREA_HOLD'): build(source, end=0, value=p)


@pytest.mark.parametrize('start,end', [(-2, 1), (-1, -1), (0, 0), (2, 1), (-1, 12), (True, 2), (-1, True), (0.0, 2), (-1, '2')])
def test_actual_selected_storage_interval_required(source, start, end):
    with pytest.raises(LeafBirthInputsHold): build(source, start=start, end=end)


def test_builder_cannot_advance_stem_leaf_or_population_or_access_DB_CLI_or_write(source, monkeypatch):
    from app import crop_rational_shoot_inventory as shoot, crop_rational_new_internodes as new
    from app import crop_rational_internode_length as length, crop_rational_leaf_area as leaf
    from app.job_store import JobStore
    import psycopg, subprocess
    before = snapshot(source[0]); calls = []
    def forbidden(*args, **kwargs): calls.append(1); raise AssertionError('input builder crossed calculation/storage boundary')
    for module, name in [(shoot, 'advance_rational_shoot_internode_inventory'),
        (new, 'create_rational_internodes_from_shoot_events'), (length, 'advance_rational_internode_length'),
        (leaf, 'advance_rational_leaf_area'), (population, 'advance_leaf_population'),
        (births, 'create_declared_leaves'), (MorphologyBlobStore, 'put'), (JobStore, 'connect'),
        (psycopg, 'connect'), (subprocess, 'run'), (subprocess, 'Popen')]:
        monkeypatch.setattr(module, name, forbidden)
    original_open = os.open
    def readonly(path, flags, *args, **kwargs):
        if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND): return forbidden()
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(os, 'open', readonly)
    result = build(source)
    assert len(result['leaf_inputs']['births']) == 2 and calls == [] and snapshot(source[0]) == before


def modified_endpoint(source, directory, change):
    shutil.copytree(source[0], directory)
    manifest = json.loads((directory/source[2]).read_bytes()); descriptor = manifest['samples'][-1]
    result = json.loads((directory/descriptor['result_sha256']).read_bytes()); state = result['state']
    if change == 'schedule': state['timeline_state']['schedule_id'] = 'changed-at-end'
    elif change == 'removed-new':
        state['internodes'].pop(); state['timeline_state']['next_sequence'] -= 1; result['step_receipts'].pop()
    elif change == 'time':
        node = state['internodes'][-1]
        for clock in [node['length_state']['clock_state'], node['length_state']['anchor']['clock_state']]:
            clock['emerged_elapsed_seconds_exact'] = exact(fraction(clock['emerged_elapsed_seconds_exact'])-Fraction(1, 17))
    else:
        node = state['internodes'][0 if change == 'old-ID' else -1]
        for clock in [node['length_state']['clock_state'], node['length_state']['anchor']['clock_state']]:
            clock['internode_id'] = 'replaced-parent-ID'
    with MorphologyBlobStore(directory, source[1], write=True) as store:
        raw = canonical(result); descriptor.update(result_sha256=store.put(raw, maximum=2*1024**2),
            result_bytes=len(raw), state_sha256=sha256(canonical(state)).hexdigest())
        manifest['terminal_state_sha256'] = descriptor['state_sha256']
        root = store.put(canonical(manifest), maximum=2*1024**2)
    return directory, source[1], root


@pytest.mark.parametrize('change', ['schedule', 'removed-new', 'time', 'old-ID', 'new-ID'])
def test_rehashed_readable_endpoint_cannot_change_clock_events_or_parent_identity(source, tmp_path, change):
    before = snapshot(source[0]); changed = modified_endpoint(source, tmp_path/'changed', change)
    assert read_rational_morphology_frame(*changed, index=11)['artifact_sha256'] == changed[2]
    with pytest.raises(LeafBirthInputsHold): build(changed)
    assert snapshot(source[0]) == before


def test_unknown_root_and_changed_blob_are_refused(source, tmp_path):
    with pytest.raises(LeafBirthInputsHold): build((source[0], source[1], '0'*64))
    directory = tmp_path/'changed'; shutil.copytree(source[0], directory)
    manifest = json.loads((directory/source[2]).read_bytes()); file = directory/manifest['samples'][-1]['result_sha256']
    file.write_bytes(file.read_bytes()+b' ')
    with pytest.raises(LeafBirthInputsHold): build((directory, source[1], source[2]))


@pytest.mark.parametrize('change', ['forcing', 'rights'])
def test_rehashed_program_change_cannot_bypass_rights_or_original_endpoint(source, tmp_path, change):
    directory = tmp_path/'changed-program'; shutil.copytree(source[0], directory)
    manifest = json.loads((directory/source[2]).read_bytes())
    program = json.loads((directory/manifest['program_sha256']).read_bytes())
    if change == 'forcing': program['segments'][0]['air_temperature']['value'] = 23
    else: program['rights']['use'] = False
    with MorphologyBlobStore(directory, source[1], write=True) as store:
        raw = canonical(program); manifest.update(program_sha256=store.put(raw, maximum=16*1024**2),
            program_bytes=len(raw), program_rights=program['rights'])
        root = store.put(canonical(manifest), maximum=128*1024)
    if change == 'forcing': assert read_rational_morphology_frame(directory, source[1], root, index=11)
    with pytest.raises(LeafBirthInputsHold, match='TIMELINE_HOLD' if change == 'forcing' else 'RIGHTS_HOLD'):
        build((directory, source[1], root))


def test_original_endpoint_is_rechecked_after_classification(source, tmp_path, monkeypatch):
    from app import crop_phytomer_kind as kinds
    directory = tmp_path/'late-change'; shutil.copytree(source[0], directory)
    manifest = json.loads((directory/source[2]).read_bytes()); original = kinds.classify_phytomer_sequences
    changed = []
    def late(*, inputs):
        result = original(inputs=inputs)
        if inputs['sequences']:
            file = directory/manifest['samples'][-1]['result_sha256']; file.write_bytes(file.read_bytes()+b' ')
            changed.append(True)
        return result
    monkeypatch.setattr(kinds, 'classify_phytomer_sequences', late)
    with pytest.raises(LeafBirthInputsHold, match='HASH_HOLD'): build((directory, source[1], source[2]))
    assert changed == [True]


def test_only_post_birth_air_is_checked_against_the_separate_leaf_base(tmp_path):
    program = zero_base_program(); timeline = program['initial_state']['timeline_state']
    timeline['next_threshold_exact'] = timeline['phyllochron_exact'] = exact(1, 'degC_day')
    program['segments'] = [
        {'start_utc': timeline['started_at'], 'end_utc': '2026-10-01T12:00:00Z',
            'air_temperature': {'value': 0, 'unit': 'degC'}},
        {'start_utc': '2026-10-01T12:00:00Z', 'end_utc': '2026-10-02T00:00:00Z',
            'air_temperature': {'value': 10, 'unit': 'degC'}}]
    program['output_times'] = ['2026-10-01T12:00:00Z', '2026-10-02T00:00:00Z']
    source = produce(tmp_path/'cold-before-birth', program); p = inputs(base=5)
    result = build(source, end=1, value=p)
    assert [fraction(e['emerged_elapsed_seconds_exact']) for e in result['leaf_inputs']['births']] == [
        Fraction(51840), Fraction(69120), Fraction(77760)]
    calculated = births.create_declared_leaves(inputs=result['leaf_inputs'])
    for record, age in zip(calculated['new_leaves'], [Fraction(2), Fraction(1), Fraction(1, 2)], strict=True):
        assert record['state']['clock_state']['age_exact'] == exact(age, 'degC_day')
        assert record['state']['area_state']['area']['value'] == pytest.approx(reference_area(age, p['leaf_profile']), rel=1e-12)


def test_512_events_and_leaves_and_invalid_513_source_are_all_or_hold(tmp_path):
    program = zero_base_program(); state = program['initial_state']; state['internodes'] = []
    state['inventory_start_sequence'] = state['timeline_state']['next_sequence'] = 0
    state['timeline_state']['next_threshold_exact'] = state['timeline_state']['phyllochron_exact'] = exact(Fraction(1, 512), 'degC_day')
    program['segments'] = [{'start_utc': state['timeline_state']['started_at'], 'end_utc': '2026-10-02T00:00:00Z',
        'air_temperature': {'value': 1, 'unit': 'degC'}}]
    program['output_times'] = ['2026-10-02T00:00:00Z']
    source = produce(tmp_path/'capacity-source', program)
    result = build(source, end=0, value=inputs(first=2**31-1, base=0))
    assert len(result['events']) == len(result['leaf_inputs']['births']) == 512
    assert len(canonical(result)) <= 2*1024**2
    assert len({item['leaf_id'] for item in result['leaf_inputs']['births']}) == 512
    assert result['leaf_inputs']['births'][-1]['emerged_elapsed_seconds_exact'] == exact(86400)
    manifest = json.loads((source[0]/source[2]).read_bytes()); descriptor = manifest['samples'][0]
    invalid = json.loads((source[0]/descriptor['result_sha256']).read_bytes()); state = invalid['state']
    extra = deepcopy(state['internodes'][-1]); extra['sequence'] = 512
    state['internodes'].append(extra); state['timeline_state']['next_sequence'] = 513
    invalid['step_receipts'].append({**deepcopy(invalid['step_receipts'][-1]), 'sequence': 512})
    with MorphologyBlobStore(source[0], source[1], write=True) as store:
        raw = canonical(invalid); descriptor.update(result_sha256=store.put(raw, maximum=2*1024**2),
            result_bytes=len(raw), state_sha256=sha256(canonical(state)).hexdigest())
        manifest['terminal_state_sha256'] = descriptor['state_sha256']
        invalid_root = store.put(canonical(manifest), maximum=128*1024)
    with pytest.raises(LeafBirthInputsHold):
        build((source[0], source[1], invalid_root), end=0, value=inputs(first=2**31-1, base=0))


def test_input_payload_budget_is_enforced_before_profile_parsing(source):
    p = inputs(); p['leaf_profile']['curve']['profile_id'] = 'x'*(2*1024**2)
    with pytest.raises(LeafBirthInputsHold, match='CAPACITY_HOLD'): build(source, value=p)
