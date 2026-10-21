"""Lean production-service assembly for synthetic morphology farm tests only."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from hashlib import sha256
import importlib
import inspect
import json
import os
from pathlib import Path
import sys

from psycopg import sql

from app import crop_morphology_farm_binding as model
from app.api_economic_scenario import EconomicScenarioRequest,EconomicScenarioService
from app.api_market_source import _MarketSources
from app.economic_contracts import EconomicScenario,OwnedEconomicRecord,OwnedSettlementRecord,PriorBatchCostRecord
from app.farm_authoring_storage import FarmAuthoringService,FarmAuthoringRequest,WRITE_SCOPES as FARM_WRITE_SCOPES
from app.farm_replay_scenario import FarmReplayScenarioService,WRITE_SCOPES as REPLAY_WRITE_SCOPES
from app.job_store import JobStore
from app.market_candidate_store import MarketCandidateStore
from app.market_hold_store import MarketHoldStore
from app.market_scenario import MarketScenarioService,MarketScenarioRequest,JointShock,InputRights,Applicability,_json
from app.market_source_store import MarketSourceStore
from app.orchestration import LocationRequest
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.owned_research import OwnedResearchService,ADMISSION_SCOPES as OWNED_SCOPES
from app.research_registry import ResearchRegistry
from app.thermal_run_store import ThermalRunStore, _canonical
from app.thermal_scenario_store import ThermalScenarioStore
from test_farm_inputs import example
from test_market_hold_store import HOLD_KEY,context_verifier
import test_market_signed_hold_integration as seed
from test_thermal_publisher import input_raws
import test_crop_morphology_input_evidence as inputs


def create_farm(login_scope,monkeypatch,decision_at, *, principal_provider_factory=None):
    import test_economics, test_economics_settlement, test_market_scenario
    for module in (test_economics,test_economics_settlement,test_market_scenario,seed):
        monkeypatch.setattr(module, "DECISION", decision_at)
    # Build registered inputs through production services; an HTTP app is unnecessary here.
    root=Path(__file__).resolve().parents[2]
    base,policy,dsns=login_scope;identity=(policy,'authority')
    monkeypatch.setattr(seed,'SNAPSHOT_RAWS',input_raws())
    _,values,req,principal,scope=seed.signed_market_assembly(dsns['authority'],policy.schema,runtime_identity=identity)
    req=MarketScenarioRequest.model_validate_json(_json(req)).model_dump(mode='json')
    principal['scopes'].update({'metadata','market_source_read','market_source_write','decision_context_read',
        'location_create','thermal_scenario_write'}|set(FARM_WRITE_SCOPES)|set(REPLAY_WRITE_SCOPES)|set(OWNED_SCOPES))
    provider=(lambda:principal) if principal_provider_factory is None else principal_provider_factory(principal)
    kw={'runtime_identity':identity,'principal_provider':provider}
    jobs=JobStore(dsns['authority'],policy.schema,base.artifact_root,audit_runtime_grants=True,**kw)
    sources=MarketSourceStore(dsns['authority'],policy.schema,**kw)
    groups={'economic_scenario':(values.scenarios,EconomicScenario),'economic_input':(values.records,OwnedEconomicRecord),
        'joint_shock':(values.shocks,JointShock),'input_rights':(values.rights,InputRights),
        'settlement_applicability':(values.bindings,Applicability),'settlement_evidence':(values.settlements,OwnedSettlementRecord),
        'prior_batch_cost':(values.prior_costs,PriorBatchCostRecord)}
    for kind,(items,cls) in groups.items():
        for value in items.values():
            data=cls.model_validate(value).model_dump(mode='json');raw=_canonical(data)
            row=base.submit('tenant-1','simulation',data,'source-'+sha256(raw).hexdigest())
            sources.adopt_job('tenant-1',kind,str(row['job_id']))
    req['shock']['sha256']=sources.get_joint_shock_pin('joint-1','r1')['sha256']
    runs=ThermalRunStore(dsns['authority'],policy.schema,gate_key=b'synthetic-gate-key-32-bytes-long!',
        release_verifier=lambda *_:None,context_verifier=context_verifier,**kw)
    holds=MarketHoldStore(dsns['authority'],policy.schema,context_store=runs,
        scope_resolver=lambda *_:dict(scope),signing_key=HOLD_KEY,**kw)
    candidates=MarketCandidateStore(dsns['authority'],policy.schema,_MarketSources(sources,holds,principal_provider=provider),**kw)
    economic_service=EconomicScenarioService(jobs,candidates)
    registered=economic_service.submit('tenant-1',EconomicScenarioRequest.model_validate_json(
        _canonical({'request':req,'idempotency_key':'farm-economics'})))
    weather=json.loads(input_raws()[1]);location={'latitude':35.0,'longitude':127.0,
        'period_start_utc':weather['start_utc'],'period_end_utc':weather['end_utc'],
        'goal_id':'historical-thermal-replay','idempotency_key':'authored-farm-research'}
    registration={'tenant_id':'tenant-1','point':{'latitude':35.0,'longitude':127.0},
        **{k:location[k] for k in ('period_start_utc','period_end_utc','goal_id')},
        'provider_ids':[OwnedFixtureRegistry(root).provider_id]}
    registry_raw=_canonical({'registry_version':'research-registry-v1','registrations':[registration]})
    registry=ResearchRegistry(registry_raw,sha256(registry_raw).hexdigest())
    owned=OwnedResearchService(jobs,runs,registry,OwnedFixtureRegistry(root),{next(iter(registry._scopes)):'context-1'})
    _,_,research=owned.submit('tenant-1',LocationRequest.model_validate(location))
    hold=holds.get_market_hold_report(req['market_context']['hold_report_id']);thermal=ThermalScenarioStore(runs,holds)
    selected=thermal.put('tenant-1',{'schema_version':'thermal-scenario-v1','scenario_id':'thermal-one','scenario_revision':'r1',
        'tenant_id':'tenant-1','snapshot_id':hold['snapshot_id'],'decision_context_id':hold['decision_context_id'],
        'market_context':req['market_context'],'zone_id':'fixture-zone','goal_id':'historical-thermal-replay',
        'model_version':'thermal-v1','parameter_set_version':'synthetic-thermal-parameters-v1','origin':'user','evidence_level':'assumed'})
    replay=FarmReplayScenarioService(jobs,thermal,candidates,registry,owned_research=owned)
    _,economic,candidate=MarketScenarioService(candidates).validate_pinned(registered.scenario_id,registered.scenario_revision,'tenant-1')
    document=example();document.update(research_job_id=str(research['job_id']),market_context=req['market_context'],
        snapshot_id=hold['snapshot_id'],decision_context_id='context-1',decision_at=economic.decision_at.isoformat().replace('+00:00','Z'),
        period_start=economic.period_start.isoformat(),period_end=economic.period_end.isoformat(),
        economic={'scenario_id':economic.scenario_id,'revision':economic.scenario_revision,
            'sha256':candidate['economic_scenario_sha256'],'candidate_id':candidate['candidate_id']})
    crop=document['crops'][0];crop['batch_id']=economic.harvests[0].batch_id
    crop['grades']=sorted({r.grade for r in economic.packouts}|{r.grade for r in economic.sales})
    crop['channels']=sorted({r.channel for r in economic.packouts}|{r.channel for r in economic.sales})
    rights={'schema_version':'farm-assumption-rights-v1','scenario_id':document['scenario_id'],
        'scenario_revision':document['scenario_revision'],'declaration_id':'self-authored-farm-1','revision':'r1',
        'origin':'user','evidence_level':'assumed','available_at':document['decision_at'],
        'scope_start':document['period_start'],'scope_end':document['period_end'],'redistribute':False,
        **{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}
    return FarmAuthoringService(replay),{'schema_version':'farm-authoring-request-v1','farm':document,'rights':rights},principal


class SyntheticMorphologyRights:
    policy_version = 'owned-morphology-input-rights-test-v1'
    allowed = True

    def __init__(self):
        self.calls = []

    def __call__(self, tenant, declaration, source, use):
        self.calls.append(use)
        return self.allowed is True and tenant == 'tenant-1' and declaration['schema_version'] == model.RIGHTS_VERSION \
            and declaration['input_source_sha256'] == source and use in ('research_calculation', 'research_display')


def source_packet():
    directory = os.environ.get('OSSF_MORPHOLOGY_SOURCE_PROOF_DIRECTORY')
    if directory:
        path = Path(directory)
        raw, source, proof = ((path/name).read_bytes() for name in ('program.private.json', 'source.private.json', 'evidence.private.json'))
        review = json.loads((path/'review.private.json').read_bytes())
        key = (path/'key.private').read_bytes()
        payload = json.loads(proof)['payload']
        authority = model.evidence.MorphologyInputEvidenceAuthority(integrity_key=key, issuer_id=payload['issuer_id'],
            key_id=payload['key_id'], review_resolver=lambda _: deepcopy(review))
        decision = datetime.fromisoformat(payload['decision_at'].replace('Z', '+00:00'))
    else:
        raw, source = inputs.prepared(); review = inputs.review(source); decision = inputs.DECISION
        authority = inputs.authority(model.evidence, source, lambda _: deepcopy(review))
        proof = authority.issue(**inputs.arguments(raw, source))
    return {'packet': dict(program_raw=raw, source_raw=source, evidence_raw=proof),
        'authority': authority, 'review': review, 'decision': decision}


def study(farm_body, registered_sha, packet, decision):
    raw, source, proof = (packet[k] for k in ('program_raw', 'source_raw', 'evidence_raw'))
    return {'study_id': 'synthetic-morphology-native-study', 'revision': 'r1',
        'farm': {'scenario_id': farm_body['farm']['scenario_id'], 'scenario_revision': farm_body['farm']['scenario_revision'],
            'registration_sha256': registered_sha, 'crop_id': 'crop-1'},
        'input': {'schema_version': model.evidence.SOURCE_VERSION, 'program_id': json.loads(raw)['program_id'],
            'program_sha256': sha256(raw).hexdigest(), 'source_sha256': sha256(source).hexdigest(), 'evidence_sha256': sha256(proof).hexdigest()},
        'rights': {'schema_version': model.RIGHTS_VERSION, 'declaration_id': 'owned-morphology-source', 'revision': 'r1',
            'input_source_sha256': sha256(source).hexdigest(), 'available_at': decision.isoformat().replace('+00:00', 'Z'),
            'redistribute': False, **{k: True for k in ('ownership_asserted', 'access', 'store', 'transform', 'use', 'display')}}}


def counts(service):
    with service.jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(service.jobs._table(table))).fetchone()['n']
            for table in ('jobs', 'job_events', 'crop_cycle_research_results', 'thermal_g1_runs'))


def forbid_growth(patch):
    calls = {}
    modules = [*inputs.GROWTH, 'crop_rational_morphology_artifact_producer']
    for name in modules:
        module = importlib.import_module('app.'+name)
        for key, fn in vars(module).copy().items():
            if inspect.isfunction(fn) and fn.__module__ == module.__name__ and not key.startswith('_'):
                label = name+'.'+key; calls[label] = 0
                def fail(*args, _label=label, **kwargs):
                    calls[_label] += 1
                    raise AssertionError('binding invoked growth '+_label)
                patch.setattr(module, key, fail)
    from app.cli_worker import CliWorker
    calls['CLI'] = 0
    def cli(*a, **kw):
        calls['CLI'] += 1
        raise AssertionError('binding invoked CLI')
    patch.setattr(CliWorker, 'run_once', cli)
    return calls


def save(name, value):
    directory = os.environ.get('OSSF_MORPHOLOGY_FARM_EVIDENCE')
    if directory:
        path = Path(directory)/name
        with path.open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2); f.flush(); os.fsync(f.fileno())


def private_file(directory, name, raw):
    path = directory/name
    with path.open('xb') as f:
        os.fchmod(f.fileno(), 0o400); f.write(raw); f.flush(); os.fsync(f.fileno())
    return str(path)


def fresh_config(service, principal, body, packet, review, expected, directory):
    directory.mkdir(mode=0o700)
    replay = service.farms.replay; registry = []
    for s in replay.registry._scopes.values():
        registry.append({'tenant_id': s.tenant_id, 'point': {'latitude': s.point[0], 'longitude': s.point[1]},
            'period_start_utc': s.period_start_utc, 'period_end_utc': s.period_end_utc, 'goal_id': s.goal_id, 'provider_ids': list(s.provider_ids)})
    registry_raw = model.documents._canonical({'registry_version': 'research-registry-v1', 'registrations': registry})
    assert sha256(registry_raw).hexdigest() == replay.registry.sha256
    paths = {k: private_file(directory, k+'.private', v) for k, v in packet.items()}
    value = {'policy': asdict(service.jobs.runtime_identity[0]), 'dsn': service.jobs._dsn,
        'artifacts': str(service.jobs.artifact_root), 'principal': {**principal, 'scopes': sorted(principal['scopes'])},
        'scope': replay.thermal.holds._scope_resolver(None, None, None), 'registry_raw': registry_raw.decode(),
        'registry_sha256': replay.registry.sha256, 'root': str(Path(__file__).resolve().parents[2]), 'review': review,
        'body': body, 'packet_files': paths, 'binding': private_file(directory, 'binding.private', expected),
        'input_key_file': private_file(directory, 'input-key.private', service.input_authority.integrity_key),
        'issuer_id': service.input_authority.issuer_id, 'key_id': service.input_authority.key_id}
    return private_file(directory, 'configuration.private.json', model.documents._canonical(value))


