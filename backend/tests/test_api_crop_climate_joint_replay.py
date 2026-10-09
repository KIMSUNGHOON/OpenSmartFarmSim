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

from app import api_crop_climate_joint_replay as public
from app import crop_climate_joint_storage as files
import test_crop_climate_joint_input_evidence as inputs
import test_crop_climate_joint_result_store as registered
from test_crop_climate_joint_result_store import login_database, original_login_scope, login_scope, authoring, farm_setup, setup

profiles = inputs.profiles
ROOT = Path(__file__).resolve().parents[2]


def save(name, value):
    root = os.environ.get('OSSF_JOINT_PROJECTION_EVIDENCE')
    if root:
        with (Path(root)/name).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2); f.flush(); os.fsync(f.fileno())


@pytest.fixture(scope='module')
def database_cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    assert schemas == roles == 0
    save('database-cleanup.json', {'schemas': schemas, 'roles': roles})


@pytest.fixture(scope='module')
def original(tmp_path_factory, profiles):
    path = tmp_path_factory.mktemp('owned-joint-projection')
    p = inputs.packet(path/'inputs', profiles, origin=inputs.reference.origin('2026-10-01T00:00:00.123456Z'))
    c = files.continuation; binding = p[2]; initial = c.start(binding._context); chunk = c.advance_chunk(binding._context, initial, 128)
    root = path/'artifact'; root.mkdir(mode=0o700)
    with files.create_writer(root, binding, initial) as writer:
        writer.append(chunk, expected_chunk_sha256=files.clock.source_chunk_sha256(binding._context, chunk)); digest = writer.finalize()
    with files.open_artifact(root, digest) as reader:
        terminal = {**reader.summary, 'manifest': binding._context.manifest, 'time_binding': binding.manifest}
        pages = {k: reader.page(k) for k in ('samples', 'events')}
    reference = json.loads((ROOT/'research/artifacts/crop-climate-joint-result-store-reference-20261010.json').read_bytes())
    packet = reference['stages'][0]['evidence']['normal.json']['packet']
    assert digest == packet['artifact']['sha256'] and binding._context.root_sha256 == packet['input']['context_sha256']
    raw = public.storage._canonical(packet)
    record = {'result_id': packet['result_id'], 'payload_raw': raw, 'payload_sha256': sha256(raw).hexdigest(),
        'recorded_at': datetime(2026, 10, 9, 20, 0, 0, 123456, tzinfo=timezone.utc)}
    return record, terminal, pages


def project(case, view='summary', *, page=None, limit=None):
    record, terminal, pages = case
    if view != 'summary':
        page = pages[view] if page is None else page; limit = (64 if view == 'samples' else 8) if limit is None else limit
    return public.project_joint_result(record, terminal, view=view, page=page, limit=limit)


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
        'original_inputs_unchanged': True, 'calls': calls, 'FD_before_after': [fd, fd], 'authenticated_current_read': False})


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
        assert projected.page.next_offset == 2 and projected.page.records[0].time == public.Point.model_validate(page['records'][0]['time'])
        page['start'] = page['total']; page['records'] = []
        assert project(original, view, page=page).page.next_offset is None
        for bad in (True, 0, 65 if view == 'samples' else 9):
            with pytest.raises(public.ProjectionHold): project(original, view, limit=bad)
    with pytest.raises(public.ProjectionHold): public.project_joint_result(original[0], original[1], page=original[2]['samples'])
    projected = project(original, 'samples'); projected.page.records.append(projected.page.records[0])
    with pytest.raises(public.ProjectionHold): public._public_bytes(projected)
    with pytest.raises(public.ProjectionHold): public._public_bytes({})


def test_closed_json_schema_and_actual_UTF8_serialization_cap(original, monkeypatch):
    registered.producer.reference.forbid(monkeypatch)
    schema = public.JointReplay.model_json_schema()
    assert schema['additionalProperties'] is False and 'JointCohorts' in schema['$defs']
    arrays = schema['$defs']['JointCohorts']['properties']
    assert all(v['minItems'] == v['maxItems'] == 50 for v in arrays.values())
    value = project(original); wire = public._public_bytes(value).decode()
    with monkeypatch.context() as patch:
        patch.setattr(public.JointReplay, 'model_dump_json', lambda *_: wire+' '*(public.MAX_RESPONSE_BYTES-len(wire.encode())))
        assert len(public._public_bytes(value)) == public.MAX_RESPONSE_BYTES
        patch.setattr(public.JointReplay, 'model_dump_json', lambda *_: wire+' '*(public.MAX_RESPONSE_BYTES-len(wire.encode())+1))
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
        with pytest.raises((ValueError, public.ProjectionHold)): public.JointReplay.model_validate(bad)


