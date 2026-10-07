"""Manual full synthetic calendar registration; no crop run or prediction."""
from copy import deepcopy
from datetime import date
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import psycopg
import pytest

from app import crop_cycle_calculation_context as calculation
from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding, CalculationFarmBindingHold
from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from app.economic_contracts import EconomicScenario
from app.economics import canonical_scenario_sha256
from app.farm_authoring_storage import FarmAuthoringService
from app.market_scenario import MarketScenarioService
from app.thermal_run_store import _canonical
from test_crop_cycle_input_evidence import authority
from test_crop_cycle_farm_binding import SyntheticInputRights, counts
from test_farm_authoring_storage import authoring, request as farm_request
from test_farm_replay_scenario import farm_setup as original_farm_setup
from login_database import login_database, login_scope, assert_host_scram
import test_economics_settlement as settlement
from test_economics import settlement_record
import test_market_scenario as market
import test_market_signed_hold_integration as signed
import test_api_economic_scenario as economic_api

END = date(2027, 3, 16)
POLICY = {'market_calculation':True, 'market_source_storage':True,
          'thermal_scenario_storage':True, 'break_even_calculation':True,
          'crop_cycle_result_storage':True}


def calendar_sources():
    def example():
        data = settlement.example()
        data['period_end'] = END
        for event in data['setoffs']:
            event['evidence_sha256'] = settlement_record(data, event)['raw_sha256']
        return data
    with patch.object(market, 'example', example):
        values, request = market.case()
    for value in values.rights.values():
        value['effective_end'] = END
    shock = values.shocks[('joint-1','r1')]
    shock['effective_end'] = END
    for record in (*shock['drivers'], *shock['contract_caps']):
        record['effective_end'] = END
    for reference in shock['settlement_bindings']:
        value = values.bindings[(reference['binding_id'], reference['revision'])]
        value['effective_end'] = END
        reference['sha256'] = market.digest(value)
    market.repin_shock(values)
    request['shock']['sha256'] = market.digest(shock)
    return values, request


def test_scoped_calendar_sources_are_valid_before_real_adoption():
    original = settlement.example()
    values, request = calendar_sources()
    scenario = EconomicScenario.model_validate(values.scenarios[('scenario-1','r1')])
    assert scenario.period_end == END
    assert all(row['scope_end'] == END for row in values.records.values())
    assert all(row['effective_end'] == END for row in values.rights.values())
    service = MarketScenarioService(values)
    candidate = service.build_candidate(request, 'tenant-1')
    result = service.calculate_pinned(candidate.scenario_id, candidate.revision, 'tenant-1')
    assert result.calculation_status == 'conditional_user_assumption'
    assert result.assessment_status == 'hold'
    assert settlement.example() == original


@pytest.fixture
def farm_setup(login_scope, monkeypatch):
    monkeypatch.setattr(signed, 'case', calendar_sources)
    original_assembly = economic_api.signed_market_assembly
    def assembly(*args, **kwargs):
        factory, values, request, principal, scope = original_assembly(*args, **kwargs)
        old = ('scenario-1','r1'); key = ('owned-full166-economics','r1')
        data = deepcopy(values.scenarios.pop(old))
        data['scenario_id'] = key[0]
        scenario = EconomicScenario.model_validate(data)
        digest = canonical_scenario_sha256(scenario)
        values.scenarios[key] = scenario.model_dump(mode='python')
        pin = values.pins.pop(old)
        pin.update(scenario_id=key[0], payload_sha256=digest, immutable_job_input_sha256=digest)
        values.pins[key] = pin
        shock = values.shocks[('joint-1','r1')]
        shock['baseline_sha256'] = digest
        market.repin_shock(values)
        request['baseline'].update(scenario_id=key[0], sha256=digest)
        request['shock']['sha256'] = market.digest(shock)
        return factory, values, request, principal, scope
    monkeypatch.setattr(economic_api, 'signed_market_assembly', assembly)
    return original_farm_setup.__wrapped__(login_scope, monkeypatch)


def save(name, value):
    directory = Path(os.environ['OSSF_FULL_CALENDAR_EVIDENCE'])
    with (directory/name).open('x') as handle:
        os.fchmod(handle.fileno(), 0o400)
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


