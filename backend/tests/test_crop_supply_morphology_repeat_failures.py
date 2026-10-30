"""Rehashed state rejection and confirmed-prefix failure behavior on real owners."""
from copy import deepcopy
import json

import pytest

from test_crop_supply_morphology_repeat import (
    current, profiles, prepared, pending, calculated, adopted, trajectory,
    post_pending, post_calculated, successor, repeat_root,
)


def set_path(value, path, replacement):
    for key in path[:-1]:
        value = value[key]
    value[path[-1]] = replacement


CONTEXT_MUTATIONS = [
    (('version',), 'foreign-context'),
    (('descriptor', 'scope'), 'production'),
    (('descriptor', 'G0_G4'), 'approved'),
    (('descriptor', 'origin_context_sha256'), '0' * 64),
    (('descriptor', 'seed', 'event_sequence'), -1),
    (('descriptor', 'seed', 'initial_sample', 'state', 0), 0.),
    (('descriptor', 'receipt_sha256'), ['0' * 64]),
    (('receipts',), [{}]),
    (('unexpected',), True),
]


@pytest.mark.parametrize('path,replacement', CONTEXT_MUTATIONS)
def test_rehashed_context_cannot_change_source_derived_state(repeat_root, monkeypatch, path, replacement):
    from app import crop_supply_morphology_repeat_context as owner
    from app import crop_supply_morphology_repeat_resume as model
    context, origin, _, _ = repeat_root
    value = json.loads(context._raw)
    set_path(value, path, replacement)
    raw = owner._canonical(value)
    def forbidden(*args, **kwargs):
        raise AssertionError('invalid Context must not evaluate biology')
    monkeypatch.setattr(model.stage, 'evaluate', forbidden)
    with pytest.raises(ValueError):
        owner.restore_context(origin, raw, expected_sha256=owner._hash(value))


CHECKPOINT_MUTATIONS = [
    (('version',), 'foreign-checkpoint'),
    (('context_sha256',), '0' * 64),
    (('branch_steps',), 1),
    (('last_confirmed', 'state', 0), 0.),
    (('schedule', 'next_sequence'), -1),
    (('at', 'elapsed_seconds_exact', 'numerator'), '0'),
    (('output_prefix_sha256',), '0' * 64),
    (('scope',), 'production'),
    (('G0_G4',), 'approved'),
    (('unexpected',), True),
]


@pytest.mark.parametrize('path,replacement', CHECKPOINT_MUTATIONS)
def test_rehashed_checkpoint_cannot_change_seed_accounts_or_prefix(repeat_root, monkeypatch, path, replacement):
    from app import crop_supply_morphology_repeat_resume as model
    context = repeat_root[0]
    value = model.start(context).value
    set_path(value, path, replacement)
    raw = model._canonical(value, model.MAX_CP)
    def forbidden(*args, **kwargs):
        raise AssertionError('invalid seed CP must fail before biology')
    monkeypatch.setattr(model.stage, 'evaluate', forbidden)
    with pytest.raises(ValueError):
        model.restore_checkpoint(context, raw, expected_sha256=model._hash(value))


