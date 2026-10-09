"""Deterministic, unpublished trajectory for an immutable authored farm."""

from dataclasses import dataclass
from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path

from .farm_authoring_storage import FarmAuthoringService
from .farm_input_compiler import CompiledFarmInputs
from .farm_inputs import canonical_farm_inputs
from .jobs import canonical_input_bytes
from .thermal import (ENGINE_VERSION, LIMITS, UNIT_REGISTRY_VERSION, ThermalHold,
                      _indoor, _iso, _need, _state, euler_step)
from .thermal_units import quantity as q, utc


VERSION = 'authored-thermal-candidate-v1'
MAX_TRACE_BYTES = 1_048_576
CODE_FILES = ('backend/app/authored_thermal_candidate.py',
              'backend/app/farm_input_compiler.py', 'backend/app/farm_inputs.py',
              'backend/app/thermal.py', 'backend/app/thermal_units.py')


class AuthoredThermalCandidateHold(ValueError):
    """The currently registered authored input cannot yield this candidate."""


@dataclass(frozen=True)
class AuthoredThermalCandidate:
    candidate_id: str
    registration_sha256: str
    numeric_input_sha256: str
    code_sha256: str
    trace_raws: tuple[bytes, bytes]

    @property
    def trace_sha256(self):
        return tuple(sha256(raw).hexdigest() for raw in self.trace_raws)


def _raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def _code_sha256():
    root = Path(__file__).resolve().parents[2]
    return sha256(_raw({'candidate_version': VERSION,
                        'files': {name: sha256((root / name).read_bytes()).hexdigest()
                                  for name in CODE_FILES}})).hexdigest()


def _digest(value):
    _need(type(value) is str and len(value) == 64 and
          all(character in '0123456789abcdef' for character in value),
          'INPUT_HOLD: invalid authored binding digest')


def _calculate(compiled, registration_sha256, binding_sha256, code_sha256):
    """Calculate all 120 steps before returning any unpublished trace bytes."""
    if type(compiled) is not CompiledFarmInputs:
        raise AuthoredThermalCandidateHold('authored numeric input unavailable')
    for digest in (registration_sha256, binding_sha256, code_sha256):
        _digest(digest)
    try:
        value = json.loads(compiled.thermal_bytes)
        _need(value['schema_version'] == 'farm-thermal-input-v1' and
              value['status'] == 'unpublished_candidate' and
              value['farm_sha256'] == compiled.farm_sha256 and
              value['engine_version'] == ENGINE_VERSION and
              value['unit_registry_version'] == UNIT_REGISTRY_VERSION and
              value['model_version'] == 'thermal-v1' and
              value['missing_evidence'] == ['authored_input_review', 'authored_snapshot_release'],
              'INPUT_HOLD: unexpected authored numeric contract')
        _need(len(value['intervals']) == 2, 'TIMESTAMP_HOLD: exactly two forcing hours required')
        identity = {'version': VERSION, 'registration_sha256': registration_sha256,
                    'binding_sha256': binding_sha256, 'farm_sha256': compiled.farm_sha256,
                    'numeric_input_sha256': compiled.thermal_sha256,
                    'code_sha256': code_sha256}
        candidate_id = VERSION + ':' + sha256(_raw(identity)).hexdigest()
        parameters, heater = value['parameters'], value['heater']
        state = (value['initial_state']['temperature']['value'],
                 value['initial_state']['humidity_ratio']['value'])
        _indoor(state, parameters)
        previous = None
        previous_end = None
        traces = []
        for index, interval in enumerate(value['intervals']):
            start, end = utc(interval['start']), utc(interval['end'])
            _need(start < end and (end - start).total_seconds() == 3600 and
                  (previous_end is None or start == previous_end),
                  'TIMESTAMP_HOLD: authored forcing interval differs')
            initial = value['initial_state'] if previous is None else {}
            if previous is not None:
                previous_raw, previous_trace = previous
                digest = sha256(previous_raw).hexdigest()
                for name in ('temperature', 'humidity_ratio'):
                    pointer = f"/steps/{len(previous_trace['steps']) - 1}/state_end/{name}"
                    record = previous_trace['steps'][-1]['state_end'][name]
                    initial[name] = {'value': record['value'], 'unit': record['unit'],
                                     'origin': 'derived',
                                     'basis_ref': f'trace-sha256:{digest}#{pointer}',
                                     'version': 'v1',
                                     'calculation_rule_ref': 'thermal-state-carry-v1',
                                     'calculation_rule_version': 'v1',
                                     'previous_trace_id': previous_trace['trace_id'],
                                     'previous_trace_sha256': digest,
                                     'previous_state_pointer': pointer}
            steps = []
            step_start = start
            while step_start < end:
                step_end = step_start + timedelta(seconds=60)
                _need(step_end <= end, 'TIMESTAMP_HOLD: nonintegral final step')
                forcing = interval['forcing']
                whole = euler_step(_state(*state), parameters, forcing, heater, q(60, 's'))
                first_half = euler_step(_state(*state), parameters, forcing, heater, q(30, 's'))
                half_state = (first_half['state_end']['temperature']['value'],
                              first_half['state_end']['humidity_ratio']['value'])
                second_half = euler_step(_state(*half_state), parameters, forcing, heater, q(30, 's'))
                deltas = {
                    'temperature': q(abs(whole['state_end']['temperature']['value'] -
                                         second_half['state_end']['temperature']['value']), 'K'),
                    'humidity_ratio': q(abs(whole['state_end']['humidity_ratio']['value'] -
                                            second_half['state_end']['humidity_ratio']['value']),
                                        'kg_v/kg_da'),
                    'delivered_heat_energy': q(abs(whole['heat_terms']['heater']['value'] -
                                                   first_half['heat_terms']['heater']['value'] -
                                                   second_half['heat_terms']['heater']['value']), 'J'),
                }
                for name, record in (('vapor_residual', whole['vapor_residual']),
                                     ('aggregate_energy_residual', whole['aggregate_energy_residual']),
                                     *deltas.items()):
                    _need(record['value'] <= LIMITS[name][0] if name in deltas else
                          abs(record['value']) <= LIMITS[name][0],
                          'NUMERICAL_HOLD: preregistered residual/convergence limit exceeded')
                whole.update(start_utc=_iso(step_start), end_utc=_iso(step_end),
                             convergence_deltas=deltas, acceptance_rule_version='v1')
                steps.append(whole)
                state = (whole['state_end']['temperature']['value'],
                         whole['state_end']['humidity_ratio']['value'])
                step_start = step_end
            trace = {**identity, 'candidate_id': candidate_id,
                     'candidate_version': VERSION, 'status': 'unpublished_candidate',
                     'claim_scope': 'synthetic_software_only',
                     'trace_id': f'{candidate_id}:hour-{index}',
                     'trace_sequence_index': index,
                     'base_snapshot_id': value['base_snapshot_id'],
                     'base_source_sha256': value['base_source_sha256'],
                     'compiler_version': value['compiler_version'],
                     'engine_version': ENGINE_VERSION,
                     'unit_registry_version': UNIT_REGISTRY_VERSION,
                     'model_version': value['model_version'],
                     'interval': {'start_utc': interval['start'], 'end_utc': interval['end']},
                     'initial_state': initial, 'parameters': parameters,
                     'forcing': interval['forcing'], 'heater': heater,
                     'condensation_policy': 'hold_on_saturation',
                     'steps': steps}
            trace_raw = _raw(trace)
            _need(len(trace_raw) <= MAX_TRACE_BYTES,
                  'INPUT_HOLD: authored trace exceeds bounded size')
            traces.append(trace_raw)
            previous = trace_raw, trace
            previous_end = end
        return AuthoredThermalCandidate(candidate_id, registration_sha256,
                                        compiled.thermal_sha256, code_sha256,
                                        tuple(traces))
    except (KeyError, IndexError, TypeError, OverflowError, UnicodeError, ValueError) as exc:
        if isinstance(exc, ThermalHold):
            raise
        raise AuthoredThermalCandidateHold('authored numeric contract unavailable') from exc


