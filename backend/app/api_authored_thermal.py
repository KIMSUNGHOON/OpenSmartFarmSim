"""Bounded display projection of a currently verified authored thermal Run."""

from datetime import timedelta
from hashlib import sha256
import json
import re
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from .api_contracts import ThermalRunSeries, ThermalSeriesPoint
from .api_thermal import _number, _utc
from .authored_thermal_candidate import _raw
from .farm_authoring_storage import READ_SCOPES as FARM_READ_SCOPES
from .jobs import canonical_input_bytes


AUTHORED_RUN_ID_PATTERN = r'^authored-thermal-run-v1:[0-9a-f]{64}$'
_RUN_ID = re.compile(AUTHORED_RUN_ID_PATTERN)
_DIGEST = re.compile(r'[0-9a-f]{64}\Z')
_MINUTE = timedelta(minutes=1)
_HOUR = timedelta(hours=1)
AUTHORED_READ_SCOPES = tuple(dict.fromkeys((
    'metadata', 'artifact', 'authored_run_read', 'authored_release_read',
    *FARM_READ_SCOPES)))


class AuthoredRunCatalogCursor(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    recorded_at: AwareDatetime
    run_id: str = Field(pattern=AUTHORED_RUN_ID_PATTERN)


class AuthoredRunCatalogItem(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    run_id: str = Field(pattern=AUTHORED_RUN_ID_PATTERN)
    simulation_job_id: UUID
    recorded_at: AwareDatetime
    verification: Literal['requires_current_read']


class AuthoredRunCatalogPage(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    items: list[AuthoredRunCatalogItem]
    next_cursor: AuthoredRunCatalogCursor | None


def _need(value):
    if not value:
        raise ValueError('authored thermal display unavailable')


def project_authored_run(stored):
    """Select numeric points after AuthoredRunStore has checked current authority."""
    try:
        _need(type(stored) is dict and type(stored.get('run_id')) is str and
              _RUN_ID.fullmatch(stored['run_id']) and
              type(stored.get('report_raw')) is bytes and
              type(stored.get('report')) is dict and
              type(stored.get('trace_raws')) in (tuple, list) and
              len(stored['trace_raws']) == 2)
        report = stored['report']
        _need(canonical_input_bytes(report) == stored['report_raw'] and
              report['gate_version'] == 'authored-thermal-run-gate-v1' and
              report['status'] == 'accepted' and
              report['claim_scope'] == 'synthetic_thermal_replay_only' and
              report['claim_mode'] == 'ex_post_replay' and
              report['run_id'] == stored['run_id'] and
              type(report['trace_sha256']) is list and
              len(report['trace_sha256']) == 2 and
              all(type(item) is str and _DIGEST.fullmatch(item)
                  for item in report['trace_sha256']))
        points = []
        previous_end = None
        engine = units = model = None
        for index, raw in enumerate(stored['trace_raws']):
            _need(type(raw) is bytes and len(raw) <= 1_048_576 and
                  sha256(raw).hexdigest() == report['trace_sha256'][index])
            trace = json.loads(raw)
            _need(_raw(trace) == raw and
                  trace['trace_version'] == 'authored-thermal-run-trace-v1' and
                  trace['status'] == 'accepted' and
                  trace['claim_scope'] == report['claim_scope'] and
                  trace['claim_mode'] == report['claim_mode'] and
                  trace['run_id'] == stored['run_id'] and
                  trace['trace_sequence_index'] == index and
                  trace['trace_id'] == f"{stored['run_id']}:hour-{index}" and
                  all(trace[key] == report[key] for key in (
                      'tenant_id', 'scenario_id', 'scenario_revision',
                      'registration_sha256', 'review_job_id',
                      'decision_context_id', 'context_sha256',
                      'decision_at_utc', 'review_at_utc', 'release_sha256')) and
                  trace['model_version'] == 'thermal-v1' and
                  trace['engine_version'] == 'thermal-euler-v1' and
                  trace['unit_registry_version'] == 'thermal-si-nws-v1')
            if index == 0:
                model, engine, units = (trace['model_version'],
                    trace['engine_version'], trace['unit_registry_version'])
            interval = trace['interval']
            start, end = _utc(interval['start_utc']), _utc(interval['end_utc'])
            _need(end - start == _HOUR and
                  (previous_end is None or start == previous_end) and
                  type(trace['steps']) is list and len(trace['steps']) == 60)
            if index == 0:
                first_start = start
            previous_end = end
            cursor = start
            for step in trace['steps']:
                at_start, at_end = _utc(step['start_utc']), _utc(step['end_utc'])
                _need(at_start == cursor and at_end - at_start == _MINUTE)
                cursor = at_end
                points.append(ThermalSeriesPoint(
                    at_utc=at_end,
                    temperature_k=_number(step['state_end']['temperature'], 'K', minimum=0),
                    humidity_ratio_kg_v_per_kg_da=_number(
                        step['state_end']['humidity_ratio'], 'kg_v/kg_da', minimum=0),
                    relative_humidity_fraction=_number(
                        step['relative_humidity_end'], '1', minimum=0, maximum=1),
                    heat_demand_w_th=_number(step['heat_demand'], 'W_th', minimum=0),
                    heat_delivered_w_th=_number(step['heat_delivered'], 'W_th', minimum=0),
                    delivered_heat_energy_kwh_th=_number(
                        step['delivered_heat_energy'], 'kWh_th', minimum=0)))
            _need(cursor == end)
        _need(len(points) == 120)
        summary = {
            'run_id': stored['run_id'], 'status': 'accepted', 'synthetic': True,
            'claim_scope': 'synthetic_thermal_replay_only',
            'temporal_provenance': 'ex_post_replay',
            'scenario_id': report['scenario_id'],
            'scenario_revision': report['scenario_revision'],
            'registration_sha256': report['registration_sha256'],
            'release_sha256': report['release_sha256'],
            'decision_at_utc': _utc(report['decision_at_utc']),
            'review_at_utc': _utc(report['review_at_utc']),
            'start_utc': first_start, 'end_utc': previous_end,
            'model_version': model, 'engine_version': engine,
            'unit_registry_version': units,
            'trace_sha256': report['trace_sha256'], 'point_count': len(points)}
        return summary, ThermalRunSeries(run_id=stored['run_id'],
            temporal_provenance='ex_post_replay', points=points)
    except Exception:
        raise ValueError('authored thermal display unavailable') from None


def read_authored_job_run(jobs, runs, tenant, job_id):
    """Discover only the authored Run published by this exact completed job."""
    job = jobs.get_job(tenant, job_id)
    if job is None or job['stage'] != 'simulation' or job['state'] != 'succeeded':
        return None
    publication = jobs.get_publication(tenant, job_id)
    if publication is None:
        raise ValueError('authored job publication unavailable')
    manifest = publication['manifest']
    run_id = manifest.get('run_id') if type(manifest) is dict else None
    if type(run_id) is not str or not _RUN_ID.fullmatch(run_id):
        return None
    stored = runs.get_run(tenant, run_id)
    if stored is None:
        raise ValueError('authored job Run unavailable')
    report = stored['report']
    expected_input = canonical_input_bytes({
        'input_version': 'authored-thermal-simulation-input-v1',
        'tenant_id': tenant,
        'review_job_id': report['review_job_id'],
        'scenario_id': report['scenario_id'],
        'scenario_revision': report['scenario_revision'],
        'registration_sha256': report['registration_sha256']})
    _need(report['simulation_job_id'] == str(job_id) and
          sha256(expected_input).hexdigest() == job['input_sha256'] and
          publication['tenant_id'] == tenant and
          publication['job_id'] == job_id and
          publication['attempt'] == job['attempt_count'] and
          publication['decision_id'] is None and
          manifest == {'schema_version': '1', 'job_id': str(job_id),
              'stage': 'simulation', 'input_sha256': job['input_sha256'],
              'attempt': job['attempt_count'],
              'artifact_sha256': publication['artifact_sha256'],
              'run_id': run_id})
    return project_authored_run(stored)[0]
