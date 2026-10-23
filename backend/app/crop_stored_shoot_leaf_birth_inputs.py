"""Build explicit leaf declarations from an immutable synthetic shoot interval."""
from copy import deepcopy
from hashlib import sha256

from . import crop_declared_leaf_births as births
from . import crop_phytomer_kind as kinds
from . import crop_rational_leaf_area as leaf
from . import crop_rational_morphology_artifact_reader as stem
from .crop_morphology_artifact_io import MorphologyArtifactHold
from .crop_rational_new_internodes import (
    AIR_ADAPTER_VERSION, RationalNewInternodeHold, rational_air_segments_from_utc,
)
from .crop_shoot_timeline import MODEL_VERSION as TIMELINE_VERSION, ShootTimelineHold, advance_shoot_event_timeline


MODEL_VERSION = 'stored-shoot-leaf-birth-inputs-research-v1'
MODEL_VERSIONS = {'stem': 'morphology-research-artifact-v2', 'timeline': TIMELINE_VERSION,
    'kind': kinds.MODEL_VERSION, 'air_adapter': AIR_ADAPTER_VERSION, 'leaf': leaf.MODEL_VERSION,
    'declared_births': births.MODEL_VERSION}


class LeafBirthInputsHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise LeafBirthInputsHold(reason)


def _digest(value):
    return sha256(births._bounded(value)).hexdigest()


def _stored_state(directory, access, root, store, manifest, index):
    stem.read_rational_morphology_frame(directory, access, root, index=index)
    descriptor = manifest['samples'][index]
    result = stem._parse(store.get(descriptor['result_sha256'], maximum=stem.RESULT_MAX), stem.RESULT_MAX)
    return result['state'], descriptor['state_sha256']


def _node_identity(node):
    state = node['length_state']
    return {'sequence': node['sequence'], 'birth_age_exact': node['birth_age_exact'],
        'clock': {k: v for k, v in state['clock_state'].items() if k not in ('age_exact', 'at_elapsed_seconds_exact')},
        **{k: state[k] for k in ('curve', 'curve_sha256', 'anchor')}}


def _profile(value, origin):
    _need(type(value) is dict and set(value) == {'base_temperature', 'curve', 'normalization', 'initial_area'},
          'INPUT_HOLD: explicit closed uniform leaf profile required')
    zero = {'numerator': '0', 'denominator': '1', 'unit': 's'}
    clock = {'origin': 'synthetic', 'age_basis': 'since_leaf_emergence',
        'temperature_basis': 'indoor_air_piecewise_constant', 'leaf_id': 'profile-validation',
        'time_origin_utc': origin, 'emerged_elapsed_seconds_exact': zero, 'at_elapsed_seconds_exact': zero,
        'base_temperature': value['base_temperature'], 'age_exact': {**zero, 'unit': 'degC_day'}}
    state = leaf.initialize_rational_leaf_area(inputs={'input_id': 'profile-validation',
        'clock_state': clock, **{k: value[k] for k in ('curve', 'normalization', 'initial_area')}})['state']
    return {'base_temperature': state['clock_state']['base_temperature'], 'curve': state['area_state']['curve'],
        'normalization': state['area_state']['normalization'], 'initial_area': state['area_state']['anchor']['requested_area']}


