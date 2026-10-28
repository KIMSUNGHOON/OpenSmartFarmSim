"""Exact current-plus-partial accounts for new-law fractional candidates."""
from copy import deepcopy
from fractions import Fraction

from . import crop_supply_morphology_resume as resume

source=resume.source
F,Q,X=resume.F,resume.Q,resume.X
need=resume._need
MASS=resume.books.MASS


def _physical(data,a,b,t,first,last,duration):
    p=data['program'];n=len(p['leaves']);m=len(p['stem_root_compartments'])
    rows=source.candidate._physical(p,a,b,t,first,last,data['profiles']['exchange_profile'].values['latent_heat'],n,{})
    for i,leaf in enumerate(p['leaves']):
        rows[f'leaf_age_{i}']=((b[106+i]-a[106+i],-(t['indoor_air_temperature_time']-F(leaf['base_temperature']['value'])*duration)/86400),a[106+i],b[106+i],'degC_day')
    for kind,start,count in [('leaf',106+2*n,n),('stem_root',106+3*n,m)]:
        for i in range(count):rows[f'{kind}_carbon_{i}']=((b[start+i]-a[start+i],-t[f'{kind}_{i}_inflow'],t[f'{kind}_{i}_maintenance'],t[f'{kind}_{i}_removal']),a[start+i],b[start+i],MASS)
    rows['stem_root_carbon']=((sum(b[106+3*n:])-sum(a[106+3*n:]),-sum(t[f'stem_root_{i}_inflow']for i in range(m)),sum(t[f'stem_root_{i}_maintenance']+t[f'stem_root_{i}_removal']for i in range(m))),sum(a[106+3*n:]),sum(b[106+3*n:]),MASS)
    return rows


def _geometry(data,a,b,t,duration):
    organs=data['initial']['organs'];n=len(data['program']['leaves']);h=len(organs['internodes']);size=data['initial']['state_layout']['original_prefix_length']
    floor=F(data['program']['model_floor_area']['value']);rows={}
    for kind,meta,offset,unit,key in [('leaf',organs['leaves'],106+n,'m2','leaves'),('internode',organs['internodes'],size+h,'m','internodes')]:
        for i,organ in enumerate(meta):
            k=f'{kind}_{i}';s,e=a[offset+i],b[offset+i];real=t[k+'_realized'];potential=t[k+'_potential'];cost=F(data['costs'][key][i])
            need(potential>=real>=0,'CONSTRAINT_HOLD: nonnegative candidate potential deficit required')
            g=t[('leaf'if kind=='leaf'else'stem_root')+'_'+str(i if kind=='leaf'else data['stem_stock_indices'][i])+'_inflow']
            rows[k+'_geometry']=((e-s,-real),s,e,unit)
            rows[k+'_partition']=((t[k+'_extension'],t[k+'_unmapped'],-g),Fraction(0),Fraction(0),MASS)
            rows[k+'_construction']=((t[k+'_extension'],-cost*real/floor),Fraction(0),Fraction(0),MASS)
            if kind=='internode':
                rows[k+'_age']=((b[size+i]-a[size+i],-(t['indoor_air_temperature_time']-F(organ['baseline']['base_temperature']['value'])*duration)/86400),a[size+i],b[size+i],'degC_day')
    return rows


def _root_physical(context,data,b,t,last,at):
    p=data['program'];n=len(p['leaves']);m=len(p['stem_root_compartments']);root_p,root_seed,_=source.stock.parent._context(context._source._source._root)
    a=tuple(map(F,root_seed['state']));first=source.stock.short._view(root_seed['evaluation'])['joint']['derived'];points={k:X(v)for k,v in data['parent']['point_totals_exact'].items()}
    rows=source.candidate._physical(p,a,b,t,first,last,data['profiles']['exchange_profile'].values['latent_heat'],len(root_p['leaves']),points)
    bases=data['source_data']['captured']['birth_bases']
    for i,base in enumerate(bases['leaf']):
        rows[f'leaf_age_{i}']=((b[106+i]-X(base['thermal_age_exact']),-(t['indoor_air_temperature_time']-X(base['air_temperature_integral_exact'])-F(base['base_temperature']['value'])*(at-X(base['at_elapsed_seconds_exact'])))/86400),Fraction(0),Fraction(0),'degC_day')
    for kind,start in [('leaf',106+2*n),('stem_root',106+3*n)]:
        for i,base in enumerate(bases[kind]):rows[f'{kind}_carbon_{i}']=((b[start+i]-F(base['carbon']['value']),-t[f'{kind}_{i}_inflow'],t[f'{kind}_{i}_maintenance'],t[f'{kind}_{i}_removal']),Fraction(0),Fraction(0),MASS)
    rows['stem_root_carbon']=((sum(b[106+3*n:])-sum(a[106+3*len(root_p['leaves']):]),-sum(t[f'stem_root_{i}_inflow']for i in range(m)),sum(t[f'stem_root_{i}_maintenance']+t[f'stem_root_{i}_removal']for i in range(m)),-points['stem_structural_carbon']),Fraction(0),Fraction(0),MASS)
    return rows


