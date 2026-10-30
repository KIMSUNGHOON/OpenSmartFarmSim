"""All-state dense candidates and same-time local refinement from genuine pending."""
from copy import deepcopy
from decimal import Decimal,localcontext
from fractions import Fraction
from math import exp,ulp
import json

import pytest

from app import crop_supply_forcing_threshold_state as model
from app import crop_supply_season as base
from app import crop_supply_forcing_owner as owner
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_supply_season import source,q,x,canonical
from test_crop_supply_forcing_owner import origin,setup_owner
from test_crop_supply_forcing_threshold import pending,stored_page,TOLERANCE


def calculate(pending,**kwargs):
    return model.calculate_threshold_state(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,**kwargs)


@pytest.fixture(scope='module')
def calculated(pending):
    result=calculate(pending)
    assert result['status']=='candidate_ready',result.get('hold')
    return result


def test_genuine_candidate_all_states_accounts_no_old_RHS_or_writes(pending,monkeypatch):
    evaluate=base.stage.evaluate;calls=[]
    def count(*a,**k):calls.append(1);return evaluate(*a,**k)
    monkeypatch.setattr(base.stage,'evaluate',count)
    monkeypatch.setattr(MorphologyBlobStore,'put',lambda *a,**k:pytest.fail('candidate wrote CAS'))
    result=calculate(pending)
    assert result['status']=='candidate_ready',result.get('hold')
    assert len(calls)==34
    assert result['progress']['root_RHS_evaluations']==5
    assert result['progress']['new_RHS_evaluations']==29
    assert result['progress']['past_confirmed_intervals_reintegrated']==0
    assert result['checkpoint_issued']is result['history_committed']is result['material_consumed']is False
    assert result['effective_rights']['redistribute']is False
    n=pending['result'].handle.current['numeric']
    for row in [result['dense_candidate'],*result['refinements']]:
        assert len(row['state'])==176 and len(row['partial_interval_transfers'])==185
        assert len(row['local_ledgers'])==len(row['pending_global_ledgers'])==124
        assert row['point_totals_exact']==n['point_totals_exact']
        assert row['transfer_origins']==n['transfer_origins']
        assert row['event_sequence']==n['event_sequence']
        assert 'output_cursor'not in row and 'output_prefix_sha256'not in row
    assert result['dense_candidate']['represented_threshold_status']=='crossed'
    assert result['at']['elapsed_seconds_exact']==result['root_certificate']['root']['upper_elapsed_seconds_exact']


def test_all176_dense_states_and185_integrals_against_independent_rounding(pending,calculated):
    result=calculated;trace=stored_page(pending)['result']['interval'];n=pending['result'].handle.current['numeric']
    left=x(trace['left_elapsed_seconds_exact']);dt=x(trace['step_seconds_exact'])
    theta=(x(result['at']['elapsed_seconds_exact'])-left)/dt
    weights=(theta-Fraction(3,2)*theta**2+Fraction(2,3)*theta**3,
             theta**2-Fraction(2,3)*theta**3,theta**2-Fraction(2,3)*theta**3,
             -theta**2/2+Fraction(2,3)*theta**3)
    with localcontext()as ctx:
        ctx.prec=2200
        def dec(v):return Decimal(v.numerator)/Decimal(v.denominator)
        for label,initial,field,actual in [
            ('state',n['last_confirmed']['state'],'rates',result['dense_candidate']['state']),
            ('flux',[0.]*185,'flux',[v['value']for v in result['dense_candidate']['partial_interval_transfers'].values()])]:
            for i,value in enumerate(initial):
                exact=Fraction(value)+dt*sum((w*Fraction(row[field][i])for w,row in zip(weights,trace['stages'],strict=True)),Fraction(0))
                decimal=Decimal.from_float(value)+dec(dt)*sum((dec(w)*Decimal.from_float(row[field][i])for w,row in zip(weights,trace['stages'],strict=True)),Decimal(0))
                assert actual[i]==float(exact),(label,i)
                assert abs(decimal-dec(exact))<Decimal('1e-2000'),(label,i)
    dense=result['dense_candidate'];duration=x(result['at']['elapsed_seconds_exact'])-left
    integral=Fraction(dense['partial_interval_transfers']['indoor_air_temperature_time']['value'])
    tb=Fraction(pending['result'].handle.basis['arithmetic_basis']['shoot_base_temperature'])
    age=x(n['schedule']['age_exact'])+(integral-tb*duration)/86400
    assert x(dense['shoot_age_exact'])==age
    assert x(dense['shoot_threshold_residual_exact'])==age-x(n['schedule']['next_threshold_exact'])


