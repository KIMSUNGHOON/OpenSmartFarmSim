"""Store original individual leaf carbon/age/area checkpoints and publish the root last."""
from hashlib import sha256
from pathlib import Path

from . import crop_leaf_carbon_stock_continuation as continuation
from . import crop_leaf_carbon_stock_artifact_reader as reader
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical


def produce_leaf_carbon_stock_artifact(directory, access, *, inputs_raw, **profiles):
    try:
        inputs = reader._inputs(inputs_raw); pins = reader._pins()
        context = continuation.prepare_context(program=inputs['program'], step_seconds=inputs['step_seconds'],
            step_count=inputs['step_count'], **profiles)
        continuation._context(context)
        notice = (Path(__file__).resolve().parents[2]/reader.NOTICE_PATH).read_bytes()
        sources = {'inputs': inputs_raw, 'request': context._request, 'program': context._program,
            'context': context._manifest, 'seed': context._seed, 'license_notice': notice,
            **{name: profile.raw_bytes for name, profile in profiles.items()}}
        with MorphologyBlobStore(directory, access, write=True) as store:
            descriptors = {name: {'sha256': store.put(raw, maximum=reader.MAX), 'bytes': len(raw)} for name, raw in sources.items()}
            cp = continuation.start(context); samples = []; previous = None
            for i in range(inputs['step_count']+1):
                _need(reader._pins() == pins, 'CODE_HOLD: source changed during calculation')
                if i:
                    chunk = continuation.advance_chunk(context, cp, 1)
                    _need(chunk['status'] in ('yielded', 'completed') and chunk['checkpoint'] is not None,
                        'CALCULATION_HOLD: '+str(chunk['hold']))
                    cp = chunk['checkpoint']
                raw = continuation.checkpoint_bytes(context, cp); sample = cp.value['last_confirmed']
                digest = store.put(raw, maximum=reader.CHECKPOINT_MAX)
                samples.append({'index': i, 'elapsed_seconds_exact': reader._offset(inputs['step_seconds'], i),
                    'checkpoint_sha256': digest, 'checkpoint_bytes': len(raw), 'sample_sha256': reader._digest(sample),
                    'state_sha256': reader._digest(sample['state']), 'previous_checkpoint_sha256': previous})
                previous = digest
            m = {**reader.ROOT_CONSTANTS, 'input_id': inputs['input_id'], 'source_rights': inputs['rights'],
                'time_origin_utc': inputs['time_origin_utc'], 'sources': descriptors, 'code_sha256': pins,
                'context_sha256': context.root_sha256, 'initial_state_sha256': samples[0]['state_sha256'],
                'terminal_state_sha256': samples[-1]['state_sha256'], 'samples': samples}
            _, _, _, _, _, raws = reader._graph(store, m)
            _need(all(store.get(sha256(raw).hexdigest(), maximum=reader.MAX) == raw for raw in sources.values()),
                'HASH_HOLD: original evidence changed before completion')
            continuation._context(context); reader._fence(store, m, raws)
            return store.put(_canonical(m), maximum=reader.MAX)
    except (MorphologyArtifactHold, continuation.ContinuationRejected, OSError, ValueError, TypeError,
            KeyError, AttributeError, OverflowError, RecursionError) as exc:
        if isinstance(exc, (MorphologyArtifactHold, continuation.ContinuationRejected)):
            raise reader.LeafCarbonStockArtifactHold(str(exc)) from None
        raise reader.LeafCarbonStockArtifactHold('INPUT_HOLD: invalid growing geometry artifact input') from None
