"""Compute-free shape validation for explicitly synthetic appearance programs."""
from . import crop_leaf_population_artifact_reader as legacy
from .crop_leaf_artifact_reader import _curve, _rights
from .crop_morphology_artifact_io import MorphologyArtifactHold, _need
from .crop_morphology_artifact_reader import _canonical, _closed, _hash, _id, _parse, _quantity


VERSION = 'leaf-appearance-software-program-v1'
MAX = legacy.MAX
DISPLAY_POLICY = {**legacy.POPULATION_DISPLAY_POLICY, 'leaf_count': 'computed_from_explicit_phytomer_policy_v1'}
POLICY_KEYS = {'origin', 'sequence_basis', 'policy_id', 'shoot_id', 'schedule_id',
               'first_generative_sequence', 'vegetative_between_generative'}


class LeafAppearanceProgramHold(ValueError):
    pass


def parse_leaf_appearance_program(*, program_raw):
    try:
        p = _parse(program_raw, MAX)
        _closed(p, {'schema_version', 'origin', 'program_id', 'rights', 'stem', 'initialization',
                    'policy', 'leaf_profile', 'display_policy'})
        _need(p['schema_version'] == VERSION and p['origin'] == 'synthetic'
              and _canonical(p['display_policy']) == _canonical(DISPLAY_POLICY),
              'SCOPE_HOLD: supported synthetic appearance program required')
        _id(p['program_id']); _rights(p['rights']); _closed(p['stem'], {'artifact_sha256', 'program_sha256'})
        for value in p['stem'].values(): _hash(value)
        _closed(p['initialization'], {'input_id', 'initial_inventory'}); _id(p['initialization']['input_id'])
        legacy._initial_program({'schema_version': 'leaf-software-program-v1', 'origin': 'synthetic',
            'program_id': p['program_id'], 'rights': p['rights'], 'stem': p['stem'],
            'initialization': p['initialization']['initial_inventory'], 'display_policy': legacy.DISPLAY_POLICY})
        policy = p['policy']; _closed(policy, POLICY_KEYS)
        _need(policy['origin'] == 'synthetic' and policy['sequence_basis'] == 'explicit_emergence_schedule',
              'SCOPE_HOLD: explicit synthetic appearance policy required')
        for key in ('policy_id', 'shoot_id', 'schedule_id'): _id(policy[key])
        for key in ('first_generative_sequence', 'vegetative_between_generative'):
            _need(type(policy[key]) is int and 0 <= policy[key] <= 2**31-1,
                  'FORMAT_HOLD: explicit bounded appearance sequence required')
        profile = p['leaf_profile']; _closed(profile, {'base_temperature', 'curve', 'normalization', 'initial_area'})
        _quantity(profile['base_temperature'], 'degC'); _curve(profile['curve']); _quantity(profile['initial_area'], 'm2', positive=True)
        _need(profile['normalization'] == 'zero_lower_asymptote_sigmoid_v1', 'MODEL_HOLD: explicit leaf normalization required')
        return p
    except MorphologyArtifactHold as exc:
        raise LeafAppearanceProgramHold(str(exc)) from None