def test_same_time_refinement_traces_and_all_component_differences(calculated,pending):
    result=calculated;left=x(pending['result'].handle.current['at']['elapsed_seconds_exact'])
    at=x(result['at']['elapsed_seconds_exact']);state=pending['result'].handle.current['numeric']['last_confirmed']['state']
    def advance(initial,rows,weights,h,field):
        return [float(Fraction(v)+h*sum((w*Fraction(row[field][i])for w,row in zip(weights,rows,strict=True)),Fraction(0)))for i,v in enumerate(initial)]
    for record,count in zip(result['refinements'],(1,2,4),strict=True):
        assert record['substeps']==count and record['at']==result['at']
        current=list(state);totals=[0.]*185;step=(at-left)/count
        for i,trace in enumerate(record['intervals']):
            rows=trace['stages'];assert rows[0]['state']==current
            assert x(trace['left_elapsed_seconds_exact'])==left+i*step
            assert x(trace['step_seconds_exact'])==step
            for j,offset in [(1,step/2),(2,step/2),(3,step)]:
                assert rows[j]['state']==advance(current,[rows[j-1]],[Fraction(1)],offset,'rates')
            w=(Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6))
            current=advance(current,rows,w,step,'rates');totals=advance(totals,rows,w,step,'flux')
            assert trace['endpoint']['state']==current
        assert record['state']==current
        assert [v['value']for v in record['partial_interval_transfers'].values()]==totals
    packets=[result['dense_candidate'],*result['refinements']]
    assert len(result['state_differences'])==176 and len(result['transfer_differences'])==185
    for name,fields in [('state_differences',[r['state']for r in packets]),
                        ('transfer_differences',[[v['value']for v in r['partial_interval_transfers'].values()]for r in packets])]:
        for i,row in enumerate(result[name]):
            for key,a,b in [('dense_to_one_exact',0,1),('one_to_two_exact',1,2),('two_to_four_exact',2,3)]:
                assert x(row[key])==abs(Fraction(fields[a][i])-Fraction(fields[b][i])),(name,i,key)


def test_pure_RK4_nonlinear_analytic_convergence():
    errors=[]
    def evaluate(state,label):return tuple(state),tuple(state),{}
    for count in (1,2,4,8):
        state=(1.,);totals=(0.,);h=Fraction(1,2*count);first=(1.,);flow=(1.,)
        for i in range(count):
            state,totals,first,flow,_,_=model._rk4(state,totals,first,flow,h,i*h,evaluate)
        errors.append(abs(state[0]-exp(.5)))
    assert all(12<a/b<20 for a,b in zip(errors,errors[1:]))


