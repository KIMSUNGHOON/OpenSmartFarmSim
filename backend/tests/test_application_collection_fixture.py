"""Actual SCRAM regression for the private hosted collector fixture assembly."""

from pathlib import Path
import runpy
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.owned_fixture_collection import CollectionService, CollectionWorker
from app.owned_fixture_registry import OwnedFixtureRegistry
from login_database import login_database, login_scope
from test_economic_calculation_worker import calculation_setup, economic_api, PROFILE

ROOT=Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_private_collection_parent_uses_same_login_and_tenant(calculation_setup,login_scope,tmp_path):
    _,jobs,_,_,_,principal=calculation_setup
    fixture=runpy.run_path(str(ROOT/'scripts/application-collection-fixture.py'))
    def private(path,value):
        path.write_bytes(value if type(value) is bytes else value.encode())
        path.chmod(0o600)
    commands=[]
    body=fixture['prepare'](tmp_path,login_scope,principal,private=private,
                            command=lambda *args:commands.append(args))
    service=CollectionService(jobs,OwnedFixtureRegistry(ROOT))
    collected=service.submit('tenant-1',body['research_job_id'],'assembly-check')
    assert CollectionWorker(service,tenant_id='tenant-1').run_once(str(collected['job_id'])).state=='succeeded'
    record=service.read_record('tenant-1',str(collected['job_id']))
    assert record['g0_status']==record['g1_status']=='not_accepted'
    assert record['assessment_status']=='hold'
    assert commands==[('sudo','chown','-R','11001:11010',str(tmp_path/'collection'))]
