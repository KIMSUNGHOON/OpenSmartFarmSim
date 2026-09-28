"""Fenced deterministic arithmetic; result and job completion share a transaction."""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import Field
from psycopg import sql

from .api_economic_scenario import EconomicScenarioService
from .jobs import canonical_input_bytes, require_name, require_seconds
from .market_result_store import MarketResultStore, MarketResultDenied
from .market_result_codec import encode_market_result
from .market_scenario import MarketScenarioService
from .provenance import FrozenContract
from .thermal_publisher import runtime_digests
from .thermal_scenario_store import IDENTIFIER


CALCULATION_SCOPES = ('metadata', 'artifact', 'simulation_execute', 'market_source_read',
    'market_candidate_read', 'market_result_read', 'market_result_write',
    'decision_context_read', 'market_hold_context_read')


class EconomicCalculationInput(FrozenContract):
    input_version: Literal['economic-calculation-input-v1']
    scenario_id: str = Field(pattern=IDENTIFIER, max_length=200)
    scenario_revision: str = Field(pattern=IDENTIFIER, max_length=200)
    scenario_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    candidate_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    formula_version: Literal['economic-ledger-v9-sales-settlement']


@dataclass(frozen=True)
class EconomicCalculationOutcome:
    job_id: UUID
    attempt: int
    state: str
    reason_code: str
    economic_result_id: str | None = None


class _LeaseLost(ValueError):
    pass


class _InputHold(ValueError):
    pass


