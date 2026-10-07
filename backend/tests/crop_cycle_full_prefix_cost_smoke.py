"""Manual registered whole-input prefix costs, never a whole-cycle completion."""
from copy import deepcopy
from datetime import datetime, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter

import pytest

from app import crop_cycle_calculation_context as engine
from app import crop_cycle_calculation_server_custody as custody
from app import crop_cycle_result_read_context as original_read
from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from app.thermal_run_store import _canonical
from crop_cycle_full_calendar_registration_smoke import (farm_setup, authoring,
    audit_registration, save, POLICY)
from crop_cycle_calculation_prefix_cost_smoke import driver, tree
from test_crop_cycle_calculation_result_store_farms import login_scope, original_login_scope, counts
from test_crop_cycle_farm_binding import SyntheticInputRights
from test_crop_cycle_input_evidence import authority
from test_crop_cycle_result_evidence import authority as original_authority
from test_api_crop_cycle_calculation_tls import Inputs, SERVER_KEY, DB_KEY
from test_farm_authoring_storage import request as farm_request
from login_database import login_database


def packet():
    paths = {'derived':Path(os.environ['OSSF_FULL_CALENDAR_INPUTS']),
        'original':Path(os.environ['OSSF_FULL_ORIGINAL_INPUTS']),
        'artifact':Path(os.environ['OSSF_FULL_ORIGINAL_ARTIFACT']),
        'proofs':Path(os.environ['OSSF_FULL_ORIGINAL_RESULT_PROOFS'])}
    receipt_raw = Path(os.environ['OSSF_FULL_CALENDAR_RECEIPT']).read_bytes()
    receipt = json.loads(receipt_raw)
    root = Path(__file__).resolve().parents[2]
    accepted = json.loads((root/'research/artifacts/crop-cycle-full166-calendar-registration-reference-20261008.json').read_bytes())
    assert sha256(receipt_raw).hexdigest() == accepted['preparation']['translation_receipt_sha256']
    assert receipt['target_root_sha256'] == '05a58cc9092682f663bb3e2f827003f51ec8a778f746bb429126a663e841fc04'
    proof = Path(os.environ['OSSF_FULL_CALENDAR_PROOF']).read_bytes()
    assert sha256(proof).hexdigest() == accepted['preparation']['proof_sha256']
    return paths, receipt, proof


def original_rows(paths, counts, *, advance_count):
    root = 'ab24eda4d763d7fe3faff1ae3c7c2f84fbec030af71a494bf284fef1f2cdcd98'
    artifact_sha = '15b609576243c73b67a4947b5affc2db14047787e4851064b3aabeafd3d0286d'
    input_proof = (paths['proofs']/'input-evidence.json').read_bytes()
    result_proof = (paths['proofs']/'result-evidence.json').read_bytes()
    head = (paths['artifact']/'HEAD').read_bytes()
    rows = {}; started = perf_counter()
    with original_read.open_result_read_context(paths['artifact'], artifact_sha, paths['original'], root,
            input_proof, result_proof, authority=original_authority()) as reader:
        assert reader.rights_or_gate_approval is False
        for kind in ('samples','events'):
            selected = []; offset = 0
            while offset < counts[kind]:
                page = reader.page(kind, offset, min(64 if kind == 'samples' else 8, counts[kind]-offset))
                assert page['next'] > offset
                selected.extend(page['records']); offset = page['next']
            assert len(selected) == counts[kind]
            for row in selected:
                row['at'] = (datetime.fromisoformat(row['at'].replace('Z','+00:00'))
                             +timedelta(days=273)).isoformat().replace('+00:00','Z')
            rows[kind] = selected
        root_raw = (paths['artifact']/(artifact_sha+'.json')).read_bytes()
        assert sha256(root_raw).hexdigest() == artifact_sha
        root_record = json.loads(root_raw)
        commit_sha = root_record['commits'][advance_count-1]
        commit_raw = (paths['artifact']/(commit_sha+'.json')).read_bytes()
        assert sha256(commit_raw).hexdigest() == commit_sha
        commit = json.loads(commit_raw)
        assert commit['sequence'] == advance_count
        checkpoint = deepcopy(commit['result']['checkpoint'])
        for node, key in ((checkpoint,'at'), (checkpoint['clock'],'segment_start')):
            node[key] = (datetime.fromisoformat(node[key].replace('Z','+00:00'))
                         +timedelta(days=273)).isoformat().replace('+00:00','Z')
        reader.recheck()
    assert reader.closed and not reader._cache and head == (paths['artifact']/'HEAD').read_bytes()
    return rows, {'artifact_sha256':artifact_sha, 'input_root_sha256':root,
        'input_evidence_sha256':sha256(input_proof).hexdigest(),
        'result_evidence_sha256':sha256(result_proof).hexdigest(),
        'original_HEAD_sha256':sha256(head).hexdigest(), 'offset_days':273,
        'selected_rows':counts, 'selected_commit_sha256':commit_sha, 'advance_count':advance_count,
        'shifted_source_checkpoint':checkpoint, 'wall_seconds':perf_counter()-started}


