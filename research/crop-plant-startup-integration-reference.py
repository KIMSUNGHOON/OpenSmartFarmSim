"""Independent 70-digit startup RK4, refined transition and number references."""
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
    'research/crop-plant-cohort-integration-reference.py':'9b880b9d06812f3cfa05bf1c5e47ef93811b548d2320136ce5ae813730d50a72',
    'research/crop-fruit-startup-source-register.json':'882022c483ef935bfca5002059490244d0466e370b8f2d33b5551d8408f2ee1d',
}
PLANT = ('buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum')
FLUX = ('photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem_root','maintenance_fruit',
        'removal_leaf','removal_stem_root','terminal_carbohydrate','terminal_number','entry_number',
        'event_carbohydrate','event_number','requested_fruit_carbohydrate',
        'realized_fruit_carbohydrate','deferred_fruit_carbohydrate','fruit_growth_respiration')


def program(pattern):
    original = runpy.run_path(str(ROOT/'research/crop-plant-cohort-integration-reference.py'))['program']
    candidate = original(pattern=='night-smooth')
    if pattern in ('positive-tail','night-smooth'):
        candidate['solver']['max_step_seconds'] = 30 if pattern=='night-smooth' else 10
        return candidate
    identifier = 'synthetic-startup-'+pattern
    stamp = lambda t:(datetime(2026,1,1)+timedelta(seconds=t)).isoformat()+'Z'
    candidate['initial_state']['input_id'] = identifier+'-initial'
    values = candidate['initial_state']['values']
    if pattern!='full-removal-reentry':
        for name in ('fruit_number','fruit_carbohydrate'):
            for j,q in enumerate(values[name]):
                q['value'] = (.25 if name=='fruit_number' else 10) if pattern=='first-only' and j==0 else 0
    for index,segment in enumerate(candidate['segments']):
        segment['start'],segment['end'] = stamp(index*60),stamp((index+1)*60)
        for block in ('forcing','removals','fruit_entry','relative_growth_rate'):
            segment[block]['input_id'] = identifier+f'-{block}-{index}'
        if pattern=='empty-no-entry':
            for q in segment['fruit_entry']['values'].values():q['value'] = 0
    candidate['output_times'] = [stamp(t) for t in (0,60,120)]
    candidate['solver']['max_step_seconds'] = 1
    if pattern=='full-removal-reentry':
        for event,t in zip(candidate['events'],(0,60,120),strict=True):
            event['at'] = stamp(t);event['removals']['input_id'] = identifier+f'-event-{t}'
            if t==60:
                for q in event['removals']['values']['fruit_fraction']:q['value'] = 1
    else:candidate['events'] = []
    return candidate


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
            z=original_rhs([*vector[:3],Decimal(0),vector[3],vector[4]],forcing,{**removal,'fruit':Decimal(0)},p)
            F=z[3];transfer,growth,factors=potentials(vector[3],RGR)
            weights=[n*g for n,g in zip(N,growth,strict=True)]
            actual=F if sum(weights[1:]) else S*W1
            deferred=F-actual
            assert S*W1<=F
            A=[S*W1]+[(actual-S*W1)*w/sum(weights[1:]) if actual>S*W1 else Decimal(0) for w in weights[1:]]
            maintenance=[c*m for c,m in zip(C,factors,strict=True)]
            dN=[transfer*((N[j-1] if j else 0)-N[j])+(S if j==0 else 0) for j in range(50)]
            dC=[transfer*((C[j-1] if j else 0)-C[j])+A[j]-maintenance[j] for j in range(50)]
            fruit_respiration=p['cFruitG']*actual
            growth_respiration=p['cLeafG']*(z[1]+z[8]+removal['leaf'])+p['cStemG']*(z[2]+z[9]+removal['stem_root'])+fruit_respiration
            return [z[0]+(1+p['cFruitG'])*deferred,z[1],z[2],z[4],z[5],*dN,*dC,z[6],growth_respiration,z[8],z[9],sum(maintenance),
                    removal['leaf'],removal['stem_root'],transfer*C[-1],transfer*N[-1],S,Decimal(0),Decimal(0),
                    F,actual,deferred,fruit_respiration]

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
                assert abs(carbon)<Decimal('1e-55') and abs(number)<Decimal('1e-55')
                assert abs(y[117]-y[118]-y[119])<Decimal('1e-55')
                assert abs(y[120]-p['cFruitG']*y[118])<Decimal('1e-55')
                frames.append({'at':outputs[t],'state':{**{k:str(v) for k,v in zip(PLANT,y[:5],strict=True)},
                    'fruit_number':list(map(str,y[5:55])),'fruit_carbohydrate':list(map(str,y[55:105]))},
                    'cumulative':{k:str(v) for k,v in zip(FLUX,y[105:],strict=True)},
                    'lai':str(p['sla']*y[1]),'fruit_carbohydrate_total':str(sum(y[55:105])),
                    'carbon_residual':str(carbon),'number_residual':str(number)})
        return frames

    cases=[]
    with localcontext() as ctx:
        ctx.prec=70
        for pattern in ('empty-no-entry','empty-entry','first-only','full-removal-reentry','positive-tail','night-smooth'):
            candidate=program(pattern)
            matched=solve(candidate,Decimal(candidate['solver']['max_step_seconds']))
            fine_step=Decimal('1') if pattern=='night-smooth' else Decimal('.5') if pattern=='positive-tail' else Decimal('.25')
            fine=solve(candidate,fine_step);coarse=solve(candidate,fine_step*2)
            differences={}
            for group in ('state','cumulative'):
                for key in fine[0][group]:
                    errors=[]
                    for a,b in zip(fine,coarse,strict=True):
                        x,z=a[group][key],b[group][key]
                        errors.extend(abs(Decimal(v)-Decimal(w)) for v,w in zip(x,z,strict=True)) if isinstance(x,list) else errors.append(abs(Decimal(x)-Decimal(z)))
                    differences[group+'.'+key]=str(max(errors))
            case={'case_id':pattern,'program':candidate,'expected':matched,'refined_expected':fine,
                  'reference_step_seconds':str(fine_step),'refinement_max_abs':differences,
                  'transition_rule':'measured_only; no fourth-order claim at zero/positive tail transitions'}
            if pattern in ('empty-entry','first-only','night-smooth'):
                transfer=cp['nDev']*(cp['cDev1']+cp['cDev2']*20)
                analytic=[]
                for frame in fine:
                    t=Decimal(str((datetime.fromisoformat(frame['at'].replace('Z','+00:00'))-
                                   datetime(2026,1,1,tzinfo=timezone.utc)).total_seconds()))
                    x=transfer*t;poisson=Decimal(1);prefix=Decimal(0);values=[]
                    for j in range(1,51):
                        if j>1:poisson*=x/(j-1)
                        if pattern=='night-smooth':
                            prefix+=poisson;mass=Decimal('.2')*(-x).exp()*prefix
                        else:
                            tail_term=poisson*x/j;tail=tail_term
                            for n in range(j+1,j+201):
                                tail_term*=x/n;tail+=tail_term
                                if tail_term==0 or abs(tail_term)<=abs(tail)*Decimal('1e-65'):break
                            else:raise ValueError('analytic tail did not converge')
                            initial=Decimal('.25')*poisson if pattern=='first-only' else Decimal(0)
                            mass=(-x).exp()*(initial+Decimal('.001')/transfer*tail)
                        values.append(str(mass))
                    analytic.append({'at':frame['at'],'fruit_number':values})
                case['analytic_number']=analytic
            cases.append(case)
    return {'fixture_version':'crop-plant-startup-integration-reference-v1',
        'scope':'synthetic research integration; no actual cultivar/harvest/gate acceptance',
        'method':'70-digit Decimal source equations, matched/refined RK4, explicit empty-sink deferral, independent constant-temperature number solutions',
        'input_sha256':dict(INPUTS),'generator_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'cases':cases}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'fixtures/crop-plant-startup-integration-reference-v1.json')
    args=parser.parse_args()
    if args.output.is_symlink() or args.output.resolve() in {Path(__file__).resolve(),*[(ROOT/k).resolve() for k in INPUTS]}:
        raise ValueError('reference_output_would_replace_input')
    result=references();args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cases':len(result['cases']),'samples':sum(len(c['expected']) for c in result['cases']),'product_imports':False}))


if __name__=='__main__':main()
