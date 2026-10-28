"""Exact physical and construction accounts for the supply-limited solver."""
from fractions import Fraction
from math import ulp

from . import crop_supply_morphology_rhs as bound

source=bound.source
numeric=source.numeric
F=Fraction.from_float
Q,X=source.Q,source.X
need=bound.need
MASS='mg_CH2O/m2_floor'


def flux_units(p,organs):
    units=dict(source.stock.short._flux_units(p))
    for kind,rows,unit in [('leaf',organs['leaves'],'m2'),('internode',organs['internodes'],'m')]:
        for i,_ in enumerate(rows):
            for name in ['potential','realized']:units[f'{kind}_{i}_{name}']=unit
            for name in ['extension','unmapped']:units[f'{kind}_{i}_{name}']=MASS
    return units


def flux(p,y,r,organs):
    c=r['crop'];f=p['scenario']['forcing'];x=r['exchange']['exchange'];m=r['capacity_transport']
    flow={'photosynthesis':c['photosynthesis']['value'],'growth_respiration':r['growth_respiration']['value'],
        'maintenance_leaf':numeric._sum(*(row['maintenance']['value']for row in r['leaves'])),
        'maintenance_stem':numeric._sum(*(row['maintenance']['value']for row in r['stem_root_stocks'])),
        'maintenance_fruit':c['fruit_maintenance']['value'],'removal_leaf':0.,'removal_stem':0.,
        'terminal_carbon':c['cohorts']['terminal_outflow']['fruit_carbohydrate']['value'],
        'entry_number':p['scenario']['fruit_entry']['fruit_number_inflow']['value'],
        'terminal_number':c['cohorts']['terminal_outflow']['fruit_number']['value'],
        'sensible':x['sensible_heat']['value'],'latent':x['latent_heat']['value'],
        'incoming_heat':m['energy_flows']['incoming']['value'],'outgoing_heat':m['energy_flows']['outgoing']['value'],
        'canopy_external':f['canopy_external_heat']['value'],'air_external':f['air_external_sensible_heat']['value'],
        'vapor':x['water_vapor']['value'],'external_vapor':f['air_external_vapor']['value'],
        'capacity_in':m['capacity_rates']['incoming']['value'],'capacity_out':m['capacity_rates']['outgoing']['value'],
        'indoor_air_temperature_time':y[104]}
    for kind,rows in [('leaf',r['leaves']),('stem_root',r['stem_root_stocks'])]:
        for i,row in enumerate(rows):
            for name in ['inflow','maintenance','removal']:flow[f'{kind}_{i}_{name}']=row[name]['value']
    for kind,rows in [('leaf',r['leaves']),('internode',r['internodes'])]:
        for i,row in enumerate(rows):
            for name,field in [('potential','potential_rate'),('realized','realized_rate'),('extension','extension_inflow'),('unmapped','unmapped_inflow')]:
                flow[f'{kind}_{i}_{name}']=row[field]['value']
    return tuple(flow[name]for name in flux_units(p,organs))


