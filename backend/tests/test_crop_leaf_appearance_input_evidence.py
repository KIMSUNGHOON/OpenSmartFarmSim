"""Original policy review and initial attachments precede farm publication."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import hmac
import importlib
import json

import pytest

from test_crop_leaf_population_input_evidence import source_for as old_source_for, variables
from test_crop_morphology_input_evidence import (
    ROOT, canonical, reidentify, prepared as stem_prepared, review as stem_review,
    authority as stem_authority, arguments as stem_arguments,
)

KEY = b'owned-appearance-review-software-key-32!'
DECISION = datetime(2026, 10, 23, 16, tzinfo=timezone.utc)
SCOPE = 'synthetic_leaf_appearance_input_structure_only'
QC = 'leaf-appearance-program-structure-provenance-v1'
COUNTERS = ('first_generative_sequence', 'vegetative_between_generative')


def source_for(raw):
    raw, source = old_source_for(raw)
    p, s = json.loads(raw), json.loads(source); record = s['provenance']
    s['schema_version'] = 'leaf-appearance-input-source-v1'
    record.update(observed_at='2026-10-23T14:17:51Z', published_at='2026-10-23T14:17:52Z',
        available_at='2026-10-23T14:17:53Z', retrieved_at='2026-10-23T14:17:54Z',
        source_evidence_id='owned-appearance-review',
        synthetic_method='self-authored explicit appearance policy software fixture; not observed farm data')
    record['variables'] = variables(p) + [{'name': 'policy.'+k, 'original_unit': '1', 'time_semantics': 'instant',
        'interval_start': None, 'interval_end': None, 'provider_qc_status': 'not_supplied', 'provider_qc_value': None}
        for k in COUNTERS]
    record['project_checks'] = [{'variable': row['name'], 'name': 'structural_software_contract', 'version': QC,
        'status': 'passed', 'evidence_id': 'owned-appearance-review', 'reviewer': 'owned-fixture-reviewer'}
        for row in record['variables']]
    for right in record['rights']:right['evidence_id'] = 'owned-appearance-review'
    return raw, reidentify(s)


def prepared(redistribute=True):
    p = json.loads((ROOT/'web/public/leaf-appearance-replay/input.json').read_bytes())
    p['rights']['redistribute'] = redistribute
    return source_for(canonical(p))


def review(source):
    return {'evidence_id': 'owned-appearance-review', 'reviewer_id': 'owned-fixture-reviewer',
        'decision_id': 'owned-appearance-decision', 'source_sha256': sha256(source).hexdigest(),
        'status': 'accepted_for_software_validation', 'scope': SCOPE}


def configured(model, raw, source, *, leaf_resolver=None, parent_resolver=None):
    parent_model = importlib.import_module('app.crop_morphology_input_evidence')
    parent_raw, parent_source = stem_prepared()
    parent = stem_authority(parent_model, parent_source)
    parent_args = {**stem_arguments(parent_raw, parent_source), 'decision_at': DECISION}
    parent_args['evidence_raw'] = parent.issue(**parent_args)
    if parent_resolver is not None:parent = stem_authority(parent_model, parent_source, parent_resolver)
    server = model.LeafAppearanceInputEvidenceAuthority(integrity_key=KEY, issuer_id='owned-software',
        key_id='owned-appearance-key-v1', review_resolver=leaf_resolver or (lambda _:review(source)),
        stem_input_authority=parent)
    return server, {'program_raw': raw, 'source_raw': source, 'expected_program_sha256': sha256(raw).hexdigest(),
        'expected_source_sha256': sha256(source).hexdigest(), 'review_id': 'owned-appearance-review',
        'decision_at': DECISION, 'stem_arguments': parent_args}


@pytest.fixture
def model():
    return importlib.import_module('app.crop_leaf_appearance_input_evidence')


@pytest.mark.parametrize('redistribute', [True, False])
def test_original_policy_profile_units_initial_mapping_and_parent_roundtrip(model, redistribute):
    raw, source = prepared(redistribute); server, args = configured(model, raw, source); before = deepcopy(args)
    evidence = server.issue(**args); result = server.verify(evidence_raw=evidence, **args)
    p, s, m = json.loads(raw), json.loads(source), result.metadata
    assert m['source_record'] == s['provenance'] and m['variable_count'] == len(variables(p))+2
    units = {v['name']:v['original_unit'] for v in m['source_record']['variables']}
    assert all(units['policy.'+key]=='1' for key in COUNTERS)
    assert units['leaf_profile.curve.values.steepness']=='1/degC_day'
    assert units['initialization.initial_inventory.at_elapsed_seconds_exact']=='s'
    for key in ['policy', 'initialization', 'leaf_profile']:
        assert m[key+'_sha256'] == sha256(canonical(p[key])).hexdigest()
    assert m['initial_leaf_count']==3 and m['initial_node_count']==3
    assert m['parent_stem_program_sha256']==p['stem']['program_sha256']
    assert m['parent_stem_evidence_sha256']==sha256(args['stem_arguments']['evidence_raw']).hexdigest()
    assert m['redistribution_allowed'] is redistribute and m['stem_artifact_root_verified'] is False
    assert result.rights_or_gate_approval is False and result.program_sha256==sha256(raw).hexdigest()
    assert len(m['initial_bindings_sha256'])==64 and KEY not in evidence and args==before
    m['source_record']['rights'][0]['status']='denied';assert result.metadata!=m
    payload=json.loads(evidence)['payload'];assert payload['scope']==SCOPE and payload['gates']=='not_assessed'
    assert payload['numerical_initial_state_validation'] is False


@pytest.mark.parametrize('change', ['source-schema','source-extra','raw-hash','product','revision','real-source','author',
    'missing-unit','duplicate-unit','unit','counter-missing','counter-unit','time-semantics','provider-qc','qc-version',
    'qc-reviewer','rights','redistribution','source-reviewer','observation','availability','retrieval','declaration',
    'record-id','url-secret'])
def test_rehashed_source_counter_units_rights_times_and_scope_cannot_bypass_review(model, change):
    raw, source=prepared();p=json.loads(raw);s=json.loads(source);r=s['provenance']
    if change=='source-schema':s['schema_version']='leaf-population-input-source-v1'
    elif change=='source-extra':s['approved']=True
    elif change=='raw-hash':r['raw_sha256']='0'*64
    elif change=='product':r['scope']['product_id']='other'
    elif change=='revision':r['revision_id']='other'
    elif change=='real-source':r.update(synthetic=False,synthetic_author=None,synthetic_method=None)
    elif change=='author':r['synthetic_author']=None
    elif change=='missing-unit':r['variables'].pop(0)
    elif change=='duplicate-unit':r['variables'].append(deepcopy(r['variables'][0]))
    elif change=='unit':r['variables'][0]['original_unit']='kg'
    elif change=='counter-missing':r['variables'].pop()
    elif change=='counter-unit':r['variables'][-1]['original_unit']='degC_day'
    elif change=='time-semantics':r['variables'][0]['time_semantics']='mean'
    elif change=='provider-qc':r['variables'][0]['provider_qc_status']='passed'
    elif change=='qc-version':r['project_checks'][0]['version']='other'
    elif change=='qc-reviewer':r['project_checks'][0]['reviewer']='other'
    elif change=='rights':r['rights'][0]['status']='denied'
    elif change=='redistribution':r['rights'][-1]['status']='denied'
    elif change=='source-reviewer':r['source_reviewer']='other'
    elif change=='observation':r['observed_at']='2026-10-23T14:17:49Z'
    elif change=='availability':r['available_at']='2026-10-23T16:00:00.000001Z'
    elif change=='retrieval':r['retrieved_at']='2026-10-23T14:17:50Z'
    elif change=='declaration':p['rights']['declared_at_utc']='2026-10-23T14:18:00Z';raw=canonical(p);s['program_sha256']=r['raw_sha256']=sha256(raw).hexdigest()
    elif change=='url-secret':r['scope']['source_url']='https://example.org/data?token=secret'
    source=reidentify(s) if change!='record-id' else canonical(s|{'provenance':r|{'record_id':'0'*64}})
    server,args=configured(model,raw,source)
    with pytest.raises(model.LeafAppearanceInputEvidenceHold):server.issue(**args)


@pytest.mark.parametrize('change', ['stem-program','parent-evidence','parent-decision','first-generative',
    'policy-gap-bool','schedule','shoot','attachment-order','attachment-id','birth-time','clock-origin','initial-time',
    'profile-unit','curve-origin','unknown-field'])
def test_policy_initial_attachment_and_verified_parent_must_agree(model, change):
    raw,_=prepared();p=json.loads(raw);leaves=p['initialization']['initial_inventory']['leaves']
    if change=='stem-program':p['stem']['program_sha256']='0'*64
    elif change=='first-generative':p['policy']['first_generative_sequence']=0
    elif change=='policy-gap-bool':p['policy']['vegetative_between_generative']=True
    elif change=='schedule':p['policy']['schedule_id']='other'
    elif change=='shoot':p['policy']['shoot_id']='other'
    elif change=='attachment-order':leaves.reverse()
    elif change=='attachment-id':leaves[0]['attachment_internode_id']='other'
    elif change=='birth-time':leaves[0]['initialization']['clock_state']['emerged_elapsed_seconds_exact']['numerator']='-1'
    elif change=='clock-origin':leaves[0]['initialization']['clock_state']['time_origin_utc']='2026-10-02T00:00:00Z'
    elif change=='initial-time':p['initialization']['initial_inventory']['at_elapsed_seconds_exact']['numerator']='1'
    elif change=='profile-unit':p['leaf_profile']['initial_area']['unit']='kg'
    elif change=='curve-origin':p['leaf_profile']['curve']['origin']='measured'
    elif change=='unknown-field':p['approved']=True
    raw,source=source_for(canonical(p));server,args=configured(model,raw,source)
    if change=='parent-evidence':args['stem_arguments']['evidence_raw']=b'{}'
    elif change=='parent-decision':args['stem_arguments']['decision_at']=DECISION+timedelta(seconds=1)
    with pytest.raises(model.LeafAppearanceInputEvidenceHold):server.issue(**args)


@pytest.mark.parametrize('who', ['leaf','parent'])
@pytest.mark.parametrize('late', [False,True])
def test_current_and_late_revocation_blocks_both_issue_and_verify(model, who, late):
    raw,source=prepared();server,args=configured(model,raw,source);evidence=server.issue(**args)
    _,parent_source=stem_prepared();calls=0
    def revoked(_):
        nonlocal calls
        calls+=1;v=review(source) if who=='leaf' else stem_review(parent_source)
        if not late or calls>1:v['status']='revoked'
        return v
    options={'leaf_resolver':revoked} if who=='leaf' else {'parent_resolver':revoked}
    other,args=configured(model,raw,source,**options)
    with pytest.raises(model.LeafAppearanceInputEvidenceHold):other.verify(evidence_raw=evidence,**args)
    calls=0
    with pytest.raises(model.LeafAppearanceInputEvidenceHold):other.issue(**args)


def test_revocation_during_final_parent_check_is_not_lost(model):
    raw,source=prepared();leaf=review(source);_,parent_source=stem_prepared();calls=0
    def parent_review(_):
        nonlocal calls
        calls+=1
        if calls==4:leaf['status']='revoked'
        return stem_review(parent_source)
    server,args=configured(model,raw,source,leaf_resolver=lambda _:dict(leaf),parent_resolver=parent_review)
    with pytest.raises(model.LeafAppearanceInputEvidenceHold):server.issue(**args)


@pytest.mark.parametrize('change', ['version','code','metadata','extra','past','future','signature'])
def test_resigned_metadata_model_time_and_foreign_signature_hold(model, change):
    raw,source=prepared();server,args=configured(model,raw,source);doc=json.loads(server.issue(**args));p=doc['payload']
    if change=='version':p['version']='other'
    elif change=='code':p['code_sha256'][next(iter(p['code_sha256']))]='0'*64
    elif change=='metadata':p['metadata_sha256']='0'*64
    elif change=='extra':p['approved']=True
    elif change=='past':p['validated_at']=(DECISION-timedelta(seconds=1)).isoformat().replace('+00:00','Z')
    elif change=='future':p['validated_at']=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat().replace('+00:00','Z')
    doc['hmac_sha256']=hmac.new(KEY,model.DOMAIN+canonical(p),'sha256').hexdigest() if change!='signature' else '0'*64
    with pytest.raises(model.LeafAppearanceInputEvidenceHold):server.verify(evidence_raw=canonical(doc),**args)


@pytest.mark.parametrize('field', ['program_raw','source_raw','evidence_raw'])
def test_raw_byte_limits_and_immutable_source_hashes(model, field):
    raw,source=prepared();server,args=configured(model,raw,source);evidence=server.issue(**args)
    limit={'program_raw':model.program.MAX,'source_raw':model.SOURCE_MAX,'evidence_raw':model.EVIDENCE_MAX}[field]
    args={**args,'evidence_raw':evidence,field:b' '*(limit+1)}
    with pytest.raises(model.LeafAppearanceInputEvidenceHold):server.verify(**args)


@pytest.mark.parametrize('change', ['code','model','paths','program-version','display-policy','authority'])
def test_runtime_source_and_authority_binding_cannot_drift(model, monkeypatch, change):
    raw,source=prepared();server,args=configured(model,raw,source)
    if change=='code':monkeypatch.setattr(model,'_pins',lambda:{})
    elif change=='model':monkeypatch.setitem(model.reader.ROOT_CONSTANTS,'model_versions',{})
    elif change=='paths':monkeypatch.setattr(model.reader,'SOURCE_PATHS',())
    elif change=='program-version':monkeypatch.setattr(model.program,'VERSION','other')
    elif change=='display-policy':monkeypatch.setattr(model.program,'DISPLAY_POLICY',{})
    else:server.key_id='other'
    with pytest.raises(model.LeafAppearanceInputEvidenceHold):server.issue(**args)


def test_unbound_stem_artifact_root_is_an_identifier_only(model):
    raw,_=prepared();p=json.loads(raw);p['stem']['artifact_sha256']='0'*64
    raw,source=source_for(canonical(p));server,args=configured(model,raw,source)
    m=server.verify(evidence_raw=server.issue(**args),**args).metadata
    assert m['stem_artifact_sha256']=='0'*64 and m['stem_artifact_root_verified'] is False


def test_changed_valid_policy_cannot_reuse_previous_source_review(model):
    raw,source=prepared();old=review(source);p=json.loads(raw);p['policy']['vegetative_between_generative']=3
    raw,source=source_for(canonical(p));server,args=configured(model,raw,source,leaf_resolver=lambda _:dict(old))
    with pytest.raises(model.LeafAppearanceInputEvidenceHold):server.issue(**args)


def test_new_accepted_source_is_required_for_a_valid_policy_change(model):
    raw,source=prepared();server,args=configured(model,raw,source);old_evidence=server.issue(**args)
    p=json.loads(raw);p['policy']['vegetative_between_generative']=3
    raw,source=source_for(canonical(p));other,args=configured(model,raw,source)
    with pytest.raises(model.LeafAppearanceInputEvidenceHold):other.verify(evidence_raw=old_evidence,**args)
    result=other.verify(evidence_raw=other.issue(**args),**args)
    assert result.metadata['policy_sha256']==sha256(canonical(p['policy'])).hexdigest()


@pytest.mark.parametrize('change', ['wrong-scope','wrong-source','extra','exception','late-decision'])
def test_resolver_must_supply_current_exact_original_policy_review(model, change):
    raw,source=prepared();calls=0
    def resolve(_):
        nonlocal calls
        calls+=1;v=review(source)
        if change=='wrong-scope':v['scope']='synthetic_leaf_population_input_structure_only'
        elif change=='wrong-source':v['source_sha256']='0'*64
        elif change=='extra':v['approved_for_farm']=True
        elif change=='exception':raise RuntimeError('test resolver unavailable')
        elif change=='late-decision' and calls>1:v['decision_id']='other-current-review'
        return v
    server,args=configured(model,raw,source,leaf_resolver=resolve)
    with pytest.raises(model.LeafAppearanceInputEvidenceHold):server.issue(**args)
