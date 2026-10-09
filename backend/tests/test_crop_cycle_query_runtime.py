"""Explicit query selection fails before connections and preserves defaults."""
import pytest

from app import api_runtime as runtime
from test_api_runtime import config, dependencies


def test_current_query_without_result_store_fails_before_connections(monkeypatch):
    calls=[]
    monkeypatch.setattr(runtime,'JobStore',lambda *a,**kw:calls.append('connection'))
    deps=dependencies(crop_cycle_current_query_factory=lambda **_:calls.append('query-factory'))
    with pytest.raises(ValueError,match='^API runtime assembly rejected$'):
        runtime.ApiRuntime(config(),deps)
    assert calls==[]


@pytest.mark.parametrize('factory',[True,0,'private query factory'])
def test_noncallable_query_factory_is_rejected_without_private_details(factory):
    with pytest.raises(ValueError,match='^API runtime dependencies rejected$'):
        dependencies(crop_cycle_current_query_factory=factory)


def test_current_query_is_optional_and_hidden_from_dependency_repr():
    deps=dependencies();assert deps.crop_cycle_current_query_factory is None
    factory=lambda **_:None
    selected=dependencies(crop_cycle_current_query_factory=factory)
    assert selected.crop_cycle_current_query_factory is factory
    assert 'crop_cycle_current_query_factory' not in repr(selected)
