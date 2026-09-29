"""Real SCRAM privilege audit budget; no cached or omitted security checks."""
from pathlib import Path
import sys
from statistics import median
from time import perf_counter

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.runtime_login import connect_runtime
from app.runtime_roles import audit_runtime_roles
from test_market_source_store import PROFILE,login_database,login_scope

pytestmark=pytest.mark.parametrize('login_scope',[{**PROFILE,'break_even_calculation':True}],indirect=True)


class CountQueries:
    def __init__(self,connection):self.connection,self.count=connection,0
    def execute(self,*args,**kwargs):
        self.count+=1
        return self.connection.execute(*args,**kwargs)
    def __getattr__(self,name):return getattr(self.connection,name)


def test_complete_effective_grant_audit_has_bounded_round_trips(login_scope):
    _,policy,dsns=login_scope
    elapsed=[];counts=[]
    with connect_runtime(dsns['authority'],policy,'authority') as conn:
        for _ in range(3):
            measured=CountQueries(conn);start=perf_counter()
            result=audit_runtime_roles(measured,policy)
            elapsed.append(perf_counter()-start);counts.append(measured.count)
            conn.commit()
            assert result['policy_version']=='runtime-market-source-login-policy-v5'
    print({'audit_queries':counts,'audit_median_seconds':round(median(elapsed),6)},flush=True)
    assert max(counts)<=120
