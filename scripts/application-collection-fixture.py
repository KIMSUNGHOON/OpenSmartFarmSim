"""Private owned-source fixtures for the hosted collection Compose proof."""

from dataclasses import asdict, replace
import json
from pathlib import Path

from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app.cli_contracts import DecisionContract
from app.cli_worker import CliWorker
from app.job_store import JobStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from test_cli_contracts import input_for, resolver
from test_cli_worker import _fake_cli
from test_job_evidence import cli_store


PLUGIN = '''import json
from pathlib import Path
from app.operator_config import _private_bytes
from app.runtime_roles import RuntimeLoginPolicy
from app.job_store import JobStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.owned_fixture_collection import CollectionService, CollectionWorker
from app.collection_consume import CollectionWorkerLoop
def worker():
    root = Path(__file__).resolve().parent.parent
    value = json.loads(_private_bytes(root/'fixture.json',maximum=65536))
    policy = RuntimeLoginPolicy(**value['policy'])
    principal = {'authenticated':True,'tenant_id':'tenant-1','scopes':frozenset(value['scopes'])}
    jobs = JobStore(_private_bytes(root/'authority.dsn',maximum=8192).decode().strip(),
        policy.schema,Path('/artifacts'),audit_runtime_grants=True,
        runtime_identity=(policy,'authority'),principal_provider=lambda:principal)
    return CollectionWorker(CollectionService(jobs,OwnedFixtureRegistry('/app')),tenant_id='tenant-1')
def build():
    return CollectionWorkerLoop(worker())
'''


def prepare(root, scope, principal, *, private, command):
    base, policy, dsns = scope
    registry = OwnedFixtureRegistry(Path(__file__).resolve().parents[1])
    principal['scopes'].update({'collection_execute','collection_read','auditor'})
    def approved(job, value):
        snapshot=resolver(job,value)
        return replace(snapshot,allow_proceed=True,missing_evidence=(),
            candidate_ids=frozenset({registry.provider_id}),
            evidence={name:replace(grant,tenant_id=job['tenant_id']) for name,grant in snapshot.evidence.items()})
    contract = DecisionContract(approved)
    jobs = JobStore(dsns['authority'],policy.schema,base.artifact_root,
        decision_validator=contract,evidence_policy=cli_store(base).evidence_policy,
        runtime_identity=(policy,'authority'),audit_runtime_grants=True,principal_provider=lambda:principal)
    seed = root/'synthetic-parent'
    seed.mkdir(mode=0o700)
    program = _fake_cli(seed)
    program.write_text(program.read_text().replace('candidate-a',registry.provider_id))
    home = seed/'home'; home.mkdir(mode=0o700)
    worker = CliWorker(jobs,contract,cli_path=program,codex_home=home,
        child_env={'CODEX_API_KEY':'synthetic-test-key'},timeout_seconds=10,
        lease_seconds=30,synthetic_smoke=True)
    value = input_for('research') | {'tenant_id':'tenant-1',
        'candidate_ids':[registry.provider_id],'provider_ids':[registry.provider_id],
        'period_start_utc':'2026-10-15T08:00:00Z','period_end_utc':'2026-10-15T10:00:00Z',
        'decision_context_id':'decision-context-v1:'+'c'*64,'decision_at_utc':'2026-09-28T00:00:00Z',
        'claim_mode':'ex_ante','decision_time_kind':'hypothetical'}
    parent = jobs.submit('tenant-1','research',value,'compose-synthetic-parent')
    result = worker.run_once()
    assert result.job_id==parent['job_id'] and result.state=='succeeded' and result.decision_id, result
    directory = root/'collection'; directory.mkdir(mode=0o700)
    plugins = directory/'plugins'; plugins.mkdir(mode=0o700)
    private(plugins/'synthetic_collection.py',PLUGIN)
    private(directory/'fixture.json',json.dumps({'policy':asdict(policy), 'scopes':sorted(principal['scopes'])}))
    authority = conninfo_to_dict(dsns['authority'])
    password = Path(authority['passfile']).read_text().strip().rsplit(':',1)[1]
    private(directory/'authority.pgpass',f'db:5432:{policy.database}:{policy.roles["authority"]}:{password}\n')
    private(directory/'authority.dsn',make_conninfo(host='db',port=5432,dbname=policy.database,
        user=policy.roles['authority'],passfile='/run/operator/collection/authority.pgpass',sslmode='disable'))
    command('sudo','chown','-R','11001:11010',str(directory))
    return {'research_job_id':str(parent['job_id']),'idempotency_key':'compose-ingestion'}


def inspect_record(compose, job_id, *, command):
    source = '''import json,sys
from hashlib import sha256
from synthetic_collection import worker
value=worker().service.read_record('tenant-1',sys.argv[1])
from app.owned_fixture_registry import collection_record_bytes
print(json.dumps({'assessment':value['assessment_status'],'g0':value['g0_status'],
    'g1':value['g1_status'],'scope':value['claim_scope'],'source_count':len(value['sources']),
    'record_sha256':sha256(collection_record_bytes(value)).hexdigest()}))
'''
    result = json.loads(command(*compose,'exec','-T','collector','python','-c',source,job_id).stdout)
    assert result | {'record_sha256':None} == {'assessment':'hold','g0':'not_accepted',
        'g1':'not_accepted','scope':'software_fixture_only','source_count':3,'record_sha256':None}
    assert len(result['record_sha256'])==64
    return result


def withdraw_parent(compose, parent_id, *, command):
    source = '''import os,sys
from synthetic_collection import worker
jobs=worker().service.jobs
decision=jobs.list_decisions('tenant-1',sys.argv[1])[0]
directory=jobs._content_directory('tenant-1')
try:
    fd=os.open(decision['output_sha256'],os.O_WRONLY|os.O_TRUNC|os.O_NOFOLLOW,dir_fd=directory)
    with os.fdopen(fd,'wb') as stream: stream.write(b'private synthetic revoked parent proof')
finally:
    os.close(directory)
'''
    command(*compose,'exec','-T','collector','python','-c',source,parent_id)
