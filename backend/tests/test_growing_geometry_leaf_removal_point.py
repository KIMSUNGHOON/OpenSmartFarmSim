from copy import deepcopy
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

import pytest

from app import crop_growing_geometry_continuation as resume
from app import crop_growing_geometry_leaf_removal_point as model
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT=Path(__file__).resolve().parents[2]
CASES=json.loads((ROOT/'fixtures/crop-growing-geometry-climate-reference-v1.json').read_bytes())['cases']


@pytest.fixture(scope='module')
def profiles():
    return {name:kind((ROOT/'fixtures'/file).read_bytes())for name,kind,file in (
        ('growth_profile',Growth,'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile',Cohort,'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile',Transport,'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile',Exchange,'crop-canopy-exchange-reference-parameters-v1.json'))}


@pytest.fixture(scope='module')
def samples(profiles):
    result=[]
    for case in CASES:
        p=deepcopy(case['program']);p['capacity_outflow']['value']=0
        ctx=resume.prepare_context(program=p,step_seconds=.125,step_count=16,**profiles)
        first=resume.start(ctx);middle=resume.advance_chunk(ctx,first,7)['checkpoint']
        last=resume.advance_chunk(ctx,middle,9)['checkpoint'];result.append((ctx,(first,middle,last)))
    return result


def declaration(ctx,cp,indices=(0,)):
    p=ctx.program;y=cp.value['last_confirmed']['state'];n=len(p['leaves']);floor=p['model_floor_area']['value']
    at=Fraction.from_float(ctx.manifest['numerical']['step_seconds'])*cp.value['step_index']
    mass=([y[1]*.25*floor,y[1]*.25*floor,y[1]*.5*floor]if n==3 else[y[1]*floor/n]*n)
    q=lambda v,u:{'value':v,'unit':u}
    k=p['scenario']['parameters']['leaf_heat_capacity']['value'];ref=p['scenario']['parameters']['reference_temperature']['value']
    tc=cp.value['last_confirmed']['derived']['canopy_temperature']['value']
    return {'schema_version':'growing-geometry-leaf-removal-point-input-v1','input_id':'own-point','origin':'synthetic',
        'context_sha256':ctx.root_sha256,'checkpoint_sha256':cp.sha256,
        'at_elapsed_seconds_exact':{'numerator':str(at.numerator),'denominator':str(at.denominator),'unit':'s'},
        'mass_basis':{'origin':'synthetic','evidence_level':'assumed','evidence_id':'own-current-carbon-distribution',
            'model_floor_area':deepcopy(p['model_floor_area']),
            'leaves':[{'leaf_id':leaf['leaf_id'],'carbohydrate':q(mass[i],'mg_CH2O')}for i,leaf in enumerate(p['leaves'])]},
        'events':[{'event_id':f'own-remove-{i}','leaf_id':p['leaves'][i]['leaf_id'],'carbohydrate':q(mass[i],'mg_CH2O'),
            'capacity':q(k*y[108+n+i]/floor,'J/m2_floor/K'),
            'sensible_energy':q(k*y[108+n+i]/floor*(tc-ref),'J/m2_floor'),
            'outgoing_temperature':q(tc,'degC')}for i in indices]}


