from copy import deepcopy
from decimal import Decimal,localcontext
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app.crop_leaf_population_artifact_reader import read_leaf_population_frame
from app.crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore
from app.crop_morphology_artifact_reader import _canonical
from test_crop_leaf_population_artifact_producer import source,produce,PROGRAM
from test_crop_leaf_stem_binding import snapshot


def fraction(value):return Fraction(int(value['numerator']),int(value['denominator']))


def test_all_original_12_frames_52_independent_areas_and_source_scope(source,tmp_path,monkeypatch):
    directory=tmp_path/'population';root=produce(directory,source);before=snapshot(directory);program=json.loads(PROGRAM)
    from app import crop_leaf_population as population,crop_leaf_area as point,crop_rational_leaf_area as leaf,crop_leaf_population_artifact_producer as producer
    from app.job_store import JobStore
    import psycopg
    def forbidden(*a,**kw):raise AssertionError('stored frame crossed compute/write boundary')
    for obj,methods in [(population,['initialize_leaf_population','normalize_leaf_population_state','advance_leaf_population']),
                        (point,['calculate_leaf_area_point','initialize_leaf_area','normalize_leaf_area_state']),
                        (leaf,['initialize_rational_leaf_area','advance_rational_leaf_area']),
                        (producer,['produce_leaf_population_artifact']),(MorphologyBlobStore,['put']),
                        (JobStore,['connect']),(psycopg,['connect'])]:
        for name in methods:monkeypatch.setattr(obj,name,forbidden)
    counts=[];points=0
    for index in range(12):
        frame=read_leaf_population_frame(directory,source[1],root,index=index);counts.append(frame['tracked_leaf_count'])
        assert frame['schema_version']=='leaf-population-replay-frame-v1' and frame['artifact_sha256']==root
        assert frame['scope']=='software_research_only' and frame['gates']=='not_assessed' and frame['claim_scope']=='synthetic_crop_math_only'
        assert frame['at']==frame['stem']['at'] and frame['tracked_leaf_count']==len(frame['leaves'])
        end=Fraction((index+1)*7200);expected=[]
        with localcontext() as context:
            context.prec=100
            for item in frame['leaves']:
                initial=program['initialization']['initial_inventory']['leaves']
                initial_match=next((q for q in initial if q['initialization']['clock_state']['leaf_id']==item['leaf_id']),None)
                if initial_match:
                    curve=initial_match['initialization']['curve'];base=initial_match['initialization']['clock_state']['base_temperature']['value']
                else:
                    event=next(q for q in program['births'] if q['leaf_id']==item['leaf_id']);curve=event['curve'];base=event['base_temperature']['value']
                age=(end-fraction(item['emerged_elapsed_seconds_exact']))*(Fraction(22)-Fraction.from_float(float(base)))/86400;assert fraction(item['age_exact'])==age
                a=Decimal(age.numerator)/Decimal(age.denominator)
                m,k,mid=(Decimal.from_float(float(curve['values'][key]['value'])) for key in ['maximum_area','steepness','inflection_age'])
                target=m/(1+(-k*(a-mid)).exp());expected.append(target)
                assert item['area']['unit']=='m2' and item['area']['value']==pytest.approx(float(target),rel=1e-12,abs=0);points+=1
            assert frame['tracked_leaf_area']['value']==pytest.approx(float(sum(expected)),rel=1e-12,abs=0)
    assert counts==[3,3,3,4,4,4,4,5,5,5,6,6] and points==52 and snapshot(directory)==before


@pytest.mark.parametrize('index',[-1,12,True,.5])
def test_explicit_stored_index(source,tmp_path,index):
    directory=tmp_path/'population';root=produce(directory,source)
    with pytest.raises(MorphologyArtifactHold):read_leaf_population_frame(directory,source[1],root,index=index)


def rehash_frame(directory,access,root,change):
    with MorphologyBlobStore(directory,access,write=True) as store:
        m=json.loads(store.get(root,maximum=2*1024**2));d=m['samples'][-1]
        r=json.loads(store.get(d['result_sha256'],maximum=2*1024**2));b=json.loads(store.get(d['binding_sha256'],maximum=2*1024**2))
        change(r,b)
        raw=_canonical(r);d['result_sha256']=store.put(raw,maximum=2*1024**2);d['result_bytes']=len(raw)
        d['state_sha256']=sha256(_canonical(r['state'])).hexdigest();d['input_sha256']=r['input_sha256'];m['terminal_state_sha256']=d['state_sha256']
        b['population_state_sha256']=d['state_sha256'];raw=_canonical(b);d['binding_sha256']=store.put(raw,maximum=2*1024**2);d['binding_bytes']=len(raw)
        return store.put(_canonical(m),maximum=2*1024**2)


@pytest.mark.parametrize('change',['leaf-ID','area-unit','birth-time','new-count','tracked-count','initial-order','missing-declaration',
                                   'declaration-hash','missing-new-leaf','curve','requested-area','clock-at','projection-only'])
def test_rehashed_semantic_and_projection_changes_hold(source,tmp_path,change):
    directory=tmp_path/'population';root=produce(directory,source)
    def mutate(r,b):
        n=r['state']['new_leaves'][-1];s=n['state'];a=s['area_state']
        if change=='leaf-ID':s['clock_state']['leaf_id']='wrong';a['leaf_id']='wrong';a['anchor']['leaf_id']='wrong';b['leaves'][-1]['leaf_id']='wrong'
        elif change=='area-unit':a['area']['unit']='cm2';b['leaves'][-1]['area']['unit']='cm2'
        elif change=='birth-time':s['clock_state']['emerged_elapsed_seconds_exact']['numerator']='1';b['leaves'][-1]['emerged_elapsed_seconds_exact']['numerator']='1'
        elif change=='new-count':r['new_leaf_count']+=1
        elif change=='tracked-count':r['tracked_leaf_count']+=1;b['tracked_leaf_count']+=1
        elif change=='initial-order':r['state']['initial_inventory_state']['leaves'].reverse();b['leaves'][:3]=list(reversed(b['leaves'][:3]))
        elif change=='missing-declaration':n.pop('declaration')
        elif change=='declaration-hash':n['declaration_sha256']='0'*64;r['state']['birth_inventory'][-1]['declaration_sha256']='0'*64
        elif change=='missing-new-leaf':
            r['state']['new_leaves'].pop();r['state']['birth_inventory'].pop();r['tracked_leaf_count']-=1;b['leaves'].pop();b['tracked_leaf_count']-=1
        elif change=='curve':
            from app.crop_leaf_artifact_reader import _curve
            a['curve']['values']['inflection_age']['value']=9;a['curve_sha256']=_curve(a['curve']);a['anchor']['curve_sha256']=a['curve_sha256']
        elif change=='requested-area':a['anchor']['requested_area']['value']*=.5
        elif change=='clock-at':s['clock_state']['at_elapsed_seconds_exact']['numerator']='86401'
        elif change=='projection-only':b['leaves'][-1]['area']['value']*=.9
    forged=rehash_frame(directory,source[1],root,mutate)
    with pytest.raises(MorphologyArtifactHold):read_leaf_population_frame(directory,source[1],forged,index=11)
