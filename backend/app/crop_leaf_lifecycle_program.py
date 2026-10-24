"""Compute-free parsing of explicit management tied to original appearance bytes."""
from .crop_leaf_appearance_program import DISPLAY_POLICY as APPEARANCE_DISPLAY_POLICY, MAX
from .crop_leaf_artifact_reader import _exact, _rights
from .crop_morphology_artifact_io import MorphologyArtifactHold, _need
from .crop_morphology_artifact_reader import _canonical, _closed, _hash, _id, _parse, _utc

VERSION = 'leaf-lifecycle-management-program-v1'
DISPLAY_POLICY = {**APPEARANCE_DISPLAY_POLICY,
                  'leaf_count': 'active_after_explicit_births_and_declared_removals_v1',
                  'pending_leaves': 'excluded_from_current_geometry_and_area',
                  'removed_leaves': 'last_state_retained_not_current_geometry'}
EVENT_KEYS = {'schema_version', 'origin', 'action', 'event_id', 'leaf_id', 'time_origin_utc', 'at_elapsed_seconds_exact'}


class LeafLifecycleProgramHold(MorphologyArtifactHold):
    pass


def parse_leaf_lifecycle_management_program(*, program_raw):
    try:
        p = _parse(program_raw, MAX)
        _closed(p, {'schema_version', 'origin', 'program_id', 'rights', 'appearance_program_sha256', 'removals', 'display_policy'})
        _need(p['schema_version'] == VERSION and p['origin'] == 'synthetic'
              and _canonical(p['display_policy']) == _canonical(DISPLAY_POLICY),
              'SCOPE_HOLD: explicit synthetic lifecycle management program required')
        _id(p['program_id']); _rights(p['rights']); _hash(p['appearance_program_sha256'])
        _need(type(p['removals']) is list and len(p['removals']) <= 512, 'CAPACITY_HOLD: 0-512 removal declarations required')
        leaves = set(); events = set()
        for declaration in p['removals']:
            _closed(declaration, EVENT_KEYS)
            _need(declaration['schema_version'] == 'declared-whole-leaf-removal-event-v1'
                  and declaration['origin'] == 'synthetic' and declaration['action'] == 'remove_whole_leaf',
                  'SCOPE_HOLD: explicit whole-leaf removal declaration required')
            _id(declaration['event_id']); _id(declaration['leaf_id']); _utc(declaration['time_origin_utc'])
            _exact(declaration['at_elapsed_seconds_exact'], 's')
            _need(declaration['leaf_id'] not in leaves and declaration['event_id'] not in events,
                  'FORMAT_HOLD: unique removal leaf and event IDs required')
            leaves.add(declaration['leaf_id']); events.add(declaration['event_id'])
        return p
    except MorphologyArtifactHold as exc:
        raise LeafLifecycleProgramHold(str(exc)) from None
