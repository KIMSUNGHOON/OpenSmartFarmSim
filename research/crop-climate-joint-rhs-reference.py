"""Decimal80 joint trial oracle using pinned independent crop/climate equations."""
from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]
D=Decimal
INPUTS={
    'fixtures/crop-growth-reference-parameters-v1.json':'d606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca',
    'fixtures/crop-fruit-cohort-reference-parameters-v1.json':'b453b4ffe618f26041e4ec6a1b1b7d2e5f38edb3d42adaaad4fa3cd4fbb99cbb',
    'fixtures/crop-fruit-transport-reference-parameters-v1.json':'09ea5e176bc745361e8e3ec8945b0f8abb0b2b427b4e9c459d0663cf390e9070',
    'fixtures/crop-canopy-exchange-reference-parameters-v1.json':'1e032ced2ffdaf8ba713184e89b628cce4173c9e7231f30710afeda8fbf20110',
    'fixtures/crop-plant-startup-reference-cases-v1.json':'4a3ef17617c172b817e32f6d2ed20153c19fd28560f9cb23e650e591485193fb',
    'research/crop-plant-startup-reference.py':'d7de6caa6ca863d1d196de1c610b6401b93977a27e0ea087f43b785b635c31b2',
    'research/crop-integration-reference.py':'a38b7a67e43cf9f590838bf915ab3e5048950b8be6ed35f70817e18b42a09ce7',
    'research/crop-canopy-air-dynamics-reference.py':'6c9e7c5d2698531133414b7817931dfe81dcc95e363ed20c2332dead4a1f95a6',
    'research/crop-canopy-energy-transport-reference.py':'09b6dbe423b71218ac05376b3e932cfe11364eba11d585b43f7ad5dc261bc120'}


def q(value,unit):return {'value':float(value),'unit':unit}
def values(block):return {k:D(str(row['value'])) for k,row in block.items()}


def legacy_case(s,tc):
    metadata={'input_id':s['input_id'],'origin':'synthetic'}
    return {'state':{**metadata,'values':s['plant_state']},
        'cohort_state':{**metadata,'values':{**s['cohort_state'],**s['relative_growth_rate'],
            **{k:s['plant_state'][k] for k in ('temperature_filtered_24h','temperature_sum')}}},
        'forcing':{**metadata,'values':{'canopy_temperature':{'value':tc,'unit':'degC'},
            **{k:s['forcing'][k] for k in ('par_above_canopy','co2')}}},
        **{k:{**metadata,'values':s[k]} for k in ('removals','fruit_entry')}}


def calculate(s,p,cp,ep,oracles):
    plant,climate,params,f = (values(s[k]) for k in ('plant_state','climate_state','parameters','forcing'))
    lai=p['sla']*plant['leaf'];capacity=params['leaf_heat_capacity']*lai
    offset=climate['canopy_sensible_energy']/capacity;tc=params['reference_temperature']+offset
    case=legacy_case(s,tc)
    crop=oracles['startup'](case,p,cp,oracles['plant'])
    y=[plant[k] for k in ('buffer','leaf','stem_root')]+[D(0),plant['temperature_filtered_24h'],plant['temperature_sum']]
    z=oracles['plant'](y,{'canopy_temperature':tc,'par_above_canopy':f['par_above_canopy'],'co2':f['co2']},
        {**values(s['removals']),'fruit':D(0)},p)
    allocation=z[1]+z[8]+values(s['removals'])['leaf']
    material=oracles['capacity']({'leaf_carbohydrate':plant['leaf'],'leaf_allocation':allocation,
        'leaf_maintenance':z[8],'leaf_removal':values(s['removals'])['leaf'],
        'leaf_heat_capacity':params['leaf_heat_capacity'],'canopy_temperature':tc,
        'incoming_capacity_temperature':f['incoming_capacity_temperature'],
        'reference_temperature':params['reference_temperature']},p['sla'])
    _,_,thermal=oracles['thermal']((tc,climate['air_temperature'],climate['air_vapor_mass']),
        {'leaf_area_index':lai,**{k:params[k] for k in params if k!='reference_temperature'}},
        {k:f[k] for k in ('canopy_external_heat','air_external_sensible_heat','air_external_vapor')},ep)
    e,h,le=(thermal[k] for k in ('water_vapor','sensible_heat','latent_heat'))
    du=f['canopy_external_heat']-h-le+material['energy_net']
    da=(f['air_external_sensible_heat']+h)/thermal['air_capacity']
    dm=e+f['air_external_vapor']
    temperature_rate=(du-offset*material['capacity_net'])/capacity
    assert abs(du+thermal['air_capacity']*da+ep['latent_heat']*dm-f['canopy_external_heat']-
        f['air_external_sensible_heat']-ep['latent_heat']*f['air_external_vapor']-material['energy_net']) < D('1e-65')
    return {'derived':{k:str(v) for k,v in (('canopy_temperature',tc),('leaf_area_index',lai),
        ('canopy_capacity',capacity),('air_capacity',thermal['air_capacity']),('air_vapor_pressure',thermal['air_pressure']),
        ('canopy_temperature_rate',temperature_rate))},
        'climate_derivatives':{k:str(v) for k,v in (('canopy_sensible_energy',du),('air_temperature',da),('air_vapor_mass',dm))},
        'plant_derivatives':crop['plant_derivatives'],'dC':crop['dC'],'dN':crop['dN'],
        'exchange':{k:str(thermal[k]) for k in ('water_vapor','sensible_heat','latent_heat')},
        'capacity_rates':{k:str(material['capacity_'+k]) for k in ('allocation','maintenance','removal','net')},
        'material_energy':{k:str(material['energy_'+k]) for k in ('incoming','maintenance_outgoing','removal_outgoing','net')},
        'crop_diagnostics':{k:crop[k] for k in ('photosynthesis','growth_respiration','fruit_allocation','deferred_fruit_allocation')}}