def same_checkpoint_values(left, right):
    excluded = {'version','root_sha256','checkpoint_sha256','parent_sha256',
                'output_prefix_sha256','event_prefix_sha256'}
    return {key:value for key,value in left.items() if key not in excluded} == {
            key:value for key,value in right.items() if key not in excluded}


def test_original_full_reference_matches_small_derived_calculation(monkeypatch):
    paths, receipt, proof = packet()
    issuer = authority()
    with engine.open_calculation_context(paths['derived'], receipt['target_root_sha256'],
            proof, authority=issuer) as context:
        result = engine.advance_chunk(context, engine.start(context), {'max_steps':125,'max_transitions':128})
    assert context.reader.closed and not context._cache and not context.reader._cache
    assert result['status'] == 'yielded' and result['steps'] == 123
    with monkeypatch.context() as no_math:
        no_math.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('reference read ran RHS'))
        expected, reference = original_rows(paths, {kind:len(result[kind]) for kind in ('samples','events')}, advance_count=1)
    assert expected == {kind:result[kind] for kind in ('samples','events')}
    assert same_checkpoint_values(result['checkpoint'], reference['shifted_source_checkpoint'])
    changed = deepcopy(result['checkpoint']); changed['y'][0] += 1
    assert not same_checkpoint_values(changed, reference['shifted_source_checkpoint'])
    save('reference-preflight-verified.json', {'scope':'derived_full166_small_calculation_and_original_stored_prefix_only',
        'steps':result['steps'], 'counts':{kind:len(result[kind]) for kind in ('samples','events')},
        'original_rows_exact_after_explicit_shift':True, 'reference':reference,
        'context_closed_caches_empty':True, 'whole_cycle_accepted':False})