def _row(terms,start,end,unit,steps):
    residual=sum(terms,Fraction(0));scale=max(abs(start),abs(end),sum(map(abs,terms),Fraction(0)))
    budget=64*(steps+1)*F(ulp(float(scale)))if steps and scale else Fraction(0)
    need(abs(residual)<=budget,'BALANCE_HOLD: unresolved supply integration '+unit)
    return {'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}


def calculate(context,data,y,rhs,totals,steps,at):
    p=data['program'];initial=data['initial'];cp=data['parent'];organs=initial['organs'];n=len(p['leaves']);m=len(p['stem_root_compartments'])
    size=initial['state_layout']['original_prefix_length'];a0=initial['state'];duration=at-X(cp['at']['elapsed_seconds_exact'])
    units=flux_units(p,organs);t={name:F(v)for name,v in zip(units,totals,strict=True)}
    old_names=source.stock.short._flux_units(p);latent=data['profiles']['exchange_profile'].values['latent_heat']
    local=source.candidate._local(p,a0[:size],y[:size],tuple(float(t[k])for k in old_names),initial['stage']['derived'],rhs['derived'],duration,latent,steps)
    if steps==0:
        need(all(X(row['residual_exact'])==0 for row in local.values()),'BALANCE_HOLD: exact zero physical branch required')
        local={k:{'residual_exact':row['residual_exact'],'budget_exact':Q(Fraction(0),row['budget_exact']['unit'])}for k,row in local.items()}
    lifetime={k:X(cp['lifetime_transfers_exact'][k])+t[k]for k in old_names}
    root_p,root_seed,_=source.stock.parent._context(context._source._source._root)
    a,b=tuple(map(F,root_seed['state'])),tuple(map(F,y[:size]));n0=len(root_p['leaves'])
    first=source.stock.short._view(root_seed['evaluation'])['joint']['derived'];points={k:X(v)for k,v in cp['point_totals_exact'].items()}
    rows=source.candidate._physical(p,a,b,lifetime,first,rhs['derived'],latent,n0,points)
    bases=data['source_data']['captured']['birth_bases']
    for i,base in enumerate(bases['leaf']):
        elapsed=at-X(base['at_elapsed_seconds_exact'])
        rows[f'leaf_age_{i}']=((b[106+i]-X(base['thermal_age_exact']),-(lifetime['indoor_air_temperature_time']-X(base['air_temperature_integral_exact'])-F(base['base_temperature']['value'])*elapsed)/86400),Fraction(0),Fraction(0),'degC_day')
    for kind,start in [('leaf',106+2*n),('stem_root',106+3*n)]:
        for i,base in enumerate(bases[kind]):
            rows[f'{kind}_carbon_{i}']=((b[start+i]-F(base['carbon']['value']),-lifetime[f'{kind}_{i}_inflow'],lifetime[f'{kind}_{i}_maintenance'],lifetime[f'{kind}_{i}_removal']),Fraction(0),Fraction(0),MASS)
    rows['stem_root_carbon']=((sum(b[106+3*n:])-sum(a[106+3*n0:]),-sum(lifetime[f'stem_root_{i}_inflow']for i in range(m)),
        sum(lifetime[f'stem_root_{i}_maintenance']+lifetime[f'stem_root_{i}_removal']for i in range(m)),-points['stem_structural_carbon']),Fraction(0),Fraction(0),MASS)
    need(set(rows)==set(cp['global_ledgers'])==set(local),'BALANCE_HOLD: complete original physical accounts required')
    global_books={}
    for name,(terms,_,_,unit)in rows.items():
        residual=sum(terms,Fraction(0));expected=X(cp['global_ledgers'][name]['residual_exact'])+X(local[name]['residual_exact'])
        budget=X(cp['global_ledgers'][name]['budget_exact'])+X(local[name]['budget_exact'])
        need(residual==expected and abs(residual)<=budget,'BALANCE_HOLD: exact source plus new branch '+name)
        global_books[name]={'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}
    diagnostics={};h=len(organs['internodes']);floor=F(p['model_floor_area']['value'])
    for kind,meta,offset,unit in [('leaf',organs['leaves'],106+n,'m2'),('internode',organs['internodes'],size+h,'m')]:
        for i,row in enumerate(meta):
            key=f'{kind}_{i}';start,end=F(a0[offset+i]),F(y[offset+i]);real=t[key+'_realized'];potential=t[key+'_potential']
            cost=F(data['costs']['leaves'if kind=='leaf'else'internodes'][i])
            extra={key+'_geometry':_row((end-start,-real),start,end,unit,steps),
                key+'_partition':_row((t[key+'_extension'],t[key+'_unmapped'],-t[('leaf'if kind=='leaf'else'stem_root')+'_'+str(i if kind=='leaf'else data['stem_stock_indices'][i])+'_inflow']),Fraction(0),Fraction(0),MASS,steps),
                key+'_construction':_row((t[key+'_extension'],-cost*real/floor),Fraction(0),Fraction(0),MASS,steps)}
            need(potential>=real>=0,'CONSTRAINT_HOLD: nonnegative integrated potential deficit required')
            diagnostics[key]={'potential_exact':Q(potential,unit),'realized_exact':Q(real,unit),'deficit_exact':Q(potential-real,unit)}
            if kind=='leaf':
                curve=p['leaves'][i]['curve'];now=source.stock.short.old.leaf_area._area_at(F(y[106+i]),curve)['value'];before=source.stock.short.old.leaf_area._area_at(F(a0[106+i]),curve)['value']
                diagnostics[key]['canonical_gap_exact']=Q(end-F(now),unit)
            else:
                curve=row['curve'];now=bound.length.calculate_internode_length_point(inputs={'input_id':row['compartment_id'],'origin':'synthetic','thermal_age_basis':'since_internode_emergence','age_exact':Q(F(y[size+i]),'degC_day'),'curve':curve})['length']['value']
                before=row['legacy_length']['value']
                local_age=_row((F(y[size+i])-F(a0[size+i]),-(t['indoor_air_temperature_time']-F(row['baseline']['base_temperature']['value'])*duration)/86400),F(a0[size+i]),F(y[size+i]),'degC_day',steps)
                extra[key+'_age']=local_age
            diagnostics[key]['canonical_potential_difference_exact']=Q(F(now)-F(before)-potential,unit)
            for name,value in extra.items():local[name]=value;global_books[name]=dict(value)
            if kind=='internode':
                name=key+'_age';residual=X(row['represented_minus_clock_exact'])+X(extra[name]['residual_exact']);budget=X(row['age_roundoff_budget_exact'])+X(extra[name]['budget_exact'])
                need(abs(residual)<=budget,'CLOCK_HOLD: internode initial plus branch roundoff')
                global_books[name]={'residual_exact':Q(residual,'degC_day'),'budget_exact':Q(budget,'degC_day')}
    return local,global_books,diagnostics,lifetime
