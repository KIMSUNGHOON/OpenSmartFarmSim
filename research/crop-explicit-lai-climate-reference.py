"""App-free shared-stage oracle: Decimal120, retained optical oracle110."""
from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from math import fsum
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[1]
INPUTS=('fixtures/crop-growth-reference-parameters-v1.json','fixtures/crop-fruit-cohort-reference-parameters-v1.json',
 'fixtures/crop-canopy-exchange-reference-parameters-v1.json','fixtures/crop-climate-joint-rhs-reference-cases-v1.json',
 'research/crop-explicit-lai-carbon-reference.py','research/crop-explicit-lai-photosynthesis-reference.py',
 'research/crop-plant-startup-reference.py','research/crop-canopy-air-dynamics-reference.py')
D=Decimal


def quantities(block):return {name:D(str(row['value']))for name,row in block.items()}
def q(value,unit):return {'value':float(value),'unit':unit}


def calculate(s,p,cp,ep,profile,optical,whole,non_optical,thermal):
    plant,c,params,f,g,flow=(quantities(s[name])for name in
        ('plant_state','climate_state','parameters','forcing','geometry','capacity_transport'))
    lai=g['leaf_area_index'];capacity=params['leaf_heat_capacity']*lai
    offset=c['canopy_sensible_energy']/capacity;tc=params['reference_temperature']+offset
    metadata={'input_id':'independent-explicit-joint','origin':'synthetic'}
    forcing={'canopy_temperature':{'value':tc,'unit':'degC'},**{name:s['forcing'][name]for name in ('par_above_canopy','co2')}}
    case={'state':{**metadata,'values':s['plant_state']},
        'cohort_state':{**metadata,'values':{**s['cohort_state'],**s['relative_growth_rate'],
            **{name:s['plant_state'][name]for name in ('temperature_filtered_24h','temperature_sum')}}},
        'forcing':{**metadata,'values':forcing},**{name:{**metadata,'values':s[name]}for name in ('removals','fruit_entry')}}
    photo=optical({'values':{**forcing,'buffer':s['plant_state']['buffer'],
        'leaf_area_index':s['geometry']['leaf_area_index']}},profile)
    assert photo is not None
    rhs=lambda y,f,r,p:non_optical(y,f,r,p,D(photo['photosynthesis']))
    crop=whole(case,p,cp,rhs)
    y=[plant[name]for name in ('buffer','leaf','stem_root')]+[D(0),plant['temperature_filtered_24h'],plant['temperature_sum']]
    removal={**quantities(s['removals']),'fruit':D(0)}
    z=rhs(y,{name:D(str(row['value']))for name,row in forcing.items()},removal,p)
    _,_,heat=thermal((tc,c['air_temperature'],c['air_vapor_mass']),{'leaf_area_index':lai,**params},
        {name:f[name]for name in ('canopy_external_heat','air_external_sensible_heat','air_external_vapor')},ep)
    e,h,le=(heat[name]for name in ('water_vapor','sensible_heat','latent_heat'))
    gin=flow['capacity_inflow'];gout=flow['capacity_outflow'];ref=params['reference_temperature']
    cdot=params['leaf_heat_capacity']*g['leaf_area_index_rate']
    incoming=gin*(f['incoming_capacity_temperature']-ref);outgoing=gout*(f['outgoing_capacity_temperature']-ref)
    material=incoming-outgoing;nonmaterial=f['canopy_external_heat']-h-le;du=nonmaterial+material
    da=(f['air_external_sensible_heat']+h)/heat['air_capacity'];dm=e+f['air_external_vapor']
    tdot=(du-offset*cdot)/capacity
    expected={**{'derived.'+name:value for name,value in {
        'canopy_temperature':tc,'leaf_area_index':lai,'leaf_area_index_rate':g['leaf_area_index_rate'],
        'canopy_capacity':capacity,'air_capacity':heat['air_capacity'],'air_vapor_pressure':heat['air_pressure'],
        'canopy_temperature_rate':tdot}.items()},
        **{'derivatives.plant.'+name:D(value)for name,value in crop['plant_derivatives'].items()},
        **{'derivatives.climate.'+name:value for name,value in
            [('canopy_sensible_energy',du),('air_temperature',da),('air_vapor_mass',dm)]},
        **{f'derivatives.cohorts.{name}.{index}':D(value)for name,key in
            [('fruit_carbohydrate','dC'),('fruit_number','dN')]for index,value in enumerate(crop[key])},
        **{'exchange.exchange.'+name:value for name,value in [('water_vapor',e),('sensible_heat',h),('latent_heat',le)]},
        **{'capacity_transport.capacity_rates.'+name:value for name,value in
            [('geometry',cdot),('transport',gin-gout),('incoming',gin),('outgoing',gout)]},
        **{'capacity_transport.energy_flows.'+name:value for name,value in
            [('incoming',incoming),('outgoing',outgoing),('material',material),('nonmaterial',nonmaterial),('total',du)]},
        'canopy_water_boundary':-e,
        **{'crop.'+name:D(crop[name])for name in ('photosynthesis','growth_respiration')},
        'crop.allocation.fruit':D(crop['fruit_allocation']),
        'crop.fruit_startup.deferred_carbohydrate_inflow':D(crop['deferred_fruit_allocation'])}
    scales={'derivatives.plant.buffer':sum(map(abs,[z[6],z[7],z[1]+z[8]+removal['leaf'],
        z[2]+z[9]+removal['stem_root'],z[3],D(crop['buffer_adjustment'])])),
        'derivatives.plant.leaf':sum(map(abs,[z[1]+z[8]+removal['leaf'],z[8],removal['leaf']])),
        'derivatives.plant.stem_root':sum(map(abs,[z[2]+z[9]+removal['stem_root'],z[9],removal['stem_root']])),
        'derivatives.plant.temperature_filtered_24h':(abs(tc)+abs(plant['temperature_filtered_24h']))/p['seconds_per_day'],
        'exchange.exchange.sensible_heat':ep['leaf_surface_factor']*ep['leaf_air_heat_transfer']*lai*(abs(tc)+abs(c['air_temperature'])),
        'capacity_transport.energy_flows.material':abs(incoming)+abs(outgoing),
        'capacity_transport.energy_flows.nonmaterial':abs(f['canopy_external_heat'])+abs(h)+abs(le),
        'capacity_transport.capacity_rates.transport':gin+gout}
    total_scale=sum(map(abs,[f['canopy_external_heat'],h,le,incoming,outgoing]))
    scales.update({'derivatives.climate.canopy_sensible_energy':total_scale,
        'capacity_transport.energy_flows.total':total_scale,
        'derivatives.climate.air_temperature':(abs(f['air_external_sensible_heat'])+abs(h))/heat['air_capacity'],
        'derivatives.climate.air_vapor_mass':abs(e)+abs(f['air_external_vapor']),
        'derived.canopy_temperature_rate':(total_scale+abs(offset*cdot))/capacity})
    return {key:str(value)for key,value in expected.items()},{key:str(value)for key,value in scales.items()}