def test_independent_all124_partial_accounts_budgets_and185_prefixes(pending,calculated):
    n0=pending['result'].handle.current['numeric'];basis=pending['result'].handle.basis['arithmetic_basis']
    seed=basis['seed'];p=seed['program'];n=len(p['leaves']);m=len(p['stem_root_compartments']);h=len(seed['organs']['internodes'])
    a=list(map(Fraction,n0['last_confirmed']['state']));size=106+3*n+m
    ca=Fraction(n0['last_confirmed']['derived']['air_capacity']['value'])
    profile_path=pending['workspace'].source_workspace.source_directory/basis['profile_sha256']['exchange_profile']
    lam=Fraction(json.loads(profile_path.read_bytes())['parameters']['latent_heat']['value'])
    reference=Fraction(p['scenario']['parameters']['reference_temperature']['value'])
    carbon=lambda y:y[0]+sum(y[3:53])+sum(y[106+2*n:106+3*n+m])
    with localcontext()as ctx:
        ctx.prec=2200
        for packet in [calculated['dense_candidate'],*calculated['refinements']]:
            b=list(map(Fraction,packet['state']));t={k:Fraction(v['value'])for k,v in packet['partial_interval_transfers'].items()}
            elapsed=x(packet['at']['elapsed_seconds_exact'])-x(n0['at']['elapsed_seconds_exact'])
            cap0=Fraction(n0['last_confirmed']['derived']['canopy_capacity']['value']);cap1=Fraction(packet['derived']['canopy_capacity']['value'])
            u0,u1=a[103],b[103];a0,a1=ca*(a[104]-reference),ca*(b[104]-reference)
            rows={
                'carbohydrate':((carbon(b)-carbon(a),-t['photosynthesis'],*(t[k]for k in ['growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit','removal_leaf','removal_stem','terminal_carbon'])),carbon(a),carbon(b)),
                'number':((sum(b[53:103])-sum(a[53:103]),-t['entry_number'],t['terminal_number']),sum(a[53:103]),sum(b[53:103])),
                'canopy_sensible':((u1-u0,-t['canopy_external'],t['sensible'],t['latent'],-t['incoming_heat'],t['outgoing_heat']),u0,u1),
                'air_sensible':((a1-a0,-t['air_external'],-t['sensible']),a0,a1),
                'vapor':((b[105]-a[105],-t['vapor'],-t['external_vapor']),a[105],b[105]),
                'area_capacity':((cap1-cap0,-t['capacity_in'],t['capacity_out']),cap0,cap1),
                'reduced_energy':((u1-u0,a1-a0,lam*(b[105]-a[105]),-t['canopy_external'],-t['air_external'],-lam*t['external_vapor'],-t['incoming_heat'],t['outgoing_heat']),u0+a0+lam*a[105],u1+a1+lam*b[105])}
            for i,leaf in enumerate(p['leaves']):
                rows[f'leaf_age_{i}']=((b[106+i]-a[106+i],-(t['indoor_air_temperature_time']-Fraction(leaf['base_temperature']['value'])*elapsed)/86400),a[106+i],b[106+i])
            for kind,offset,count in [('leaf',106+2*n,n),('stem_root',106+3*n,m)]:
                for i in range(count):rows[f'{kind}_carbon_{i}']=((b[offset+i]-a[offset+i],-t[f'{kind}_{i}_inflow'],t[f'{kind}_{i}_maintenance'],t[f'{kind}_{i}_removal']),a[offset+i],b[offset+i])
            rows['stem_root_carbon']=((sum(b[106+3*n:106+3*n+m])-sum(a[106+3*n:106+3*n+m]),-sum(t[f'stem_root_{i}_inflow']for i in range(m)),sum(t[f'stem_root_{i}_maintenance']+t[f'stem_root_{i}_removal']for i in range(m))),sum(a[106+3*n:106+3*n+m]),sum(b[106+3*n:106+3*n+m]))
            floor=Fraction(p['model_floor_area']['value']);indices={v['compartment_id']:i for i,v in enumerate(p['stem_root_compartments'])}
            for kind,organs,offset,key in [('leaf',seed['organs']['leaves'],106+n,'leaves'),('internode',seed['organs']['internodes'],size+h,'internodes')]:
                for i,organ in enumerate(organs):
                    label=f'{kind}_{i}';stock=f'leaf_{i}'if kind=='leaf'else f"stem_root_{indices[organ['compartment_id']]}"
                    rows[label+'_geometry']=((b[offset+i]-a[offset+i],-t[label+'_realized']),a[offset+i],b[offset+i])
                    rows[label+'_partition']=((t[label+'_extension'],t[label+'_unmapped'],-t[stock+'_inflow']),Fraction(0),Fraction(0))
                    rows[label+'_construction']=((t[label+'_extension'],-Fraction(seed['costs'][key][i])*t[label+'_realized']/floor),Fraction(0),Fraction(0))
                    if kind=='internode':rows[label+'_age']=((b[size+i]-a[size+i],-(t['indoor_air_temperature_time']-Fraction(organ['baseline']['base_temperature']['value'])*elapsed)/86400),a[size+i],b[size+i])
            assert len(rows)==124 and set(rows)==set(packet['local_ledgers'])
            for name,(terms,start,end)in rows.items():
                residual=sum(terms,Fraction(0));scale=max(abs(start),abs(end),sum(map(abs,terms),Fraction(0)))
                budget=64*(packet['partial_steps']+1)*Fraction(ulp(float(scale)))if scale else Fraction(0)
                assert x(packet['local_ledgers'][name]['residual_exact'])==residual,name
                assert x(packet['local_ledgers'][name]['budget_exact'])==budget,name
                for kind in ['branch','global']:
                    final=packet['pending_'+kind+'_ledgers'][name];prior=n0[kind+'_ledgers'][name]
                    assert x(final['residual_exact'])==x(prior['residual_exact'])+residual,(kind,name)
                    assert x(final['budget_exact'])==x(prior['budget_exact'])+budget,(kind,name)
                    dec=lambda f:Decimal(f.numerator)/Decimal(f.denominator)
                    assert abs(dec(x(final['residual_exact'])))<=dec(x(final['budget_exact'])),(kind,name)
            for name,value in t.items():
                assert x(packet['pending_branch_transfers_exact'][name])==Fraction(n0['branch_integrated_transfers'][name]['value'])+value,name
                assert x(packet['pending_lifetime_transfers_exact'][name])==x(n0['lifetime_transfers_exact'][name])+value,name


def test_full_split_source_has_same_calculation(pending,calculated):
    first=owner.advance(pending['start'],base.AdvanceRequest(q(536),step_budget=1))
    second=owner.advance(first.handle,base.AdvanceRequest(q(536),step_budget=10))
    assert second.handle.cursor_sha256==pending['result'].handle.cursor_sha256
    assert second.pending['page_sha256']==pending['result'].pending['page_sha256']
    result=model.calculate_threshold_state(second.handle,second.pending['page_sha256'],TOLERANCE)
    assert result==calculated


