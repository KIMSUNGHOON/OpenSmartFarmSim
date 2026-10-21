"""Independent declared leaf areas and totals; no product imports."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path


def reference():
    root=Path(__file__).resolve().parents[1]
    clocks=json.loads((root/'fixtures/crop-rational-leaf-area-reference-v1.json').read_bytes())['cases'];cases=[]
    with localcontext() as c:
        c.prec=100
        for index in (0,2,5,7):
            source=clocks[index];init=source['initialization'];leaves=[];initials=[];finals=[];ages=[]
            for number,maximum in enumerate((.01,.02,.03)):
                p=deepcopy(init);p['input_id']='synthetic-leaf-'+str(number);p['clock_state']['leaf_id']='leaf-'+str(number)
                p['curve']['profile_id']='synthetic-curve-'+str(number);p['curve']['values']['maximum_area']['value']=maximum
                age=Fraction(int(p['clock_state']['age_exact']['numerator']),int(p['clock_state']['age_exact']['denominator']))
                m,k,tm=(Decimal.from_float(float(p['curve']['values'][key]['value'])) for key in ('maximum_area','steepness','inflection_age'))
                def area(a):return m/(1+(-k*(Decimal(a.numerator)/Decimal(a.denominator)-tm)).exp())
                before=area(age);p['initial_area']={'value':float(before),'unit':'m2'}
                for segment in source['segments']:
                    def seconds(value):return Fraction(int(value['numerator']),int(value['denominator']))
                    duration=seconds(segment['end_elapsed_seconds_exact'])-seconds(segment['start_elapsed_seconds_exact'])
                    age+=(Fraction.from_float(float(segment['air_temperature']['value']))-Fraction.from_float(float(p['clock_state']['base_temperature']['value'])))*duration/86400
                after=area(age);leaves.append({'attachment_internode_id':'internode-'+str(number),'initialization':p})
                initials.append(before);finals.append(after);ages.append({'numerator':str(age.numerator),'denominator':str(age.denominator),'unit':'degC_day'})
            cases.append({'case_id':source['case_id'],'initialization':{'input_id':source['case_id'],
                'time_origin_utc':init['clock_state']['time_origin_utc'],'at_elapsed_seconds_exact':init['clock_state']['at_elapsed_seconds_exact'],'leaves':leaves},
                'segments':deepcopy(source['segments']),'expected_initial_areas_m2':list(map(str,initials)),
                'expected_final_areas_m2':list(map(str,finals)),'expected_ages_exact':ages,
                'expected_initial_sum_m2':str(sum(initials)),'expected_final_sum_m2':str(sum(finals)),
                'expected_total_change_m2':str(sum(finals)-sum(initials))})
    return {'version':'declared-leaf-inventory-reference-v1','precision':100,
            'origin':'synthetic_arithmetic_probes_not_crop_parameters','cases':cases}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    args.output.write_text(json.dumps(reference(),sort_keys=True,indent=2)+'\n')