class EconomicCalculationWorker:
    def __init__(self, jobs, results, *, tenant_id, lease_seconds=300):
        try:
            require_name(tenant_id, 'tenant_id')
            require_seconds(lease_seconds, 'lease_seconds')
            if type(results) is not MarketResultStore:
                raise ValueError()
            self.jobs, self.results = jobs, results
            self.authority = EconomicScenarioService(jobs, results._candidates)
            self._binding()
        except Exception:
            raise ValueError('economic calculation binding rejected') from None
        self.tenant_id, self.lease_seconds = tenant_id, lease_seconds

    def _binding(self):
        self.authority._binding()
        if (type(self.results) is not MarketResultStore or self.authority.jobs is not self.jobs or
                self.authority.candidates is not self.results._candidates or
                self.results.runtime_identity != self.jobs.runtime_identity or
                self.results.schema != self.jobs.schema or self.results.dsn != self.jobs._dsn or
                self.results._principal_provider is not self.jobs.principal_provider):
            raise RuntimeError('economic calculation binding rejected')

    def _pointers(self):
        candidate = self.results._candidates
        view = candidate._source
        return (self.jobs, self.results, candidate, view, view._source, view._holds, view._holds._context_store)

    def _access(self):
        if not all(self.jobs._has_scope(self.tenant_id, scope) for scope in CALCULATION_SCOPES):
            raise PermissionError('economic calculation denied')

    @staticmethod
    def _digests():
        return runtime_digests(Path(__file__).resolve().parents[2])

    def _calculate(self, value):
        self._access()
        record = self.results._candidates.get_market_candidate(value.scenario_id, value.scenario_revision)
        if (record is None or record['candidate_id'] != value.candidate_id or
                record['economic_scenario_sha256'] != value.scenario_sha256):
            raise _InputHold()
        try:
            result = MarketScenarioService(self.results._candidates).calculate_pinned(
                value.scenario_id, value.scenario_revision, self.tenant_id)
        except ValueError as exc:
            if exc.__cause__ is not None:
                raise RuntimeError('economic source unavailable') from None
            raise _InputHold() from None
        if result.economic_result.formula_version != value.formula_version:
            raise _InputHold()
        return result

    def _close(self, lease, kind, code):
        try:
            closed = self.jobs.fail(self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'],
                kind, code, termination_reason=code)
            job = self.jobs.get_job(self.tenant_id, lease['job_id']) if closed else None
            state = job['state'] if job else 'unclosed'
        except Exception:
            state = 'unclosed'
        return EconomicCalculationOutcome(lease['job_id'], lease['attempt'], state, code)

    def _lost(self, lease):
        try:
            canceled = self.jobs.ack_cancel(self.tenant_id, lease['job_id'], lease['attempt'],
                lease['lease_token'], termination_reason='canceled_by_request')
        except Exception:
            canceled = False
        return EconomicCalculationOutcome(lease['job_id'], lease['attempt'],
            'canceled' if canceled else 'unclosed', 'canceled_by_request' if canceled else 'economic_lease_lost')

    def run_once(self, job_id):
        self._binding()
        self._access()
        try:
            if type(job_id) is not str or str(UUID(job_id)) != job_id:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise ValueError('economic calculation job ID rejected') from None
        with self.jobs.connect() as conn:
            job = self.jobs._locked_job(conn, self.tenant_id, job_id)
            if job is None or job['stage'] != 'simulation' or job['state'] not in ('queued', 'simulating'):
                return None
            candidate = json.loads(self.jobs._verified_input(job))
            if type(candidate) is not dict or candidate.get('input_version') != 'economic-calculation-input-v1':
                return None
        lease = self.jobs.claim(self.lease_seconds, tenant_id=self.tenant_id,
            allowed_stages=('simulation',), job_id=job_id)
        if lease is None:
            return None
        try:
            self._binding()
            pointers, digests = self._pointers(), self._digests()
            raw = self.jobs.read_input(self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'])
            if raw is None:
                raise _LeaseLost()
            try:
                value = EconomicCalculationInput.model_validate_json(raw)
                if canonical_input_bytes(value.model_dump(mode='json')) != raw:
                    raise ValueError()
            except Exception:
                return self._close(lease, 'fatal', 'economic_input_rejected')
            result = self._calculate(value)
            self._finish(lease, raw, value, result, pointers, digests)
            return EconomicCalculationOutcome(lease['job_id'], lease['attempt'], 'succeeded',
                'completed', result.economic_result.result_id)
        except _LeaseLost:
            return self._lost(lease)
        except (_InputHold, PermissionError, MarketResultDenied):
            return self._close(lease, 'hold', 'economic_input_hold')
        except Exception:
            return self._close(lease, 'transient', 'economic_runtime_failure')

    def _finish(self, lease, raw, value, result, pointers, digests):
        encoded = encode_market_result(result)
        receipt = {'receipt_version': 'economic-calculation-result-v1', 'status': 'completed',
            'claim_scope': 'user_assumption_arithmetic_only', 'scenario_id': value.scenario_id,
            'scenario_revision': value.scenario_revision, 'scenario_sha256': value.scenario_sha256,
            'candidate_id': value.candidate_id, 'formula_version': value.formula_version,
            'market_result_id': result.result_id, 'economic_result_id': result.economic_result.result_id,
            'result_sha256': sha256(encoded).hexdigest(), 'calculation_status': result.calculation_status,
            'assessment_status': result.assessment_status, 'code_sha256': digests[0], 'environment_sha256': digests[1]}
        artifact = canonical_input_bytes(receipt)
        digest = sha256(artifact).hexdigest()
        self.jobs._durable_artifact(artifact, digest)
        def guard():
            self._binding()
            self._access()
            if self._pointers() != pointers or self._digests() != digests:
                raise RuntimeError('economic calculation binding changed')
        with self.jobs.connect() as conn:
            job = self.jobs._locked_job(conn, self.tenant_id, lease['job_id'])
            if (not self.jobs._owns_live_lease(job, lease['attempt'], lease['lease_token']) or
                    job['cancel_requested'] or job['stage'] != 'simulation' or self.jobs._verified_input(job) != raw):
                raise _LeaseLost()
            guard()
            stored = self.results._pin_in_transaction(conn, self.tenant_id, result)
            guard()
            if encode_market_result(self._calculate(value)) != stored['result_raw'] or stored['result_raw'] != encoded:
                raise _InputHold()
            guard()
            updated = conn.execute(sql.SQL("""
                UPDATE {} SET state='succeeded', reason=NULL, lease_token=NULL, lease_until=NULL,
                    updated_at=clock_timestamp()
                WHERE tenant_id=%s AND job_id=%s AND stage='simulation' AND state='simulating'
                    AND attempt_count=%s AND lease_token=%s AND lease_until>clock_timestamp()
                    AND NOT cancel_requested
            """).format(self.jobs._table('jobs')),
                (self.tenant_id, job['job_id'], lease['attempt'], lease['lease_token']))
            if updated.rowcount != 1:
                raise _LeaseLost()
            manifest = {'schema_version': '1', 'job_id': str(job['job_id']), 'stage': 'simulation',
                'input_sha256': job['input_sha256'], 'attempt': lease['attempt'], 'artifact_sha256': digest}
            self.jobs._insert_publication(conn, self.tenant_id, job['job_id'], lease['attempt'], None,
                digest, len(artifact), manifest)
            self.jobs._event(conn, self.tenant_id, job['job_id'], 'succeeded', lease['attempt'])
            self.jobs._outcome(conn, self.tenant_id, job['job_id'], lease['attempt'], 'succeeded',
                termination_reason='completed')
