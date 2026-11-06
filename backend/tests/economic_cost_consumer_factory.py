"""Test-only cost operator factory; the parent removes its private configuration."""
import json
import os
from pathlib import Path
import stat

from app.deterministic_work import DeterministicWorkerLoop
from app.economic_batch_calculation import EconomicBatchAuthority,READ_SCOPES
from app.economic_batch_source_store import EconomicBatchSourceStore
from app.economic_cost_worker import EconomicCostWorker
from app import economic_cost_trace as trace
from app.economic_production_batches import ProductionBatchLedger
from app.job_store import JobStore
from app.market_hold_store import MarketHoldStore
from app.runtime_roles import RuntimeLoginPolicy
from app.thermal_run_store import ThermalRunStore
from test_market_hold_store import context_verifier


def build():
    path=Path(os.environ['OSSF_COST_CONSUMER_TEST_CONFIG'])
    metadata=path.stat();assert metadata.st_uid==os.getuid()and stat.S_IMODE(metadata.st_mode)==0o600
    data=json.loads(path.read_bytes());root=path.parent;policy=RuntimeLoginPolicy(**data['policy'])
    principal={'authenticated':True,'tenant_id':'tenant-1',
        'scopes':frozenset(READ_SCOPES+('artifact','simulation_execute'))}
    kwargs={'runtime_identity':(policy,'authority'),'principal_provider':lambda:principal}
    jobs=JobStore(data['dsn'],policy.schema,Path(data['artifact_root']),audit_runtime_grants=True,**kwargs)
    source=EconomicBatchSourceStore(data['dsn'],policy.schema,**kwargs)
    contexts=ThermalRunStore(data['dsn'],policy.schema,gate_key=bytes.fromhex(data['gate_key']),
        release_verifier=lambda *_:None,context_verifier=context_verifier,**kwargs)
    holds=MarketHoldStore(data['dsn'],policy.schema,context_store=contexts,
        scope_resolver=lambda *_:dict(data['hold_scope']),signing_key=bytes.fromhex(data['hold_key']),**kwargs)
    loop=DeterministicWorkerLoop(EconomicCostWorker(EconomicBatchAuthority(jobs,source,holds),tenant_id='tenant-1'),
        input_versions=frozenset({'economic-cost-line-calculation-input-v1'}),page_size=2)
    def append(name,value):
        fd=os.open(root/name,os.O_WRONLY|os.O_APPEND|os.O_CREAT,0o600)
        with os.fdopen(fd,'w')as handle:handle.write(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n')
    calculate=trace.CostLineLedger.calculate;calculate_base=ProductionBatchLedger.calculate
    def counted(*a,**k):append('trace-calls.private.jsonl',{'actual_trace_entry':True});return calculate(*a,**k)
    def counted_base(*a,**k):append('v10-calls.private.jsonl',{'actual_v10_entry':True});return calculate_base(*a,**k)
    trace.CostLineLedger.calculate=counted;ProductionBatchLedger.calculate=counted_base
    page=loop.discovery.page
    def observed(**kwargs):
        result=page(**kwargs)
        append('discovery-pages.private.jsonl',{'cursor_is_none':kwargs.get('cursor')is None,
            'scanned_count':result.scanned_count,'job_ids':[job.job_id for job in result.jobs],
            'has_next_cursor':result.next_cursor is not None})
        return result
    loop.discovery.page=observed
    return loop
