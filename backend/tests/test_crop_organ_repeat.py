from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_organ_repeat as model
from test_crop_organ_successor_point import row, inputs, pending, short_event_context, captured, candidates, crossings, contexts, roots, stored, profiles, TOLERANCE


def adopt(row,with_leaf=True):
    context,raw,digest,_=row
    return model.adopt_first(context,raw,expected_sha256=digest,time_tolerance_seconds_exact=TOLERANCE,inputs=inputs(row,with_leaf))


@pytest.mark.parametrize('with_leaf',[False,True])
def test_first_successor_creates_genuine_new_context_with_consumed_schedule_and_exact_global_composition(row,with_leaf):
    context=adopt(row,with_leaf);cp=model.start(context);data=context.value
    assert type(context)is model.Context and type(cp)is model.Checkpoint
    assert data['origin_context_sha256']==row[0].root_sha256
    assert data['seed']['parent_context_sha256']==row[0].root_sha256 and data['seed']['parent_checkpoint_sha256']==row[2]
    assert data['seed']['source_context_sha256']==row[0].value['captured']['source_context_sha256']
    assert data['seed']['source_checkpoint_sha256']==row[0].value['captured']['source_checkpoint_sha256']
    old=row[3]['source_prefix'];new=cp.value
    assert new['event_sequence']==old['event_sequence']+1
    assert new['schedule']['consumed_sequence']==old['schedule']['next_sequence']
    assert new['schedule']['next_sequence']==old['schedule']['next_sequence']+1
    assert new['at']==row[3]['at'] and new['branch_steps']==0
    assert len(new['last_confirmed']['state'])==len(old['last_confirmed']['state'])+1+3*with_leaf
    assert new['output_cursor']==old['output_cursor']+2 and new['point_totals_exact']!=old['point_totals_exact']
    assert all(model.X(q['budget_exact'])==0 for q in new['branch_ledgers'].values())
    assert all(abs(model.X(q['residual_exact']))<=model.X(q['budget_exact']) for q in new['global_ledgers'].values())
    first=model.advance_chunk(context,cp,1)
    assert first['checkpoint']is not None and first['intervals'][0]['step_seconds_exact']==data['seed']['original_grid_position']['remaining_to_next_grid_seconds_exact']
    assert first['checkpoint'].value['at']['elapsed_seconds_exact']==data['seed']['original_grid_position']['next_grid_elapsed_seconds_exact']


def repeat_inputs(context,raw,digest,candidate):
    from app import crop_organ_repeat_events as events
    data=model._context(context);p=data['captured']['program'];event=events._source_event(data,candidate)
    rights=json.loads(context._receipts[-1])['inputs']['rights']
    value={'schema_version':'individual-organ-successor-material-point-input-v1','input_id':'own-repeat-'+str(event['sequence']),
        'origin':'synthetic','policy':events.POLICY,'context_sha256':context.root_sha256,'checkpoint_sha256':digest,
        'candidate_sha256':candidate['calculation_sha256'],'initial_binding_sha256':data['source_snapshot']['manifest']['initial_binding_sha256'],
        'at_elapsed_seconds_exact':deepcopy(candidate['at']['elapsed_seconds_exact']),'model_floor_area':deepcopy(p['model_floor_area']),
        'source_event_id':event['source_event_id'],'source_threshold_sequence':event['sequence'],'source_threshold_exact':deepcopy(event['threshold_exact']),
        'parent_internode_id':[item['compartment_id']for item in p['stem_root_compartments']if item['kind']=='internode'][-1],
        'internode':{'compartment_id':event['internode_id'],'kind':'internode','initial_carbon':{'value':.25,'unit':events.MASS},
            'sink_weight':{'value':1.,'unit':'1'},'carbon_removal':{'value':0.,'unit':events.MASS+'/s'}},
        'leaf':None,'rights':deepcopy(rights),'reviewer':'native-software-QA-not-cultivar-validation'}
    leaf=deepcopy(p['leaves'][0]);area=model.stock.short.old.leaf_area._area_at(Fraction(0),leaf['curve'])
    leaf.update(leaf_id=event['leaf_id'],thermal_age={'value':0.,'unit':'degC_day'},initial_area=area,initial_carbon={'value':.125,'unit':events.MASS})
    value['leaf']={'declaration':leaf,'incoming_temperature':{'value':22.,'unit':'degC'}}
    return value


