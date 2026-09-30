"""Owned authored input review admission; synthetic authorities, no release."""

import json
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cli_contracts import ProposalHold
from app.cli_worker import CliWorker
from app.calculation_assessment import CalculationAssessmentService
from app.execution_attestation import ExecutionAttestationStore
from app.execution_verifier import ExecutionVerifier
from app.farm_authored_review import (FarmAuthoredReviewContract,
    FarmAuthoredReviewService, FarmAuthoredReviewHold, INPUT_VERSION)
from app.farm_authored_review_completion import (AuthoredReviewCompletionVerifier,
    AuthoredReviewCompletionHold)
from app.jobs import canonical_input_bytes
from app.market_result_store import MarketResultStore
from app.owned_cli_contracts import OwnedCliContractRouter
from app.owned_collection_review import OwnedCollectionReviewService
from app.owned_fixture_collection import CollectionService
from test_farm_authoring_storage import authoring, request
from test_farm_replay_scenario import farm_setup
from test_cli_worker import _fake_cli
from test_execution_attestation import _signed
from test_jobs import synthetic_evidence_policy
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
    assert review.verify_input(stored,json.loads(stored['input_bytes']))==value
    with pytest.raises(PermissionError):
        review.submit('tenant-1','farm-1','r1',registration.scenario_sha256,'later')
    principal['scopes'].add('collection_review_create')
    monkeypatch.setattr(author.replay.candidates._source._source,
        'get_input_rights',lambda *_:None)
    with pytest.raises(FarmAuthoredReviewHold):
        review.verify_input(stored,json.loads(stored['input_bytes']))


def self_authored_evidence_policy(tenant,source,intended_use,kind,payload,digest):
    result=synthetic_evidence_policy(tenant,source,intended_use,kind,payload,digest)
    return {**result,'source_id':'synthetic_self_authored',
        'rights_proof_id':'synthetic_self_authored','classification':'private',
        'read_scope':'auditor','retain_raw':True}


self_authored_evidence_policy.policy_version='synthetic-storage-v1'


@pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,
    'break_even_calculation':True}],indirect=True)
def test_authored_review_completion_requires_signed_attestation(authoring,login_scope,monkeypatch,tmp_path):
    author,body,principal=authoring
    principal['scopes'].add('collection_review_create')
    registration=author.submit('tenant-1',request(body))
    review=FarmAuthoredReviewService(author)
    value=review.prepare('tenant-1','farm-1','r1',registration.scenario_sha256)
    first=review.submit('tenant-1','farm-1','r1',registration.scenario_sha256,'farm-review-completion')
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
    jobs.decision_validator=router
    jobs.evidence_policy=self_authored_evidence_policy
    program=_fake_cli(tmp_path)
    program.write_text(program.read_text().replace(
        "['candidate-a'] if context['server_allows_proceed']",
        "[context['input']['candidate_ids'][0]] if context['server_allows_proceed']"))
    home=tmp_path/'authored-cli-home';home.mkdir(mode=0o700)
    worker=CliWorker(jobs,router,cli_path=program,codex_home=home,
        child_env={'CODEX_API_KEY':'synthetic-test-key'},timeout_seconds=10,
        lease_seconds=300,synthetic_smoke=True)
    seen={}
    record_launch=jobs.record_cli_launch
    def captured_launch(*args,**kwargs):
        seen['argv']=list(kwargs['argv'])
        return record_launch(*args,**kwargs)
    monkeypatch.setattr(jobs,'record_cli_launch',captured_launch)
    lease=jobs.claim(300,allowed_stages=('collection_review',),
        tenant_id='tenant-1',job_id=str(first['job_id']))
    worked=worker._run_claimed(lease)
    assert worked.state=='succeeded' and worked.capture_id and worked.decision_id, (
        worked.state,worked.reason_code)
    with jobs.connect() as conn:
        rows={name:conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(jobs._table(name)),('tenant-1',first['job_id'])).fetchone()
            for name in ('jobs','attempt_invocations','attempt_cli_launches',
                         'attempt_cli_captures')}
    record,attestation_raw,signature,untrusted,_,_=_signed(
        jobs,worker,worked,rows,seen['argv'])
    base,_,_=login_scope
    attestations=ExecutionAttestationStore(base,untrusted.public_keys)
    execution=ExecutionVerifier(attestations,
        executable_sha256=record.executable_sha256,
        environment_sha256=record.environment_sha256)
    completed=AuthoredReviewCompletionVerifier(review,execution)
    with pytest.raises(AuthoredReviewCompletionHold):
        completed.verify('tenant-1',first['job_id'],registration.scenario_sha256)
    attestations.put(attestation_raw,signature)
    proof=completed.verify('tenant-1',first['job_id'],registration.scenario_sha256)
    assert proof.review_input_sha256==first['input_sha256']
    assert (proof.scenario_id,proof.scenario_revision)==('farm-1','r1')
    assert proof.trace_sha256==tuple(value['trace_sha256']) and proof.proof_sha256
    with pytest.raises(AuthoredReviewCompletionHold):
        completed.verify('tenant-1',first['job_id'],'0'*64)
