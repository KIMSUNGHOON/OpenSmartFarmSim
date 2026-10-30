from copy import deepcopy
from fractions import Fraction

import pytest

from test_crop_supply_morphology_successor_context import (
    current, profiles, prepared, pending, calculated, adopted, trajectory,
    post_pending, post_calculated, successor,
)


def test_pin_check_reads_each_declared_source_once(monkeypatch):
    from collections import Counter
    from pathlib import Path
    from app import crop_supply_morphology_repeat_context as owner
    root = Path(owner.__file__).resolve().parents[2]
    expected = owner._pins()
    reads = []
    read = Path.read_bytes
    def counted(path):
        reads.append(str(path.relative_to(root)))
        return read(path)
    monkeypatch.setattr(Path, 'read_bytes', counted)
    assert owner._pins() == expected
    assert Counter(reads) == Counter({name: 1 for name in expected})


@pytest.mark.parametrize('which', ['ancestor', 'repeat'])
def test_flat_pin_check_still_rejects_changed_current_bytes(monkeypatch, which):
    from pathlib import Path
    from app import crop_supply_morphology_repeat_context as owner
    pins = owner._pins()
    name = 'backend/app/crop_growth_rates.py' if which == 'ancestor' else 'backend/app/crop_supply_morphology_repeat_context.py'
    assert name in pins
    root = Path(owner.__file__).resolve().parents[2]
    changed = root / name
    read = Path.read_bytes
    def altered(path):
        raw = read(path)
        return raw + b'changed-current-code' if path == changed else raw
    monkeypatch.setattr(Path, 'read_bytes', altered)
    with pytest.raises(ValueError):
        owner._pins()


def test_repeat_api_uses_its_own_context_and_checkpoint_family():
    from app import crop_supply_morphology_repeat_context as owner
    from app import crop_supply_morphology_repeat_resume as model
    assert owner.Context is not model.initial.owner.Context
    assert model.Checkpoint is not model.initial.Checkpoint


def test_repeat_adoption_uses_the_same_real_family_after_each_event():
    from app import crop_supply_morphology_repeat_context as owner
    from app import crop_supply_morphology_repeat_candidate as candidate
    assert callable(owner.prepare_next_context)
    assert callable(candidate.calculate_next_event_candidate)


@pytest.mark.parametrize('untrusted', [None, {}, b'raw-proposal'])
def test_raw_proposals_are_not_genuine_prepared_candidates(untrusted):
    from app import crop_supply_morphology_repeat_candidate as candidate
    with pytest.raises(ValueError):
        candidate.use_prepared(None, b'', expected_sha256='0' * 64,
                               time_tolerance_seconds_exact={'numerator': '1', 'denominator': '1000', 'unit': 's'},
                               prepared_candidate=untrusted)


@pytest.fixture(scope='module')
def repeat_root(successor):
    from app import crop_supply_morphology_successor_resume as initial
    from app import crop_supply_morphology_repeat_context as owner
    origin = successor[0]
    checkpoint = initial.start(origin)
    raw = initial.checkpoint_bytes(origin, checkpoint)
    context = owner.prepare_context(origin, raw, expected_sha256=checkpoint.sha256)
    return context, origin, raw, checkpoint.sha256


def test_actual_successor_bridge_preserves_state_origins_and_zero_rhs_export(repeat_root, monkeypatch):
    from app import crop_supply_morphology_repeat_context as owner
    from app import crop_supply_morphology_repeat_resume as model
    context, origin, _, _ = repeat_root
    def forbidden(*args, **kwargs):
        raise AssertionError('bridge export/start/cold context must not evaluate biology')
    monkeypatch.setattr(model.stage, 'evaluate', forbidden)
    checkpoint = model.start(context)
    assert checkpoint.value['last_confirmed'] == origin.value['seed']['initial_sample']
    assert context.value['seed']['geometry_baselines'] == origin.value['seed']['geometry_baselines']
    raw = owner.context_bytes(context)
    cold = owner.restore_context(origin, raw, expected_sha256=context.root_sha256)
    assert owner.context_bytes(cold) == raw
    assert model.checkpoint_bytes(cold, model.start(cold)) == model.checkpoint_bytes(context, checkpoint)


def test_generic_branch_advances_actual_fractional_remainder(repeat_root):
    from app import crop_supply_morphology_repeat_resume as model
    context = repeat_root[0]
    checkpoint = model.start(context)
    result = model.advance_chunk(context, checkpoint, 1)
    assert result['status'] == 'yielded', result['hold']
    assert model.X(result['checkpoint'].value['at']['elapsed_seconds_exact']) == Fraction(304)
    assert result['samples'][0]['state'][-1] > 0
    assert result['current_validation_RHS_evaluations'] == 1
    assert result['new_RHS_evaluations'] == 4
    assert result['checkpoint'].value['point_totals_exact'] == checkpoint.value['point_totals_exact']