def drive(context,split=False):
    from app import crop_organ_repeat_events as events
    cp=model.start(context);samples=[];event_ids=[];event_times=[];count=0
    while count<256:
        count+=1
        result=model.advance_chunk(context,cp,1 if split else 128);samples.extend(result['samples'])
        if result['status']=='completed':return context,result['checkpoint'],samples,event_ids,event_times
        if result['pending_event']is None:
            assert result['checkpoint']is not None,result['hold'];cp=result['checkpoint'];continue
        raw=model._canonical(result['last_confirmed']);digest=sha256(raw).hexdigest()
        candidate=events.calculate_candidate(context,raw,expected_sha256=digest,time_tolerance_seconds_exact=TOLERANCE)
        value=repeat_inputs(context,raw,digest,candidate)
        event_ids.append(candidate['source_interval']['source_event_id']);event_times.append(candidate['at'])
        context=model.adopt_successor(context,raw,expected_sha256=digest,time_tolerance_seconds_exact=TOLERANCE,inputs=value)
        if split:
            context=model.restore_context(context._origin,model.context_bytes(context),expected_sha256=context.root_sha256,
                receipt_bytes=model.proof_bytes(context))
        cp=model.start(context)
    raise AssertionError('explicit finite original horizon must terminate')


def test_repeated_new_family_events_reach_original_horizon_with_partition_and_restore_identical_bytes(row):
    initial=adopt(row);whole=drive(initial);split=drive(initial,True)
    assert len(whole[3])>=2 and whole[3:]==split[3:] and whole[2]==split[2]
    assert model.context_bytes(whole[0])==model.context_bytes(split[0])
    assert model.checkpoint_bytes(whole[0],whole[1])==model.checkpoint_bytes(split[0],split[1])
    assert model.X(whole[1].value['at']['elapsed_seconds_exact'])==512
    assert len(whole[0]._receipts)==1+len(whole[3]) and len(set(whole[3]))==len(whole[3])
    assert whole[1].value['schedule']['next_sequence']==initial.value['seed']['schedule']['next_sequence']+len(whole[3])


def test_context_proof_start_and_checkpoint_restore_do_not_reexecute_past_points(row,monkeypatch):
    context=adopt(row);raw=model.context_bytes(context);proofs=model.proof_bytes(context);cp=model.start(context);cpraw=model.checkpoint_bytes(context,cp)
    evaluate=model.stock.short._evaluate;calls=[]
    def counted(*args,**kw):calls.append(1);return evaluate(*args,**kw)
    def forbidden(*args,**kw):raise AssertionError('no past material jump, initialization or integration')
    for owner,name in [(model.material,'apply_successor_material_point'),(model.material.stem,'_jump'),(model.material.leaf,'_jump'),
            (model.stock.short.old.leaf_area,'initialize_leaf_area'),(model.stock.short.old.leaf_area,'normalize_leaf_area_state'),
            (model.legacy,'start'),(model.legacy,'advance_chunk'),(model.stock,'adopt_births')]:monkeypatch.setattr(owner,name,forbidden)
    monkeypatch.setattr(model.stock.short,'_evaluate',counted)
    restored=model.restore_context(row[0],raw,expected_sha256=context.root_sha256,receipt_bytes=proofs)
    assert model.checkpoint_bytes(restored,model.start(restored))==cpraw and calls==[]
    restored_cp=model.restore_checkpoint(restored,cpraw,expected_sha256=cp.sha256)
    assert model.checkpoint_bytes(restored,restored_cp)==cpraw and calls==[1]
