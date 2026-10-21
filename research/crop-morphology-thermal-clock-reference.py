"""Independent 100-digit synthetic arithmetic references, no product imports."""
import argparse
from datetime import datetime
from decimal import Decimal, localcontext
import json
from pathlib import Path


def reference():
    rows = [
        ('day', '2026-10-01T00:00:00Z', '2026-10-01T00:00:00Z', '0', '1', 5,
         [('2026-10-02T00:00:00Z', 20)]),
        ('half-day', '2026-10-01T00:00:00Z', '2026-10-02T00:00:00Z', '1', '3', 5,
         [('2026-10-02T12:00:00Z', 11)]),
        ('variable', '2026-10-01T00:00:00Z', '2026-10-02T00:00:00Z', '3', '2', 5,
         [('2026-10-02T06:00:00Z', 5), ('2026-10-03T00:00:00Z', 17)]),
        ('negative-celsius', '2026-10-01T00:00:00Z', '2026-10-01T00:00:00Z', '0', '1', -5,
         [('2026-10-02T00:00:00Z', -2)]),
        ('equal-base', '2026-10-01T00:00:00Z', '2026-10-02T00:00:00Z', '1', '3', 5,
         [('2026-10-03T00:00:00Z', 5)]),
        ('binary-increment', '2026-10-01T00:00:00Z', '2026-10-01T00:00:00Z', '0', '1', 1,
         [('2026-10-01T00:00:01Z', 1.0000000000000002)]),
        ('leap-day', '2028-02-28T00:00:00Z', '2028-02-28T00:00:00Z', '0', '1', 8,
         [('2028-03-01T00:00:00Z', 9)]),
        ('UTC-midnight', '2026-10-21T23:59:59Z', '2026-10-21T23:59:59Z', '0', '1', 5,
         [('2026-10-22T00:00:01Z', 6)]),
        ('large-signed-difference', '2026-10-01T00:00:00Z', '2026-10-01T00:00:00Z', '0', '1', -1e308,
         [('2026-10-01T00:00:01Z', 1e308)]),
    ]
    cases = []
    with localcontext() as context:
        context.prec = 100
        for name, emerged, start, numerator, denominator, base, intervals in rows:
            state = {'origin': 'synthetic', 'age_basis': 'since_internode_emergence',
                     'temperature_basis': 'indoor_air_piecewise_constant', 'internode_id': 'synthetic-internode-1',
                     'emerged_at': emerged, 'at': start, 'base_temperature': {'value': base, 'unit': 'degC'},
                     'age_exact': {'numerator': numerator, 'denominator': denominator, 'unit': 'degC_day'}}
            age = Decimal(numerator) / Decimal(denominator)
            segments = []
            previous = start
            for end, temperature in intervals:
                elapsed = datetime.fromisoformat(end) - datetime.fromisoformat(previous)
                seconds = elapsed.days * 86400 + elapsed.seconds
                age += (Decimal.from_float(float(temperature)) - Decimal.from_float(float(base))) * seconds / 86400
                segments.append({'start_utc': previous, 'end_utc': end,
                                 'air_temperature': {'value': temperature, 'unit': 'degC'}})
                previous = end
            cases.append({'case_id': 'synthetic-' + name,
                          'inputs': {'input_id': 'synthetic-' + name, 'state': state, 'segments': segments},
                          'expected_age_degC_day': str(age)})
    return {'version': 'morphology-thermal-clock-reference-v1', 'precision': 100,
            'origin': 'synthetic_arithmetic_not_cultivar_or_weather_data', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(reference(), indent=2, sort_keys=True) + '\n')
