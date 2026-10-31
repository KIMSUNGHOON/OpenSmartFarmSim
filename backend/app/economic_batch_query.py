"""Typed original batch results, current read authority, and no amount replay."""
from dataclasses import dataclass,fields,is_dataclass,replace
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
import os
from uuid import UUID

from pydantic import Field,TypeAdapter
from psycopg import sql

from .economic_batch_calculation import (EconomicBatchAuthority,EconomicBatchCalculationInput,
    EconomicBatchCalculationRequest,EconomicBatchCalculationService)
from .economic_batch_worker import ARTIFACT_VERSION,MAX_ARTIFACT_BYTES
from .economic_contracts import untrusted_data,iter_economic_numbers
from .economic_production_batches import (ProductionBatchResult,BatchEconomicScenario,OwnedProductionBatch,
    CODE_SHA256,COMPONENT_SHA256,FORMULA_VERSION,_code_fence,_raw,result_bytes)
from .jobs import canonical_input_bytes
from .provenance import FrozenContract,Name,Digest

_RESULT=TypeAdapter(ProductionBatchResult)
_NAME=TypeAdapter(Name)


class BatchResultHold(ValueError):
    pass


class _Envelope(FrozenContract):
    artifact_version: str
    status: str
    claim_scope: str
    tenant_id: Name
    job_id: UUID
    attempt: int=Field(ge=1,le=3)
    input_sha256: Digest
    input: EconomicBatchCalculationInput
    code_sha256: Digest
    environment_sha256: Digest
    result_sha256: Digest
    result: dict


def _finite(value):
    if isinstance(value,Decimal):
        if not value.is_finite():raise BatchResultHold('nonfinite stored amount')
    elif isinstance(value,datetime):
        if value.utcoffset()is None:raise BatchResultHold('stored time needs an explicit offset')
    elif is_dataclass(value):
        for field in fields(value):_finite(getattr(value,field.name))
    elif type(value)is dict:
        for item in value.values():_finite(item)
    elif type(value)in(tuple,list):
        for item in value:_finite(item)


def decode_stored_batch_result(raw):
    try:
        if type(raw)is not bytes or not 1<=len(raw)<=MAX_ARTIFACT_BYTES:raise ValueError()
        value=json.loads(raw)
        if type(value)is not dict or _raw(value)!=raw:raise ValueError()
        entries=value['ledger']['closing_inventory'];inventory=None
        if entries is not None:
            if type(entries)is not list:raise ValueError()
            inventory={}
            for entry in entries:
                if type(entry)is not dict or set(entry)!={'batch_id','grade','channel','quantity_kg'}:
                    raise ValueError()
                key=tuple(_NAME.validate_python(entry[n],strict=True)for n in ['batch_id','grade','channel'])
                if type(entry['quantity_kg'])is not str or key in inventory:raise ValueError()
                amount=Decimal(entry['quantity_kg'])
                if not amount.is_finite()or amount<0:raise ValueError()
                inventory[key]=amount
        parsed={**value,'ledger':{**value['ledger'],'closing_inventory':None}}
        result=_RESULT.validate_json(_raw(parsed))
        result=replace(result,ledger=replace(result.ledger,closing_inventory=inventory))
        _finite(result)
        if(result_bytes(result)!=raw or result.scope!='conditional_user_assumptions_only'or
                result.G0_G4!='not_assessed'or result.R2!='not_approved'or
                result.ledger.assessment_status!='hold'or result.ledger.formula_version!=FORMULA_VERSION or
                result.code_sha256!=CODE_SHA256 or result.component_sha256!=COMPONENT_SHA256):
            raise ValueError()
        return result
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,RecursionError):
        raise BatchResultHold('stored economic batch result invalid')from None


@dataclass(frozen=True)
class StoredBatchResult:
    raw: bytes
    publication_id: UUID
    published_at: datetime
    result: ProductionBatchResult


