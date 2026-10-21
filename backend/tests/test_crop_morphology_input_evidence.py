"""Source/review checks for the existing public synthetic rational program."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import hmac
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
KEY = b'owned-morphology-software-test-key-32!'
DECISION = datetime(2026, 10, 21, 18, tzinfo=timezone.utc)
SCOPE = 'synthetic_morphology_input_structure_only'
QC = 'morphology-program-structure-provenance-v1'
GROWTH = ['crop_rational_shoot_inventory', 'crop_rational_new_internodes', 'crop_rational_internode_length',
          'crop_rational_morphology_clock', 'crop_shoot_inventory', 'crop_new_internodes', 'crop_shoot_timeline',
          'crop_phytomer_emergence', 'crop_internode_length', 'crop_internode_length_change',
          'crop_morphology_thermal_clock', 'crop_internode_elongation']


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def variables(p):
    found = {}
    def walk(v, path):
        if isinstance(v, dict):
            if 'unit' in v:
                found[path] = {'name': path, 'original_unit': v['unit'], 'time_semantics': 'instant',
                    'interval_start': None, 'interval_end': None, 'provider_qc_status': 'not_supplied', 'provider_qc_value': None}
            else:
                for k, child in v.items():
                    sub = f'{path}.{k}' if path else k
                    if k in ('sequence', 'next_sequence', 'inventory_start_sequence'):
                        found[sub] = {'name': sub, 'original_unit': '1', 'time_semantics': 'instant',
                            'interval_start': None, 'interval_end': None, 'provider_qc_status': 'not_supplied', 'provider_qc_value': None}
                    else:
                        walk(child, sub)
        elif isinstance(v, list):
            for i, child in enumerate(v): walk(child, f'{path}.{i}')
    walk(p, '')
    for i, s in enumerate(p['segments']):
        found[f'segments.{i}.air_temperature'].update(time_semantics='mean', interval_start=s['start_utc'], interval_end=s['end_utc'])
    return [found[k] for k in sorted(found)]


def reidentify(source):
    r = source['provenance']; r['record_id'] = sha256(canonical({k: v for k, v in r.items() if k != 'record_id'})).hexdigest()
    return canonical(source)


def prepared(redistribute=True):
    p = json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes())
    p['rights']['redistribute'] = redistribute
    raw = canonical(p); unit_rows = variables(p)
    r = {'schema_version': '1', 'scope': {'provider': 'self-authored-software-fixture', 'product_id': p['program_id'],
        'product_version': p['schema_version'], 'source_url': 'https://github.com/KIMSUNGHOON/OpenSmartFarmSim', 'station_or_grid_id': None},
        'revision_id': p['rights']['revision'], 'request_details': [], 'observed_at': '2026-10-21T17:40:17Z',
        'published_at': '2026-10-21T17:40:18Z', 'available_at': '2026-10-21T17:40:19Z',
        'retrieved_at': '2026-10-21T17:40:20Z', 'valid_from': None, 'valid_to': None,
        'variables': unit_rows, 'project_checks': [{'variable': v['name'], 'name': 'structural_software_contract',
            'version': QC, 'status': 'passed', 'evidence_id': 'owned-morphology-review', 'reviewer': 'owned-fixture-reviewer'} for v in unit_rows],
        'rights': [{'action': k, 'status': 'denied' if k == 'redistribute' and not redistribute else 'allowed',
            'evidence_id': 'owned-morphology-review', 'reviewer': 'owned-fixture-reviewer'}
            for k in ('access', 'store', 'transform', 'display', 'redistribute')],
        'raw_sha256': sha256(raw).hexdigest(), 'synthetic': True, 'synthetic_author': 'owned-fixture-author',
        'synthetic_method': 'explicit synthetic constant-air calculation software input',
        'source_reviewer': 'owned-fixture-reviewer', 'source_evidence_id': 'owned-morphology-review'}
    source = {'schema_version': 'morphology-input-source-v1', 'program_sha256': sha256(raw).hexdigest(), 'provenance': r}
    return raw, reidentify(source)


def review(source):
    return {'evidence_id': 'owned-morphology-review', 'reviewer_id': 'owned-fixture-reviewer', 'decision_id': 'owned-morphology-decision',
        'source_sha256': sha256(source).hexdigest(), 'status': 'accepted_for_software_validation', 'scope': SCOPE}


@pytest.fixture
def model():
    return importlib.import_module('app.crop_morphology_input_evidence')


def authority(model, source, resolver=None, **kw):
    return model.MorphologyInputEvidenceAuthority(integrity_key=kw.get('key', KEY), issuer_id=kw.get('issuer', 'owned-software'),
        key_id=kw.get('key_id', 'owned-key-v1'), review_resolver=resolver or (lambda _: review(source)))


def arguments(raw, source):
    return {'program_raw': raw, 'source_raw': source, 'expected_program_sha256': sha256(raw).hexdigest(),
        'expected_source_sha256': sha256(source).hexdigest(), 'review_id': 'owned-morphology-review', 'decision_at': DECISION}


@pytest.mark.parametrize('redistribute', [True, False])
def test_roundtrip_preserves_original_metadata_and_private_redistribution_denial(model, redistribute):
    raw, source = prepared(redistribute); before = (raw, source); server = authority(model, source)
    evidence = server.issue(**arguments(raw, source)); result = server.verify(**arguments(raw, source), evidence_raw=evidence)
    assert result.program_sha256 == sha256(raw).hexdigest() and result.source_sha256 == sha256(source).hexdigest()
    assert result.evidence_sha256 == sha256(evidence).hexdigest() and result.rights_or_gate_approval is False
    metadata = result.metadata
    assert metadata['source_record'] == json.loads(source)['provenance']
    assert metadata['program_id'] == json.loads(raw)['program_id'] and metadata['variable_count'] == 59
    assert metadata['redistribution_allowed'] is redistribute
    assert metadata['initial_state_sha256'] == sha256(canonical(json.loads(raw)['initial_state'])).hexdigest()
    by_name = {r['name']: r for r in metadata['source_record']['variables']}
    assert by_name['segments.0.air_temperature']['interval_start'] == '2026-10-01T00:00:00Z'
    assert by_name['initial_state.internodes.0.length_state.clock_state.emerged_elapsed_seconds_exact']['original_unit'] == 's'
    assert by_name['initial_state.emergence_profile.curve.values.steepness']['original_unit'] == '1/degC_day'
    assert by_name['initial_state.timeline_state.next_sequence']['original_unit'] == '1'
    metadata['source_record']['rights'][0]['status'] = 'denied'
    assert result.metadata != metadata and (raw, source) == before and KEY not in evidence
    doc = json.loads(evidence)
    assert doc['payload']['scope'] == SCOPE and doc['payload']['gates'] == 'not_assessed'
    assert doc['payload']['numerical_initial_state_validation'] is False


@pytest.mark.parametrize('change', ['source-schema', 'source-extra', 'raw-hash', 'source-program', 'record-id', 'real-source',
    'author', 'product', 'version', 'revision', 'station', 'request', 'validity', 'url-secret', 'publication', 'availability',
    'retrieval', 'observed', 'unit', 'missing-unit', 'duplicate-unit', 'extra-unit', 'semantics', 'interval', 'provider-qc',
    'project-qc', 'project-version', 'project-kind', 'project-reviewer', 'source-reviewer', 'rights', 'right-reviewer',
    'redistribution', 'missing-right', 'clock-fraction', 'output-time', 'declaration-time',
    'model-clock-as-observation', 'observation-after-publication', 'declaration-after-retrieval'])
def test_semantically_changed_sources_hold_after_updating_all_public_content_hashes(model, change):
    raw, source = prepared(); p, s = json.loads(raw), json.loads(source); r = s['provenance']
    if change == 'source-schema': s['schema_version'] = 'morphology-input-source-v0'
    elif change == 'source-extra': s['approved'] = True
    elif change == 'raw-hash': r['raw_sha256'] = '0'*64
    elif change == 'source-program': s['program_sha256'] = '0'*64
    elif change == 'record-id': pass
    elif change == 'real-source': r.update(synthetic=False, synthetic_author=None, synthetic_method=None)
    elif change == 'author': r['synthetic_author'] = None
    elif change == 'product': r['scope']['product_id'] = 'unrelated'
    elif change == 'version': r['scope']['product_version'] = 'v1'
    elif change == 'revision': r['revision_id'] = 'unrelated'
    elif change == 'station': r['scope']['station_or_grid_id'] = 'observed-station'
    elif change == 'request': r['request_details'] = [{'name': 'region', 'value': 'KR'}]
    elif change == 'validity': r.update(valid_from='2026-10-01T00:00:00Z', valid_to='2026-10-02T00:00:00Z')
    elif change == 'url-secret': r['scope']['source_url'] += '?token=forbidden'
    elif change in ('publication', 'availability', 'retrieval', 'observed'):
        r[{'publication': 'published_at', 'availability': 'available_at', 'retrieval': 'retrieved_at', 'observed': 'observed_at'}[change]] = '2026-10-21T18:00:01Z'
    elif change == 'unit': r['variables'][0]['original_unit'] = 'cm'
    elif change == 'missing-unit': r['variables'].pop()
    elif change == 'duplicate-unit': r['variables'].append(deepcopy(r['variables'][0]))
    elif change == 'extra-unit': r['variables'].append({**r['variables'][0], 'name': 'invented'})
    elif change == 'semantics': r['variables'][-1]['time_semantics'] = 'instant'
    elif change == 'interval': r['variables'][-1]['interval_end'] = '2026-10-02T00:00:01Z'
    elif change == 'provider-qc': r['variables'][0].update(provider_qc_status='passed', provider_qc_value='0')
    elif change == 'project-qc': r['project_checks'][0]['status'] = 'unknown'
    elif change == 'project-version': r['project_checks'][0]['version'] = 'unverified'
    elif change == 'project-kind': r['project_checks'][0]['name'] = 'numerical_validation'
    elif change == 'project-reviewer': r['project_checks'][0]['reviewer'] = 'other'
    elif change == 'source-reviewer': r['source_reviewer'] = 'other'
    elif change == 'rights': r['rights'][0]['status'] = 'unknown'
    elif change == 'right-reviewer': r['rights'][0]['reviewer'] = 'other'
    elif change == 'redistribution': r['rights'][-1]['status'] = 'denied'
    elif change == 'missing-right': r['rights'].pop()
    elif change == 'clock-fraction': p['initial_state']['internodes'][0]['length_state']['clock_state']['emerged_elapsed_seconds_exact']['denominator'] = '2'
    elif change == 'output-time': p['output_times'][-1] = '2026-10-03T00:00:00Z'
    elif change == 'declaration-time': p['rights']['declared_at_utc'] = '2026-10-21T18:00:01Z'
    elif change == 'model-clock-as-observation': r['observed_at'] = '2026-10-01T00:00:00Z'
    elif change == 'observation-after-publication': r['observed_at'] = '2026-10-21T17:40:20Z'
    elif change == 'declaration-after-retrieval': p['rights']['declared_at_utc'] = '2026-10-21T17:50:00Z'
    if change in ('clock-fraction', 'output-time', 'declaration-time', 'declaration-after-retrieval'):
        raw = canonical(p); s['program_sha256'] = r['raw_sha256'] = sha256(raw).hexdigest()
    source = reidentify(s)
    if change == 'record-id':
        s = json.loads(source); s['provenance']['record_id'] = '0'*64; source = canonical(s)
    with pytest.raises(model.MorphologyInputEvidenceHold): authority(model, source).issue(**arguments(raw, source))


@pytest.mark.parametrize('change', ['status', 'scope', 'source', 'id', 'extra', 'missing', 'resolver-error', 'late-revoke', 'late-decision'])
def test_current_review_is_required_before_and_after_both_operations(model, change):
    raw, source = prepared(); good = review(source); bad = deepcopy(good)
    if change in ('status', 'scope'): bad[change] = 'unknown'
    elif change == 'source': bad['source_sha256'] = '0'*64
    elif change == 'id': bad['evidence_id'] = 'other'
    elif change == 'extra': bad['approved'] = True
    elif change == 'missing': bad.pop('reviewer_id')
    elif change == 'late-revoke': bad['status'] = 'revoked'
    elif change == 'late-decision': bad['decision_id'] = 'new-decision'
    for operation in ('issue', 'verify'):
        evidence = authority(model, source).issue(**arguments(raw, source)); calls = []
        def resolve(_):
            calls.append(1)
            if change == 'resolver-error': raise RuntimeError('private-error-not-for-public')
            return deepcopy(good if change.startswith('late-') and len(calls) == 1 else bad)
        server = authority(model, source, resolve)
        with pytest.raises(model.MorphologyInputEvidenceHold) as exc:
            getattr(server, operation)(**arguments(raw, source), **({'evidence_raw': evidence} if operation == 'verify' else {}))
        assert 'private-error' not in str(exc.value)
        if change.startswith('late-'): assert len(calls) == 2


@pytest.mark.parametrize('change', ['signature', 'version', 'issuer', 'key-id', 'code', 'program', 'source', 'decision', 'gates', 'math', 'extra'])
def test_signed_receipts_cannot_change_identity_or_claim_scope(model, change):
    raw, source = prepared(); server = authority(model, source); doc = json.loads(server.issue(**arguments(raw, source)))
    p = doc['payload']
    if change == 'signature': doc['hmac_sha256'] = '0'*64
    elif change == 'version': p['version'] = 'other'
    elif change == 'issuer': p['issuer_id'] = 'other'
    elif change == 'key-id': p['key_id'] = 'other'
    elif change == 'code': p['code_sha256'][next(iter(p['code_sha256']))] = '0'*64
    elif change == 'program': p['program_sha256'] = '0'*64
    elif change == 'source': p['source_sha256'] = '0'*64
    elif change == 'decision': p['decision_at'] = '2026-10-21T17:59:59Z'
    elif change == 'gates': p['gates'] = 'G0'
    elif change == 'math': p['numerical_initial_state_validation'] = True
    else: p['farm_approved'] = True
    if change != 'signature': doc['hmac_sha256'] = hmac.new(KEY, model.DOMAIN+canonical(p), 'sha256').hexdigest()
    with pytest.raises(model.MorphologyInputEvidenceHold): server.verify(**arguments(raw, source), evidence_raw=canonical(doc))


@pytest.mark.parametrize('change', ['wrong-program-pin', 'wrong-source-pin', 'noncanonical', 'duplicate', 'source-big', 'program-big',
    'evidence-big', 'naive-decision', 'future-decision', 'bool-key', 'short-key', 'bad-issuer', 'changed-authority', 'changed-code', 'changed-models'])
def test_bounded_original_bytes_and_fixed_server_identity(model, change, monkeypatch):
    raw, source = prepared(); server = authority(model, source); args = arguments(raw, source)
    if change == 'wrong-program-pin': args['expected_program_sha256'] = '0'*64
    elif change == 'wrong-source-pin': args['expected_source_sha256'] = '0'*64
    elif change == 'noncanonical': args['source_raw'] = b' '+source
    elif change == 'duplicate': args['source_raw'] = source[:-1]+b',"schema_version":"morphology-input-source-v1"}'
    elif change == 'source-big': args['source_raw'] = b'x'*(1024**2+1)
    elif change == 'program-big': args['program_raw'] = b'x'*(16*1024**2+1)
    elif change == 'naive-decision': args['decision_at'] = DECISION.replace(tzinfo=None)
    elif change == 'future-decision': args['decision_at'] = datetime.now(timezone.utc)+timedelta(days=1)
    elif change in ('bool-key', 'short-key', 'bad-issuer'):
        with pytest.raises(model.MorphologyInputEvidenceHold):
            authority(model, source, **({'issuer': ' invalid '} if change == 'bad-issuer' else {'key': True if change == 'bool-key' else b'short'}))
        return
    elif change == 'changed-authority': server.key_id = 'other'
    elif change == 'changed-code': monkeypatch.setattr(model, '_current_pins', lambda: {})
    elif change == 'changed-models': monkeypatch.setitem(model.reader.MODEL_VERSIONS, 'clock', 'unverified')
    if change == 'evidence-big':
        with pytest.raises(model.MorphologyInputEvidenceHold): server.verify(**args, evidence_raw=b'x'*(2*1024**2+1))
    else:
        with pytest.raises(model.MorphologyInputEvidenceHold): server.issue(**args)


def test_fresh_issue_and_verify_import_no_growth_models_and_use_no_DB_or_CLI(model, tmp_path):
    raw, source = prepared(); server = authority(model, source); evidence = server.issue(**arguments(raw, source))
    for name, value in [('program', raw), ('source', source), ('evidence', evidence)]: (tmp_path/name).write_bytes(value)
    code = '''import json,sys,subprocess
from pathlib import Path
from datetime import datetime,timezone
from app import crop_morphology_input_evidence as m
from app.job_store import JobStore
def forbidden(*a,**k):raise AssertionError('DB/CLI forbidden')
JobStore.connect=forbidden;subprocess.Popen=forbidden
b=Path(sys.argv[1]);raw=(b/'program').read_bytes();source=(b/'source').read_bytes();evidence=(b/'evidence').read_bytes()
names=json.loads(sys.argv[2]);assert not any('app.'+n in sys.modules for n in names)
review=json.loads(sys.argv[3]);a=m.MorphologyInputEvidenceAuthority(integrity_key=b'owned-morphology-software-test-key-32!',issuer_id='owned-software',key_id='owned-key-v1',review_resolver=lambda _:review)
args=dict(program_raw=raw,source_raw=source,expected_program_sha256=__import__('hashlib').sha256(raw).hexdigest(),expected_source_sha256=__import__('hashlib').sha256(source).hexdigest(),review_id=review['evidence_id'],decision_at=datetime(2026,10,21,18,tzinfo=timezone.utc))
a.issue(**args);v=a.verify(**args,evidence_raw=evidence)
assert not any('app.'+n in sys.modules for n in names) and v.rights_or_gate_approval is False
print(json.dumps(v.metadata,sort_keys=True))
'''
    done = subprocess.run([sys.executable, '-c', code, str(tmp_path), json.dumps(GROWTH), json.dumps(review(source))],
        capture_output=True, text=True, timeout=15)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout) == server.verify(**arguments(raw, source), evidence_raw=evidence).metadata


def test_exact_source_size_boundary_remains_bounded_and_original(model):
    raw, source = prepared(); s = json.loads(source)
    remaining = model.SOURCE_MAX-len(source)
    s['provenance']['synthetic_method'] += 'A'*remaining
    source = reidentify(s)
    assert len(source) == 1024**2
    server = authority(model, source); args = arguments(raw, source)
    evidence = server.issue(**args)
    assert server.verify(**args, evidence_raw=evidence).metadata['source_record'] == json.loads(source)['provenance']
    s['provenance']['synthetic_method'] += 'A'; oversized = reidentify(s)
    assert len(oversized) == 1024**2+1
    with pytest.raises(model.MorphologyInputEvidenceHold): authority(model, oversized).issue(**arguments(raw, oversized))


@pytest.mark.parametrize('stamp', ['2026-10-21T17:59:59.000000Z', '2099-01-01T00:00:00.000000Z',
    '2026-10-22T03:00:00.000000+09:00', '2026-10-21T18:00:00', 'invalid'])
def test_even_signed_validation_times_require_original_utc_and_decision_order(model, stamp):
    raw, source = prepared(); server = authority(model, source); args = arguments(raw, source)
    doc = json.loads(server.issue(**args)); doc['payload']['validated_at'] = stamp
    doc['hmac_sha256'] = hmac.new(KEY, model.DOMAIN+canonical(doc['payload']), 'sha256').hexdigest()
    with pytest.raises(model.MorphologyInputEvidenceHold): server.verify(**args, evidence_raw=canonical(doc))


@pytest.mark.parametrize('change', ['late-code', 'late-key'])
def test_late_server_identity_change_never_returns_a_receipt(model, monkeypatch, change):
    raw, source = prepared(); calls = []; pins = model._current_pins
    monkeypatch.setattr(model, '_current_pins', lambda: {} if change == 'late-code' and len(calls) == 2 else pins())
    def resolve(_):
        calls.append(1)
        if change == 'late-key': server.integrity_key = b'other-known-software-test-key-32!'
        return review(source)
    server = authority(model, source, resolve)
    with pytest.raises(model.MorphologyInputEvidenceHold): server.issue(**arguments(raw, source))


def test_structure_receipt_does_not_certify_numerically_inconsistent_initial_length(model, tmp_path):
    raw, source = prepared(); p, s = json.loads(raw), json.loads(source)
    p['initial_state']['internodes'][0]['length_state']['length']['value'] *= 2
    raw = canonical(p); s['program_sha256'] = s['provenance']['raw_sha256'] = sha256(raw).hexdigest(); source = reidentify(s)
    server = authority(model, source); evidence = server.issue(**arguments(raw, source))
    assert server.verify(**arguments(raw, source), evidence_raw=evidence).rights_or_gate_approval is False
    # The separate numerical producer remains responsible for this check.
    from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
    from app.crop_morphology_artifact_io import MorphologyArtifactHold
    from app.content_access import ContentAccess
    import os
    with pytest.raises(MorphologyArtifactHold):
        produce_rational_morphology_artifact(tmp_path/'invalid-numeric', ContentAccess(os.getuid(), os.getgid()), program_raw=raw)
