"""Independent Decimal80 event-grid oracle; immutable source cases, no app imports."""
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
    'research/crop-climate-joint-boundary-reference.py': 'b6971db93a43632021c58b2a5ee4e195cdc9108b3d1cb7d183abe3d68ac6ab3b',
    'research/crop-greenhouse-ventilation-joint-reference.py': '02cbd0c0e4d69ed0f52610baa82fc670a2991e6b446a2ec220b09ce04f0ba077',
    'fixtures/crop-climate-joint-boundary-reference-cases-v1.json': 'd49dafbbba95f84d141d9b4845111ec08ff65690e45e4166c3aaac149a22c784'}


def trajectory(case, weather, dt, old, ventilation, management, prior, env):
    s = case['scenario']
    base_dt = D(str(case['step_seconds']))
    count = int(base_dt*case['step_count']/dt)
    assert count*dt == base_dt*case['step_count']
    def index(i):
        scaled = D(i)*base_dt/dt
        assert scaled == int(scaled)
        return int(scaled)
    schedule = {index(row['step_index']): row['event'] for row in case['events']}
    outputs = {index(i) for i in case['output_steps']}
    flow = prior['FLOW']+ventilation['EXTRA']
    y = prior['initial'](s)+(D(0),)*25
    events = {k: D(0) for k in management['EVENT_FIELDS']}
    samples, journal = [], []
    rhs = lambda z: ventilation['rhs'](s, weather, z, env, prior)
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
        totals = dict(zip(flow, y[108:], strict=True))
        old['balances'](s, y, totals, events, prior, env)
        partitions = [totals['air_external_sensible_heat']-D(str(s['forcing']['air_external_sensible_heat']['value']))*i*dt-totals['ventilation_sensible_heat'],
            totals['air_external_vapor']-D(str(s['forcing']['air_external_vapor']['value']))*i*dt-totals['ventilation_vapor'],
            totals['ventilation_latent_energy']-env['ep']['latent_heat']*totals['ventilation_vapor']]
        assert max(map(abs, partitions)) < D('1e-60')
        if i in outputs:
            samples.append({'step_index': i, 'elapsed_seconds': str(i*dt), 'state': list(map(str, y[:108])),
                'integrated_transfers': {k: str(v) for k, v in totals.items()},
                'event_totals': {k: str(v) for k, v in events.items()}, 'event_count': len(journal),
                'derived': management['derived'](s, y, env)})
    return {'samples': samples, 'events': journal}


def references():
    for name, digest in INPUTS.items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == digest
    old = runpy.run_path(str(ROOT/'research/crop-climate-joint-boundary-reference.py'))
    ventilation = runpy.run_path(str(ROOT/'research/crop-greenhouse-ventilation-joint-reference.py'))
    management, prior, env = old['environment']()
    source = json.loads((ROOT/'fixtures/crop-climate-joint-boundary-reference-cases-v1.json').read_bytes())['cases']
    definitions = [(c, ventilation['weather']('program-'+c['case_id'], *(
        (28, 2800, .008) if c['case_id']=='reverse-mid' else (26, 1200, .010) if c['case_id']=='dark-mid' else (16, 800, .015)))) for c in source]
    definitions.append((source[0], ventilation['weather']('zero-ventilation', flow=0)))
    cases = []
    with localcontext() as context:
        context.prec = 80
        for position, (case, weather) in enumerate(definitions):
            row = {'case_id': case['case_id'] if position < len(source) else 'zero-ventilation',
                'source_case_id': case['case_id'], 'ventilation': weather,
                'expected_decimal': trajectory(case, weather, D(2), old, ventilation, management, prior, env)}
            if row['case_id'] in ('warm-mid', 'reverse-mid', 'dark-mid'):
                row['fine_32s_dt0_25_decimal'] = trajectory(case, weather, D('.25'), old, ventilation, management, prior, env)
            cases.append(row)
    return {'version': 'ventilation-management-program-reference-cases-v1',
        'generator_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_sha256': {**INPUTS, **old['INPUTS'], **management['INPUTS'], **prior['INPUTS'], **env['prior']['INPUTS']},
        'source_cases': 'fixtures/crop-climate-joint-boundary-reference-cases-v1.json',
        'oracle': 'Decimal80_independent_133_vector_RK4_retention_events_no_app_import',
        'scope': 'self_authored_synthetic_math_only', 'G0_G4': 'not_assessed', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as output:
        json.dump(references(), output, indent=2, sort_keys=True, allow_nan=False)
        output.write('\n')
