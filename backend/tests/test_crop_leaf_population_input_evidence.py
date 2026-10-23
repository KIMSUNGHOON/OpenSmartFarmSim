"""Leaf source evidence remains structural and keeps the parent review current."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import importlib
import hmac
import json

import pytest

from test_crop_morphology_input_evidence import (
    ROOT, canonical, prepared as stem_prepared, reidentify, review as stem_review,
    authority as stem_authority, arguments as stem_arguments,
)

KEY = b'owned-leaf-source-software-test-key-32!'
DECISION = datetime(2026, 10, 22, tzinfo=timezone.utc)
SCOPE = 'synthetic_leaf_population_input_structure_only'
QC = 'leaf-population-program-structure-provenance-v1'


def variables(program):
    rows = []
    def visit(value, path):
        if isinstance(value, dict) and 'unit' in value:
            rows.append({'name': path, 'original_unit': value['unit'], 'time_semantics': 'instant',
                'interval_start': None, 'interval_end': None, 'provider_qc_status': 'not_supplied', 'provider_qc_value': None})
        elif isinstance(value, dict):
            for key, child in value.items(): visit(child, f'{path}.{key}' if path else key)
        elif isinstance(value, list):
            for index, child in enumerate(value): visit(child, f'{path}.{index}')
    visit(program, '')
    return rows


def prepared(redistribute=True):
    program = json.loads((ROOT/'fixtures/crop-leaf-population-software-program-v1.json').read_bytes())
    program['rights']['redistribute'] = redistribute
    return source_for(canonical(program))


def source_for(raw):
    program = json.loads(raw)
    _, parent_source = stem_prepared()
    record = json.loads(parent_source)['provenance']
    record.update(scope={**record['scope'], 'product_id': program['program_id'], 'product_version': program['schema_version']},
        revision_id=program['rights']['revision'], observed_at='2026-10-21T23:45:00Z', published_at='2026-10-21T23:45:01Z',
        available_at='2026-10-21T23:45:02Z', retrieved_at='2026-10-21T23:45:03Z',
        raw_sha256=sha256(raw).hexdigest(), source_evidence_id='owned-leaf-review',
        synthetic_method='explicit synthetic leaf population software input')
    record['variables'] = variables(program)
    record['project_checks'] = [{'variable': row['name'], 'name': 'structural_software_contract', 'version': QC,
        'status': 'passed', 'evidence_id': 'owned-leaf-review', 'reviewer': 'owned-fixture-reviewer'} for row in record['variables']]
    for right in record['rights']:
        right.update(evidence_id='owned-leaf-review', status='denied' if right['action']=='redistribute' and not program['rights']['redistribute'] else 'allowed')
    source = {'schema_version': 'leaf-population-input-source-v1', 'program_sha256': sha256(raw).hexdigest(), 'provenance': record}
    return raw, reidentify(source)


def review(source):
    return {'evidence_id': 'owned-leaf-review', 'reviewer_id': 'owned-fixture-reviewer', 'decision_id': 'owned-leaf-decision',
        'source_sha256': sha256(source).hexdigest(), 'status': 'accepted_for_software_validation', 'scope': SCOPE}


def configured(model, raw, source, *, leaf_resolver=None, parent_resolver=None):
    parent_model = importlib.import_module('app.crop_morphology_input_evidence')
    parent_raw, parent_source = stem_prepared()
    parent = stem_authority(parent_model, parent_source)
    parent_args = {**stem_arguments(parent_raw, parent_source), 'decision_at': DECISION}
    parent_args['evidence_raw'] = parent.issue(**parent_args)
    if parent_resolver is not None:
        parent = stem_authority(parent_model, parent_source, parent_resolver)
    server = model.LeafPopulationInputEvidenceAuthority(integrity_key=KEY, issuer_id='owned-software',
        key_id='owned-leaf-key-v1', review_resolver=leaf_resolver or (lambda _: review(source)), stem_input_authority=parent)
    args = {'program_raw': raw, 'source_raw': source, 'expected_program_sha256': sha256(raw).hexdigest(),
        'expected_source_sha256': sha256(source).hexdigest(), 'review_id': 'owned-leaf-review',
        'decision_at': DECISION, 'stem_arguments': parent_args}
    return server, args


@pytest.fixture
def model():
    return importlib.import_module('app.crop_leaf_population_input_evidence')


@pytest.mark.parametrize('redistribute', [True, False])
def test_roundtrip_preserves_original_units_parent_and_denied_redistribution(model, redistribute):
    raw, source = prepared(redistribute); server, args = configured(model, raw, source)
    before = deepcopy(args); evidence = server.issue(**args); result = server.verify(evidence_raw=evidence, **args)
    metadata = result.metadata; parent = args['stem_arguments']; program = json.loads(raw)
    assert metadata['source_record'] == json.loads(source)['provenance']
    assert metadata['variable_count'] == len(variables(program))
    assert metadata['redistribution_allowed'] is redistribute
    assert metadata['parent_stem_program_sha256'] == program['stem']['program_sha256']
    assert metadata['parent_stem_evidence_sha256'] == sha256(parent['evidence_raw']).hexdigest()
    assert metadata['initialization_sha256'] == sha256(canonical(program['initialization'])).hexdigest()
    assert metadata['births_sha256'] == sha256(canonical(program['births'])).hexdigest()
    assert metadata['stem_artifact_root_verified'] is False and result.rights_or_gate_approval is False
    units = {r['name']: r['original_unit'] for r in metadata['source_record']['variables']}
    assert units['births.0.emerged_elapsed_seconds_exact']=='s'
    assert units['births.0.curve.values.steepness']=='1/degC_day'
    assert units['births.0.initial_area']=='m2'
    metadata['source_record']['rights'][0]['status']='denied'
    assert result.metadata != metadata and args==before and KEY not in evidence
    payload=json.loads(evidence)['payload']
    assert payload['scope']==SCOPE and payload['gates']=='not_assessed'
    assert payload['numerical_initial_state_validation'] is False


@pytest.mark.parametrize('change', ['source-schema','source-extra','raw-hash','product','revision','real-source','author',
    'missing-unit','duplicate-unit','unit','time-semantics','provider-qc','qc-version','qc-reviewer',
    'rights','redistribution','source-reviewer','observation','availability','retrieval','declaration',
    'record-id','url-secret'])
def test_source_mutations_hold_after_rehashing_public_metadata(model, change):
    raw, source=prepared(); p=json.loads(raw); s=json.loads(source); r=s['provenance']
    if change=='source-schema':s['schema_version']='leaf-population-input-source-v0'
    elif change=='source-extra':s['approved']=True
    elif change=='raw-hash':r['raw_sha256']='0'*64
    elif change=='product':r['scope']['product_id']='other'
    elif change=='revision':r['revision_id']='other'
    elif change=='real-source':r.update(synthetic=False,synthetic_author=None,synthetic_method=None)
    elif change=='author':r['synthetic_author']=None
    elif change=='missing-unit':r['variables'].pop()
    elif change=='duplicate-unit':r['variables'].append(deepcopy(r['variables'][0]))
    elif change=='unit':r['variables'][0]['original_unit']='kg'
    elif change=='time-semantics':r['variables'][0]['time_semantics']='mean'
    elif change=='provider-qc':r['variables'][0]['provider_qc_status']='passed'
    elif change=='qc-version':r['project_checks'][0]['version']='other'
    elif change=='qc-reviewer':r['project_checks'][0]['reviewer']='other'
    elif change=='rights':r['rights'][0]['status']='denied'
    elif change=='redistribution':r['rights'][-1]['status']='denied'
    elif change=='source-reviewer':r['source_reviewer']='other'
    elif change=='observation':r['observed_at']='2026-10-21T22:00:00Z'
    elif change=='availability':r['available_at']='2026-10-22T00:00:00.000001Z'
    elif change=='retrieval':r['retrieved_at']='2026-10-21T23:44:00Z'
    elif change=='declaration':p['rights']['declared_at_utc']='2026-10-21T23:50:00Z';raw=canonical(p);s['program_sha256']=r['raw_sha256']=sha256(raw).hexdigest()
    elif change=='url-secret':r['scope']['source_url']='https://example.org/data?token=secret'
    source=reidentify(s) if change!='record-id' else canonical(s|{'provenance':r|{'record_id':'0'*64}})
    server,args=configured(model,raw,source)
    with pytest.raises(model.LeafPopulationInputEvidenceHold):server.issue(**args)


@pytest.mark.parametrize('change',['stem-program','parent-evidence','parent-decision','birth-order','duplicate-id','unit','curve-origin','unknown-field'])
def test_program_and_parent_mismatches_hold(model,change):
    raw,_=prepared();p=json.loads(raw)
    if change=='stem-program':p['stem']['program_sha256']='0'*64
    elif change=='birth-order':p['births'].reverse()
    elif change=='duplicate-id':p['births'][0]['leaf_id']=p['initialization']['initial_inventory']['leaves'][0]['initialization']['clock_state']['leaf_id']
    elif change=='unit':p['births'][0]['initial_area']['unit']='kg'
    elif change=='curve-origin':p['births'][0]['curve']['origin']='measured'
    elif change=='unknown-field':p['approved']=True
    raw,source=source_for(canonical(p));server,args=configured(model,raw,source)
    if change=='parent-evidence':args['stem_arguments']['evidence_raw']=b'{}'
    elif change=='parent-decision':args['stem_arguments']['decision_at']=DECISION.replace(hour=1)
    with pytest.raises(model.LeafPopulationInputEvidenceHold):server.issue(**args)


@pytest.mark.parametrize('who',['leaf','parent'])
@pytest.mark.parametrize('late',[False,True])
def test_current_and_late_review_revocation_hold_issue_and_verify(model,who,late):
    raw,source=prepared();server,args=configured(model,raw,source);evidence=server.issue(**args)
    _,parent_source=stem_prepared();calls=0
    def revoked(_):
        nonlocal calls
        calls+=1;value=review(source) if who=='leaf' else stem_review(parent_source)
        if not late or calls>1:value['status']='revoked'
        return value
    kwargs={'leaf_resolver':revoked} if who=='leaf' else {'parent_resolver':revoked}
    other,args=configured(model,raw,source,**kwargs)
    with pytest.raises(model.LeafPopulationInputEvidenceHold):other.verify(evidence_raw=evidence,**args)
    calls=0
    with pytest.raises(model.LeafPopulationInputEvidenceHold):other.issue(**args)


def test_evidence_signature_and_config_binding_hold(model):
    raw,source=prepared();server,args=configured(model,raw,source);evidence=server.issue(**args)
    doc=json.loads(evidence);doc['payload']['scope']='approved_for_farm'
    with pytest.raises(model.LeafPopulationInputEvidenceHold):server.verify(evidence_raw=canonical(doc),**args)
    server.key_id='other'
    with pytest.raises(model.LeafPopulationInputEvidenceHold):server.issue(**args)


def test_arbitrary_stem_root_remains_explicitly_unverified(model):
    raw,_=prepared();p=json.loads(raw);p['stem']['artifact_sha256']='0'*64
    raw,source=source_for(canonical(p));server,args=configured(model,raw,source)
    result=server.verify(evidence_raw=server.issue(**args),**args)
    assert result.metadata['stem_artifact_sha256']=='0'*64
    assert result.metadata['stem_artifact_root_verified'] is False


@pytest.mark.parametrize('change',['version','code','metadata','extra','past','future'])
def test_resigned_semantic_evidence_changes_still_hold(model,change):
    raw,source=prepared();server,args=configured(model,raw,source);doc=json.loads(server.issue(**args));payload=doc['payload']
    if change=='version':payload['version']='other'
    elif change=='code':payload['code_sha256'][next(iter(payload['code_sha256']))]='0'*64
    elif change=='metadata':payload['metadata_sha256']='0'*64
    elif change=='extra':payload['approved']=True
    elif change=='past':payload['validated_at']=(DECISION-timedelta(seconds=1)).isoformat().replace('+00:00','Z')
    elif change=='future':payload['validated_at']=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat().replace('+00:00','Z')
    doc['hmac_sha256']=hmac.new(KEY,model.DOMAIN+canonical(payload),'sha256').hexdigest()
    with pytest.raises(model.LeafPopulationInputEvidenceHold):server.verify(evidence_raw=canonical(doc),**args)


@pytest.mark.parametrize('field',['program_raw','source_raw','evidence_raw'])
def test_raw_byte_limits_hold(model,field):
    raw,source=prepared();server,args=configured(model,raw,source);evidence=server.issue(**args)
    limit={'program_raw':model.reader.MAX,'source_raw':model.SOURCE_MAX,'evidence_raw':model.EVIDENCE_MAX}[field]
    args={**args,'evidence_raw':evidence,field:b' '*(limit+1)}
    with pytest.raises(model.LeafPopulationInputEvidenceHold):server.verify(**args)


@pytest.mark.parametrize('change',['code','model','paths'])
def test_runtime_source_model_or_module_drift_holds(model,monkeypatch,change):
    raw,source=prepared();server,args=configured(model,raw,source)
    if change=='code':monkeypatch.setattr(model,'_pins',lambda:{})
    elif change=='model':monkeypatch.setattr(model.reader,'POPULATION_MODEL_VERSIONS',{})
    elif change=='paths':monkeypatch.setattr(model.reader,'SOURCE_PATHS',())
    with pytest.raises(model.LeafPopulationInputEvidenceHold):server.issue(**args)


def test_leaf_revocation_during_final_parent_review_holds(model):
    raw,source=prepared();leaf=review(source);_,parent_source=stem_prepared();calls=0
    def parent_review(_):
        nonlocal calls
        calls+=1
        if calls==4:leaf['status']='revoked'
        return stem_review(parent_source)
    server,args=configured(model,raw,source,leaf_resolver=lambda _:dict(leaf),parent_resolver=parent_review)
    with pytest.raises(model.LeafPopulationInputEvidenceHold):server.issue(**args)
