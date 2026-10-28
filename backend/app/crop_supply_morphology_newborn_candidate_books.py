"""Exact current-plus-partial accounts on the actual post-material trajectory."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_supply_morphology_newborn_resume as resume
from . import crop_supply_morphology_candidate_books as algebra

source=resume.source
F,Q,X=resume.F,resume.Q,resume.X
need=resume._need
MASS=resume.books.MASS
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def projection(data):
    return {**data,'initial':{'organs':data['organs'],'state_layout':data['seed']['state_layout'],'state':data['seed']['initial_sample']['state']}}


def _global_rows(context,data,state,lifetime,last,at):
    seed=data['seed'];p=data['program'];n=len(p['leaves']);m=len(p['stem_root_compartments']);organs=data['organs'];h=len(organs['internodes']);size=seed['state_layout']['original_prefix_length']
    root_p,root_seed,_=source.stock.parent._context(context._origin._source._source._root)
    a,b=tuple(map(F,root_seed['state'])),tuple(map(F,state));first=source.stock.short._view(root_seed['evaluation'])['joint']['derived'];points={k:X(v)for k,v in seed['point_totals_exact'].items()}
    rows=source.candidate._physical(p,a,b[:size],lifetime,first,last,data['profiles']['exchange_profile'].values['latent_heat'],len(root_p['leaves']),points)
    for i,birth in enumerate(seed['birth_bases']['leaf']):
        rows[f'leaf_age_{i}']=((b[106+i]-X(birth['thermal_age_exact']),-(lifetime['indoor_air_temperature_time']-X(birth['air_temperature_integral_exact'])-F(birth['base_temperature']['value'])*(at-X(birth['at_elapsed_seconds_exact'])))/86400),Fraction(0),Fraction(0),'degC_day')
    for kind,start in [('leaf',106+2*n),('stem_root',106+3*n)]:
        for i,birth in enumerate(seed['birth_bases'][kind]):rows[f'{kind}_carbon_{i}']=((b[start+i]-F(birth['carbon']['value']),-lifetime[f'{kind}_{i}_inflow'],lifetime[f'{kind}_{i}_maintenance'],lifetime[f'{kind}_{i}_removal']),Fraction(0),Fraction(0),MASS)
    rows['stem_root_carbon']=((sum(b[106+3*n:size])-sum(a[106+3*len(root_p['leaves']):]),-sum(lifetime[f'stem_root_{i}_inflow']for i in range(m)),sum(lifetime[f'stem_root_{i}_maintenance']+lifetime[f'stem_root_{i}_removal']for i in range(m)),-points['stem_structural_carbon']),Fraction(0),Fraction(0),MASS)
    old=data['origin_data'];old_initial=old['initial'];old_n=len(old['program']['leaves']);old_h=len(old_initial['organs']['internodes']);floor=F(p['model_floor_area']['value'])
    for kind,meta,offset,unit,cost_key in [('leaf',organs['leaves'],106+n,'m2','leaves'),('internode',organs['internodes'],size+h,'m','internodes')]:
        for i,node in enumerate(meta):
            key=f'{kind}_{i}';existing=i<(old_n if kind=='leaf'else old_h);old_offset=106+old_n if kind=='leaf'else old_initial['state_layout']['original_prefix_length']+old_h
            geometry_origin=F(old_initial['state'][old_offset+i])if existing else F(seed['initial_sample']['state'][offset+i]);stock_i=i if kind=='leaf'else data['stem_stock_indices'][i]
            inflow=f'{"leaf"if kind=="leaf"else"stem_root"}_{stock_i}_inflow';flow_origin=X(old['parent']['lifetime_transfers_exact'][inflow])if existing else X(seed['lifetime_transfers_exact'][inflow]);cost=F(data['costs'][cost_key][i])
            rows[key+'_geometry']=((b[offset+i]-geometry_origin,-lifetime[key+'_realized']),Fraction(0),Fraction(0),unit)
            rows[key+'_partition']=((lifetime[key+'_extension'],lifetime[key+'_unmapped'],-lifetime[inflow]+flow_origin),Fraction(0),Fraction(0),MASS)
            rows[key+'_construction']=((lifetime[key+'_extension'],-cost*lifetime[key+'_realized']/floor),Fraction(0),Fraction(0),MASS)
            if kind=='internode':
                birth=node['baseline'];rows[key+'_age']=((b[size+i]-X(birth['thermal_age_exact']),-(lifetime['indoor_air_temperature_time']-X(birth['air_temperature_integral_exact'])-F(birth['base_temperature']['value'])*(at-X(birth['at_elapsed_seconds_exact'])))/86400),Fraction(0),Fraction(0),'degC_day')
    return rows


def packet(context,data,cp,state,transfers,rhs,duration,steps):
    p=data['program'];seed=data['seed'];initial=seed['initial_sample'];organs=data['organs'];size=seed['state_layout']['original_prefix_length'];at=X(cp['at']['elapsed_seconds_exact'])+duration
    units=resume.books.flux_units(p,organs);partial={k:F(v)for k,v in zip(units,transfers,strict=True)}
    branch={k:F(cp['branch_integrated_transfers'][k]['value'])+partial[k]for k in units};lifetime={k:X(cp['lifetime_transfers_exact'][k])+partial[k]for k in units}
    a,b=tuple(map(F,cp['last_confirmed']['state'])),tuple(map(F,state));a0=tuple(map(F,initial['state']));model_data=projection(data)
    local_rows={**algebra._physical(model_data,a[:size],b[:size],partial,cp['last_confirmed']['derived'],rhs['derived'],duration),**algebra._geometry(model_data,a,b,partial,duration)}
    local={k:resume.books.base._row(terms,start,end,unit,steps)for k,(terms,start,end,unit)in local_rows.items()}
    branch_duration=at-X(initial['at']['elapsed_seconds_exact'])
    branch_rows={**algebra._physical(model_data,a0[:size],b[:size],branch,initial['derived'],rhs['derived'],branch_duration),**algebra._geometry(model_data,a0,b,branch,branch_duration)}
    global_rows=_global_rows(context,data,state,lifetime,rhs['derived'],at)
    need(set(local)==set(branch_rows)==set(global_rows)==set(cp['global_ledgers'])==set(cp['branch_ledgers']),'BALANCE_HOLD: complete actual newborn candidate accounts required')
    books={}
    for label,rows in [('branch',branch_rows),('global',global_rows)]:
        result={}
        for k,(terms,_,_,unit)in rows.items():
            residual=sum(terms,Fraction(0));expected=X(cp[label+'_ledgers'][k]['residual_exact'])+X(local[k]['residual_exact']);budget=X(cp[label+'_ledgers'][k]['budget_exact'])+X(local[k]['budget_exact'])
            need(residual==expected and abs(residual)<=budget,'BALANCE_HOLD: exact current plus partial newborn '+label+' '+k)
            result[k]={'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}
        books[label+'_ledgers']=result
    age=X(cp['schedule']['age_exact'])+(partial['indoor_air_temperature_time']-F(data['shoot_base_temperature'])*duration)/86400;residual=age-X(cp['schedule']['next_threshold_exact']);diagnostics={}
    for kind,rows,unit in [('leaf',organs['leaves'],'m2'),('internode',organs['internodes'],'m')]:
        for i,node in enumerate(rows):
            key=f'{kind}_{i}';pot,real=branch[key+'_potential'],branch[key+'_realized'];need(pot>=real>=0 and lifetime[key+'_potential']>=lifetime[key+'_realized']>=0,'CONSTRAINT_HOLD: nonnegative actual branch/lifetime deficit required')
            diagnostics[key]={'potential_exact':Q(pot,unit),'realized_exact':Q(real,unit),'deficit_exact':Q(pot-real,unit),'lifetime_potential_exact':Q(lifetime[key+'_potential'],unit),'lifetime_realized_exact':Q(lifetime[key+'_realized'],unit),'lifetime_deficit_exact':Q(lifetime[key+'_potential']-lifetime[key+'_realized'],unit)}
            if kind=='leaf':
                n=len(p['leaves']);curve=p['leaves'][i]['curve'];now=source.stock.short.old.leaf_area._area_at(b[106+i],curve)['value'];before=source.stock.short.old.leaf_area._area_at(a0[106+i],curve)['value'];actual=b[106+n+i]
            else:
                h=len(rows)
                def length(thermal_age):return resume.resume.bound.length.calculate_internode_length_point(inputs={'input_id':node['compartment_id'],'origin':'synthetic','thermal_age_basis':'since_internode_emergence','age_exact':Q(thermal_age,'degC_day'),'curve':node['curve']})['length']['value']
                now,before=length(b[size+i]),length(a0[size+i]);actual=b[size+h+i]
            diagnostics[key].update(canonical_gap_exact=Q(actual-F(now),unit),canonical_potential_difference_exact=Q(F(now)-F(before)-pot,unit))
    return {**resume._sample(data,at,state,rhs),'partial_interval_transfers':{k:source.numeric._q(v,unit)for(k,unit),v in zip(units.items(),transfers,strict=True)},
        'pending_branch_transfers_exact':{k:Q(v,units[k])for k,v in branch.items()},'pending_lifetime_transfers_exact':{k:Q(v,units[k])for k,v in lifetime.items()},
        'point_totals_exact':deepcopy(cp['point_totals_exact']),'local_ledgers':local,**books,'geometry_diagnostics':diagnostics,
        'shoot_age_exact':Q(age,'degC_day'),'shoot_threshold_residual_exact':Q(residual,'degC_day'),'represented_threshold_status':'crossed'if residual>=0 else'not_crossed'}
