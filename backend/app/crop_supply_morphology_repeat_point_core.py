"""Explicit successor seeds and shared pure material arithmetic on actual owners."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from . import crop_supply_morphology_repeat_candidate as candidate
from . import crop_supply_morphology_point_core as material

resume=candidate.resume
source=resume.source
stem,leaf=material.stem,material.leaf
arithmetic,numeric,stage=material.arithmetic,material.numeric,material.stage
F,Q,X=resume.F,resume.Q,resume.X
need=resume._need
MASS=material.MASS
compatibility=material.compatibility
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def source_event(data,calculation):
    return material.source_event({'source_data':data['source_data']},calculation)


def apply(context,data,calculation,value,event,seeds,evaluate):
    need(len(data['program']['leaves'])+(seeds['leaf']is not None)<=512 and len(data['program']['stem_root_compartments'])+1<=512 and len(data['organs']['internodes'])+1<=512,
        'CAPACITY_HOLD: bounded resulting successor inventory required')
    return material.apply(context,candidate.accounts.projection(data),calculation,value,event,seeds,evaluate)


def previous_event_ids(context,data):
    past={row['event_id']for rows in data['organs'].values()if type(rows)is list for row in rows if 'event_id'in row}
    past.update(data['verified_material_event_ids'])
    return past


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
    profile=data['emergence_profile']
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
