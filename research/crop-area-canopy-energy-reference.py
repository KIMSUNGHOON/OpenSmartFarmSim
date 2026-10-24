"""App-free Decimal energy-inventory oracle; own synthetic software inputs."""
from decimal import Decimal, localcontext
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

UNITS={'leaf_area_index':'m2_leaf/m2_floor','leaf_area_index_rate':'m2_leaf/m2_floor/s',
       'leaf_heat_capacity':'J/m2_leaf/K','capacity_inflow':'J/m2_floor/K/s',
       'capacity_outflow':'J/m2_floor/K/s','canopy_temperature':'degC',
       'incoming_capacity_temperature':'degC','outgoing_capacity_temperature':'degC',
       'reference_temperature':'degC','nonmaterial_heat':'W/m2_floor'}


def calculate(values):
    v={name:Decimal(str(quantity['value']))for name,quantity in values.items()}
    lai=v['leaf_area_index'];rate=v['leaf_area_index_rate'];k=v['leaf_heat_capacity']
    tc=v['canopy_temperature'];ref=v['reference_temperature']
    gin=v['capacity_inflow'];gout=v['capacity_outflow'];heat=v['nonmaterial_heat']
    capacity=k*lai;change=k*rate;net=gin-gout;energy=capacity*(tc-ref)
    incoming=gin*(v['incoming_capacity_temperature']-ref)
    outgoing=gout*(v['outgoing_capacity_temperature']-ref)
    material=incoming-outgoing;total=heat+material
    capacity_part=(tc-ref)*change
    temperature_rate=(total-capacity_part)/capacity
    temperature_part=capacity*temperature_rate
    return {name:str(value)for name,value in {
        'leaf_area_index':lai,'leaf_area_index_rate':rate,'canopy_capacity':capacity,
        'canopy_sensible_energy':energy,'capacity_rates.geometry':change,'capacity_rates.transport':net,
        'capacity_rates.incoming':gin,'capacity_rates.outgoing':gout,'energy_flows.incoming':incoming,
        'energy_flows.outgoing':outgoing,'energy_flows.material':material,'energy_flows.nonmaterial':heat,
        'energy_flows.total':total,'canopy_temperature_rate':temperature_rate,
        'chain_rule.temperature_part':temperature_part,'chain_rule.capacity_part':capacity_part,
        'chain_rule.total':temperature_part+capacity_part,
        'balance_residuals.capacity_rate':change-net,'balance_residuals.energy':temperature_part+capacity_part-total}.items()}


def generate():
    experiments=[(gi,go,ti,to,ref,q)for(gi,go),(ti,to),ref,q in product(
        [(0,0),(3,0),(0,3),(3,1),(3,3),(1,3)],[(14,22),(30,18)],[-10,0,22,30],[0,20])]
    experiments += [(3,1,22,22,0,20),(0,0,22,22,30,-20),
                    (0,3,22,22,-10,-20),(2**40,2**40,14,30,22,20)]
    cases=[]
    with localcontext()as context:
        context.prec=120
        for index,(gi,go,ti,to,ref,q)in enumerate(experiments):
            numbers={'leaf_area_index':1.25,'leaf_area_index_rate':(gi-go)/1024,
                'leaf_heat_capacity':1024,'capacity_inflow':gi,'capacity_outflow':go,
                'canopy_temperature':22,'incoming_capacity_temperature':ti,
                'outgoing_capacity_temperature':to,'reference_temperature':ref,'nonmaterial_heat':q}
            quantities={name:{'value':value,'unit':UNITS[name]}for name,value in numbers.items()}
            cases.append({'case_id':f'own-area-energy-{index:03}',
                'inputs':{'input_id':f'own-area-energy-{index:03}','origin':'synthetic','values':quantities},
                'expected':calculate(quantities)})
    assert len(cases)==100 and not any(name=='app'or name.startswith('app.')for name in sys.modules)
    return {'schema_version':'explicit-area-canopy-energy-decimal-reference-v1',
        'origin':'own_synthetic_software_fixture','independent_precision':120,'G0_G4':'not_assessed',
        'generator_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'cases':cases}


if __name__=='__main__':
    output=Path(sys.argv[1]);data=generate();output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'cases':len(data['cases']),'app_imports':0,'sha256':sha256(output.read_bytes()).hexdigest()}))
