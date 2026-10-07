"""Generated legacy operator files; isolated assembly is not a Compose/UID proof."""
from dataclasses import asdict,replace
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
from types import SimpleNamespace

import pytest

from app.operator_config import load_api_runtime,OperatorConfigHold
from test_operator_config import private_config,store
from test_api_runtime import policy,dependencies

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture
def generator(monkeypatch,tmp_path):
    spec=importlib.util.spec_from_file_location('application_policy_generator',ROOT/'scripts/check-application-runtime.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    commands=[]
    monkeypatch.setattr(module,'command',lambda *args,**kwargs:commands.append(args))
    def owned_web_files(path,uid,files):
        path.mkdir(mode=0o700)
        for source,name in files:module.private(path/name,source.read_bytes())
    monkeypatch.setitem(module.IMAGE_TOOLS,'private_directory',owned_web_files)
    try:yield module,commands
    finally:shutil.rmtree(tmp_path)


def generate(module,root,selected):
    certs=root/'certificates';certs.mkdir(mode=0o700)
    for name in ('api.pem','api.key','ca.pem','web.pem','web.key'):
        module.private(certs/name,b'synthetic-owned-certificate-or-key')
    passfile=root/'source.pgpass';module.private(passfile,'db:5432:project_database:project_role_authority:synthetic-owned-password\n')
    dsns={'authority':f'dbname=project_database user=project_role_authority passfile={passfile}'}
    worker=SimpleNamespace(results=SimpleNamespace(_candidates=SimpleNamespace(_source=SimpleNamespace(
        _holds=SimpleNamespace(_scope_resolver=lambda:{'schema_version':'owned-software-scope'})))))
    module.operator_files(root,selected,dsns,worker,{'scopes':frozenset({'metadata'})},certs,'synthetic-owned-bearer')
    path=root/'api/operator.json';doc=json.loads(path.read_text())
    for key in ('dsn_file','certificate','private_key','thermal_gate_key_file','market_hold_key_file'):
        doc[key]=str(root/doc[key].removeprefix('/run/operator/'))
    doc['artifact_root']=str(root/'artifacts');store(path,doc)
    return path,doc


@pytest.mark.parametrize('options',[{}, {'crop_result_storage':True},
    {'market_source_storage':True,'thermal_scenario_storage':True,'authored_release_storage':True,
     'authored_run_storage':True,'crop_coupled_result_storage':True,'crop_startup_result_storage':True,'crop_cycle_result_storage':True}])
def test_generated_legacy_operator_policy_loads_and_preserves_existing_options(tmp_path,generator,monkeypatch,options):
    module,commands=generator;selected=replace(policy(),**options);before=asdict(selected)
    fd_before=len(os.listdir('/proc/self/fd'));path,doc=generate(module,tmp_path,selected)
    calls=[]
    def factory(*,config):
        calls.append(config);return dependencies()
    def factory_module(name):
        assert name=='synthetic_operator'
        return SimpleNamespace(dependencies_factory=factory)
    monkeypatch.setattr('app.operator_config.ApiRuntime',lambda config,deps:('assembled',config,deps))
    monkeypatch.setattr('app.operator_config.importlib.import_module',factory_module)
    loaded=load_api_runtime(path)
    expected=asdict(selected);assert expected.pop('crop_cycle_calculation_result_storage') is False
    assert doc['policy']==expected and asdict(calls[0].policy)==before and loaded[0]=='assembled'
    assert json.loads((tmp_path/'simulation/fixture.json').read_text())['policy']==before
    assert asdict(selected)==before and len(commands)==2
    assert all(args[:3]==('sudo','chown','-R') for args in commands)
    assert stat.S_IMODE(path.stat().st_mode)==0o600 and stat.S_IMODE(path.parent.stat().st_mode)==0o700
    assert len(os.listdir('/proc/self/fd'))==fd_before


def test_unsupported_active_calculation_flag_is_refused_before_writes_or_chown(tmp_path,generator):
    module,commands=generator;selected=replace(policy(),crop_cycle_calculation_result_storage=True)
    def forbidden(*args,**kwargs):pytest.fail('unsupported active policy wrote private files')
    module.private=forbidden
    with pytest.raises(ValueError,match='^unsupported_legacy_api_policy$'):
        module.operator_files(tmp_path,selected,{},None,{'scopes':frozenset()},None,'synthetic-owned-bearer')
    assert not list(tmp_path.iterdir()) and commands==[] and selected.crop_cycle_calculation_result_storage is True


@pytest.mark.parametrize('value',[False,True,0,1,'false',None])
def test_original_closed_loader_still_refuses_the_new_field_before_factory(private_config,monkeypatch,value):
    path,doc=private_config;doc['policy']['crop_cycle_calculation_result_storage']=value;store(path,doc)
    monkeypatch.setattr('app.operator_config.importlib.import_module',
        lambda *_:pytest.fail('unsupported legacy policy imported a dependency'))
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(OperatorConfigHold,match='^operator_config_rejected$'):load_api_runtime(path)
    assert len(os.listdir('/proc/self/fd'))==before
