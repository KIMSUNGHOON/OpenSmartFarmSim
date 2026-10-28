"""Shared carbon/construction/climate stage; crop-supply-limited-morphology-v1.md."""
from copy import deepcopy
from fractions import Fraction
from math import exp, fsum, isfinite, ulp

from . import crop_explicit_lai_climate_rhs as joint
from . import crop_leaf_carbon_partition as leaf_partition
from . import crop_stem_root_carbon_partition as stem_partition
from . import crop_stem_root_stock_dynamics as short
from . import crop_internode_elongation as elongation

numeric = joint.numeric
F = Fraction.from_float
MASS = 'mg_CH2O/m2_floor'
RATE = MASS+'/s'
q = numeric._q


class SupplyMorphologyHold(ValueError):
    pass


def need(condition, reason):
    if not condition:
        raise SupplyMorphologyHold(reason)


def _normal(value):
    return leaf_partition._normal(value)


def _ledger(terms, unit, inherited=0.):
    residual=fsum(terms); scale=max(map(abs,terms),default=0.)
    budget=fsum((inherited,64*(len(terms)+1)*ulp(scale))) if scale else inherited
    need(isfinite(budget) and abs(residual)<=budget,'BALANCE_HOLD: unresolved supply morphology '+unit)
    return q(residual,unit),q(budget,unit)


def _classification(supply,potential,cost,floor,unit):
    need(supply>=0 and potential>=0 and cost>0 and floor>0,'DOMAIN_HOLD: nonnegative extension supply/potential and positive cost/floor required')
    demand=F(cost)*F(potential)/F(floor); extension=min(F(supply),demand)
    exact={'construction_demand':demand,'extension_inflow':extension,'unmapped_inflow':F(supply)-extension,
           'realized_rate':F(floor)*extension/F(cost)}
    values={}
    for name,value in exact.items():
        number=_normal(float(value));need(value==0 or number>0,'NUMERIC_HOLD: positive construction quantity lost')
        values[name]=q(number,unit if name=='realized_rate' else RATE)
    rate=values['realized_rate']['value'];need(0<=rate<=potential,'CONSTRAINT_HOLD: extension exceeds potential')
    residual,budget=_ledger((values['extension_inflow']['value'],values['unmapped_inflow']['value'],-supply),RATE)
    cost_res,cost_budget=_ledger((cost*rate/floor,-values['extension_inflow']['value']),RATE)
    return {'construction_cost':q(cost,'mg_CH2O/'+('m2_leaf' if unit=='m2/s' else 'm_internode')),
            'potential_rate':q(potential,unit),**values,'classification_residual':residual,'classification_budget':budget,
            'construction_residual':cost_res,'construction_budget':cost_budget}


def _stocks(rows,carbons,allocations,maintenance,key):
    total=sum(map(F,carbons),Fraction(0));need(total>0,'EMPTY_STOCK_HOLD: positive aggregate organ stock required')
    need(maintenance>0,'NUMERIC_HOLD: positive aggregate maintenance lost')
    result=[]
    for row,carbon,allocated in zip(rows,carbons,allocations,strict=True):
        need(carbon>=0 and row['carbon_removal']['value']==0,'REMOVAL_DOMAIN_HOLD: nonnegative stock and zero organ removal required')
        need(allocated[key]==row[key],'IDENTITY_HOLD: actual allocation order required')
        m=_normal(float(F(maintenance)*F(carbon)/total));g=allocated['carbohydrate_inflow']['value']
        need(carbon==0 or m>0,'NUMERIC_HOLD: positive individual maintenance lost')
        derivative=_normal(fsum((g,-m)));need(carbon!=0 or derivative>=0,'DEPLETED_STATE_HOLD: outward individual stock derivative')
        result.append({key:row[key],**({'kind':row['kind']}if 'kind'in row else {}),
            'carbon':q(carbon,MASS),'inflow':q(g,RATE),'maintenance':q(m,RATE),'removal':q(0.,RATE),'derivative':q(derivative,RATE)})
    return result


def _age_rate(temperature,base):
    delta=numeric._sum(temperature,-base)
    need(delta>=0,'TEMPERATURE_DOMAIN_HOLD: indoor air below organ base')
    return numeric._divide(delta,86400)


