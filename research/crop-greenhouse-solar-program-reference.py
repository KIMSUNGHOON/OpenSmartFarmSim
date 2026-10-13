"""App-free Decimal80 solar149-vector RK and independent atomic retention."""
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
    'research/crop-greenhouse-solar-integration-reference.py': '22a3996d7b2ed0bbdf4187e349a84d1c4466c4dbdfb70451c258aa95ed178574',
    'fixtures/crop-greenhouse-solar-integration-reference-cases-v1.json': '511a791251ad9a4e100f2f7cecc79177f7e386c3ad8a6ccd9613214a0c367bf8',
    'research/crop-climate-joint-boundary-reference.py': 'b6971db93a43632021c58b2a5ee4e195cdc9108b3d1cb7d183abe3d68ac6ab3b',
    'fixtures/crop-climate-joint-boundary-reference-cases-v1.json': 'd49dafbbba95f84d141d9b4845111ec08ff65690e45e4166c3aaac149a22c784'}


def trajectory(case, dt, solar, environment, old, management, prior, env):
    s, sun, weather = (case[k] for k in ('scenario', 'solar', 'ventilation'))
    base_dt = D(str(case['step_seconds']))
    def index(i):
        scaled = D(i)*base_dt/dt
        assert scaled == int(scaled)
        return int(scaled)
    count = index(case['step_count'])
    schedule = {index(row['step_index']): row['event'] for row in case['events']}
    outputs = {index(i) for i in case['output_steps']}
    flow = prior['FLOW']+environment['base']['vent']['EXTRA']+('canopy_non_solar_heat',)+tuple(
        'solar_par_'+k for k in environment['prior']['PAR_FIELDS'])+tuple('solar_nir_'+k for k in solar['NIR_FIELDS'])
    y = prior['initial'](s)+(D(0),)*len(flow)
    events = {k: D(0) for k in management['EVENT_FIELDS']}
    samples, journal = [], []
    rhs = lambda z: solar['rhs'](s, sun, weather, z, environment)
    for i in range(count+1):
        if i:
            a = rhs(y)
            b = rhs(tuple(v+dt*k/2 for v, k in zip(y, a, strict=True)))
            c = rhs(tuple(v+dt*k/2 for v, k in zip(y, b, strict=True)))
            d = rhs(tuple(v+dt*k for v, k in zip(y, c, strict=True)))
            y = tuple(v+dt*(p+2*q+2*r+t)/6 for v, p, q, r, t in zip(y, a, b, c, d, strict=True))
        if i in schedule:
            before = list(map(str, y[:108]))
            current = prior['trial'](s, y[:108])
            _, removed = management['removal'](current, schedule[i], prior, env)
            increment = {k: sum(map(D, v)) if isinstance(v, list) else D(v) for k, v in removed['removed'].items()}
            events = {k: events[k]+increment[k] for k in events}
            y = tuple(map(D, removed['state']))+y[108:]
            journal.append({'step_index': i, 'elapsed_seconds': str(i*dt), 'before': before,
                'after': removed['state'], 'removed_totals': {k: str(v) for k, v in increment.items()}})
        t = dict(zip(flow, y[108:], strict=True))
        old['balances'](s, y, t, events, prior, env)
        partitions = [t['air_external_sensible_heat']-D(str(s['forcing']['air_external_sensible_heat']['value']))*i*dt-t['ventilation_sensible_heat'],
            t['air_external_vapor']-D(str(s['forcing']['air_external_vapor']['value']))*i*dt-t['ventilation_vapor'],
            t['ventilation_latent_energy']-env['ep']['latent_heat']*t['ventilation_vapor'],
            t['canopy_external_heat']-t['canopy_non_solar_heat']-t['solar_par_canopy_absorbed']-t['solar_nir_canopy_absorbed'],
            t['solar_par_above_canopy']-sum(t['solar_par_'+k] for k in ('canopy_absorbed','floor_absorbed','unresolved_reflected','upward_transmitted')),
            t['solar_par_outdoor']-sum(t['solar_par_'+k] for k in ('above_canopy','cover_reflected','cover_absorbed','construction_intercepted')),
            t['solar_nir_available_virtual']-sum(t['solar_nir_'+k] for k in ('canopy_absorbed','floor_absorbed','upward_virtual')),
            t['solar_nir_outdoor']-t['solar_nir_available_virtual']-t['solar_nir_construction_unallocated']]
        assert max(map(abs, partitions)) < D('1e-60')
        if i in outputs:
            samples.append({'step_index': i, 'elapsed_seconds': str(i*dt), 'state': list(map(str, y[:108])),
                'integrated_transfers': {k: str(v) for k, v in t.items()},
                'event_totals': {k: str(v) for k, v in events.items()}, 'event_count': len(journal),
                'derived': management['derived'](s, y, env)})
    return {'samples': samples, 'events': journal}