def seed_inputs(context, digest, calculation, *, with_leaf, length):
    from app import crop_supply_morphology_repeat_point as point
    data = point.resume._context(context)
    event = point.core.source_event(data, calculation)
    value = {
        'schema_version': 'supply-morphology-repeat-material-point-input-v1',
        'input_id': 'own-repeat-seed-QA', 'origin': 'synthetic', 'policy': point.POLICY,
        'parameter_source': 'own_declared_synthetic_assumptions',
        'parameter_revision': 'own-QA-explicit-repeat-seed-v1', 'reviewer': 'software-QA-not-field-validation',
        'context_sha256': context.root_sha256, 'checkpoint_sha256': digest,
        'candidate_sha256': calculation['calculation_sha256'],
        'initial_binding_sha256': data['initial_binding_sha256'],
        'at_elapsed_seconds_exact': deepcopy(calculation['at']['elapsed_seconds_exact']),
        'model_floor_area': deepcopy(data['program']['model_floor_area']),
        'source_event_id': event['source_event_id'], 'source_threshold_sequence': event['sequence'],
        'source_threshold_exact': event['threshold_exact'],
        'parent_internode_id': data['organs']['internodes'][-1]['compartment_id'],
        'internode': {'declaration': {'compartment_id': event['internode_id'], 'kind': 'internode',
                      'initial_carbon': {'value': .25, 'unit': point.core.MASS},
                      'sink_weight': {'value': 1., 'unit': '1'},
                      'carbon_removal': {'value': 0., 'unit': point.core.MASS + '/s'}},
                      'initial_length': {'value': length, 'unit': 'm'},
                      'construction_cost': {'value': 1e-6, 'unit': 'mg_CH2O/m_internode'}},
        'leaf': None, 'rights': deepcopy(data['_original_data']['point']['inputs']['rights']),
    }
    if with_leaf:
        declaration = deepcopy(data['program']['leaves'][0])
        declaration.update(leaf_id=event['leaf_id'], thermal_age={'value': 0., 'unit': 'degC_day'},
                           initial_area=point.core.arithmetic.resume.short.old.leaf_area._area_at(Fraction(0), declaration['curve']),
                           initial_carbon={'value': .125, 'unit': point.core.MASS}, sink_weight={'value': 1., 'unit': '1'})
        value['leaf'] = {'declaration': declaration, 'incoming_temperature': {'value': 22., 'unit': 'degC'},
                         'construction_cost': {'value': 1e-6, 'unit': 'mg_CH2O/m2_leaf'}}
    return value


def test_multiple_real_events_reach_original_horizon(repeat_root):
    from app import crop_supply_morphology_repeat_context as owner
    from app import crop_supply_morphology_repeat_resume as model
    from app import crop_supply_morphology_repeat_candidate as candidate
    context = repeat_root[0]
    checkpoint = model.start(context)
    first = checkpoint.value
    events = []
    for index in range(12):
        result = model.advance_chunk(context, checkpoint, 128)
        if result['status'] == 'completed':
            checkpoint = result['checkpoint']
            break
        assert result['status'] == 'hold' and result['pending_event'] is not None, result['hold']
        raw = model._canonical(result['last_confirmed'])
        digest = model._hash(result['last_confirmed'])
        tolerance = {'numerator': '1', 'denominator': '1000', 'unit': 's'}
        prepared_candidate = candidate.prepare(context, raw, expected_sha256=digest,
                            time_tolerance_seconds_exact=tolerance)
        calculation = prepared_candidate.value
        value = seed_inputs(context, digest, calculation, with_leaf=index % 2 == 0, length=.01 if index % 2 else 0.)
        previous = context
        context = owner.prepare_next_context(context, raw, expected_sha256=digest,
                            time_tolerance_seconds_exact=tolerance, inputs=value, prepared_candidate=prepared_candidate)
        assert type(context) is type(previous) is owner.Context
        seed = context.value['seed']
        for kind in ['leaves', 'internodes']:
            assert seed['geometry_baselines'][kind][:len(previous.value['seed']['geometry_baselines'][kind])] == previous.value['seed']['geometry_baselines'][kind]
        assert seed['event_sequence'] == result['last_confirmed']['event_sequence'] + 1
        assert seed['schedule']['next_sequence'] == result['last_confirmed']['schedule']['next_sequence'] + 1
        events.append(seed['schedule']['consumed_event_id'])
        checkpoint = model.start(context)
    else:
        pytest.fail('bounded repeated execution did not reach the original horizon')
    assert len(events) >= 2 and len(events) == len(set(events))
    assert model.X(checkpoint.value['at']['elapsed_seconds_exact']) == Fraction(512)
    assert checkpoint.value['event_sequence'] == first['event_sequence'] + len(events)
    assert len(owner.context_bytes(context)) <= owner.MAX_BYTES
    for row in checkpoint.value['global_ledgers'].values():
        assert abs(model.X(row['residual_exact'])) <= model.X(row['budget_exact'])
