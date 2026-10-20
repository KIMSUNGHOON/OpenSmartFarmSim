"""Project original CO2 records without regenerating physical state or diagnostics."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from app import api_crop_greenhouse_co2_replay as public
from app import crop_greenhouse_co2_storage as files
import test_crop_greenhouse_co2_input_evidence as inputs
import test_crop_greenhouse_co2_result_store as registered

profiles = inputs.profiles
ROOT = Path(__file__).resolve().parents[2]


def save(name, value):
    directory = os.environ.get('OSSF_JOINT_PREFIX_SDK_EVIDENCE')
    if directory:
        with (Path(directory)/('co2-projection-'+name)).open('x') as handle:
            os.fchmod(handle.fileno(), 0o400)
            json.dump(value, handle, sort_keys=True, indent=2)
            handle.flush(); os.fsync(handle.fileno())


def owned_result(path, profiles, *, held=False, case=None):
    if held:
        case = deepcopy(inputs.producer.reference.BY_ID['weather-multiple'])
        case['events'][-1]['event']['values']['leaf']['value'] = 50000
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    p = inputs.packet(path/'inputs', profiles, case)
    c = files.continuation; binding = p[2]; initial = c.start(binding._context)
    chunk = c.advance_chunk(binding._context, initial, 128)
    directory = path/'artifact'; directory.mkdir(mode=0o700)
    with files.create_writer(directory, binding, initial) as writer:
        writer.append(chunk, expected_chunk_sha256=files.clock.source_chunk_sha256(binding._context, chunk))
        digest = writer.finalize()
    with files.open_artifact(directory, digest) as reader:
        terminal = {**reader.summary, 'manifest': binding._context.manifest,
                    'time_binding': binding.manifest}
        pages = {kind: reader.page(kind) for kind in ('samples', 'events')}
        head = deepcopy(reader._head_value); head_sha = reader.head_sha256
        size, count = reader._usage()
    template = json.loads((ROOT/'fixtures/synthetic-co2-result-projection-template-v1.json').read_bytes())
    farm_binding = deepcopy(template['binding']); source = farm_binding['input']
    proof = inputs.issue(inputs.authority(p[3]), p)
    source_raw = json.loads((p[0]/'source.json').read_bytes())
    native = inputs.model._record(binding, source_raw['provenance'])
    source.update(program_id=native['program']['scenario']['input_id'],
        period={'start': native['binding']['start_utc'], 'end': native['binding']['end_utc']},
        source_sha256=p[1], context_sha256=native['context_sha256'],
        time_binding_sha256=native['binding_sha256'], evidence_sha256=sha256(proof).hexdigest(),
        initial_state_sha256=native['initial_state_sha256'], model_identity=native['manifest']['identity'],
        review=p[3], provenance=native['provenance'],
        provenance_sha256=sha256(public.storage._canonical(native['provenance'])).hexdigest())
    farm_binding['registration']['decision_at'] = source['provenance']['available_at']
    farm_binding['request']['input'].update({key: source[key] for key in
        ('program_id', 'source_sha256', 'context_sha256', 'time_binding_sha256', 'evidence_sha256')})
    farm_binding['request']['rights']['input_source_sha256'] = p[1]
    binding_raw = public.storage._canonical(farm_binding)
    progress = deepcopy(template['policies']['server_progress'])
    progress.update({key: terminal[key] for key in
        ('context_sha256', 'status', 'counts', 'checkpoint', 'last_confirmed', 'hold', 'times')})
    progress.update(source_sha256=p[1], time_binding_sha256=native['binding_sha256'],
        binding_sha256=sha256(binding_raw).hexdigest(), provenance_sha256=source['provenance_sha256'],
        artifact_sha256=digest, header_sha256=head['header_sha256'], head_sha256=head_sha,
        commit_count=head['commit_count'], steps=terminal['last_confirmed']['step_index'],
        planned_steps=native['manifest']['numerical']['step_count'], storage_bytes=size, file_count=count,
        intent_sha256=sha256(b'owned-unregistered-co2-projection'+binding_raw).hexdigest(),
        proof_sha256=sha256(b'owned-unregistered-co2-proof'+digest.encode()).hexdigest())
    progress_raw = public.storage._canonical(progress)
    raw = public.storage._packet(binding_raw, progress_raw, template['policies']['resolver_version'])
    packet = json.loads(raw)
    record = {'result_id': packet['result_id'], 'payload_raw': raw, 'payload_sha256': sha256(raw).hexdigest(),
        'progress_raw': progress_raw, 'progress_sha256': sha256(progress_raw).hexdigest(),
        'recorded_at': datetime(2026, 10, 9, 20, 0, 0, 123456, tzinfo=timezone.utc)}
    return record, terminal, pages, binding._context.program


@pytest.fixture(scope='module')
def original(tmp_path_factory, profiles):
    return owned_result(tmp_path_factory.mktemp('owned-co2-projection'), profiles)


def project(case, view='summary', *, page=None, limit=None, program=None):
    record, terminal, pages, source = case
    if view != 'summary':
        page = pages[view] if page is None else page
        limit = (64 if view == 'samples' else 8) if limit is None else limit
    return public.project_co2_result(record, terminal,
        source_program=source if program is None else program, view=view, page=page, limit=limit)


def private_fields_absent(value):
    forbidden = {'tenant_id', 'registration_job_id', 'rights', 'review', 'reviewer_id',
        'parameters', 'forcing', 'relative_growth_rate', 'source.json', 'payload_raw',
        'integrity_signature', 'scenario', 'origin', 'source_program', 'after_rhs', 'event'}
    if isinstance(value, dict):
        assert not forbidden.intersection(value)
        for item in value.values(): private_fields_absent(item)
    elif isinstance(value, list):
        for item in value: private_fields_absent(item)


def test_original_states_ledgers_events_units_basis_UTC_and_privacy(original, monkeypatch):
    before = deepcopy(original); calls = registered.producer.reference.forbid(monkeypatch)
    record, terminal, pages, program = original
    bases = {row['step_index']: row['co2']['basis'] for row in program['forcing_program']}
    fd = len(os.listdir('/proc/self/fd')); responses = {}
    for view in ('summary', 'samples', 'events'):
        projected = project(original, view); value = projected.model_dump(mode='json')
        raw = public._public_bytes(projected)
        assert json.loads(raw) == value and len(raw) <= 2*1024**2
        assert value['reference']['G0_G4'] == 'not_assessed'
        assert value['reference']['rights_or_gate_approval'] is False
        assert value['reference']['model'] == terminal['manifest']['identity']
        responses[view] = {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}
        if view == 'summary':
            last = value['summary']['last_confirmed']
            assert last['value'] == terminal['last_confirmed'] and last['time'] == terminal['times']['last_confirmed']
            assert last['co2_basis'] == bases[last['value']['forcing_step_index']]
            assert value['summary']['manifest'] == terminal['manifest']
        elif view == 'samples':
            for saved, actual in zip(pages[view]['records'], value['page']['records'], strict=True):
                assert actual['value'] == saved['value'] and actual['time'] == saved['time']
                sample = actual['value']
                assert actual['co2_basis'] == bases[sample['forcing_step_index']]
                assert len(sample['plant_state'])+len(sample['climate_state'])+sum(map(len, sample['cohort_state'].values())) == 109
                assert len(sample['derived']) == 8 and len(sample['integrated_transfers']) == 44
                assert len(sample['event_totals']) == 6 and len(sample['balance_residuals']) == 17
                assert sample['climate_state']['air_co2_mass']['unit'] == 'mg_CO2/m2_floor'
                assert sample['derived']['air_co2_density']['unit'] == 'mg_CO2/m3'
                assert sample['derived']['crop_co2_ppm']['unit'] == 'ppm'
        else:
            for saved, actual in zip(pages[view]['records'], value['page']['records'], strict=True):
                assert actual['time'] == saved['time']
                assert actual['co2_basis'] == bases[saved['value']['forcing_step_index']]
                assert set(actual['value']) == {'step_index', 'elapsed_seconds', 'forcing_step_index', 'management'}
                old = saved['value']['management']; got = actual['value']['management']
                assert set(got) == set(old)-{'event'}
                assert len(got['balance_residuals']) == len(got['balance_budgets']) == 10
                for key in got:
                    if key in ('before', 'after'):
                        assert got[key] == {**{n: old[key][n] for n in ('derived', 'input_sha256', 'calculation_sha256')},
                            **{n: old[key]['scenario'][n] for n in ('plant_state', 'cohort_state', 'climate_state')}}
                    else: assert got[key] == old[key]
        private_fields_absent(value)
    assert original == before and all(value == 0 for value in calls.values())
    assert len(os.listdir('/proc/self/fd')) == fd
    save('original.json', {'responses': responses, 'original109_states44_ledgers17_balances_and_basis': True,
        'actual_rows': terminal['counts'], 'private_fields_absent': True,
        'no_unretained_diagnostics_regenerated': True, 'calls': calls, 'FD_before_after': [fd, fd],
        'authenticated_current_read': False, 'unregistered_software_template': True})
    save('fresh-pack.private.json', {'record': {key: item.decode() if isinstance(item, bytes)
        else item.isoformat() if isinstance(item, datetime) else item for key, item in record.items()},
        'terminal': terminal, 'pages': pages, 'program': program, 'expected': responses})


def test_hold_preserves_original_last_confirmed_time_state_and_reason(profiles, tmp_path, monkeypatch):
    case = owned_result(tmp_path, profiles, held=True)
    calls = registered.producer.reference.forbid(monkeypatch)
    value = project(case).model_dump(mode='json'); terminal = case[1]
    assert terminal['status'] == value['summary']['status'] == 'hold'
    assert value['summary']['checkpoint_sha256'] is None
    assert value['summary']['last_confirmed']['value'] == terminal['last_confirmed']
    assert value['summary']['last_confirmed']['time'] == terminal['times']['last_confirmed']
    assert value['summary']['hold']['time'] == terminal['times']['hold']
    assert value['summary']['hold']['reason_code'] == terminal['hold']['reason'].partition(':')[0]
    for kind in ('samples', 'events'):
        page = project(case, kind).model_dump(mode='json')['page']
        assert all(row['value']['step_index'] < terminal['hold']['step_index'] for row in page['records'])
    assert all(value == 0 for value in calls.values()); private_fields_absent(value)
    save('hold.json', {'last_confirmed_step': terminal['last_confirmed']['step_index'],
        'last_confirmed_time': terminal['times']['last_confirmed'], 'failed_time': terminal['times']['hold'],
        'checkpoint_sha256': None, 'original_hold_preserved': True, 'calls': calls})


@pytest.mark.parametrize('case', inputs.producer.CASES, ids=lambda case: case['case_id'])
def test_original_programs_use_stored_forcing_cursor_and_basis(case, profiles, tmp_path, monkeypatch):
    original = owned_result(tmp_path, profiles, case=case)
    calls = registered.producer.reference.forbid(monkeypatch)
    bases = {row['step_index']: row['co2']['basis'] for row in original[3]['forcing_program']}
    for view in ('summary', 'samples', 'events'):
        value = project(original, view).model_dump(mode='json')
        rows = [value['summary']['last_confirmed']] if view == 'summary' else value['page']['records']
        for row in rows: assert row['co2_basis'] == bases[row['value']['forcing_step_index']]
    assert all(value == 0 for value in calls.values())
    save('program-'+case['case_id']+'.json', {'views': 3, 'basis_by_original_cursor': True, 'calls': calls})


def test_forcing_hold_does_not_use_unconfirmed_new_basis_at_same_UTC(profiles, tmp_path, monkeypatch):
    source = deepcopy(inputs.producer.reference.BY_ID['weather-multiple'])
    for row in source['forcing_program']: row['co2']['basis'] = 'wet'
    source['forcing_program'][-1]['co2']['basis'] = 'dry'
    source['forcing_program'][-1]['co2']['parameters']['air_pressure']['value'] = 1.0
    case = owned_result(tmp_path, profiles, case=source)
    calls = registered.producer.reference.forbid(monkeypatch)
    terminal = case[1]; assert terminal['status'] == 'hold' and terminal['hold']['phase'] == 'forcing'
    last = terminal['last_confirmed']; assert last['step_index'] == terminal['hold']['step_index']
    assert last['forcing_step_index'] < source['forcing_program'][-1]['step_index']
    value = project(case).model_dump(mode='json')
    assert value['summary']['last_confirmed']['co2_basis'] == 'wet'
    assert value['summary']['last_confirmed']['value'] == last
    assert value['reference']['failed_boundary'] == value['reference']['last_confirmed']
    assert all(value == 0 for value in calls.values())
    save('unconfirmed-forcing.json', {'original_basis': 'wet', 'unconfirmed_future_basis': 'dry',
        'same_confirmed_and_failed_UTC': True, 'no_new_basis_inference': True, 'calls': calls})


@pytest.mark.parametrize('fault', ('state-extra', 'mass-unit', 'float-bool', 'array49', 'exchange-extra',
    'missing-transfer', 'event-total-extra', 'missing-balance', 'bad-phase', 'forcing-bool', 'forcing-future',
    'bad-UTC', 'old-artifact', 'old-family-event', 'event-transient'))
def test_closed_original_rows_reject_wrong_units_types_versions_and_mixed_pages(original, monkeypatch, fault):
    case = deepcopy(original); kind = 'samples'; page = case[2][kind]; value = page['records'][0]['value']
    if fault == 'state-extra': value['climate_state']['invented_mass'] = {'value': 0.0, 'unit': '1'}
    elif fault == 'mass-unit': value['climate_state']['air_co2_mass']['unit'] = 'mg_CH2O/m2_floor'
    elif fault == 'float-bool': value['derived']['crop_co2_ppm']['value'] = True
    elif fault == 'array49': value['cohort_state']['fruit_number'].pop()
    elif fault == 'exchange-extra': value['co2_exchange']['net']['invented'] = {'value': 0.0, 'unit': '1'}
    elif fault == 'missing-transfer': value['integrated_transfers'].pop('co2_crop_to_air')
    elif fault == 'event-total-extra': value['event_totals']['invented'] = {'value': 0.0, 'unit': '1'}
    elif fault == 'missing-balance': value['balance_residuals'].pop('crop_air_carbon_equivalent')
    elif fault == 'bad-phase': value['phase'] = 'unconfirmed-trial'
    elif fault == 'forcing-bool': value['forcing_step_index'] = False
    elif fault == 'forcing-future': value['forcing_step_index'] = case[3]['step_count']
    elif fault == 'bad-UTC': page['records'][0]['time']['at'] = '2026-10-01T00:00:00.123457Z'
    elif fault == 'old-artifact': page['version'] = 'joint-solar-ventilation-storage-research-v1'
    else:
        kind = 'events'; page = case[2][kind]
        if fault == 'old-family-event': page['records'][0]['value']['solar_before'] = {}
        else: page['records'][0]['value']['management']['after_rhs'] = {}
    calls = registered.producer.reference.forbid(monkeypatch)
    with pytest.raises(public.ProjectionHold): project(case, kind, page=page)
    assert all(value == 0 for value in calls.values())


@pytest.mark.parametrize('fault', ('missing', 'extra', 'basis', 'index-bool', 'wrong-step', 'edited-input', 'oversize'))
def test_matching_program_is_required_for_concentration_basis(original, monkeypatch, fault):
    program = deepcopy(original[3])
    if fault == 'missing': program = {}
    elif fault == 'extra': program['caller_basis'] = 'dry'
    elif fault == 'basis': program['forcing_program'][0]['co2']['basis'] = 'unknown'
    elif fault == 'index-bool': program['forcing_program'][0]['step_index'] = False
    elif fault == 'wrong-step': program['step_seconds'] += 1.0
    elif fault == 'edited-input': program['forcing_program'][0]['co2']['parameters']['air_pressure']['value'] += 1.0
    else: program['scenario']['input_id'] = 'x'*(2*1024**2)
    calls = registered.producer.reference.forbid(monkeypatch)
    with pytest.raises(public.ProjectionHold): project(original, program=program)
    assert all(value == 0 for value in calls.values())


def test_runtime_identity_is_preserved_from_original_manifest(profiles, tmp_path, monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(files.continuation.transport.platform, 'python_version', lambda: '3.12.13')
        case = owned_result(tmp_path, profiles)
    calls = registered.producer.reference.forbid(monkeypatch)
    for view in ('summary', 'samples', 'events'):
        assert project(case, view).reference.model.python_version == '3.12.13'
    assert all(value == 0 for value in calls.values())


def test_page_boundaries_missing_source_program_and_serialization_limit(original, monkeypatch):
    calls = registered.producer.reference.forbid(monkeypatch)
    for kind, limit in (('samples', 65), ('events', 9), ('samples', True), ('events', 0)):
        with pytest.raises(public.ProjectionHold): project(original, kind, limit=limit)
    with pytest.raises(public.ProjectionHold): project(original, 'unknown', page={}, limit=1)
    with pytest.raises(public.ProjectionHold):
        public.project_co2_result(original[0], original[1], source_program=None)
    model = project(original)
    monkeypatch.setattr(public, 'MAX_RESPONSE_BYTES', 1)
    with pytest.raises(public.ProjectionHold): public._public_bytes(model)
    assert all(value == 0 for value in calls.values())
