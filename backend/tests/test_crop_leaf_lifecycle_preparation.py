from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import builtins
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from app import crop_leaf_lifecycle_preparation as preparation
from app import crop_leaf_lifecycle_program as program
from app import crop_leaf_lifecycle as lifecycle
from app import crop_leaf_appearance_preparation as appearance
from app import crop_leaf_population as population
from test_crop_leaf_appearance_program import program as appearance_program
from test_crop_stored_shoot_leaf_birth_inputs import source, canonical, exact, fraction, snapshot


def management(raw, removals=None):
    p = appearance_program()
    return {'schema_version': 'leaf-lifecycle-management-program-v1', 'origin': 'synthetic',
            'program_id': 'owned-lifecycle-management',
            'rights': {**deepcopy(p['rights']), 'declaration_id': 'owned-lifecycle-management'},
            'appearance_program_sha256': sha256(raw).hexdigest(), 'removals': [] if removals is None else removals,
            'display_policy': deepcopy(program.DISPLAY_POLICY)}


def removal(identifier, at, identity='owned-remove'):
    return {'schema_version': 'declared-whole-leaf-removal-event-v1', 'origin': 'synthetic',
            'action': 'remove_whole_leaf', 'event_id': identity, 'leaf_id': identifier,
            'time_origin_utc': '2026-10-01T00:00:00Z', 'at_elapsed_seconds_exact': exact(at)}


def prepare(source, p=None, m=None):
    raw = canonical(appearance_program() if p is None else p)
    return preparation.prepare_leaf_lifecycle_program(source[0], source[1], appearance_program_raw=raw,
        management_raw=canonical(management(raw) if m is None else m))


def test_original_preparation_initial_state_forcing_code_and_rights_remain_bound(source):
    raw = canonical(appearance_program()); m = management(raw); before = snapshot(source[0])
    original = appearance.prepare_leaf_appearance_program(source[0], source[1], program_raw=raw)
    result = prepare(source, m=m)
    assert result['appearance_preparation'] == original
    assert result['appearance_program_sha256'] == sha256(raw).hexdigest()
    assert result['management_program_sha256'] == sha256(canonical(m)).hexdigest()
    assert result['appearance_preparation_sha256'] == sha256(canonical(original)).hexdigest()
    assert result['lifecycle_initialization_sha256'] == sha256(canonical(result['lifecycle_initialization'])).hexdigest()
    initialized = lifecycle.initialize_leaf_lifecycle(inputs=result['lifecycle_initialization'])
    assert result['initial_state_sha256'] == sha256(canonical(initialized['state'])).hexdigest()
    initial = population.initialize_leaf_population(inputs=original['generated_program']['initialization'])['state']
    assert result['lifecycle_initialization']['population_state'] == initial
    assert result['lifecycle_initialization']['births'] == original['generated_program']['births']
    assert result['forcing'] == original['derivation']['leaf_inputs']['segments']
    assert result['start_elapsed_seconds_exact'] == result['forcing'][0]['start_elapsed_seconds_exact']
    assert result['end_elapsed_seconds_exact'] == result['forcing'][-1]['end_elapsed_seconds_exact']
    assert result['stem'] == appearance_program()['stem']
    assert result['source_rights']['appearance'] == appearance_program()['rights']
    assert result['source_rights']['management'] == m['rights']
    assert all(result['code_sha256'][name] == pin for name, pin in original['code_sha256'].items())
    assert (result['scope'], result['claim_scope'], result['gates']) == ('software_research_only', 'synthetic_crop_math_only', 'not_assessed')
    assert prepare(source, m=m) == result and snapshot(source[0]) == before


@pytest.mark.parametrize('at', [Fraction(0), Fraction(1, 3), Fraction(86400)])
def test_existing_leaf_removal_at_initial_fractional_and_end_times_is_fixed(source, at):
    raw = canonical(appearance_program()); records = [removal('declared-leaf-0', at)]
    result = prepare(source, m=management(raw, records))
    assert result['lifecycle_initialization']['removals'] == records
    assert lifecycle.initialize_leaf_lifecycle(inputs=result['lifecycle_initialization'])['removed_leaf_count'] == int(at == 0)


def test_automatic_birth_removal_can_match_exact_original_emergence(source):
    raw = canonical(appearance_program()); original = appearance.prepare_leaf_appearance_program(source[0], source[1], program_raw=raw)
    birth = original['generated_program']['births'][0]
    record = removal(birth['leaf_id'], fraction(birth['emerged_elapsed_seconds_exact']))
    result = prepare(source, m=management(raw, [record]))
    assert result['lifecycle_initialization']['births'] == original['generated_program']['births']
    assert result['lifecycle_initialization']['removals'] == [record]
    assert result['appearance_preparation']['initial_bindings'] == original['initial_bindings']


