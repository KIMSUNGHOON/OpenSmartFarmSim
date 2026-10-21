"""Independent Fraction/Decimal probe; no product imports or farm coefficients."""
from decimal import Decimal,localcontext
from fractions import Fraction
import json
import sys


def record(value,unit='s'):
    value=Fraction(value)
    return {'numerator':str(value.numerator),'denominator':str(value.denominator),'unit':unit}


def area(age,maximum,k,midpoint):
    with localcontext() as c:
        c.prec=100
        a=Decimal(age.numerator)/Decimal(age.denominator)
        return Decimal.from_float(maximum)/(1+(-Decimal.from_float(k)*(a-Decimal.from_float(midpoint))).exp())


def build():
    cases=[]
    programs=[('fractional',[(0,86400,22.)],[Fraction(1,3),Fraction(43200),Fraction(86400)]),
              ('temperature-boundary',[(0,3600,12.),(3600,7200,32.),(7200,86400,18.)],[Fraction(1200),Fraction(3600),Fraction(7200)]),
              ('simultaneous',[(0,100,22.)],[Fraction(37,5),Fraction(37,5),Fraction(37,5)]),
              ('flat',[(0,86400,10.)],[Fraction(1),Fraction(86400)]),
              ('no-events',[(0,100,22.)],[])]
    for name,forcing,births in programs:
        events=[];expected=[]
        for i,birth in enumerate(births):
            maximum=.01*(i+1);k=.25;mid=8.;base=10.
            curve={'origin':'synthetic','profile_id':'synthetic-declared-birth-'+str(i),'values':{
                'maximum_area':{'value':maximum,'unit':'m2'},'steepness':{'value':k,'unit':'1/degC_day'},
                'inflection_age':{'value':mid,'unit':'degC_day'}}}
            initial=area(Fraction(0),maximum,k,mid)
            events.append({'leaf_id':'declared-birth-'+str(i),'attachment_internode_id':'declared-stem-'+str(i),
                'emerged_elapsed_seconds_exact':record(birth),'base_temperature':{'value':base,'unit':'degC'},
                'curve':curve,'normalization':'zero_lower_asymptote_sigmoid_v1','initial_area':{'value':float(initial),'unit':'m2'}})
            age=sum((Fraction.from_float(t)-Fraction.from_float(base))*(Fraction(end)-max(Fraction(start),birth))/86400
                    for start,end,t in forcing if end>birth)
            final=area(age,maximum,k,mid)
            expected.append({'age_exact':record(age,'degC_day'),'initial_area_m2':str(initial),'final_area_m2':str(final)})
        cases.append({'case_id':name,'inputs':{'input_id':name,'origin':'synthetic','time_origin_utc':'2026-10-01T00:00:00Z',
            'segments':[{'start_elapsed_seconds_exact':record(start),'end_elapsed_seconds_exact':record(end),
                         'air_temperature':{'value':t,'unit':'degC'}} for start,end,t in forcing],
            'births':events},'expected':expected})
    return {'schema_version':'declared-leaf-births-reference-v1','origin':'synthetic','method':'independent Fraction clock / Decimal100 logistic; no product imports',
            'cases':cases}


if __name__=='__main__':
    sys.stdout.write(json.dumps(build(),ensure_ascii=False,sort_keys=True,indent=2)+'\n')