def references():
    for name, digest in INPUTS.items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    solar = runpy.run_path(str(ROOT/'research/crop-greenhouse-solar-integration-reference.py'))
    environment = solar['environment']()
    old = runpy.run_path(str(ROOT/'research/crop-climate-joint-boundary-reference.py'))
    management, prior, env = old['environment']()
    source = json.loads((ROOT/'fixtures/crop-climate-joint-boundary-reference-cases-v1.json').read_bytes())['cases']
    boundary = json.loads((ROOT/'fixtures/crop-greenhouse-solar-integration-reference-cases-v1.json').read_bytes())['cases'][0]
    cases = []
    with localcontext() as context:
        context.prec = 80
        for position, original in enumerate([*source, source[1], source[1]]):
            c = deepcopy({k: original[k] for k in ('case_id','scenario','events','output_steps','step_seconds','step_count')})
            s = c['scenario']; s['forcing']['canopy_non_solar_heat'] = s['forcing'].pop('canopy_external_heat')
            s['forcing'].pop('par_above_canopy')
            c['solar'], c['ventilation'] = (deepcopy(boundary[k]) for k in ('solar','ventilation'))
            c['solar']['input_id'] = 'solar-program-'+str(position)
            c['ventilation']['input_id'] = 'weather-program-'+str(position)
            if c['case_id'] == 'dark-mid': c['solar']['values']['outdoor_global_radiation']['value'] = 0
            if c['case_id'] == 'reverse-mid':
                c['ventilation']['forcing']['outdoor_air_temperature']['value'] = 28
                c['ventilation']['forcing']['outdoor_vapor_pressure']['value'] = 2800
            if position == len(source):
                c['case_id'] = 'zero-ventilation'; c['ventilation']['forcing']['volume_exchange_per_floor_area']['value'] = 0
            if position == len(source)+1:
                c['case_id'] = 'zero-NIR'; c['solar']['values']['solar_nir_fraction']['value'] = 0
                c['solar']['values']['solar_par_fraction']['value'] = 1
            c['expected_decimal'] = trajectory(c, D(2), solar, environment, old, management, prior, env)
            if c['case_id'] in ('warm-mid','reverse-mid','dark-mid'):
                c['fine_32s_dt0_25_decimal'] = trajectory(c, D('.25'), solar, environment, old, management, prior, env)
            cases.append(c)
    return {'version': 'crop-greenhouse-solar-program-reference-cases-v1',
        'generator_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_sha256': {**INPUTS, **solar['INPUTS'], **old['INPUTS'], **management['INPUTS'],
            **prior['INPUTS'], **env['prior']['INPUTS']},
        'oracle': 'Decimal80_independent149_vector_solar_RK4_and_capacity_energy_retention_no_app_import',
        'scope': 'self_authored_synthetic_math_only', 'G0_G4': 'not_assessed', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as output:
        output.write(json.dumps(references(), indent=2, sort_keys=True, allow_nan=False)+'\n')