@pytest.mark.parametrize('target', ['appearance', 'management'])
def test_no_redistribution_is_preserved_without_inventing_grants(source, target):
    p = appearance_program()
    if target == 'appearance': p['rights']['redistribute'] = False
    raw = canonical(p); m = management(raw)
    if target == 'management': m['rights']['redistribute'] = False
    result = prepare(source, p, m)
    assert result['source_rights'][target]['redistribute'] is False


@pytest.mark.parametrize('fault', ['appearance-sha', 'unknown-ID', 'before-new-birth', 'after-horizon', 'wrong-origin'])
def test_wrong_source_identity_emergence_or_stored_horizon_holds(source, fault):
    raw = canonical(appearance_program()); m = management(raw, [removal('declared-leaf-0', Fraction(1, 3))])
    if fault == 'appearance-sha': m['appearance_program_sha256'] = '0' * 64
    elif fault == 'unknown-ID': m['removals'][0]['leaf_id'] = 'another-program-leaf'
    elif fault == 'before-new-birth':
        old = appearance.prepare_leaf_appearance_program(source[0], source[1], program_raw=raw)
        m['removals'][0]['leaf_id'] = old['generated_program']['births'][0]['leaf_id']; m['removals'][0]['at_elapsed_seconds_exact'] = exact(0)
    elif fault == 'after-horizon': m['removals'][0]['at_elapsed_seconds_exact'] = exact(86401)
    elif fault == 'wrong-origin': m['removals'][0]['time_origin_utc'] = '2026-10-02T00:00:00Z'
    before = deepcopy(m)
    with pytest.raises(preparation.LeafLifecyclePreparationHold): prepare(source, m=m)
    assert m == before


@pytest.mark.parametrize('fault', ['extra', 'origin', 'missing', 'bad-sha', 'display', 'bool-display',
                                  'none-events', 'unknown-schema', 'partial-action', 'extra-event',
                                  'duplicate-leaf', 'duplicate-event', 'unhashable-ID', 'unit', 'non-reduced',
                                  'boolean-time', 'bad-UTC', 'nan', 'noncanonical', '2MiB'])
def test_management_parser_rejects_unsupported_scope_types_and_payloads(fault):
    raw = canonical(appearance_program()); p = management(raw, [removal('leaf-0', Fraction(1, 3)), removal('leaf-1', Fraction(2), 'other')])
    if fault == 'extra': p['recommendation'] = True
    elif fault == 'origin': p['origin'] = 'observed'
    elif fault == 'missing': del p['appearance_program_sha256']
    elif fault == 'bad-sha': p['appearance_program_sha256'] = '0' * 63
    elif fault == 'display': p['display_policy']['leaf_count'] = 'predicted'
    elif fault == 'bool-display': p['display_policy']['petiole_rachis_area_excluded'] = 1
    elif fault == 'none-events': p['removals'] = None
    elif fault == 'unknown-schema': p['removals'][0]['schema_version'] = 'automatic-v1'
    elif fault == 'partial-action': p['removals'][0]['action'] = 'remove_half_leaf'
    elif fault == 'extra-event': p['removals'][0]['reason'] = 'model-inferred'
    elif fault == 'duplicate-leaf': p['removals'][1]['leaf_id'] = 'leaf-0'
    elif fault == 'duplicate-event': p['removals'][1]['event_id'] = p['removals'][0]['event_id']
    elif fault == 'unhashable-ID': p['removals'][0]['leaf_id'] = []
    elif fault == 'unit': p['removals'][0]['at_elapsed_seconds_exact']['unit'] = 'day'
    elif fault == 'non-reduced': p['removals'][0]['at_elapsed_seconds_exact'].update(numerator='2', denominator='2')
    elif fault == 'boolean-time': p['removals'][0]['at_elapsed_seconds_exact']['numerator'] = True
    elif fault == 'bad-UTC': p['removals'][0]['time_origin_utc'] = '2026-10-01T00:00:00+00:00'
    elif fault == 'nan': p['removals'][0]['at_elapsed_seconds_exact']['numerator'] = float('nan')
    elif fault == '2MiB': p['program_id'] = 'x' * (2 * 1024**2)
    encoded = json.dumps(p).encode() if fault in ('nan', 'noncanonical') else canonical(p)
    with pytest.raises(program.LeafLifecycleProgramHold): program.parse_leaf_lifecycle_management_program(program_raw=encoded)