def tree(directory):
    return {p.name:(sha256(p.read_bytes()).hexdigest(), p.stat().st_mode, p.stat().st_dev, p.stat().st_ino)
            for p in directory.iterdir() if p.is_file()}


@pytest.fixture(scope='module')
def audit_registration(login_database, tmp_path_factory):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
        methods = assert_host_scram(conn)
    passfiles = list(tmp_path_factory.getbasetemp().rglob('*.pgpass'))
    assert schemas == roles == len(passfiles) == 0
    save('database-cleanup.json', {'schemas_after':schemas, 'roles_after':roles,
        'passfiles_after':len(passfiles), 'server_host_auth_methods':methods})


@pytest.mark.parametrize('login_scope', [POLICY], indirect=True)
def test_full166_actual_registration_current_rights_and_bad_periods_without_rhs(
        audit_registration, authoring, monkeypatch):
    farms, body, principal = authoring
    original_directory = Path(os.environ['OSSF_FULL_ORIGINAL_INPUTS'])
    directory = Path(os.environ['OSSF_FULL_CALENDAR_INPUTS'])
    receipt = json.loads(Path(os.environ['OSSF_FULL_CALENDAR_RECEIPT']).read_bytes())
    original_proof = Path(os.environ['OSSF_FULL_ORIGINAL_PROOF']).read_bytes()
    proof = Path(os.environ['OSSF_FULL_CALENDAR_PROOF']).read_bytes()
    original_before, derived_before = tree(original_directory), tree(directory)
    fd_before = len(os.listdir('/proc/self/fd')); calls = []
    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError('calendar registration evaluated crop equations')
    monkeypatch.setattr(calculation.short._Evaluator, 'rhs', forbidden)
    monkeypatch.setattr(calculation, 'advance_chunk', forbidden)
    principal['scopes'].update(set(READ_SCOPES) | set(WRITE_SCOPES))
    short = deepcopy(body)
    short['farm']['scenario_id'] = short['rights']['scenario_id'] = 'owned-full166-farm'
    short['rights']['declaration_id'] = 'owned-full166-calendar-rights'
    short_registered = farms.submit('tenant-1', farm_request(short))
    full = deepcopy(short)
    full['farm']['scenario_revision'] = full['rights']['scenario_revision'] = 'r2'
    full['rights']['revision'] = 'r2'
    full['farm']['crops'][0]['occupancy']['end'] = '2027-03-16T00:00:00Z'
    full['farm']['crops'][0]['release_at'] = '2027-03-17T00:00:00Z'
    registered = farms.submit('tenant-1', farm_request(full))
    assert registered.registration_status == 'registered_unpublished_inputs'
    assert farms.submit('tenant-1', farm_request(full)) == registered
    fresh_farms = FarmAuthoringService(farms.replay)
    current = fresh_farms.read_registration('tenant-1', 'owned-full166-farm', 'r2', registered.scenario_sha256)
    assert current['farm'].period_end == END
    assert current['farm'].crops[0].occupancy.end.isoformat() == '2027-03-16T00:00:00+00:00'
    assert fresh_farms.get('tenant-1', 'owned-full166-farm', 'r1') == short_registered
    issuer = authority(); rights = SyntheticInputRights()
    binding = CalculationFarmBinding(fresh_farms, issuer, input_rights=rights)
    reference = dict(scenario_id='owned-full166-farm', scenario_revision='r2',
        registration_sha256=registered.scenario_sha256, crop_id='crop-1')
    request = {'study_id':'owned-full166-calendar', 'revision':'r1', 'farm':reference,
        'input':{'schema_version':calculation.inputs.VERSION,
                 'root_sha256':receipt['target_root_sha256'], 'program_id':receipt['target_program_id']},
        'rights':{'schema_version':'crop-cycle-input-rights-v1',
            'declaration_id':'owned-full166-calendar-input', 'revision':'r1',
            'input_root_sha256':receipt['target_root_sha256'], 'available_at':full['farm']['decision_at'],
            'redistribute':False,
            **{key:True for key in ('ownership_asserted','access','store','transform','use','display')}}}
    raw = _canonical(request); before_binding = counts(binding); started = perf_counter()
    with calculation.open_calculation_context(directory, receipt['target_root_sha256'], proof, authority=issuer) as context:
        assert context.segment_count == 47808 and context.planned_steps == 1816704
        tick = perf_counter(); accepted = binding.prepare('tenant-1', raw, context)
        prepare_seconds = perf_counter()-tick
        tick = perf_counter(); assert binding.current('tenant-1', raw, context, accepted) == accepted
        current_seconds = perf_counter()-tick
        value = json.loads(accepted)
        assert value['input']['period'] == receipt['target_period']
        assert value['registration']['registration_job_id'] == str(registered.intent_job.job_id)
        assert value['registration']['registration_sha256'] == registered.scenario_sha256
        assert value['registration']['profile_applicability'] == 'unvalidated_for_registered_crop'
        assert value['scope'] == 'synthetic_crop_math_only'
        bad = deepcopy(request)
        bad['farm'].update(scenario_revision='r1', registration_sha256=short_registered.scenario_sha256)
        with pytest.raises(CalculationFarmBindingHold): binding.prepare('tenant-1', _canonical(bad), context)
        rights.allowed = False
        with pytest.raises(CalculationFarmBindingHold): binding.current('tenant-1', raw, context, accepted)
        rights.allowed = True
        principal['scopes'].remove('crop_result_read')
        with pytest.raises(PermissionError): binding.current('tenant-1', raw, context, accepted)
        principal['scopes'].add('crop_result_read')
        assert binding.current('tenant-1', raw, context, accepted) == accepted
    assert context.reader.closed and not context._cache and not context.reader._cache
    with calculation.open_calculation_context(original_directory, receipt['source_root_sha256'],
            original_proof, authority=issuer) as original_context:
        bad = deepcopy(request)
        bad['input'].update(root_sha256=receipt['source_root_sha256'], program_id=receipt['source_program_id'])
        bad['rights']['input_root_sha256'] = receipt['source_root_sha256']
        with pytest.raises(CalculationFarmBindingHold): binding.prepare('tenant-1', _canonical(bad), original_context)
    assert original_context.reader.closed and not original_context._cache and not original_context.reader._cache
    assert counts(binding) == before_binding and before_binding[2:] == (0,0)
    assert original_before == tree(original_directory) and derived_before == tree(directory)
    assert len(os.listdir('/proc/self/fd')) == fd_before and not calls
    assert fresh_farms.get('tenant-1', 'owned-full166-farm', 'r1') == short_registered
    save('full166-registration-verified.json', {
        'scope':'derived_synthetic_full166_calendar_registration_only',
        'translation_receipt_sha256':sha256(Path(os.environ['OSSF_FULL_CALENDAR_RECEIPT']).read_bytes()).hexdigest(),
        'source_root_sha256':receipt['source_root_sha256'], 'target_root_sha256':receipt['target_root_sha256'],
        'period':receipt['target_period'], 'farm_period_start':str(current['farm'].period_start),
        'farm_period_end':str(current['farm'].period_end), 'crop':value['registration']['crop'],
        'economic_reference':full['farm']['economic'], 'registration':registered.model_dump(mode='json'),
        'older_registration':short_registered.model_dump(mode='json'),
        'binding_sha256':sha256(accepted).hexdigest(), 'context_sha256':value['input']['input_validation']['context_sha256'],
        'prepare_seconds':prepare_seconds, 'current_seconds':current_seconds,
        'binding_and_denials_wall_seconds':perf_counter()-started,
        'planned_steps':context.planned_steps, 'actual_steps':0, 'rhs_calls':len(calls),
        'original_input_files':len(original_before), 'derived_input_files':len(derived_before),
        'original_and_derived_hash_mode_device_inode_preserved':True,
        'descriptors_before':fd_before, 'descriptors_after':len(os.listdir('/proc/self/fd')),
        'contexts_closed_caches_empty':True, 'old_registration_preserved':True,
        'original_period_and_short_occupancy_denied':True, 'current_rights_and_principal_denied':True,
        'after_registration_counts':before_binding,
        'binding_writes':0, 'actual_crop_Runs':0, 'rights_or_gate_approval':False})
