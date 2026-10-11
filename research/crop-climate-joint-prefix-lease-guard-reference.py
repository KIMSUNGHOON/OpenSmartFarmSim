from pathlib import Path
import hashlib,json,os,subprocess,sys,threading
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend/tests'))
import pytest
from pytest import MonkeyPatch
import psycopg
import login_database as database_reference
import test_crop_climate_joint_prefix_runtime as reference
pytest_plugins=['test_crop_climate_joint_prefix_runtime']

@pytest.fixture(scope='module')
def login_database():
    real=subprocess.run;startup=[]
    binary=str(Path(os.environ['OSSF_TEST_PG_BIN'])/'pg_ctl')
    def small_cluster(args,*a,**kw):
        if isinstance(args,list) and args[0]==binary and 'start' in args:
            args=list(args);i=args.index('-o')+1
            directory=Path(args[args.index('-D')+1]);assert directory.name=='data' and directory.parent.name.startswith('ossf-login-pg-')
            args[i]+=' -c shared_buffers=16MB -c max_connections=32 -c work_mem=1MB -c maintenance_work_mem=16MB'
            startup.append(True)
        return real(args,*a,**kw)
    with MonkeyPatch.context() as patch:
        patch.setattr(subprocess,'run',small_cluster)
        generator=database_reference.login_database.__wrapped__()
        value=next(generator)
        try:
            with psycopg.connect(value['admin']) as conn:
                settings={key:conn.execute('SHOW '+key).fetchone()[0] for key in ('server_version','shared_buffers','max_connections','work_mem','maintenance_work_mem')}
            assert len(startup)==1 and settings['shared_buffers']=='16MB' and settings['max_connections']=='32'
            reference.save('isolated-PG-settings',{'settings':settings,'production_or_user_PG_modified':False,'storage_auth_schema_unchanged':True})
            yield value
        finally:
            try:next(generator)
            except StopIteration:pass

@reference.LOGIN
def test_traced_unpaused_normal(prefix_native,tmp_path,monkeypatch):
    trace=[];previous=threading.gettrace()
    def observe(frame,event,arg):
        if '/backend/app/' not in frame.f_code.co_filename:return None
        frame.f_trace_lines=False
        if event=='exception' and len(trace)<2000:
            kind,error,_=arg
            if kind.__name__ not in ('StopIteration','StopAsyncIteration','GeneratorExit'):
                value={'module':Path(frame.f_code.co_filename).name,'function':frame.f_code.co_name,'line':frame.f_lineno,'exception':kind.__name__}
                if kind.__name__=='ValidationError':
                    try:value['validation_fields']=[{'type':e['type'],'loc':e['loc']} for e in error.errors(include_url=False,include_context=False,include_input=False)]
                    except Exception:pass
                trace.append(value)
        return observe
    threading.settrace(observe)
    try:
        reference.test_actual_unpaused_worker_prefix_to_original_terminal(prefix_native,tmp_path,monkeypatch,'completed')
    finally:
        threading.settrace(previous)
        reference.save('actual-422-trace',{'exceptions':trace,'API_thread_only':True,'worker_traced':False,'test_pause':False,'private_reference_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})

@reference.LOGIN
@pytest.mark.parametrize('setup',['hold'],indirect=True)
def test_unpaused_hold_small_cluster(prefix_native,tmp_path,monkeypatch):
    reference.test_actual_unpaused_worker_prefix_to_original_terminal(prefix_native,tmp_path,monkeypatch,'hold')

@reference.LOGIN
def test_unpaused_cancel_small_cluster(prefix_native,tmp_path,monkeypatch):
    reference.test_actual_unpaused_cancel_closes_prefix(prefix_native,tmp_path,monkeypatch)
