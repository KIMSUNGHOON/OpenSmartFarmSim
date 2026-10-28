"""Explicit seed compatibility and material-only transitions on genuine new states."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_supply_morphology_candidate as candidate
from . import crop_supply_morphology_birth_stage as stage
from . import crop_rational_new_internodes as source_ids

resume=candidate.resume
source=resume.source
stem,leaf=source.material.stem,source.material.leaf
arithmetic=stem.arithmetic
numeric=resume.numeric
F,Q,X=resume.F,resume.Q,resume.X
need=resume._need
MASS=resume.books.MASS
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def source_event(data,calculation):
    timeline=data['source_data']['point']['before_candidate']['source_root_certificate']['source_timeline'];schedule=calculation['source_prefix']['schedule']
    entity={k:deepcopy(timeline[k])for k in ['shoot_id','development_origin_id','schedule_id','started_at']}
    entity.update(sequence=schedule['next_sequence'],birth_age_exact=deepcopy(schedule['next_threshold_exact']))
    digest=source_ids._digest(entity);age=X(calculation['dense_candidate']['shoot_age_exact']);threshold=X(entity['birth_age_exact']);spacing=X(timeline['phyllochron_exact'])
    need(calculation['source_next_sequence']==entity['sequence']and calculation['threshold_exact']==entity['birth_age_exact']and spacing>0 and threshold<=age<threshold+spacing,
        'EVENT_HOLD: actual first unconsumed new-law event required')
    return {'entity':entity,'source_event_id':'shoot-event:'+digest,'internode_event_id':'shoot-event:'+digest+'/internode','leaf_event_id':'shoot-event:'+digest+'/leaf',
        'internode_id':'internode:'+digest,'leaf_id':'leaf:'+source_ids._digest({**entity,'organ':'leaf','slot':0}),'sequence':entity['sequence'],'threshold_exact':deepcopy(entity['birth_age_exact'])}


def compatibility(carbon,cost,dimension,floor,unit):
    need(carbon>0 and cost>0 and dimension>=0 and floor>0,'SEED_HOLD: positive C/cost/floor and nonnegative seed geometry required')
    available=F(carbon)*F(floor);required=F(cost)*F(dimension)
    need(available>=required,'SEED_COMPATIBILITY_HOLD: declared seed C cannot fund declared geometry and cost')
    extension=required/F(floor);unmapped=F(carbon)-extension
    return {'seed_geometry':numeric._q(dimension,unit),'construction_cost':numeric._q(cost,'mg_CH2O/'+('m2_leaf'if unit=='m2'else'm_internode')),
        'available_carbon_exact':Q(available,'mg_CH2O'),'construction_required_exact':Q(required,'mg_CH2O'),
        'available_minus_required_exact':Q(available-required,'mg_CH2O'),'compatibility_budget_exact':Q(Fraction(0),'mg_CH2O'),
        'seed_extension_exact':Q(extension,MASS),'seed_unmapped_exact':Q(unmapped,MASS),'scope':'exact_declared_binary64_quantities_no_second_debit_or_respiration'}


def baseline(identifier,kind,carbon,base,calculation):
    before=calculation['dense_candidate'];result={'at_elapsed_seconds_exact':deepcopy(calculation['at']['elapsed_seconds_exact']),
        'air_temperature_integral_exact':deepcopy(before['pending_lifetime_transfers_exact']['indoor_air_temperature_time']),
        'thermal_age_exact':Q(Fraction(0),'degC_day'),'base_temperature':deepcopy(base),'carbon':numeric._q(carbon,MASS)}
    result['leaf_id'if kind=='leaf'else'compartment_id']=identifier
    if kind!='leaf':result['kind']='internode'
    return result


def _metadata(identifier,kind,parent,event,base,calculation):
    return {('leaf_id'if kind=='leaf'else'compartment_id'):identifier,'lineage_kind':'supply_limited_numerical_material',
        'parent_internode_id':parent,'event_id':event[kind+'_event_id'],'material_event_sequence':calculation['source_prefix']['event_sequence']+1,
        'source_threshold_sequence':event['sequence'],'baseline':base,'age_exact':Q(Fraction(0),'degC_day'),
        'represented_age':numeric._q(0.,'degC_day'),'represented_minus_clock_exact':Q(Fraction(0),'degC_day'),'age_roundoff_budget_exact':Q(Fraction(0),'degC_day')}


def validate_seeds(context,data,calculation,value,event):
    p=data['program'];floor=p['model_floor_area']['value'];part=source.stock.short.stock.part
    arithmetic._closed(value['internode'],{'declaration','initial_length','construction_cost'})
    row=value['internode']['declaration'];arithmetic._closed(row,{'compartment_id','kind',*source.stock.short.STOCK_FIELDS})
    part._id(row['compartment_id']);need(row['compartment_id']==event['internode_id']and row['kind']=='internode','EVENT_HOLD: actual next internode ID/kind required')
    numbers={k:arithmetic._quantity(row[k],unit)for k,unit in source.stock.short.STOCK_FIELDS.items()}
    need(numbers['initial_carbon']>0 and numbers['sink_weight']>=0 and numbers['carbon_removal']==0,'SEED_HOLD: positive declared C/nonnegative sink/zero removal required')
    node={k:deepcopy(v)for k,v in row.items()}
    node.update({k:numeric._q(v,source.stock.short.STOCK_FIELDS[k])for k,v in numbers.items()})
    length=arithmetic._quantity(value['internode']['initial_length'],'m');cost=arithmetic._quantity(value['internode']['construction_cost'],'mg_CH2O/m_internode')
    binding=source.stock._source(context._source._source);profile=binding['stem_selection']['source_state']['emergence_profile']
    need(0<=length<=profile['curve']['values']['maximum_length']['value'],'GEOMETRY_HOLD: explicit bounded nonnegative seed length required')
    compatibility_rows={'internode':compatibility(numbers['initial_carbon'],cost,length,floor,'m')};new_leaf=None;init=None;leaf_cost=None;temperature=None
    if value['leaf']is not None:
        packet=value['leaf'];arithmetic._closed(packet,{'declaration','incoming_temperature','construction_cost'})
        new_leaf,init=arithmetic._new_leaf(packet['declaration'])
        need(new_leaf['leaf_id']==event['leaf_id']and new_leaf['carbon_removal']['value']==0,'EVENT_HOLD: actual next leaf ID and zero removal required')
        temperature=arithmetic._quantity(packet['incoming_temperature'],'degC');numeric._temperature(temperature)
        leaf_cost=arithmetic._quantity(packet['construction_cost'],'mg_CH2O/m2_leaf')
        compatibility_rows['leaf']=compatibility(new_leaf['initial_carbon']['value'],leaf_cost,init['state']['area']['value'],floor,'m2')
    base=data['source_data']['point']['before_candidate']['source_root_certificate']['source_timeline']['base_temperature']
    return {'node':node,'length':length,'cost':cost,'profile':deepcopy(profile),'base_temperature':deepcopy(base),
        'leaf':new_leaf,'initialization':init,'leaf_cost':leaf_cost,'temperature':temperature,'compatibility':compatibility_rows}


def _component(mass,cost,before):
    structural,respiration,debit,buffer=arithmetic._fund(before,[mass],cost)
    return {k:numeric._q(v,MASS)for k,v in [('structural_carbon',structural),('growth_respiration',respiration),('buffer_debit',debit)]}|{
        'capacity_in':numeric._q(0.,numeric.CAPACITY),'sensible_in':numeric._q(0.,numeric.ENERGY)},buffer


def apply(context,data,calculation,value,event,seeds,evaluate):
    p=deepcopy(data['program']);y=list(calculation['dense_candidate']['state']);organs=deepcopy(data['initial']['organs']);costs=deepcopy(data['costs'])
    n=len(p['leaves']);m=len(p['stem_root_compartments']);h=len(organs['internodes']);size=106+3*n+m
    growth=stem._cost(data['profiles']);component,buffer=_component(seeds['node']['initial_carbon']['value'],growth,y[0]);components={'internode':component}
    p['stem_root_compartments'].append(deepcopy(seeds['node']));base=baseline(event['internode_id'],'internode',seeds['node']['initial_carbon']['value'],seeds['base_temperature'],calculation)
    meta=_metadata(event['internode_id'],'internode',value['parent_internode_id'],event,base,calculation)
    meta.update(curve=deepcopy(seeds['profile']['curve']),seed_length=numeric._q(seeds['length'],'m'),source_emergence_initial_length=deepcopy(seeds['profile']['initial_length']))
    organs['internodes'].append(meta);costs['internodes'].append(seeds['cost'])
    z=[*y[:size],seeds['node']['initial_carbon']['value'],*y[size:size+h],0.,*y[size+h:],seeds['length']];z[0]=buffer
    first=evaluate(p,z,organs,costs);last=first;leaf_receipts=[];new_bases={'leaf':[],'stem_root':[base]}
    if seeds['leaf']is not None:
        declaration=seeds['leaf'];mass=declaration['initial_carbon']['value'];leaf_growth=leaf._cost(data['profiles']);part,buffer=_component(mass,leaf_growth,z[0])
        area=seeds['initialization']['state']['area']['value'];heat=p['scenario']['parameters']['leaf_heat_capacity']['value'];ref=p['scenario']['parameters']['reference_temperature']['value'];floor=p['model_floor_area']['value']
        capacity=arithmetic._rounded(F(heat)*F(area)/F(floor));energy=arithmetic._rounded(F(capacity)*(F(seeds['temperature'])-F(ref)))
        need(capacity>0,'CAPACITY_HOLD: positive leaf seed capacity required');after_u=arithmetic._rounded(F(z[103])+F(energy))
        need(energy==0 or after_u!=z[103],'NUMERIC_HOLD: incoming seed heat lost')
        part['capacity_in']=numeric._q(capacity,numeric.CAPACITY);part['sensible_in']=numeric._q(energy,numeric.ENERGY);components['leaf']=part
        scalar=z[:106];scalar[0],scalar[103]=buffer,after_u
        z=[*scalar,*z[106:106+n],0.,*z[106+n:106+2*n],area,*z[106+2*n:106+3*n],mass,*z[106+3*n:]]
        p['leaves'].append(deepcopy(declaration));costs['leaves'].append(seeds['leaf_cost'])
        base=baseline(event['leaf_id'],'leaf',mass,declaration['base_temperature'],calculation)
        meta=_metadata(event['leaf_id'],'leaf',event['internode_id'],event,base,calculation);meta.update(attachment_status='declared_material_parent_not_validated_anatomy',seed_area=numeric._q(area,'m2'))
        organs['leaves'].append(meta);new_bases['leaf'].append(base)
        leaf_receipts=[{'event_id':event['leaf_event_id'],'parent_internode_id':event['internode_id'],'initialization':deepcopy(seeds['initialization']),
            'capacity_in':deepcopy(part['capacity_in']),'sensible_in':deepcopy(part['sensible_in'])}]
        last=evaluate(p,z,organs,costs)
    else:leaf_growth=None
    return {'program':p,'state':z,'organs':organs,'costs':costs,'evaluation':last,'components':components,'new_birth_baselines':new_bases,
        'leaf_receipts':leaf_receipts,'growth_costs':{'cStemG':growth,'cLeafG':leaf_growth,'unit':'mg_CH2O/mg_CH2O','profile_sha256':data['profiles']['growth_profile'].sha256}}
