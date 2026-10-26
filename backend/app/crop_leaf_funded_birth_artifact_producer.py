"""Store original root/funded checkpoints and publish the completed graph last."""
from hashlib import sha256
from pathlib import Path

from . import crop_leaf_funded_birth_continuation as model
from . import crop_leaf_funded_birth_artifact_reader as reader
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical


def _adopt(root, context, raw, digest, inputs):
    if context is None:
        cp = model.parent.restore_checkpoint(root, raw, expected_sha256=digest)
        p, seed, manifest = model.parent._context(root)
        anchors = seed['evaluation']['curve_residuals']; bases = model._root_bases(p, seed); history = []
        context_sha = root.root_sha256
    else:
        cp = model.restore_checkpoint(context, raw, expected_sha256=digest)
        p, seed, manifest = model._context(context)
        anchors, bases, history = seed['anchors'], seed['birth_bases'], context.point_history
        context_sha = context.root_sha256
    seen = {event['event_id'] for item in history for event in item['inputs']['events']}
    _need(all(event['event_id'] not in seen for event in inputs['events']), 'EVENT_HOLD: funded event repeated')
    point = model.point._apply_current(program=p, anchors=anchors, manifest=manifest, saved=cp.value,
        context_sha256=context_sha, checkpoint_sha256=digest, profiles=model.parent._profiles(root), inputs=inputs)
    return model._capture(root, point, anchors, bases, history), point


def produce_funded_leaf_artifact(directory, access, *, inputs_raw, **profiles):
    try:
        inputs = reader._inputs(inputs_raw); pins = reader._pins()
        root = model.parent.prepare_context(program=inputs['program'], step_seconds=inputs['step_seconds'],
                                             step_count=inputs['step_count'], **profiles)
        notice = (Path(__file__).resolve().parents[2]/reader.stock.NOTICE_PATH).read_bytes()
        sources = {'inputs': inputs_raw, 'request': root._request, 'program': root._program,
                   'context': root._manifest, 'seed': root._seed, 'license_notice': notice,
                   **{name: profile.raw_bytes for name, profile in profiles.items()}}
        with MorphologyBlobStore(directory, access, write=True) as store:
            descriptors = {name: {'sha256': store.put(raw, maximum=reader.MAX), 'bytes': len(raw)}
                           for name, raw in sources.items()}
            samples = []; events = []; context = None; cp = model.parent.start(root); event_index = 0

            def save_checkpoint():
                _need(reader._pins() == pins, 'CODE_HOLD: source changed during funded calculation')
                engine = model if context is not None else model.parent
                raw = engine.checkpoint_bytes(context if context is not None else root, cp)
                value = cp.value; sample = value['last_confirmed']; index = len(samples)
                digest = store.put(raw, maximum=reader.CHECKPOINT_MAX)
                samples.append({'index': index, 'step_index': value['step_index'],
                    'elapsed_seconds_exact': reader.stock._offset(inputs['step_seconds'], value['step_index']),
                    'phase': value['phase'] if context is not None else 'root_interval', 'event_sequence': len(events),
                    'context_sha256': context.root_sha256 if context is not None else root.root_sha256,
                    'checkpoint_sha256': digest, 'checkpoint_bytes': len(raw), 'sample_sha256': reader._digest(sample),
                    'state_sha256': reader._digest(sample['state']),
                    'previous_checkpoint_sha256': samples[-1]['checkpoint_sha256'] if samples else None})
                return raw, digest

            for step in range(inputs['step_count']+1):
                if step:
                    engine = model if context is not None else model.parent
                    out = engine.advance_chunk(context if context is not None else root, cp, 1)
                    _need(out['status'] in ('yielded', 'completed') and out['checkpoint'] is not None,
                          'CALCULATION_HOLD: '+str(out['hold']))
                    cp = out['checkpoint']
                raw, digest = save_checkpoint()
                while event_index < len(inputs['births']) and inputs['births'][event_index]['step_index'] == step:
                    item = inputs['births'][event_index]
                    context, point = _adopt(root, context, raw, digest, item['point_inputs'])
                    point_raw = _canonical(point); snapshot = model.context_bytes(context)
                    events.append({'event_sequence': event_index+1, 'step_index': step, 'after_frame_index': len(samples),
                        'point': {'sha256': store.put(point_raw, maximum=reader.MAX), 'bytes': len(point_raw)},
                        'context_snapshot': {'sha256': store.put(snapshot, maximum=reader.MAX), 'bytes': len(snapshot)},
                        'context_sha256': context.root_sha256})
                    cp = model.start(context); raw, digest = save_checkpoint(); event_index += 1
            manifest = {**reader.ROOT_CONSTANTS, 'input_id': inputs['input_id'], 'source_rights': inputs['rights'],
                'time_origin_utc': inputs['time_origin_utc'], 'sources': descriptors, 'code_sha256': pins,
                'context_sha256': root.root_sha256, 'initial_state_sha256': samples[0]['state_sha256'],
                'terminal_state_sha256': samples[-1]['state_sha256'], 'events': events, 'samples': samples}
            _, _, _, _, _, _, raws = reader._graph(store, manifest)
            model.parent._context(root); model._context(context); reader._fence(store, manifest, raws)
            raw_root = _canonical(manifest); digest = store.put(raw_root, maximum=reader.MAX)
            raws['root'] = raw_root; reader._fence(store, manifest, raws)
            return digest
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as error:
        if isinstance(error, MorphologyArtifactHold) or isinstance(error, ValueError):
            raise reader.FundedLeafArtifactHold(str(error)) from None
        raise reader.FundedLeafArtifactHold('INPUT_HOLD: invalid funded leaf artifact input') from None
