"""Independent owned-test reader; credentials stay in the private input file."""
import json
from pathlib import Path
import sys
from hashlib import sha256

sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).parent)]
from psycopg import Connection
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy
from app.economic_batch_source_store import EconomicBatchSourceStore
from app.economic_batch_calculation import EconomicBatchAuthority
from app.economic_batch_query import EconomicBatchResultQuery
from app.economic_production_batches import ProductionBatchLedger
from app.economics import EconomicLedger
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from test_market_hold_store import HOLD_KEY,context_verifier

doc=json.loads(Path(sys.argv[1]).read_bytes());policy=RuntimeLoginPolicy(**doc['policy'])
principal={'authenticated':True,'tenant_id':'tenant-1','scopes':['metadata','artifact',
    'economic_batch_source_read','decision_context_read','market_hold_context_read']}
provider=lambda:principal;binding=(policy,'authority')
jobs=JobStore(doc['dsn'],policy.schema,Path(doc['artifact_root']),principal_provider=provider,
    runtime_identity=binding,audit_runtime_grants=True)
source=EconomicBatchSourceStore(doc['dsn'],policy.schema,principal_provider=provider,runtime_identity=binding)
contexts=ThermalRunStore(doc['dsn'],policy.schema,gate_key=b'self-authored-gate-test-key-32bytes',
    release_verifier=lambda *_:None,context_verifier=context_verifier,
    principal_provider=provider,runtime_identity=binding)
holds=MarketHoldStore(doc['dsn'],policy.schema,context_store=contexts,
    scope_resolver=lambda *_:dict(doc['scope']),principal_provider=provider,
    signing_key=HOLD_KEY,runtime_identity=binding)
stats={'amount_calls':0,'SQL_writes':0}
def no_calculation(*a,**k):
    stats['amount_calls']+=1;raise AssertionError('arithmetic in independent reader')
ProductionBatchLedger.calculate=no_calculation
EconomicLedger.calculate=no_calculation
EconomicLedger._calculate_verified=no_calculation
execute=Connection.execute
def measured(conn,*a,**k):
    cursor=execute(conn,*a,**k)
    if(cursor.statusmessage or '').split(' ')[0]in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:stats['SQL_writes']+=1
    return cursor
Connection.execute=measured
found=EconomicBatchResultQuery(EconomicBatchAuthority(jobs,source,holds)).read('tenant-1',doc['job_id'])
assert found is not None and stats=={'amount_calls':0,'SQL_writes':0}
with Path(doc['output']).open('xb')as f:f.write(found.raw)
Path(doc['output']).chmod(0o600)
print(json.dumps({'artifact_sha256':sha256(found.raw).hexdigest(),'artifact_bytes':len(found.raw),
    'publication_id':str(found.publication_id),'published_at':found.published_at.isoformat(),**stats}))
