"""Prepare final authored thermal bytes from a current signed release packet."""

from dataclasses import dataclass
from hashlib import sha256
import json

from .authored_thermal_candidate import (AuthoredThermalCandidate,
    calculate_authored_candidate, _raw)
from .farm_authoring_storage import FarmAuthoringService
from .farm_authored_release import VerifiedAuthoredRelease, _runtime_manifest
from .farm_authored_release_store import AuthoredReleaseStore
from .jobs import canonical_input_bytes


VERSION = 'authored-thermal-run-v1'


class AuthoredRunHold(ValueError):
    pass


def _need(condition):
    if not condition:
        raise AuthoredRunHold('authored thermal Run preparation unavailable')


def _hash(raw):
    return sha256(raw).hexdigest()


@dataclass(frozen=True)
class PreparedAuthoredRun:
    run_id: str
    report_raw: bytes
    trace_raws: tuple[bytes, bytes]

    @property
    def trace_sha256(self):
        return tuple(_hash(raw) for raw in self.trace_raws)


def build_authored_run_packet(candidate, release, *, tenant, scenario_id, revision,
                              registration_sha256):
    """Pure byte derivation; only a trusted caller may treat it as publishable."""
    try:
        _need(type(candidate) is AuthoredThermalCandidate and
              type(release) is VerifiedAuthoredRelease)
        request = json.loads(release.request_raw)
        _need(canonical_input_bytes(request) == release.request_raw and
              request['request_version'] == 'farm-authored-release-request-v1' and
              request['scope'] == 'synthetic_software_only' and
              request['pending_holds'] ==
                  ['authored_input_review', 'authored_snapshot_release'])
        proof = request['completion']
        original = {key: value for key, value in proof.items() if key != 'proof_sha256'}
        _need(_hash(canonical_input_bytes(original)) == proof['proof_sha256'] and
              (proof['tenant_id'], proof['scenario_id'], proof['scenario_revision'],
               proof['registration_sha256']) ==
              (tenant, scenario_id, revision, registration_sha256) and
              proof['claim_mode'] == 'ex_post_replay' and
              candidate.registration_sha256 == registration_sha256 and
              candidate.numeric_input_sha256 == proof['numeric_input_sha256'] and
              candidate.code_sha256 == proof['code_sha256'] and
              candidate.candidate_id == proof['candidate_id'] and
              list(candidate.trace_sha256) == proof['trace_sha256'])
        identity = {'run_version': VERSION, 'tenant_id': tenant,
            'registration_sha256': registration_sha256,
            'review_job_id': proof['review_job_id'],
            'review_input_sha256': proof['review_input_sha256'],
            'candidate_id': candidate.candidate_id,
            'candidate_trace_sha256': list(candidate.trace_sha256),
            'decision_context_id': proof['decision_context_id'],
            'context_sha256': proof['context_sha256'],
            'decision_at_utc': proof['decision_at_utc'],
            'review_at_utc': proof['decision_recorded_at_utc'],
            'release_sha256': release.release_sha256,
            'release_request_sha256': _hash(release.request_raw)}
        run_id = VERSION + ':' + _hash(canonical_input_bytes(identity))
        traces = []
        for index, raw in enumerate(candidate.trace_raws):
            trace = json.loads(raw)
            _need(_raw(trace) == raw and trace['status'] == 'unpublished_candidate' and
                  trace['claim_scope'] == 'synthetic_software_only' and
                  trace['trace_sequence_index'] == index and
                  trace['trace_id'] == f'{candidate.candidate_id}:hour-{index}' and
                  trace['candidate_id'] == candidate.candidate_id and
                  trace['registration_sha256'] == registration_sha256 and
                  trace['numeric_input_sha256'] == proof['numeric_input_sha256'] and
                  trace['farm_sha256'] == proof['farm_sha256'] and
                  trace['binding_sha256'] == proof['binding_sha256'] and
                  trace['base_snapshot_id'] == proof['base_snapshot_id'] and
                  trace['base_source_sha256'] == proof['base_source_sha256'] and
                  trace['code_sha256'] == proof['code_sha256'] and
                  len(trace['steps']) == 60)
            original_id = trace['trace_id']
            trace.update(trace_version='authored-thermal-run-trace-v1',
                status='accepted', claim_scope='synthetic_thermal_replay_only',
                run_id=run_id, trace_id=f'{run_id}:hour-{index}',
                candidate_trace_id=original_id,
                candidate_trace_sha256=candidate.trace_sha256[index],
                tenant_id=tenant, scenario_id=scenario_id,
                scenario_revision=revision,
                review_job_id=proof['review_job_id'],
                review_input_sha256=proof['review_input_sha256'],
                decision_id=proof['decision_id'], capture_id=proof['capture_id'],
                decision_context_id=proof['decision_context_id'],
                context_sha256=proof['context_sha256'],
                decision_at_utc=proof['decision_at_utc'],
                review_at_utc=proof['decision_recorded_at_utc'],
                claim_mode=proof['claim_mode'],
                decision_time_kind=proof['decision_time_kind'],
                release_sha256=release.release_sha256,
                release_request_sha256=_hash(release.request_raw),
                release_issued_at_utc=release.issued_at_utc)
            if index == 1:
                previous = traces[0]
                previous_value = json.loads(previous)
                _need(trace['interval']['start_utc'] ==
                      previous_value['interval']['end_utc'])
                for field in ('temperature', 'humidity_ratio'):
                    carry = trace['initial_state'][field]
                    pointer = f"/steps/{len(previous_value['steps']) - 1}/state_end/{field}"
                    _need(carry['previous_trace_id'] ==
                          f'{candidate.candidate_id}:hour-0' and
                          carry['previous_trace_sha256'] == candidate.trace_sha256[0] and
                          carry['previous_state_pointer'] == pointer and
                          (carry['value'], carry['unit']) ==
                          (previous_value['steps'][-1]['state_end'][field]['value'],
                           previous_value['steps'][-1]['state_end'][field]['unit']))
                    carry['previous_trace_id'] = previous_value['trace_id']
                    carry['previous_trace_sha256'] = _hash(previous)
                    carry['basis_ref'] = f'trace-sha256:{_hash(previous)}#{pointer}'
            final_raw = _raw(trace)
            _need(len(final_raw) <= 1_048_576)
            traces.append(final_raw)
        report = {**identity, 'gate_version': 'authored-thermal-run-preparation-v1',
            'status': 'prepared_unpublished',
            'scenario_id': scenario_id, 'scenario_revision': revision,
            'run_id': run_id, 'release_issued_at_utc': release.issued_at_utc,
            'trace_sha256': [_hash(raw) for raw in traces],
            'claim_scope': 'synthetic_thermal_replay_only'}
        report_raw = canonical_input_bytes(report)
        return PreparedAuthoredRun(run_id, report_raw, tuple(traces))
    except Exception:
        raise AuthoredRunHold('authored thermal Run preparation unavailable') from None


