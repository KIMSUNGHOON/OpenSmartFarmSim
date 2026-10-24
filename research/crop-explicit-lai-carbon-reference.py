"""Independent Decimal explicit-LAI whole-plant oracle; no app imports."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[1]
INPUTS=('fixtures/crop-growth-reference-parameters-v1.json','fixtures/crop-fruit-cohort-reference-parameters-v1.json',
 'fixtures/crop-plant-startup-reference-cases-v1.json','research/crop-plant-startup-reference.py',
 'research/crop-explicit-lai-photosynthesis-reference.py')


def non_optical(y,f,r,p,photo):
    one=Decimal(1);two=Decimal(2);buffer,leaf,stem,_,T,tsum=y[:6];tc=f['canopy_temperature']
    available=one/(one+(-p['buffer_empty_slope']*(buffer-p['cBufMin'])).exp())
    instant=one/(one+(-p['instant_low_slope']*(tc-p['tCanMin'])).exp())/(one+(p['instant_high_slope']*(tc-p['tCanMax'])).exp())
    averaged=one/(one+(-p['filtered_low_slope']*(T-p['tCan24Min'])).exp())/(one+(p['filtered_high_slope']*(T-p['tCan24Max'])).exp())
    x=tsum/p['tEndSum'];smooth=p['development_smoothing_squared']
    development=(x+(x*x+smooth).sqrt())/two-(x-one+((x-one)**2+smooth).sqrt())/two
    common=available*averaged*(p['allocation_temperature_slope']*T+p['allocation_temperature_intercept'])
    lf=common*p['rgLeaf'];sf=common*p['rgStem'];ff=common*instant*development*p['rgFruit']
    growth=p['cLeafG']*lf+p['cStemG']*sf+p['cFruitG']*ff
    factor=(one-(-p['cRgr']*p['rgr']).exp())*(p['q10m'].ln()*(T-p['maintenance_temperature_reference_c'])/p['q10_temperature_interval_c']).exp()
    lm=factor*leaf*p['cLeafM'];sm=factor*stem*p['cStemM']
    return [photo-lf-sf-ff-growth,lf-lm-r['leaf'],sf-sm-r['stem_root'],ff,
            (tc-T)/p['seconds_per_day'],tc/p['seconds_per_day'],photo,growth,lm,sm,Decimal(0)]


def generate():
    raw={path:(ROOT/path).read_bytes() for path in INPUTS}
    p_document=json.loads(raw[INPUTS[0]]);cp_document=json.loads(raw[INPUTS[1]])
    p={key:Decimal(str(row['value']))for key,row in p_document['parameters'].items()}
    cp={key:Decimal(row['source_value'])for key,row in cp_document['parameters'].items()}
    optical=runpy.run_path(str(ROOT/INPUTS[4]))['independent_optics']
    whole=runpy.run_path(str(ROOT/INPUTS[3]))['calculate']
    sources=json.loads(raw[INPUTS[2]])['cases'];cases=[]
    experiments=[(source,None,float(p_document['parameters']['sla']['value'])*source['state']['values']['leaf']['value']*2,'double-LAI')for source in sources]
    edge=next(source for source in sources if source['forcing']['values']['canopy_temperature']['value']==17)
    experiments += [(edge,1,1.0,'legacy-domain-outside'),(edge,None,0.001,'explicit-domain-outside')]
    with localcontext()as context:
        context.prec=120
        for source,leaf_override,lai,label in experiments:
            case=deepcopy(source)
            if leaf_override is not None:case['state']['values']['leaf']['value']=leaf_override
            probe={'input_id':'independent-explicit-carbon-optical','origin':'synthetic','values':{
                **deepcopy(case['forcing']['values']),'buffer':deepcopy(case['state']['values']['buffer']),
                'leaf_area_index':{'value':lai,'unit':'m2_leaf/m2_floor'}}}
            optics=optical(probe,p_document['parameters'])
            expected=None
            if optics is not None:
                photo=Decimal(optics['photosynthesis'])
                expected=whole(case,p,cp,lambda y,f,r,parameters:non_optical(y,f,r,parameters,photo))
                expected['lai']=str(Decimal(str(lai)))
            cases.append({'case_id':source['case_id']+'-'+label,'source_case_id':source['case_id'],
                'leaf_carbohydrate_override':leaf_override,'geometry':{'input_id':'explicit-carbon-reference','origin':'synthetic',
                 'values':{'leaf_area_index':{'value':lai,'unit':'m2_leaf/m2_floor'}}},
                'expected':expected,'status':'supported'if expected is not None else'COMPENSATION_POINT_HOLD'})
    assert len(cases)==24 and not any(name=='app'or name.startswith('app.')for name in sys.modules)
    return {'schema_version':'explicit-lai-carbon-cohort-decimal-reference-v1','origin':'own_synthetic_software_fixture',
        'G0_G4':'not_assessed','independent_precision':120,'input_sha256':{key:sha256(value).hexdigest()for key,value in raw.items()},
        'generator_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'cases':cases}


if __name__=='__main__':
    output=Path(sys.argv[1]);data=generate();output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'cases':len(data['cases']),'supported':sum(c['status']=='supported'for c in data['cases']),
                      'app_imports':0,'sha256':sha256(output.read_bytes()).hexdigest()}))