class EconomicBatchResultQuery:
    def __init__(self,authority):
        if type(authority)is not EconomicBatchAuthority or authority._binding()!=authority._bound:
            raise ValueError('economic batch server authority required')
        self.authority,self.jobs=authority,authority.jobs
        self._bound=self._pointers()

    def _pointers(self):
        return(self.authority,self.jobs,self.authority.jobs,self.jobs.artifact_root,self.jobs.content_access)

    def _access(self,tenant):
        if self._pointers()!=self._bound:raise RuntimeError('economic batch query binding changed')
        self.authority.require(tenant)
        if not self.jobs._has_scope(tenant,'artifact'):raise PermissionError('economic batch query denied')
        _code_fence()

    def _metadata(self,conn,tenant,job_id):
        job=conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s').format(
            self.jobs._table('jobs')),(tenant,job_id)).fetchone()
        if job is None or job['stage']!='simulation'or job['state']!='succeeded':return None
        raw=self.jobs._verified_input(job);data=json.loads(raw)
        if type(data)is not dict or data.get('input_version')!='economic-batch-calculation-input-v1':return None
        value=EconomicBatchCalculationInput.model_validate_json(raw)
        if canonical_input_bytes(value.model_dump(mode='json'))!=raw:raise BatchResultHold('batch input differs')
        publication=conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s').format(
            self.jobs._table('job_publications')),(tenant,job_id)).fetchone()
        if(publication is None or type(publication['artifact_size'])is not int or
                not 1<=publication['artifact_size']<=MAX_ARTIFACT_BYTES or
                job['lease_token']is not None or job['lease_until']is not None or job['cancel_requested']or
                publication['attempt']!=job['attempt_count']or publication['decision_id']is not None):
            raise BatchResultHold('batch publication invalid')
        manifest={'schema_version':'1','job_id':job_id,'stage':'simulation',
            'input_sha256':job['input_sha256'],'attempt':job['attempt_count'],
            'artifact_sha256':publication['artifact_sha256']}
        if canonical_input_bytes(publication['manifest'])!=canonical_input_bytes(manifest):
            raise BatchResultHold('batch manifest differs')
        return job,raw,value,publication

    def _read_raw(self,publication):
        try:
            fd=self.jobs._content_directory()
            try:return self.jobs._read_content(fd,publication['artifact_sha256'],publication['artifact_size'])
            finally:os.close(fd)
        except (OSError,ValueError):raise BatchResultHold('stored batch artifact unavailable')from None

    def _current(self,tenant,value):
        request=EconomicBatchCalculationRequest(scenario_id=value.scenario_id,
            scenario_revision=value.scenario_revision,scenario_sha256=value.scenario_sha256,
            idempotency_key='stored-result-verification')
        if EconomicBatchCalculationService(self.authority)._prepare(tenant,request)!=value:
            raise BatchResultHold('current batch evidence differs')
        self._access(tenant)

    def _binding(self,tenant,value,result):
        scenario=BatchEconomicScenario.model_validate(untrusted_data(self.authority.get_economic_scenario(
            value.scenario_id,value.scenario_revision)))
        batches=tuple(OwnedProductionBatch.model_validate(untrusted_data(self.authority.get_production_batch(
            ref.batch_id,ref.revision)))for ref in scenario.production_batches)
        ledger=result.ledger;inputs=tuple(iter_economic_numbers(scenario))
        if((ledger.scenario_id,ledger.scenario_revision,ledger.scenario_sha256,ledger.decision_at)!=
                (scenario.scenario_id,scenario.scenario_revision,value.scenario_sha256,scenario.decision_at)or
                scenario.tenant_id!=tenant or result.production_batches!=batches or
                ledger.input_provenance!=inputs or ledger.input_versions!=tuple((v.input_id,v.revision)for v in inputs)or
                ledger.market_context!=scenario.market_context or ledger.assessment_market_context!=scenario.scenario_market_context):
            raise BatchResultHold('stored batch result binding differs')
        harvested={v.batch_id for v in scenario.harvests}
        if tuple((v.batch_id,v.revision,v.harvest_event_declared)for v in result.batch_costs)!=tuple(
                (v.batch_id,v.revision,v.batch_id in harvested)for v in batches):
            raise BatchResultHold('stored batch summaries differ')
        identity={'scenario_sha256':value.scenario_sha256,'formula_version':FORMULA_VERSION,
            'batch_records_sha256':sha256(_raw(batches)).hexdigest(),
            'code_sha256':CODE_SHA256,'component_sha256':COMPONENT_SHA256}
        if ledger.result_id!=sha256(_raw(identity)).hexdigest():
            raise BatchResultHold('stored batch identity differs')

    def read(self,tenant,job_id):
        self._access(tenant)
        if type(job_id)is not str or str(UUID(job_id))!=job_id:raise ValueError('canonical batch UUID required')
        try:
            with self.jobs.connect()as conn:
                conn.execute('SET TRANSACTION READ ONLY')
                before=self._metadata(conn,tenant,job_id)
                if before is None:return None
                job,raw_input,value,publication=before
                with self.authority._source.read_scope(tenant):
                    raw=self._read_raw(publication);envelope=_Envelope.model_validate_json(raw)
                    if(_raw(envelope.model_dump(mode='json'))!=raw or
                            envelope.artifact_version!=ARTIFACT_VERSION or envelope.status!='completed'or
                            envelope.claim_scope!='conditional_user_assumptions_only'or
                            (envelope.tenant_id,str(envelope.job_id),envelope.attempt,envelope.input_sha256)!=
                            (tenant,job_id,job['attempt_count'],job['input_sha256'])or envelope.input!=value or
                            sha256(raw).hexdigest()!=publication['artifact_sha256']or len(raw)!=publication['artifact_size']):
                        raise BatchResultHold('batch envelope differs')
                    result_raw=_raw(envelope.result)
                    if sha256(result_raw).hexdigest()!=envelope.result_sha256:raise BatchResultHold('batch result hash differs')
                    result=decode_stored_batch_result(result_raw)
                    self._current(tenant,value);self._binding(tenant,value,result);self._current(tenant,value)
                    if self._metadata(conn,tenant,job_id)!=before or self._read_raw(publication)!=raw:
                        raise BatchResultHold('stored batch changed during query')
                    self._access(tenant)
                    return StoredBatchResult(raw,publication['publication_id'],publication['published_at'],result)
        except PermissionError:raise
        except (ValueError,TypeError,KeyError,AttributeError,OSError,ArithmeticError,RecursionError):
            raise BatchResultHold('economic batch result unavailable')from None
        finally:self._access(tenant)
