"""Bound stored schema4 references and a calculation-free immutable job intent."""
from hashlib import sha256
from typing import Literal
from uuid import UUID

from pydantic import Field,field_validator

from .economic_batch_source_store import EconomicBatchSourceStore
from .economic_contracts import untrusted_data
from .economic_production_batches import (BatchEconomicScenario,ProductionBatchLedger,
    FORMULA_VERSION,_code_fence,_raw)
from .economics import canonical_scenario_sha256
from .job_store import JobStore
from .market_hold_store import MarketHoldStore
from .provenance import FrozenContract,Name,Digest
from .runtime_roles import RuntimeLoginPolicy
from .thermal_run_store import ThermalRunStore
from .thermal_scenario_store import IDENTIFIER

READ_SCOPES=('metadata','economic_batch_source_read','decision_context_read','market_hold_context_read')
_SOURCE_READS=frozenset({'get_economic_scenario','get_economic_scenario_pin','get_economic_input',
    'get_prior_batch_cost','get_settlement_evidence','get_production_batch'})


class BatchCalculationHold(ValueError):
    pass


class EconomicBatchAuthority:
    def __init__(self,jobs,source,holds):
        self.jobs,self._source,self._holds=jobs,source,holds
        try:self._bound=self._binding()
        except RuntimeError:raise ValueError('economic batch authority binding rejected')from None

    def _binding(self):
        try:
            jobs,source,holds=self.jobs,self._source,self._holds
            binding=jobs.runtime_identity
            contexts=holds._context_store
            if (type(jobs)is not JobStore or type(source)is not EconomicBatchSourceStore or
                    type(holds)is not MarketHoldStore or type(contexts)is not ThermalRunStore or
                    type(binding)is not tuple or len(binding)!=2 or type(binding[0])is not RuntimeLoginPolicy or
                    binding[1]!='authority' or not binding[0].economic_batch_source_storage or
                    binding[0].schema!=jobs.schema or jobs.audit_runtime_grants is not True or
                    type(jobs._dsn)is not str or not jobs._dsn or not callable(jobs.principal_provider)):
                raise ValueError()
            for store in (source,holds,contexts):
                if (store.runtime_identity!=binding or store.schema!=jobs.schema or
                        store.dsn!=jobs._dsn or store._principal_provider is not jobs.principal_provider):
                    raise ValueError()
            return (jobs,source,holds,contexts,binding,jobs._dsn,jobs.schema,jobs.principal_provider,
                    holds._scope_resolver,holds._key,contexts._context_verifier)
        except Exception:raise RuntimeError('economic batch authority binding changed')from None

    def require(self,tenant,*,execute=False):
        if self._binding()!=self._bound:
            raise RuntimeError('economic batch authority binding changed')
        scopes=READ_SCOPES+(('simulation_execute',)if execute else ())
        if not all(self.jobs._has_scope(tenant,scope)for scope in scopes):
            raise PermissionError('economic batch access denied')

    def tenant_is_authenticated(self,tenant):
        try:self.require(tenant);return True
        except PermissionError:return False

    def __getattr__(self,name):
        if name not in _SOURCE_READS|{'get_market_hold_report','get_decision_context'}:
            raise AttributeError(name)
        def read(*args):
            try:tenant=self.jobs.principal_provider()['tenant_id']
            except Exception:raise PermissionError('economic batch access denied')from None
            self.require(tenant)
            if name=='get_decision_context'and(not args or args[0]!=tenant):
                raise PermissionError('economic batch access denied')
            store=self._source if name in _SOURCE_READS else self._holds
            try:return getattr(store,name)(*args)
            finally:self.require(tenant)
        return read


class EconomicBatchCalculationRequest(FrozenContract):
    scenario_id: Name=Field(max_length=200)
    scenario_revision: Name=Field(max_length=200)
    scenario_sha256: Digest
    idempotency_key: str=Field(pattern=IDENTIFIER,max_length=200)


class EconomicBatchCalculationInput(FrozenContract):
    input_version: Literal['economic-batch-calculation-input-v1']
    scenario_id: Name=Field(max_length=200)
    scenario_revision: Name=Field(max_length=200)
    scenario_sha256: Digest
    scenario_source_job_id: str
    evidence_sha256: Digest
    formula_version: Literal['economic-ledger-v10-declared-production-batches']

    @field_validator('scenario_source_job_id')
    @classmethod
    def canonical_uuid(cls,value):
        if str(UUID(value))!=value:raise ValueError('canonical source job UUID required')
        return value


class EconomicBatchCalculationService:
    def __init__(self,authority):
        if type(authority)is not EconomicBatchAuthority:
            raise ValueError('economic batch server authority required')
        self.authority=authority

    def _prepare(self,tenant,body):
        authority=self.authority
        try:
            _code_fence()
            scenario=BatchEconomicScenario.model_validate(untrusted_data(
                authority.get_economic_scenario(body.scenario_id,body.scenario_revision)))
            if ((scenario.tenant_id,scenario.scenario_id,scenario.scenario_revision)!=
                    (tenant,body.scenario_id,body.scenario_revision)or
                    canonical_scenario_sha256(scenario)!=body.scenario_sha256):
                raise ValueError()
            verified=ProductionBatchLedger(authority)._context(scenario)
            pin=authority.get_economic_scenario_pin(body.scenario_id,body.scenario_revision)
            report=authority.get_market_hold_report(scenario.market_context.hold_report_id)
            context=authority.get_decision_context(tenant,report['snapshot_id'],report['decision_context_id'])
            evidence={'scenario':scenario.model_dump(mode='json'),'pin':pin,'verified':verified,
                      'hold':report,'decision_context':context}
            _code_fence()
            return EconomicBatchCalculationInput(input_version='economic-batch-calculation-input-v1',
                scenario_id=scenario.scenario_id,scenario_revision=scenario.scenario_revision,
                scenario_sha256=body.scenario_sha256,scenario_source_job_id=pin['immutable_job_input_ref'],
                evidence_sha256=sha256(_raw(evidence)).hexdigest(),formula_version=FORMULA_VERSION)
        except (ValueError,TypeError,KeyError,AttributeError):
            raise BatchCalculationHold('economic batch input unavailable')from None
        finally:authority.require(tenant)

    def submit(self,tenant,body):
        authority=self.authority
        if type(authority)is not EconomicBatchAuthority:
            raise RuntimeError('economic batch authority changed')
        def guard():
            if self.authority is not authority:
                raise RuntimeError('economic batch authority changed')
            authority.require(tenant,execute=True)
        guard()
        body=EconomicBatchCalculationRequest.model_validate(untrusted_data(body))
        try:value=self._prepare(tenant,body)
        finally:guard()
        def final_guard():
            guard()
            try:
                if self._prepare(tenant,body)!=value:
                    raise RuntimeError('economic batch evidence changed')
            finally:guard()
        key='economic-batch-calculation-v1:'+sha256(body.idempotency_key.encode('ascii')).hexdigest()
        return authority.jobs.submit(tenant,'simulation',value.model_dump(mode='json'),key,
                                     commit_guard=final_guard)
