"""Persist genuine repeated Context/CP bytes, then publish a validated root last."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from . import crop_supply_morphology_repeat_context as owner
from . import crop_supply_morphology_repeat_resume as model
from . import crop_supply_morphology_artifact_reader as reader
from .crop_morphology_artifact_io import MorphologyBlobStore, _need

CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


def produce_supply_morphology_artifact(directory, access, *, segments, terminal):
    try:
        _need(type(segments) in (list,tuple) and 1 <= len(segments) <= 512,
              'CAPACITY_HOLD: nonempty bounded actual segment list required')
        pins = reader._pins()
        _need(pins['backend/app/crop_supply_morphology_artifact_producer.py'] == CODE_SHA256
            and {name:pins[name] for name in reader.MODEL_SOURCE_PATHS} == model._pins(),
            'CODE_HOLD: original loaded producer/model sources required')
        saved, contexts, checkpoint_objects = [], [], []
        for segment in segments:
            reader._closed(segment, {'context','checkpoints'})
            context = segment['context']
            data = model._context(context)
            _need(type(segment['checkpoints']) in (list,tuple) and 1 <= len(segment['checkpoints']) <= 512,
                  'CAPACITY_HOLD: complete actual checkpoint list required')
            row = {'context':context._raw, 'checkpoints':[]}
            for checkpoint in segment['checkpoints']:
                raw = model._raw(context, checkpoint)
                model._shape(context, data, checkpoint.value)
                row['checkpoints'].append(raw)
                checkpoint_objects.append((context, checkpoint, raw))
            saved.append(row)
            contexts.append((context, data))
        first = contexts[0][0]
        mixed = first._origin._origin._origin._source._source
        binding = model.source.stock._source(mixed)
        selection = json.loads(mixed._selection)
        root = first._root
        profiles = model.source.stock.parent._profiles(root)
        root_inputs = {name:getattr(root, '_'+name) for name in ('request','program','seed','manifest')}
        root_inputs.update(origin_context=first._origin._raw,
            license_notice=(Path(__file__).resolve().parents[2]/reader.carbon.NOTICE_PATH).read_bytes(),
            **{name:profile.raw_bytes for name,profile in profiles.items()})
        all_sources = {}
        for source_directory in mixed._directories[:2]:
            with MorphologyBlobStore(source_directory, mixed._directories[2]) as source:
                source._usage()
                for path in source_directory.iterdir():
                    all_sources[path.name] = source.get(path.name, maximum=16*1024**2)
        with MorphologyBlobStore(directory, access, write=True) as store:
            def put(raw, maximum=reader.MAX):
                return {'sha256':store.put(raw, maximum=maximum), 'bytes':len(raw)}
            manifest = {**reader.FLAGS, 'code_sha256':pins,
                'source_blobs':[put(raw,16*1024**2) for _,raw in sorted(all_sources.items())],
                'root_inputs':{name:put(raw) for name,raw in root_inputs.items()},
                'selection':selection, 'initial_binding':put(reader._canonical(binding)),
                'source_rights':deepcopy(binding['source_rights']),
                'redistribution_authorized':all(v['redistribute'] for v in binding['source_rights'].values()) and contexts[-1][1]['seed']['redistribution_authorized'],
                'shoot_base_temperature':contexts[0][1]['shoot_base_temperature'],
                'segments':[{'context':put(row['context']), 'checkpoints':[put(raw,reader.CP_MAX) for raw in row['checkpoints']]} for row in saved],
                'frames':[], 'terminal':deepcopy(terminal)}
            frames, _, _ = reader._frame_graph(store, manifest, {})
            manifest['frames'] = [reader.frame_descriptor(frame) for frame in frames]
            raw = reader._canonical(manifest)
            _need(len(raw) <= reader.MAX, 'CAPACITY_HOLD: bounded artifact root required')
            digest = sha256(raw).hexdigest()
            _, _, raws = reader._load(store, digest, unpublished_raw=raw)
            for context, data in contexts:
                model._fence(context, data)
            for context, checkpoint, original in checkpoint_objects:
                _need(model._raw(context,checkpoint) == original, 'CHECKPOINT_HOLD: caller checkpoint changed during production')
            for segment in segments:
                reader._closed(segment, {'context','checkpoints'})
            _need(terminal == manifest['terminal'] and len(segments) == len(saved)
                and all(segment['context'] is context and list(segment['checkpoints']) == [cp for ctx,cp,_ in checkpoint_objects if ctx is context]
                        for segment,(context,_) in zip(segments,contexts,strict=True)),
                'INPUT_HOLD: original caller segments and terminal required')
            reader._fence(store, manifest, raws)
            result = store.put(raw, maximum=reader.MAX)
            reader._read(store, result, raws)
            reader._fence(store, manifest, raws)
            return result
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise reader.SupplyMorphologyArtifactHold(str(error)) from None