def generate():
    raw={name:(ROOT/name).read_bytes()for name in INPUTS};profile=json.loads(raw[INPUTS[0]])['parameters']
    p={name:D(str(row['value']))for name,row in profile.items()}
    cp={name:D(row['source_value'])for name,row in json.loads(raw[INPUTS[1]])['parameters'].items()}
    ep={name:D(str(row['value']))for name,row in json.loads(raw[INPUTS[2]])['parameters'].items()}
    non_optical=runpy.run_path(str(ROOT/INPUTS[4]))['non_optical']
    optical=runpy.run_path(str(ROOT/INPUTS[5]))['independent_optics']
    whole=runpy.run_path(str(ROOT/INPUTS[6]))['calculate'];thermal=runpy.run_path(str(ROOT/INPUTS[7]))['rhs']
    cases=[]
    with localcontext()as context:
        context.prec=120
        for old in json.loads(raw[INPUTS[3]])['cases']:
            for multiplier in (1,2):
                for turnover in (False,True):
                    s=deepcopy(old['scenario']);reference=old['expected_decimal'];rates=reference['capacity_rates']
                    gin=3.0 if turnover else float(rates['allocation'])
                    gout=3.0 if turnover else fsum(float(rates[name])for name in ('maintenance','removal'))
                    s['geometry']={'model_floor_area':q(1,'m2_floor'),
                        'leaf_area_index':q(float(reference['derived']['leaf_area_index'])*multiplier,'m2_leaf/m2_floor'),
                        'leaf_area_index_rate':q(fsum((gin,-gout))/s['parameters']['leaf_heat_capacity']['value'],'m2_leaf/m2_floor/s')}
                    s['capacity_transport']={name:q(value,'J/m2_floor/K/s')for name,value in [('capacity_inflow',gin),('capacity_outflow',gout)]}
                    s['climate_state']['canopy_sensible_energy']['value']*=multiplier
                    s['forcing']['outgoing_capacity_temperature']=q(float(reference['derived']['canopy_temperature'])+(2 if turnover else 0),'degC')
                    s['input_id']=old['case_id']+f'-LAI{multiplier}-turnover{int(turnover)}'
                    expected,scales=calculate(s,p,cp,ep,profile,optical,whole,non_optical,thermal)
                    cases.append({'case_id':s['input_id'],'source_case_id':old['case_id'],'scenario':s,
                        'expected':expected,'cancellation_scales':scales})
    assert len(cases)==40 and not any(name=='app'or name.startswith('app.')for name in sys.modules)
    return {'schema_version':'explicit-lai-climate-decimal-reference-v1','origin':'own_synthetic_software_fixture',
        'G0_G4':'not_assessed','independent_precision':120,'optical_oracle_precision':110,
        'input_sha256':{name:sha256(value).hexdigest()for name,value in raw.items()},
        'generator_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'cases':cases}


if __name__=='__main__':
    output=Path(sys.argv[1]);data=generate();output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'cases':len(data['cases']),'app_imports':0,'sha256':sha256(output.read_bytes()).hexdigest()}))
