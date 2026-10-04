"""Independent 60-digit plant/cohort RK4 and Erlang number reference."""
import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    'fixtures/crop-growth-reference-parameters-v1.json':'d606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca',
    'fixtures/crop-fruit-cohort-reference-parameters-v1.json':'b453b4ffe618f26041e4ec6a1b1b7d2e5f38edb3d42adaaad4fa3cd4fbb99cbb',
    'research/crop-integration-reference.py':'a38b7a67e43cf9f590838bf915ab3e5048950b8be6ed35f70817e18b42a09ce7',
}
PLANT = ('buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum')
FLUX = ('photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem_root','maintenance_fruit',
        'removal_leaf','removal_stem_root','terminal_carbohydrate','terminal_number','entry_number',
        'event_carbohydrate','event_number')


def block(identifier, values):
    return {'input_id':identifier,'origin':'synthetic','values':values}


def q(value, unit):
    return {'value':value,'unit':unit}


def program(night=False):
    stamp=lambda t:(datetime(2026,1,1)+timedelta(seconds=t)).isoformat()+'Z'
    identifier='synthetic-night-convergence' if night else 'synthetic-day-night-management'
    values={k:q(v,u) for k,v,u in (
        ('buffer',1000 if night else 10000,'mg_CH2O/m2_floor'),('leaf',100000,'mg_CH2O/m2_floor'),
        ('stem_root',40000,'mg_CH2O/m2_floor'),('temperature_filtered_24h',20,'degC'),('temperature_sum',500,'degC_day'))}
    values.update({'fruit_number':[q(.2,'fruits_equivalent/m2_floor') for _ in range(50)],
                   'fruit_carbohydrate':[q(40,'mg_CH2O/m2_floor') for _ in range(50)]})
    segments=[]
    for index,(start,end,light) in enumerate(((0,3600,0),) if night else ((0,150,400),(150,300,0))):
        segments.append({'start':stamp(start),'end':stamp(end),
            'forcing':block(identifier+f'-forcing-{index}',{'canopy_temperature':q(20,'degC'),
                'par_above_canopy':q(light,'umol_photons/m2_floor/s'),'co2':q(800,'ppm')}),
            'removals':block(identifier+f'-continuous-{index}',{'leaf':q(0 if night else .01,'mg_CH2O/m2_floor/s'),
                'stem_root':q(0,'mg_CH2O/m2_floor/s')}),
            'fruit_entry':block(identifier+f'-entry-{index}',{'fruit_number_inflow':q(0 if night else .001,'fruits_equivalent/m2_floor/s'),
                'fruit_entry_carbohydrate':q(0 if night else 1,'mg_CH2O/fruit_equivalent')}),
            'relative_growth_rate':block(identifier+f'-RGR-{index}',{'fruit_relative_growth_rate':[
                q(((j+index)%5)*1e-6,'1/s') for j in range(50)]})})
    events=[]
    if not night:
        for t,leaf,stem,selected in ((0,10,0,{0:.1}),(150,100,0,{10:.25,49:.5}),(300,0,10,{1:.1})):
            events.append({'at':stamp(t),'removals':block(identifier+f'-event-{t}',{
                'leaf':q(leaf,'mg_CH2O/m2_floor'),'stem_root':q(stem,'mg_CH2O/m2_floor'),
                'fruit_fraction':[q(selected.get(j,0),'1') for j in range(50)]})})
    return {'initial_state':block(identifier+'-initial',values),'segments':segments,'events':events,
        'output_times':[stamp(t) for t in ((0,60,120,180,240,300) if not night else (0,900,1800,2700,3600))],
        'solver':{'method':'rk4-fixed-v1','max_step_seconds':10,'max_steps':10000,'roundoff_rule':'64-ulp-per-operation-v1'}}


