"""Independent Decimal plant/cohort composition; no product imports."""
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
    'fixtures/crop-growth-reference-cases-v1.json': 'f96b119c561981a459bdbd5dd82daaa6965b54f483174552b3867105cc01e0fc',
    'fixtures/crop-fruit-cohort-reference-cases-v1.json': 'bb52e2ccbf7f9737b3c9d5c2c673145101c0c302947c96d521c448c6e368e2e9',
    'research/crop-integration-reference.py': 'a38b7a67e43cf9f590838bf915ab3e5048950b8be6ed35f70817e18b42a09ce7',
}


def references():
    for name, digest in INPUTS.items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    rhs = runpy.run_path(str(ROOT/'research/crop-integration-reference.py'))['decimal_rhs']
    growth = json.loads((ROOT/'fixtures/crop-growth-reference-cases-v1.json').read_bytes())['cases']
    cohort = json.loads((ROOT/'fixtures/crop-fruit-cohort-reference-cases-v1.json').read_bytes())['cases']
    p = {k: Decimal(str(v['value'])) for k,v in json.loads(
        (ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes())['parameters'].items()}
    cases = []
    with localcontext() as ctx:
        ctx.prec = 60
        for temperature, source in ((17,2),(20,3),(23,1)):
            for rgr in ('zero','varying'):
                case = deepcopy(growth[source])
                fruit = deepcopy(next(c for c in cohort if c['case_id'] == f'synthetic-{temperature}C-multiple-{rgr}-RGR'))
                identifier = f'synthetic-plant-{temperature}C-{rgr}-RGR'
                state = case['state']; state['input_id'] = identifier
                state['values'].pop('fruit')
                state['values']['temperature_filtered_24h']['value'] = temperature
                fruit_state = fruit['state']; fruit_state['input_id'] = identifier+'-cohort'
                fruit_state['values']['temperature_sum'] = deepcopy(state['values']['temperature_sum'])
                forcing = case['forcing']; forcing['input_id'] = identifier+'-forcing'
                removals = case['removals']; removals['input_id'] = identifier+'-removal'
                removals['values'].pop('fruit')
                entry = deepcopy(fruit['inflow']); entry['input_id'] = identifier+'-entry'
                entry['values'].pop('fruit_carbohydrate_inflow')
                N,C = ([Decimal(str(q['value'])) for q in fruit_state['values'][name]]
                       for name in ('fruit_number','fruit_carbohydrate'))
                raw = fruit['expected']
                weights,maintenance,dN = ([Decimal(v) for v in raw[key]] for key in ('weighted_demand','maintenance','dN'))
                y = [Decimal(str(state['values'][k]['value'])) for k in ('buffer','leaf','stem_root')]
                y += [sum(C), Decimal(temperature), Decimal(str(state['values']['temperature_sum']['value']))]
                f = {k:Decimal(str(q['value'])) for k,q in forcing['values'].items()}
                removed = {k:Decimal(str(q['value'])) for k,q in removals['values'].items()}
                z = rhs(y, f, {**removed,'fruit':Decimal(0)}, p)
                F = z[3]+z[10]
                S,W1 = (Decimal(str(entry['values'][key]['value'])) for key in (
                    'fruit_number_inflow','fruit_entry_carbohydrate'))
                allocated = [S*W1] + [(F-S*W1)*w/sum(weights[1:]) for w in weights[1:]]
                transfer = Decimal(50)*Decimal(raw['development_rate'])
                dC = [transfer*((C[j-1] if j else 0)-C[j])+allocated[j]-maintenance[j] for j in range(50)]
                terminal_C,terminal_N = transfer*C[-1],transfer*N[-1]
                carbon = sum(z[:3])+sum(dC)+z[7]+z[8]+z[9]+sum(maintenance)+sum(removed.values())+terminal_C-z[6]
                number = sum(dN)+terminal_N-S
                assert abs(carbon) < Decimal('1e-48') and abs(number) < Decimal('1e-48')
                expected = {'photosynthesis':str(z[6]),'growth_respiration':str(z[7]),
                    'fruit_allocation':str(F),'fruit_buffer_debit':str(F*(1+p['cFruitG'])),
                    'fruit_carbohydrate_total':str(sum(C)), 'fruit_maintenance':str(sum(maintenance)),
                    'old_single_fruit_maintenance':str(z[10]),
                    'terminal_carbohydrate':str(terminal_C),'terminal_number':str(terminal_N),
                    'lai':str(p['sla']*y[1]),
                    'plant_derivatives':{k:str(z[j]) for k,j in (
                        ('buffer',0),('leaf',1),('stem_root',2),('temperature_filtered_24h',4),('temperature_sum',5))},
                    'dC':list(map(str,dC)),'dN':list(map(str,dN))}
                cases.append({'case_id':identifier,'state':state,'cohort_state':fruit_state,
                    'forcing':forcing,'removals':removals,'fruit_entry':entry,'expected':expected})
    return {'fixture_version':'crop-plant-cohort-decimal-reference-v1',
        'scope':'synthetic instantaneous software math; no actual cultivar, integration or claim gates',
        'input_sha256':dict(INPUTS),'generator_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
        'method':'60-digit Decimal original plant RHS plus independent pinned cohort demand/transport/maintenance',
        'cases':cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'fixtures/crop-plant-cohort-reference-cases-v1.json')
    args = parser.parse_args()
    if args.output.is_symlink() or args.output.resolve() in {
        Path(__file__).resolve(), *[(ROOT/k).resolve() for k in INPUTS]}:
        raise ValueError('reference_output_would_replace_input')
    result = references()
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cases':len(result['cases']),'product_imports':False}))


if __name__ == '__main__':
    main()
