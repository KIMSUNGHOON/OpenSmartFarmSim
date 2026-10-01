"""Derive assessment context only from the verified authored parent pair."""

from hashlib import sha256
import json

from .api_authored_thermal import VerifiedAuthoredCompletion
from .farm_authoring_storage import FarmAuthoringService
from .jobs import canonical_input_bytes


AUTHORED_INPUT_VERSION = 'calculation-assessment-input-v3'
AUTHORED_FIELDS = ('authored_scenario_id', 'authored_scenario_revision',
    'registration_sha256', 'authored_bindings_sha256', 'numeric_input_sha256', 'release_sha256')


def authored_assessment_parent(authoring, tenant, run_job_id, economic):
    thermal = economic.authored_completion
    value, receipt = economic.value, economic.receipt
    if (type(authoring) is not FarmAuthoringService or
            type(thermal) is not VerifiedAuthoredCompletion or
            economic.thermal_completion is not None or
            value.input_version != 'economic-calculation-input-v3' or
            value.thermal_job_id != run_job_id or receipt['thermal_job_id'] != run_job_id or
            receipt['thermal_input_sha256'] != thermal.input_sha256 or
            receipt['thermal_receipt_sha256'] != sha256(canonical_input_bytes(thermal.receipt)).hexdigest() or
            receipt['thermal_report_sha256'] != sha256(thermal.stored['report_raw']).hexdigest() or
            receipt['thermal_run_id'] != thermal.summary['run_id']):
        raise ValueError('authored assessment parent unavailable')
    registered = authoring.read_registration(tenant, value.authored_scenario_id,
        value.authored_scenario_revision, value.registration_sha256)
    farm = registered['farm']
    report = thermal.stored['report']
    numeric_hash = sha256(registered['numeric_input_bytes']).hexdigest()
    binding_hash = sha256(canonical_input_bytes(registered['binding'])).hexdigest()
    if ((report['scenario_id'], report['scenario_revision'], report['registration_sha256']) !=
            (value.authored_scenario_id, value.authored_scenario_revision, value.registration_sha256) or
            report['simulation_job_id'] != run_job_id or
            report['decision_context_id'] != farm.decision_context_id or
            receipt['authored_bindings_sha256'] != binding_hash or
            receipt['numeric_input_sha256'] != numeric_hash or
            receipt['release_sha256'] != report['release_sha256']):
        raise ValueError('authored assessment registration differs')
    traces = [json.loads(raw) for raw in thermal.stored['trace_raws']]
    if len(traces) != 2 or any(
            trace['base_snapshot_id'] != farm.snapshot_id or
            trace['decision_context_id'] != report['decision_context_id'] or
            trace['context_sha256'] != report['context_sha256'] or
            trace['numeric_input_sha256'] != numeric_hash or
            trace['binding_sha256'] != binding_hash or
            trace['release_sha256'] != report['release_sha256'] or
            trace['decision_time_kind'] != traces[0]['decision_time_kind']
            for trace in traces):
        raise ValueError('authored assessment trace context differs')
    return ({**report, 'snapshot_id': farm.snapshot_id,
        'decision_time_kind': traces[0]['decision_time_kind']},
        {key: receipt[key] for key in AUTHORED_FIELDS})