class AuthoredRunPreparer:
    """Bind current owned farm, release custody and final trace bytes."""

    def __init__(self, authoring, release_store):
        self.authoring = authoring
        self.release_store = release_store
        self._binding()

    def _binding(self):
        authoring, release_store = self.authoring, self.release_store
        if (type(authoring) is not FarmAuthoringService or
                type(release_store) is not AuthoredReleaseStore or
                release_store.verifier.completion.review.authoring is not authoring or
                release_store.jobs is not authoring.replay.jobs):
            raise AuthoredRunHold('authored Run authority unavailable')

    def prepare(self, tenant, review_job_id, scenario_id, revision,
                registration_sha256):
        try:
            self._binding()
            release = self.release_store.get(tenant, review_job_id,
                                             registration_sha256)
            _need(release is not None)
            candidate = calculate_authored_candidate(self.authoring, tenant,
                scenario_id, revision, registration_sha256)
            packet = build_authored_run_packet(candidate, release,
                tenant=tenant, scenario_id=scenario_id, revision=revision,
                registration_sha256=registration_sha256)
            code, environment = _runtime_manifest(self.release_store.verifier.root)
            request = json.loads(release.request_raw)
            _need((code, environment) ==
                  (request['runtime_code_files'], request['runtime_environment_files']))
            self._binding()
            return packet
        except Exception:
            raise AuthoredRunHold('authored thermal Run preparation unavailable') from None
