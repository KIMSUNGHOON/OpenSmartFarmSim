"""Independent Decimal80 solar149-vector RK4, pinned equations, no app imports."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
D = Decimal
INPUTS = {
    'research/crop-greenhouse-radiation-par-integration-reference.py': 'fd36df9fda10e6ede0f4873905f6e831e6fefe7665722ee13b7d94263efd9fbe',
    'fixtures/crop-greenhouse-radiation-par-integration-reference-cases-v1.json': 'cac16f0edd1c0b6296a50a7704796d50912e83699663406d776a46b7d6a798a4',
    'fixtures/crop-greenhouse-radiation-nir-reference-cases-v1.json': '3398869d04479885ff92f1d31c234251f064e6d4a66f60fc0e7f6b7669438c61',
    'research/crop-greenhouse-radiation-nir-reference.py': '42f315d1f539ab4e5f4d03f650d51723acce8c632c85a72da2028fa6ac78ef74'}
NIR_FIELDS = ('outdoor', 'available_virtual', 'canopy_absorbed', 'floor_absorbed',
    'upward_virtual', 'construction_unallocated')


def environment():
    for name, digest in INPUTS.items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    prior = runpy.run_path(str(ROOT/'research/crop-greenhouse-radiation-par-integration-reference.py'))
    return {'prior': prior, 'base': prior['environment']()}


def nir(solar, lai):
    v = {k: D.from_float(float(q['value'])) for k, q in solar['values'].items()}
    one = D(1); c, f = v['cover_nir_reflectance'], v['floor_nir_reflectance']
    x, y = one-c, one-f
    t = (-v['nir_extinction_coefficient']*lai).exp()
    r = v['canopy_nir_reflectance']*(one-t)
    a = (one-v['canopy_nir_reflectance'])*(one-t)
    # Independent expanded cavity; current Decimal trial LAI is never rounded to binary64.
    determinant = x*y+(c*y+x*f)*(t+a)+c*f*a*(a+2*t)
    canopy = a*x*(y+f*(a+2*t))/determinant
    floor = x*y*t/determinant
    reflected = c+x*x*(r*(y+f*(t+a))+f*t*t)/determinant
    outside = v['outdoor_global_radiation']*v['solar_nir_fraction']
    available = (one-v['construction_interception_fraction'])*outside
    return (outside, available, available*canopy, available*floor, available*reflected,
        v['construction_interception_fraction']*outside)


def rhs(s, solar, weather, y, e):
    near = nir(solar, e['base']['env']['p']['sla']*y[1])
    forcing = deepcopy(s['forcing'])
    other = D(str(forcing.pop('canopy_non_solar_heat')['value']))
    forcing['canopy_non_par_heat'] = {'value': other+near[2], 'unit': 'W/m2_floor'}
    prior = e['prior']['rhs']({**s, 'forcing': forcing}, solar, weather, y, e['base'])
    return prior[:133]+(other,)+prior[134:]+near


def trajectory(s, solar, weather, dt, count, e):
    base = e['base']
    flow = base['prior']['FLOW']+base['vent']['EXTRA']+('canopy_non_solar_heat',)+tuple(
        'solar_par_'+k for k in e['prior']['PAR_FIELDS'])+tuple('solar_nir_'+k for k in NIR_FIELDS)
    y = base['prior']['initial'](s)+(D(0),)*len(flow)
    for _ in range(count):
        a = rhs(s, solar, weather, y, e)
        b = rhs(s, solar, weather, tuple(v+dt*k/2 for v, k in zip(y, a, strict=True)), e)
        c = rhs(s, solar, weather, tuple(v+dt*k/2 for v, k in zip(y, b, strict=True)), e)
        d = rhs(s, solar, weather, tuple(v+dt*k for v, k in zip(y, c, strict=True)), e)
        y = tuple(v+dt*(p+2*q+2*r+t)/6 for v, p, q, r, t in zip(y, a, b, c, d, strict=True))
    params = base['env']['prior']['values'](s['parameters'])
    capacity = params['leaf_heat_capacity']*base['env']['p']['sla']*y[1]
    return {'state': list(map(str, y[:108])), 'integrated_transfers': dict(zip(flow, map(str, y[108:]), strict=True)),
        'derived': {'canopy_temperature': str(params['reference_temperature']+y[105]/capacity),
            'leaf_area_index': str(base['env']['p']['sla']*y[1]), 'canopy_capacity': str(capacity)}}


def references():
    e = environment()
    source = json.loads((ROOT/'fixtures/crop-greenhouse-radiation-par-integration-reference-cases-v1.json').read_bytes())['cases']
    near = json.loads((ROOT/'fixtures/crop-greenhouse-radiation-nir-reference-cases-v1.json').read_bytes())['cases'][0]['scenario']['values']
    cases = []
    with localcontext() as context:
        context.prec = 80
        for index, original in enumerate([*source, source[0]]):
            s, solar, weather = (deepcopy(original[k]) for k in ('scenario', 'solar', 'ventilation'))
            s['forcing']['canopy_non_solar_heat'] = s['forcing'].pop('canopy_non_par_heat')
            solar['values'].update(deepcopy({k: v for k, v in near.items() if k not in (
                'leaf_area_index', 'outdoor_global_radiation', 'construction_interception_fraction')}))
            name = original['case_id'].replace('non-PAR', 'non-solar')
            if index == 6:
                name = 'zero-NIR'; solar['values']['solar_nir_fraction']['value'] = 0
                solar['values']['solar_par_fraction']['value'] = 1
            row = {'case_id': name, 'scenario': s, 'solar': solar, 'ventilation': weather,
                'step_seconds': 2, 'step_count': 16,
                'expected_decimal': trajectory(s, solar, weather, D(2), 16, e)}
            if index < 3:
                row['fine_32s_dt0_25_decimal'] = trajectory(s, solar, weather, D('.25'), 128, e)
            cases.append(row)
    return {'version': 'crop-greenhouse-solar-integration-reference-cases-v1',
        'generator_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_sha256': {**INPUTS, **e['prior']['INPUTS'],
            str(e['base']['vent']['PRIOR'].relative_to(ROOT)): e['base']['vent']['PRIOR_SHA256'],
            **e['base']['prior']['INPUTS'], **e['base']['env']['prior']['INPUTS']},
        'oracle': 'Decimal80_independent149_vector_RK4_expanded_NIR_cavity_no_app_import',
        'scope': 'self_authored_synthetic_math_only', 'G0_G4': 'not_assessed', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as output:
        output.write(json.dumps(references(), indent=2, sort_keys=True, allow_nan=False)+'\n')
