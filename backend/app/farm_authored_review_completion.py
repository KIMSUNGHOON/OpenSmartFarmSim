"""Verify a completed authored review before an independent release decision."""

from dataclasses import dataclass
from datetime import timezone
from hashlib import sha256
import json

from psycopg import sql

from .execution_verifier import ExecutionVerifier
from .farm_authored_review import (FarmAuthoredReviewService, INPUT_VERSION,
                                   review_artifact)
from .jobs import canonical_input_bytes
from .thermal_units import utc


class AuthoredReviewCompletionHold(ValueError):
    pass


def _need(condition):
    if not condition:
        raise AuthoredReviewCompletionHold('authored CLI review completion unavailable')


def _iso(moment):
    return moment.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


@dataclass(frozen=True)
class AuthoredReviewCompletion:
    tenant_id: str
    review_job_id: str
    review_input_sha256: str
    scenario_id: str
    scenario_revision: str
    registration_sha256: str
    farm_sha256: str
    numeric_input_sha256: str
    rights_declaration_sha256: str
    binding_sha256: str
    base_snapshot_id: str
    base_source_sha256: str
    decision_context_id: str
    context_sha256: str
    decision_at_utc: str
    claim_mode: str
    decision_time_kind: str
    candidate_id: str
    code_sha256: str
    trace_sha256: tuple[str, str]
    artifact_sha256: str
    decision_id: str
    capture_id: str
    attempt: int
    decision_recorded_at_utc: str

    @property
    def proof_sha256(self):
        return sha256(canonical_input_bytes({**self.__dict__,
            'trace_sha256': list(self.trace_sha256)})).hexdigest()


class AuthoredReviewCompletionVerifier:
    def __init__(self, review, execution_verifier):
        if (type(review) is not FarmAuthoredReviewService or
                type(execution_verifier) is not ExecutionVerifier):
            raise AuthoredReviewCompletionHold('authored review verifier authority unavailable')
        self.review = review
        self.execution_verifier = execution_verifier
        self.jobs = review.authoring.replay.jobs
        self.runs = review.authoring.replay.thermal.runs

    def verify(self, tenant, review_job_id, expected_registration_sha256):
        try:
            with self.jobs.connect() as conn:
                table = self.jobs._table
                job = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
                    .format(table('jobs')), (tenant, review_job_id)).fetchone()
                _need(job is not None and job['stage'] == 'collection_review' and
                      job['state'] == 'succeeded' and not job['cancel_requested'])
                self.jobs._verified_input(job)
                value = json.loads(job['input_bytes'])
                _need(value.get('input_version') == INPUT_VERSION and
                      value.get('registration_sha256') == expected_registration_sha256 and
                      canonical_input_bytes(value) == job['input_bytes'])
                _need(self.review.verify_input(job, value) == value)
                snapshot = self.runs.get_snapshot(tenant, value['base_snapshot_id'])
                context = self.runs.get_decision_context(tenant, value['base_snapshot_id'],
                    value['decision_context_id'])
                _need(snapshot is not None and context is not None and
                      context['context_sha256'] == value['context_sha256'] and
                      context['claim_mode'] == value['claim_mode'] and
                      context['decision_time_kind'] == value['decision_time_kind'] and
                      context['decision_at_utc'] == value['decision_at_utc'])
                publication = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
                    .format(table('job_publications')), (tenant, review_job_id)).fetchone()
                _need(publication is not None and publication['decision_id'] is not None and
                      publication['manifest'].get('input_sha256') == job['input_sha256'] and
                      publication['manifest'].get('stage') == 'collection_review')
                attempt = publication['attempt']
                rows = {}
                for name, table_name in (('decision', 'ai_decisions'),
                                         ('invocation', 'attempt_invocations'),
                                         ('outcome', 'attempt_outcomes')):
                    rows[name] = conn.execute(sql.SQL(
                        'SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s')
                        .format(table(table_name)), (tenant, review_job_id, attempt)).fetchone()
                decision, invocation, outcome = (rows[key] for key in
                                                 ('decision', 'invocation', 'outcome'))
                _need(all(row is not None for row in (decision, invocation, outcome)))
                expected_artifact = review_artifact(value, job['input_sha256'])
                artifact_sha256 = sha256(expected_artifact).hexdigest()
                _need(decision['decision_id'] == publication['decision_id'] and
                      decision['artifact_sha256'] == publication['artifact_sha256'] ==
                      artifact_sha256 and decision['disposition'] == 'proceed' and
                      job['attempt_count'] == attempt and
                      invocation['execution_kind'] == 'codex_cli' and
                      (invocation['model'], invocation['reasoning_effort']) ==
                      ('gpt-6-sol', 'xhigh') and
                      outcome['state'] == 'succeeded' and outcome['exit_code'] == 0 and
                      outcome['decision_id'] == decision['decision_id'] and
                      snapshot['recorded_at'] <= job['created_at'] <=
                      decision['recorded_at'] <= publication['published_at'] and
                      context['recorded_at'] <= job['created_at'] and
                      utc(context['issued_at_utc']) <= job['created_at'] and
                      utc(value['decision_at_utc']) <= decision['recorded_at'] and
                      self.jobs._verify_decision_final(conn, job, attempt,
                          decision['decision_id'], artifact_sha256))
                capture = self.jobs._valid_cli_capture(conn, job, attempt,
                                                       decision['output_sha256'])
                _need(capture is not None and capture['capture_id'] == decision['capture_id'] and
                      capture['jsonl_sha256'] == decision['capture_sha256'] and
                      invocation['created_at'] <= capture['sealed_at'] <=
                      decision['recorded_at'])
            _need(self.jobs.read_artifact(tenant, review_job_id) == expected_artifact)
            _need(self.execution_verifier(tenant, review_job_id, attempt,
                capture['capture_id'], value['base_snapshot_id'], decision['decision_id']) is True)
            with self.jobs.connect() as conn:
                final_job = conn.execute(sql.SQL(
                    'SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
                    .format(self.jobs._table('jobs')),
                    (tenant, review_job_id)).fetchone()
                _need(final_job is not None and final_job['state'] == 'succeeded' and
                      final_job['input_sha256'] == job['input_sha256'] and
                      not final_job['cancel_requested'])
            _need(self.review.verify_input(final_job, value) == value)
            return AuthoredReviewCompletion(
                tenant_id=tenant, review_job_id=str(review_job_id),
                review_input_sha256=job['input_sha256'],
                scenario_id=value['scenario_id'],
                scenario_revision=value['scenario_revision'],
                registration_sha256=value['registration_sha256'],
                farm_sha256=value['farm_sha256'],
                numeric_input_sha256=value['numeric_input_sha256'],
                rights_declaration_sha256=value['rights_declaration_sha256'],
                binding_sha256=value['binding_sha256'],
                base_snapshot_id=value['base_snapshot_id'],
                base_source_sha256=value['base_source_sha256'],
                decision_context_id=value['decision_context_id'],
                context_sha256=value['context_sha256'],
                decision_at_utc=value['decision_at_utc'],
                claim_mode=value['claim_mode'],
                decision_time_kind=value['decision_time_kind'],
                candidate_id=value['candidate_id'],
                code_sha256=value['code_sha256'],
                trace_sha256=tuple(value['trace_sha256']),
                artifact_sha256=artifact_sha256,
                decision_id=str(decision['decision_id']),
                capture_id=str(capture['capture_id']),
                attempt=attempt,
                decision_recorded_at_utc=_iso(decision['recorded_at']))
        except Exception:
            raise AuthoredReviewCompletionHold(
                'authored CLI review completion unavailable') from None
