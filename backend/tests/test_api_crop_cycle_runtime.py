"""Cycle reader options fail before connections; actual assembly is tested over TLS."""
from dataclasses import replace

import pytest

from app import api_runtime as runtime
from test_api_runtime import config,dependencies,policy


def test_cycle_flag_without_factory_fails_before_connections(monkeypatch):
    calls=[]
    monkeypatch.setattr(runtime,'JobStore',lambda *a,**kw:calls.append('connection'))
    with pytest.raises(ValueError,match='^API runtime assembly rejected$'):
        runtime.ApiRuntime(config(policy=replace(policy(),crop_cycle_result_storage=True)),dependencies())
    assert calls==[]


def test_cycle_factory_without_flag_fails_before_connections_and_invocation(monkeypatch):
    calls=[]
    monkeypatch.setattr(runtime,'JobStore',lambda *a,**kw:calls.append('connection'))
    with pytest.raises(ValueError,match='^API runtime assembly rejected$'):
        runtime.ApiRuntime(config(),dependencies(crop_cycle_result_store_factory=lambda **_:calls.append('factory')))
    assert calls==[]


@pytest.mark.parametrize('factory',[True,0,'private factory path'])
def test_cycle_noncallable_factory_is_rejected_without_private_error(factory):
    with pytest.raises(ValueError,match='^API runtime dependencies rejected$'):
        dependencies(crop_cycle_result_store_factory=factory)


def test_cycle_factory_is_optional_hidden_and_preserves_legacy_defaults():
    deps=dependencies();assert deps.crop_cycle_result_store_factory is None and not policy().crop_cycle_result_storage
    factory=lambda **_:None;selected=dependencies(crop_cycle_result_store_factory=factory)
    assert selected.crop_cycle_result_store_factory is factory and 'crop_cycle_result_store_factory' not in repr(selected)