def test_cancellation_before_and_during_refinement_returns_no_candidate(pending,monkeypatch):
    result=calculate(pending,cancelled=lambda:True)
    assert result['status']=='hold'and result['hold'].startswith('CANCELLED_HOLD:')
    assert result['progress']['root_RHS_evaluations']==0
    stage=base.stage.evaluate;counter=[];cancel={'now':False}
    def evaluate(*a,**k):
        value=stage(*a,**k);counter.append(1)
        if len(counter)==7:cancel['now']=True
        return value
    monkeypatch.setattr(base.stage,'evaluate',evaluate)
    result=calculate(pending,cancelled=lambda:cancel['now'])
    assert result['status']=='hold'and result['hold'].startswith('CANCELLED_HOLD:')
    assert result['dense_candidate']is None and result['refinements']==[]
    assert len(counter)==7 and result['historical_cursor_sha256']==pending['result'].handle.cursor_sha256


@pytest.mark.parametrize('change',['source','pending'])
def test_late_source_or_pending_change_removes_entire_candidate(pending,tmp_path,monkeypatch,change):
    import shutil
    old=pending['workspace'];src=tmp_path/'source';parent=tmp_path/'parent';archive=tmp_path/'archive'
    shutil.copytree(old.source_workspace.source_directory,src);shutil.copytree(old.source_workspace.archive_directory,parent);shutil.copytree(old.archive_directory,archive)
    ws=owner.Workspace(base.Workspace(src,parent,old.access),archive,old.access)
    h=owner.open_season(owner.CursorRef(pending['result'].handle.cursor_sha256),pending['definition'],ws)
    reference=pending['result'].pending['page_sha256']
    path=src/h.basis['arithmetic_basis']['profile_sha256']['growth_profile']if change=='source'else archive/reference
    evaluate=base.stage.evaluate;calls=[]
    def corrupt(*a,**k):
        value=evaluate(*a,**k);calls.append(1)
        if len(calls)==6:path.write_bytes(path.read_bytes()+b' ')
        return value
    monkeypatch.setattr(base.stage,'evaluate',corrupt)
    result=model.calculate_threshold_state(h,reference,TOLERANCE)
    assert result['status']=='hold'and result['dense_candidate']is None and result['refinements']==[]
    assert result['authority_hold']is not None


def test_bad_dense_capacity_fails_account_validation(pending,monkeypatch):
    evaluate=base.stage.evaluate;calls=[]
    def wrong(*a,**k):
        value=evaluate(*a,**k);calls.append(1)
        if len(calls)==6:value['derived']['air_capacity']['value']*=2
        return value
    monkeypatch.setattr(base.stage,'evaluate',wrong)
    result=calculate(pending)
    assert result['status']=='hold'and result['hold'].startswith('BALANCE_HOLD:')
    assert result['dense_candidate']is None and result['refinements']==[]


def test_caller_tolerance_change_keeps_admitted_selection(pending,calculated,monkeypatch):
    tolerance=deepcopy(TOLERANCE);evaluate=base.stage.evaluate;calls=[]
    def change(*a,**k):
        value=evaluate(*a,**k);calls.append(1)
        if len(calls)==6:tolerance.update(q(1))
        return value
    monkeypatch.setattr(base.stage,'evaluate',change)
    result=model.calculate_threshold_state(pending['result'].handle,pending['result'].pending['page_sha256'],tolerance)
    assert tolerance!=TOLERANCE
    assert result==calculated


@pytest.mark.parametrize('tolerance',[q(0),q(1,'degC_day'),True])
def test_invalid_tolerance_never_evaluates_RHS(pending,tolerance,monkeypatch):
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('invalid request ran RHS'))
    result=model.calculate_threshold_state(pending['result'].handle,pending['result'].pending['page_sha256'],tolerance)
    assert result['status']=='hold'and result['dense_candidate']is None


def test_exhausted_whole_wall_budget_never_restarts_root_deadline(pending,monkeypatch):
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('exhausted wall ran RHS'))
    result=calculate(pending,wall_seconds=1)
    assert result['status']=='hold'and result['hold'].startswith('WALL_HOLD:')
    assert result['progress']['root_RHS_evaluations']==0


def test_pure_RK4_rejects_a_nonzero_change_lost_to_rounding():
    with pytest.raises(ValueError,match='NUMERIC_HOLD:'):
        model._rk4((1.,),(0.,),(1e-320,),(0.,),Fraction(1,8),Fraction(0),lambda *a:pytest.fail('rounded stage accepted'))
