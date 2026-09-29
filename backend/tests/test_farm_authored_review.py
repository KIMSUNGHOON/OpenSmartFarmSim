"""Owned authored input review admission; synthetic authorities, no release."""

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cli_contracts import ProposalHold
from app.calculation_assessment import CalculationAssessmentService
from app.farm_authored_review import (FarmAuthoredReviewContract,
    FarmAuthoredReviewService, FarmAuthoredReviewHold, INPUT_VERSION)
from app.jobs import canonical_input_bytes
from app.market_result_store import MarketResultStore
from app.owned_cli_contracts import OwnedCliContractRouter
from app.owned_collection_review import OwnedCollectionReviewService
from app.owned_fixture_collection import CollectionService
from test_farm_authoring_storage import authoring, request
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope


@pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,
    'break_even_calculation':True}],indirect=True)
def test_owned_authored_review_intent_and_cli_contract(authoring,login_scope,monkeypatch):
    author,body,principal=authoring
    principal['scopes'].add('collection_review_create')
    registration=author.submit('tenant-1',request(body))
    review=FarmAuthoredReviewService(author)
    value=review.prepare('tenant-1','farm-1','r1',registration.scenario_sha256)
    assert value['input_version']==INPUT_VERSION
    assert len(value['trace_sha256'])==2 and value['candidate_id']
    raw=canonical_input_bytes(value)
    assert b'latitude' not in raw and b'longitude' not in raw
    assert b'capex' not in raw and b'floor_area' not in raw
    first=review.submit('tenant-1','farm-1','r1',registration.scenario_sha256,'farm-review-r1')
    assert first['stage']=='collection_review' and first['state']=='queued'
    assert review.submit('tenant-1','farm-1','r1',registration.scenario_sha256,
        'farm-review-r1')['job_id']==first['job_id']
    with author.replay.jobs.connect() as conn:
        stored=author.replay.jobs._locked_job(conn,'tenant-1',first['job_id'])
        author.replay.jobs._verified_input(stored)
    assert review.verify_input(stored,json.loads(stored['input_bytes']))==value
    contract=FarmAuthoredReviewContract(review)
    parsed,authority=contract.input_context(stored)
    assert parsed['candidate_ids']==[value['candidate_id']]
    assert authority.allow_proceed and authority.missing_evidence==()
    proposal={'schema_version':'decision_v1','stage':'collection_review',
        'input_sha256':stored['input_sha256'],'proposed_status':'proceed',
        'selected_ids':[value['candidate_id']],'rejected_ids':[],
        'claims':[],'missing_evidence':[],'reason':'Synthetic input bindings checked.',
        **{name:value[name] for name in ('decision_context_id','decision_at_utc',
            'claim_mode','decision_time_kind')}}
    plan=contract.plan(stored,canonical_input_bytes(proposal))
    assert plan.disposition=='proceed'
    artifact=json.loads(plan.artifact)
    assert artifact['registration_sha256']==registration.scenario_sha256
    assert artifact['trace_sha256']==value['trace_sha256']
    replay=author.replay
    jobs=replay.jobs
    runs=replay.thermal.runs
    results=MarketResultStore(jobs._dsn,jobs.schema,replay.candidates,
        principal_provider=jobs.principal_provider,runtime_identity=jobs.runtime_identity)
    assessment=CalculationAssessmentService(jobs,runs,results,replay.thermal,replay)
    owned_review=OwnedCollectionReviewService(
        CollectionService(jobs,replay.owned_research.registry),runs)
    router=OwnedCliContractRouter(replay.owned_research,owned_review,assessment,
        lambda *_:None,review)
    assert router.input_context(stored)[0]['candidate_ids']==[value['candidate_id']]
    assert router.plan(stored,canonical_input_bytes(proposal)).artifact==plan.artifact
    assert author.replay.thermal.runs.get_run('tenant-1',value['candidate_id']) is None
    with pytest.raises(ProposalHold):
        contract.plan(stored,canonical_input_bytes({**proposal,'claims':[
            {'claim':'crop prediction','uncertainty':'none','evidence_ids':[]}]}))
    principal['scopes'].remove('collection_review_create')
    with pytest.raises(PermissionError):
        review.submit('tenant-1','farm-1','r1',registration.scenario_sha256,'later')
    principal['scopes'].add('collection_review_create')
    monkeypatch.setattr(author.replay.candidates._source._source,
        'get_input_rights',lambda *_:None)
    with pytest.raises(FarmAuthoredReviewHold):
        review.verify_input(stored,json.loads(stored['input_bytes']))
