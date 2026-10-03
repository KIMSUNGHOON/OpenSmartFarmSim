"""Current joint selection and owned parent lineage for a thermal execution."""

from hashlib import sha256
import json

from .farm_replay_scenario import FarmReplayScenarioService, READ_SCOPES
from .jobs import canonical_input_bytes
from .owned_fixture_collection import CollectionInput
from .owned_collection_review import INPUT_VERSION as REVIEW_VERSION


class FarmThermalHold(ValueError):
    pass


def _parent(jobs,tenant,job_id,stage):
    with jobs.connect() as conn:
        row=jobs._locked_job(conn,tenant,job_id)
        if row is None or row['stage']!=stage or row['state']!='succeeded' or row['cancel_requested']:
            raise ValueError()
        raw=jobs._verified_input(row)
    return row,raw


def _publication(jobs,tenant,row,*,maximum):
    publication=jobs.get_publication(tenant,row['job_id'])
    if publication is None or not 1<=publication['artifact_size']<=maximum:
        raise ValueError()
    raw=jobs.read_artifact(tenant,row['job_id'])
    if type(raw) is not bytes or not 1<=len(raw)<=maximum:
        raise ValueError()
    manifest={'schema_version':'1','job_id':str(row['job_id']),'stage':row['stage'],
        'input_sha256':row['input_sha256'],'attempt':row['attempt_count'],'artifact_sha256':sha256(raw).hexdigest()}
    if row['stage']=='research':
        if publication['decision_id'] is None:raise ValueError()
        manifest['decision_id']=str(publication['decision_id'])
    elif publication['decision_id'] is not None:raise ValueError()
    if (publication['tenant_id']!=tenant or publication['job_id']!=row['job_id'] or
            publication['attempt']!=row['attempt_count'] or publication['artifact_size']!=len(raw) or
            publication['artifact_sha256']!=sha256(raw).hexdigest() or
            canonical_input_bytes(publication['manifest'])!=canonical_input_bytes(manifest)):
        raise ValueError()
    return raw,publication


def farm_thermal_execution_binding(service,jobs,tenant,value,report=None):
    return _farm_thermal_execution_selection(service,jobs,tenant,value,report)[0]


def _farm_thermal_execution_selection(service,jobs,tenant,value,report=None):
    if type(service) is not FarmReplayScenarioService or service.jobs is not jobs:
        raise FarmThermalHold('farm thermal binding unavailable')
    pointers=service._pointers()
    guard=lambda:service._guard(tenant,pointers,READ_SCOPES)
    try:
        guard()
        selected=service.read_selection(tenant,value.farm_scenario_id,value.farm_scenario_revision,
            value.farm_scenario_sha256)
        request,bindings=selected['request'],selected['bindings']
        if service.owned_research is None or (
                value.scenario_id,value.scenario_revision,value.scenario_sha256,value.snapshot_id)!= (
                request.thermal.scenario_id,request.thermal.revision,request.thermal.sha256,bindings['snapshot_id']):
            raise ValueError()
        research,_=_parent(jobs,tenant,request.research_job_id,'research')
        if research['input_sha256']!=bindings['research_input_sha256']:raise ValueError()
        research_raw,research_publication=_publication(jobs,tenant,research,maximum=65536)
        review,raw=_parent(jobs,tenant,value.review_job_id,'collection_review')
        submitted=json.loads(raw)
        if (submitted.get('input_version')!=REVIEW_VERSION or submitted.get('snapshot_id')!=value.snapshot_id or
                submitted.get('context_sha256')!=bindings['thermal_pins']['context_sha256'] or
                submitted.get('decision_context_id')!=bindings['decision_context_id']):
            raise ValueError()
        collected,collected_raw=_parent(jobs,tenant,submitted['collection_job_id'],'collection')
        collection=CollectionInput.model_validate_json(collected_raw)
        if (canonical_input_bytes(collection.model_dump(mode='json'))!=collected_raw or
                collection.research_job_id!=request.research_job_id or
                collection.research_attempt!=research['attempt_count'] or
                collection.research_decision_id!=str(research_publication['decision_id']) or
                collection.research_input_sha256!=research['input_sha256'] or
                collection.research_artifact_sha256!=sha256(research_raw).hexdigest() or
                submitted['collection_attempt']!=collected['attempt_count'] or
                submitted['collection_input_sha256']!=collected['input_sha256'] or
                collection.decision_context_id!=bindings['decision_context_id'] or
                sha256(_publication(jobs,tenant,collected,maximum=131072)[0]).hexdigest()!=submitted['collection_record_sha256']):
            raise ValueError()
        if report is not None and any(report[key]!=expected for key,expected in (
                ('tenant_id',tenant),
                ('snapshot_id',bindings['snapshot_id']),('review_job_id',str(review['job_id'])),
                ('context_sha256',bindings['thermal_pins']['context_sha256']),
                ('decision_context_id',bindings['decision_context_id']))):
            raise ValueError()
        binding={'farm_scenario_id':value.farm_scenario_id,'farm_scenario_revision':value.farm_scenario_revision,
            'farm_scenario_sha256':selected['scenario_sha256'],
            'farm_bindings_sha256':sha256(canonical_input_bytes(bindings)).hexdigest()}
        return binding,selected
    except Exception:
        raise FarmThermalHold('farm thermal selection or lineage unavailable') from None
    finally:
        try:guard()
        except Exception:raise FarmThermalHold('farm thermal current authority unavailable') from None
