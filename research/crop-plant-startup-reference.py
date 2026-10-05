"""Independent Decimal whole-plant empty-sink reference; no product imports."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    'fixtures/crop-growth-reference-parameters-v1.json': 'd606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca',
    'fixtures/crop-fruit-cohort-reference-parameters-v1.json': 'b453b4ffe618f26041e4ec6a1b1b7d2e5f38edb3d42adaaad4fa3cd4fbb99cbb',
    'fixtures/crop-plant-cohort-reference-cases-v1.json': 'a5a35ae7baacaae4f1e87f7734005a9e40fb19f64dc0f2c0363fbe1a2bd96a58',
    'research/crop-integration-reference.py': 'a38b7a67e43cf9f590838bf915ab3e5048950b8be6ed35f70817e18b42a09ce7',
    'research/crop-fruit-startup-source-register.json': '882022c483ef935bfca5002059490244d0466e370b8f2d33b5551d8408f2ee1d',
}


def calculate(case, p, cp, rhs):
    state, cohorts = case['state']['values'], case['cohort_state']['values']
    N, C, RGR = ([Decimal(str(q['value'])) for q in cohorts[name]] for name in (
        'fruit_number', 'fruit_carbohydrate', 'fruit_relative_growth_rate'))
    T = Decimal(str(state['temperature_filtered_24h']['value']))
    # Fruit aggregate is unused: final fruit derivatives/maintenance come from 50 cohorts.
    y = [Decimal(str(state[k]['value'])) for k in ('buffer', 'leaf', 'stem_root')]
    y += [Decimal(0), T, Decimal(str(state['temperature_sum']['value']))]
    forcing = {k: Decimal(str(q['value'])) for k, q in case['forcing']['values'].items()}
    removed = {k: Decimal(str(q['value'])) for k, q in case['removals']['values'].items()}
    z = rhs(y, forcing, {**removed, 'fruit': Decimal(0)}, p)
    requested = z[3]
    S, W1 = (Decimal(str(case['fruit_entry']['values'][k]['value'])) for k in (
        'fruit_number_inflow', 'fruit_entry_carbohydrate'))
    rate = cp['cDev1'] + cp['cDev2']*T
    period = 1/(rate*cp['seconds_per_day'])
    peak = cp['Gompertz_M_intercept'] + cp['Gompertz_M_slope']*period
    steepness = 1/(cp['Gompertz_B_intercept'] + cp['Gompertz_B_M_slope']*peak)
    ages = [(Decimal(j)-cp['stage_age_midpoint'])/cp['nDev']*period for j in range(1, 51)]
    growth = [cp['GMax']*steepness*(-steepness*(t-peak)).exp()*
              (-(-steepness*(t-peak)).exp()).exp() for t in ages]
    weights = [n*g for n, g in zip(N, growth, strict=True)]
    entry = S*W1
    assert entry <= requested
    actual = requested if sum(weights[1:]) else entry
    deferred = requested-actual
    allocated = [entry] + [(actual-entry)*w/sum(weights[1:]) if actual>entry else Decimal(0)
                           for w in weights[1:]]
    temperature_factor = (cp['Q10'].ln()*(T-cp['maintenance_temperature_reference_c']) /
                          cp['q10_temperature_interval_c']).exp()
    maintenance = [cp['fruit_maintenance']*c*(1-(-cp['cRgr']*r).exp())*temperature_factor
                   for c, r in zip(C, RGR, strict=True)]
    transfer = cp['nDev']*rate
    dN = [transfer*((N[j-1] if j else 0)-N[j]) + (S if j==0 else 0) for j in range(50)]
    dC = [transfer*((C[j-1] if j else 0)-C[j])+allocated[j]-maintenance[j] for j in range(50)]
    terminalC, terminalN = transfer*C[-1], transfer*N[-1]
    leaf_allocation, stem_allocation = z[1]+z[8]+removed['leaf'], z[2]+z[9]+removed['stem_root']
    fruit_respiration = p['cFruitG']*actual
    total_growth = p['cLeafG']*leaf_allocation+p['cStemG']*stem_allocation+fruit_respiration
    adjustment = (1+p['cFruitG'])*deferred
    buffer_rate = z[0]+adjustment
    carbon_terms = [buffer_rate, z[1], z[2], *dC, total_growth, z[8], z[9],
                    *maintenance, *removed.values(), terminalC, -z[6]]
    number_terms = [*dN, terminalN, -S]
    for terms in (carbon_terms, number_terms):
        assert abs(sum(terms)) <= max(Decimal(1), *map(abs, terms))*Decimal('1e-50')
    return {
        'requested_fruit_allocation': str(requested), 'fruit_allocation': str(actual),
        'deferred_fruit_allocation': str(deferred), 'buffer_adjustment': str(adjustment),
        'fruit_growth_respiration': str(fruit_respiration), 'growth_respiration': str(total_growth),
        'fruit_buffer_debit': str(actual+fruit_respiration), 'photosynthesis': str(z[6]),
        'fruit_carbohydrate_total': str(sum(C)), 'fruit_maintenance': str(sum(maintenance)),
        'terminal_carbohydrate': str(terminalC), 'terminal_number': str(terminalN),
        'lai': str(p['sla']*y[1]),
        'plant_derivatives': {k: str(v) for k, v in (
            ('buffer', buffer_rate), ('leaf', z[1]), ('stem_root', z[2]),
            ('temperature_filtered_24h', z[4]), ('temperature_sum', z[5]))},
        'allocation': list(map(str, allocated)), 'maintenance': list(map(str, maintenance)),
        'dC': list(map(str, dC)), 'dN': list(map(str, dN)),
    }


def references():
    for path, digest in INPUTS.items():
        assert sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
    old = json.loads((ROOT/'fixtures/crop-plant-cohort-reference-cases-v1.json').read_bytes())['cases']
    p = {k: Decimal(str(v['value'])) for k, v in json.loads(
        (ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes())['parameters'].items()}
    cp = {k: Decimal(v['source_value']) for k, v in json.loads(
        (ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes())['parameters'].items()}
    rhs = runpy.run_path(str(ROOT/'research/crop-integration-reference.py'))['decimal_rhs']
    cases = deepcopy(old)
    for case in cases:
        case['case_id'] += '-positive-tail'
    for index, temperature in ((0, 17), (2, 20), (4, 23)):
        for pattern in ('empty-no-entry', 'empty-entry', 'first-only', 'small-tail', 'large-tail'):
            case = deepcopy(old[index+1])
            identifier = f'synthetic-startup-{temperature}C-{pattern}'
            case['case_id'] = identifier
            for block in ('state', 'cohort_state', 'forcing', 'removals', 'fruit_entry'):
                case[block]['input_id'] = identifier+'-'+block
            c = case['cohort_state']['values']
            for name in ('fruit_number', 'fruit_carbohydrate'):
                for j, q in enumerate(c[name]):
                    if pattern in ('empty-no-entry', 'empty-entry', 'first-only'):
                        q['value'] = (.25 if name=='fruit_number' else 10) if pattern=='first-only' and j==0 else 0
                    else:
                        factor = Decimal('1e-200') if pattern=='small-tail' else Decimal('1e200')
                        q['value'] = float(Decimal(str(q['value']))*factor)
            c['fruit_relative_growth_rate'][0]['value'] = 3e-6
            if pattern=='empty-no-entry':
                for q in case['fruit_entry']['values'].values(): q['value'] = 0
            cases.append(case)
    zero = deepcopy(cases[6]); zero['case_id'] = 'synthetic-startup-zero-buffer-request'
    zero['state']['values']['buffer']['value'] = 0
    for block in ('state', 'cohort_state', 'forcing', 'removals', 'fruit_entry'):
        zero[block]['input_id'] = zero['case_id']+'-'+block
    cases.append(zero)
    with localcontext() as ctx:
        ctx.prec = 70
        for case in cases:
            case['expected'] = calculate(case, p, cp, rhs)
    return {'fixture_version': 'crop-plant-startup-decimal-reference-v1',
        'scope': 'synthetic instantaneous math only; no actual cultivar, time integration or claim gates',
        'input_sha256': dict(INPUTS), 'generator_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'method': '70-digit Decimal plant RHS and original cohort equations; simultaneous buffer/realized-respiration policy',
        'cases': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'fixtures/crop-plant-startup-reference-cases-v1.json')
    args = parser.parse_args()
    if args.output.is_symlink() or args.output.resolve() in {
        Path(__file__).resolve(), *[(ROOT/k).resolve() for k in INPUTS]}:
        raise ValueError('reference_output_would_replace_input')
    result = references()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'cases': len(result['cases']), 'product_imports': False}))


if __name__ == '__main__':
    main()
