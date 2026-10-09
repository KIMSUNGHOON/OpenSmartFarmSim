"""Independent Decimal-80 transcription for the fixed canopy exchange test cases."""
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = '1e032ced2ffdaf8ba713184e89b628cce4173c9e7231f30710afeda8fbf20110'
UNITS = {'leaf_area_index':'m2_leaf/m2_floor','canopy_temperature':'degC','air_temperature':'degC',
    'air_vapor_pressure':'Pa','air_capacity_density':'kg_air/m3','canopy_vapor_resistance':'s/m'}


def references():
    raw = (ROOT/'fixtures/crop-canopy-exchange-reference-parameters-v1.json').read_bytes()
    assert sha256(raw).hexdigest() == PROFILE
    p = {k:Decimal(str(v['value'])) for k,v in json.loads(raw)['parameters'].items()}
    cases = [('warm', (2,20,18,1500,1.2,82)), ('reverse', (3,20,25,4000,1.2,82)),
        ('empty', (0,20,18,1500,1.2,82)), ('isothermal', (2,25,25,1500,1.2,82)),
        ('resistant', (4,30,22,1800,1.18,1000000))]
    result = []
    with localcontext() as context:
        context.prec = 80
        for name,values in cases:
            f = dict(zip(UNITS, map(lambda v:Decimal(str(v)), values)))
            t,area = f['canopy_temperature'], f['leaf_area_index']
            svp = p['saturation_pressure_coefficient'] * (
                p['saturation_exponent_factor'] * t / (t+p['saturation_denominator_offset'])).exp()
            delta = svp-f['air_vapor_pressure']
            conductance = (p['leaf_surface_factor']*f['air_capacity_density']*p['air_heat_capacity']*area /
                (p['latent_heat']*p['psychrometric_constant']*(p['boundary_resistance']+f['canopy_vapor_resistance'])))
            water = conductance*delta
            heat = p['leaf_surface_factor']*p['leaf_air_heat_transfer']*area*(t-f['air_temperature'])
            latent = p['latent_heat']*water
            expected = dict(zip(('saturation_pressure','vapor_difference','coefficient','water_vapor',
                'sensible_heat','latent_heat','canopy_total_heat_outflow'),(svp,delta,conductance,water,heat,latent,heat+latent)))
            result.append({'case_id':name,'forcing':{'input_id':'synthetic-canopy-'+name,'origin':'synthetic',
                'values':{k:{'value':float(f[k]),'unit':UNITS[k]} for k in UNITS}},
                'expected_decimal':{k:str(value) for k,value in expected.items()}})
    return {'version':'crop-canopy-exchange-reference-cases-v1','scope':'synthetic_software_reference_only',
        'profile_sha256':PROFILE,'oracle':'independent_Decimal_80_source_transcription_no_app_import',
        'forcing_basis':'explicit synthetic cases; density and resistance are not site/cultivar defaults',
        'cases':result}


if __name__ == '__main__':
    print(json.dumps(references(),sort_keys=True,indent=2))