def packet(context,data,cp,state,transfers,rhs,duration,steps):
    p=data['program'];initial=data['initial'];size=initial['state_layout']['original_prefix_length'];at=X(cp['at']['elapsed_seconds_exact'])+duration
    units=resume.books.flux_units(p,initial['organs']);partial={k:F(v)for k,v in zip(units,transfers,strict=True)}
    branch={k:F(cp['branch_integrated_transfers'][k]['value'])+partial[k]for k in units}
    lifetime={k:X(v)+partial[k]for k,v in cp['lifetime_transfers_exact'].items()}
    a,b=tuple(map(F,cp['last_confirmed']['state'])),tuple(map(F,state));a0=tuple(map(F,initial['state']))
    local_rows={**_physical(data,a[:size],b[:size],partial,cp['last_confirmed']['derived'],rhs['derived'],duration),**_geometry(data,a,b,partial,duration)}
    local={k:resume.books._row(terms,start,end,unit,steps)for k,(terms,start,end,unit)in local_rows.items()}
    branch_duration=at-X(data['parent']['at']['elapsed_seconds_exact'])
    branch_rows={**_physical(data,a0[:size],b[:size],branch,initial['stage']['derived'],rhs['derived'],branch_duration),**_geometry(data,a0,b,branch,branch_duration)}
    global_rows=_root_physical(context,data,b[:size],lifetime,rhs['derived'],at)
    for k,row in branch_rows.items():
        if k not in global_rows:
            terms,start,end,unit=row
            if k.startswith('internode_')and k.endswith('_age'):
                baseline=initial['organs']['internodes'][int(k.split('_')[1])]['represented_minus_clock_exact'];terms=(*terms,X(baseline))
            global_rows[k]=(terms,start,end,unit)
    need(set(local)==set(branch_rows)==set(global_rows)==set(cp['global_ledgers'])==set(cp['branch_ledgers']),'BALANCE_HOLD: complete current and candidate accounts required')
    books={}
    for label,rows in [('branch',branch_rows),('global',global_rows)]:
        result={}
        for k,(terms,_,_,unit)in rows.items():
            residual=sum(terms,Fraction(0));expected=X(cp[label+'_ledgers'][k]['residual_exact'])+X(local[k]['residual_exact']);budget=X(cp[label+'_ledgers'][k]['budget_exact'])+X(local[k]['budget_exact'])
            need(residual==expected and abs(residual)<=budget,'BALANCE_HOLD: exact current plus partial '+label+' '+k)
            result[k]={'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}
        books[label+'_ledgers']=result
    age=X(cp['schedule']['age_exact'])+(partial['indoor_air_temperature_time']-F(data['shoot_base_temperature'])*duration)/86400
    residual=age-X(cp['schedule']['next_threshold_exact']);diagnostics={}
    for kind,rows,unit in [('leaf',initial['organs']['leaves'],'m2'),('internode',initial['organs']['internodes'],'m')]:
        for i,organ in enumerate(rows):
            k=f'{kind}_{i}';pot,real=branch[k+'_potential'],branch[k+'_realized'];diagnostics[k]={'potential_exact':Q(pot,unit),'realized_exact':Q(real,unit),'deficit_exact':Q(pot-real,unit)}
            if kind=='leaf':
                n=len(p['leaves']);curve=p['leaves'][i]['curve'];now=source.stock.short.old.leaf_area._area_at(b[106+i],curve)['value'];before=source.stock.short.old.leaf_area._area_at(a0[106+i],curve)['value'];actual=b[106+n+i]
            else:
                h=len(rows);now=resume.bound.length.calculate_internode_length_point(inputs={'input_id':organ['compartment_id'],'origin':'synthetic','thermal_age_basis':'since_internode_emergence','age_exact':Q(b[size+i],'degC_day'),'curve':organ['curve']})['length']['value'];before=organ['legacy_length']['value'];actual=b[size+h+i]
            diagnostics[k]['canonical_gap_exact']=Q(actual-F(now),unit)
            diagnostics[k]['canonical_potential_difference_exact']=Q(F(now)-F(before)-pot,unit)
    return {**resume._sample(data,at,state,rhs),'partial_interval_transfers':{k:source.numeric._q(v,unit)for(k,unit),v in zip(units.items(),transfers,strict=True)},
        'pending_branch_transfers_exact':{k:Q(v,units[k])for k,v in branch.items()},'pending_lifetime_transfers_exact':{k:Q(v,units[k])for k,v in lifetime.items()},
        'point_totals_exact':deepcopy(cp['point_totals_exact']),'local_ledgers':local,**books,'geometry_diagnostics':diagnostics,
        'shoot_age_exact':Q(age,'degC_day'),'shoot_threshold_residual_exact':Q(residual,'degC_day'),'represented_threshold_status':'crossed'if residual>=0 else'not_crossed'}