@pytest.mark.parametrize('original_login_scope', [POLICY], indirect=True)
def test_actual_full166_registered_prefix_cost_and_original_checkpoint(
        audit_registration, authoring, tmp_path, driver, monkeypatch):
    paths, receipt, proof = packet()
    original_input = tree(paths['original']); original_artifact = tree(paths['artifact'])
    derived_input = tree(paths['derived'])
    farms, farm_body, principal = authoring
    body = deepcopy(farm_body)
    body['farm']['scenario_id'] = body['rights']['scenario_id'] = 'owned-full166-cost-farm'
    body['rights']['declaration_id'] = 'owned-full166-cost-rights'
    body['farm']['crops'][0]['occupancy']['end'] = '2027-03-16T00:00:00Z'
    body['farm']['crops'][0]['release_at'] = '2027-03-17T00:00:00Z'
    registered = farms.submit('tenant-1', farm_request(body))
    principal['scopes'].update(set(READ_SCOPES) | set(WRITE_SCOPES))
    issuer = authority(); rights = SyntheticInputRights(); resolver = Inputs()
    resolver.values[receipt['target_root_sha256']] = (paths['derived'], proof)
    binding = CalculationFarmBinding(farms, issuer, input_rights=rights)
    request = {'study_id':'owned-full166-prefix-cost', 'revision':'r1', 'farm':{
        'scenario_id':body['farm']['scenario_id'], 'scenario_revision':body['farm']['scenario_revision'],
        'registration_sha256':registered.scenario_sha256, 'crop_id':'crop-1'},
        'input':{'schema_version':engine.inputs.VERSION, 'root_sha256':receipt['target_root_sha256'],
                 'program_id':receipt['target_program_id']},
        'rights':{'schema_version':'crop-cycle-input-rights-v1',
            'declaration_id':'owned-full166-cost-input-rights','revision':'r1',
            'input_root_sha256':receipt['target_root_sha256'], 'available_at':body['farm']['decision_at'],
            'redistribute':False,
            **{key:True for key in ('ownership_asserted','access','store','transform','use','display')}}}
    raw = _canonical(request); directory = tmp_path/'registered-server'; directory.mkdir(mode=0o700)
    server = custody.CalculationServerCustody(binding, directory, input_resolver=resolver, integrity_key=SERVER_KEY)
    before = counts(binding); observed = []
    def sink(row):
        observed.append(row); save('full166-advance-'+str(len(observed))+'.json', row)
    report = driver.profile_registered_prefix(server, raw, tenant='tenant-1',
        budget={'max_steps':10000,'max_transitions':128},
        max_advances=int(os.environ.get('OSSF_FULL_PREFIX_MAX_ADVANCES','32')),
        wall_budget_seconds=900, on_advance=sink)
    save('full166-prefix-profile.json', report)
    assert report['growth_curve'] == observed and 1 <= len(observed) <= 32
    assert report['last_progress']['status'] == 'yielded'
    assert 0 < report['last_progress']['steps'] < report['last_progress']['planned_steps'] == 1816704
    assert report['read_rhs_calls'] == 0 and report['fresh_service_checkpoint_exact']
    assert report['descriptors_before'] == report['descriptors_after']
    for name in ('rhs','farm.registration_read','market.validate_pinned','economics.calculate',
                 'economics.verified_arithmetic','market.source_read','artifact.prefix_verify'):
        assert report['costs'][name]['calls'] > 0
    immutable = tree(directory)
    with monkeypatch.context() as no_math:
        no_math.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('full prefix read ran RHS'))
        with server._open('tenant-1', raw, False) as journal:
            head, _ = journal.writer._head()
            _, checkpoint, summary, index, count = journal.writer._load_prefix(journal.context, journal.notice, head)
            selected = {}
            for kind in ('samples','events'):
                rows = []
                for descriptor in index[kind]:
                    page, _ = journal.writer._records([{key:value for key,value in descriptor.items() if key != 'start'}])
                    rows.extend(page)
                selected[kind] = rows
        assert checkpoint == report['checkpoint'] and summary['status'] == 'yielded'
        expected, reference = original_rows(paths, count, advance_count=len(observed))
        assert expected == selected
        assert same_checkpoint_values(checkpoint, reference['shifted_source_checkpoint'])
        store = CalculationCycleCropResultStore(server, integrity_key=DB_KEY)
        with pytest.raises(custody.CalculationCustodyHold): store.put('tenant-1', raw)
        rights.allowed = False
        try:
            with pytest.raises(custody.CalculationCustodyHold): server.inspect('tenant-1', raw)
        finally: rights.allowed = True
        principal['scopes'].remove('crop_result_read')
        try:
            with pytest.raises(PermissionError): server.inspect('tenant-1', raw)
        finally: principal['scopes'].add('crop_result_read')
    assert tree(directory) == immutable and counts(binding) == before
    assert tree(paths['original']) == original_input and tree(paths['artifact']) == original_artifact
    assert tree(paths['derived']) == derived_input
    assert all(c.reader.closed and not c._cache and not c.reader._cache for c in resolver.opened)
    save('full166-prefix-verified.json', {'scope':'derived_full166_registered_initial_prefix_measurement_only',
        'calculation':report, 'reference':reference, 'original_rows_and_checkpoint_values_equal':True,
        'yielded_not_published':True, 'current_rights_and_principal_denied':True,
        'original_and_derived_inputs_and_original_result_preserved':True,
        'original_artifact_files':len(original_artifact), 'row_counts_before_after':[before,counts(binding)],
        'all_owned_contexts_closed_caches_empty':True, 'whole166_cycle_accepted':False,
        'actual_crop_Runs':0, 'gates':'not_assessed'})
