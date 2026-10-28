"""One source-bound supply-limited material point; no schedule/CP adoption."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json

from . import crop_supply_morphology_newborn_point_core as core
from . import crop_supply_morphology_newborn_point_books as books

candidate,resume=core.candidate,core.resume
source=core.source
Q,X,F=core.Q,core.X,core.F
VERSION='supply-morphology-newborn-material-point-research-v1'
POLICY='explicit-compatible-successor-seed-on-newborn-trajectory-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES=2*1024**2
MAX_INPUT_BYTES=128*1024
FIELDS={'schema_version','input_id','origin','policy','parameter_source','parameter_revision','context_sha256','checkpoint_sha256','candidate_sha256',
    'initial_binding_sha256','at_elapsed_seconds_exact','model_floor_area','source_event_id','source_threshold_sequence','source_threshold_exact','parent_internode_id','internode','leaf','rights','reviewer'}


class SupplyPointHold(ValueError):
    pass


def _pins():
    root=Path(__file__).resolve().parents[2];pins={**candidate._pins(),'backend/app/crop_supply_morphology_newborn_point.py':CODE_SHA256,
        'backend/app/crop_supply_morphology_newborn_point_core.py':core.CODE_SHA256,'backend/app/crop_supply_morphology_newborn_point_books.py':books.CODE_SHA256,
        'backend/app/crop_supply_morphology_birth_stage.py':core.stage.CODE_SHA256}
    core.need(all(sha256((root/name).read_bytes()).hexdigest()==v for name,v in pins.items()),'CODE_HOLD: original material point/kernel sources required')
    return pins


def apply_fractional_material_point(context,raw_checkpoint,*,expected_sha256,time_tolerance_seconds_exact,inputs):
    try:
        pins=_pins();core.arithmetic._closed(inputs,FIELDS);raw=resume._canonical(inputs,MAX_INPUT_BYTES);v=json.loads(raw)
        data=resume._context(context);p=data['program'];part=source.stock.short.stock.part
        for k in ['input_id','reviewer','parent_internode_id','parameter_revision']:part._id(v[k])
        core.stem._rights(v['rights'])
        core.need(v['schema_version']=='supply-morphology-newborn-material-point-input-v1'and v['origin']=='synthetic'and v['policy']==POLICY
            and v['parameter_source']=='own_declared_synthetic_assumptions','POLICY_HOLD: explicit source-bound synthetic construction parameters required')
        for k in ['context_sha256','checkpoint_sha256','candidate_sha256','initial_binding_sha256']:core.need(source.stock.parent._digest(v[k]),'HASH_HOLD: canonical trusted source digest required')
        core.need(v['context_sha256']==context.root_sha256 and v['checkpoint_sha256']==expected_sha256,'HASH_HOLD: actual new context/checkpoint required')
        core.need(core.arithmetic._quantity(v['model_floor_area'],'m2_floor')==p['model_floor_area']['value'],'BASIS_HOLD: actual common floor required')
        tolerance=deepcopy(time_tolerance_seconds_exact)
        calculation=candidate.calculate_next_event_candidate(context,raw_checkpoint,expected_sha256=expected_sha256,time_tolerance_seconds_exact=tolerance)
        core.need(v['candidate_sha256']==calculation['calculation_sha256']and v['initial_binding_sha256']==data['origin_data']['source_data']['source_snapshot']['manifest']['initial_binding_sha256'],
            'HASH_HOLD: actual complete new-law candidate and original binding required')
        core.need(v['at_elapsed_seconds_exact']==calculation['at']['elapsed_seconds_exact'],'TIME_HOLD: exact candidate time required')
        event=core.source_event(data,calculation)
        core.need(type(v['source_threshold_sequence'])is int and v['source_threshold_sequence']==event['sequence']and v['source_threshold_exact']==event['threshold_exact']and v['source_event_id']==event['source_event_id'],
            'EVENT_HOLD: actual first pending source entity required')
        parents={r['compartment_id']for r in p['stem_root_compartments']if r['kind']=='internode'}
        core.need(v['parent_internode_id']in parents and event['internode_id']not in {r['compartment_id']for r in p['stem_root_compartments']}and event['leaf_id']not in {r['leaf_id']for r in p['leaves']},'PARENT_HOLD: actual pre-point parent and unused new organ IDs required')
        past=core.previous_event_ids(context,data)
        core.need(not past.intersection(event[k]for k in ['source_event_id','internode_event_id','leaf_event_id']),'EVENT_HOLD: source event already present in original history')
        seeds=core.validate_seeds(context,data,calculation,v,event);calls=[]
        def evaluate(program,state,organs,costs):
            resume._fence(context,data);core.need(_pins()==pins,'CODE_HOLD: current point dependencies required')
            snapshot=resume._canonical({'program':program,'state':state,'organs':organs,'costs':costs});calls.append(1)
            out=core.stage.evaluate(program,state,organs,costs,data['profiles'])
            core.need(resume._canonical({'program':program,'state':state,'organs':organs,'costs':costs})==snapshot,'INPUT_HOLD: stage mutated material state inputs')
            resume._fence(context,data);core.need(_pins()==pins,'CODE_HOLD: current point dependencies required');return out
        jump=core.apply(context,data,calculation,v,event,seeds,evaluate);preview=books.calculate(context,data,calculation,jump)
        program=jump['program'];size=106+3*len(program['leaves'])+len(program['stem_root_compartments'])
        layout={**deepcopy(data['seed']['state_layout']),'original':source.stock.short._layout(program),'original_prefix_length':size,
            'internode_ids':[r['compartment_id']for r in jump['organs']['internodes']]}
        out={'model_version':VERSION,'policy':POLICY,'source_code_sha256':pins,'scope':'software_research_only','time_kind':'synthetic_model_clock_not_observation','G0_G4':'not_assessed',
            'context_sha256':context.root_sha256,'checkpoint_sha256':expected_sha256,'input_sha256':sha256(raw).hexdigest(),'inputs':v,'before_candidate_sha256':calculation['calculation_sha256'],'before_candidate':calculation,
            'source_event':event,'at':deepcopy(calculation['at']),'after_program':program,'after_state':jump['state'],'after_rates':deepcopy(jump['evaluation']['rates']),
            'after_stage':jump['evaluation'],'after_derived':deepcopy(jump['evaluation']['derived']),'after_organs':jump['organs'],'after_costs':jump['costs'],'after_state_layout':layout,
            'seed_compatibility':seeds['compatibility'],'new_birth_baselines':jump['new_birth_baselines'],'flow_components':jump['components'],'growth_costs':jump['growth_costs'],'leaf_receipts':jump['leaf_receipts'],**preview,
            'point_order':['internode','leaf']if v['leaf']is not None else['internode'],'point_stage_RHS_evaluations':len(calls),
            'current_validation_RHS_evaluations':calculation['current_validation_RHS_evaluations'],'candidate_new_RHS_evaluations':calculation['new_RHS_evaluations'],
            'birth_stage_version':core.stage.VERSION,'redistribution_authorized':calculation['redistribution_authorized']and v['rights']['redistribute'],
            'elapsed_seconds_advanced':Q(Fraction(0),'s'),'past_intervals_reintegrated':0,'schedule_adoption':'not_performed','integrator_checkpoint':None,
            'initialization_scope':'only_declared_new_leaf_F0_no_existing_reinitialization_no_stem_length_fitting','global_prefix_adoption':'not_performed',
            'effects':'readonly_stateless_same_before_source_and_inputs_repeat_identical_result'}
        out['calculation_sha256']=resume._hash(out);resume._canonical(out,MAX_BYTES)
        resume._fence(context,data);core.need(_pins()==pins,'CODE_HOLD: original point dependencies required before return')
        core.need(resume._canonical(inputs,MAX_INPUT_BYTES)==raw and time_tolerance_seconds_exact==tolerance,'INPUT_HOLD: caller material/tolerance input changed during calculation')
        return deepcopy(out)
    except SupplyPointHold:raise
    except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:raise SupplyPointHold(str(error))from None
