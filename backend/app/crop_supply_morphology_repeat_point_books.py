"""Point conservation and unadopted physical/geometry global preview."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_supply_morphology_repeat_point_core as core

source,resume=core.source,core.resume
F,Q,X=core.F,core.Q,core.X
MASS=core.MASS
need=core.need
balance=source.capture.point._balance
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def calculate(context,data,calculation,jump):
    before=calculation['dense_candidate'];p=jump['program'];z=jump['state'];derived=jump['evaluation']['derived'];n=len(data['program']['leaves']);nn=len(p['leaves']);m=len(data['program']['stem_root_compartments'])
    old_size=106+3*n+m;size=106+3*nn+len(p['stem_root_compartments']);a=tuple(map(F,before['state'][:old_size]));b=tuple(map(F,z[:size]));components=jump['components']
    units={k:v['unit']for k,v in components['internode'].items()};flows={k:sum((F(row[k]['value'])for row in components.values()),Fraction(0))for k in units}
    carbon=lambda v,count:sum((v[0],*v[3:53],*v[106+2*count:]),Fraction(0));ca=F(before['derived']['air_capacity']['value']);need(ca==F(derived['air_capacity']['value']),'BALANCE_HOLD: same air heat capacity required')
    latent=F(data['profiles']['exchange_profile'].values['latent_heat']);ref=F(p['scenario']['parameters']['reference_temperature']['value']);energy=lambda v:v[103]+ca*(v[104]-ref)+latent*v[105]
    terms={
        'buffer':((b[0],-a[0],flows['buffer_debit']),MASS),'whole_carbohydrate':((carbon(b,nn),-carbon(a,n),flows['growth_respiration']),MASS),
        'new_internode':((b[-1],-F(components['internode']['structural_carbon']['value'])),MASS),
        'stem_root_carbon':((sum(b[106+3*nn:]),-sum(a[106+3*n:]),-F(components['internode']['structural_carbon']['value'])),MASS),
        'capacity':((F(derived['canopy_capacity']['value']),-F(before['derived']['canopy_capacity']['value']),-flows['capacity_in']),core.numeric.CAPACITY),
        'canopy_sensible':((b[103],-a[103],-flows['sensible_in']),core.numeric.ENERGY),'air_sensible':((ca*b[104],-ca*a[104]),core.numeric.ENERGY),
        'vapor':((b[105],-a[105]),'kg_water/m2_floor'),'fruit_number':((sum(b[53:103]),-sum(a[53:103])),'fruits_equivalent/m2_floor'),
        'reduced_energy':((energy(b),-energy(a),-flows['sensible_in']),core.numeric.ENERGY)}
    if nn>n:terms['new_leaf']=((b[106+2*nn+n],-F(components['leaf']['structural_carbon']['value'])),MASS)
    point={k:balance(values,unit)for k,(values,unit)in terms.items()}
    # Existing coordinates move only by declared insertions; only buffer/U may jump.
    h=len(data['organs']['internodes']);nh=h+1
    need(z[1:103]==list(a[1:103])and z[104:106]==list(a[104:106]),'STATE_HOLD: original plant/cohorts/air/vapor required')
    for old_start,new_start,count in [(106,106,n),(106+n,106+nn,n),(106+2*n,106+2*nn,n),(106+3*n,106+3*nn,m),
        (old_size,size,h),(old_size+h,size+nh,h)]:
        need(z[new_start:new_start+count]==before['state'][old_start:old_start+count],'STATE_HOLD: original organ age/area/C/length required')
    if nn==n:need(z[103]==before['state'][103]and derived['canopy_capacity']==before['derived']['canopy_capacity'],'STATE_HOLD: no leaf means no thermal point')
    deltas={**flows,'stem_structural_carbon':F(components['internode']['structural_carbon']['value']),
        'leaf_structural_carbon':F(components['leaf']['structural_carbon']['value'])if nn>n else Fraction(0)}
    need(set(deltas)==set(before['point_totals_exact']),'BALANCE_HOLD: original complete point totals required')
    points={k:X(q)+deltas[k]for k,q in before['point_totals_exact'].items()}
    lifetime={k:X(before['pending_lifetime_transfers_exact'][k])if k in before['pending_lifetime_transfers_exact']else Fraction(0)for k in resume.books.flux_units(p,jump['organs'])}
    root_p,root_seed=data['root_program'],data['root_seed'];root=tuple(map(F,root_seed['state']));first=source.stock.short._view(root_seed['evaluation'])['joint']['derived']
    rows=source.candidate._physical(p,root,b,lifetime,first,derived,float(latent),len(root_p['leaves']),points)
    bases=deepcopy(data['seed']['birth_bases'])
    for kind in ['leaf','stem_root']:bases[kind].extend(deepcopy(jump['new_birth_baselines'][kind]))
    at=X(calculation['at']['elapsed_seconds_exact'])
    for i,base in enumerate(bases['leaf']):
        rows[f'leaf_age_{i}']=((b[106+i]-X(base['thermal_age_exact']),-(lifetime['indoor_air_temperature_time']-X(base['air_temperature_integral_exact'])-F(base['base_temperature']['value'])*(at-X(base['at_elapsed_seconds_exact'])))/86400),Fraction(0),Fraction(0),'degC_day')
    for kind,start in [('leaf',106+2*nn),('stem_root',106+3*nn)]:
        for i,base in enumerate(bases[kind]):rows[f'{kind}_carbon_{i}']=((b[start+i]-F(base['carbon']['value']),-lifetime[f'{kind}_{i}_inflow'],lifetime[f'{kind}_{i}_maintenance'],lifetime[f'{kind}_{i}_removal']),Fraction(0),Fraction(0),MASS)
    rows['stem_root_carbon']=((sum(b[106+3*nn:])-sum(root[106+3*len(root_p['leaves']):]),-sum(lifetime[f'stem_root_{i}_inflow']for i in range(len(p['stem_root_compartments']))),
        sum(lifetime[f'stem_root_{i}_maintenance']+lifetime[f'stem_root_{i}_removal']for i in range(len(p['stem_root_compartments']))),-points['stem_structural_carbon']),Fraction(0),Fraction(0),MASS)
    mapping={'carbohydrate':'whole_carbohydrate','number':'fruit_number','canopy_sensible':'canopy_sensible','air_sensible':'air_sensible','vapor':'vapor','area_capacity':'capacity','reduced_energy':'reduced_energy','stem_root_carbon':'stem_root_carbon'}
    preview={};zero=lambda unit:{'residual_exact':Q(Fraction(0),unit),'budget_exact':Q(Fraction(0),unit)}
    for name,(values,_,_,unit)in rows.items():
        r=sum(values,Fraction(0));old=before['global_ledgers'].get(name,zero(unit));delta=point[mapping[name]]if name in mapping else(point['new_leaf']if name==f'leaf_carbon_{n}'and nn>n else point['new_internode']if name==f'stem_root_carbon_{m}'else zero(unit))
        expected=X(old['residual_exact'])+X(delta['residual_exact']);budget=X(old['budget_exact'])+X(delta['budget_exact'])
        need(r==expected and abs(r)<=budget,'BALANCE_HOLD: original global plus actual point '+name)
        preview[name]={'residual_exact':Q(r,unit),'budget_exact':Q(budget,unit)}
    for name,row in before['global_ledgers'].items():
        if name not in preview:preview[name]=deepcopy(row)
    for kind,index,unit in [('internode',h,'m'),*([('leaf',n,'m2')]if nn>n else [])]:
        for suffix in ['geometry','partition','construction']:preview[f'{kind}_{index}_{suffix}']=zero(unit if suffix=='geometry'else MASS)
        if kind=='internode':preview[f'{kind}_{index}_age']=zero('degC_day')
    for kind,offset,rows_meta in [('leaf',106,jump['organs']['leaves']),('internode',size,jump['organs']['internodes'])]:
        for i,meta in enumerate(rows_meta):
            base=meta['baseline'];age=X(base['thermal_age_exact'])+(lifetime['indoor_air_temperature_time']-X(base['air_temperature_integral_exact'])-F(base['base_temperature']['value'])*(at-X(base['at_elapsed_seconds_exact'])))/86400
            residual=F(z[offset+i])-age;ledger=preview['leaf_age_'+str(i)if kind=='leaf'else f'internode_{i}_age']
            need(residual==X(ledger['residual_exact'])and abs(residual)<=X(ledger['budget_exact']),'CLOCK_HOLD: actual post-point current organ clock required')
            meta.update(age_exact=Q(age,'degC_day'),represented_age=core.numeric._q(z[offset+i],'degC_day'),represented_minus_clock_exact=Q(residual,'degC_day'),age_roundoff_budget_exact=deepcopy(ledger['budget_exact']))
    return {'point_balances':point,'point_flows_exact':{k:Q(v,units[k])for k,v in flows.items()},
        'post_point_global_ledgers_preview':preview,'post_point_point_totals_exact_preview':{k:Q(v,before['point_totals_exact'][k]['unit'])for k,v in points.items()},
        'post_point_lifetime_transfers_exact_preview':{k:Q(v,resume.books.flux_units(p,jump['organs'])[k])for k,v in lifetime.items()},'after_birth_baselines':bases,'after_geometry_baselines':geometry_origins(data,calculation,jump),
        'preview_scope':'unadopted_original_global_plus_point_and_explicit_new_geometry_birth_baselines'}


def geometry_origins(data,calculation,jump):
    result=deepcopy(data['seed']['geometry_baselines']);n=len(data['program']['leaves']);h=len(data['organs']['internodes'])
    nn=len(jump['program']['leaves']);hh=len(jump['organs']['internodes']);size=106+3*nn+len(jump['program']['stem_root_compartments'])
    for key,rows,start,offset,identifier,unit in [('leaves',jump['organs']['leaves'],n,106+nn,'leaf_id','m2'),('internodes',jump['organs']['internodes'],h,size+hh,'compartment_id','m')]:
        need(len(result[key])==start and all(a[identifier]==b[identifier]for a,b in zip(result[key],rows[:start],strict=True)),'ORIGIN_HOLD: all original ordered geometry origins required')
        for i in range(start,len(rows)):
            result[key].append({identifier:rows[i][identifier],'origin_geometry':core.numeric._q(jump['state'][offset+i],unit),
                'origin_lifetime_inflow_exact':Q(Fraction(0),MASS),'origin_elapsed_seconds_exact':deepcopy(calculation['at']['elapsed_seconds_exact']),'origin':'current_material_seed'})
    return result
