"""Independent 800-digit direct sigmoid differences; no product imports."""
import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path


def reference():
    probes = [
        ('first', 0, 2, '.04', '.5', '4'),
        ('inflection', 2, 6, '.04', '.5', '4'),
        ('last', 6, 8, '.04', '.5', '4'),
        ('whole', 0, 8, '.04', '.5', '4'),
        ('equal-age', 4, 4, '.04', '.5', '4'),
        ('tiny-increment', 4, Fraction(4000000001, 1000000000), '.04', '.5', '4'),
        ('negative-tail', 0, 1, '1e308', '1', '1000'),
        ('positive-tail', 1999, 2000, '1e308', '1', '1000'),
        ('sub-float-age-increment', 1, Fraction(10**400+1, 10**400), '1e308', '1', '1'),
        ('whole-curve', 0, 2000, '.04', '1', '1000'),
    ]
    cases = []
    with localcontext() as context:
        context.prec = 800
        for name, start, end, maximum, steepness, inflection in probes:
            start, end = Fraction(start), Fraction(end)
            m, k, tm = (Decimal.from_float(float(v)) for v in (maximum, steepness, inflection))
            a0, a1 = (Decimal(v.numerator)/Decimal(v.denominator) for v in (start, end))
            expected = m/(1+(-k*(a1-tm)).exp()) - m/(1+(-k*(a0-tm)).exp())
            identifier = 'synthetic-' + name
            def age(v):
                return {'numerator': str(v.numerator), 'denominator': str(v.denominator), 'unit': 'degC_day'}
            cases.append({'case_id': identifier, 'inputs': {'input_id': identifier,
                'start_age_exact': age(start), 'end_age_exact': age(end),
                'curve': {'profile_id': identifier, 'origin': 'synthetic', 'values': {
                    'maximum_area': {'value': float(maximum), 'unit': 'm2'},
                    'steepness': {'value': float(steepness), 'unit': '1/degC_day'},
                    'inflection_age': {'value': float(inflection), 'unit': 'degC_day'}}}},
                'expected_change_m2': str(expected)})
    return {'version': 'leaf-area-change-decimal-reference-v1', 'precision': 800,
            'origin': 'synthetic_arithmetic_probes_not_crop_parameters', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(reference(), sort_keys=True, indent=2)+'\n')
