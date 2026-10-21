"""Independent Decimal800 lengths/sums from manually known shoot ages."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
import json
from pathlib import Path


def reference():
    root = Path(__file__).resolve().parents[1]
    new = json.loads((root / 'fixtures/crop-new-internodes-reference-v1.json').read_bytes())['cases']
    base = json.loads((root / 'fixtures/crop-internode-length-state-reference-v1.json').read_bytes())['cases'][0]['inputs']
    cases = []
    with localcontext() as context:
        context.prec = 800
        m, k, tm = [Decimal.from_float(float(base['curve']['values'][name]['value']))
                    for name in ('maximum_length', 'steepness', 'inflection_age')]
        for index, count, first in [(0,3,0),(1,3,0),(4,3,0),(3,3,0),(0,0,3)]:
            source = new[index]
            timeline = source['inputs']['timeline_state']
            a = timeline['age_exact']
            start_age = Decimal(a['numerator']) / Decimal(a['denominator'])
            end = source['timeline_checkpoint']['age_exact']
            end_age = Decimal(end['numerator']) / Decimal(end['denominator'])
            initial_inputs = []
            expected = []
            for sequence in range(first, first+count):
                p = deepcopy(base)
                p['input_id'] = 'synthetic-initial-' + str(sequence)
                p['clock_state'].update(internode_id=p['input_id'], emerged_at=timeline['started_at'],
                    at=timeline['at'], base_temperature=timeline['base_temperature'], age_exact=a)
                p['initial_length']['value'] = float(m / (1 + (-k * (start_age-tm)).exp()))
                initial_inputs.append({'sequence':sequence, 'birth_age_exact': {
                    'numerator':'0','denominator':'1','unit':'degC_day'}, 'length_inputs':p})
                expected.append({'sequence':sequence,'end_age_exact':end,
                                 'end_length_m':str(m / (1 + (-k * (end_age-tm)).exp()))})
            expected.extend(source['new_internodes'])
            total = sum(Decimal(e['end_length_m']) for e in expected)
            cases.append({'case_id':source['case_id'] + '-existing-' + str(count),
                'input_id':'synthetic-inventory-' + str(len(cases)), 'timeline_state':timeline,
                'inventory_start_sequence':first, 'initial_internodes':initial_inputs,
                'emergence_profile':{'curve':source['inputs']['curve'],'initial_length':source['inputs']['initial_length']},
                'segments':source['inputs']['segments'], 'expected':expected,
                'expected_axis_length_m':str(total), 'timeline_checkpoint':source['timeline_checkpoint']})
    return {'version':'shoot-internode-inventory-reference-v1','origin':'synthetic_math_only',
            'method':'independent Decimal800 direct logistic and sum from hand-derived ages','cases':cases}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.write_text(json.dumps(reference(),indent=2,sort_keys=True)+'\n')
