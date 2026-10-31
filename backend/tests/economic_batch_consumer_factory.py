"""Test-only operator factory. Its private config is removed by the parent test."""
from hashlib import sha256
import json
import os
from pathlib import Path

from app.deterministic_work import DeterministicWorkerLoop
from app.economic_batch_calculation import EconomicBatchAuthority,READ_SCOPES
from app.economic_batch_source_store import EconomicBatchSourceStore
from app.economic_batch_worker import EconomicBatchWorker
from app.economic_production_batches import ProductionBatchLedger
from app.job_store import JobStore
from app.market_hold_store import MarketHoldStore
from app.runtime_roles import RuntimeLoginPolicy
from app.thermal_run_store import ThermalRunStore
from test_market_hold_store import context_verifier


def build():
    path=Path(os.environ['OSSF_BATCH_CONSUMER_TEST_CONFIG']);data=json.loads(path.read_bytes());root=path.parent
    policy=RuntimeLoginPolicy(**data['policy'])
    principal={'authenticated':True,'tenant_id':'tenant-1',
        'scopes':frozenset(READ_SCOPES+('artifact','simulation_execute'))}
    provider=lambda:principal;kwargs={'runtime_identity':(policy,'authority'),'principal_provider':provider}
    jobs=JobStore(data['dsn'],policy.schema,Path(data['artifact_root']),audit_runtime_grants=True,**kwargs)
    source=EconomicBatchSourceStore(data['dsn'],policy.schema,**kwargs)
    contexts=ThermalRunStore(data['dsn'],policy.schema,gate_key=bytes.fromhex(data['gate_key']),
        release_verifier=lambda *_:None,context_verifier=context_verifier,**kwargs)
    holds=MarketHoldStore(data['dsn'],policy.schema,context_store=contexts,
        scope_resolver=lambda *_:dict(data['hold_scope']),signing_key=bytes.fromhex(data['hold_key']),**kwargs)
    authority=EconomicBatchAuthority(jobs,source,holds)
    worker=EconomicBatchWorker(authority,tenant_id='tenant-1')
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({'economic-batch-calculation-input-v1'}),page_size=2)
    def append(name,value):
        with(root/name).open('a')as f:f.write(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n')
    calculate=ProductionBatchLedger.calculate
    def counted(*a,**k):
        append('calculation-calls.private.jsonl',{'actual_v10_entry':True});return calculate(*a,**k)
    ProductionBatchLedger.calculate=counted
    page=loop.discovery.page
    def observed(**kwargs):
        result=page(**kwargs)
        append('discovery-pages.private.jsonl',{'cursor_is_none':kwargs.get('cursor')is None,
            'scanned_count':result.scanned_count,'job_ids':[job.job_id for job in result.jobs],
            'has_next_cursor':result.next_cursor is not None})
        return result
    loop.discovery.page=observed
    return loop
