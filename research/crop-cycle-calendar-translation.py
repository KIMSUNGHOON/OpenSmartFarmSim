"""Create a separately identified UTC calendar version of synthetic input pages."""
from datetime import timedelta
from hashlib import sha256
from pathlib import Path

from app import crop_cycle_input_stream as inputs

VERSION = 'crop-cycle-calendar-translation-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


def _translate(kind, value, offset):
    def stamp(raw):
        return inputs.physical._stamp(inputs.physical._utc(raw)+offset)
    if kind in ('anchors', 'outputs'):
        return stamp(value)
    keys = ('start', 'end') if kind == 'segments' else ('at',)
    return {**value, **{key: stamp(value[key]) for key in keys}}


def translate_packet(source, source_root_sha256, target, *, offset_days, program_id, **profiles):
    if type(offset_days) is not int or not -366 <= offset_days <= 366 or offset_days == 0:
        raise ValueError('a nonzero integer UTC day offset within one year is required')
    if type(program_id) is not str or not program_id.strip() or len(program_id) > 256:
        raise ValueError('a distinct bounded program ID is required')
    offset = timedelta(days=offset_days)
    with inputs.open_input_packet(source, source_root_sha256, **profiles) as old:
        root = old.manifest
        if program_id == root['program_id']:
            raise ValueError('calendar version needs a distinct program ID')
        counts = {kind: root['streams'][kind]['count'] for kind in inputs.KINDS}
        def records(kind):
            for index in range(counts[kind]):
                yield _translate(kind, old.record(kind, index), offset)
        streams = {kind: records(kind) for kind in inputs.KINDS}
        packet = inputs.write_input_packet(target, initial_state=root['initial_state'],
            solver=root['solver'], program_id=program_id, **streams, **profiles)
        with inputs.open_input_packet(target, packet['root_sha256'], **profiles) as new:
            newer = new.manifest
            for key in ('initial_state', 'solver', 'profile_sha256', 'normalization_sha256', 'python_version'):
                if newer[key] != root[key]:
                    raise ValueError('calendar version changed a non-calendar input')
            if any(new.plan[key] != old.plan[key] for key in ('counts', 'boundaries', 'planned_steps')):
                raise ValueError('calendar version changed the calculation grid')
            audited = {}
            for kind in inputs.KINDS:
                restored = inputs._hash([])
                for index in range(counts[kind]):
                    value = _translate(kind, new.record(kind, index), -offset)
                    if inputs._canonical(value) != inputs._canonical(old.record(kind, index)):
                        raise ValueError('calendar version changed a stream value or interval')
                    restored = inputs._chain(restored, value)
                original = root['streams'][kind]['record_chain_sha256']
                if restored != original:
                    raise ValueError('calendar version record chain mismatch')
                audited[kind] = {'count': counts[kind], 'source_record_chain_sha256': original,
                    'target_restored_record_chain_sha256': restored,
                    'target_record_chain_sha256': newer['streams'][kind]['record_chain_sha256']}
            prefixes = [[block['clock_prefix'] for block in reader.manifest['streams']['segments']['blocks']]
                        for reader in (old, new)]
            if prefixes[0] != prefixes[1]:
                raise ValueError('calendar version changed the analytic temperature clock')
            receipt = {'version': VERSION, 'scope': 'synthetic_calendar_version_only',
                'source_root_sha256': old.root_sha256, 'target_root_sha256': new.root_sha256,
                'source_calculation_sha256': old.calculation_sha256,
                'target_calculation_sha256': new.calculation_sha256,
                'source_program_id': root['program_id'], 'target_program_id': program_id,
                'source_period': root['period'], 'target_period': newer['period'],
                'offset_seconds': offset_days*86400, 'streams': audited, 'plan': new.plan,
                'temperature_clock_prefix_sha256': inputs._hash(prefixes[0]),
                'non_calendar_inputs_preserved': True, 'rights_or_gate_approval': False,
                'translation_code_sha256': CODE_SHA256, 'input_stream_code_sha256': inputs.CODE_SHA256}
        if sha256((Path(source)/'root.json').read_bytes()).hexdigest() != source_root_sha256:
            raise ValueError('source root changed during calendar versioning')
        return receipt
