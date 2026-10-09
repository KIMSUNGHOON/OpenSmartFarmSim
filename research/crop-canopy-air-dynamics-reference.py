"""Independent Decimal-80 reduced dynamics oracle; no product-module imports."""
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_SHA256 = '1e032ced2ffdaf8ba713184e89b628cce4173c9e7231f30710afeda8fbf20110'
STATE_UNITS = {'canopy_temperature':'degC', 'air_temperature':'degC', 'air_vapor_mass':'kg_water/m2_floor'}
PARAMETER_UNITS = {'leaf_area_index':'m2_leaf/m2_floor', 'leaf_heat_capacity':'J/m2_leaf/K',
    'air_volume_per_floor_area':'m3/m2_floor', 'air_capacity_density':'kg_air/m3',
    'canopy_vapor_resistance':'s/m', 'vapor_gas_constant':'J/kg_water/K'}
FORCING_UNITS = {'canopy_external_heat':'W/m2_floor', 'air_external_sensible_heat':'W/m2_floor',
    'air_external_vapor':'kg_water/m2_floor/s'}
D = Decimal


def rhs(state, p, forcing, c):
    tc, ta, mv = state
    vp = mv * p['vapor_gas_constant'] * (ta+D('273.15')) / p['air_volume_per_floor_area']
    sat = c['saturation_pressure_coefficient'] * (
        c['saturation_exponent_factor']*tc/(tc+c['saturation_denominator_offset'])).exp()
    e = (c['leaf_surface_factor']*p['air_capacity_density']*c['air_heat_capacity']*p['leaf_area_index'] /
        (c['latent_heat']*c['psychrometric_constant']*(c['boundary_resistance']+p['canopy_vapor_resistance'])))*(sat-vp)
    h = c['leaf_surface_factor']*c['leaf_air_heat_transfer']*p['leaf_area_index']*(tc-ta)
    le = c['latent_heat']*e
    ccan = p['leaf_heat_capacity']*p['leaf_area_index']
    cair = p['air_volume_per_floor_area']*p['air_capacity_density']*c['air_heat_capacity']
    rates = ((forcing['canopy_external_heat']-h-le)/ccan,
        (forcing['air_external_sensible_heat']+h)/cair, e+forcing['air_external_vapor'])
    diagnostics = dict(zip(('air_pressure','canopy_capacity','air_capacity','water_vapor','sensible_heat',
        'latent_heat','canopy_temperature_rate','air_temperature_rate','air_vapor_mass_rate'),
        (vp,ccan,cair,e,h,le,*rates)))
    return rates, (e,h,le), diagnostics


def trajectory(initial, p, forcing, c, dt, count):
    state = initial
    totals = (D(0),)*3
    for _ in range(count):
        k1, j1, _ = rhs(state,p,forcing,c)
        k2, j2, _ = rhs(tuple(y+dt*k/2 for y,k in zip(state,k1)),p,forcing,c)
        k3, j3, _ = rhs(tuple(y+dt*k/2 for y,k in zip(state,k2)),p,forcing,c)
        k4, j4, _ = rhs(tuple(y+dt*k for y,k in zip(state,k3)),p,forcing,c)
        state = tuple(y+dt*(a+2*b+2*d+e)/6 for y,a,b,d,e in zip(state,k1,k2,k3,k4))
        totals = tuple(y+dt*(a+2*b+2*d+e)/6 for y,a,b,d,e in zip(totals,j1,j2,j3,j4))
    return {'state':dict(zip(STATE_UNITS,map(str,state))),
        'transfers':dict(zip(('water_vapor','sensible_heat','latent_heat'),map(str,totals)))}


def references():
    raw=(ROOT/'fixtures/crop-canopy-exchange-reference-parameters-v1.json').read_bytes()
    assert sha256(raw).hexdigest()==PROFILE_SHA256
    c={k:D(str(row['value'])) for k,row in json.loads(raw)['parameters'].items()}
    params=dict(zip(PARAMETER_UNITS,map(D,('2','1200','4','1.2','82','461'))))
    programs=(('warm',('20','18','0.04'),('0','0','0')),
        ('reverse',('20','25','0.08'),('0','0','0')),
        ('isothermal',('20','20','0.04'),('0','0','0')),
        ('forced',('22','18','0.04'),('150','20','-0.000001')))
    cases=[]
    with localcontext() as context:
        context.prec=80
        for name,initial,external in programs:
            state=tuple(map(D,initial));forcing=dict(zip(FORCING_UNITS,map(D,external)))
            scenario={'input_id':'synthetic-dynamic-'+name,'origin':'synthetic',
                'state':{k:{'value':float(v),'unit':STATE_UNITS[k]} for k,v in zip(STATE_UNITS,state)},
                'parameters':{k:{'value':float(v),'unit':PARAMETER_UNITS[k]} for k,v in params.items()},
                'forcing':{k:{'value':float(v),'unit':FORCING_UNITS[k]} for k,v in forcing.items()}}
            cases.append({'case_id':name,'scenario':scenario,
                'rhs_decimal':{k:str(v) for k,v in rhs(state,params,forcing,c)[2].items()},
                'trajectory_60s_dt1_decimal':trajectory(state,params,forcing,c,D(1),60),
                'trajectory_60s_dt0_25_decimal':trajectory(state,params,forcing,c,D('.25'),240)})
    return {'version':'crop-canopy-air-dynamics-reference-cases-v1',
        'scope':'synthetic_software_reference_only','profile_sha256':PROFILE_SHA256,
        'oracle':'independent_Decimal_80_RHS_and_RK4_no_app_import',
        'input_basis':'self-authored constant-LAI synthetic cases, not cultivar/site data; all capacities, geometry, density, resistance and gas constant explicit; capLeaf1200 equals a source example without adoption, Rv461 is an explicit synthetic assumption, not a source-ratio adoption',
        'cases':cases}


if __name__=='__main__':
    print(json.dumps(references(),sort_keys=True,indent=2))
