"""Private fake CLI and scoped registry-hold factories for real Compose RPC."""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from app.owned_fixture_collection import COLLECTION_SCOPES

from test_api_location_research import BODY
from test_cli_worker import _fake_cli
from test_research_registry import document


PLUGIN = '''import json
from hashlib import sha256
from pathlib import Path
from app.operator_config import _private_bytes
from app.authority_rpc import AuthorityServer
from app.cli_contracts import DecisionContract, _canonical
from app.cli_supervisor_client import SupervisorClient
from app.cli_supervisor_service import SupervisorServer
from app.cli_worker import CliWorker
from app.content_access import ContentAccess
from app.execution_attestation import ExecutionAttestationStore
from app.job_store import JobStore
from app.research_registry import ResearchRegistry
from app.runtime_roles import RuntimeLoginPolicy
def data():
    root=Path(__file__).resolve().parent.parent
    return json.loads(_private_bytes(root/'fixture.json',maximum=65536)),root
def store(value,root,kind):
    raw=_canonical(value['research_registry'])
    contract=DecisionContract(ResearchRegistry(raw,sha256(raw).hexdigest()).authority_snapshot)
    def evidence(tenant,source,use,kind,payload,digest):
        return dict(tenant_id=tenant,source_id='synthetic_cli_test',intended_use=use,
            payload_sha256=digest,rights_proof_id='synthetic_cli_test',rights_version='fixture-v1',
            policy_version='fixture-v1',classification='private',read_scope='auditor',
            retain_raw=True,retain_digest=True)
    principal={'authenticated':True,'tenant_id':'tenant-1','scopes':{'metadata','artifact','auditor'}}
    policy=RuntimeLoginPolicy(**value['policy'])
    jobs=JobStore(_private_bytes(root/(kind+'.dsn'),maximum=8192).decode().strip(),
        policy.schema,Path('/artifacts'),decision_validator=contract,evidence_policy=evidence,
        principal_provider=lambda:principal,runtime_identity=(policy,kind),audit_runtime_grants=True,
        content_access=ContentAccess(owner_uid=11001,reader_gid=11010))
    return jobs,contract,policy
def supervisor():
    value,root=data();jobs,_,_=store(value,root,'supervisor')
    return SupervisorServer(jobs,socket_path='/run/ipc/supervisor/supervisor.sock',worker_uid=11001,
        tenant_id='tenant-1',key_file=root/'private.key',key_id=value['key_id'],
        cli_path=root/'fake-codex',codex_home=root/'home',
        executable_sha256=value['executable_sha256'],environment_sha256=value['environment_sha256'],
        child_env={'CODEX_API_KEY':'synthetic-test-key'},timeout_seconds=10)
def authority():
    value,root=data();jobs,contract,policy=store(value,root,'authority')
    client=SupervisorClient('/run/ipc/supervisor/supervisor.sock',supervisor_uid=11003,tenant_id='tenant-1',
        executable_sha256=value['executable_sha256'],environment_sha256=value['environment_sha256'])
    observed=ExecutionAttestationStore(jobs,{value['key_id']:bytes.fromhex(value['public_key'])})
    worker=CliWorker(jobs,contract,supervisor_client=client,attestation_store=observed,
        timeout_seconds=10,lease_seconds=30,synthetic_smoke=True)
    return AuthorityServer(worker,socket_path='/run/ipc/authority/authority.sock',worker_uid=11004,
        tenant_id='tenant-1',role_policy=policy)
'''


def prepare(root,scope,principal,*,private,command):
    _,policy,dsns=scope
    principal['scopes'].update({'location_create','auditor'})
    principal['scopes'].update(COLLECTION_SCOPES)
    catalog=document();catalog['registrations'][0]['tenant_id']='tenant-1'
    key=Ed25519PrivateKey.generate()
    supervisor=root/'supervisor';supervisor.mkdir(mode=0o700)
    fake=_fake_cli(supervisor,mode='valid_slow')
    text=fake.read_text().replace('#!/usr/bin/env python3','#!/app/.venv/bin/python')
    text=text.replace(str(supervisor/'actual-prompt.sha256'),'/tmp/actual-prompt.sha256')
    text=text.replace(str(supervisor/'actual-schema.sha256'),'/tmp/actual-schema.sha256')
    private(supervisor/'fake-codex',text);(supervisor/'fake-codex').chmod(0o700)
    fake.unlink()
    (supervisor/'home').mkdir(mode=0o700)
    private(supervisor/'private.key',key.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption()))
    settings={'policy':asdict(policy),'research_registry':catalog,'key_id':'synthetic-compose-key',
        'public_key':key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex(),
        'executable_sha256':sha256(text.encode()).hexdigest(),
        'environment_sha256':sha256((Path(__file__).resolve().parents[1]/'backend/uv.lock').read_bytes()).hexdigest()}
    for service,uid,gid in (('supervisor',11003,11020),('authority',11001,11010)):
        directory=root/service
        if service=='authority': directory.mkdir(mode=0o700)
        plugins=directory/'plugins';plugins.mkdir(mode=0o700)
        private(plugins/'synthetic_authority.py',PLUGIN)
        private(directory/'fixture.json',json.dumps(settings))
        config=conninfo_to_dict(dsns[service])
        password=Path(config['passfile']).read_text().strip().rsplit(':',1)[1]
        private(directory/(service+'.pgpass'),f'db:5432:{policy.database}:{policy.roles[service]}:{password}\n')
        private(directory/(service+'.dsn'),make_conninfo(host='db',port=5432,dbname=policy.database,
            user=policy.roles[service],passfile=f'/run/operator/{service}/{service}.pgpass',sslmode='disable'))
        command('sudo','chown','-R',f'{uid}:{gid}',str(directory))
    for service,uid,gid in (('supervisor',11003,11020),('authority',11001,11030)):
        directory=root/(service+'-socket');directory.mkdir(mode=0o750)
        command('sudo','chown',f'{uid}:{gid}',str(directory))
        command('sudo','chmod','2750',str(directory))
    return BODY | {'idempotency_key':'compose-authority-research'}


