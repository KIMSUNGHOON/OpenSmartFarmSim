"""Closed original Co2 prefix schema and quantities; pure projection is not access."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from uuid import uuid4
import pytest
from app import api_crop_greenhouse_co2_prefix as model
import test_api_crop_greenhouse_co2_replay as terminal
import test_crop_greenhouse_co2_prefix as prefix
profiles = terminal.profiles

def save(name, value):
    root = os.environ.get('OSSF_CO2_PREFIX_PROJECTION_EVIDENCE')
    if root:
        with (Path(root) / (name + '.json')).open('x') as f:
            os.fchmod(f.fileno(), 256)
            json.dump(value, f, sort_keys=True, indent=2)
            f.flush()
            os.fsync(f.fileno())

def record(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return model.current.PrefixRead(raw, sha256(raw).hexdigest())

def project(value, source_program):
    projected = model.project_prefix(record(value), source_program=source_program)
    raw = model._public_bytes(projected)
    assert model.PrefixReplay.model_validate_json(raw).model_dump(mode='json') == projected.model_dump(mode='json')
    assert 0 < len(raw) <= model.MAX_RESPONSE_BYTES
    return json.loads(raw)

def owned_case(path, profiles, case=None):
    saved, result, pages, program = terminal.owned_result(path, profiles, case=case)
    packet = json.loads(saved['payload_raw'])
    p = packet['policies']['server_progress']
    cp_store = model.current.checkpoints
    cp = {'version': cp_store.VERSION, 'scope': model.current.custody.SCOPE, 'G0_G4': 'not_assessed', 'rights_or_gate_approval': False, 'publication_sequence': 1, 'input_sha256': sha256(b'unregistered projection fixture').hexdigest(), **{k: p[k] for k in ('head_sha256', 'proof_sha256', 'intent_sha256', 'source_sha256', 'context_sha256', 'time_binding_sha256', 'header_sha256', 'artifact_sha256', 'custody_code_sha256', 'status', 'steps', 'planned_steps', 'counts', 'provenance_sha256')}, 'farm_binding_sha256': p['binding_sha256'], 'execution_code_sha256': cp_store.execution.CODE_SHA256, 'checkpoint_code_sha256': cp_store.CODE_SHA256, 'custody_sequence': 1, 'computed_through_utc': result['times']['last_confirmed']['at']}
    cp_store._payload(cp)
    value = {'version': model.current.VERSION, 'scope': model.current.custody.SCOPE, 'claim_scope': model.current.CLAIM_SCOPE, 'G0_G4': 'not_assessed', 'rights_or_gate_approval': False, 'job': {'job_id': str(uuid4()), 'stage': 'simulation', 'state': 'simulating', 'attempt_count': 1, 'max_attempts': 3, 'created_at': '2026-10-09T00:00:00Z', 'updated_at': '2026-10-10T00:00:00Z', 'reason_code': None}, 'cancel_requested': False, 'observed_at': '2026-10-10T01:00:00Z', 'prefix_status': 'accepted', 'selection': {'checkpoint': cp, 'checkpoint_recorded_at': '2026-10-10T00:00:00Z', 'checkpoint_attempt': 1}, 'binding': packet['binding'], 'manifest': result['manifest'], 'time_binding': result['time_binding'], 'summary': {'counts': result['counts'], 'last_sample_utc': pages['samples']['records'][-1]['time']['at'], 'last_event_utc': pages['events']['records'][-1]['time']['at']}, 'page': None}
    public_pages = {k: {'kind': k, 'start': 0, 'limit': 64 if k == 'samples' else 8, 'total': v['total'], 'next_offset': None, 'records': v['records']} for k, v in pages.items()}
    return (value, public_pages, program)

@pytest.fixture(scope='module')
def original(tmp_path_factory, profiles):
    return owned_case(tmp_path_factory.mktemp('owned-co2-prefix-projection'), profiles)


@pytest.fixture(scope='module')
def basis_transition(tmp_path_factory, profiles):
    case=deepcopy(terminal.inputs.producer.reference.BY_ID['weather-multiple'])
    case['forcing_program'][1]['co2']['basis']='dry'
    return owned_case(tmp_path_factory.mktemp('owned-co2-prefix-basis-transition'), profiles, case)


def page_case(original, kind):
    value = deepcopy(original[0])
    value.update(summary=None, page=deepcopy(original[1][kind]))
    return value

def inspect_private(value):
    forbidden = {'tenant_id', 'registration_job_id', 'rights', 'review', 'reviewer_id', 'parameters', 'forcing', 'scenario', 'origin', 'event', 'payload_raw', 'integrity_signature', 'hmac_sha256', 'intent_sha256', 'farm_binding_sha256', 'lease_token', 'dsn', 'provenance'}
    if isinstance(value, dict):
        assert not forbidden.intersection(value)
        for v in value.values():
            inspect_private(v)
    elif isinstance(value, list):
        for v in value:
            inspect_private(v)

def test_original_values_units_UTC_and_closed_whitelist(original, monkeypatch):
    before = deepcopy(original)
    output = {}
    fd = len(os.listdir('/proc/self/fd'))
    with monkeypatch.context() as patch:
        calls = prefix.reference.forbid(patch)
        for kind in ('summary', 'samples', 'events'):
            case = original[0] if kind == 'summary' else page_case(original, kind)
            value = project(case, original[2])
            output[kind] = value
            assert value['reference']['selector'] == prefix.selector(case)
            assert value['reference']['checkpoint']['checkpoint_recorded_at'] == case['selection']['checkpoint_recorded_at']
            assert value['rights_or_gate_approval'] is value['reference']['rights_or_gate_approval'] is False
            assert value['reference']['checkpoint']['provenance_sha256'] == value['reference']['input']['provenance_sha256']
            if kind == 'summary':
                assert value['summary'] == case['summary'] and value['page'] is None
            elif kind == 'samples':
                raw_page = deepcopy(value['page'])
                bases = {r['step_index']: r['co2']['basis'] for r in original[2]['forcing_program']}
                for row in raw_page['records']:
                    assert row.pop('co2_basis') == bases[row['value']['forcing_step_index']]
                assert model.current.execution._same(raw_page, case['page'])
            else:
                assert model.current.execution._same(value['page']['records'], [model.public._event(r, case['manifest']['identity'], model.public._basis_map(original[2], case['manifest'])) for r in case['page']['records']])
            inspect_private(value)
        assert not any(calls.values())
    assert original == before and len(os.listdir('/proc/self/fd')) == fd
    save('pure-original', {'original_values_units_UTC': True, 'private_fields_absent': True, 'calls': calls, 'response_bytes': {k: len(model.public.storage._canonical(v)) for k, v in output.items()}, 'FD_unchanged': True, 'unregistered_pure_fixture_not_current_access': True})

@pytest.mark.parametrize('bad', [True, False, 1, '1.0', None, float('nan'), float('inf'), -float('inf')])
def test_non_binary64_is_rejected(original, monkeypatch, bad):
    calls = prefix.reference.forbid(monkeypatch)
    case = page_case(original, 'samples')
    case['page']['records'][0]['value']['plant_state']['leaf']['value'] = bad
    with pytest.raises(model.ProjectionHold):
        project(case, original[2])
    assert all((n == 0 for n in calls.values()))

@pytest.mark.parametrize('fault', ['extra-envelope', 'scope', 'claim', 'gate', 'extra-quantity', 'unit', 'array', 'negative', 'UTC', 'elapsed', 'order', 'total', 'start-bool', 'limit-bool', 'next', 'extra-page', 'summary-and-page', 'binding', 'manifest', 'grid', 'checkpoint-time', 'checkpoint-count', 'attempt', 'job-state', 'cancel', 'event-input', 'event-code', 'event-state-extra'])
def test_mixed_invalid_projection_is_rejected(original, monkeypatch, fault):
    calls = prefix.reference.forbid(monkeypatch)
    case = page_case(original, 'samples')
    page = case['page']
    row = page['records'][0]
    if fault == 'extra-envelope':
        case['secret'] = 'hidden'
    elif fault == 'scope':
        case['scope'] = 'approved'
    elif fault == 'claim':
        case['claim_scope'] = 'crop_prediction'
    elif fault == 'gate':
        case['G0_G4'] = 'passed'
    elif fault == 'extra-quantity':
        row['value']['plant_state']['leaf']['secret'] = 'hidden'
    elif fault == 'unit':
        row['value']['plant_state']['leaf']['unit'] = 'kg'
    elif fault == 'array':
        row['value']['cohort_state']['fruit_number'].pop()
    elif fault == 'negative':
        row['value']['plant_state']['leaf']['value'] = -1.0
    elif fault == 'UTC':
        row['time']['at'] = '2026-10-01T00:00:00.123457Z'
    elif fault == 'elapsed':
        row['value']['elapsed_seconds'] += 1e-06
    elif fault == 'order':
        page['records'].reverse()
    elif fault == 'total':
        page['total'] += 1
    elif fault == 'start-bool':
        page['start'] = True
    elif fault == 'limit-bool':
        page['limit'] = True
    elif fault == 'next':
        page['next_offset'] = 1
    elif fault == 'extra-page':
        page['private'] = 'hidden'
    elif fault == 'summary-and-page':
        case['summary'] = original[0]['summary']
    elif fault == 'binding':
        case['binding']['request']['study_id'] = 'mixed-study'
    elif fault == 'manifest':
        case['manifest']['identity']['rhs_code_sha256'] = '0' * 64
    elif fault == 'grid':
        case['time_binding']['step_microseconds'] += 1
    elif fault == 'checkpoint-time':
        case['selection']['checkpoint']['computed_through_utc'] = '2026-10-01T00:00:00Z'
    elif fault == 'checkpoint-count':
        case['selection']['checkpoint']['counts']['samples'] = 513
    elif fault == 'attempt':
        case['selection']['checkpoint_attempt'] = 2
    elif fault == 'job-state':
        case['job']['state'] = 'succeeded'
    elif fault == 'cancel':
        case['cancel_requested'] = True
    else:
        case = page_case(original, 'events')
        m = case['page']['records'][0]['value']['management']
        if fault == 'event-input':
            m['event']['secret'] = 'changed'
        elif fault == 'event-code':
            m['code_sha256'] = '0' * 64
        else:
            m['before']['scenario']['extra'] = 'hidden'
    with pytest.raises(model.ProjectionHold):
        project(case, original[2])
    assert all((n == 0 for n in calls.values()))

def test_end_pages_limits_summary_and_byte_revalidation(original, monkeypatch):
    calls = prefix.reference.forbid(monkeypatch)
    for kind in ('samples', 'events'):
        case = page_case(original, kind)
        page = case['page']
        page.update(start=1, limit=1, records=page['records'][1:2], next_offset=2)
        assert project(case, original[2])['page']['next_offset'] == 2
        page.update(start=page['total'], records=[], next_offset=None)
        assert project(case, original[2])['page']['records'] == []
        for bad in (0, 65 if kind == 'samples' else 9):
            page['limit'] = bad
            with pytest.raises(model.ProjectionHold):
                project(case, original[2])
    for name, bad in [('last_sample_utc', None), ('last_event_utc', '2026-10-01T00:00:00.123457Z')]:
        case = deepcopy(original[0])
        case['summary'][name] = bad
        with pytest.raises(model.ProjectionHold):
            project(case, original[2])
    projected = model.project_prefix(record(page_case(original, 'samples')), source_program=original[2])
    projected.root.page.records.append(projected.root.page.records[0])
    with pytest.raises(model.ProjectionHold):
        model._public_bytes(projected)
    with pytest.raises(model.ProjectionHold):
        model.project_prefix(model.current.PrefixRead(b'{}', '0' * 64), source_program=original[2])
    with pytest.raises(model.ProjectionHold):
        model.project_prefix({}, source_program=original[2])
    assert all((n == 0 for n in calls.values()))

def test_closed_discriminated_schema_and_UTF8_cap(original, monkeypatch):
    prefix.reference.forbid(monkeypatch)
    schema = model.PrefixReplay.model_json_schema()
    assert set(schema['discriminator']['mapping']) == {'none', 'closed', 'accepted'}
    assert all((schema['$defs'][name]['additionalProperties'] is False for name in ('NoPrefix', 'AcceptedPrefix', 'PrefixReference')))
    assert schema['$defs']['Co2Cohorts']['properties']['fruit_number']['minItems'] == 50
    projected = model.project_prefix(record(original[0]), source_program=original[2])
    wire = model._public_bytes(projected).decode()
    with monkeypatch.context() as patch:
        patch.setattr(model.PrefixReplay, 'model_dump_json', lambda *_: wire + ' ' * (model.MAX_RESPONSE_BYTES - len(wire.encode())))
        assert len(model._public_bytes(projected)) == model.MAX_RESPONSE_BYTES
        patch.setattr(model.PrefixReplay, 'model_dump_json', lambda *_: wire + ' ' * (model.MAX_RESPONSE_BYTES - len(wire.encode()) + 1))
        with pytest.raises(model.ProjectionHold):
            model._public_bytes(projected)
    save('schema', {'discriminators': ['none', 'closed', 'accepted'], 'closed_allowlists': True, 'array_length': 50, 'actual_serialized_UTF8_cap': model.MAX_RESPONSE_BYTES, 'serialization_fault_injection': True})

@pytest.mark.parametrize('status', ['none', 'closed', 'ready'])
def test_empty_none_closed_ready_without_invented_rows(original, monkeypatch, status):
    calls = prefix.reference.forbid(monkeypatch)
    case = deepcopy(original[0])
    if status != 'ready':
        case.update(prefix_status=status, **dict.fromkeys(('selection', 'binding', 'manifest', 'time_binding', 'summary', 'page')))
        case['job']['state'] = 'queued' if status == 'none' else 'canceled'
        case['cancel_requested'] = status == 'closed'
        with pytest.raises(model.ProjectionHold):
            project(case, original[2])
        result = project(case, None)
        assert result['reference'] is result['summary'] is result['page'] is None
    else:
        cp = case['selection']['checkpoint']
        cp.update(status='ready', steps=0, counts={'samples': 0, 'events': 0}, artifact_sha256=None, computed_through_utc=None)
        case['summary'] = {'counts': cp['counts'], 'last_sample_utc': None, 'last_event_utc': None}
        assert project(case, original[2])['summary'] == case['summary']
        case.update(summary=None, page={'kind': 'samples', 'start': 0, 'limit': 64, 'total': 0, 'next_offset': None, 'records': []})
        assert project(case, original[2])['page']['records'] == []
    assert all((n == 0 for n in calls.values()))

@pytest.mark.parametrize('field', ['engine_code_sha256', 'driver_code_sha256', 'short_code_sha256', 'management_code_sha256', 'rhs_code_sha256', 'component_code_sha256', 'policy_sha256', 'profile_sha256', 'transport_helpers_code_sha256', 'co2_solar_component_code_sha256', 'co2_solar_policy_sha256'])
def test_current_model_code_and_policy_identity_rejects_mixed_values(original, field):
    value = project(original[0], original[2])
    identity = value['reference']['manifest']['identity']
    if isinstance(identity[field], dict):
        identity[field][next(iter(identity[field]))] = '0' * 64
    else:
        identity[field] = '0' * 64
    value['reference']['input']['context_sha256'] = model.public.continuation._hash(value['reference']['manifest'])
    with pytest.raises(ValueError):
        model.PrefixReplay.model_validate(value)

@pytest.mark.parametrize('fault', ['approval', 'approval-zero', 'approval-string', 'reference-approval', 'checkpoint-approval', 'provenance', 'normalization', 'applicability', 'normalization-version', 'qc-version', 'input-evidence-version'])
def test_approval_provenance_and_applicability_are_closed(original, fault):
    value = project(original[0], original[2])
    ref = value['reference']
    if fault == 'approval':
        value['rights_or_gate_approval'] = True
    elif fault == 'approval-zero':
        value['rights_or_gate_approval'] = 0
    elif fault == 'approval-string':
        value['rights_or_gate_approval'] = 'false'
    elif fault == 'reference-approval':
        ref['rights_or_gate_approval'] = True
    elif fault == 'checkpoint-approval':
        ref['checkpoint']['rights_or_gate_approval'] = True
    elif fault == 'provenance':
        ref['input']['provenance_sha256'] = '0' * 64
    elif fault == 'normalization':
        ref['normalization'] = 'per_plant'
    elif fault == 'applicability':
        ref['profile_applicability'] = 'validated'
    else:
        ref[fault.replace('-', '_')] = 'future-version'
    with pytest.raises(ValueError):
        model.PrefixReplay.model_validate(value)

@pytest.mark.parametrize('field', ['solar_par_canopy_absorbed', 'solar_nir_canopy_absorbed', 'canopy_non_solar_heat'])
def test_original_solar_integrated_units_required(original, field):
    case = page_case(original, 'samples')
    case['page']['records'][0]['value']['integrated_transfers'][field]['unit'] = 'K'
    with pytest.raises(model.ProjectionHold):
        project(case, original[2])

@pytest.mark.parametrize('field', ['canopy_solar_heat_partition', 'interior_PAR_partition', 'exterior_PAR_partition', 'virtual_NIR_partition', 'exterior_virtual_NIR_partition'])
def test_original_solar_partition_residuals_required(original, field):
    case = page_case(original, 'samples')
    del case['page']['records'][0]['value']['balance_residuals'][field]
    with pytest.raises(model.ProjectionHold):
        project(case, original[2])

def test_other_reader_record_and_untrusted_facade_are_rejected(original):
    from app.crop_greenhouse_ventilation_prefix import PrefixRead as OtherRead
    good = record(original[0])
    with pytest.raises(model.ProjectionHold):
        model.project_prefix(OtherRead(good.payload_raw, good.payload_sha256), source_program=original[2])
    with pytest.raises(model.ProjectionHold):
        model.read_prefix(object(), 'tenant-1', original[0]['job']['job_id'])


def test_every_sample_and_event_uses_its_original_wet_dry_basis(basis_transition, monkeypatch):
    original=basis_transition
    calls=prefix.reference.forbid(monkeypatch)
    program=original[2]
    before=deepcopy(original)
    bases={row['step_index']:row['co2']['basis'] for row in program['forcing_program']}
    observed=set()
    for kind in ('samples','events'):
        value=project(page_case(original,kind),program)
        for row in value['page']['records']:
            assert row['co2_basis']==bases[row['value']['forcing_step_index']]
            observed.add(row['co2_basis'])
        if kind=='samples':
            preserved=deepcopy(value['page']['records'])
            for row in preserved:row.pop('co2_basis')
            assert preserved==original[1]['samples']['records']
    assert observed=={'wet','dry'}
    assert original==before and not any(calls.values())
    save('pure-basis-transition',{'explicit_32s_owned_program_reexecuted':True,
        'changed_input_only':'forcing_program[1].co2.basis= dry',
        'numeric_coefficients_unchanged':True,'program_sha256':original[0]['manifest']['program_sha256'],
        'basis_by_forcing_index':bases,'sample_values_units_UTC_preserved':True,
        'all_sample_and_event_basis_matches_original_forcing':True,'calls':calls,
        'independent_crop_validation':False})


@pytest.mark.parametrize('fault',['missing','missing-forcing','changed-basis','changed-program','unknown-index','extra-row-basis','co2-unit','co2-ledger','carbon-ledger'])
def test_co2_program_basis_and_original_quantity_contracts(original, monkeypatch, fault):
    calls=prefix.reference.forbid(monkeypatch)
    case=page_case(original,'samples');program=deepcopy(original[2])
    row=case['page']['records'][0]
    if fault=='missing':program=None
    elif fault=='missing-forcing':del program['forcing_program']
    elif fault=='changed-basis':
        block=program['forcing_program'][0]['co2'];block['basis']='dry' if block['basis']=='wet' else 'wet'
    elif fault=='changed-program':program['step_count']+=1
    elif fault=='unknown-index':row['value']['forcing_step_index']=4096
    elif fault=='extra-row-basis':row['co2_basis']='wet'
    elif fault=='co2-unit':row['value']['climate_state']['air_co2_mass']['unit']='kg'
    elif fault=='co2-ledger':del row['value']['balance_residuals']['air_co2']
    else:del row['value']['balance_residuals']['crop_air_carbon_equivalent']
    with pytest.raises(model.ProjectionHold):project(case,program)
    assert not any(calls.values())