def calculate_authored_candidate(service, tenant, scenario_id, revision,
                                 expected_scenario_sha256):
    if type(service) is not FarmAuthoringService:
        raise AuthoredThermalCandidateHold('authored farm authority unavailable')
    try:
        before = service.read_registration(tenant, scenario_id, revision,
                                           expected_scenario_sha256)
        compiled = CompiledFarmInputs(canonical_farm_inputs(before['farm']),
                                      before['numeric_input_bytes'])
        if before['compiled'] != json.loads(compiled.thermal_bytes):
            raise AuthoredThermalCandidateHold('authored numeric input differs')
        binding_sha256 = sha256(canonical_input_bytes(before['binding'])).hexdigest()
        code_sha256 = _code_sha256()
        result = _calculate(compiled, before['scenario_sha256'], binding_sha256,
                            code_sha256)
        after = service.read_registration(tenant, scenario_id, revision,
                                          expected_scenario_sha256)
        if (before['scenario_sha256'] != after['scenario_sha256'] or
                before['numeric_input_bytes'] != after['numeric_input_bytes'] or
                before['binding'] != after['binding'] or
                code_sha256 != _code_sha256()):
            raise AuthoredThermalCandidateHold('authored inputs changed during calculation')
        return result
    except (PermissionError, ValueError, KeyError, TypeError) as exc:
        if isinstance(exc, (AuthoredThermalCandidateHold, ThermalHold)):
            raise
        raise AuthoredThermalCandidateHold('current authored registration unavailable') from exc


def verify_authored_candidate(service, tenant, scenario_id, revision,
                              expected_scenario_sha256, candidate):
    if type(candidate) is not AuthoredThermalCandidate:
        raise AuthoredThermalCandidateHold('authored candidate type differs')
    expected = calculate_authored_candidate(service, tenant, scenario_id, revision,
                                             expected_scenario_sha256)
    if candidate != expected:
        raise AuthoredThermalCandidateHold('authored candidate replay differs')
    return True