@pytest.mark.parametrize('target', ['appearance', 'management'])
@pytest.mark.parametrize('field', ['ownership_asserted', 'access', 'store', 'use', 'transform', 'display'])
def test_each_source_requires_its_own_rights(source, target, field):
    p = appearance_program()
    if target == 'appearance': p['rights'][field] = False
    raw = canonical(p); m = management(raw)
    if target == 'management': m['rights'][field] = False
    with pytest.raises(preparation.LeafLifecyclePreparationHold, match='RIGHTS_HOLD'): prepare(source, p, m)


@pytest.mark.parametrize('fault', ['stem-root', 'stem-program', 'shoot', 'schedule', 'initial-attachment', 'initial-base'])
def test_matching_management_hash_cannot_approve_wrong_original_stem_or_policy(source, fault):
    p = appearance_program()
    if fault == 'stem-root': p['stem']['artifact_sha256'] = '0' * 64
    elif fault == 'stem-program': p['stem']['program_sha256'] = '0' * 64
    elif fault == 'shoot': p['policy']['shoot_id'] = 'other-shoot'
    elif fault == 'schedule': p['policy']['schedule_id'] = 'other-schedule'
    elif fault == 'initial-attachment': p['initialization']['initial_inventory']['leaves'][0]['attachment_internode_id'] = 'other'
    elif fault == 'initial-base': p['initialization']['initial_inventory']['leaves'][0]['initialization']['clock_state']['base_temperature']['value'] = 23
    with pytest.raises(preparation.LeafLifecyclePreparationHold): prepare(source, p, management(canonical(p)))


def test_parser_512_declarations_and_513_limit_are_separate_from_source_binding():
    raw = canonical(appearance_program()); p = management(raw, [removal('leaf-' + str(i), Fraction(i), 'event-' + str(i)) for i in range(512)])
    assert len(program.parse_leaf_lifecycle_management_program(program_raw=canonical(p))['removals']) == 512
    p['removals'].append(removal('extra', Fraction(513), 'extra'))
    with pytest.raises(program.LeafLifecycleProgramHold, match='512'):
        program.parse_leaf_lifecycle_management_program(program_raw=canonical(p))


def test_file_custodian_owner_must_match_before_preparation(source):
    from app.content_access import ContentAccess
    access = ContentAccess(source[1].owner_uid + 1, source[1].reader_gid)
    raw = canonical(appearance_program())
    with pytest.raises(preparation.LeafLifecyclePreparationHold, match='STORAGE_HOLD'):
        preparation.prepare_leaf_lifecycle_program(source[0], access, appearance_program_raw=raw,
                                                   management_raw=canonical(management(raw)))


def test_new_code_drift_is_checked_after_initialization(source, monkeypatch):
    original = preparation._code_pins; calls = []
    def changed():
        result = original(); calls.append(1)
        if len(calls) > 1: result['backend/app/crop_leaf_lifecycle.py'] = '0' * 64
        return result
    monkeypatch.setattr(preparation, '_code_pins', changed)
    with pytest.raises(preparation.LeafLifecyclePreparationHold, match='CODE_HOLD'): prepare(source)


@pytest.mark.parametrize('field', ['generated_program_sha256', 'derivation_sha256', 'initial_state_sha256', 'initial_bindings_sha256'])
def test_late_original_preparation_drift_is_not_deferred_to_producer(source, monkeypatch, field):
    original = appearance.prepare_leaf_appearance_program; calls = []
    def changed(*args, **kwargs):
        result = original(*args, **kwargs); calls.append(1)
        if len(calls) > 1: result[field] = '0' * 64
        return result
    monkeypatch.setattr(appearance, 'prepare_leaf_appearance_program', changed)
    with pytest.raises(preparation.LeafLifecyclePreparationHold, match='HASH_HOLD'): prepare(source)


@pytest.mark.parametrize('fault', ['sample-bytes', 'sample-mode', 'directory-replacement'])
def test_source_changes_after_initial_preparation_are_rejected_before_return(source, tmp_path, monkeypatch, fault):
    directory = tmp_path/'source'; shutil.copytree(source[0], directory)
    manifest = json.loads((directory/source[2]).read_bytes()); original = lifecycle.initialize_leaf_lifecycle
    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        if fault == 'directory-replacement':
            held = tmp_path/'held'; directory.rename(held); shutil.copytree(held, directory)
        else:
            file = directory/manifest['samples'][5]['result_sha256']
            if fault == 'sample-bytes': file.write_bytes(file.read_bytes() + b' ')
            else: file.chmod(0o600)
        return result
    monkeypatch.setattr(lifecycle, 'initialize_leaf_lifecycle', changed)
    with pytest.raises(preparation.LeafLifecyclePreparationHold, match='STORAGE_HOLD' if fault != 'sample-bytes' else 'HASH_HOLD'):
        prepare((directory, source[1], source[2]))


