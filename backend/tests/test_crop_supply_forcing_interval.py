"""Real saved source, shared-stage forcing, exact grid remainder and balances."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_supply_season as base
from app import crop_supply_forcing_interval as forcing
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_supply_season import source, setup, q, x, canonical, SOURCE


@pytest.fixture(scope='module')
def actual(source,tmp_path_factory):
    directory=tmp_path_factory.mktemp('forcing-parent')
    ws,definition,_,_,_=setup(source,directory)
    start=base.open_season(base.SourceRef(SOURCE,36),definition,ws)
    first=base.advance(start,base.AdvanceRequest(q(520),step_budget=1))
    last=base.advance(first.handle,base.AdvanceRequest(q(520)))
    assert first.status=='yielded'and last.status=='completed'
    basis=first.handle.basis
    classes={'growth_profile':base.growth.ReferenceParameters,'cohort_profile':base.cohort.ReferenceFruitCohortParameters,
             'transport_profile':base.transport.ReferenceFruitTransportParameters,'exchange_profile':base.exchange.ReferenceParameters}
    with MorphologyBlobStore(ws.source_directory,ws.access)as store:
        profiles={k:cls(store.get(basis['profile_sha256'][k],maximum=64*1024))for k,cls in classes.items()}
    return {'basis':basis,'before':first.handle.current,'constant520':last.handle.current,'profiles':profiles}


def span(actual,begin,end,*,changed=False):
    p=actual['basis']['seed']['program']['scenario']
    value={'input_id':'own-synthetic-forcing-change'if changed else'own-original-forcing',
           'origin':'synthetic','start':q(begin),'end':q(end),
           'forcing':deepcopy(p['forcing']),'fruit_entry':deepcopy(p['fruit_entry'])}
    if changed:
        value['forcing']['canopy_external_heat']['value']+=p['forcing']['air_external_sensible_heat']['value']
        for key in ['air_external_sensible_heat','air_external_vapor','par_above_canopy','co2']:
            value['forcing'][key]['value']*=2
        value['fruit_entry']['fruit_number_inflow']['value']*=2
    return value


def run(actual,current,inputs,end):
    return forcing.advance_interval(basis=actual['basis'],current=current,profiles=actual['profiles'],span=inputs,end=q(end))


def test_constant_original_grid_step_matches_saved_family_oracle(actual):
    result=run(actual,actual['before'],span(actual,512,520),520)
    assert result['status']=='interval_ready'
    for field in base.NUMERIC_FIELDS:
        if field not in ('output_cursor','output_prefix_sha256'):
            assert result['current'][field]==actual['constant520'][field],field
    assert result['checkpoint_issued']is False and result['history_committed']is False
    assert 'output_cursor'not in result['current']and 'output_prefix_sha256'not in result['current']


def test_fractional_edge_preserves_grid_and_applies_same_view_to_RHS_and_flux(actual,monkeypatch):
    seen={};evaluate=base.stage.evaluate;flux=base.books.flux
    def evaluate_spy(program,*args,**kwargs):
        result=evaluate(program,*args,**kwargs)
        seen[id(result)]=canonical({k:program['scenario'][k]for k in ('forcing','fruit_entry')})
        return result
    def flux_spy(program,state,rhs,organs):
        assert seen[id(rhs)]==canonical({k:program['scenario'][k]for k in ('forcing','fruit_entry')})
        return flux(program,state,rhs,organs)
    monkeypatch.setattr(base.stage,'evaluate',evaluate_spy);monkeypatch.setattr(base.books,'flux',flux_spy)
    first=run(actual,actual['before'],span(actual,512,Fraction(1025,2)),Fraction(1025,2))
    second=run(actual,first['current'],span(actual,Fraction(1025,2),520,changed=True),520)
    assert first['status']==second['status']=='interval_ready'
    assert first['current']['grid_index']==64
    assert first['current']['grid_remainder_exact']==q(Fraction(1,2))
    assert first['current']['next_grid_endpoint_exact']==q(520)
    assert second['current']['grid_index']==65 and second['current']['grid_remainder_exact']==q(0)
    transition=second['forcing_transition']
    assert transition['changed']is True and transition['at']==first['current']['at']
    assert transition['before_state_sha256']==transition['after_state_sha256']
    assert transition['before_derived']!=transition['after_derived']
    assert second['current']['point_totals_exact']==actual['before']['point_totals_exact']


def test_serialized_interval_state_replays_same_declared_partition(actual):
    left=span(actual,512,Fraction(1025,2));right=span(actual,Fraction(1025,2),520,changed=True)
    first=run(actual,actual['before'],left,Fraction(1025,2))
    direct=run(actual,first['current'],right,520)
    serialized=json.loads(canonical(first['current']))
    again=run(actual,serialized,right,520)
    assert direct==again
    assert direct['current']['last_confirmed']['state']!=actual['constant520']['last_confirmed']['state']


def test_external_heat_vapor_and_number_fluxes_use_active_span(actual):
    edge=Fraction(1025,2)
    first=run(actual,actual['before'],span(actual,512,edge),edge)
    changed=span(actual,edge,520,changed=True)
    result=run(actual,first['current'],changed,520)
    names=[v['name']for v in result['interval']['flux_order']]
    fields={'canopy_external':changed['forcing']['canopy_external_heat']['value'],
            'air_external':changed['forcing']['air_external_sensible_heat']['value'],
            'external_vapor':changed['forcing']['air_external_vapor']['value'],
            'entry_number':changed['fruit_entry']['fruit_number_inflow']['value']}
    for name,value in fields.items():
        for row in result['interval']['stages']:assert row['flux'][names.index(name)]==value
        before=first['current']['branch_integrated_transfers'][name]['value']
        expected=float(Fraction(before)+Fraction(value)*(520-edge))
        assert result['current']['branch_integrated_transfers'][name]['value']==expected


def test_pending_interval_never_issues_a_state_after_material_threshold(actual):
    result=run(actual,actual['constant520'],span(actual,520,528),528)
    assert result['status']=='awaiting_material'and result['current']is None
    assert result['pending']['left_at']==q(520)and result['pending']['right_at']==q(528)
    assert result['pending']['schedule_consumed']is False
    assert result['checkpoint_issued']is False


@pytest.mark.parametrize('kind',['gap','cross_grid','unit','retroactive_change'])
def test_invalid_span_fails_before_RHS(actual,kind,monkeypatch):
    inputs=span(actual,512,520);end=520
    if kind=='gap':inputs['start']=q(513)
    if kind=='cross_grid':inputs['end']=q(528);end=Fraction(1041,2)
    if kind=='unit':inputs['forcing']['co2']['unit']='percent'
    if kind=='retroactive_change':inputs=span(actual,504,520,changed=True)
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('bad span evaluated RHS'))
    with pytest.raises(ValueError):run(actual,actual['before'],inputs,end)


def test_original_basis_current_span_and_512_horizon_are_unchanged(actual):
    inputs=span(actual,512,520,changed=True)
    before=canonical([actual['basis'],actual['before'],inputs])
    run(actual,actual['before'],inputs,520)
    assert canonical([actual['basis'],actual['before'],inputs])==before
    assert actual['basis']['seed']['original_numerical']['duration_seconds']==512.


def test_inconsistent_source_grid_is_rejected_before_RHS(actual,monkeypatch):
    bad=deepcopy(actual['before']);bad['grid_index']+=1
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('bad grid evaluated RHS'))
    with pytest.raises(ValueError,match='TIME_HOLD:'):
        run(actual,bad,span(actual,512,520),520)


def test_independent_all124_residual_changes_and_185_lifetime_sums(actual):
    from decimal import Decimal,localcontext
    edge=Fraction(1025,2)
    first=run(actual,actual['before'],span(actual,512,edge),edge)
    result=run(actual,first['current'],span(actual,edge,520,changed=True),520)
    before,after=actual['before'],result['current'];seed=actual['basis']['seed'];p=seed['program']
    n=len(p['leaves']);m=len(p['stem_root_compartments']);h=len(seed['organs']['internodes']);size=106+3*n+m
    a,b=([Fraction(v)for v in row['last_confirmed']['state']]for row in [before,after])
    t={k:x(after['lifetime_transfers_exact'][k])-x(before['lifetime_transfers_exact'][k])for k in before['lifetime_transfers_exact']}
    d0,d1=before['last_confirmed']['derived'],after['last_confirmed']['derived'];ca=Fraction(d0['air_capacity']['value']);lam=Fraction(actual['profiles']['exchange_profile'].values['latent_heat'])
    carbon=lambda y:y[0]+sum(y[3:53])+sum(y[106+2*n:106+3*n+m])
    rows={'carbohydrate':carbon(b)-carbon(a)-t['photosynthesis']+sum(t[k]for k in ['growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit','removal_leaf','removal_stem','terminal_carbon']),
          'number':sum(b[53:103])-sum(a[53:103])-t['entry_number']+t['terminal_number'],
          'canopy_sensible':b[103]-a[103]-t['canopy_external']+t['sensible']+t['latent']-t['incoming_heat']+t['outgoing_heat'],
          'air_sensible':ca*(b[104]-a[104])-t['air_external']-t['sensible'],
          'vapor':b[105]-a[105]-t['vapor']-t['external_vapor'],
          'area_capacity':Fraction(d1['canopy_capacity']['value'])-Fraction(d0['canopy_capacity']['value'])-t['capacity_in']+t['capacity_out'],
          'reduced_energy':b[103]-a[103]+ca*(b[104]-a[104])+lam*(b[105]-a[105])-t['canopy_external']-t['air_external']-lam*t['external_vapor']-t['incoming_heat']+t['outgoing_heat']}
    elapsed=x(after['at']['elapsed_seconds_exact'])-x(before['at']['elapsed_seconds_exact'])
    for i,leaf in enumerate(p['leaves']):rows[f'leaf_age_{i}']=b[106+i]-a[106+i]-(t['indoor_air_temperature_time']-Fraction(leaf['base_temperature']['value'])*elapsed)/86400
    for kind,offset,count in [('leaf',106+2*n,n),('stem_root',106+3*n,m)]:
        for i in range(count):rows[f'{kind}_carbon_{i}']=b[offset+i]-a[offset+i]-t[f'{kind}_{i}_inflow']+t[f'{kind}_{i}_maintenance']+t[f'{kind}_{i}_removal']
    rows['stem_root_carbon']=sum(b[106+3*n:106+3*n+m])-sum(a[106+3*n:106+3*n+m])-sum(t[f'stem_root_{i}_inflow']for i in range(m))+sum(t[f'stem_root_{i}_maintenance']+t[f'stem_root_{i}_removal']for i in range(m))
    floor=Fraction(p['model_floor_area']['value']);indices={v['compartment_id']:i for i,v in enumerate(p['stem_root_compartments'])}
    for kind,organs,offset,key in [('leaf',seed['organs']['leaves'],106+n,'leaves'),('internode',seed['organs']['internodes'],size+h,'internodes')]:
        for i,organ in enumerate(organs):
            label=f'{kind}_{i}';stock=f'leaf_{i}'if kind=='leaf'else f"stem_root_{indices[organ['compartment_id']]}"
            rows[label+'_geometry']=b[offset+i]-a[offset+i]-t[label+'_realized']
            rows[label+'_partition']=t[label+'_extension']+t[label+'_unmapped']-t[stock+'_inflow']
            rows[label+'_construction']=t[label+'_extension']-Fraction(seed['costs'][key][i])*t[label+'_realized']/floor
            if kind=='internode':rows[label+'_age']=b[size+i]-a[size+i]-(t['indoor_air_temperature_time']-Fraction(organ['baseline']['base_temperature']['value'])*elapsed)/86400
    assert len(rows)==124 and set(rows)==set(after['global_ledgers'])
    with localcontext()as ctx:
        ctx.prec=2200
        for name,residual in rows.items():
            left=x(before['global_ledgers'][name]['residual_exact']);right=x(after['global_ledgers'][name]['residual_exact'])
            assert residual==right-left,name
            decimal=lambda f:Decimal(f.numerator)/Decimal(f.denominator)
            assert abs(decimal(right))<=decimal(x(after['global_ledgers'][name]['budget_exact'])),name
    for name in before['lifetime_transfers_exact']:
        assert x(after['lifetime_transfers_exact'][name])==x(seed['lifetime_transfers_exact'][name])+Fraction(after['branch_integrated_transfers'][name]['value']),name
