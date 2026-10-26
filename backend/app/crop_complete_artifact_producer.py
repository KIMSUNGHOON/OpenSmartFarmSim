"""Capture actual complete bindings and publish their validated immutable root last."""
from hashlib import sha256
from pathlib import Path

from . import crop_funded_complete_prefix as model
from . import crop_complete_artifact_reader as reader
from .crop_morphology_artifact_io import MorphologyBlobStore,MAX_BLOB_BYTES,_need
from .crop_morphology_artifact_reader import _canonical

CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def produce_complete_crop_artifact(directory,access,*,segments):
    try:
        pins=reader._pins();_need(pins['backend/app/crop_complete_artifact_producer.py']==CODE_SHA256,'CODE_HOLD: original loaded producer required')
        packet=model.bind_complete_trajectory(segments)
        _need(packet['basis']['code_sha256']=={k:pins[k]for k in reader.MODEL_SOURCE_PATHS},'CODE_HOLD: actual model dependency set required')
        contexts=[s['context']for s in segments];first=contexts[0];sources={}
        for source_directory in (first._leaf_directory,first._stem_directory):
            with MorphologyBlobStore(source_directory,access)as source:
                for path in source_directory.iterdir():
                    raw=source.get(path.name,maximum=MAX_BLOB_BYTES);sources[path.name]=raw
        with MorphologyBlobStore(directory,access,write=True)as store:
            def put(raw,maximum=reader.MAX):return {'sha256':store.put(raw,maximum=maximum),'bytes':len(raw)}
            source_descriptors=[put(raw,MAX_BLOB_BYTES)for _,raw in sorted(sources.items())]
            context_descriptors=[put(model.crop.context_bytes(context))for context in contexts]
            packet_descriptor=put(_canonical(packet));geometry=[]
            for frame in packet['frames']:
                receipts=[]
                for node in frame['shoot']['internodes']:
                    request=reader.point_request(packet,frame,node)
                    response=model.binding.point.calculate_internode_length_point(inputs=request)
                    _need(response['input_sha256']==node['point_input_sha256']and response['length']==node['length'],'GEOMETRY_HOLD: actual point receipt differs from bound frame')
                    receipts.append(put(_canonical({'request':request,'response':response}),reader.POINT_MAX))
                geometry.append(receipts)
            manifest={**reader.FLAGS,'code_sha256':pins,'packet':packet_descriptor,'contexts':context_descriptors,'source_blobs':source_descriptors,
                'geometry_receipts':geometry,'frames':[reader.frame_descriptor(i,f)for i,f in enumerate(packet['frames'])]}
            raw=_canonical(manifest);_need(len(raw)<=reader.MAX,'CAPACITY_HOLD: bounded complete artifact root required');digest=sha256(raw).hexdigest()
            # Validation uses the same immutable bytes before a completed root is published.
            def unpublished_get(requested,*,maximum):
                return raw if requested==digest else original_get(requested,maximum=maximum)
            original_get=store.get;store.get=unpublished_get
            try:_,_,raws=reader._load(store,digest)
            finally:store.get=original_get
            raws.pop(digest,None);reader._fence(store,manifest,raws)
            for context in contexts:model.crop._context(context)
            _need(reader._pins()==pins,'CODE_HOLD: dependencies changed during complete production')
            result=store.put(raw,maximum=reader.MAX);raws[result]=raw;reader._fence(store,manifest,raws)
            return result
    except (OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError)as error:
        raise reader.CompleteCropArtifactHold(str(error))from None
