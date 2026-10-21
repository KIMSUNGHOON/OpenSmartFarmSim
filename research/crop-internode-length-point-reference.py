"""Independent Decimal800 points; explicit synthetic arithmetic, no cultivar data."""
import argparse
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path


def quantity(age):
    return {'numerator': str(age.numerator), 'denominator': str(age.denominator), 'unit': 'degC_day'}


def point_inputs(name, age, curve):
    return {'input_id': name, 'origin': 'synthetic', 'thermal_age_basis': 'since_internode_emergence',
            'age_exact': quantity(age), 'curve': deepcopy(curve)}


def reference():
    previous = json.loads((Path(__file__).resolve().parents[1] /
        'fixtures/crop-internode-length-state-reference-v1.json').read_bytes())['cases']
    cases = []
    for c in previous:
        clock = c['inputs']['clock_state']; a = clock['age_exact']
        age = Fraction(int(a['numerator']), int(a['denominator']))
        curve = c['inputs']['curve']; base = Fraction.from_float(float(clock['base_temperature']['value']))
        cases.append({'case_id': c['case_id'] + ':start', 'inputs': point_inputs(c['case_id'] + ':start', age, curve),
                      'expected_length_m': c['expected_length_m'], 'reference': 'retained independent Decimal800 initial point'})
        for s in c['segments']:
            duration = datetime.fromisoformat(s['end_utc']) - datetime.fromisoformat(s['start_utc'])
            seconds = duration.days * 86400 + duration.seconds
            age += (Fraction.from_float(float(s['air_temperature']['value'])) - base) * seconds / 86400
        cases.append({'case_id': c['case_id'] + ':end', 'inputs': point_inputs(c['case_id'] + ':end', age, curve),
                      'expected_length_m': c['expected_end_length_m'], 'reference': 'retained independent Decimal800 endpoint'})
    extra = [('synthetic-one-third', Fraction(1, 3), .12, .05, 40),
             ('synthetic-large-minus-third', Fraction(2**56) - Fraction(1, 3), .12, 3, 2**56),
             ('synthetic-large-plus-third', Fraction(2**56) + Fraction(1, 3), .12, 3, 2**56),
             ('synthetic-underflow-rescue', Fraction(0), 1e308, 1, 800),
             ('synthetic-upper-tail', Fraction(1000), .12, 1, 200)]
    with localcontext() as ctx:
        ctx.prec = 800
        for name, age, m, k, tm in extra:
            curve = {'profile_id': name, 'origin': 'synthetic', 'values': {
                'maximum_length': {'value': m, 'unit': 'm'}, 'steepness': {'value': k, 'unit': '1/degC_day'},
                'inflection_age': {'value': tm, 'unit': 'degC_day'}}}
            a = Decimal(age.numerator) / Decimal(age.denominator)
            maximum, steepness, inflection = (Decimal.from_float(float(x)) for x in (m, k, tm))
            expected = maximum / (1 + (-steepness * (a - inflection)).exp())
            cases.append({'case_id': name, 'inputs': point_inputs(name, age, curve),
                          'expected_length_m': str(expected), 'reference': 'independent Decimal800 direct logistic'})
    return {'version': 'internode-length-point-reference-v1', 'origin': 'synthetic_arithmetic_not_cultivar_parameters',
            'precision': 800, 'retained_independent_points': 16, 'new_independent_points': 5, 'cases': cases}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); args.output.write_text(json.dumps(reference(), sort_keys=True, indent=2) + '\n')
