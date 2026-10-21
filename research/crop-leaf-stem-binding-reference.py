"""Owned synthetic attachment probe against an existing immutable stem artifact."""
from copy import deepcopy
from decimal import Decimal,localcontext
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.content_access import ContentAccess
from app.crop_leaf_population import initialize_leaf_population,advance_leaf_population
from app.crop_leaf_stem_binding import bind_leaf_population_to_stored_stem
from app.crop_rational_morphology_artifact_reader import read_rational_morphology_frame


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def fraction(value):return Fraction(int(value['numerator']),int(value['denominator']))


def seconds(value):
    value=Fraction(value);return {'numerator':str(value.numerator),'denominator':str(value.denominator),'unit':'s'}


def snapshot(directory):
    result={}
    for p in directory.iterdir():
        s=p.stat();result[p.name]=[s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,sha256(p.read_bytes()).hexdigest()]
    return result


def run(directory,root):
    access=ContentAccess(os.getuid(),os.getgid());before=snapshot(directory)
    program=json.loads((ROOT/'fixtures/crop-leaf-area-software-program-v1.json').read_bytes())
    initial=deepcopy(program['initialization']);prototype=initial['leaves'][0]['initialization'];events=[]
    # This explicit probe declaration is not a biological leaf-per-node rule.
    final=read_rational_morphology_frame(directory,access,root,index=11)
    for i,node in enumerate(final['internodes'][3:]):
        events.append({'leaf_id':'explicit-followup-leaf-'+str(i),'attachment_internode_id':node['internode_id'],
            'emerged_elapsed_seconds_exact':deepcopy(node['emerged_elapsed_seconds_exact']),
            **{k:deepcopy(prototype[k]) for k in ['curve','normalization','initial_area']},
            'base_temperature':deepcopy(prototype['clock_state']['base_temperature'])})
    state=initialize_leaf_population(inputs={'input_id':'owned-explicit-probe','initial_inventory':initial})['state']
    maximum=Decimal(0);points=0;frames=[];start=Fraction(0)
    for index in range(12):
        end=Fraction((index+1)*7200)
        chosen=[e for e in events if start<fraction(e['emerged_elapsed_seconds_exact'])<=end]
        state=advance_leaf_population(inputs={'input_id':'owned-step-'+str(index),'state':state,
            'segments':[{'start_elapsed_seconds_exact':seconds(start),'end_elapsed_seconds_exact':seconds(end),'air_temperature':{'value':22,'unit':'degC'}}],
            'births':chosen})['state']
        bound=bind_leaf_population_to_stored_stem(directory,access,root,index=index,population_state=state)
        current=[v['state'] for v in state['initial_inventory_state']['leaves']]+[v['state'] for v in state['new_leaves']]
        with localcontext() as context:
            context.prec=100;areas=[]
            for item in current:
                clock=item['clock_state'];age=(end-fraction(clock['emerged_elapsed_seconds_exact']))*17/86400
                assert fraction(clock['age_exact'])==age
                a=Decimal(age.numerator)/Decimal(age.denominator);values=item['area_state']['curve']['values']
                m,k,mid=(Decimal.from_float(float(values[key]['value'])) for key in ['maximum_area','steepness','inflection_age'])
                expected=m/(1+(-k*(a-mid)).exp());actual=Decimal.from_float(item['area_state']['area']['value'])
                difference=abs(actual-expected)/expected;assert difference<Decimal('1e-12');maximum=max(maximum,difference);points+=1;areas.append(expected)
            total=sum(areas);difference=abs(Decimal.from_float(bound['tracked_leaf_area']['value'])-total)/total
            assert difference<Decimal('1e-12');maximum=max(maximum,difference)
        frames.append({'index':index,'at':bound['at'],'leaf_count':bound['tracked_leaf_count'],'total_area_m2':bound['tracked_leaf_area']['value'],
            'binding_sha256':sha256(canonical(bound)).hexdigest(),'population_state_sha256':bound['population_state_sha256'],
            'stem_result_sha256':bound['stem_result_sha256']});start=end
    assert before==snapshot(directory)
    return {'frames':frames,'independent_area_and_exact_age_points':points,'independent_totals':12,'maximum_relative_difference':str(maximum),
        'explicit_synthetic_births':events,'original_blob_metadata_and_bytes_preserved':len(before),'new_numeric_artifact_published':False,
        'new_UI_deployment':False,'scope':'software_research_only','actual_farm_Runs':0,'G0_G4':'not_assessed'}


if __name__=='__main__':
    print(json.dumps(run(Path(sys.argv[1]),sys.argv[2]),sort_keys=True))
