"""Independent Fraction air integration and Decimal leaf-area equation."""
import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path


def record(value,unit):
    v=Fraction(value)
    return {'numerator':str(v.numerator),'denominator':str(v.denominator),'unit':unit}


def reference():
    probes=[('day',0,0,0,10,[(86400,22)]),
            ('fractional-birth',Fraction(1,3),Fraction(1,3),0,10,[(86400,22)]),
            ('warm-cool',0,0,0,5,[(21600,25),(64800,13),(86400,5)]),
            ('explicit-prior-age',0,3600,3,10,[(90000,18)]),
            ('flat',0,0,0,10,[(3600,10),(86400,10)]),
            ('rational-split',Fraction(13,3),Fraction(13,3),0,5,[(1000,22),(3000,13),(86400,15)]),
            ('binary-Celsius',0,0,0,5.3,[(43200,25.2),(86400,12.4)]),
            ('rational-prior-age',0,86400,Fraction(1,7),10,[(172800,16)])]
    cases=[]
    with localcontext() as c:
        c.prec=100
        for name,birth,at,age,base,steps in probes:
            identifier='synthetic-'+name;age=Fraction(age);start=Fraction(at);initial=age;segments=[]
            curve={'profile_id':'synthetic-leaf-clock-curve','origin':'synthetic','values':{
                'maximum_area':{'value':.04,'unit':'m2'},'steepness':{'value':.25,'unit':'1/degC_day'},
                'inflection_age':{'value':8,'unit':'degC_day'}}}
            m,k,tm=(Decimal.from_float(float(curve['values'][v]['value'])) for v in ('maximum_area','steepness','inflection_age'))
            def area(a):
                x=Decimal(a.numerator)/Decimal(a.denominator)
                return m/(1+(-k*(x-tm)).exp())
            before=area(age)
            for end,temp in steps:
                end=Fraction(end);segments.append({'start_elapsed_seconds_exact':record(start,'s'),
                    'end_elapsed_seconds_exact':record(end,'s'),'air_temperature':{'value':temp,'unit':'degC'}})
                age+=(Fraction.from_float(float(temp))-Fraction.from_float(float(base)))*(end-start)/86400;start=end
            clock={'origin':'synthetic','age_basis':'since_leaf_emergence','temperature_basis':'indoor_air_piecewise_constant',
                'leaf_id':'leaf-'+name,'time_origin_utc':'2026-10-01T00:00:00Z','emerged_elapsed_seconds_exact':record(birth,'s'),
                'at_elapsed_seconds_exact':record(at,'s'),'base_temperature':{'value':base,'unit':'degC'},'age_exact':record(initial,'degC_day')}
            cases.append({'case_id':identifier,'initialization':{'input_id':identifier,'clock_state':clock,'curve':curve,
                'normalization':'zero_lower_asymptote_sigmoid_v1','initial_area':{'value':float(before),'unit':'m2'}},
                'segments':segments,'expected_age_exact':record(age,'degC_day'),'expected_at_seconds_exact':record(start,'s'),
                'expected_initial_area_m2':str(before),'expected_area_m2':str(area(age)),'expected_change_m2':str(area(age)-before)})
    return {'version':'rational-leaf-area-reference-v1','precision':100,
            'origin':'synthetic_arithmetic_probes_not_crop_parameters','cases':cases}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    args.output.write_text(json.dumps(reference(),sort_keys=True,indent=2)+'\n')
