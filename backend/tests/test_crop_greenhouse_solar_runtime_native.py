"""Real solar operator assembly in a process after its owned producer exits."""
import ast
import json

import test_api_crop_greenhouse_solar_native as base


ASSEMBLE = r'''
from dataclasses import asdict,replace
from types import SimpleNamespace
from app import crop_greenhouse_solar_operator_config as loader
from app.api_runtime import ApiRuntime,ApiRuntimeConfig,ApiRuntimeDependencies
from app.crop_cycle_farm_binding import CycleFarmBinding
from app.crop_cycle_server_custody import CycleServerCustody
from app.crop_cycle_result_store import CycleCropResultStore
from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters

profiles_root=Path(p['root']);legacy_root=root/'legacy-custody';legacy_root.mkdir(mode=0o700)
profiles={
 'growth_profile':ReferenceParameters((profiles_root/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()),
 'cohort_profile':ReferenceFruitCohortParameters((profiles_root/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
 'transport_profile':ReferenceFruitTransportParameters((profiles_root/'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes())}
notice=(profiles_root/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()
class UnusedLegacy:
 version='owned-solar-runtime-unused-cycle-v1'
 policy_version=version
 def __call__(self,*a,**kw):raise AssertionError('solar runtime resolved legacy input')
def legacy_factory(*,farm_authoring_service):
 binding=CycleFarmBinding(farm_authoring_service,**profiles,notice_raw=notice,input_rights=UnusedLegacy())
 server=CycleServerCustody(binding,legacy_root,input_resolver=UnusedLegacy(),
  integrity_key=b'owned-solar-runtime-legacy-custody-key-'+b'c'*32)
 return CycleCropResultStore(server,integrity_key=b'owned-solar-runtime-legacy-result-key-'+b'r'*32)
options={'server_key':custody.integrity_key,'db_key':result.integrity_key}
seed=result;original_query=query
def solar_factory(*,farm_authoring_service):
 binding=model.SolarFarmBinding(farm_authoring_service,authority,input_rights=rights)
 server=custody_model.SolarServerCustody(binding,Path(p['custody']),input_resolver=resolver,
  integrity_key=options['server_key'])
 return result_model.SolarResultStore(server,integrity_key=options['db_key'])
def source_factory(*,principal_provider):
 return MarketSourceStore(dsn,schema,principal_provider=principal_provider,runtime_identity=identity)
grant=BearerGrant(token_digest(TOKEN),'tenant-1',frozenset(READ_SCOPES),NOW,NOW+timedelta(hours=1))
cfg=ApiRuntimeConfig(policy=policy,dsn=dsn,artifact_root=jobs.artifact_root,certificate=cert,
 private_key=private,thermal_gate_key=b'synthetic-gate-key-32-bytes-long!',market_hold_key=HOLD_KEY,port=0)
deps=ApiRuntimeDependencies(research_registry=registry,bearer_registry=BearerRegistry((grant,),clock=lambda:clock['now']),
 context_verifier=context_verifier,release_verifier=lambda *_:None,market_scope_resolver=lambda *_:dict(p['scope']),
 market_source_factory=source_factory,owned_fixture_registry=owned.registry,owned_research_contexts=dict(owned._contexts),
 crop_cycle_result_store_factory=legacy_factory,crop_greenhouse_solar_result_store_factory=solar_factory,
 crop_greenhouse_solar_current_query_factory=lambda *,result_store:current_model.SolarCurrentQuery(result_store))
operator=root/'operator';operator.mkdir(mode=0o700)
def private_file(name,raw):
 path=operator/name;path.write_bytes(raw);path.chmod(0o600);return str(path)
document={'config_version':loader.VERSION,'policy':asdict(policy),
 'dsn_file':private_file('authority.dsn',dsn.encode()),'artifact_root':str(jobs.artifact_root),
 'certificate':str(cert),'private_key':str(private),
 'thermal_gate_key_file':private_file('thermal.key',cfg.thermal_gate_key),
 'market_hold_key_file':private_file('hold.key',cfg.market_hold_key),
 'authored_run_gate_key_file':None,'content_access':None,'host':'127.0.0.1','port':0,
 'dependencies_factory':'owned_solar_operator:dependencies'}
config_path=Path(private_file('operator.json',json.dumps(document).encode()))
factory_calls=[]
def trusted_factory(*,config):
 assert config==cfg;factory_calls.append(1);return deps
sys.modules['owned_solar_operator']=SimpleNamespace(dependencies=trusted_factory)
descriptor=jobs._content_directory(create=True);os.close(descriptor)
protected_files={path:sha256(path.read_bytes()).hexdigest() for path in (config_path,cert,private,
 *(Path(document[k]) for k in ('dsn_file','thermal_gate_key_file','market_hold_key_file')))}
runtime=loader.load_solar_api_runtime(config_path)
assert type(runtime) is ApiRuntime and factory_calls==[1]
assert type(runtime.solar_crop_results) is result_model.SolarResultStore
assert type(runtime.solar_crop_query) is current_model.SolarCurrentQuery
assert runtime.solar_crop_query.store is runtime.solar_crop_results
assert runtime.solar_crop_results.jobs is runtime.jobs
assert runtime.solar_crop_results.server.binding.farms is runtime.farm_authoring
assert runtime.jobs.principal_provider is current_principal
assert runtime.ventilation_crop_results is runtime.joint_crop_results is None
assert len({runtime.solar_crop_results.integrity_key,runtime.solar_crop_results.server.integrity_key,
 runtime.solar_crop_results.server.binding.input_authority.integrity_key})==3
app=runtime.service.app.app;protected=runtime.service.app
jobs=runtime.jobs;result=runtime.solar_crop_results;query=runtime.solar_crop_query
service=result.server.binding;replay=runtime.farm_scenarios;custody=result.server
mode['preparing']=False
with jobs.connect() as conn:
 assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
assert inventory()==initial

misassemblies=[];owner_grant_mutations=0
if status=='completed':
 import gc,ctypes
 def deny(candidate):
  try:ApiRuntime(cfg,candidate)
  except ValueError as error:assert str(error)=='API runtime assembly rejected'
  else:raise AssertionError('invalid solar runtime assembled')
  gc.collect();ctypes.CDLL(None).malloc_trim(0)
 for name,changes in (
  ('wrong-store',{'crop_greenhouse_solar_result_store_factory':lambda **_:object()}),
  ('foreign-store',{'crop_greenhouse_solar_result_store_factory':lambda **_:seed}),
  ('wrong-query',{'crop_greenhouse_solar_current_query_factory':lambda **_:object()}),
  ('foreign-query',{'crop_greenhouse_solar_current_query_factory':lambda **_:original_query})):
  deny(replace(deps,**changes));misassemblies.append(name)
 for key in ('server_key','db_key'):
  previous=options[key];options[key]=authority.integrity_key
  try:deny(deps);misassemblies.append(key+'-reused-input-key')
  finally:options[key]=previous
 previous=options['db_key'];options['db_key']=options['server_key']
 try:deny(deps);misassemblies.append('reused-server-db-key')
 finally:options['db_key']=previous
 previous=current_model.CODE_SHA256;current_model.CODE_SHA256='0'*64
 try:deny(deps);misassemblies.append('current-code-pin')
 finally:current_model.CODE_SHA256=previous
 cluster=json.loads((root/'cluster.private.json').read_bytes())
 def owned_grant(verb):
  global owner_grant_mutations
  with psycopg.connect(cluster['database']['admin']) as conn:
   execute(conn,sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
   execute(conn,sql.SQL(verb+' SELECT ON {} '+('TO' if verb=='GRANT' else 'FROM')+' {}').format(
    sql.Identifier(policy.schema,result_model.schema.TABLE),sql.Identifier(policy.roles['authority'])))
  owner_grant_mutations+=1
 owned_grant('REVOKE')
 try:deny(deps);misassemblies.append('actual-revoked-select-grant')
 finally:owned_grant('GRANT')
assert inventory()==initial
assert {path:sha256(path.read_bytes()).hexdigest() for path in protected_files}==protected_files
assert list(legacy_root.iterdir())==[]
server=runtime.service.server()
'''


