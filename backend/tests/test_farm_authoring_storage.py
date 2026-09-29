"""Actual SCRAM custody for authored inputs; no published farm claim."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.farm_authoring_storage import (FarmAuthoringService, FarmAuthoringRequest,
    FarmAuthoringHold, READ_SCOPES, WRITE_SCOPES)
from app.jobs import canonical_input_bytes
from app.market_scenario import MarketScenarioService
from app.orchestration import LocationRequest
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.owned_research import OwnedResearchService, ADMISSION_SCOPES as OWNED_SCOPES
from test_farm_inputs import example
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope


ROOT=Path(__file__).resolve().parents[2]
pytestmark=pytest.mark.parametrize('login_scope', [{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,
    'break_even_calculation':True}],indirect=True)


@pytest.fixture
def authoring(farm_setup):
    selection,old_body,principal=farm_setup
    principal['scopes'].update(set(WRITE_SCOPES)|set(OWNED_SCOPES))
    owned=OwnedResearchService(selection.jobs,selection.thermal.runs,selection.registry,
        OwnedFixtureRegistry(ROOT),{next(iter(selection.registry._scopes)):'context-1'})
    with selection.jobs.connect() as conn:
        old_root=selection.jobs._locked_job(conn,'tenant-1',old_body['research_job_id'])
    original=json.loads(old_root['input_bytes'])
    location=LocationRequest.model_validate({**original['point'],
        **{key:original[key] for key in ('period_start_utc','period_end_utc','goal_id')},
        'idempotency_key':'authored-farm-research'})
    _,_,root=owned.submit('tenant-1',location)
    selection.owned_research=owned
    _,economic,candidate=MarketScenarioService(selection.candidates).validate_pinned(
        old_body['economic']['scenario_id'],old_body['economic']['revision'],'tenant-1')
    document=example()
    document.update(research_job_id=str(root['job_id']),
        market_context=old_body['market_context'],
        snapshot_id=selection.thermal.get('tenant-1','thermal-one','r1')['scenario'].snapshot_id,
        decision_context_id='context-1',decision_at=economic.decision_at.isoformat().replace('+00:00','Z'),
        period_start=economic.period_start.isoformat(),period_end=economic.period_end.isoformat(),
        economic=dict(scenario_id=economic.scenario_id,revision=economic.scenario_revision,
            sha256=candidate['economic_scenario_sha256'],candidate_id=candidate['candidate_id']))
    crop=document['crops'][0]
    crop['batch_id']=economic.harvests[0].batch_id
    crop['grades']=sorted({row.grade for row in economic.packouts}|{row.grade for row in economic.sales})
    crop['channels']=sorted({row.channel for row in economic.packouts}|{row.channel for row in economic.sales})
    rights=dict(schema_version='farm-assumption-rights-v1',
        scenario_id=document['scenario_id'],scenario_revision=document['scenario_revision'],
        declaration_id='self-authored-farm-1',revision='r1',origin='user',
        evidence_level='assumed',ownership_asserted=True,access=True,store=True,
        transform=True,use=True,display=True,redistribute=False,
        available_at=document['decision_at'],scope_start=document['period_start'],
        scope_end=document['period_end'])
    return FarmAuthoringService(selection),{
        'schema_version':'farm-authoring-request-v1','farm':document,'rights':rights},principal


def request(body):
    return FarmAuthoringRequest.model_validate_json(canonical_input_bytes(body))


def counts(service):
    with service.replay.jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(service.replay.jobs._table(name))).fetchone()['n']
            for name in ('jobs','job_events'))


def test_owned_registration_is_immutable_replayable_and_numerically_bound(authoring):
    service,body,principal=authoring
    before=counts(service)
    first=service.submit('tenant-1',request(body))
    assert first.registration_status=='registered_unpublished_inputs'
    assert first.intent_job.state=='queued' and first.intent_job.attempt_count==0
    assert counts(service)==(before[0]+1,before[1]+1)
    assert service.submit('tenant-1',request(body))==first
    fresh=FarmAuthoringService(service.replay)
    assert fresh.get('tenant-1','farm-1','r1')==first
    registered=fresh.read_registration('tenant-1','farm-1','r1',first.scenario_sha256)
    assert registered['farm'].scenario_id=='farm-1'
    assert registered['user_rights_declaration'].ownership_asserted is True
    assert sha256(registered['numeric_input_bytes']).hexdigest()==first.numeric_input_sha256
    assert registered['binding']['point']=={'latitude':35.0,'longitude':127.0}
    assert registered['binding']['spatial_support']=='pending_research'
    assert registered['compiled']['status']=='unpublished_candidate'
    assert registered['compiled']['missing_evidence']==[
        'authored_input_review','authored_snapshot_release']
    assert service.replay.jobs.get_publication('tenant-1',first.intent_job.job_id) is None
    assert service.get('tenant-other','farm-1','r1') is None
    assert not any(name in first.model_dump(mode='json') for name in
        ('point','species','money','farm','rights','numerical_input','source_approval'))
    changed=deepcopy(body)
    changed['farm']['facility']['floor_area']['value']='101'
    from app.job_store import JobIntentConflict
    with pytest.raises(JobIntentConflict):
        service.submit('tenant-1',request(changed))
    assert counts(service)==(before[0]+1,before[1]+1)
    changed=deepcopy(body)
    changed['farm']['scenario_revision']='r2'
    changed['rights']['scenario_revision']='r2'
    second=service.submit('tenant-1',request(changed))
    assert second.farm_sha256 != first.farm_sha256
    assert second.numeric_input_sha256 != first.numeric_input_sha256


def test_bad_references_and_rights_cannot_create_intents(authoring):
    service,body,_=authoring
    before=counts(service)
    changes=[('farm','snapshot_id','thermal-snapshot-v1:'+'b'*64),
             ('farm','decision_context_id','other-context'),
             ('farm','research_job_id','00000000-0000-4000-8000-000000000004'),
             ('farm','economic','candidate_id','b'*64),
             ('rights','store',False),('rights','ownership_asserted',False),
             ('rights','scope_end','2026-10-01'),
             ('rights','available_at','2026-10-01T00:00:00Z')]
    for path in changes:
        changed=deepcopy(body)
        node=changed
        for key in path[:-2]: node=node[key]
        node[path[-2]]=path[-1]
        with pytest.raises((ValueError,PermissionError)):
            service.submit('tenant-1',request(changed))
    with service.replay.jobs.connect() as conn:
        other=conn.execute(sql.SQL("SELECT job_id FROM {} WHERE tenant_id=%s AND stage='research' AND job_id!=%s")
            .format(service.replay.jobs._table('jobs')),
            ('tenant-1',body['farm']['research_job_id'])).fetchone()
    assert other is not None
    changed=deepcopy(body)
    changed['farm']['research_job_id']=str(other['job_id'])
    with pytest.raises(FarmAuthoringHold):
        service.submit('tenant-1',request(changed))
    assert counts(service)==before


def test_revocation_and_late_scope_loss_recheck_before_commit(authoring,monkeypatch):
    service,body,principal=authoring
    before=counts(service)
    original=service._prepare
    calls=0
    def revoke(*args,**kwargs):
        nonlocal calls
        result=original(*args,**kwargs)
        calls+=1
        if calls==1: principal['scopes'].remove('farm_scenario_write')
        return result
    monkeypatch.setattr(service,'_prepare',revoke)
    with pytest.raises(PermissionError):
        service.submit('tenant-1',request(body))
    assert counts(service)==before
    principal['scopes'].add('farm_scenario_write')
    monkeypatch.setattr(service,'_prepare',original)
    first=service.submit('tenant-1',request(body))
    original_find=service._find
    def corrupted(*args):
        row=original_find(*args)
        return {**row,'input_bytes':row['input_bytes']+b' '}
    monkeypatch.setattr(service,'_find',corrupted)
    with pytest.raises(FarmAuthoringHold):
        service.read_registration('tenant-1','farm-1','r1',first.scenario_sha256)
    monkeypatch.setattr(service,'_find',original_find)
    original_authority=service.replay.owned_research
    service.replay.owned_research=None
    with pytest.raises(FarmAuthoringHold):
        service.get('tenant-1','farm-1','r1')
    service.replay.owned_research=original_authority
    monkeypatch.setattr(service.replay.candidates._source._source,
        'get_input_rights',lambda *_:None)
    with pytest.raises(FarmAuthoringHold):
        service.get('tenant-1','farm-1','r1')
    assert service.replay.jobs.get_publication('tenant-1',first.intent_job.job_id) is None
