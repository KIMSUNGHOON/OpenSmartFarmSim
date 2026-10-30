"""Exact post-material branch and original-origin lifetime conservation accounts."""
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_supply_morphology_repeat_context as owner

resume=owner.resume.resume
source=owner.source
base=resume.books
F,Q,X=owner.F,owner.Q,owner.X
MASS=base.MASS
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
flux_units,flux=base.flux_units,base.flux


def calculate(context,data,y,rhs,totals,steps,at):
    seed=data['seed'];p=seed['program'];organs=seed['organs'];initial=seed['initial_sample'];a0=initial['state']
    n=len(p['leaves']);m=len(p['stem_root_compartments']);h=len(organs['internodes']);size=seed['state_layout']['original_prefix_length']
    units=flux_units(p,organs);t={k:F(v)for k,v in zip(units,totals,strict=True)}
    lifetime={k:X(seed['lifetime_transfers_exact'][k])+v for k,v in t.items()};duration=at-X(initial['at']['elapsed_seconds_exact'])
    physical=source.stock.short._flux_units(p);latent=data['profiles']['exchange_profile'].values['latent_heat']
    local=source.candidate._local(p,a0[:size],y[:size],tuple(float(t[k])for k in physical),initial['derived'],rhs['derived'],duration,latent,steps)
    if steps==0:
        resume._need(all(X(v['residual_exact'])==0 for v in local.values()),'BALANCE_HOLD: exact zero post-material branch required')
        local={k:{'residual_exact':v['residual_exact'],'budget_exact':Q(Fraction(0),v['budget_exact']['unit'])}for k,v in local.items()}
    root_p,root_seed=data['root_program'],data['root_seed']
    a,b=tuple(map(F,root_seed['state'])),tuple(map(F,y[:size]));first=source.stock.short._view(root_seed['evaluation'])['joint']['derived']
    points={k:X(v)for k,v in seed['point_totals_exact'].items()}
    rows=source.candidate._physical(p,a,b,lifetime,first,rhs['derived'],latent,len(root_p['leaves']),points)
    for i,birth in enumerate(seed['birth_bases']['leaf']):
        elapsed=at-X(birth['at_elapsed_seconds_exact'])
        rows[f'leaf_age_{i}']=((b[106+i]-X(birth['thermal_age_exact']),-(lifetime['indoor_air_temperature_time']-X(birth['air_temperature_integral_exact'])-F(birth['base_temperature']['value'])*elapsed)/86400),Fraction(0),Fraction(0),'degC_day')
    for kind,start in [('leaf',106+2*n),('stem_root',106+3*n)]:
        for i,birth in enumerate(seed['birth_bases'][kind]):rows[f'{kind}_carbon_{i}']=((b[start+i]-F(birth['carbon']['value']),-lifetime[f'{kind}_{i}_inflow'],lifetime[f'{kind}_{i}_maintenance'],lifetime[f'{kind}_{i}_removal']),Fraction(0),Fraction(0),MASS)
    rows['stem_root_carbon']=((sum(b[106+3*n:])-sum(a[106+3*len(root_p['leaves']):]),-sum(lifetime[f'stem_root_{i}_inflow']for i in range(m)),
        sum(lifetime[f'stem_root_{i}_maintenance']+lifetime[f'stem_root_{i}_removal']for i in range(m)),-points['stem_structural_carbon']),Fraction(0),Fraction(0),MASS)
    diagnostics={};floor=F(p['model_floor_area']['value'])
    for kind,meta,offset,unit in [('leaf',organs['leaves'],106+n,'m2'),('internode',organs['internodes'],size+h,'m')]:
        origins=seed['geometry_baselines']['leaves'if kind=='leaf'else'internodes']
        for i,(node,origin)in enumerate(zip(meta,origins,strict=True)):
            identifier='leaf_id'if kind=='leaf'else'compartment_id'
            resume._need(node[identifier]==origin[identifier]and origin['origin_geometry']['unit']==unit and origin['origin_lifetime_inflow_exact']['unit']==MASS,'ORIGIN_HOLD: exact ordered original geometry/inflow origins required')
            key=f'{kind}_{i}';start,end=F(a0[offset+i]),F(y[offset+i]);real,potential=t[key+'_realized'],t[key+'_potential'];cost=F(seed['costs']['leaves'if kind=='leaf'else'internodes'][i])
            stock_i=i if kind=='leaf'else data['stem_stock_indices'][i];inflow=f'{"leaf"if kind=="leaf"else"stem_root"}_{stock_i}_inflow'
            local[key+'_geometry']=base._row((end-start,-real),start,end,unit,steps)
            local[key+'_partition']=base._row((t[key+'_extension'],t[key+'_unmapped'],-t[inflow]),Fraction(0),Fraction(0),MASS,steps)
            local[key+'_construction']=base._row((t[key+'_extension'],-cost*real/floor),Fraction(0),Fraction(0),MASS,steps)
            geometry_origin=F(origin['origin_geometry']['value']);physical_origin=X(origin['origin_lifetime_inflow_exact'])
            rows[key+'_geometry']=((end-geometry_origin,-lifetime[key+'_realized']),Fraction(0),Fraction(0),unit)
            rows[key+'_partition']=((lifetime[key+'_extension'],lifetime[key+'_unmapped'],-lifetime[inflow]+physical_origin),Fraction(0),Fraction(0),MASS)
            rows[key+'_construction']=((lifetime[key+'_extension'],-cost*lifetime[key+'_realized']/floor),Fraction(0),Fraction(0),MASS)
            resume._need(potential>=real>=0 and lifetime[key+'_potential']>=lifetime[key+'_realized']>=0,'CONSTRAINT_HOLD: nonnegative branch and lifetime potential deficit required')
            diagnostics[key]={'potential_exact':Q(potential,unit),'realized_exact':Q(real,unit),'deficit_exact':Q(potential-real,unit),
                'lifetime_potential_exact':Q(lifetime[key+'_potential'],unit),'lifetime_realized_exact':Q(lifetime[key+'_realized'],unit),
                'lifetime_deficit_exact':Q(lifetime[key+'_potential']-lifetime[key+'_realized'],unit)}
            if kind=='leaf':
                curve=p['leaves'][i]['curve'];now=source.stock.short.old.leaf_area._area_at(F(y[106+i]),curve)['value'];before=source.stock.short.old.leaf_area._area_at(F(a0[106+i]),curve)['value']
            else:
                def length(age):return resume.bound.length.calculate_internode_length_point(inputs={'input_id':node['compartment_id'],'origin':'synthetic','thermal_age_basis':'since_internode_emergence','age_exact':Q(F(age),'degC_day'),'curve':node['curve']})['length']['value']
                now,before=length(y[size+i]),length(a0[size+i]);birth=node['baseline'];base_temperature=F(birth['base_temperature']['value'])
                local[key+'_age']=base._row((F(y[size+i])-F(a0[size+i]),-(t['indoor_air_temperature_time']-base_temperature*duration)/86400),F(a0[size+i]),F(y[size+i]),'degC_day',steps)
                rows[key+'_age']=((F(y[size+i])-X(birth['thermal_age_exact']),-(lifetime['indoor_air_temperature_time']-X(birth['air_temperature_integral_exact'])-base_temperature*(at-X(birth['at_elapsed_seconds_exact'])))/86400),Fraction(0),Fraction(0),'degC_day')
            diagnostics[key].update(canonical_gap_exact=Q(end-F(now),unit),canonical_potential_difference_exact=Q(F(now)-F(before)-potential,unit))
    resume._need(set(rows)==set(seed['global_ledgers'])==set(local),'BALANCE_HOLD: complete original/new global accounts required')
    global_books={}
    for name,(terms,_,_,unit)in rows.items():
        residual=sum(terms,Fraction(0));expected=X(seed['global_ledgers'][name]['residual_exact'])+X(local[name]['residual_exact']);budget=X(seed['global_ledgers'][name]['budget_exact'])+X(local[name]['budget_exact'])
        resume._need(residual==expected and abs(residual)<=budget,'BALANCE_HOLD: original global plus post-material branch '+name)
        global_books[name]={'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}
    return local,global_books,diagnostics,lifetime
