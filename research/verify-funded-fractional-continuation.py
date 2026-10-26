"""Independent numeric integration and conservation oracle over owned source graphs."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from math import inf, nextafter
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app import crop_funded_fractional_continuation as model
from app.content_access import ContentAccess


def frac(v):return Fraction(int(v['numerator']),int(v['denominator']))


def point_driver():
    spec=importlib.util.spec_from_file_location('point_qa',ROOT/'research/verify-funded-fractional-birth-points.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def extra_inputs(context,checkpoint,first):
    v=deepcopy(first);v.pop('candidate_sha256')
    v.update(schema_version='fractional-continuation-birth-input-v1',input_id='additional-fractional-point',
        context_sha256=context.sha256,checkpoint_sha256=checkpoint.sha256,
        at_elapsed_seconds_exact=checkpoint.value['at']['elapsed_seconds_exact'])
    for i,event in enumerate(v['events']):
        event['event_id']=f'extra-event-{i}';event['leaf']['leaf_id']=f'extra-leaf-{i}'
    return v


def reference_ledgers(data,final,transfers,points,bases,first,at,latent):
    F=Fraction.from_float;p=data['program'];a=list(map(F,first['state']));b=list(map(F,final['state']));n=len(p['leaves']);n0=(len(a)-107)//3
    t={k:F(v['value'])for k,v in transfers.items()};q={k:F(v['value'])for k,v in points.items()}
    c=lambda y,count:sum((y[0],y[1],*y[4:54],*y[107+2*count:]),Fraction(0));number=lambda y:sum(y[54:104],Fraction(0))
    ca=F(first['derived']['air_capacity']['value']);du=b[104]-a[104];da=ca*(b[105]-a[105]);dw=b[106]-a[106]
    rows={'carbohydrate':c(b,n)-c(a,n0)-t['photosynthesis']+sum((t[k]for k in ['growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit','removal_leaf','removal_stem','terminal_carbon']),Fraction(0))+q['growth_respiration'],
        'number':number(b)-number(a)-t['entry_number']+t['terminal_number'],
        'canopy_sensible':du-t['canopy_external']+t['sensible']+t['latent']-t['incoming_heat']+t['outgoing_heat']-q['sensible_in'],
        'air_sensible':da-t['air_external']-t['sensible'],'vapor':dw-t['vapor']-t['external_vapor'],
        'area_capacity':F(final['derived']['canopy_capacity']['value'])-F(first['derived']['canopy_capacity']['value'])-t['capacity_in']+t['capacity_out']-q['capacity_in'],
        'reduced_energy':du+da+F(latent)*dw-t['canopy_external']-t['air_external']-F(latent)*t['external_vapor']-t['incoming_heat']+t['outgoing_heat']-q['sensible_in']}
    for i,base in enumerate(bases):
        rows[f'leaf_age_{i}']=b[107+i]-F(base['age'])-t['indoor_air_temperature_time']/86400+F(base['air'])/86400+F(p['leaves'][i]['base_temperature']['value'])*(at-base['at'])/86400
        rows[f'leaf_carbon_{i}']=b[107+2*n+i]-F(base['carbon'])-t[f'leaf_{i}_inflow']+t[f'leaf_{i}_maintenance']+t[f'leaf_{i}_removal']
    return rows


def independent(context,initial_cp,samples,final_cp):
    data=context.value;p=data['program'];start=data['seed']['sample'];state=list(start['state']);units=model.short._flux_units(p)
    totals=[0.]*len(units);elapsed=frac(start['at']['elapsed_seconds_exact']);dt=Fraction.from_float(data['original']['grid_step_seconds'])
    profiles=model._profiles(context);current_rhs_calls=0;decimal_midpoint_corrections=0
    def rhs(y):
        nonlocal current_rhs_calls
        current_rhs_calls+=1;return model.short._evaluate(p,tuple(y),profiles)
    with localcontext()as dc:
        dc.prec=400
        dec=lambda f:Decimal(f.numerator)/Decimal(f.denominator)
        def advance(y,rates,h):
            nonlocal decimal_midpoint_corrections
            weights=[1]if len(rates)==1 else [1,2,2,1];denominator=1 if len(rates)==1 else 6;result=[]
            for i,v in enumerate(y):
                exact=Fraction.from_float(v)+h*sum((w*Fraction.from_float(rate[i])for w,rate in zip(weights,rates,strict=True)),Fraction(0))/denominator
                rounded=float(exact)
                approximate=float(Decimal.from_float(v)+dec(h)*sum((Decimal(w)*Decimal.from_float(rate[i])for w,rate in zip(weights,rates,strict=True)),Decimal(0))/denominator)
                if approximate!=rounded:
                    lo,hi=sorted([approximate,rounded])
                    assert nextafter(lo,inf)==hi and exact==(Fraction.from_float(lo)+Fraction.from_float(hi))/2
                    decimal_midpoint_corrections+=1
                result.append(rounded)
            return result
        k1,first=rhs(state);current=first;state_values=0
        for sample in samples:
            target=dt*(int(elapsed//dt)+1);h=target-elapsed;f1=model.short._flux(p,tuple(state),current)
            y2=advance(state,[k1],h/2);k2,r2=rhs(y2)
            y3=advance(state,[k2],h/2);k3,r3=rhs(y3)
            y4=advance(state,[k3],h);k4,r4=rhs(y4)
            state=advance(state,[k1,k2,k3,k4],h)
            totals=advance(totals,[f1,model.short._flux(p,tuple(y2),r2),model.short._flux(p,tuple(y3),r3),model.short._flux(p,tuple(y4),r4)],h)
            k1,current=rhs(state);elapsed=target
            assert state==sample['state']and frac(sample['at']['elapsed_seconds_exact'])==elapsed
            assert sample['at']['time_origin_utc']==start['at']['time_origin_utc']
            assert sample['derived']==model.short._view(current)['joint']['derived']
            state_values+=len(state)
    final=final_cp.value;assert totals==[final['segment_integrated_transfers'][k]['value']for k in units]
    F=Fraction.from_float
    branch={k:{'value':float(F(v)+F(data['seed']['branch_base_transfers'].get(k,{'value':0.})['value'])),'unit':unit}
            for(k,unit),v in zip(units.items(),totals,strict=True)}
    lifetime={k:{'value':float(F(row['value'])+F(data['base_lifetime_transfers'].get(k,{'value':0.})['value'])),'unit':row['unit']}for k,row in branch.items()}
    assert branch==final['branch_integrated_transfers']and lifetime==final['lifetime_integrated_transfers']
    own={name:{'value':float(sum((F(r['point_flows'][name]['value'])for r in data['records']),Fraction(0))),'unit':unit}for name,unit in model.POINT_UNITS.items()}
    allpoints={name:{'value':float(F(data['original']['left_checkpoint'].get('point_totals',{}).get(name,{'value':0.})['value'])+
        sum((F(row['point_flows'][name]['value'])for row in data['records']),Fraction(0))),'unit':unit}for name,unit in model.POINT_UNITS.items()}
    assert own==final['branch_point_transfers']and allpoints==final['lifetime_point_transfers']
    branch_bases=[];life_bases=[];old_n=len(data['source']['program']['leaves']);y0=data['branch_initial']['state'];t0=frac(data['branch_initial']['at']['elapsed_seconds_exact'])
    for i,leaf in enumerate(data['source']['program']['leaves']):branch_bases.append({'age':y0[107+i],'carbon':y0[107+2*old_n+i],'at':t0,'air':0.})
    for base in data['original']['source_birth_bases']:life_bases.append({'age':base['thermal_age'],'carbon':base['carbon'],'at':dt*base['step_index'],'air':base['air_temperature_integral']})
    for row in data['records']:
        for leaf in row['new_leaves']:
            branch_bases.append({'age':0.,'carbon':leaf['initial_carbon']['value'],'at':frac(row['at']),'air':row['branch_air_integral_at_birth']})
            life_bases.append({'age':0.,'carbon':leaf['initial_carbon']['value'],'at':frac(row['at']),'air':row['lifetime_air_integral_at_birth']})
    checks=0;largest=0.
    for prefix,flows,points,bases,origin in [('branch',branch,own,branch_bases,data['branch_initial']),('global',lifetime,allpoints,life_bases,data['original']['root_sample'])]:
        residuals=reference_ledgers(data,final['last_confirmed'],flows,points,bases,origin,elapsed,context._profiles[-1].values['latent_heat'])
        assert set(residuals)==set(final[prefix+'_balance_residuals'])
        for name,value in residuals.items():
            assert float(value)==final[prefix+'_balance_residuals'][name]['value']and abs(value)<=F(final[prefix+'_balance_budgets'][name]['value'])
            largest=max(largest,float(abs(value)/F(final[prefix+'_balance_budgets'][name]['value'])));checks+=1
    assert final['output_cursor']==initial_cp.value['output_cursor']+len(samples)
    return {'endpoint_state_values':state_values,'segment_transfer_values':len(units),'branch_and_lifetime_transfer_values':2*len(units),
            'exact_final_ledger_residuals':checks,'reference_RHS_evaluations':current_rhs_calls,'Decimal400_exact_midpoint_corrections':decimal_midpoint_corrections,'maximum_budget_utilisation':largest}


def verify(source,output):
    source,output=Path(source),Path(output);raw=(ROOT/'fixtures/crop-funded-fractional-continuation-fixtures-v1.json').read_bytes();declaration=json.loads(raw)
    for path,expected in declaration['sources'].items():assert sha256((ROOT/path).read_bytes()).hexdigest()==expected
    assert all(declaration['rights'][k] is True for k in ('use','display','redistribute'))
    register=json.loads((source/'register.json').read_bytes());assert register['declaration_sha256']==declaration['sources']['fixtures/crop-funded-event-state-fixtures-v2.json']
    output.mkdir(mode=0o750);access=ContentAccess(os.getuid(),os.getegid());driver=point_driver()
    web=json.loads((ROOT/'fixtures/crop-leaf-funded-birth-web-declaration-v1.json').read_bytes());records=[]
    for case in register['cases']:
        directory=source/'leaves'/str(case['case_index']);m=model.birth.leaf.read_funded_leaf_manifest(directory,access,case['leaf_root_sha256']);assert m['source_rights']['redistribute']is True
        pc=model.birth.prepare_fractional_birth_context(directory,source/'stem',access,leaf_root_sha256=case['leaf_root_sha256'],
            stem_root_sha256=register['stem_root_sha256'],stem_start_index=case['stem_start_index'],bracket_index=0,
            time_tolerance_seconds_exact={'numerator':'1','denominator':'1000000','unit':'s'})
        first=driver.declared(pc,declaration,web,declaration['initial_point']['leaf_count'],declaration['initial_point']['incoming_temperature_degC'])
        context=model.prepare_context(point_context=pc,inputs=first);initial=model.start(context)
        def run(ctx,seed,group):
            cp=seed;samples=[]
            for budget in group:
                result=model.advance_chunk(ctx,cp,budget);assert result['hold']is None
                cp=result['checkpoint'];samples.extend(result['samples'])
                if result['status']=='completed':break
            assert result['status']=='completed'
            return {**result,'samples':samples}
        baseline=run(context,initial,declaration['groupings'][0])
        metrics=independent(context,initial,baseline['samples'],baseline['checkpoint'])
        split=run(context,initial,declaration['groupings'][1]);assert split['checkpoint']._raw==baseline['checkpoint']._raw
        additional=declaration['additional_point'];middle=model.advance_chunk(context,initial,additional['after_grid_endpoints'])['checkpoint']
        second=driver.declared(pc,declaration,web,additional['leaf_count'],additional['incoming_temperature_degC'])
        extra=model.adopt_births(context,middle,extra_inputs(context,middle,second));after=model.start(extra)
        continued=run(extra,after,declaration['groupings'][0])
        extra_metrics=independent(extra,after,continued['samples'],continued['checkpoint'])
        for label,ctx,seed,run,check in [('initial',context,initial,baseline,metrics),('additional',extra,after,continued,extra_metrics)]:
            files={}
            for kind,data in [('context',ctx._raw),('initial-checkpoint',seed._raw),('final-checkpoint',run['checkpoint']._raw),('samples',model._canonical(run['samples']))]:
                name=f"case-{case['case_index']}-{label}-{kind}.json";(output/name).write_bytes(data);files[kind]={'path':name,'sha256':sha256(data).hexdigest(),'bytes':len(data)}
            records.append({'case_index':case['case_index'],'branch':label,'files':files,'endpoints':len(run['samples']),
                'leaf_count':len(ctx.value['program']['leaves']),'final_at':run['checkpoint'].value['at'],
                'chunk_grouping_final_bytes_equal':True if label=='initial' else 'unit_tested_separately','independent':check})
    summary={'scope':'software_research_only','G0_G4':'not_assessed','declaration_sha256':sha256(raw).hexdigest(),'records':records,
        'context_count':len(records),'known_512_metadata_hold':'not_resolved','source_code_sha256':model._pins(),
        'independent_RHS_is_existing_reviewed_oracle':'not_independent_agricultural_model_validation'}
    (output/'index.json').write_bytes(model._canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    print(json.dumps(verify(args.source,args.output),sort_keys=True))
