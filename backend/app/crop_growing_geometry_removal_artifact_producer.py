"""Publish pre-event, event and post-event immutable blobs; root last."""
from hashlib import sha256
from pathlib import Path

from . import crop_growing_geometry_continuation as parent
from . import crop_growing_geometry_post_removal_context as post
from . import crop_growing_geometry_removal_next_interval as engine
from . import crop_growing_geometry_removal_artifact_reader as reader
from .crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore,_need
from .crop_morphology_artifact_reader import _canonical


def produce_removal_artifact(directory,access,*,inputs_raw,**profiles):
    try:
        inputs=reader._inputs(inputs_raw);pins=reader._pins()
        _need({name:p.sha256 for name,p in profiles.items()}==reader.base.PROFILE_SHA,'PROFILE_HOLD: four pinned profiles required')
        context=parent.prepare_context(program=inputs['program'],step_seconds=inputs['step_seconds'],step_count=inputs['step_count'],**profiles)
        cp=parent.start(context);sources={'inputs':inputs_raw,'request':context._request,'program':context._program,
            'context':context._manifest,'seed':context._seed,
            'license_notice':(Path(__file__).resolve().parents[2]/reader.base.NOTICE_PATH).read_bytes(),
            'point_inputs':_canonical(inputs['point_inputs']),**{name:p.raw_bytes for name,p in profiles.items()}}
        with MorphologyBlobStore(directory,access,write=True)as store:
            descriptors={name:{'sha256':store.put(raw,maximum=reader.MAX),'bytes':len(raw)}for name,raw in sources.items()}
            samples=[];previous=None
            def save(raw,sample,index,phase):
                nonlocal previous
                _need(reader._pins()==pins,'CODE_HOLD: source changed during removal calculation')
                digest=store.put(raw,maximum=reader.CHECKPOINT_MAX);samples.append({'index':len(samples),'global_step_index':index,'phase':phase,
                    'elapsed_seconds_exact':reader.base._offset(inputs['step_seconds'],index),'checkpoint_sha256':digest,'checkpoint_bytes':len(raw),
                    'sample_sha256':reader._digest(sample),'state_sha256':reader._digest(sample['state']),'previous_checkpoint_sha256':previous});previous=digest
            for i in range(inputs['event_step_index']+1):
                if i:
                    chunk=parent.advance_chunk(context,cp,1)
                    _need(chunk['status']in('yielded','completed')and chunk['checkpoint']is not None,'CALCULATION_HOLD: '+str(chunk['hold']))
                    cp=chunk['checkpoint']
                save(parent.checkpoint_bytes(context,cp),cp.value['last_confirmed'],i,'before_removal')
            current=post.prepare_context(parent_context=context,raw_parent_checkpoint=cp._raw,expected_parent_sha256=cp.sha256,inputs=inputs['point_inputs'])
            post_snapshot=post.snapshot(current)
            extra={'point_result':current._point,'post_context':current._manifest,'post_program':current._program,'post_seed':current._seed,
                'post_snapshot':post.checkpoint_bytes(current,post_snapshot)}
            sources.update(extra)
            descriptors.update({name:{'sha256':store.put(raw,maximum=reader.MAX),'bytes':len(raw)}for name,raw in extra.items()})
            later=engine.start(current);save(engine.checkpoint_bytes(current,later),later.value['last_confirmed'],inputs['event_step_index'],'after_removal_before_next_step')
            for i in range(inputs['event_step_index']+1,inputs['step_count']+1):
                chunk=engine.advance_chunk(current,later,1)
                _need(chunk['status']in('yielded','completed')and chunk['checkpoint']is not None,'CALCULATION_HOLD: '+str(chunk['hold']))
                later=chunk['checkpoint'];save(engine.checkpoint_bytes(current,later),later.value['last_confirmed'],i,'post_removal_interval')
            manifest={**reader.ROOT_CONSTANTS,'input_id':inputs['input_id'],'source_rights':inputs['rights'],'time_origin_utc':inputs['time_origin_utc'],
                'sources':descriptors,'code_sha256':pins,'parent_context_sha256':context.root_sha256,'post_context_sha256':current.root_sha256,
                'point_calculation_sha256':current.point_result['calculation_sha256'],'event_step_index':inputs['event_step_index'],
                'initial_state_sha256':samples[0]['state_sha256'],'terminal_state_sha256':samples[-1]['state_sha256'],'samples':samples}
            *_,raws=reader._graph(store,manifest)
            _need(all(store.get(sha256(raw).hexdigest(),maximum=reader.MAX)==raw for raw in sources.values()),'HASH_HOLD: original source changed before completion')
            parent._context(context);post._context(current);reader._fence(store,manifest,raws)
            return store.put(_canonical(manifest),maximum=reader.MAX)
    except(MorphologyArtifactHold,OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError)as error:
        if isinstance(error,MorphologyArtifactHold):raise reader.RemovalArtifactHold(str(error))from None
        if isinstance(error,(parent.ContinuationRejected,post.PostRemovalContextHold,engine.RemovalIntervalHold)):
            raise reader.RemovalArtifactHold('CALCULATION_HOLD: '+str(error))from None
        raise reader.RemovalArtifactHold('INPUT_HOLD: invalid removal artifact request')from None