def test_preparation_never_advances_produces_connects_invokes_cli_or_writes(source, monkeypatch):
    import psycopg
    from app.job_store import JobStore
    from app.crop_morphology_artifact_io import MorphologyBlobStore
    from app import crop_rational_shoot_inventory as shoot
    from app import crop_leaf_population_artifact_producer as producer
    from app import crop_leaf_appearance_artifact_producer as appearance_producer
    calls = []
    def forbidden(*args, **kwargs): calls.append(1); raise AssertionError('preparation crossed execution boundary')
    for module, name in [(lifecycle, 'advance_leaf_lifecycle'), (lifecycle.base, 'advance_leaf_removal_inventory'),
        (lifecycle.single, 'advance_leaf_removal_timeline'), (lifecycle.point.leaf, 'advance_rational_leaf_area'),
        (population, 'advance_leaf_population'), (lifecycle.point.births, 'create_declared_leaves'),
        (shoot, 'advance_rational_shoot_internode_inventory'), (producer, 'produce_leaf_population_artifact'),
        (appearance_producer, 'produce_leaf_appearance_artifact'), (MorphologyBlobStore, 'put'),
        (JobStore, 'connect'), (psycopg, 'connect'), (subprocess, 'run'), (subprocess, 'Popen')]: monkeypatch.setattr(module, name, forbidden)
    original_open = os.open
    def readonly(path, flags, *args, **kwargs):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND): return forbidden()
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(os, 'open', readonly)
    for module in [builtins, io]:
        original = module.open
        def checked(file, mode='r', *args, _original=original, **kwargs):
            if isinstance(mode, str) and any(x in mode for x in 'wax+'): return forbidden()
            return _original(file, mode, *args, **kwargs)
        monkeypatch.setattr(module, 'open', checked)
    result = prepare(source)
    assert len(result['lifecycle_initialization']['births']) == 2 and calls == []


def test_preparation_output_fields_do_not_alias_each_other_or_caller(source):
    p = appearance_program(); raw = canonical(p); m = management(raw, [removal('declared-leaf-0', Fraction(1, 3))]); before = deepcopy((p, m))
    result = prepare(source, p, m)
    birth = result['lifecycle_initialization']['births'][0]['leaf_id']
    result['appearance_preparation']['generated_program']['births'][0]['leaf_id'] = 'changed'
    assert result['lifecycle_initialization']['births'][0]['leaf_id'] == birth
    result['forcing'][0]['air_temperature']['value'] = 99
    assert result['appearance_preparation']['derivation']['leaf_inputs']['segments'][0]['air_temperature']['value'] != 99
    result['source_rights']['management']['use'] = False
    result['lifecycle_initialization']['removals'][0]['event_id'] = 'changed'
    assert (p, m) == before


def test_parser_fresh_process_has_no_growth_imports_or_database_cli_writes(tmp_path):
    raw = canonical(appearance_program()); file = tmp_path/'management.json'; file.write_bytes(canonical(management(raw)))
    script = '''
import importlib.abc,json,os,sys
from pathlib import Path
import psycopg,subprocess
blocked={'app.crop_leaf_lifecycle','app.crop_leaf_removal_inventory','app.crop_leaf_removal_timeline','app.crop_declared_leaf_removal',
 'app.crop_leaf_population','app.crop_leaf_inventory','app.crop_rational_leaf_area','app.crop_leaf_appearance_preparation',
 'app.crop_phytomer_kind','app.crop_stored_shoot_leaf_birth_inputs'}
class Forbid(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname in blocked:raise AssertionError('growth import '+fullname)
sys.meta_path.insert(0,Forbid())
from app.job_store import JobStore
def forbidden(*a,**kw):raise AssertionError('parser crossed IO boundary')
JobStore.connect=psycopg.connect=subprocess.run=subprocess.Popen=forbidden
def audit(event,args):
 if event=='open' and isinstance(args[2],int) and args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):forbidden()
sys.addaudithook(audit)
from app.crop_leaf_lifecycle_program import parse_leaf_lifecycle_management_program
p=parse_leaf_lifecycle_management_program(program_raw=Path(sys.argv[1]).read_bytes())
assert not blocked.intersection(sys.modules)
print(json.dumps({'passed':True,'growth_imports':0,'DB_CLI_writes':0,'removals':len(p['removals'])}))
'''
    env = {**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1]), 'PYTHONDONTWRITEBYTECODE': '1'}
    result = subprocess.run([sys.executable, '-B', '-c', script, str(file)], env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {'passed': True, 'growth_imports': 0, 'DB_CLI_writes': 0, 'removals': 0}
