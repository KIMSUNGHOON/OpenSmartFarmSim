"""Independent direct logistic on hand-derived birth/end ages."""
import argparse
from decimal import Decimal, localcontext
from math import gcd
import json
from pathlib import Path


def reference():
    root = Path(__file__).resolve().parents[1]
    timeline = json.loads((root / 'fixtures/crop-shoot-timeline-reference-v1.json').read_bytes())['cases']
    profile = json.loads((root / 'fixtures/crop-internode-length-state-reference-v1.json').read_bytes())['cases'][0]['inputs']
    cases = []
    with localcontext() as context:
        context.prec = 800
        m, k, tm = [Decimal.from_float(float(profile['curve']['values'][key]['value']))
                    for key in ('maximum_length', 'steepness', 'inflection_age')]
        initial = m / (1 + (k * tm).exp())
        for case in timeline:
            if any(e['utc_whole_second'] is None for e in case['events']):
                continue
            end = case['checkpoint']['age_exact']
            en, ed = int(end['numerator']), int(end['denominator'])
            expected = []
            for event in case['events']:
                birth = event['thermal_age_exact']
                bn, bd = int(birth['numerator']), int(birth['denominator'])
                n, d = en * bd - bn * ed, ed * bd
                common = gcd(n, d)
                n, d = n // common, d // common
                age = Decimal(n) / Decimal(d)
                length = m / (1 + (-k * (age - tm)).exp())
                expected.append({'sequence': event['sequence'], 'birth_age_exact': birth,
                    'birth_utc': event['utc_whole_second'], 'end_age_exact': {
                        'numerator': str(n), 'denominator': str(d), 'unit': 'degC_day'},
                    'end_length_m': str(length)})
            cases.append({'case_id': case['case_id'], 'inputs': {'input_id': case['inputs']['input_id'],
                'timeline_state': case['inputs']['state'], 'segments': case['inputs']['segments'],
                'curve': profile['curve'], 'initial_length': {'value': float(initial), 'unit': 'm'}},
                'timeline_checkpoint': case['checkpoint'], 'new_internodes': expected})
    return {'version': 'shoot-new-internodes-reference-v1', 'origin': 'synthetic_math_only',
            'method': 'manual timeline ages and independent Decimal800 direct logistic', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(reference(), indent=2, sort_keys=True) + '\n')