def share_artifacts(root,*,command):
    command('sudo','chown','-R','11001:11010',str(root/'artifacts'))
    script='''from pathlib import Path
import sys
root=Path(sys.argv[1]);root.chmod(0o750)
for path in root.rglob('*'):
    assert not path.is_symlink()
    path.chmod(0o750 if path.is_dir() else 0o640)
'''
    command('sudo','python3','-c',script,str(root/'artifacts'))


def assert_persisted(job_id,*,command,compose):
    source='''import json,sys
from synthetic_authority import data,store
from psycopg import sql
value,root=data();jobs,_,_=store(value,root,'authority')
from uuid import UUID
identity=UUID(sys.argv[1]);decisions=jobs.list_decisions('tenant-1',identity)
assert len(decisions)==1
with jobs.connect() as conn:
    decision=conn.execute(sql.SQL('SELECT disposition,capture_id,decision_id FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=1').format(
        jobs._table('ai_decisions')),('tenant-1',identity)).fetchone()
    captures=conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE tenant_id=%s AND job_id=%s').format(
        jobs._table('attempt_cli_captures')),('tenant-1',identity)).fetchone()['n']
    observed=conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE tenant_id=%s AND job_id=%s').format(
        jobs._table('execution_attestations')),('tenant-1',identity)).fetchone()['n']
    invocation=conn.execute(sql.SQL('SELECT model,reasoning_effort FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=1').format(
        jobs._table('attempt_invocations')),('tenant-1',identity)).fetchone()
assert decision is not None and decision['disposition']=='hold'
assert decision['decision_id']==decisions[0]['decision_id']
assert captures==observed==1
from app.execution_attestation import ExecutionAttestationStore
signed=ExecutionAttestationStore(jobs,{value['key_id']:bytes.fromhex(value['public_key'])}).get('tenant-1',identity,1)
assert signed is not None and signed.capture_id==decision['capture_id']
assert invocation=={'model':'gpt-6.1-sol','reasoning_effort':'xhigh'}
print(json.dumps({'decisions':1,'captures':captures,'signed_executions':observed,'scope':'software_fixture_only'}))
'''
    return json.loads(command(*compose,'exec','-T','authority','python','-c',source,job_id).stdout)


def assert_denials(compose,*,command):
    source='''import json,sys
for path in sys.argv[1:]:
    try:
        with open(path,'rb') as stream: stream.read(1)
    except PermissionError:
        continue
    raise AssertionError('private fixture access unexpectedly allowed')
print(json.dumps({'private_files':'denied'}))
'''
    for service,user,paths in (
            ('authority','11004:11030',('/run/operator/authority/authority.pgpass','/artifacts/.evidence')),
            ('supervisor','11001:11010',('/run/operator/supervisor/private.key','/run/operator/supervisor/supervisor.pgpass'))):
        result=command(*compose,'run','--rm','--no-deps','--user',user,'--entrypoint','python',
            service,'-c',source,*paths)
        assert json.loads(result.stdout)=={'private_files':'denied'}
    authority_probe='''import json
from app.authority_rpc import AuthorityClient,AuthorityDispatchError
try:
    AuthorityClient('/run/ipc/authority/authority.sock',authority_uid=11001,tenant_id='tenant-1',wait_seconds=10).run_once()
except AuthorityDispatchError:
    print(json.dumps({'authority_peer':'denied'}))
else:
    raise AssertionError('rogue authority peer admitted')
'''
    result=command(*compose,'run','--rm','--no-deps','--user','11005:11030','--entrypoint','python',
        'dispatcher','-c',authority_probe)
    assert json.loads(result.stdout)=={'authority_peer':'denied'}
    supervisor_probe='''import json,socket
from app.cli_ipc import receive,MAX_RESPONSE
with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
    connection.settimeout(5);connection.connect('/run/ipc/supervisor/supervisor.sock')
    assert receive(connection,MAX_RESPONSE)=={'ok':False,'code':'supervisor_rejected'}
print(json.dumps({'supervisor_peer':'denied'}))
'''
    result=command(*compose,'run','--rm','--no-deps','--user','11005:11020','--entrypoint','python',
        'authority','-c',supervisor_probe)
    assert json.loads(result.stdout)=={'supervisor_peer':'denied'}
