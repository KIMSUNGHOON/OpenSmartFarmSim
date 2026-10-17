"""Closed Solar execution/prefix operator configuration and pre-I/O boundaries."""
from copy import deepcopy
from dataclasses import replace
import pytest

from app import crop_greenhouse_solar_operator_config as loader
from app import calculation_operator_config as calculation
from app import crop_climate_joint_operator_config as joint
from app import crop_greenhouse_ventilation_operator_config as ventilation
from app.api_runtime import ApiRuntime
from test_crop_greenhouse_solar_runtime import (
    solar_config, private_config, store, isolated_assembly, config, dependencies, policy, original)
import test_crop_greenhouse_solar_runtime as reader


@pytest.fixture
def execution_config(solar_config):
    path, doc = solar_config
    doc.update(config_version=loader.EXECUTION_VERSION, crop_greenhouse_solar_execution=True)
    doc['policy'].update(crop_greenhouse_solar_result_storage=True, crop_cycle_result_storage=True)
    store(path, doc)
    return path, doc


@pytest.fixture
def prefix_config(execution_config):
    path, doc = execution_config
    doc.update(config_version=loader.PREFIX_VERSION, crop_greenhouse_solar_prefix=True)
    store(path, doc)
    return path, doc


@pytest.mark.parametrize('version,execution,prefix', [
    (loader.EXECUTION_VERSION,False,False), (loader.EXECUTION_VERSION,True,False),
    (loader.PREFIX_VERSION,False,False), (loader.PREFIX_VERSION,True,False), (loader.PREFIX_VERSION,True,True)])
def test_explicit_versions_preserve_exact_flags(prefix_config, monkeypatch, version, execution, prefix):
    path, doc = prefix_config; doc.update(config_version=version, crop_greenhouse_solar_execution=execution)
    if version==loader.EXECUTION_VERSION: del doc[loader.PREFIX_FLAG]
    else: doc[loader.PREFIX_FLAG]=prefix
    store(path, doc); calls=isolated_assembly(monkeypatch)
    assert loader.load_solar_api_runtime(path)[0]=='assembled'
    assert calls[0].crop_greenhouse_solar_execution is execution and calls[0].crop_greenhouse_solar_prefix is prefix


@pytest.mark.parametrize('flag', [loader.EXECUTION_FLAG,loader.PREFIX_FLAG])
@pytest.mark.parametrize('value', [None,0,1,'true','false',[],{},0.0])
def test_flags_reject_coercion_before_factory(prefix_config, monkeypatch, flag, value):
    path, doc=prefix_config; doc[flag]=value; store(path,doc)
    monkeypatch.setattr(original.importlib,'import_module',lambda *_:pytest.fail('invalid configuration imported factory'))
    with pytest.raises(original.OperatorConfigHold,match='^operator_config_rejected$'): loader.load_solar_api_runtime(path)


@pytest.mark.parametrize('fault', ['missing-execution','missing-prefix','extra','policy-flag','execution-disabled',
    'solar-disabled','cycle-disabled','reader-version','execution-version'])
def test_closed_versions_and_dependencies_fail_before_factory(prefix_config, monkeypatch, fault):
    path,doc=prefix_config
    if fault=='missing-execution':del doc[loader.EXECUTION_FLAG]
    elif fault=='missing-prefix':del doc[loader.PREFIX_FLAG]
    elif fault=='extra':doc['worker']={}
    elif fault=='policy-flag':doc['policy'][loader.PREFIX_FLAG]=True
    elif fault=='execution-disabled':doc[loader.EXECUTION_FLAG]=False
    elif fault=='solar-disabled':doc['policy'][loader.FLAG]=False
    elif fault=='cycle-disabled':doc['policy']['crop_cycle_result_storage']=False
    elif fault=='reader-version':doc['config_version']=loader.VERSION
    else:doc['config_version']=loader.EXECUTION_VERSION
    store(path,doc)
    monkeypatch.setattr(original.importlib,'import_module',lambda *_:pytest.fail('invalid configuration imported factory'))
    with pytest.raises(original.OperatorConfigHold,match='^operator_config_rejected$'):loader.load_solar_api_runtime(path)


