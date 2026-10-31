"""One leased Decimal v10 calculation with immutable full result publication."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from uuid import UUID

from psycopg import sql

from .economic_batch_calculation import (EconomicBatchAuthority,EconomicBatchCalculationService,
    EconomicBatchCalculationRequest,EconomicBatchCalculationInput,BatchCalculationHold)
from .economic_contracts import untrusted_data
from .economic_production_batches import BatchEconomicScenario,ProductionBatchLedger,result_bytes,_raw
from .jobs import canonical_input_bytes,require_name,require_seconds
from .thermal_publisher import runtime_digests

ARTIFACT_VERSION='economic-batch-calculation-result-v1'
MAX_ARTIFACT_BYTES=2*1024**2
_BATCH_CODE_FILES=('economic_batch_worker.py','economic_batch_calculation.py','economic_batch_source_store.py',
    'economic_production_batches.py','economic_contracts.py','economics.py','market.py','provenance.py',
    'market_source_store.py','thermal_run_store.py')


@dataclass(frozen=True)
class BatchCalculationOutcome:
    job_id: UUID
    attempt: int
    state: str
    reason_code: str
    economic_result_id: str|None=None


class _LeaseLost(ValueError):
    pass


class EconomicBatchWorker:
    def __init__(self,authority,*,tenant_id,lease_seconds=300):
        if type(authority)is not EconomicBatchAuthority:
            raise ValueError('economic batch server authority required')
        require_name(tenant_id,'tenant_id');require_seconds(lease_seconds,'lease_seconds')
        if authority._binding()!=authority._bound:
            raise ValueError('economic batch binding rejected')
        self.authority,self.jobs=authority,authority.jobs
        self.tenant_id,self.lease_seconds=tenant_id,lease_seconds
        self._bound=self._pointers()

    def _pointers(self):
        return (self.authority,self.jobs,self.authority.jobs,self.jobs.artifact_root,self.jobs.content_access)

    def _access(self):
        if self._pointers()!=self._bound:
            raise RuntimeError('economic batch worker binding changed')
        self.authority.require(self.tenant_id,execute=True)
        if not self.jobs._has_scope(self.tenant_id,'artifact'):
            raise PermissionError('economic batch worker denied')

    @staticmethod
    def _digests():
        root=Path(__file__).resolve().parents[2]
        base,environment=runtime_digests(root)
        files={n:sha256((root/'backend/app'/n).read_bytes()).hexdigest()for n in _BATCH_CODE_FILES}
        return sha256(_raw({'base':base,'batch':files})).hexdigest(),environment

    def _verify(self,value):
        body=EconomicBatchCalculationRequest(scenario_id=value.scenario_id,
            scenario_revision=value.scenario_revision,scenario_sha256=value.scenario_sha256,
            idempotency_key='worker-verification')
        current=EconomicBatchCalculationService(self.authority)._prepare(self.tenant_id,body)
        if current!=value:
            raise BatchCalculationHold('economic batch evidence differs')

    def _guard(self,value,digests):
        self._access()
        if self._digests()!=digests:
            raise BatchCalculationHold('economic batch code or environment changed')
        self._verify(value)
        self._access()
        if self._digests()!=digests:
            raise BatchCalculationHold('economic batch code or environment changed')

    def _close(self,lease,kind,reason):
        try:
            closed=self.jobs.fail(self.tenant_id,lease['job_id'],lease['attempt'],lease['lease_token'],
                kind,reason,termination_reason=reason)
            job=self.jobs.get_job(self.tenant_id,lease['job_id'])if closed else None
            state=job['state']if job else'unclosed'
        except Exception:state='unclosed'
        return BatchCalculationOutcome(lease['job_id'],lease['attempt'],state,reason)

    def _lost(self,lease):
        try:
            canceled=self.jobs.ack_cancel(self.tenant_id,lease['job_id'],lease['attempt'],lease['lease_token'],
                termination_reason='canceled_by_request')
        except Exception:canceled=False
        return BatchCalculationOutcome(lease['job_id'],lease['attempt'],
            'canceled'if canceled else'unclosed','canceled_by_request'if canceled else'economic_batch_lease_lost')

    def run_once(self,job_id):
        self._access()
        if type(job_id)is not str or str(UUID(job_id))!=job_id:
            raise ValueError('canonical batch job UUID required')
        with self.jobs.connect()as conn:
            job=self.jobs._locked_job(conn,self.tenant_id,job_id)
            if job is None or job['stage']!='simulation'or job['state']not in('queued','simulating'):
                return None
            candidate=json.loads(self.jobs._verified_input(job))
            if type(candidate)is not dict or candidate.get('input_version')!='economic-batch-calculation-input-v1':
                return None
        lease=self.jobs.claim(self.lease_seconds,allowed_stages=('simulation',),
            tenant_id=self.tenant_id,job_id=job_id)
        if lease is None:return None
        try:
            self._access();digests=self._digests()
            raw=self.jobs.read_input(self.tenant_id,lease['job_id'],lease['attempt'],lease['lease_token'])
            if raw is None:raise _LeaseLost()
            value=EconomicBatchCalculationInput.model_validate_json(raw)
            if canonical_input_bytes(value.model_dump(mode='json'))!=raw:
                raise BatchCalculationHold('economic batch input differs')
            self._guard(value,digests)
            scenario=BatchEconomicScenario.model_validate(untrusted_data(self.authority.get_economic_scenario(
                value.scenario_id,value.scenario_revision)))
            result=ProductionBatchLedger(self.authority).calculate(scenario)
            self._finish(lease,raw,value,result,digests)
            return BatchCalculationOutcome(lease['job_id'],lease['attempt'],'succeeded','completed',result.ledger.result_id)
        except _LeaseLost:return self._lost(lease)
        except (ValueError,RuntimeError,PermissionError):
            return self._close(lease,'hold','economic_batch_input_hold')
        except Exception:return self._close(lease,'transient','economic_batch_runtime_failure')

    def _finish(self,lease,raw,value,result,digests):
        self._guard(value,digests)
        encoded=result_bytes(result)
        artifact=_raw({'artifact_version':ARTIFACT_VERSION,'status':'completed',
            'claim_scope':'conditional_user_assumptions_only','tenant_id':self.tenant_id,
            'job_id':str(lease['job_id']),'attempt':lease['attempt'],'input_sha256':sha256(raw).hexdigest(),
            'input':value.model_dump(mode='json'),'code_sha256':digests[0],'environment_sha256':digests[1],
            'result_sha256':sha256(encoded).hexdigest(),'result':json.loads(encoded)})
        if not 1<=len(artifact)<=MAX_ARTIFACT_BYTES:
            raise BatchCalculationHold('bounded complete economic batch result required')
        digest=sha256(artifact).hexdigest()
        self.jobs._durable_artifact(artifact,digest)
        with self.jobs.connect()as conn:
            job=self.jobs._locked_job(conn,self.tenant_id,lease['job_id'])
            if(not self.jobs._owns_live_lease(job,lease['attempt'],lease['lease_token'])or
                    job['cancel_requested']or job['stage']!='simulation'):
                raise _LeaseLost()
            if self.jobs._verified_input(job)!=raw:
                raise BatchCalculationHold('economic batch immutable input changed')
            deadline=job['lease_until']
            self._guard(value,digests)
            updated=conn.execute(sql.SQL("""
                UPDATE {} SET state='succeeded',reason=NULL,lease_token=NULL,lease_until=NULL,
                    updated_at=clock_timestamp()
                WHERE tenant_id=%s AND job_id=%s AND stage='simulation'AND state='simulating'
                    AND attempt_count=%s AND lease_token=%s AND lease_until>clock_timestamp()
                    AND NOT cancel_requested
            """).format(self.jobs._table('jobs')),
                (self.tenant_id,lease['job_id'],lease['attempt'],lease['lease_token']))
            if updated.rowcount!=1:raise _LeaseLost()
            manifest={'schema_version':'1','job_id':str(lease['job_id']),'stage':'simulation',
                'input_sha256':job['input_sha256'],'attempt':lease['attempt'],'artifact_sha256':digest}
            self.jobs._insert_publication(conn,self.tenant_id,lease['job_id'],lease['attempt'],None,
                digest,len(artifact),manifest)
            self.jobs._event(conn,self.tenant_id,lease['job_id'],'succeeded',lease['attempt'])
            self.jobs._outcome(conn,self.tenant_id,lease['job_id'],lease['attempt'],'succeeded',
                termination_reason='completed')
            self._guard(value,digests)
            terminal=self.jobs._locked_job(conn,self.tenant_id,lease['job_id'])
            publication=conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s').format(
                self.jobs._table('job_publications')),(self.tenant_id,lease['job_id'])).fetchone()
            if(terminal['state']!='succeeded'or terminal['cancel_requested']or
                    terminal['attempt_count']!=lease['attempt']or terminal['lease_token']is not None or
                    terminal['lease_until']is not None or self.jobs._verified_input(terminal)!=raw or
                    publication is None or publication['attempt']!=lease['attempt']or
                    publication['decision_id']is not None or publication['artifact_sha256']!=digest or
                    publication['artifact_size']!=len(artifact)or publication['manifest']!=manifest):
                raise BatchCalculationHold('economic batch publication differs')
            if conn.execute('SELECT clock_timestamp()AS now').fetchone()['now']>=deadline:
                raise _LeaseLost()
