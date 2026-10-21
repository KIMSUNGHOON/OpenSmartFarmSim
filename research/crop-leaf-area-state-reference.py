"""Independent Decimal canonical sigmoid points under an explicit synthetic policy."""
import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path


def reference():
    probes=[('ordinary','.04','.5','4',[0,2,4,6,8]),
            ('fractional','.0625','.125','7.25',[0,Fraction(29,4),Fraction(29,2)]),
            ('rational','.03','.2','2',[Fraction(1,3),Fraction(2,3),Fraction(7,3)]),
            ('negative-tail','1e308','1','1000',[0]),
            ('positive-tail','1e308','1','1000',[2000]),
            ('large-product','1e308','4','1',[1]),
            ('zero-midpoint','.08','.2','0',[0]),
            ('balanced-scales','1e-300','1e300','0',[0])]
    cases=[]
    with localcontext() as context:
        context.prec=100
        for name,maximum,steepness,inflection,ages in probes:
            m,k,tm=(Decimal.from_float(float(v)) for v in (maximum,steepness,inflection))
            for age in ages:
                a=Fraction(age);value=Decimal(a.numerator)/Decimal(a.denominator)
                expected=m/(1+(-k*(value-tm)).exp());identifier='synthetic-'+name+'-'+str(a).replace('/','_')
                cases.append({'case_id':identifier,'inputs':{'input_id':identifier,'origin':'synthetic',
                    'thermal_age_basis':'since_leaf_emergence','normalization':'zero_lower_asymptote_sigmoid_v1',
                    'age_exact':{'numerator':str(a.numerator),'denominator':str(a.denominator),'unit':'degC_day'},
                    'curve':{'profile_id':'synthetic-'+name,'origin':'synthetic','values':{
                        'maximum_area':{'value':float(maximum),'unit':'m2'},
                        'steepness':{'value':float(steepness),'unit':'1/degC_day'},
                        'inflection_age':{'value':float(inflection),'unit':'degC_day'}}}},'expected_area_m2':str(expected)})
    return {'version':'leaf-area-state-decimal-reference-v1','precision':100,
            'origin':'synthetic_arithmetic_probes_not_crop_parameters','cases':cases}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    args.output.write_text(json.dumps(reference(),sort_keys=True,indent=2)+'\n')
