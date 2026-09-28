"""Register the existing conditional scenario and actual intent atomically."""

from datetime import datetime
from hashlib import sha256
from typing import Literal

from pydantic import Field

from .api_contracts import JobStatus, public_job_status
from .api_market_source import _MarketSources
from .job_store import JobStore
from .jobs import canonical_input_bytes
from .market_candidate_store import MarketCandidateStore
from .market_hold_store import MarketHoldStore
from .market_source_store import MarketSourceStore
from .market_scenario import (MarketScenarioRequest, MarketScenarioService,
    _UnsupportedPath, _InventoryUnresolved, _json)
from .provenance import FrozenContract
from .runtime_roles import RuntimeLoginPolicy
from .thermal_run_store import ThermalRunStore
from .thermal_scenario_store import IDENTIFIER


ECONOMIC_SCENARIO_SCOPES = ('metadata', 'market_source_read', 'market_candidate_read',
    'market_candidate_write', 'decision_context_read', 'market_hold_context_read')


class EconomicScenarioRequest(FrozenContract):
    request: MarketScenarioRequest
    idempotency_key: str = Field(pattern=IDENTIFIER, max_length=200)


class EconomicScenarioSummary(FrozenContract):
    candidate_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    scenario_id: str = Field(min_length=1, max_length=200)
    scenario_revision: str = Field(min_length=1, max_length=200)
    scenario_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    registration_status: Literal['pinned_user_assumption']
    recorded_at: datetime
    intent_job: JobStatus


class EconomicScenarioService:
    def __init__(self, jobs, candidates):
        self.jobs, self.candidates = jobs, candidates
        try:
            self._binding()
        except RuntimeError:
            raise ValueError('economic scenario binding rejected') from None

    def _binding(self):
        jobs, candidates = self.jobs, self.candidates
        binding = getattr(jobs, 'runtime_identity', None)
        view = getattr(candidates, '_source', None)
        if (type(jobs) is not JobStore or type(candidates) is not MarketCandidateStore or
                type(binding) is not tuple or len(binding) != 2 or type(binding[0]) is not RuntimeLoginPolicy or
                binding[1] != 'authority' or not binding[0].market_calculation or
                not binding[0].market_source_storage or binding[0].schema != jobs.schema or
                type(jobs._dsn) is not str or not jobs._dsn or jobs.audit_runtime_grants is not True or
                not callable(jobs.principal_provider) or type(view) is not _MarketSources or
                view._principal_provider is not jobs.principal_provider or
                type(view._source) is not MarketSourceStore or type(view._holds) is not MarketHoldStore or
                type(view._holds._context_store) is not ThermalRunStore):
            raise RuntimeError('economic scenario binding rejected')
        for store in (candidates, view._source, view._holds, view._holds._context_store):
            if (store.runtime_identity != binding or store.schema != jobs.schema or
                    store.dsn != jobs._dsn or store._principal_provider is not jobs.principal_provider):
                raise RuntimeError('economic scenario binding rejected')

    def _access(self, tenant):
        if not all(self.jobs._has_scope(tenant, scope) for scope in ECONOMIC_SCENARIO_SCOPES):
            raise PermissionError('economic scenario admission denied')

    def _prepare(self, tenant, request):
        try:
            return MarketScenarioService(self.candidates)._prepare(request.model_dump(mode='json'), tenant)
        except (_UnsupportedPath, _InventoryUnresolved):
            raise ValueError('economic scenario preparation unavailable') from None
        except ValueError as exc:
            self._access(tenant)
            self._binding()
            if exc.__cause__ is not None:
                raise RuntimeError('economic scenario source unavailable') from None
            raise

    @staticmethod
    def _fingerprint(prepared):
        _, scenario, record, numbers = prepared
        return sha256(_json([scenario.model_dump(mode='json'), record, numbers]).encode()).digest()

    def submit(self, tenant, body):
        self._access(tenant)
        self._binding()
        body = EconomicScenarioRequest.model_validate_json(canonical_input_bytes(body.model_dump(mode='json')))
        jobs, candidates, view = self.jobs, self.candidates, self.candidates._source
        source, holds, contexts = view._source, view._holds, view._holds._context_store
        def guard():
            self._access(tenant)
            self._binding()
            if (self.jobs is not jobs or self.candidates is not candidates or candidates._source is not view or
                    view._source is not source or view._holds is not holds or holds._context_store is not contexts):
                raise RuntimeError('economic scenario binding rejected')
        guard()
        prepared = self._prepare(tenant, body.request)
        guard()
        fingerprint = self._fingerprint(prepared)
        admitted = []
        def adopt(conn, _row):
            guard()
            _, scenario, record, numbers = prepared
            admitted.append(candidates._pin_in_transaction(conn, record, scenario.model_dump(mode='python'), numbers))
            guard()
        def final_guard():
            guard()
            if self._fingerprint(self._prepare(tenant, body.request)) != fingerprint:
                raise RuntimeError('economic scenario input changed')
            guard()
        key = 'economic-scenario-v1:'+sha256(body.idempotency_key.encode('ascii')).hexdigest()
        job = jobs.submit(tenant, 'collection', body.request.model_dump(mode='json'), key,
                          admission_action=adopt, commit_guard=final_guard)
        row = admitted[0]
        return EconomicScenarioSummary(candidate_id=row['candidate_id'], scenario_id=row['scenario_id'],
            scenario_revision=row['revision'], scenario_sha256=row['scenario_sha256'],
            registration_status='pinned_user_assumption', recorded_at=row['recorded_at'],
            intent_job=public_job_status(job))
