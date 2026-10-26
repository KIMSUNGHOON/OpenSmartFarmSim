"""Project an original stored stem state from its own epoch using funded air."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import fsum, isfinite
from pathlib import Path

from . import crop_leaf_funded_birth_artifact_reader as leaf
from . import crop_rational_morphology_artifact_reader as stem
from . import crop_rational_internode_length as initial
from . import crop_internode_length as point
from . import crop_phytomer_emergence as thresholds
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical

MODEL_VERSION='funded-air-stored-shoot-epoch-projection-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES=2*1024**2


class FundedShootEpochHold(MorphologyArtifactHold):
    pass


def _digest(value):return sha256(_canonical(value)).hexdigest()


def _pins():
    root=Path(__file__).resolve().parents[2]
    paths=dict.fromkeys((*stem.SOURCE_PATHS,*leaf.SOURCE_PATHS,'backend/app/crop_funded_shoot_epochs.py'))
    return {name:sha256((root/name).read_bytes()).hexdigest()for name in paths}


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256,'CODE_HOLD: original shoot epoch projection required')


def _exact(value,unit):
    result={'numerator':str(value.numerator),'denominator':str(value.denominator),'unit':unit}
    (stem._elapsed if unit=='s'else stem._age)(result)
    return result


def _selected(store,directory,access,root,manifest,program,index):
    if index==-1:return program['initial_state'],manifest['initial_state_sha256'],None,None
    stem.read_rational_morphology_frame(directory,access,root,index=index)
    d=manifest['samples'][index];raw=store.get(d['result_sha256'],maximum=stem.RESULT_MAX)
    state=stem._parse(raw,stem.RESULT_MAX)['state']
    _need(_digest(state)==d['state_sha256'],'HASH_HOLD: original selected state required')
    return state,d['state_sha256'],d['result_sha256'],raw


def project_funded_shoot_from_stored_state(leaf_directory,stem_directory,access,*,leaf_root_sha256,stem_root_sha256,stem_start_index):
    try:
        _fence();_need(type(stem_start_index)is int and stem_start_index>=-1,'INDEX_HOLD: explicit stored initial-state index required')
        pins=_pins();lm=leaf.read_funded_leaf_manifest(leaf_directory,access,leaf_root_sha256)
        sm=stem.read_rational_morphology_manifest(stem_directory,access,stem_root_sha256)
        _need(sm['code_sha256']=={p:pins[p]for p in stem.SOURCE_PATHS},'CODE_HOLD: original stem source required')
        _need(stem_start_index<len(sm['samples']),'INDEX_HOLD: selected source frame absent')
        _need(all(sm['program_rights'][k]is True and lm['source_rights'][k]is True for k in ('use','display')),'RIGHTS_HOLD: original source grants required')
        with MorphologyBlobStore(stem_directory,access)as store:
            program_raw=store.get(sm['program_sha256'],maximum=stem.PROGRAM_MAX);program=stem._parse(program_raw,stem.PROGRAM_MAX)
            state,state_sha,result_sha,selected_raw=_selected(store,stem_directory,access,stem_root_sha256,sm,program,stem_start_index)
            stem._state(state);t=state['timeline_state'];origin,current=stem._utc(t['started_at']),stem._utc(t['at'])
            _need(t['at']==lm['time_origin_utc'] and origin<=current,'TIME_HOLD: simulation must begin at the original selected source time')
            delta=current-origin;offset=Fraction(delta.days*86400+delta.seconds);base=Fraction.from_float(float(t['base_temperature']['value']))
            nodes=state['internodes'];_need(len(nodes)>=1,'SCOPE_HOLD: nonempty stored stem required')
            normalized=[initial.normalize_rational_internode_length_state(state=n['length_state'])for n in nodes]
            node_ages=[stem._fraction(n['clock_state']['age_exact'])for n in normalized];node_hashes=[_digest(n['length_state'])for n in nodes]
            phase={**{k:t[k]for k in ('origin','age_basis','shoot_id','development_origin_id','schedule_id','next_threshold_exact','phyllochron_exact','next_sequence')},'at_age_exact':t['age_exact']}
            frames=[];brackets=[];frame_bytes=2;previous_seconds=None;previous_integral=None;previous_ages=node_ages[:]
            for i in range(len(lm['samples'])):
                source=leaf.read_funded_leaf_frame(leaf_directory,access,leaf_root_sha256,index=i)
                seconds=stem._fraction(source['at']['elapsed_seconds_exact']);row=source['integrated_transfers']['indoor_air_temperature_time'];integral=row['value']
                _need(type(integral)is float and isfinite(integral)and row['unit']=='degC_s','UNIT_HOLD: original finite air integral required')
                if i==0:_need(seconds==0 and integral==0.,'TIME_HOLD: original zero simulation prefix required')
                if seconds==previous_seconds:_need(integral==previous_integral,'TIME_HOLD: funding point cannot advance the air clock')
                change=(Fraction.from_float(integral)-base*seconds)/86400;shoot_age=_exact(stem._fraction(t['age_exact'])+change,'degC_day')
                listed=thresholds.advance_phytomer_emergence(inputs={'input_id':_digest({'model_version':MODEL_VERSION,'source_state_sha256':state_sha,'frame_index':i}),
                    'state':phase,'end_age_exact':shoot_age});phase=listed['checkpoint']
                if listed['events']:
                    _need(frames and seconds>previous_seconds,'TIME_HOLD: threshold candidate needs a forward source interval')
                    for event in listed['events']:
                        brackets.append({**event,'left_frame_index':i-1,'right_frame_index':i,'start_at':deepcopy(frames[-1]['at']),'end_at':deepcopy(source['at']),
                            'left_checkpoint_sha256':frames[-1]['checkpoint_sha256'],'right_checkpoint_sha256':source['checkpoint_sha256'],
                            'enumeration_input_sha256':listed['input_sha256'],'time_status':'within_step_time_unresolved'})
                    _need(len(brackets)<=512 and len(nodes)+len(brackets)<=512,'CAPACITY_HOLD: bounded source-node/candidate inventory required')
                projected=[]
                for j,(node,a0)in enumerate(zip(nodes,node_ages,strict=True)):
                    original=node['length_state'];age=_exact(a0+change,'degC_day');_need(a0+change>=previous_ages[j],'AGE_HOLD: reversing sampled stem age unsupported')
                    receipt=point.calculate_internode_length_point(inputs={'input_id':_digest({'model_version':MODEL_VERSION,'source_state_sha256':state_sha,'internode_id':original['clock_state']['internode_id']}),
                        'origin':'synthetic','thermal_age_basis':'since_internode_emergence','age_exact':age,'curve':original['curve']})
                    _need(receipt['curve_sha256']==original['curve_sha256'],'HASH_HOLD: original source curve required')
                    if i==0:_need(receipt['length']==original['length'],'STATE_HOLD: selected source initial length required')
                    projected.append({'sequence':node['sequence'],'internode_id':original['clock_state']['internode_id'],
                        'emerged_development_seconds_exact':deepcopy(original['clock_state']['emerged_elapsed_seconds_exact']),'age_exact':age,
                        'curve_sha256':original['curve_sha256'],'source_state_sha256':node_hashes[j],'point_input_sha256':receipt['input_sha256'],'length':receipt['length']})
                    previous_ages[j]=a0+change
                total=fsum(n['length']['value']for n in projected);_need(isfinite(total)and total>0,'NUMERIC_HOLD: finite source-axis sum required')
                frames.append({**{k:source[k]for k in ('index','step_index','phase','event_sequence','checkpoint_sha256','at')},
                    'development_elapsed_seconds_exact':_exact(offset+seconds,'s'),'air_temperature_integral':deepcopy(row),
                    'shoot_age_exact':shoot_age,'internodes':projected,'tracked_source_axis_length':{'value':total,'unit':'m'}})
                frame_bytes+=len(_canonical(frames[-1]))+1;_need(frame_bytes<=MAX_BYTES,'CAPACITY_HOLD: bounded epoch trajectory required')
                previous_seconds,previous_integral=seconds,integral
            result={'model_version':MODEL_VERSION,'scope':'software_research_only','G0_G4':'not_assessed','claim_scope':'stored_source_history_projection_and_endpoint_threshold_brackets_only',
                'code_sha256':CODE_SHA256,'source_code_sha256':pins,'leaf_artifact_sha256':leaf_root_sha256,'stem_artifact_sha256':stem_root_sha256,
                'stem_program_sha256':sm['program_sha256'],'stem_start_index':stem_start_index,'stem_source_state_sha256':state_sha,'stem_source_result_sha256':result_sha,
                'stem_source_state':deepcopy(state),'source_rights':{'leaf':lm['source_rights'],'stem':sm['program_rights']},
                'development_origin_utc':t['started_at'],'simulation_origin_utc':t['at'],'simulation_start_development_elapsed_seconds_exact':_exact(offset,'s'),
                'after_start_air_scope':'original_stored_funded_RK4_integral','historical_forcing_scope':'selected_source_state_not_reintegrated',
                'point_model_version':point.POINT_VERSION,'threshold_model_version':thresholds.MODEL_VERSION,'threshold_enumeration_checkpoint':phase,
                'new_internodes':'not_created','leaf_attachment':'not_bound','frames':frames,'event_brackets':brackets}
            _need(len(_canonical(result))<=MAX_BYTES,'CAPACITY_HOLD: bounded epoch result required')
            _need(store.get(sm['program_sha256'],maximum=stem.PROGRAM_MAX)==program_raw,'HASH_HOLD: original stem program changed')
            if result_sha is not None:_need(store.get(result_sha,maximum=stem.RESULT_MAX)==selected_raw,'HASH_HOLD: selected source result changed')
        _need(leaf.read_funded_leaf_manifest(leaf_directory,access,leaf_root_sha256)==lm and stem.read_rational_morphology_manifest(stem_directory,access,stem_root_sha256)==sm,
            'HASH_HOLD: original source changed before return')
        _need(_pins()==pins,'CODE_HOLD: original calculation sources changed');_fence()
        return deepcopy(result)
    except (OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError)as error:
        raise FundedShootEpochHold(str(error))from None
