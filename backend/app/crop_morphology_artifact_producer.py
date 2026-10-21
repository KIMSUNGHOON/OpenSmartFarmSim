"""Publish complete synthetic morphology calculations as immutable private blobs."""
from hashlib import sha256
from pathlib import Path

from . import crop_shoot_inventory as inventory
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import (
    PROGRAM_MAX, RESULT_MAX, ROOT_MAX, ROOT_CONSTANTS, SOURCE_PATHS, _canonical, _parse, _program,
)


def _digest(value):
    return sha256(_canonical(value)).hexdigest()


def _code_pins():
    repo = Path(__file__).resolve().parents[2]
    try:
        return {path: sha256((repo / path).read_bytes()).hexdigest() for path in SOURCE_PATHS}
    except OSError:
        raise MorphologyArtifactHold('CODE_HOLD: source identity unavailable') from None


def _forcing(segments, start, end):
    return [{**s, 'start_utc': max(start, s['start_utc']), 'end_utc': min(end, s['end_utc'])}
            for s in segments if s['end_utc'] > start and s['start_utc'] < end]


def produce_morphology_artifact(directory, access, *, program_raw):
    p = _parse(program_raw, PROGRAM_MAX); _program(p)
    pins = _code_pins(); state = p['initial_state']; descriptors = []
    with MorphologyBlobStore(directory, access, write=True) as store:
        program_sha = store.put(program_raw, maximum=PROGRAM_MAX)
        for index, at in enumerate(p['output_times']):
            _need(_code_pins() == pins, 'CODE_HOLD: source changed during calculation')
            before = _digest(state)
            try:
                result = inventory.advance_shoot_internode_inventory(inputs={
                    'input_id': _digest({'program_id': p['program_id'], 'output_at': at}), 'state': state,
                    'segments': _forcing(p['segments'], state['timeline_state']['at'], at)})
            except inventory.ShootInventoryHold as exc:
                raise MorphologyArtifactHold(str(exc)) from None
            raw = _canonical(result)
            result_sha = store.put(raw, maximum=RESULT_MAX)
            state = result['state']
            descriptors.append({'index': index, 'at': at, 'result_sha256': result_sha, 'result_bytes': len(raw),
                'input_state_sha256': before, 'state_sha256': _digest(state), 'input_sha256': result['input_sha256']})
        _need(_code_pins() == pins, 'CODE_HOLD: source changed during calculation')
        manifest = {**ROOT_CONSTANTS, 'program_sha256': program_sha, 'program_bytes': len(program_raw),
            'initial_state_sha256': _digest(p['initial_state']), 'program_rights': p['rights'],
            'code_sha256': pins, 'samples': descriptors, 'terminal_state_sha256': _digest(state)}
        return store.put(_canonical(manifest), maximum=ROOT_MAX)
