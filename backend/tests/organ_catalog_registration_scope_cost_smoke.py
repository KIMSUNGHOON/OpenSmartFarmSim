"""Manual paired comparison on three normal small signed rows; no capacity claim."""
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import time

import psycopg
import pytest

from app.crop_organ_result_catalog import OrganCropResultCatalog
from app.crop_result_store import CropResultStore
from app.farm_authoring_storage import FarmAuthoringService
from test_crop_result_store import crop_setup,authoring,farm_setup,login_scope,login_database,put,count

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,
    'break_even_calculation':True,'crop_result_storage':True}],indirect=True)


def test_same_three_signed_results_ABBA_registration_scope_cost(crop_setup,monkeypatch):
    store,body,_,rights=crop_setup
    records=[]
    for index in range(3):
        request=deepcopy(body);request['study_id']='paired-scope-'+str(index)
        records.append(put(store,request))
    before={r['result_id']:store._find('tenant-1',result_id=r['result_id']) for r in records}
    scope=OrganCropResultCatalog._inspection_scope
    original_read=FarmAuthoringService._read_registration
    original_rights=type(rights).__call__
    measured={'reconstructions':0,'rights':0,'forbidden':0,'SQL_writes':0}
    def read(self,*args):
        measured['reconstructions']+=1
        return original_read(self,*args)
    def current_rights(self,*args):
        measured['rights']+=1
        return original_rights(self,*args)
    @contextmanager
    def baseline(self,tenant,farm):
        yield
    def forbidden(*args,**kwargs):
        measured['forbidden']+=1
        raise AssertionError('paired metadata query attempted production or calculation')
    execute=psycopg.Connection.execute
    def read_only(conn,statement,*args,**kwargs):
        text=statement.as_string(conn) if hasattr(statement,'as_string') else statement
        if text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
            measured['SQL_writes']+=1
            raise AssertionError('paired metadata query attempted SQL mutation')
        return execute(conn,statement,*args,**kwargs)
    rows=[]
    page_before=None
    with monkeypatch.context() as patch:
        patch.setattr(FarmAuthoringService,'_read_registration',read)
        patch.setattr(type(rights),'__call__',current_rights)
        patch.setattr(CropResultStore,'put',forbidden)
        patch.setattr('app.crop_result_store.integrate_crop',forbidden)
        patch.setattr('app.crop_growth_integration.rates.calculate_rates',forbidden)
        patch.setattr(psycopg.Connection,'execute',read_only)
        for mode in ('baseline','candidate','candidate','baseline'):
            patch.setattr(OrganCropResultCatalog,'_inspection_scope',baseline if mode=='baseline' else scope)
            measured['reconstructions']=measured['rights']=0
            began=time.monotonic()
            with OrganCropResultCatalog(store).open('tenant-1','organ_v1',body['farm'],limit=3) as page:
                if page_before is None:page_before=deepcopy(page)
                else:assert page==page_before
            elapsed=time.monotonic()-began
            assert store.farms._registration_read.get() is None
            assert measured['reconstructions']==(23 if mode=='baseline' else 8)
            assert measured['rights']==18
            rows.append({'mode':mode,'wall_seconds':elapsed,'full_reconstructions':measured['reconstructions'],
                'current_program_rights_checks':measured['rights']})
        assert count(store)==3 and {k:store._find('tenant-1',result_id=k) for k in before}==before
    gains=[100*(rows[0]['wall_seconds']-rows[1]['wall_seconds'])/rows[0]['wall_seconds'],
        100*(rows[3]['wall_seconds']-rows[2]['wall_seconds'])/rows[3]['wall_seconds']]
    mean=sum(gains)/2
    accepted=mean>=5 and all(g>0 for g in gains)
    evidence={'scope':'paired direct metadata cost on same three small normal signed rows only',
        'order':'baseline,candidate,candidate,baseline','trials':rows,'paired_reductions_percent':gains,
        'mean_reduction_percent':mean,'threshold_mean_percent':5,'both_pairs_must_improve':True,
        'accepted_component_cost':accepted,'original_rows_unchanged':True,
        'same_metadata':True,'current_program_rights_checks_each_trial':18,
        'put_integrate_RHS_or_SQL_write_calls':measured['forbidden']+measured['SQL_writes'],
        'HTTPS_performed':False,'large_packet_or_twenty_capacity_accepted':False,
        'WSL_capacity_accepted':False,'actual_crop_Runs':0,'G0_G4':'not_assessed'}
    path=Path(os.environ['OSSF_JOINT_PREFIX_RUNTIME_EVIDENCE'])/'organ-registration-scope-cost.private.json'
    with path.open('x') as stream:
        os.fchmod(stream.fileno(),0o400);json.dump(evidence,stream,sort_keys=True,indent=2)
    assert measured['forbidden']==measured['SQL_writes']==0 and accepted,evidence