def test_fresh_exec_same_response_bytes_without_any_numerical_entrypoint(original, tmp_path, monkeypatch):
    registered.producer.reference.forbid(monkeypatch); record, terminal, pages = original
    expected = {k: sha256(public._public_bytes(project(original, k))).hexdigest() for k in ('summary', 'samples', 'events')}
    packet = {'record': {**record, 'payload_raw': record['payload_raw'].hex(), 'recorded_at': record['recorded_at'].isoformat()},
        'terminal': terminal, 'pages': pages, 'expected': expected}
    path = tmp_path/'fresh-projection.private.json'; path.write_text(json.dumps(packet)); path.chmod(0o600)
    script = '''import json,sys,os
from pathlib import Path
from datetime import datetime
from hashlib import sha256
from pytest import MonkeyPatch
import test_api_crop_climate_joint_replay as t
p=json.loads(Path(sys.argv[1]).read_bytes());r=p['record'];r['payload_raw']=bytes.fromhex(r['payload_raw']);r['recorded_at']=datetime.fromisoformat(r['recorded_at'])
with MonkeyPatch.context() as patch:
 calls=t.registered.producer.reference.forbid(patch)
 actual={k:sha256(t.public._public_bytes(t.project((r,p['terminal'],p['pages']),k))).hexdigest() for k in ('summary','samples','events')}
 assert actual==p['expected'] and all(n==0 for n in calls.values())
print(json.dumps({'PID':os.getpid(),'response_sha256':actual,'calls':calls}))
'''
    child = subprocess.run([sys.executable, '-B', '-c', script, str(path)], capture_output=True,
        timeout=30, env=dict(os.environ, PYTHONPATH=registered.producer.FRESH_PYTHONPATH))
    assert child.returncode == 0, child.stderr.decode(); result = json.loads(child.stdout)
    assert not Path('/proc', str(result['PID'])).exists(); save('fresh.json', result)


@pytest.mark.parametrize('original_login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)
@pytest.mark.parametrize('setup', [None, 'hold'], indirect=True)
def test_actual_scram_registered_completed_and_hold_result_projection(setup, monkeypatch, database_cleanup):
    result, raw, value, done = registered.ready(setup)
    record = result.put('tenant-1', raw); farm = value[1]['farm']
    calls = registered.producer.reference.forbid(monkeypatch); before = registered.producer.reference.counts(result.server.binding)
    terminal = result.summary('tenant-1', record['result_id'], farm)
    pages = {k: result.page('tenant-1', record['result_id'], farm, k) for k in ('samples', 'events')}
    case = record, terminal, pages; state = json.loads(done)['status']; hashes = {}
    for view in ('summary', 'samples', 'events'):
        model = project(case, view); hashes[view] = sha256(public._public_bytes(model)).hexdigest()
        assert model.reference.artifact.status == state
        if view == 'summary':
            assert model.summary.last_confirmed.value.model_dump(mode='json') == terminal['last_confirmed']
            assert (model.summary.hold is not None) == (state == 'hold')
    if state == 'hold':
        bad = deepcopy(pages['samples']); bad['records'][-1] = {'value': terminal['last_confirmed'], 'time': terminal['times']['last_confirmed']}
        with pytest.raises(public.ProjectionHold): project(case, 'samples', page=bad)
        changed_terminal = deepcopy(terminal); changed_record = deepcopy(record); packet = json.loads(record['payload_raw'])
        changed_terminal['hold']['reason'] = 'private host path: /private/owned-record'
        packet['policies']['server_progress']['hold'] = changed_terminal['hold']
        packet['result_id'] = public.storage.VERSION+':'+sha256(public.storage._canonical({k: v for k, v in packet.items() if k != 'result_id'})).hexdigest()
        changed_raw = public.storage._canonical(packet)
        changed_record.update(result_id=packet['result_id'], payload_raw=changed_raw, payload_sha256=sha256(changed_raw).hexdigest())
        fallback = public.project_joint_result(changed_record, changed_terminal)
        assert fallback.summary.hold.reason_code == 'CALCULATION_HOLD' and b'/private/' not in public._public_bytes(fallback)
    assert registered.producer.reference.counts(result.server.binding) == before and all(n == 0 for n in calls.values())
    save('actual-'+state+'.json', {'actual_scram': True, 'status': state, 'response_sha256': hashes,
        'counts_unchanged': True, 'calls': calls, 'G0_G4': 'not_assessed', 'actual_crop_Runs': 0})