@pytest.mark.parametrize('which', ['context', 'checkpoint'])
def test_authority_wire_size_limit_is_enforced_before_biology(repeat_root, monkeypatch, which):
    from hashlib import sha256
    from app import crop_supply_morphology_repeat_context as owner
    from app import crop_supply_morphology_repeat_resume as model
    context, origin, _, _ = repeat_root
    def forbidden(*args, **kwargs):
        raise AssertionError('oversize input must fail before biology')
    monkeypatch.setattr(model.stage, 'evaluate', forbidden)
    cap = owner.MAX_BYTES if which == 'context' else model.MAX_CP
    raw = b' ' * (cap + 1)
    with pytest.raises(ValueError):
        if which == 'context':
            owner.restore_context(origin, raw, expected_sha256=sha256(raw).hexdigest())
        else:
            model.restore_checkpoint(context, raw, expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('budget', [True, False, 0, -1, 129, 1., None])
def test_invalid_endpoint_budgets_do_not_admit_authority(budget):
    from app import crop_supply_morphology_repeat_resume as model
    with pytest.raises(ValueError, match='BUDGET_HOLD'):
        model.advance_chunk(None, None, budget)


@pytest.mark.parametrize('failure', ['domain', 'late_code', 'caller_checkpoint', 'profile', 'rights', 'stage_input'])
def test_failed_second_interval_keeps_only_publishable_confirmed_prefix(repeat_root, monkeypatch, failure):
    from pathlib import Path
    from app import crop_supply_morphology_repeat_resume as model
    context = repeat_root[0]
    checkpoint = model.start(context)
    original_raw = checkpoint._raw
    before_context = context._raw
    profile = context._root._profiles[0]
    original_bounds = profile.filtered_temperature_bounds
    from stat import S_IMODE
    directory = Path(context._origin._origin._origin._source._source._directories[0])
    original_mode = S_IMODE(directory.stat().st_mode)
    evaluate = model.stage.evaluate
    read = Path.read_bytes
    changed = {'active': False, 'stage_calls': 0}
    changed_path = Path(model.__file__).resolve().parents[2] / 'backend/app/crop_growth_rates.py'
    def current_bytes(path):
        raw = read(path)
        return raw + b'changed-current-source' if changed['active'] and path == changed_path else raw
    def injected(*args, **kwargs):
        changed['stage_calls'] += 1
        if changed['stage_calls'] == 6:
            if failure == 'domain':
                raise ValueError('DOMAIN_HOLD: injected second-interval evaluation failure')
            if failure == 'late_code':
                changed['active'] = True
            elif failure == 'caller_checkpoint':
                object.__setattr__(checkpoint, '_raw', b'caller-changed-bytes')
            elif failure == 'profile':
                object.__setattr__(profile, 'filtered_temperature_bounds', (1., 2.))
            elif failure == 'rights':
                directory.chmod(0)
            else:
                args[2]['internodes'][-1]['parent_internode_id'] = 'invented-parent'
        return evaluate(*args, **kwargs)
    monkeypatch.setattr(model.stage, 'evaluate', injected)
    monkeypatch.setattr(Path, 'read_bytes', current_bytes)
    try:
        result = model.advance_chunk(context, checkpoint, 2)
    finally:
        changed['active'] = False
        object.__setattr__(profile, 'filtered_temperature_bounds', original_bounds)
        directory.chmod(original_mode)
        object.__setattr__(checkpoint, '_raw', original_raw)
    assert changed['stage_calls'] >= 6
    assert result['status'] == 'hold' and result['checkpoint'] is None and result['pending_event'] is None
    assert result['past_intervals_reintegrated'] == 0
    if failure == 'domain':
        assert len(result['samples']) == len(result['intervals']) == 1
        assert model.X(result['last_confirmed']['at']['elapsed_seconds_exact']) == model.F(304)
        assert result['last_confirmed']['output_prefix_link']['previous_output_prefix_sha256'] == checkpoint.value['output_prefix_sha256']
    else:
        assert result['samples'] == result['intervals'] == [] and result['last_confirmed'] is None
    assert context._raw == before_context and checkpoint._raw == original_raw


@pytest.fixture(scope='module')
def repeat_pending(repeat_root):
    from test_crop_supply_morphology_repeat import seed_inputs
    from app import crop_supply_morphology_repeat_resume as model
    from app import crop_supply_morphology_repeat_candidate as candidate
    context = repeat_root[0]
    result = model.advance_chunk(context, model.start(context), 128)
    assert result['status'] == 'hold' and result['pending_event'] is not None
    raw = model._canonical(result['last_confirmed'])
    digest = model._hash(result['last_confirmed'])
    tolerance = {'numerator': '1', 'denominator': '1000', 'unit': 's'}
    prepared_candidate = candidate.prepare(context, raw, expected_sha256=digest,
                                          time_tolerance_seconds_exact=tolerance)
    inputs = seed_inputs(context, digest, prepared_candidate.value, with_leaf=True, length=0.)
    return context, raw, digest, tolerance, prepared_candidate, inputs


POINT_MUTATIONS = [
    (('internode', 'declaration', 'initial_carbon', 'value'), 0.),
    (('internode', 'declaration', 'initial_carbon', 'value'), -1.),
    (('internode', 'declaration', 'initial_carbon', 'value'), 1e6),
    (('internode', 'declaration', 'initial_carbon', 'value'), 1e-300),
    (('internode', 'declaration', 'sink_weight', 'value'), -1.),
    (('internode', 'declaration', 'carbon_removal', 'value'), 1.),
    (('internode', 'declaration', 'compartment_id'), 'wrong-child'),
    (('internode', 'initial_length', 'value'), -1.),
    (('internode', 'initial_length', 'value'), 1e6),
    (('internode', 'construction_cost', 'value'), 0.),
    (('leaf', 'declaration', 'leaf_id'), 'wrong-leaf'),
    (('leaf', 'incoming_temperature', 'value'), -300.),
    (('leaf', 'construction_cost', 'value'), 0.),
    (('source_threshold_sequence',), -1),
    (('candidate_sha256',), '0' * 64),
    (('at_elapsed_seconds_exact', 'numerator'), '0'),
    (('rights', 'use'), False),
]


@pytest.mark.parametrize('path,replacement', POINT_MUTATIONS)
def test_invalid_seed_domain_funding_and_rights_never_issue_a_point(repeat_pending, monkeypatch, path, replacement):
    from app import crop_supply_morphology_repeat_point as point
    context, raw, digest, tolerance, prepared_candidate, original = repeat_pending
    inputs = deepcopy(original)
    set_path(inputs, path, replacement)
    before = context._raw
    caller_before = point.resume._canonical(inputs)
    def forbidden(*args, **kwargs):
        raise AssertionError('invalid declaration must fail before post-material biology')
    monkeypatch.setattr(point.core.stage, 'evaluate', forbidden)
    with pytest.raises(ValueError) as error:
        point.apply_fractional_material_point(context, raw, expected_sha256=digest,
            time_tolerance_seconds_exact=tolerance, inputs=inputs, prepared_candidate=prepared_candidate)
    if path == ('internode', 'declaration', 'initial_carbon', 'value') and replacement == 1e6:
        assert 'FUNDING_HOLD' in str(error.value)
    if path == ('internode', 'declaration', 'initial_carbon', 'value') and replacement == 1e-300:
        assert 'NUMERIC_HOLD' in str(error.value)
    assert context._raw == before and point.resume._canonical(inputs) == caller_before


@pytest.mark.parametrize('foreign', ['self_rehashed', 'copied_capability', 'checkpoint', 'tolerance'])
def test_prepared_candidate_reuse_still_requires_issued_current_authority(repeat_pending, monkeypatch, foreign):
    from app import crop_supply_morphology_repeat_candidate as candidate
    context, raw, digest, tolerance, issued, _ = repeat_pending
    prepared_candidate = issued
    issued_raw, issued_sha = issued._raw, issued.sha256
    tolerance = deepcopy(tolerance)
    if foreign == 'self_rehashed':
        value = issued.value
        value['scope'] = 'production'
        changed_raw = candidate.resume._canonical(value)
        object.__setattr__(issued, '_raw', changed_raw)
        object.__setattr__(issued, 'sha256', candidate.resume.sha256(changed_raw).hexdigest())
    elif foreign == 'copied_capability':
        prepared_candidate = candidate.PreparedCandidate(issued._raw, issued.sha256, issued._token)
    elif foreign == 'checkpoint':
        value = json.loads(raw)
        value['scope'] = 'production'
        raw = candidate.resume._canonical(value)
        digest = candidate.resume._hash(value)
    else:
        tolerance['denominator'] = '2000'
    def forbidden(*args, **kwargs):
        raise AssertionError('prepared reuse must not integrate')
    monkeypatch.setattr(candidate.resume.stage, 'evaluate', forbidden)
    try:
        with pytest.raises(ValueError):
            candidate.use_prepared(context, raw, expected_sha256=digest,
                time_tolerance_seconds_exact=tolerance, prepared_candidate=prepared_candidate)
    finally:
        object.__setattr__(issued, '_raw', issued_raw)
        object.__setattr__(issued, 'sha256', issued_sha)


def test_issued_prepared_candidate_reuse_does_no_rhs(repeat_pending, monkeypatch):
    from app import crop_supply_morphology_repeat_candidate as candidate
    context, raw, digest, tolerance, issued, _ = repeat_pending
    def forbidden(*args, **kwargs):
        raise AssertionError('prepared reuse must not integrate')
    monkeypatch.setattr(candidate.resume.stage, 'evaluate', forbidden)
    value = candidate.use_prepared(context, raw, expected_sha256=digest,
                                  time_tolerance_seconds_exact=tolerance, prepared_candidate=issued)
    assert candidate.resume._canonical(value) == issued._raw


def test_point_rejects_caller_mutation_after_capture(repeat_pending, monkeypatch):
    from app import crop_supply_morphology_repeat_point as point
    context, raw, digest, tolerance, issued, original = repeat_pending
    inputs = deepcopy(original)
    evaluate = point.core.stage.evaluate
    calls = []
    def changed(*args, **kwargs):
        result = evaluate(*args, **kwargs)
        inputs['reviewer'] = 'changed-after-input-capture'
        calls.append(1)
        return result
    monkeypatch.setattr(point.core.stage, 'evaluate', changed)
    with pytest.raises(ValueError, match='INPUT_HOLD'):
        point.apply_fractional_material_point(context, raw, expected_sha256=digest,
            time_tolerance_seconds_exact=tolerance, inputs=inputs, prepared_candidate=issued)
    assert calls


@pytest.fixture(scope='module')
def repeat_receipt(repeat_pending):
    from app import crop_supply_morphology_repeat_point as point
    from app import crop_supply_morphology_repeat_proofs as proofs
    context, raw, digest, tolerance, issued, inputs = repeat_pending
    proposal = point.apply_fractional_material_point(context, raw, expected_sha256=digest,
        time_tolerance_seconds_exact=tolerance, inputs=inputs, prepared_candidate=issued)
    return context, proofs.compact(proposal)


@pytest.mark.parametrize('field', ['funding', 'state', 'baseline', 'geometry', 'parent', 'budget', 'stage_extra', 'candidate_extra', 'json_type', 'initialization'])
def test_rehashed_compact_receipt_must_match_saved_arithmetic(repeat_receipt, monkeypatch, field):
    from app import crop_supply_morphology_repeat_proofs as proofs
    context, original = repeat_receipt
    original_bytes = proofs.resume._canonical(original)
    value = deepcopy(original)
    if field == 'funding':
        value['flow_components']['internode']['buffer_debit']['value'] += 1.
    elif field == 'state':
        value['after_state'][0] += 1.
    elif field == 'baseline':
        value['new_birth_baselines']['stem_root'][-1]['base_temperature']['value'] += 1.
    elif field == 'geometry':
        value['after_geometry_baselines']['internodes'][-2]['origin_geometry']['value'] += 1.
    elif field == 'json_type':
        value['after_geometry_baselines']['internodes'][-1]['origin_geometry']['value'] = False
    elif field == 'parent':
        value['after_organs']['internodes'][-1]['parent_internode_id'] = 'other-parent'
    elif field == 'budget':
        next(iter(value['post_point_global_ledgers_preview'].values()))['budget_exact']['numerator'] = '123'
    elif field == 'stage_extra':
        value['after_stage']['extra'] = 1
    elif field == 'candidate_extra':
        value['before_candidate']['extra'] = 1
        value['before_candidate']['calculation_sha256'] = proofs._hash({k:v for k,v in value['before_candidate'].items() if k != 'calculation_sha256'})
    else:
        value['leaf_receipts'][0]['initialization']['state']['anchor']['requested_area']['value'] *= 2
    value['calculation_sha256'] = proofs._hash({k:v for k,v in value.items() if k != 'calculation_sha256'})
    def forbidden(*args, **kwargs):
        raise AssertionError('saved receipt validation must not replay biology')
    monkeypatch.setattr(proofs.core.stage, 'evaluate', forbidden)
    with pytest.raises(ValueError):
        proofs.validate(context, value)
    assert proofs.resume._canonical(original) == original_bytes


@pytest.mark.parametrize('changed', ['profile', 'rights'])
def test_prepared_reuse_rechecks_current_profile_and_source_access(repeat_pending, monkeypatch, changed):
    from pathlib import Path
    from stat import S_IMODE
    from app import crop_supply_morphology_repeat_candidate as candidate
    context, raw, digest, tolerance, issued, _ = repeat_pending
    profile = context._root._profiles[0]
    original_bounds = profile.filtered_temperature_bounds
    directory = Path(context._origin._origin._origin._source._source._directories[0])
    original_mode = S_IMODE(directory.stat().st_mode)
    def forbidden(*args, **kwargs):
        raise AssertionError('current-authority check must not integrate')
    monkeypatch.setattr(candidate.resume.stage, 'evaluate', forbidden)
    try:
        if changed == 'profile':
            object.__setattr__(profile, 'filtered_temperature_bounds', (1., 2.))
        else:
            directory.chmod(0)
        with pytest.raises(ValueError):
            candidate.use_prepared(context, raw, expected_sha256=digest,
                                  time_tolerance_seconds_exact=tolerance, prepared_candidate=issued)
    finally:
        object.__setattr__(profile, 'filtered_temperature_bounds', original_bounds)
        directory.chmod(original_mode)
