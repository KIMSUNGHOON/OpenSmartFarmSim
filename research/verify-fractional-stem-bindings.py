"""Independent clocks, logistic lengths and unchanged stored leaf/CP quantities."""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app import crop_funded_fractional_stem_binding as model
from app.content_access import ContentAccess


def frac(v):return Fraction(int(v['numerator']),int(v['denominator']))


def load_driver():
    spec=importlib.util.spec_from_file_location('continued_QA',ROOT/'research/verify-funded-fractional-continuation.py')
    driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver);return driver


def initial_links(context,declaration):
    data=context.value;selection=data['source']['candidate']['selection']
    manifest=json.loads((context._leaf_directory/selection['leaf_root_sha256']).read_bytes())
    return {'schema_version':'funded-fractional-initial-links-v1','input_id':'own-initial-coupled-links','origin':'synthetic',
        'context_sha256':context.sha256,'leaf_root_sha256':selection['leaf_root_sha256'],'stem_root_sha256':selection['stem_root_sha256'],
        'root_initial_state_sha256':manifest['initial_state_sha256'],'model_floor_area':deepcopy(data['program']['model_floor_area']),
        'initial_attachments':deepcopy(declaration['initial_attachments']),'rights':deepcopy(declaration['rights']),'reviewer':declaration['reviewer']}


def independent(context,checkpoint,result,stem_state):
    data=context.value;cp=checkpoint.value;F=Fraction.from_float;time=frac(cp['at']['elapsed_seconds_exact'])
    birth=frac(data['records'][0]['at']);timeline=stem_state['timeline_state'];base=F(float(timeline['base_temperature']['value']))
    air=F(cp['lifetime_integrated_transfers']['indoor_air_temperature_time']['value']);first_air=F(data['base_lifetime_transfers']['indoor_air_temperature_time']['value'])
    expected_shoot=frac(timeline['age_exact'])+(air-base*time)/86400
    assert frac(result['shoot']['shoot_age_exact'])==expected_shoot
    threshold=frac(timeline['next_threshold_exact']);birth_shoot=frac(timeline['age_exact'])+(first_air-base*birth)/86400
    assert frac(result['shoot']['birth']['threshold_overshoot_exact'])==birth_shoot-threshold
    expected_ages=[frac(n['length_state']['clock_state']['age_exact'])+(air-base*time)/86400 for n in stem_state['internodes']]
    expected_ages.append((air-first_air-base*(time-birth))/86400)
    with localcontext()as dc:
        dc.prec=110;D=Decimal.from_float;maximum=Decimal(0)
        for node,age in zip(result['shoot']['internodes'],expected_ages,strict=True):
            assert frac(node['age_exact'])==age
            values=node['curve']['values'];a=Decimal(age.numerator)/Decimal(age.denominator)
            x=D(float(values['steepness']['value']))*(a-D(float(values['inflection_age']['value'])))
            exact=D(float(values['maximum_length']['value']))/(1+(-x).exp())
            relative=abs(D(node['length']['value'])-exact)/exact;assert relative<=Decimal('2e-15');maximum=max(maximum,relative)
    count=len(result['leaves']);y=cp['last_confirmed']['state']
    for i,leaf in enumerate(result['leaves']):
        assert leaf['leaf_id']==data['program']['leaves'][i]['leaf_id']
        assert [leaf[k]['value']for k in ['thermal_age','area','carbohydrate']]==[y[107+i],y[107+count+i],y[107+2*count+i]]
    assert result['checkpoint']==cp and result['at']==cp['at']and result['model_floor_area']==data['program']['model_floor_area']
    assert result['shoot']['internodes'][-1]['internode_id']==result['leaves'][-1]['attachment_internode_id']
    assert result['shoot']['birth']['numerical_root_interval']==data['source']['candidate']['source_root_certificate']['numerical_root_interval']
    assert result['G0_G4']=='not_assessed'and result['R2']=='not_approved'
    return {'exact_age_and_overshoot_checks':len(expected_ages)+2,'independent_lengths':len(expected_ages),
        'leaf_state_values':3*count,'maximum_length_relative_difference':float(maximum)}


