"""Independent existing/new leaf population references; no product imports."""
from decimal import Decimal,localcontext
from fractions import Fraction
import json
from pathlib import Path
import runpy
import sys


ROOT=Path(__file__).resolve().parents[1]


def exact(record):return Fraction(int(record['numerator']),int(record['denominator']))


def area(age,curve):
    with localcontext() as context:
        context.prec=100;values=curve['values']
        a=Decimal(age.numerator)/Decimal(age.denominator)
        maximum,k,midpoint=(Decimal.from_float(float(values[k]['value'])) for k in ['maximum_area','steepness','inflection_age'])
        return maximum/(1+(-k*(a-midpoint)).exp())


def build():
    cases=[];births=runpy.run_path(str(ROOT/'research/crop-declared-leaf-births-reference.py'))['build']()
    source=json.loads((ROOT/'fixtures/crop-leaf-inventory-reference-v1.json').read_bytes())['cases'][0]['initialization']
    for p in births['cases']:
        initial=json.loads(json.dumps(source));initial['input_id']='population-'+p['case_id'];expected=[]
        for item in initial['leaves']:
            init=item['initialization'];clock=init['clock_state'];base=Fraction.from_float(float(clock['base_temperature']['value']))
            age=exact(clock['age_exact'])+sum((Fraction.from_float(float(s['air_temperature']['value']))-base)*
                (exact(s['end_elapsed_seconds_exact'])-exact(s['start_elapsed_seconds_exact']))/86400 for s in p['inputs']['segments'])
            expected.append({'leaf_id':clock['leaf_id'],'attachment_internode_id':item['attachment_internode_id'],
                'area_m2':str(area(age,init['curve'])),'age_exact':{'numerator':str(age.numerator),'denominator':str(age.denominator),'unit':'degC_day'}})
        for declaration,e in zip(p['inputs']['births'],p['expected']):
            expected.append({'leaf_id':declaration['leaf_id'],'attachment_internode_id':declaration['attachment_internode_id'],
                'area_m2':e['final_area_m2'],'age_exact':e['age_exact']})
        with localcontext() as context:
            context.prec=100;total=sum(Decimal(v['area_m2']) for v in expected)
        cases.append({'case_id':p['case_id'],'initialization':{'input_id':'population-'+p['case_id'],'initial_inventory':initial},
            'segments':p['inputs']['segments'],'births':p['inputs']['births'],'expected':expected,'expected_sum_m2':str(total)})
    return {'schema_version':'leaf-population-reference-v1','origin':'synthetic','method':'independent Fraction clock / Decimal100 logistic; no product imports','cases':cases}


if __name__=='__main__':sys.stdout.write(json.dumps(build(),ensure_ascii=False,sort_keys=True,indent=2)+'\n')
