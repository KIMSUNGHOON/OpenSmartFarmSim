"""Store actual declared leaf calculations beside an unchanged copied stem artifact."""
from pathlib import Path
from hashlib import sha256

from . import crop_leaf_inventory as inventory
from .crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore,_need
from .crop_leaf_artifact_reader import (MAX,SOURCE_PATHS,ROOT_CONSTANTS,_canonical,_parse,_program,_digest,
    _frame_payload,_exact,read_rational_morphology_frame,read_rational_morphology_manifest)
from .crop_morphology_artifact_reader import PROGRAM_MAX,RESULT_MAX,ROOT_MAX,_utc


def _code_pins():
    root=Path(__file__).resolve().parents[2]
    try:return {name:sha256((root/name).read_bytes()).hexdigest() for name in SOURCE_PATHS}
    except OSError:raise MorphologyArtifactHold('CODE_HOLD: leaf source unavailable') from None


def _seconds(at,origin):
    delta=_utc(at)-_utc(origin);return {'numerator':str(delta.days*86400+delta.seconds),'denominator':'1','unit':'s'}


def _forcing(segments,origin,start,end):
    return [{'start_elapsed_seconds_exact':_seconds(max(s['start_utc'],start),origin),
        'end_elapsed_seconds_exact':_seconds(min(s['end_utc'],end),origin),'air_temperature':s['air_temperature']}
        for s in segments if s['end_utc']>start and s['start_utc']<end]


def produce_leaf_area_artifact(directory,access,*,stem_directory,program_raw):
    _need(Path(directory).resolve()!=Path(stem_directory).resolve(),'STORAGE_HOLD: separate leaf artifact directory required')
    p=_parse(program_raw,MAX);meta=_program(p);pins=_code_pins();descriptors=[]
    old=read_rational_morphology_manifest(stem_directory,access,p['stem']['artifact_sha256'])
    _need(old['program_sha256']==p['stem']['program_sha256'],'HASH_HOLD: original stem program required')
    with MorphologyBlobStore(stem_directory,access) as original,MorphologyBlobStore(directory,access,write=True) as store:
        stem_raw=original.get(old['program_sha256'],maximum=PROGRAM_MAX);stem_program=_parse(stem_raw,PROGRAM_MAX)
        timeline=stem_program['initial_state']['timeline_state'];origin=timeline['started_at'];previous=timeline['at']
        _need(meta['time_origin_utc']==origin and meta['initial_at_elapsed_seconds_exact']==_seconds(previous,origin),
              'TIME_HOLD: leaf initialization must match original stem checkpoint')
        blobs=[(p['stem']['artifact_sha256'],ROOT_MAX),(old['program_sha256'],PROGRAM_MAX),
               *((d['result_sha256'],RESULT_MAX) for d in old['samples'])]
        for digest,maximum in blobs:_need(store.put(original.get(digest,maximum=maximum),maximum=maximum)==digest,'HASH_HOLD: stem copy mismatch')
        program_sha=store.put(program_raw,maximum=MAX)
        try:state=inventory.initialize_leaf_inventory(inputs=p['initialization'])['state']
        except inventory.LeafInventoryHold as exc:raise MorphologyArtifactHold(str(exc)) from None
        initial_state_sha=_digest(state)
        for index,d in enumerate(old['samples']):
            _need(_code_pins()==pins,'CODE_HOLD: leaf source changed during calculation');before=_digest(state)
            stem=read_rational_morphology_frame(directory,access,p['stem']['artifact_sha256'],index=index)
            _need(all(item['attachment_internode_id'] in {n['internode_id'] for n in stem['internodes']}
                      for item in state['leaves']),'STATE_HOLD: leaf attachment absent from original stored stem')
            try:
                result=inventory.advance_leaf_inventory(inputs={'input_id':_digest({'program_id':p['program_id'],'at':d['at']}),
                    'state':state,'segments':_forcing(stem_program['segments'],origin,previous,d['at'])})
            except inventory.LeafInventoryHold as exc:raise MorphologyArtifactHold(str(exc)) from None
            raw=_canonical(result);result_sha=store.put(raw,maximum=MAX);state=result['state']
            payload=_canonical(_frame_payload(result,stem,index,p));payload_sha=store.put(payload,maximum=MAX)
            descriptors.append({'index':index,'at':d['at'],'result_sha256':result_sha,'result_bytes':len(raw),
                'payload_sha256':payload_sha,'payload_bytes':len(payload),'input_state_sha256':before,
                'state_sha256':_digest(state),'input_sha256':result['input_sha256'],'stem_result_sha256':d['result_sha256']})
            previous=d['at']
        _need(_code_pins()==pins,'CODE_HOLD: leaf source changed before completion')
        root={**ROOT_CONSTANTS,**meta,'program_sha256':program_sha,'program_bytes':len(program_raw),'program_rights':p['rights'],
            'stem_artifact_sha256':p['stem']['artifact_sha256'],'stem_program_sha256':p['stem']['program_sha256'],
            'code_sha256':pins,'initial_state_sha256':initial_state_sha,'terminal_state_sha256':_digest(state),'samples':descriptors}
        return store.put(_canonical(root),maximum=MAX)
