"""Independent Decimal reference for instantaneous explicit-entry cohorts."""

import argparse
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'fixtures/crop-fruit-cohort-reference-parameters-v1.json'
PROFILE_SHA256 = 'b453b4ffe618f26041e4ec6a1b1b7d2e5f38edb3d42adaaad4fa3cd4fbb99cbb'
VERSION = 'crop-fruit-cohort-decimal-reference-v1'


def references():
    raw = PROFILE.read_bytes()
    assert sha256(raw).hexdigest() == PROFILE_SHA256
    profile = json.loads(raw)
    p = {k: Decimal(v['source_value']) for k, v in profile['parameters'].items()}
    cases = []
    with localcontext() as context:
        context.prec = 60
        for temperature in (17, 20, 23):
            for pattern in ('zero', 'uniform', 'multiple', 'entry-only'):
                for rgr in ('zero', 'varying'):
                    N, C = [Decimal(0)] * 50, [Decimal(0)] * 50
                    if pattern == 'uniform':
                        N, C = [Decimal('0.2')] * 50, [Decimal('40')] * 50
                    elif pattern == 'multiple':
                        for j in range(50):
                            if j not in (7, 27):
                                N[j] = Decimal(j % 7 + 1) / 10
                                C[j] = N[j] * Decimal(42 + j) / 3
                    elif pattern == 'entry-only':
                        N[0], C[0] = Decimal('0.25'), Decimal('10')
                    RGR = [Decimal(0) if rgr == 'zero' else Decimal(j % 5) * Decimal('1e-6')
                           for j in range(50)]
                    identifier = f'synthetic-{temperature}C-{pattern}-{rgr}-RGR'
                    arrays = {name: [{'value': float(v), 'unit': unit} for v in array]
                              for name, array, unit in (
                        ('fruit_number', N, 'fruits_equivalent/m2_floor'),
                        ('fruit_carbohydrate', C, 'mg_CH2O/m2_floor'),
                        ('fruit_relative_growth_rate', RGR, '1/s'))}
                    arrays.update({'temperature_filtered_24h': {'value': temperature, 'unit': 'degC'},
                                   'temperature_sum': {'value': 1, 'unit': 'degC_day'}})
                    F, S, W1 = (('0', '0', '0') if pattern == 'zero' else
                                ('0.125', '0.03125', '4') if pattern == 'entry-only' else
                                ('0.1', '0.01', '1'))
                    inflow = {name: {'value': float(value), 'unit': unit} for name, value, unit in (
                        ('fruit_carbohydrate_inflow', F, 'mg_CH2O/m2_floor/s'),
                        ('fruit_number_inflow', S, 'fruits_equivalent/m2_floor/s'),
                        ('fruit_entry_carbohydrate', W1, 'mg_CH2O/fruit_equivalent'))}
                    N, C, RGR = ([Decimal(str(q['value'])) for q in arrays[name]] for name in (
                        'fruit_number', 'fruit_carbohydrate', 'fruit_relative_growth_rate'))
                    rate = p['cDev1'] + p['cDev2'] * temperature
                    period = 1 / (rate * p['seconds_per_day'])
                    peak = p['Gompertz_M_intercept'] + p['Gompertz_M_slope'] * period
                    steepness = 1 / (p['Gompertz_B_intercept'] + p['Gompertz_B_M_slope'] * peak)
                    ages = [(Decimal(j) - p['stage_age_midpoint']) / p['nDev'] * period for j in range(1, 51)]
                    growth = [p['GMax'] * steepness * (-steepness * (t - peak)).exp() *
                              (-(-steepness * (t - peak)).exp()).exp() for t in ages]
                    weights = [n * g for n, g in zip(N, growth, strict=True)]
                    temperature_factor = (p['Q10'].ln() * (Decimal(temperature) -
                        p['maintenance_temperature_reference_c']) / p['q10_temperature_interval_c']).exp()
                    maintenance = [p['fruit_maintenance'] * c * (1 - (-p['cRgr'] * r).exp()) * temperature_factor
                                   for c, r in zip(C, RGR, strict=True)]
                    F, S, W1 = map(Decimal, (F, S, W1))
                    entry, remainder = S * W1, F - S * W1
                    allocation = [entry] + [remainder * w / sum(weights[1:]) if remainder else Decimal(0)
                                           for w in weights[1:]]
                    transfer = p['nDev'] * rate
                    dN = [transfer * ((N[j-1] if j else 0) - N[j]) + (S if j == 0 else 0) for j in range(50)]
                    dC = [transfer * ((C[j-1] if j else 0) - C[j]) + allocation[j] - maintenance[j] for j in range(50)]
                    terminalN, terminalC = transfer * N[-1], transfer * C[-1]
                    growth_respiration = p['fruit_growth_respiration'] * F
                    debit = F + growth_respiration
                    for residual in (sum(dN) + terminalN - S,
                                     sum(dC) + terminalC + sum(maintenance) - F,
                                     sum(dC) + terminalC + sum(maintenance) + growth_respiration - debit):
                        assert abs(residual) <= Decimal('1e-50')
                    expected = {'development_rate': str(rate), 'fruit_growth_period': str(period),
                                'peak_age': str(peak), 'steepness': str(steepness),
                                'fruit_growth_respiration': str(growth_respiration),
                                'fruit_buffer_debit': str(debit),
                                'terminal_number': str(terminalN), 'terminal_carbohydrate': str(terminalC)}
                    for name, array in (('stage_age', ages), ('potential_growth', growth), ('weighted_demand', weights),
                                        ('allocation', allocation), ('maintenance', maintenance), ('dN', dN), ('dC', dC)):
                        expected[name] = list(map(str, array))
                    cases.append({'case_id': identifier,
                        'state': {'input_id': identifier, 'origin': 'synthetic', 'values': arrays},
                        'inflow': {'input_id': identifier + '-inflow', 'origin': 'synthetic', 'values': inflow},
                        'expected': expected})
    return {'fixture_version': VERSION, 'scope': 'synthetic instantaneous math only; no crop cycle or gate evidence',
            'method': '60-digit Decimal original Gompertz/transport/maintenance plus separately versioned allocation; no product imports',
            'profile_sha256': PROFILE_SHA256, 'generator_sha256': sha256(Path(__file__).read_bytes()).hexdigest(), 'cases': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'fixtures/crop-fruit-cohort-reference-cases-v1.json')
    args = parser.parse_args()
    if args.output.is_symlink() or args.output.resolve() in (PROFILE.resolve(), Path(__file__).resolve()):
        raise ValueError('reference_output_would_replace_input')
    document = references()
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'reference_cases': len(document['cases']), 'product_imports': False, 'profile_sha256': PROFILE_SHA256}))


if __name__ == '__main__':
    main()