def evaluate(program,state,organs,costs,profiles):
    """Internal stage for checked branch/state owners; never authenticates a CP."""
    p=program;n=len(p['leaves']);m=len(p['stem_root_compartments']);h=len(organs['internodes']);size=106+3*n+m
    need(len(state)==size+2*h and all(type(x)is float and isfinite(x) for x in state),'STATE_HOLD: complete finite extended binary64 state required')
    need(p['capacity_outflow']['value']==0,'REMOVAL_DOMAIN_HOLD: zero capacity outflow required')
    for row in [*p['leaves'],*p['stem_root_compartments']]:
        need(row['carbon_removal']['value']==0,'REMOVAL_DOMAIN_HOLD: zero vegetative removals required')
    y=tuple(state[:size]);floor=p['model_floor_area']['value'];leaf_ages=[];potential=[]
    for i,leaf in enumerate(p['leaves']):
        age,area=y[106+i],y[106+n+i]
        need(age>=0 and 0<area<=leaf['curve']['values']['maximum_area']['value'],'STATE_HOLD: bounded positive leaf geometry required')
        age_rate=_age_rate(y[104],leaf['base_temperature']['value']);leaf_ages.append(age_rate)
        per_age=short.old.expansion.calculate_leaf_expansion_rate(inputs={'input_id':leaf['leaf_id'],'origin':'synthetic',
            'thermal_age_basis':'since_leaf_emergence','values':{**leaf['curve']['values'],'thermal_age':q(age,'degC_day')}})
        potential.append(numeric._multiply(per_age['expansion_per_thermal_age']['value'],age_rate))
    stem_ages=[];stem_potential=[]
    for i,node in enumerate(organs['internodes']):
        age,length=state[size+i],state[size+h+i]
        need(age>=0 and 0<length<=node['curve']['values']['maximum_length']['value'],'STATE_HOLD: bounded positive internode geometry required')
        age_rate=_age_rate(y[104],node['baseline']['base_temperature']['value']);stem_ages.append(age_rate)
        per_age=elongation.calculate_internode_elongation(inputs={'input_id':node['compartment_id'],'origin':'synthetic',
            'thermal_age_basis':'since_internode_emergence','values':{**node['curve']['values'],'thermal_age':q(age,'degC_day')}})
        stem_potential.append(numeric._multiply(per_age['elongation_per_thermal_age']['value'],age_rate))
    scenario=short.old._scenario(p,short._project(p,y))
    scenario['removals']={**scenario['removals'],'leaf':q(0.,RATE),'stem_root':q(0.,RATE)}
    numbers={};normalized={}
    for name in ('plant_state','climate_state','parameters','forcing','removals','fruit_entry','cohort_state','relative_growth_rate'):
        units=joint.ARRAY_BLOCKS.get(name,joint.SCALAR_BLOCKS.get(name));is_array=name in joint.ARRAY_BLOCKS
        numbers[name],normalized[name]=joint._quantities(scenario[name],units,is_array)
    physical=numbers['parameters'];climate=numbers['climate_state'];forcing=numbers['forcing']
    need(all(physical[k]>0 for k in joint.PARAMETER_UNITS if k!='reference_temperature'),'DOMAIN_HOLD: positive physical parameters required')
    lai=numeric._divide(numeric._sum(*y[106+n:106+2*n]),floor);need(lai>0,'EMPTY_CANOPY_HOLD: positive canopy required')
    capacity=numeric._multiply(physical['leaf_heat_capacity'],lai);offset=numeric._divide(climate['canopy_sensible_energy'],capacity)
    temperature=numeric._sum(physical['reference_temperature'],offset)
    need(abs(numeric._sum(temperature,-physical['reference_temperature'],-offset))<=numeric.TEMPERATURE_TOLERANCE,'NUMERIC_HOLD: canopy temperature resolution')
    for value in (temperature,climate['air_temperature'],forcing['incoming_capacity_temperature'],forcing['outgoing_capacity_temperature']):numeric._temperature(value)
    need(climate['air_vapor_mass']>=0,'STATE_HOLD: negative vapor storage')
    constants=profiles['exchange_profile'].values
    air_capacity=numeric._multiply(numeric._multiply(physical['air_volume_per_floor_area'],physical['air_capacity_density']),constants['air_heat_capacity'])
    pressure=numeric._multiply(numeric._multiply(numeric._divide(climate['air_vapor_mass'],physical['air_volume_per_floor_area']),physical['vapor_gas_constant']),numeric._sum(climate['air_temperature'],273.15))
    saturation=numeric._multiply(constants['saturation_pressure_coefficient'],exp(constants['saturation_exponent_factor']*climate['air_temperature']/(climate['air_temperature']+constants['saturation_denominator_offset'])))
    need(pressure<saturation,'BULK_SATURATION_HOLD: no condensation closure')
    block=joint._block;carbon=joint.carbon
    crop=carbon.calculate_plant_rates(state=block('plant',normalized['plant_state']),
        cohort_state=block('cohorts',{**normalized['cohort_state'],**normalized['relative_growth_rate'],**{k:normalized['plant_state'][k]for k in carbon.fruit.SCALAR_UNITS}}),
        forcing=block('crop-forcing',{'canopy_temperature':q(temperature,'degC'),**{k:normalized['forcing'][k]for k in ('par_above_canopy','co2')}}),
        removals=block('removals',normalized['removals']),fruit_entry=block('entry',normalized['fruit_entry']),geometry=block('geometry',{'leaf_area_index':q(lai,'m2_leaf/m2_floor')}),
        **{k:profiles[k]for k in ('growth_profile','cohort_profile','transport_profile')})
    lp=leaf_partition.calculate_partition(inputs={'input_id':p['input_id'],'origin':'synthetic','policy':leaf_partition.POLICY_ID,
        'requested_leaf_growth':crop['allocation']['leaf'],'leaves':[{k:deepcopy(x[k])for k in ('leaf_id','sink_weight')}for x in p['leaves']]},growth_profile=profiles['growth_profile'])
    sp=stem_partition.calculate_partition(inputs={'input_id':p['input_id'],'origin':'synthetic','policy':stem_partition.POLICY_ID,'model_floor_area':p['model_floor_area'],
        'requested_stem_root_growth':crop['allocation']['stem_root'],'compartments':[{k:deepcopy(x[k])for k in ('compartment_id','kind','sink_weight')}for x in p['stem_root_compartments']]},growth_profile=profiles['growth_profile'])
    leaves=_stocks(p['leaves'],y[106+2*n:106+3*n],lp['allocation'],crop['vegetative_maintenance']['leaf']['value'],'leaf_id')
    stems=_stocks(p['stem_root_compartments'],y[106+3*n:],sp['allocation'],crop['vegetative_maintenance']['stem_root']['value'],'compartment_id')
    leaf_geometry=[{**item,**_classification(item['inflow']['value'],P,cost,floor,'m2/s')}for item,P,cost in zip(leaves,potential,costs['leaves'],strict=True)]
    by_id={x['compartment_id']:x for x in stems}
    internodes=[{**by_id[node['compartment_id']],**_classification(by_id[node['compartment_id']]['inflow']['value'],P,cost,floor,'m/s')}
        for node,P,cost in zip(organs['internodes'],stem_potential,costs['internodes'],strict=True)]
    area_rates=[x['realized_rate']['value']for x in leaf_geometry];length_rates=[x['realized_rate']['value']for x in internodes]
    ldot=numeric._divide(numeric._sum(*area_rates),floor);gin=numeric._multiply(physical['leaf_heat_capacity'],ldot)
    exchanged=joint.exchange.calculate_exchange(profile=profiles['exchange_profile'],forcing=block('exchange',{
        'leaf_area_index':q(lai,'m2_leaf/m2_floor'),'canopy_temperature':q(temperature,'degC'),'air_temperature':normalized['climate_state']['air_temperature'],
        'air_vapor_pressure':q(pressure,'Pa'),**{k:normalized['parameters'][k]for k in ('air_capacity_density','canopy_vapor_resistance')}}))
    vapor,sensible,latent=(exchanged['exchange'][k]['value']for k in ('water_vapor','sensible_heat','latent_heat'))
    material=joint.area.calculate_area_energy(inputs=block('area-energy',{'leaf_area_index':q(lai,'m2_leaf/m2_floor'),
        'leaf_area_index_rate':q(ldot,'m2_leaf/m2_floor/s'),**{k:normalized['parameters'][k]for k in ('leaf_heat_capacity','reference_temperature')},
        'capacity_inflow':q(gin,numeric.CAPACITY_RATE),'capacity_outflow':q(0.,numeric.CAPACITY_RATE),'canopy_temperature':q(temperature,'degC'),
        **{k:normalized['forcing'][k]for k in ('incoming_capacity_temperature','outgoing_capacity_temperature')},
        'nonmaterial_heat':q(numeric._sum(forcing['canopy_external_heat'],-sensible,-latent),numeric.POWER)}))
    need(material['canopy_capacity']['value']==capacity and crop['lai']['value']==lai,'STATE_MISMATCH_HOLD: same stage geometry required')
    plant=deepcopy(crop['derivatives']);growth=crop['growth_respiration']['value']
    for partition in (lp,sp):
        for name,value in partition['derivative_adjustments'].items():
            if name=='growth_respiration':growth=fsum((growth,value['value']))
            else:plant[name]=q(fsum((plant[name]['value'],value['value'])),RATE)
    need(growth>=0 and all(isfinite(x['value'])for x in plant.values()),'NUMERIC_HOLD: finite adjusted carbon derivatives required')
    for label,rows in [('leaf',leaves),('stem_root',stems)]:plant[label]=q(numeric._sum(*(x['derivative']['value']for x in rows)),RATE)
    need(y[0]!=0 or plant['buffer']['value']>=0,'DEPLETED_STATE_HOLD: outward buffer derivative')
    du=material['energy_flows']['total']['value'];heat_material=material['energy_flows']['material']['value']
    da=numeric._divide(numeric._sum(forcing['air_external_sensible_heat'],sensible),air_capacity);dm=numeric._sum(vapor,forcing['air_external_vapor'])
    need(climate['air_vapor_mass']!=0 or dm>=0,'DEPLETED_STATE_HOLD: outward vapor derivative')
    climate_rates={'canopy_sensible_energy':q(du,numeric.POWER),'air_temperature':q(da,'K/s'),'air_vapor_mass':q(dm,joint.exchange.WATER_UNIT)}
    inherited=fsum((crop['balance_budget']['carbohydrate']['value'],lp['balance_budgets']['whole_leaf_budget']['value'],sp['balance_budgets']['whole_stem_root_budget']['value']))
    entries={'carbon':([plant[k]['value']for k in ('buffer','leaf','stem_root')]+[x['value']for x in crop['cohorts']['derivatives']['fruit_carbohydrate']]+
        [growth,*[x['maintenance']['value']for x in leaves+stems],crop['fruit_maintenance']['value'],crop['cohorts']['terminal_outflow']['fruit_carbohydrate']['value'],-crop['photosynthesis']['value']],RATE,inherited),
        'canopy_sensible':([du,-forcing['canopy_external_heat'],sensible,latent,-heat_material],numeric.POWER,0.),
        'air_sensible':([air_capacity*da,-forcing['air_external_sensible_heat'],-sensible],numeric.POWER,0.),
        'vapor_water':([dm,-vapor,-forcing['air_external_vapor']],joint.exchange.WATER_UNIT,0.),
        'reduced_energy':([du,air_capacity*da,constants['latent_heat']*dm,-forcing['canopy_external_heat'],-forcing['air_external_sensible_heat'],-constants['latent_heat']*forcing['air_external_vapor'],-heat_material],numeric.POWER,0.)}
    for label,rows,partition in [('leaf',leaves,lp),('stem_root',stems,sp)]:
        entries[label+'_allocation']=([*[x['inflow']['value']for x in rows],-partition['effective_'+('leaf'if label=='leaf'else'stem_root')+'_growth']['value']],RATE,partition['balance_budgets']['allocation']['value'])
        entries[label+'_maintenance']=([*[x['maintenance']['value']for x in rows],-crop['vegetative_maintenance'][label]['value']],RATE,0.)
        entries[label+'_stock']=([plant[label]['value'],*[x['maintenance']['value']for x in rows],*[-x['inflow']['value']for x in rows]],RATE,0.)
    books={k:_ledger(*v)for k,v in entries.items()}
    rates=tuple([plant[k]['value']for k in short.PLANT]+[x['value']for k in short.COHORT for x in crop['cohorts']['derivatives'][k]]+
        [climate_rates[k]['value']for k in short.CLIMATE]+leaf_ages+area_rates+[x['derivative']['value']for x in leaves+stems]+stem_ages+length_rates)
    need(len(rates)==len(state)and all(isfinite(x)for x in rates),'STATE_HOLD: complete finite derivative vector required')
    return {'rates':list(rates),'leaves':leaf_geometry,'internodes':internodes,'stem_root_stocks':stems,
        'derived':{'leaf_area_index':q(lai,'m2_leaf/m2_floor'),'leaf_area_index_rate':q(ldot,'m2_leaf/m2_floor/s'),
            'canopy_capacity':q(capacity,numeric.CAPACITY),'canopy_temperature':q(temperature,'degC'),'air_capacity':q(air_capacity,numeric.CAPACITY),
            'leaf_carbohydrate':q(numeric._sum(*y[106+2*n:106+3*n]),MASS),'stem_root_carbohydrate':q(numeric._sum(*y[106+3*n:]),MASS),
            'air_vapor_pressure':q(pressure,'Pa'),'canopy_temperature_rate':deepcopy(material['canopy_temperature_rate'])},
        'derivatives':{'plant':plant,'cohorts':deepcopy(crop['cohorts']['derivatives']),'climate':climate_rates},'growth_respiration':q(growth,RATE),
        'crop':crop,'leaf_partition':lp,'stem_root_partition':sp,'exchange':exchanged,'capacity_transport':material,
        'canopy_water_boundary':q(-vapor,joint.exchange.WATER_UNIT),
        'balance_residuals':{k:v[0]for k,v in books.items()},'balance_budgets':{k:v[1]for k,v in books.items()}}
