"""Closed worker authority and resource options before database access."""
import psycopg
import pytest
from app import crop_greenhouse_co2_execution_worker as model


@pytest.mark.parametrize('change',[{'tenant_id':None},{'lease_seconds':True},{'lease_seconds':0},
    {'chunk_budget':True},{'chunk_budget':0},{'chunk_budget':129}])
def test_invalid_worker_options_reject_before_io(monkeypatch,change):
    called=[]
    def deny(*a,**kw):called.append(1);raise AssertionError('invalid worker used database')
    monkeypatch.setattr(psycopg,'connect',deny)
    options={'tenant_id':'tenant-1',**change}
    with pytest.raises(ValueError):model.Co2ExecutionWorker(None,None,**options)
    assert called==[]


@pytest.mark.parametrize('checkpoints,result',[(None,object()),(object(),None),(object(),object())])
def test_exact_checkpoint_and_result_authorities_are_required(checkpoints,result):
    with pytest.raises(model.checkpoints.Co2CheckpointHold,match='^co2 worker authority unavailable$'):
        model.Co2ExecutionWorker(checkpoints,result,tenant_id='tenant-1')
