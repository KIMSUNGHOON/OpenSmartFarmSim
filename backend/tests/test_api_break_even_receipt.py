"""Historical intent metadata only; all source records/keys are synthetic."""
import asyncio
from hashlib import sha256
from urllib.parse import urlencode
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from app.jobs import canonical_input_bytes
from app.break_even_plan_submission import PLAN_RECEIPT_SCOPES
from test_api_break_even_plan import plan_api,post,login_database,login_scope,PROFILE
from test_http_identity import request
import pytest

pytestmark=pytest.mark.parametrize('login_scope',[{**PROFILE,'break_even_calculation':True}],indirect=True)


def receipt(app,plan_id,digest):
    return asyncio.run(request(app,path='/v1/break-even-plans/receipt',
        query=urlencode({'plan_id':plan_id,'submission_sha256':digest}).encode()))[:2]


def test_receipt_is_exact_historical_read_without_source_reapproval(plan_api,monkeypatch):
    app,service,body,principal=plan_api
    assert '409' in app.openapi()['paths']['/v1/break-even-plans/receipt']['get']['responses']
    body['request']['plan_id']='가격/#?'
    digest=sha256(canonical_input_bytes(body)).hexdigest()
    assert receipt(app,body['request']['plan_id'],digest)[0]==404
    status,accepted=post(app,body);assert status==202
    principal['scopes']=set(PLAN_RECEIPT_SCOPES)
    def forbidden_prepare(*args,**kwargs):raise AssertionError('receipt must not reprepare sources')
    monkeypatch.setattr(service,'_prepare',forbidden_prepare)
    status,value=receipt(app,body['request']['plan_id'],digest)
    assert status==200 and value=={'plan_id':body['request']['plan_id'],'submission_sha256':digest,'intent_status':'stored','intent_job':accepted['intent_job']}
    assert receipt(app,body['request']['plan_id'],'f'*64)==(409,{'error':{'code':'intent_conflict','message':'Intent already has a different request'}})
    for scope in PLAN_RECEIPT_SCOPES:
        principal['scopes'].remove(scope);assert receipt(app,body['request']['plan_id'],digest)[0]==403;principal['scopes'].add(scope)
    principal['tenant_id']='tenant-2';assert receipt(app,body['request']['plan_id'],digest)[0]==404
    principal['tenant_id']='tenant-1';principal['authenticated']=False;assert receipt(app,body['request']['plan_id'],digest)[0]==401
    principal['authenticated']=True
    assert receipt(app,' '+body['request']['plan_id'],digest)[0]==422 and receipt(app,body['request']['plan_id'],'invalid')[0]==422
    def revoked_input(*args,**kwargs):
        principal['scopes'].remove('artifact');raise RuntimeError('private fixture detail')
    monkeypatch.setattr(service.jobs,'_verified_input',revoked_input)
    assert receipt(app,body['request']['plan_id'],digest)==(403,{'error':{'code':'forbidden','message':'Resource access denied'}})