def verify(source,output):
    source,output=Path(source),Path(output);raw=(ROOT/'fixtures/crop-funded-fractional-stem-bindings-v1.json').read_bytes();declaration=json.loads(raw)
    register=json.loads((source/'register.json').read_bytes());assert register['declaration_sha256']==sha256(raw).hexdigest()
    web_raw=(ROOT/declaration['new_values_source']).read_bytes();assert sha256(web_raw).hexdigest()==declaration['new_values_source_sha256'];web=json.loads(web_raw)
    manifest=json.loads((source/'stem'/register['stem_root_sha256']).read_bytes());state=json.loads((source/'stem'/manifest['samples'][0]['result_sha256']).read_bytes())['state']
    output.mkdir(mode=0o750);access=ContentAccess(os.getuid(),os.getegid());driver=load_driver();point_driver=driver.point_driver();records=[]
    for case in register['cases']:
        directory=source/'leaves'/str(case['case_index']);pc=model.crop.birth.prepare_fractional_birth_context(directory,source/'stem',access,
            leaf_root_sha256=case['leaf_root_sha256'],stem_root_sha256=register['stem_root_sha256'],stem_start_index=case['stem_start_index'],bracket_index=0,
            time_tolerance_seconds_exact={'numerator':'1','denominator':'1000000','unit':'s'})
        identity=model.describe_fractional_internode(pc);first=point_driver.declared(pc,declaration,web,1,web['new_leaf_values']['incoming_temperature']['value'])
        first['events'][0]['attachment_internode_id']=identity['internode_id'];ctx=model.crop.prepare_context(point_context=pc,inputs=first)
        initial=model.crop.start(ctx);mid_run=model.crop.advance_chunk(ctx,initial,1);assert mid_run['hold']is None;mid=mid_run['checkpoint']
        end_run=model.crop.advance_chunk(ctx,mid,128);assert end_run['status']=='completed';final=end_run['checkpoint']
        next_point=driver.extra_inputs(ctx,mid,first);extra=model.crop.adopt_births(ctx,mid,next_point);after=model.crop.start(extra)
        continued=model.crop.advance_chunk(extra,after,128);assert continued['status']=='completed'
        for branch,current in [('initial',ctx),('additional',extra)]:
            name=f"case-{case['case_index']}-{branch}-context.json";(output/name).write_bytes(current._raw)
        for label,current,cp in [('initial',ctx,initial),('mid',ctx,mid),('final',ctx,final),('additional',extra,after),('additional-final',extra,continued['checkpoint'])]:
            value=model.bind_fractional_crop(current,cp,initial_links(current,declaration));check=independent(current,cp,value,state)
            name=f"case-{case['case_index']}-{label}-binding.json";data=model.crop._canonical(value);(output/name).write_bytes(data)
            records.append({'case_index':case['case_index'],'label':label,'path':name,'sha256':sha256(data).hexdigest(),'bytes':len(data),
                'context_path':f"case-{case['case_index']}-{'additional'if label.startswith('additional')else'initial'}-context.json",'independent':check})
    result={'scope':'software_research_only','G0_G4':'not_assessed','R2':'not_approved','declaration_sha256':sha256(raw).hexdigest(),
        'records':records,'code_sha256':model._pins(),'independent_scope':'Fraction clocks/Decimal110 logistic/unchanged CP leaf values; existing RHS validation shared',
        'new_stem_carbon_allocation':'not_independently_allocated_in_aggregate_stem_pool','initial_leaf_past_emergence':'unknown carry-over input',
        'known_512_request_hold':'unchanged, not retested or accepted'}
    (output/'index.json').write_bytes(model.crop._canonical(result));return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    print(json.dumps(verify(args.source,args.output),sort_keys=True))