def references():
    for name,digest in INPUTS.items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    def profile(name,source=False):
        d=json.loads((ROOT/('fixtures/'+name)).read_bytes())['parameters']
        return {k:D(v['source_value'] if source else str(v['value'])) for k,v in d.items()}
    p=profile('crop-growth-reference-parameters-v1.json');cp=profile('crop-fruit-cohort-reference-parameters-v1.json',True)
    ep=profile('crop-canopy-exchange-reference-parameters-v1.json')
    oracles={'startup':runpy.run_path(str(ROOT/'research/crop-plant-startup-reference.py'))['calculate'],
        'plant':runpy.run_path(str(ROOT/'research/crop-integration-reference.py'))['decimal_rhs'],
        'thermal':runpy.run_path(str(ROOT/'research/crop-canopy-air-dynamics-reference.py'))['rhs'],
        'capacity':runpy.run_path(str(ROOT/'research/crop-canopy-energy-transport-reference.py'))['transport']}
    source=json.loads((ROOT/'fixtures/crop-plant-startup-reference-cases-v1.json').read_bytes())['cases']
    programs=[('warm-day',3,'22','18','.04','14','0',False),
        ('reverse',3,'20','25','.08','14','0',False),('cool-dark',3,'18','22','.05','22','0',True),
        ('empty-entry',12,'20','18','.04','14','0',False),('empty-no-entry',11,'20','18','.04','14','0',False),
        ('warm-reference30',3,'22','18','.04','14','30',False),('warm-reference22',3,'22','18','.04','14','22',False),
        ('equal-incoming-temperature',3,'22','18','.04','22','0',False),
        ('explicit-removal',3,'22','18','.04','14','0',False),('gross-turnover',3,'22','18','.04','14','0',False)]
    cases=[]
    with localcontext() as context:
        context.prec=80
        for name,index,tc,ta,mass,tin,ref,dark in programs:
            old=deepcopy(source[index]);leaf=D(str(old['state']['values']['leaf']['value']))
            scenario={'input_id':'synthetic-joint-'+name,'origin':'synthetic',
                'plant_state':old['state']['values'],
                'cohort_state':{k:old['cohort_state']['values'][k] for k in ('fruit_carbohydrate','fruit_number')},
                'relative_growth_rate':{'fruit_relative_growth_rate':old['cohort_state']['values']['fruit_relative_growth_rate']},
                'climate_state':{'canopy_sensible_energy':q(D('1200')*p['sla']*leaf*(D(tc)-D(ref)),'J/m2_floor'),
                    'air_temperature':q(ta,'degC'),'air_vapor_mass':q(mass,'kg_water/m2_floor')},
                'parameters':{k:q(v,u) for k,v,u in (('leaf_heat_capacity','1200','J/m2_leaf/K'),
                    ('air_volume_per_floor_area','4','m3/m2_floor'),('air_capacity_density','1.2','kg_air/m3'),
                    ('canopy_vapor_resistance','82','s/m'),('vapor_gas_constant','461','J/kg_water/K'),('reference_temperature',ref,'degC'))},
                'forcing':{'canopy_external_heat':q('150','W/m2_floor'),'air_external_sensible_heat':q('20','W/m2_floor'),
                    'air_external_vapor':q('-.000001','kg_water/m2_floor/s'),'incoming_capacity_temperature':q(tin,'degC'),
                    'par_above_canopy':q('0' if dark else '500','umol_photons/m2_floor/s'),'co2':q('600','ppm')},
                'removals':old['removals']['values'],'fruit_entry':old['fruit_entry']['values']}
            scenario['plant_state']['temperature_filtered_24h']=q('19.5','degC')
            if name=='explicit-removal':scenario['removals']['leaf']=q('2','mg_CH2O/m2_floor/s')
            if name=='gross-turnover':
                plant=values(scenario['plant_state']);y=[plant[k] for k in ('buffer','leaf','stem_root')]+[D(0),plant['temperature_filtered_24h'],plant['temperature_sum']]
                z=oracles['plant'](y,{'canopy_temperature':D(tc),'par_above_canopy':D('500'),'co2':D('600')},
                    {'leaf':D(0),'stem_root':D(0),'fruit':D(0)},p)
                scenario['removals']['leaf']=q(z[1],'mg_CH2O/m2_floor/s')
            cases.append({'case_id':name,'scenario':scenario,'expected_decimal':calculate(scenario,p,cp,ep,oracles)})
    return {'version':'crop-climate-joint-rhs-reference-cases-v1','scope':'synthetic_software_reference_only',
        'oracle':'Decimal80_pinned_independent_crop_startup_exchange_capacity_equations_no_app_import',
        'input_sha256':dict(INPUTS),'input_basis':'explicit synthetic stage cases; capLeaf/Tin/RGR not cultivar evidence; no time integration or actual tissue-water/metabolic energy model',
        'cases':cases}


if __name__=='__main__':print(json.dumps(references(),sort_keys=True,indent=2))
