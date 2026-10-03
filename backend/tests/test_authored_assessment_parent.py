"""Pure binding counterexamples; synthetic records do not prove stored custody."""

from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api_authored_thermal import VerifiedAuthoredCompletion
from app.authored_calculation_assessment import authored_assessment_parent, AUTHORED_FIELDS
from app.economic_calculation_worker import ECONOMIC_INPUT
from app.farm_authoring_storage import FarmAuthoringService
from app.jobs import canonical_input_bytes
from test_authored_economic_input import body


def records():
    value = ECONOMIC_INPUT.validate_python(body())
    binding = {'decision_context_id': 'context-one', 'context_sha256': 'd' * 64}
    numeric = b'{}'
    report = {'scenario_id': value.authored_scenario_id,
        'scenario_revision': value.authored_scenario_revision,
        'registration_sha256': value.registration_sha256,
        'simulation_job_id': value.thermal_job_id, 'decision_context_id': 'context-one',
        'context_sha256': 'd' * 64, 'release_sha256': 'e' * 64}
    trace = {'base_snapshot_id': 'snapshot-one', 'decision_context_id': 'context-one',
        'context_sha256': 'd' * 64, 'numeric_input_sha256': sha256(numeric).hexdigest(),
        'binding_sha256': sha256(canonical_input_bytes(binding)).hexdigest(),
        'release_sha256': 'e' * 64, 'decision_time_kind': 'hypothetical'}
    thermal = VerifiedAuthoredCompletion({}, {'receipt_version': 'synthetic'},
        {'report': report, 'report_raw': canonical_input_bytes(report),
         'trace_raws': [canonical_input_bytes(trace), canonical_input_bytes(trace)]},
        {'run_id': 'authored-run-one'}, 'f' * 64)
    receipt = {key: getattr(value, key) for key in (
        'authored_scenario_id', 'authored_scenario_revision', 'registration_sha256', 'thermal_job_id')}
    receipt.update(authored_bindings_sha256=trace['binding_sha256'],
        numeric_input_sha256=trace['numeric_input_sha256'], release_sha256='e' * 64,
        thermal_input_sha256=thermal.input_sha256,
        thermal_receipt_sha256=sha256(canonical_input_bytes(thermal.receipt)).hexdigest(),
        thermal_report_sha256=sha256(thermal.stored['report_raw']).hexdigest(),
        thermal_run_id=thermal.summary['run_id'])
    registered = {'farm': SimpleNamespace(snapshot_id='snapshot-one', decision_context_id='context-one'),
        'binding': binding, 'numeric_input_bytes': numeric}
    author = object.__new__(FarmAuthoringService)
    author.read_registration = lambda *_: registered
    economic = SimpleNamespace(value=value, receipt=receipt,
        authored_completion=thermal, thermal_completion=None)
    return author, value.thermal_job_id, economic, registered


def test_authored_context_and_extra_fields_come_from_verified_parent_and_registration():
    author, job_id, economic, _ = records()
    report, pins = authored_assessment_parent(author, 'tenant-one', job_id, economic)
    assert report['snapshot_id'] == 'snapshot-one' and report['decision_time_kind'] == 'hypothetical'
    assert set(pins) == set(AUTHORED_FIELDS)
    assert pins == {key: economic.receipt[key] for key in AUTHORED_FIELDS}


@pytest.mark.parametrize('mutation', [
    'other_job', 'receipt_report', 'receipt_input', 'receipt_release', 'binding',
    'snapshot', 'trace_kind', 'trace_numeric', 'registration_context', 'mixed_completion',
])
def test_authored_parent_rejects_mixed_or_altered_server_pins(mutation):
    author, job_id, economic, registered = records()
    if mutation == 'other_job':
        job_id = '22222222-2222-4222-8222-222222222222'
    elif mutation.startswith('receipt_'):
        key = {'receipt_report': 'thermal_report_sha256', 'receipt_input': 'thermal_input_sha256',
            'receipt_release': 'release_sha256'}[mutation]
        economic.receipt[key] = '0' * 64
    elif mutation == 'binding':
        registered['binding']['context_sha256'] = '0' * 64
    elif mutation == 'registration_context':
        registered['farm'].decision_context_id = 'other-context'
    elif mutation == 'mixed_completion':
        economic.thermal_completion = object()
    else:
        traces = list(economic.authored_completion.stored['trace_raws'])
        trace = json.loads(traces[1])
        key, changed = {'snapshot': ('base_snapshot_id', 'other-snapshot'),
            'trace_kind': ('decision_time_kind', 'actual'),
            'trace_numeric': ('numeric_input_sha256', '0' * 64)}[mutation]
        trace[key] = changed
        traces[1] = canonical_input_bytes(trace)
        economic.authored_completion.stored['trace_raws'] = traces
    with pytest.raises(ValueError):
        authored_assessment_parent(author, 'tenant-one', job_id, economic)


def test_current_registration_denial_remains_permission_failure():
    author, job_id, economic, _ = records()
    def denied(*_):
        raise PermissionError('synthetic current read denied')
    author.read_registration = denied
    with pytest.raises(PermissionError):
        authored_assessment_parent(author, 'tenant-one', job_id, economic)