def native_script():
    script = base.HTTP_READ
    start = script.index('app=api.create_app(')
    end = script.index('\nTOKEN=', start)
    script = script[:start]+'app=None'+script[end:]
    script = script.replace("protected=protect();mode['preparing']=False", 'received_wires=[]')
    script = script.replace('def get(target=protected,', 'def get(target=None,')
    script = script.replace(' sent=[]\n async def receive():', ' target=protected if target is None else target\n sent=[]\n async def receive():')
    script = script.replace(" return first['status'],json.loads(wire)", " received_wires.append(wire)\n return first['status'],json.loads(wire)")
    target = 'server=HttpsApiService(protected,cert,private,port=0).server();baseline=inventory()'
    assert script.count(target) == 1
    script = script.replace(target, ASSEMBLE+'\nbaseline=inventory()')
    target = "assert closed.is_set() and query.read('tenant-1',result_id,farm)==wires[1]"
    assert script.count(target) == 1
    script = script.replace(target, "assert closed.is_set() and get()[0]==200 and received_wires[-1]==wires[1]")
    script = script.replace("'PID':os.getpid(),'status':status", "'PID':os.getpid(),'runtime_assembled':True,'misassemblies_denied':misassemblies,'test_owner_grant_mutations':owner_grant_mutations,'protected_files_preserved':True,'legacy_custody_unused':True,'status':status")
    ast.parse(script)
    return script


def exercise(tmp_path, case):
    previous = base.HTTP_READ
    try:
        base.HTTP_READ = native_script()
        base.exercise(tmp_path, case)
    finally:
        base.HTTP_READ = previous
    proof = json.loads((tmp_path/'prepared.private.json').read_bytes())
    assert proof['PID'] > 0


def test_owned_runtime_completed_tls_current_rights_and_misassembly(tmp_path):
    exercise(tmp_path, None)


def test_owned_runtime_hold_original_tls_wires(tmp_path):
    exercise(tmp_path, 'hold')