def build_leaf_birth_inputs_from_stored_shoot(directory, access, root_sha256, *, start_index, end_index, inputs):
    try:
        _need(type(inputs) is dict and set(inputs) == {'input_id', 'policy', 'leaf_profile'},
              'INPUT_HOLD: closed stored-shoot leaf inputs required')
        births._bounded(inputs); inputs = deepcopy(inputs)
        kinds.classify_phytomer_sequences(inputs={'input_id': inputs['input_id'],
            'policy': inputs['policy'], 'sequences': []})
        _need(type(start_index) is int and type(end_index) is int and -1 <= start_index < end_index,
              'INDEX_HOLD: explicit forward stored interval required')
        with stem.MorphologyBlobStore(directory, access) as store:
            manifest = stem._load_manifest(store, root_sha256)
            _need(end_index < len(manifest['samples']), 'INDEX_HOLD: selected stored frame unavailable')
            program = stem._parse(store.get(manifest['program_sha256'], maximum=stem.PROGRAM_MAX), stem.PROGRAM_MAX)
            if start_index == -1:
                before, before_sha = program['initial_state'], manifest['initial_state_sha256']
            else:
                before, before_sha = _stored_state(directory, access, root_sha256, store, manifest, start_index)
            after, after_sha = _stored_state(directory, access, root_sha256, store, manifest, end_index)
            checkpoint = before['timeline_state']; origin = checkpoint['started_at']; policy = inputs['policy']
            _need(policy['shoot_id'] == checkpoint['shoot_id'] and policy['schedule_id'] == checkpoint['schedule_id'],
                  'SCOPE_HOLD: policy and original shoot schedule differ')
            start, end = checkpoint['at'], after['timeline_state']['at']
            segments = [{**s, 'start_utc': max(start, s['start_utc']), 'end_utc': min(end, s['end_utc'])}
                for s in program['segments'] if s['end_utc'] > start and s['start_utc'] < end]
            timeline = advance_shoot_event_timeline(inputs={'input_id': inputs['input_id'],
                'state': checkpoint, 'segments': segments})
            _need(timeline['checkpoint'] == after['timeline_state'], 'TIMELINE_HOLD: original endpoint and timeline differ')
            old_nodes, nodes, events = before['internodes'], after['internodes'], timeline['events']
            _need(before['inventory_start_sequence'] == after['inventory_start_sequence']
                  and len(nodes) == len(old_nodes)+len(events), 'PARENT_HOLD: stored interval inventory differs')
            _need(all(_node_identity(old) == _node_identity(current)
                for old, current in zip(old_nodes, nodes[:len(old_nodes)], strict=True)),
                'PARENT_HOLD: original parent identity changed')
            classified = kinds.classify_phytomer_sequences(inputs={'input_id': inputs['input_id'],
                'policy': policy, 'sequences': [e['sequence'] for e in events]})
            profile = _profile(inputs['leaf_profile'], origin)
            forcing = rational_air_segments_from_utc(time_origin_utc=origin, segments=segments)
            declarations = []; bound_events = []
            for event, node, typed in zip(events, nodes[len(old_nodes):], classified['phytomers'], strict=True):
                clock = node['length_state']['clock_state']
                entity = {k: checkpoint[k] for k in ('shoot_id', 'development_origin_id', 'schedule_id', 'started_at')}
                entity.update(sequence=event['sequence'], birth_age_exact=event['thermal_age_exact'])
                _need(node['sequence'] == event['sequence'] and node['birth_age_exact'] == event['thermal_age_exact']
                      and clock['emerged_elapsed_seconds_exact'] == event['elapsed_seconds_exact']
                      and clock['internode_id'] == 'internode:'+_digest(entity),
                      'PARENT_HOLD: source event and stored attachment differ')
                identifier = None
                if typed['kind'] == 'vegetative':
                    identifier = 'leaf:'+_digest({'model_version': MODEL_VERSION,
                        'stem_program_sha256': manifest['program_sha256'], 'policy_sha256': classified['policy_sha256'],
                        'sequence': event['sequence'], 'attachment_internode_id': clock['internode_id']})
                    birth_time = stem._fraction(event['elapsed_seconds_exact'])
                    _need(all(segment['air_temperature']['value'] >= profile['base_temperature']['value']
                        for segment in forcing if stem._fraction(segment['end_elapsed_seconds_exact']) > birth_time),
                        'THERMAL_DOMAIN_HOLD: post-birth air below explicit leaf base unsupported')
                    declarations.append({'leaf_id': identifier, 'attachment_internode_id': clock['internode_id'],
                        'emerged_elapsed_seconds_exact': deepcopy(event['elapsed_seconds_exact']), **deepcopy(profile)})
                bound_events.append({**deepcopy(event), 'kind': typed['kind'],
                    'attachment_internode_id': clock['internode_id'], 'leaf_id': identifier})
            result = {'model_version': MODEL_VERSION, **stem.FLAGS, 'model_versions': dict(MODEL_VERSIONS),
                'input_sha256': _digest({'model_version': MODEL_VERSION, 'model_versions': MODEL_VERSIONS,
                    'stem_artifact_sha256': root_sha256, 'start_index': start_index, 'end_index': end_index, 'inputs': inputs}),
                'stem_artifact_sha256': root_sha256, 'stem_program_sha256': manifest['program_sha256'],
                'start_index': start_index, 'end_index': end_index, 'start_state_sha256': before_sha, 'end_state_sha256': after_sha,
                'timeline_input_sha256': timeline['input_sha256'], 'policy_sha256': classified['policy_sha256'],
                'leaf_profile_sha256': _digest({'model_version': MODEL_VERSION, 'leaf_profile': profile}),
                'policy': deepcopy(policy), 'time_origin_utc': origin, 'timeline_checkpoint': timeline['checkpoint'],
                'start_elapsed_seconds_exact': deepcopy(forcing[0]['start_elapsed_seconds_exact']),
                'end_elapsed_seconds_exact': deepcopy(forcing[-1]['end_elapsed_seconds_exact']), 'events': bound_events,
                'leaf_inputs': {'input_id': inputs['input_id'], 'origin': 'synthetic', 'time_origin_utc': origin,
                    'segments': forcing, 'births': declarations}}
            births._bounded(result)
            stem._load_manifest(store, root_sha256)
            for index in (start_index, end_index):
                if index >= 0:
                    store.get(manifest['samples'][index]['result_sha256'], maximum=stem.RESULT_MAX)
            return result
    except (MorphologyArtifactHold, births.DeclaredLeafBirthHold, kinds.PhytomerKindHold,
            leaf.RationalLeafAreaHold, RationalNewInternodeHold, ShootTimelineHold) as exc:
        raise LeafBirthInputsHold(str(exc)) from None
