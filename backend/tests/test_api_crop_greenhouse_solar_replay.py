"""Original owned rows, typed projection, and actual current store integration."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import psycopg

from app import api_crop_greenhouse_solar_replay as public
from app import crop_greenhouse_solar_storage as files
import test_crop_greenhouse_solar_input_evidence as inputs
import test_crop_greenhouse_solar_result_store as registered

profiles = inputs.profiles
ROOT = Path(__file__).resolve().parents[2]


def save(name, value):
    root = os.environ.get('OSSF_SOLAR_PUBLIC_EVIDENCE')
    if root:
        with (Path(root)/name).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2); f.flush(); os.fsync(f.fileno())


def owned_result(path, profiles, *, held=False):
    case = deepcopy(inputs.reference.reference.CASES[6]) if held else None
    if held: case['events'][-1]['event']['values']['leaf']['value'] = 50000
    p = inputs.packet(path/'inputs', profiles, case=case, origin=inputs.reference.origin('2026-10-01T00:00:00.123456Z'))
    c = files.continuation; binding = p[2]; initial = c.start(binding._context); chunk = c.advance_chunk(binding._context, initial, 128)
    root = path/'artifact'; root.mkdir(mode=0o700)
    with files.create_writer(root, binding, initial) as writer:
        writer.append(chunk, expected_chunk_sha256=files.clock.source_chunk_sha256(binding._context, chunk)); digest = writer.finalize()
    with files.open_artifact(root, digest) as reader:
        terminal = {**reader.summary, 'manifest': binding._context.manifest, 'time_binding': binding.manifest}
        pages = {k: reader.page(k) for k in ('samples', 'events')}
        head = deepcopy(reader._head_value); head_sha = reader.head_sha256; size, count = reader._usage()
    template = json.loads((ROOT/'fixtures/synthetic-solar-result-projection-template-v1.json').read_bytes())
    farm_binding = deepcopy(template['binding']); source = farm_binding['input']
    proof = inputs.issue(inputs.authority(p[3]), p)
    source_raw = json.loads((p[0]/'source.json').read_bytes())
    native = inputs.model._record(binding, source_raw['provenance'])
    source.update(program_id=native['program']['scenario']['input_id'],
        period={'start':native['binding']['start_utc'],'end':native['binding']['end_utc']}, source_sha256=p[1], context_sha256=native['context_sha256'], time_binding_sha256=native['binding_sha256'],
        evidence_sha256=sha256(proof).hexdigest(), initial_state_sha256=native['initial_state_sha256'],
        model_identity=native['manifest']['identity'], review=p[3], provenance=native['provenance'],
        provenance_sha256=sha256(public.storage._canonical(native['provenance'])).hexdigest())
    farm_binding['registration']['decision_at'] = source['provenance']['available_at']
    farm_binding['request']['input'].update({k: source[k] for k in
        ('program_id', 'source_sha256', 'context_sha256', 'time_binding_sha256', 'evidence_sha256')})
    farm_binding['request']['rights']['input_source_sha256'] = p[1]
    binding_raw = public.storage._canonical(farm_binding)
    progress = deepcopy(template['policies']['server_progress'])
    progress.update({k: terminal[k] for k in ('context_sha256', 'status', 'counts', 'checkpoint', 'last_confirmed', 'hold', 'times')})
    progress.update(source_sha256=p[1], time_binding_sha256=native['binding_sha256'], binding_sha256=sha256(binding_raw).hexdigest(),
        provenance_sha256=source['provenance_sha256'], artifact_sha256=digest, header_sha256=head['header_sha256'], head_sha256=head_sha,
        commit_count=head['commit_count'], steps=terminal['last_confirmed']['step_index'],
        planned_steps=native['manifest']['numerical']['step_count'], storage_bytes=size, file_count=count,
        intent_sha256=sha256(b'owned-unregistered-pure-intent'+binding_raw).hexdigest(),
        proof_sha256=sha256(b'owned-unregistered-pure-proof'+digest.encode()).hexdigest())
    progress_raw = public.storage._canonical(progress)
    raw = public.storage._packet(binding_raw, progress_raw, template['policies']['resolver_version'])
    packet = json.loads(raw)
    record = {'result_id': packet['result_id'], 'payload_raw': raw, 'payload_sha256': sha256(raw).hexdigest(),
        'progress_raw': progress_raw, 'progress_sha256': sha256(progress_raw).hexdigest(),
        'recorded_at': datetime(2026, 10, 9, 20, 0, 0, 123456, tzinfo=timezone.utc)}
    return record, terminal, pages


@pytest.fixture(scope='module')
def original(tmp_path_factory, profiles):
    return owned_result(tmp_path_factory.mktemp('owned-joint-projection'), profiles)


def project(case, view='summary', *, page=None, limit=None):
    record, terminal, pages = case
    if view != 'summary':
        page = pages[view] if page is None else page; limit = (64 if view == 'samples' else 8) if limit is None else limit
    return public.project_solar_result(record, terminal, view=view, page=page, limit=limit)


def test_original_summary_all_108_states_ledgers_events_units_UTC_and_privacy(original, monkeypatch):
    before = deepcopy(original); calls = registered.producer.reference.forbid(monkeypatch)
    record, terminal, pages = original; summaries = {}; fd = len(os.listdir('/proc/self/fd'))
    for view in ('summary', 'samples', 'events'):
        model = project(original, view); value = model.model_dump(mode='json'); raw = public._public_bytes(model)
        assert len(raw) <= 2*1024**2 and json.loads(raw) == value
        assert value['farm']['batch_id'] and value['reference']['model'] == terminal['manifest']['identity']
        assert value['reference']['input']['context_sha256'] == terminal['context_sha256']
        assert value['reference']['G0_G4'] == 'not_assessed' and value['schema_version'] == public.VERSION
        summaries[view] = {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}
        if view == 'summary':
            assert value['summary']['manifest'] == terminal['manifest']
            assert value['summary']['last_confirmed'] == {'value': terminal['last_confirmed'], 'time': terminal['times']['last_confirmed']}
            assert value['summary']['checkpoint_sha256'] == terminal['checkpoint']['sha256']
        elif view == 'samples': assert value['page']['records'] == pages[view]['records']
        else:
            for saved, actual in zip(pages[view]['records'], value['page']['records'], strict=True):
                assert actual['time'] == saved['time']
                assert actual['value']['solar_before'] == saved['value']['solar_before']
                assert actual['value']['solar_after'] == saved['value']['solar_after']
                assert not {'combined_forcing_before','combined_forcing_after'} & set(actual['value'])
                old = saved['value']['management']; got = actual['value']['management']
                assert 'event' not in got
                for k in got:
                    if k in ('before', 'after'):
                        assert got[k] == {**{n: old[k][n] for n in ('derived', 'input_sha256', 'calculation_sha256')},
                            **{n: old[k]['scenario'][n] for n in ('plant_state', 'cohort_state', 'climate_state')}}
                    else: assert got[k] == old[k]
        forbidden = {'tenant_id', 'registration_job_id', 'rights', 'review', 'reviewer_id', 'parameters', 'forcing',
            'relative_growth_rate', 'source.json', 'payload_raw', 'integrity_signature', 'scenario', 'origin'}
        def inspect(obj):
            if type(obj) is dict:
                assert not forbidden & set(obj)
                for x in obj.values(): inspect(x)
            elif type(obj) is list:
                for x in obj: inspect(x)
        inspect(value)
    assert original == before and all(n == 0 for n in calls.values()) and len(os.listdir('/proc/self/fd')) == fd
    save('original.json', {'responses': summaries, 'rows': {'samples': 3, 'events': 3},
        'all_original_108_states_and_ledgers_events_units_UTC': True, 'private_fields_absent': True,
        'original_inputs_unchanged': True, 'calls': calls, 'FD_before_after': [fd, fd], 'authenticated_current_read': False,
        'native_runtime_identity': terminal['manifest']['identity'], 'unregistered_farm_and_custody_type_fixture': True})


def test_runtime_identity_preserved_without_fixed_historical_root(profiles, tmp_path, monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(files.continuation.transport.platform, 'python_version', lambda: '3.12.13')
        case = owned_result(tmp_path, profiles)
    calls = registered.producer.reference.forbid(monkeypatch)
    for view in ('summary', 'samples', 'events'):
        value = project(case, view)
        assert value.reference.model.python_version == '3.12.13'
        assert value.reference.input.context_sha256 == case[1]['context_sha256']
    assert all(n == 0 for n in calls.values())
    save('runtime-identity.json', {'simulated_python_identity': '3.12.13', 'actual_interpreter': sys.version.split()[0],
        'fault_injection_only': True, 'authenticated_current_read': False, 'native_context_and_identity_preserved': True, 'calls': calls})


@pytest.mark.parametrize('value', [True, False, 1, '1.0', None, float('nan'), float('inf'), -float('inf')])
def test_non_binary64_quantity_is_rejected(original, monkeypatch, value):
    calls = registered.producer.reference.forbid(monkeypatch); changed = deepcopy(original)
    changed[2]['samples']['records'][0]['value']['plant_state']['leaf']['value'] = value
    with pytest.raises(public.ProjectionHold): project(changed, 'samples')
    assert all(n == 0 for n in calls.values())


@pytest.mark.parametrize('kind', ['unit', 'extra-quantity', 'extra-state', 'short-array', 'long-array', 'negative-inventory',
    'time', 'elapsed', 'index-bool', 'order', 'root', 'tag', 'total', 'offset-bool', 'extra-page',
    'terminal', 'manifest', 'grid', 'SHA', 'record-id', 'naive-recorded', 'event-code', 'event-SHA', 'extra-event'])
def test_mixed_or_invalid_original_projection_is_rejected(original, monkeypatch, kind):
    calls = registered.producer.reference.forbid(monkeypatch); changed = deepcopy(original); record, terminal, pages = changed
    page = pages['samples']; row = page['records'][0]; view = 'samples'
    if kind == 'unit': row['value']['climate_state']['canopy_sensible_energy']['unit'] = 'W/m2_floor'
    elif kind == 'extra-quantity': row['value']['plant_state']['leaf']['secret'] = 'private'
    elif kind == 'extra-state': row['value']['extra'] = 1
    elif kind == 'short-array': row['value']['cohort_state']['fruit_number'].pop()
    elif kind == 'long-array': row['value']['cohort_state']['fruit_number'].append(deepcopy(row['value']['cohort_state']['fruit_number'][0]))
    elif kind == 'negative-inventory': row['value']['plant_state']['leaf']['value'] = -1.0
    elif kind == 'time': row['time']['at'] = '2026-10-01T00:00:00.123457Z'
    elif kind == 'elapsed': row['value']['elapsed_seconds'] += .000001
    elif kind == 'index-bool': row['time']['step_index'] = True
    elif kind == 'order': page['records'].reverse()
    elif kind == 'root': page['artifact_sha256'] = '0'*64
    elif kind == 'tag': page['version'] = 'crop-cycle-verified-artifact-v1'
    elif kind == 'total': page['total'] += 1
    elif kind == 'offset-bool': page['start'] = True
    elif kind == 'extra-page': page['extra'] = 1
    elif kind == 'terminal': terminal['last_confirmed']['step_index'] -= 1
    elif kind == 'manifest': terminal['manifest']['identity']['rhs_code_sha256'] = '0'*64
    elif kind == 'grid': terminal['time_binding']['step_microseconds'] += 1
    elif kind == 'SHA': record['payload_sha256'] = '0'*64
    elif kind == 'record-id': record['result_id'] = public.storage.VERSION+':'+'0'*64
    elif kind == 'naive-recorded': record['recorded_at'] = record['recorded_at'].replace(tzinfo=None)
    else:
        view = 'events'; event = pages['events']['records'][0]['value']['management']
        if kind == 'event-code': event['code_sha256'] = '0'*64
        elif kind == 'event-SHA': event['event_sha256'] = '0'*64
        else: event['extra'] = 1
    with pytest.raises(public.ProjectionHold): project(changed, view)
    assert all(n == 0 for n in calls.values())


def test_page_ranges_caps_summary_exclusivity_and_serialization_recheck(original, monkeypatch):
    registered.producer.reference.forbid(monkeypatch)
    for view in ('samples', 'events'):
        page = deepcopy(original[2][view]); page['start'] = 1; page['records'] = page['records'][1:2]
        projected = project(original, view, page=page, limit=1)
        assert projected.page.next_offset == 2 and projected.page.records[0].time == public.SolarPoint.model_validate(page['records'][0]['time'])
        page['start'] = page['total']; page['records'] = []
        assert project(original, view, page=page).page.next_offset is None
        for bad in (True, 0, 65 if view == 'samples' else 9):
            with pytest.raises(public.ProjectionHold): project(original, view, limit=bad)
    with pytest.raises(public.ProjectionHold): public.project_solar_result(original[0], original[1], page=original[2]['samples'])
    projected = project(original, 'samples'); projected.page.records.append(projected.page.records[0])
    with pytest.raises(public.ProjectionHold): public._public_bytes(projected)
    with pytest.raises(public.ProjectionHold): public._public_bytes({})


def test_closed_json_schema_and_actual_UTF8_serialization_cap(original, monkeypatch):
    registered.producer.reference.forbid(monkeypatch)
    schema = public.SolarReplay.model_json_schema()
    assert schema['additionalProperties'] is False and 'SolarCohorts' in schema['$defs']
    arrays = schema['$defs']['SolarCohorts']['properties']
    assert all(v['minItems'] == v['maxItems'] == 50 for v in arrays.values())
    value = project(original); wire = public._public_bytes(value).decode()
    with monkeypatch.context() as patch:
        patch.setattr(public.SolarReplay, 'model_dump_json', lambda *_: wire+' '*(public.MAX_RESPONSE_BYTES-len(wire.encode())))
        assert len(public._public_bytes(value)) == public.MAX_RESPONSE_BYTES
        patch.setattr(public.SolarReplay, 'model_dump_json', lambda *_: wire+' '*(public.MAX_RESPONSE_BYTES-len(wire.encode())+1))
        with pytest.raises(public.ProjectionHold): public._public_bytes(value)


def test_signed_energy_and_temperature_types_keep_negative_finite_values(original, monkeypatch):
    registered.producer.reference.forbid(monkeypatch)
    climate = deepcopy(original[1]['last_confirmed']['climate_state'])
    climate['canopy_sensible_energy']['value'] = -1000.0
    climate['air_temperature']['value'] = -5.0
    assert public.Climate.model_validate(climate).model_dump(mode='json') == climate


def test_serialization_rejects_changed_current_code_and_grid(original, monkeypatch):
    registered.producer.reference.forbid(monkeypatch)
    model = project(original, 'samples'); value = model.model_dump(mode='json')
    for block, key, changed in (('model', 'rhs_code_sha256', '0'*64), ('time_grid', 'step_seconds_decimal', '3.0')):
        bad = deepcopy(value); bad['reference'][block][key] = changed
        with pytest.raises((ValueError, public.ProjectionHold)): public.SolarReplay.model_validate(bad)


def test_all_new_ledger_balance_and_ventilation_diagnostics_preserved(original, monkeypatch):
    calls = registered.producer.reference.forbid(monkeypatch)
    assert len(public.Transfers.model_fields)==41 and len(public.Balance.model_fields)==15
    model=project(original,'samples')
    for row, saved in zip(model.page.records,original[2]['samples']['records'],strict=True):
        for key in ('ventilation','solar_heat_composition','solar_par','solar_nir'):
            assert getattr(row.value,key).model_dump(mode='json')==saved['value'][key]
        assert set(row.value.integrated_transfers.model_dump())==set(public.driver.stage.FLUX_UNITS)
    assert all(n==0 for n in calls.values())


@pytest.mark.parametrize('kind',['missing-snapshot-diagnostic','bad-vapor-unit','missing-ledger',
    'missing-partition','old-ledger-schema','changed-stage-policy','missing-event-diagnostic',
    'bad-event-latent-unit','extra-event-private-field'])
def test_new_ventilation_boundary_cannot_be_dropped_or_mixed(original,monkeypatch,kind):
    calls=registered.producer.reference.forbid(monkeypatch);changed=deepcopy(original)
    record,terminal,pages=changed;row=pages['samples']['records'][0]['value'];view='samples'
    if kind=='missing-snapshot-diagnostic':row.pop('ventilation')
    elif kind=='bad-vapor-unit':row['ventilation']['derived']['indoor_vapor_density']['unit']='kg_water/m2_floor'
    elif kind=='missing-ledger':row['integrated_transfers'].pop('ventilation_vapor')
    elif kind=='missing-partition':row['balance_residuals'].pop('ventilation_latent_partition')
    elif kind=='old-ledger-schema':terminal['manifest']['identity']['ledger_schema']='old22'
    elif kind=='changed-stage-policy':terminal['manifest']['identity']['solar_component_policy_sha256']['crop_greenhouse_solar_integration']='0'*64
    else:
        view='events';event=pages['events']['records'][0]['value']
        if kind=='missing-event-diagnostic':event.pop('solar_after')
        elif kind=='bad-event-latent-unit':event['solar_after']['ventilation']['latent_energy']['unit']='J/m2_floor'
        else:event['secret']='private'
    with pytest.raises(public.ProjectionHold):project(changed,view)
    assert all(n==0 for n in calls.values())


def test_new_failure_phase_and_inner_stage_are_typed_without_raw_reason(original):
    point=original[1]['times']['last_confirmed']
    value={'reason_code':'VENTILATION_HOLD','phase':'event-after-solar',
        'inner_failed_stage':'k2','time_meaning':'failed_grid_boundary','time':point}
    assert public.SolarHold.model_validate(value).model_dump(mode='json')==value
    with pytest.raises(ValueError):public.SolarHold.model_validate({**value,'inner_failed_stage':'/private/raw-stage'})


@pytest.mark.parametrize('kind', ['missing-PAR', 'missing-NIR', 'missing-heat', 'PAR-unit', 'NIR-unit',
    'heat-unit', 'missing-PAR-ledger', 'missing-NIR-ledger', 'missing-solar-balance',
    'missing-optics', 'extra-optics', 'missing-reflection-denominator', 'NIR-balance-unit',
    'before-diagnostic', 'after-diagnostic', 'source-code-map', 'source-policy-map',
    'source-map-extra', 'notice-map-extra', 'provenance', 'progress-bytes', 'progress-hash', 'approval'])
def test_solar_fields_provenance_progress_and_identity_cannot_be_dropped(original, monkeypatch, kind):
    calls = registered.producer.reference.forbid(monkeypatch)
    changed = deepcopy(original); record, terminal, pages = changed
    row = pages['samples']['records'][0]['value']; view = 'samples'
    if kind == 'missing-PAR': row.pop('solar_par')
    elif kind == 'missing-NIR': row.pop('solar_nir')
    elif kind == 'missing-heat': row.pop('solar_heat_composition')
    elif kind == 'PAR-unit': row['solar_par']['crop_forcing']['par_above_canopy']['unit'] = 'W/m2_floor'
    elif kind == 'NIR-unit': row['solar_nir']['heat_components']['canopy_absorbed_nir']['unit'] = 'J/m2_floor'
    elif kind == 'heat-unit': row['solar_heat_composition']['canopy_non_solar_heat']['unit'] = 'J/m2_floor'
    elif kind == 'missing-PAR-ledger': row['integrated_transfers'].pop('solar_par_canopy_absorbed')
    elif kind == 'missing-NIR-ledger': row['integrated_transfers'].pop('solar_nir_canopy_absorbed')
    elif kind == 'missing-solar-balance': row['balance_residuals'].pop('canopy_solar_heat_partition')
    elif kind == 'missing-optics': row['solar_nir']['optics'].pop('floor_absorptance')
    elif kind == 'extra-optics': row['solar_nir']['optics']['secret'] = 1.0
    elif kind == 'missing-reflection-denominator': row['solar_nir']['reflection_denominators'].pop('cover_canopy')
    elif kind == 'NIR-balance-unit': row['solar_nir']['partition_budgets']['virtual_nir_energy']['unit'] = '1'
    elif kind in ('before-diagnostic', 'after-diagnostic'):
        view = 'events'; pages['events']['records'][0]['value']['solar_'+kind.split('-')[0]].pop('solar_par')
    elif kind == 'source-code-map': terminal['manifest']['identity']['solar_component_code_sha256']['crop_greenhouse_radiation_nir'] = '0'*64
    elif kind == 'source-policy-map': terminal['manifest']['identity']['solar_component_policy_sha256']['crop_greenhouse_solar_integration'] = '0'*64
    elif kind in ('source-map-extra', 'notice-map-extra'): terminal['manifest']['identity'][kind.split('-')[0]+'_sha256']['extra'] = '0'*64
    elif kind == 'progress-bytes': record['progress_raw'] += b' '
    elif kind == 'progress-hash': record['progress_sha256'] = '0'*64
    else:
        packet = json.loads(record['payload_raw'])
        if kind == 'approval': packet['rights_or_gate_approval'] = True
        else: packet['input']['provenance_sha256'] = '0'*64
        record['payload_raw'] = public.storage._canonical(packet)
        record['payload_sha256'] = sha256(record['payload_raw']).hexdigest()
    with pytest.raises(public.ProjectionHold): project(changed, view)
    assert all(v == 0 for v in calls.values())


@pytest.mark.parametrize('bad', [True, 0, 1, None, 'false'])
def test_public_false_approval_requires_exact_boolean(original, bad):
    value = project(original).model_dump(mode='json'); value['reference']['rights_or_gate_approval'] = bad
    with pytest.raises(ValueError): public.SolarReplay.model_validate(value)


def test_public_provenance_progress_and_both_event_diagnostics_are_preserved(original):
    record, terminal, pages = original; packet = json.loads(record['payload_raw'])
    value = project(original).model_dump(mode='json')
    assert value['reference']['rights_or_gate_approval'] is False
    assert value['reference']['progress_sha256'] == record['progress_sha256']
    assert value['reference']['input']['provenance_sha256'] == packet['input']['provenance_sha256']
    events = project(original, 'events').model_dump(mode='json')['page']['records']
    for actual, expected in zip(events, pages['events']['records'], strict=True):
        for key in ('solar_before','solar_after'):
            assert actual['value'][key] == expected['value'][key]


def test_owned_hold_and_private_error_fallback_keep_original_boundary(tmp_path, profiles, monkeypatch):
    case = owned_result(tmp_path, profiles, held=True)
    calls = registered.producer.reference.forbid(monkeypatch)
    record, terminal, pages = case; assert terminal['status'] == 'hold'
    for view in ('summary','samples','events'):
        value = project(case, view).model_dump(mode='json')
        assert value['reference']['failed_boundary'] == terminal['times']['hold']
        if view == 'summary':
            assert value['summary']['last_confirmed']['value'] == terminal['last_confirmed']
            assert value['summary']['checkpoint_sha256'] is None
    altered = deepcopy(case); altered[1]['hold']['reason'] = 'private path: /private/owned-input'
    packet = json.loads(record['payload_raw']); progress = packet['policies']['server_progress']
    progress['hold'] = altered[1]['hold']; progress_raw = public.storage._canonical(progress)
    raw = public.storage._packet(public.storage._canonical(packet['binding']), progress_raw, packet['policies']['resolver_version'])
    altered[0].update(result_id=json.loads(raw)['result_id'],payload_raw=raw,payload_sha256=sha256(raw).hexdigest(),
        progress_raw=progress_raw,progress_sha256=sha256(progress_raw).hexdigest())
    model = project(altered); assert model.summary.hold.reason_code == 'CALCULATION_HOLD'
    assert b'/private/' not in public._public_bytes(model) and all(v==0 for v in calls.values())