def references():
    for path,wanted in INPUTS.items():assert sha256((ROOT/path).read_bytes()).hexdigest()==wanted
    original_rhs=runpy.run_path(str(ROOT/'research/crop-integration-reference.py'))['decimal_rhs']
    p={k:Decimal(str(v['value'])) for k,v in json.loads((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes())['parameters'].items()}
    cp={k:Decimal(v['source_value']) for k,v in json.loads((ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes())['parameters'].items()}

    @lru_cache(maxsize=256)
    def potentials(temperature,rgr):
        rate=cp['cDev1']+cp['cDev2']*temperature;period=1/(rate*cp['seconds_per_day'])
        peak=cp['Gompertz_M_intercept']+cp['Gompertz_M_slope']*period
        steepness=1/(cp['Gompertz_B_intercept']+cp['Gompertz_B_M_slope']*peak)
        growth=[]
        for j in range(1,51):
            age=(Decimal(j)-cp['stage_age_midpoint'])/cp['nDev']*period
            x=-steepness*(age-peak)
            growth.append(cp['GMax']*steepness*x.exp()*(-x.exp()).exp())
        tf=(cp['Q10'].ln()*(temperature-cp['maintenance_temperature_reference_c'])/cp['q10_temperature_interval_c']).exp()
        factors=[cp['fruit_maintenance']*(1-(-cp['cRgr']*r).exp())*tf for r in rgr]
        return cp['nDev']*rate,growth,factors

    def solve(candidate,step):
        start=datetime.fromisoformat(candidate['segments'][0]['start'].replace('Z','+00:00'))
        seconds=lambda t:Decimal(str((datetime.fromisoformat(t.replace('Z','+00:00'))-start).total_seconds()))
        values=candidate['initial_state']['values']
        y=[Decimal(str(values[k]['value'])) for k in PLANT]
        y += [Decimal(str(q['value'])) for k in ('fruit_number','fruit_carbohydrate') for q in values[k]]
        y += [Decimal(0)]*len(FLUX);seed=list(y)
        events={seconds(e['at']):e for e in candidate['events']};outputs={seconds(t):t for t in candidate['output_times']}
        boundaries=sorted(set(outputs)|set(events)|{seconds(s['end']) for s in candidate['segments']})
        index=0;t=Decimal(0);frames=[]

        def rhs(vector):
            segment=candidate['segments'][index]
            forcing={k:Decimal(str(q['value'])) for k,q in segment['forcing']['values'].items()}
            removal={k:Decimal(str(q['value'])) for k,q in segment['removals']['values'].items()}
            RGR=tuple(Decimal(str(q['value'])) for q in segment['relative_growth_rate']['values']['fruit_relative_growth_rate'])
            S=Decimal(str(segment['fruit_entry']['values']['fruit_number_inflow']['value']))
            W1=Decimal(str(segment['fruit_entry']['values']['fruit_entry_carbohydrate']['value']))
            N,C=vector[5:55],vector[55:105]
            z=original_rhs([*vector[:3],sum(C),vector[3],vector[4]],forcing,{**removal,'fruit':Decimal(0)},p)
            F=z[3]+z[10];transfer,growth,factors=potentials(vector[3],RGR)
            weights=[n*g for n,g in zip(N,growth,strict=True)]
            A=[S*W1]+[(F-S*W1)*w/sum(weights[1:]) for w in weights[1:]]
            maintenance=[c*m for c,m in zip(C,factors,strict=True)]
            dN=[transfer*((N[j-1] if j else 0)-N[j])+(S if j==0 else 0) for j in range(50)]
            dC=[transfer*((C[j-1] if j else 0)-C[j])+A[j]-maintenance[j] for j in range(50)]
            return [z[0],z[1],z[2],z[4],z[5],*dN,*dC,z[6],z[7],z[8],z[9],sum(maintenance),
                    removal['leaf'],removal['stem_root'],transfer*C[-1],transfer*N[-1],S,Decimal(0),Decimal(0)]

        for target in boundaries:
            while t<target:
                h=min(step,target-t)
                k1=rhs(y);k2=rhs([v+h*d/2 for v,d in zip(y,k1,strict=True)])
                k3=rhs([v+h*d/2 for v,d in zip(y,k2,strict=True)]);k4=rhs([v+h*d for v,d in zip(y,k3,strict=True)])
                y=[v+h*(a+2*b+2*c+d)/6 for v,a,b,c,d in zip(y,k1,k2,k3,k4,strict=True)];t+=h
                assert all(v>=0 for v in y)
            if index+1<len(candidate['segments']) and t==seconds(candidate['segments'][index]['end']):index+=1
            if t in events:
                removal=events[t]['removals']['values'];mass=Decimal(0);number=Decimal(0)
                for j,k in enumerate(('leaf','stem_root'),start=1):
                    value=Decimal(str(removal[k]['value']));y[j]-=value;mass+=value
                for j,f in enumerate(removal['fruit_fraction']):
                    fraction=Decimal(str(f['value']));n=y[5+j]*fraction;c=y[55+j]*fraction
                    y[5+j]-=n;y[55+j]-=c;number+=n;mass+=c
                y[115]+=mass;y[116]+=number
            if t in outputs:
                carbon=sum(y[:3])+sum(y[55:105])-sum(seed[:3])-sum(seed[55:105])-y[105]+sum(y[106:113])+y[115]
                number=sum(y[5:55])-sum(seed[5:55])-y[114]+y[113]+y[116]
                assert abs(carbon)<Decimal('1e-45') and abs(number)<Decimal('1e-45')
                frames.append({'at':outputs[t],'state':{**{k:str(v) for k,v in zip(PLANT,y[:5],strict=True)},
                    'fruit_number':list(map(str,y[5:55])),'fruit_carbohydrate':list(map(str,y[55:105]))},
                    'cumulative':{k:str(v) for k,v in zip(FLUX,y[105:],strict=True)},
                    'lai':str(p['sla']*y[1]),'fruit_carbohydrate_total':str(sum(y[55:105])),
                    'carbon_residual':str(carbon),'number_residual':str(number)})
        return frames

    cases=[]
    with localcontext() as ctx:
        ctx.prec=60
        for night,fine_step in ((False,Decimal('.5')),(True,Decimal('1'))):
            candidate=program(night);fine=solve(candidate,fine_step);coarse=solve(candidate,fine_step*2)
            differences={}
            for group in ('state','cumulative'):
                for key in fine[0][group]:
                    errors=[]
                    for a,b in zip(fine,coarse,strict=True):
                        x,z=a[group][key],b[group][key]
                        errors.extend(abs(Decimal(v)-Decimal(w)) for v,w in zip(x,z,strict=True)) if isinstance(x,list) else errors.append(abs(Decimal(x)-Decimal(z)))
                    differences[group+'.'+key]=str(max(errors))
            case={'case_id':candidate['initial_state']['input_id'],'program':candidate,'expected':fine,
                  'reference_step_seconds':str(fine_step),'refinement_max_abs':differences}
            if night:
                transfer=cp['nDev']*(cp['cDev1']+cp['cDev2']*20)
                analytic=[]
                for frame in fine:
                    t=Decimal(str((datetime.fromisoformat(frame['at'].replace('Z','+00:00'))-
                                   datetime(2026,1,1,tzinfo=timezone.utc)).total_seconds()))
                    x=transfer*t;poisson=Decimal(1);prefix=Decimal(0);values=[]
                    for j in range(50):
                        if j:poisson*=x/j
                        prefix+=poisson;values.append(str(Decimal('.2')*(-x).exp()*prefix))
                    analytic.append({'at':frame['at'],'fruit_number':values})
                case['analytic_number']=analytic
            cases.append(case)
    return {'fixture_version':'crop-plant-cohort-integration-reference-v1',
        'scope':'synthetic research integration; no actual cultivar/harvest/gate acceptance',
        'method':'60-digit Decimal source equations, independent refined RK4 and constant-temperature S=0 Erlang number solution',
        'input_sha256':dict(INPUTS),'generator_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'cases':cases}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'fixtures/crop-plant-cohort-integration-reference-v1.json')
    args=parser.parse_args()
    if args.output.is_symlink() or args.output.resolve() in {Path(__file__).resolve(),*[(ROOT/k).resolve() for k in INPUTS]}:
        raise ValueError('reference_output_would_replace_input')
    result=references();args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cases':len(result['cases']),'samples':sum(len(c['expected']) for c in result['cases']),'product_imports':False}))


if __name__=='__main__':main()