def apply(ctx,cp,inputs):
    return model.apply_removals(context=ctx,raw_checkpoint=resume.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256,inputs=inputs)


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('position',range(3))
@pytest.mark.parametrize('indices',[(0,),(0,2)])
def test_point_independent_balances_and_original_state(samples,case,position,indices):
    ctx,points=samples[case];cp=points[position];inputs=declaration(ctx,cp,indices);before=deepcopy(inputs)
    result=apply(ctx,cp,inputs);assert inputs==before
    assert result==apply(ctx,cp,inputs)
    y=cp.value['last_confirmed']['state'];n=3;keep=[i for i in range(n)if i not in indices];after=result['after']['state']
    assert after[:1]==y[:1] and after[2:105]==y[2:105] and after[106:108]==y[106:108]
    assert after[108:108+len(keep)]==[y[108+i]for i in keep]
    assert after[108+len(keep):]==[y[108+n+i]for i in keep]
    assert result['original_interval_transfers']==cp.value['integrated_transfers']
    seed=json.loads(ctx._seed)
    assert result['original_curve_invariant']==seed['evaluation']['curve_residuals']
    assert result['original_initial_area_receipts']==seed['initial_area_receipts']
    assert result['after']['leaf_ids']==[ctx.program['leaves'][i]['leaf_id']for i in keep]
    with localcontext() as c:
        c.prec=120;d=Decimal.from_float;floor=d(ctx.program['model_floor_area']['value'])
        removed=sum((d(e['carbohydrate']['value'])for e in inputs['events']),Decimal(0))/floor
        expected=d(y[1])-removed
        assert abs(after[1]-float(expected))<=8e-13*abs(float(expected))
        area=sum((d(y[108+n+i])for i in keep),Decimal(0))/floor
        cap=area*d(ctx.program['scenario']['parameters']['leaf_heat_capacity']['value'])
        energy=d(y[105])-sum((d(e['sensible_energy']['value'])for e in inputs['events']),Decimal(0))
        for actual,reference in [(result['after']['leaf_area_index']['value'],area),(result['after']['capacity']['value'],cap),(after[105],energy)]:
            assert actual==0 if reference==0 else abs(actual-float(reference))<=3e-13*abs(float(reference))
    tc=cp.value['last_confirmed']['derived']['canopy_temperature']['value']
    assert abs(result['after']['canopy_temperature']['value']-tc)<=2e-13
    assert result['G0_G4']=='not_assessed'
    assert result['at_elapsed_seconds_exact']==inputs['at_elapsed_seconds_exact']
    with pytest.raises(resume.ContinuationRejected):
        raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode()
        resume.restore_checkpoint(ctx,raw,expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('mutation',[
    lambda x:x.update(origin='measured'),lambda x:x.update(extra=0),
    lambda x:x.update(context_sha256='0'*64),lambda x:x.update(checkpoint_sha256='0'*64),
    lambda x:x['at_elapsed_seconds_exact'].update(numerator='1'),
    lambda x:x['mass_basis']['leaves'].reverse(),lambda x:x['mass_basis']['leaves'].pop(),
    lambda x:x['mass_basis'].update(evidence_level='measured'),
    lambda x:x['mass_basis']['model_floor_area'].update(value=2),
    lambda x:x['mass_basis']['leaves'][0]['carbohydrate'].update(value=0),
    lambda x:x['mass_basis']['leaves'][0]['carbohydrate'].update(value=True),
    lambda x:x['mass_basis']['leaves'][0]['carbohydrate'].update(unit='g_DM'),
    lambda x:x['events'].clear(),lambda x:x['events'].append(deepcopy(x['events'][0])),
    lambda x:x['events'][0].update(leaf_id='missing'),
    lambda x:x['events'][0]['capacity'].update(value=0),
    lambda x:x['events'][0]['sensible_energy'].update(value=0),
    lambda x:x['events'][0]['outgoing_temperature'].update(value=10),
    lambda x:x['events'][0]['carbohydrate'].update(value=1),
    lambda x:x['events'][0]['sensible_energy'].update(unit='W/m2_floor'),
])
def test_invalid_point_is_atomic(samples,mutation):
    ctx,points=samples[0];cp=points[1];inputs=declaration(ctx,cp);mutation(inputs);old=deepcopy(inputs);saved=cp.value
    with pytest.raises(model.LeafRemovalPointHold):apply(ctx,cp,inputs)
    assert inputs==old and cp.value==saved


def test_all_leaf_removal_is_held(samples):
    ctx,points=samples[0];cp=points[0]
    with pytest.raises(model.LeafRemovalPointHold,match='EMPTY_CANOPY_HOLD'):apply(ctx,cp,declaration(ctx,cp,(0,1,2)))


def test_original_nonzero_continuous_capacity_outflow_is_held(profiles):
    for case in CASES:
        ctx=resume.prepare_context(program=case['program'],step_seconds=2,step_count=16,**profiles);cp=resume.start(ctx)
        with pytest.raises(model.LeafRemovalPointHold,match='DUPLICATE_REMOVAL_HOLD'):apply(ctx,cp,declaration(ctx,cp))


def test_point_never_reinitializes_or_advances(samples,monkeypatch):
    ctx,points=samples[0];cp=points[1];inputs=declaration(ctx,cp)
    def forbidden(*args,**kwargs):raise AssertionError('point cannot initialize, integrate or advance')
    monkeypatch.setattr(resume.short,'_prepare',forbidden);monkeypatch.setattr(resume.short,'integrate',forbidden)
    monkeypatch.setattr(resume,'prepare_context',forbidden);monkeypatch.setattr(resume,'start',forbidden)
    monkeypatch.setattr(resume,'advance_chunk',forbidden)
    assert apply(ctx,cp,inputs)['after']['state']


def test_independent_mass_distribution_cannot_change_without_event_agreement(samples):
    ctx,points=samples[0];cp=points[0];inputs=declaration(ctx,cp)
    inputs['mass_basis']['leaves'][0]['carbohydrate']['value']+=100
    inputs['mass_basis']['leaves'][1]['carbohydrate']['value']-=100
    with pytest.raises(model.LeafRemovalPointHold,match='MASS_HOLD'):apply(ctx,cp,inputs)


@pytest.mark.parametrize('fault',['bytes','digest','context','code','profile','oversize','subnormal','infinity'])
def test_checkpoint_and_numeric_boundaries(samples,fault):
    ctx,points=samples[0];cp=points[1];inputs=declaration(ctx,cp);raw=cp._raw;expected=cp.sha256
    if fault=='bytes':raw=raw+b' '
    if fault=='digest':expected='0'*64
    if fault=='context':ctx=samples[1][0]
    if fault in ('code','profile'):
        manifest=ctx.manifest;identity=manifest['identity']
        if fault=='code':identity['engine_code_sha256']='0'*64
        else:identity['profile_sha256']['growth']='0'*64
        changed=resume._canonical(manifest);ctx=replace(ctx,_manifest=changed,root_sha256=sha256(changed).hexdigest())
    if fault=='oversize':inputs['input_id']='x'*(2*1024**2)
    if fault=='subnormal':inputs['events'][0]['capacity']['value']=5e-324
    if fault=='infinity':inputs['events'][0]['sensible_energy']['value']=float('inf')
    with pytest.raises(model.LeafRemovalPointHold):
        model.apply_removals(context=ctx,raw_checkpoint=raw,expected_sha256=expected,inputs=inputs)


def test_nonzero_carbon_removal_also_needs_attribution(profiles):
    p=deepcopy(CASES[0]['program']);p['capacity_outflow']['value']=0;p['scenario']['removals']['leaf']['value']=.001
    ctx=resume.prepare_context(program=p,step_seconds=2,step_count=16,**profiles);cp=resume.start(ctx)
    with pytest.raises(model.LeafRemovalPointHold,match='DUPLICATE_REMOVAL_HOLD'):apply(ctx,cp,declaration(ctx,cp))


def test_zero_reference_energy_remains_exactly_zero(profiles):
    p=deepcopy(CASES[0]['program']);p['capacity_outflow']['value']=0
    p['scenario']['parameters']['reference_temperature']['value']=20
    p['scenario']['climate_state']['canopy_sensible_energy']['value']=0
    ctx=resume.prepare_context(program=p,step_seconds=.125,step_count=1,**profiles);cp=resume.start(ctx)
    result=apply(ctx,cp,declaration(ctx,cp))
    assert result['point_outflows']['sensible_energy']['value']==0
    assert result['after']['state'][105]==0
    assert result['after']['canopy_temperature']['value']==20


def test_512_declared_leaves_keep_original_order_and_area(profiles):
    p=deepcopy(CASES[0]['program']);p['capacity_outflow']['value']=0
    p['leaves']=[{**deepcopy(p['leaves'][0]),'leaf_id':f'own-{i}'}for i in range(512)]
    p['model_floor_area']['value']=512
    k=p['scenario']['parameters']['leaf_heat_capacity']['value'];ref=p['scenario']['parameters']['reference_temperature']['value']
    p['scenario']['climate_state']['canopy_sensible_energy']['value']=k*.25*(20-ref)
    ctx=resume.prepare_context(program=p,step_seconds=.125,step_count=1,**profiles);cp=resume.start(ctx)
    inputs=declaration(ctx,cp);inputs['mass_basis']['leaves']=[{'leaf_id':f'own-{i}','carbohydrate':{'value':50000,'unit':'mg_CH2O'}}for i in range(512)]
    inputs['events'][0]['carbohydrate']['value']=50000
    result=apply(ctx,cp,inputs)
    assert result['after']['leaf_ids']==[f'own-{i}'for i in range(1,512)]
    assert len(result['after']['state'])==108+2*511
    assert result['after']['state'][108+511:]==cp.value['last_confirmed']['state'][108+512+1:]
