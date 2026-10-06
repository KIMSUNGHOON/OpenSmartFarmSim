from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

from app import crop_cycle_stream_execution as engine
from app import crop_cycle_artifact as artifact
from app import crop_plant_startup_integration as original
from test_crop_cycle_artifact import PROFILES, NOTICE, program

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def driver():
    path = ROOT / 'research/crop-cycle-burden-profile.py'
    spec = importlib.util.spec_from_file_location('cycle_burden_profile', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_digest(rows):
    digest = sha256()
    for row in rows:
        digest.update(json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n')
    return digest.hexdigest()


@pytest.mark.parametrize('name', ['empty-entry', 'full-removal-reentry', 'positive-tail'])
def test_actual_observation_and_quota_restore_preserve_original_rows_state_and_clock(driver, tmp_path, name):
    raw = program(name); before = deepcopy(raw)
    expected = original.integrate_plant_startup(**raw, **PROFILES)
    rhs = engine.short._Evaluator.rhs
    report = driver.profile_pure(tmp_path / 'profile', raw,
        budgets=[{'max_steps':10000, 'max_transitions':10000},
                 {'max_steps':17, 'max_transitions':31},
                 {'max_steps':10000, 'max_transitions':128}], profiles=PROFILES)
    assert raw == before and engine.short._Evaluator.rhs is rhs
    assert report['scope'] == 'own_synthetic_cost_measurement_only'
    assert report['measurement_code_sha256'] == sha256((ROOT/'research/crop-cycle-burden-profile.py').read_bytes()).hexdigest()
    assert report['full166day_accepted'] is False
    assert report['descriptors_before'] == report['descriptors_after']
    runs = report['runs']; assert len(runs) == 3
    assert len({r['semantic_sha256'] for r in runs}) == 1
    for result in runs:
        assert result['status'] == expected['status'] == 'completed'
        assert result['steps'] == expected['steps']
        assert result['sample_count'] == len(expected['samples'])
        assert result['event_count'] == len(expected['events'])
        assert result['samples_sha256'] == row_digest(expected['samples'])
        assert result['events_sha256'] == row_digest(expected['events'])
        assert original._state(result['semantic_checkpoint']['y']) == expected['samples'][-1]['state']
    assert runs[1]['checkpoint_restores'] > 0
    assert runs[1]['costs']['rhs']['calls'] > 0
    assert runs[1]['costs']['json.canonical']['calls'] > 0
    assert runs[1]['costs']['checkpoint.restore']['calls'] == runs[1]['checkpoint_restores']
    assert all(metric['wall_seconds'] >= metric['exclusive_wall_seconds'] >= 0
               and metric['cpu_seconds'] >= metric['exclusive_cpu_seconds'] >= 0
               for r in runs for metric in r['costs'].values())


def test_observer_restores_real_functions_on_exception_and_propagates_hold(driver):
    rhs = engine.short._Evaluator.rhs; canonical = engine._canonical
    observer = driver.Costs()
    with pytest.raises(RuntimeError, match='original failure'):
        with observer.observe():
            assert engine.short._Evaluator.rhs is not rhs
            with observer.measure('outer'):
                engine._canonical({'value':1})
                raise RuntimeError('original failure')
    assert engine.short._Evaluator.rhs is rhs and engine._canonical is canonical
    assert observer.values['outer']['calls'] == 1
    assert observer.values['json.canonical']['calls'] == 1
    assert not observer.stack


@pytest.mark.parametrize('budget', [None, {}, {'max_steps':True,'max_transitions':1},
    {'max_steps':0,'max_transitions':1}, {'max_steps':1,'max_transitions':10001}])
def test_invalid_measurement_quota_does_not_create_input_or_run_rhs(driver, tmp_path, budget):
    destination = tmp_path / 'rejected'
    with pytest.raises(ValueError):
        driver.profile_pure(destination, program(), budgets=[budget], profiles=PROFILES)
    assert not destination.exists()


@pytest.mark.parametrize('name', ['empty-entry', 'full-removal-reentry'])
def test_actual_artifact_reopen_costs_preserve_all_original_rows_and_seed(driver, tmp_path, name, monkeypatch):
    raw = program(name)
    pure = driver.profile_pure(tmp_path / 'pure', raw,
        budgets=[{'max_steps':10000,'max_transitions':10000}], profiles=PROFILES)
    original_rhs = engine.short._Evaluator.rhs
    report = driver.profile_artifact(tmp_path / 'artifact', raw,
        budgets=[{'max_steps':10000,'max_transitions':128},
                 {'max_steps':17,'max_transitions':31}], profiles=PROFILES, notice_raw=NOTICE)
    assert engine.short._Evaluator.rhs is original_rhs
    assert report['descriptors_before'] == report['descriptors_after']
    assert report['input_root_sha256'] == pure['input_root_sha256']
    assert all(r['semantic_sha256'] == pure['runs'][0]['semantic_sha256'] for r in report['runs'])
    for result in report['runs']:
        assert result['status'] == 'completed'
        assert result['commit_count'] == result['costs']['artifact.append']['calls']
        assert result['costs']['artifact.verify']['calls'] >= result['commit_count']
        assert len(result['growth_curve']) == result['commit_count']
        assert result['storage_bytes'] > 0 and result['file_count'] > 0
        assert result['read_rhs_calls'] == 0
        assert result['max_page_bytes'] <= artifact.LIMITS['page_bytes']
    assert report['runs'][1]['writer_reopens'] > 0
    assert report['runs'][1]['costs']['artifact.reopen']['calls'] == report['runs'][1]['writer_reopens']


def test_artifact_profile_rejects_pure_only_transition_budget_before_writing(driver, tmp_path):
    destination = tmp_path / 'rejected'
    with pytest.raises(ValueError):
        driver.profile_artifact(destination, program(),
            budgets=[{'max_steps':10000,'max_transitions':129}], profiles=PROFILES, notice_raw=NOTICE)
    assert not destination.exists()


def test_numeric_hold_remains_explicit_and_preserves_only_confirmed_past(driver, tmp_path):
    raw = program('positive-tail')
    raw['segments'][0]['removals']['values']['leaf']['value'] = 1e9
    expected = original.integrate_plant_startup(**raw, **PROFILES)
    budgets = [{'max_steps':10000,'max_transitions':128}, {'max_steps':1,'max_transitions':1}]
    pure = driver.profile_pure(tmp_path/'pure', raw, budgets=budgets, profiles=PROFILES)
    stored = driver.profile_artifact(tmp_path/'stored', raw, budgets=budgets, profiles=PROFILES, notice_raw=NOTICE)
    for result in [*pure['runs'], *stored['runs']]:
        assert result['status'] == expected['status'] == 'hold'
        assert result['hold'] == expected['hold']
        assert result['last_confirmed'] == expected['last_confirmed']
        assert result['semantic_checkpoint'] is None
        assert result['samples_sha256'] == row_digest(expected['samples'])


def test_source_shape_plan_reads_every_anchor_without_executing_rhs(driver, tmp_path, monkeypatch):
    from test_crop_cycle_input_stream import long_program
    raw = long_program(2); raw['solver']['max_step_seconds'] = 8
    before = deepcopy(raw)
    def forbidden(*args, **kwargs):pytest.fail('shape planning executed RHS')
    monkeypatch.setattr(engine.short._Evaluator, 'rhs', forbidden)
    result = driver.profile_shape(tmp_path/'shape', raw,
        intervals=129, interval_seconds=300, profiles=PROFILES)
    assert raw == before
    assert result['plan']['planned_steps'] == 129*38
    assert result['plan']['counts'] == {'segments':129,'events':0,'anchors':130,'outputs':130}
    assert result['plan']['boundaries'] == 130
    assert result['index_pages'] > 1
    assert result['rhs_calls'] == 0 and result['actual_rhs_steps'] == 0
    assert result['full166day_accepted'] is False
    assert result['descriptors_before'] == result['descriptors_after']
    assert result['costs']['input.write_and_preflight']['calls'] == 1
    assert result['costs']['input.open_and_preflight']['calls'] == 1
    assert result['costs']['input.prepare_context']['calls'] == 1


from test_crop_cycle_server_custody_farms import server_setup
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope

NATIVE_POLICY = {'market_calculation':True, 'market_source_storage':True,
    'thermal_scenario_storage':True, 'break_even_calculation':True, 'crop_cycle_result_storage':True}


@pytest.mark.parametrize('login_scope', [NATIVE_POLICY], indirect=True)
def test_actual_registered_scram_worker_restore_and_public_costs_preserve_original(driver, server_setup):
    from test_crop_cycle_result_store_farms import DB_KEY
    from test_crop_cycle_farm_binding import counts
    server, raw, rights, principal, expected = server_setup
    before = counts(server.binding)
    result = driver.profile_native(server, raw, tenant='tenant-1',
        first_budget={'max_steps':10000,'max_transitions':64},
        resume_budget={'max_steps':10000,'max_transitions':128}, db_key=DB_KEY, worker_timeout=180,
        input_rights=rights, principal=principal)
    assert result['actual_scram'] is True and result['worker_exit_code'] == 0
    assert result['worker_restore_exact'] is True and result['final_semantics_equal'] is True
    assert result['initial_progress']['status'] == 'yielded'
    assert result['terminal_progress']['status'] == 'completed'
    assert result['terminal_progress']['steps'] == expected['steps'] == 120
    assert result['samples_sha256'] == row_digest(expected['samples'])
    assert result['events_sha256'] == row_digest(expected['events'])
    assert result['public_all_original_rows_equal'] is True
    assert result['put_and_read_rhs_calls'] == 0
    assert result['current_rights_withdrawal_denied'] and result['current_principal_withdrawal_denied']
    assert rights.allowed and 'crop_result_read' in principal['scopes']
    assert counts(server.binding) == (before[0],before[1],1,0)
    assert result['descriptors_before'] == result['descriptors_after']
    assert result['transport_scope'] == 'direct_actual_public_response_function_without_TLS'
    assert result['full166day_accepted'] is False
    for name in ('farm.current_rights','farm.input_validate','db.put','public.response'):
        assert result['parent_costs'][name]['calls'] > 0
    assert result['worker']['costs']['rhs']['calls'] > 0
    assert result['worker']['descriptors_before'] == result['worker']['descriptors_after']
    Path('/tmp/ossf-cycle-burden-native-20261006.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