def test_reader_and_direct_runtime_remain_disabled(solar_config, monkeypatch):
    calls=isolated_assembly(monkeypatch);loader.load_solar_api_runtime(solar_config[0])
    for value in (calls[0],config()):
        assert value.crop_greenhouse_solar_execution is value.crop_greenhouse_solar_prefix is False
    for field in (loader.EXECUTION_FLAG,loader.PREFIX_FLAG):
        for value in (None,0,1,'true',[],{}):
            with pytest.raises(ValueError,match='^API runtime configuration rejected$'):config(**{field:value})
    with pytest.raises(ValueError,match='^API runtime configuration rejected$'):config(crop_greenhouse_solar_execution=True)
    with pytest.raises(ValueError,match='^API runtime configuration rejected$'):
        config(policy=replace(policy(),crop_greenhouse_solar_result_storage=True),crop_greenhouse_solar_prefix=True)


def test_execution_requires_complete_store_graph_before_io(monkeypatch):
    def denied(*a,**kw):pytest.fail('invalid runtime performed I/O')
    monkeypatch.setattr('app.api_runtime.JobStore',denied)
    cfg=config(policy=replace(policy(),crop_greenhouse_solar_result_storage=True,crop_cycle_result_storage=True),
        crop_greenhouse_solar_execution=True,crop_greenhouse_solar_prefix=True)
    for result,query in ((None,None),(denied,None),(None,denied)):
        deps=dependencies(crop_cycle_result_store_factory=denied,crop_greenhouse_solar_result_store_factory=result,
            crop_greenhouse_solar_current_query_factory=query)
        with pytest.raises(ValueError,match='^API runtime assembly rejected$'):ApiRuntime(cfg,deps)


@pytest.mark.parametrize('phase',['factory','assembly'])
@pytest.mark.parametrize('field',['config','dsn_file','thermal_gate_key_file','market_hold_key_file','certificate','private_key','permissions'])
def test_protected_files_rechecked_at_each_boundary(prefix_config, monkeypatch, phase, field):
    reader.test_protected_files_are_rechecked_after_factory_and_assembly(prefix_config,monkeypatch,phase,field)


def test_other_nine_operator_versions_reject_solar_root_flags(private_config, monkeypatch):
    path,seed=private_config; calls=isolated_assembly(monkeypatch)
    versions=((original.load_api_runtime,'operator-api-config-v1'),
        (calculation.load_calculation_api_runtime,calculation.VERSION),
        *((joint.load_joint_api_runtime,v) for v in (joint.VERSION,joint.EXECUTION_VERSION,joint.PREFIX_VERSION)),
        *((ventilation.load_ventilation_api_runtime,v) for v in (ventilation.VERSION,ventilation.EXECUTION_VERSION,ventilation.PREFIX_VERSION,ventilation.MIXED_PREFIX_VERSION)))
    for load,version in versions:
        doc=deepcopy(seed);doc['config_version']=version
        if version==calculation.VERSION:doc['policy']['crop_cycle_calculation_result_storage']=False
        if version in (joint.EXECUTION_VERSION,joint.PREFIX_VERSION):doc[joint.EXECUTION_FLAG]=False
        if version==joint.PREFIX_VERSION:doc[joint.PREFIX_FLAG]=False
        if version in (ventilation.EXECUTION_VERSION,ventilation.PREFIX_VERSION,ventilation.MIXED_PREFIX_VERSION):doc[ventilation.EXECUTION_FLAG]=False
        if version in (ventilation.PREFIX_VERSION,ventilation.MIXED_PREFIX_VERSION):doc[ventilation.PREFIX_FLAG]=False
        if version==ventilation.MIXED_PREFIX_VERSION:doc[ventilation.JOINT_EXECUTION_FLAG]=doc[ventilation.JOINT_PREFIX_FLAG]=False
        store(path,doc)
        assert load(path)[0]=='assembled'
        before=len(calls)
        for flag in (loader.EXECUTION_FLAG,loader.PREFIX_FLAG):
            for value in (False,True):
                body=deepcopy(doc);body[flag]=value;store(path,body)
                with pytest.raises(original.OperatorConfigHold,match='^operator_config_rejected$'):load(path)
                assert len(calls)==before
    assert len(calls)==9
