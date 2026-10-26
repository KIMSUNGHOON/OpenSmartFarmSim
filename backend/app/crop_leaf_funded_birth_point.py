"""Declared structural allocation point; crop-leaf-funded-birth-point-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite, ulp
from pathlib import Path
from sys import float_info

from . import crop_leaf_carbon_stock_continuation as resume
from . import crop_rational_morphology_clock as clock

VERSION = 'leaf-funded-structural-birth-point-research-v1'
POLICY = 'explicit-new-structural-carbon-from-buffer-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
CLOCK_CODE_SHA256 = sha256(Path(clock.__file__).read_bytes()).hexdigest()
FIELDS = {'schema_version', 'input_id', 'origin', 'policy', 'context_sha256',
          'checkpoint_sha256', 'at_elapsed_seconds_exact', 'model_floor_area', 'events'}
numeric = resume.short.numeric
MASS = resume.short.stock.part.source.MASS_UNIT


class FundedBirthHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise FundedBirthHold(reason)


def _canonical(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                     allow_nan=False).encode()
    _need(len(raw) <= 2*1024**2, 'CAPACITY_HOLD: 2MiB point input/output required')
    return raw


def _closed(value, keys):
    _need(type(value) is dict and set(value) == set(keys), 'INPUT_HOLD: closed point fields required')


def _quantity(value, unit):
    _closed(value, {'value', 'unit'})
    _need(value['unit'] == unit, 'UNIT_HOLD: '+unit+' required')
    _need(type(value['value']) in (int, float), 'INPUT_HOLD: explicit number required')
    v = float(value['value'])
    _need(isfinite(v) and (v == 0 or abs(v) >= float_info.min), 'NUMERIC_HOLD: finite normal or zero required')
    return v


def _rounded(exact):
    value = float(exact)
    _need(isfinite(value) and (exact == 0 or abs(value) >= float_info.min), 'NUMERIC_HOLD: normal representable transfer required')
    return value


def _balance(terms, unit):
    residual = numeric._sum(*terms)
    budget = 64*ulp(max(map(abs, terms)))
    _need(isfinite(budget) and abs(residual) <= budget, 'BALANCE_HOLD: unresolved point '+unit)
    return {'residual': numeric._q(residual, unit), 'budget': numeric._q(budget, unit)}


def _fund(buffer, masses, cost):
    exact = sum(map(Fraction.from_float, masses), Fraction(0))
    structural = _rounded(exact)
    respiration = _rounded(Fraction.from_float(cost)*exact)
    debit = _rounded(exact*(1+Fraction.from_float(cost)))
    after = _rounded(Fraction.from_float(buffer)-Fraction.from_float(debit))
    _need(structural > 0 and respiration > 0 and debit > 0 and after > 0,
          'FUNDING_HOLD: positive seed, growth cost and remaining buffer required')
    _need(after != buffer, 'NUMERIC_HOLD: nonzero buffer debit lost')
    return structural, respiration, debit, after


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
          and sha256(Path(clock.__file__).read_bytes()).hexdigest() == CLOCK_CODE_SHA256,
          'CODE_HOLD: original point/clock sources required')
    resume._fence()


def _new_leaf(leaf):
    short = resume.short
    _closed(leaf, {'leaf_id', 'curve', *short.old.LEAF_UNITS, *short.STOCK_FIELDS})
    values = {k: _quantity(leaf[k], unit) for k, unit in
              {**short.old.LEAF_UNITS, **short.STOCK_FIELDS}.items()}
    _need(values['thermal_age'] == 0 and values['initial_carbon'] > 0
          and values['sink_weight'] >= 0 and values['carbon_removal'] >= 0,
          'BIRTH_HOLD: zero age, positive carbon and nonnegative sink/removal required')
    receipt = short.old.leaf_area.initialize_leaf_area(inputs={
        'input_id': leaf['leaf_id'], 'leaf_id': leaf['leaf_id'], 'origin': 'synthetic',
        'thermal_age_basis': 'since_leaf_emergence', 'normalization': short.old.leaf_area.NORMALIZATION,
        'age_exact': {'numerator': '0', 'denominator': '1', 'unit': 'degC_day'},
        'curve': leaf['curve'], 'initial_area': leaf['initial_area']})
    normalized = {'leaf_id': leaf['leaf_id'], 'curve': receipt['state']['curve'],
                  **{k: numeric._q(v, ({**short.old.LEAF_UNITS, **short.STOCK_FIELDS})[k])
                     for k, v in values.items()}}
    return normalized, receipt


def _apply_current(*, program, anchors, manifest, saved, context_sha256, checkpoint_sha256, profiles, inputs):
    try:
        _fence()
        _closed(inputs, FIELDS)
        raw = _canonical(inputs)
        v = json.loads(raw)
        resume.short.old.leaf_area._identifier(v['input_id'])
        _need(v['schema_version'] == 'leaf-funded-birth-point-input-v1'
              and v['origin'] == 'synthetic' and v['policy'] == POLICY,
              'POLICY_HOLD: explicit synthetic new structural growth required')
        _need(v['context_sha256'] == context_sha256 and v['checkpoint_sha256'] == checkpoint_sha256,
              'HASH_HOLD: original context/checkpoint required')
        p = program
        y = saved['last_confirmed']['state']
        n = len(p['leaves'])
        at = Fraction.from_float(manifest['numerical']['step_seconds'])*saved['step_index']
        _need(clock._seconds(v['at_elapsed_seconds_exact']) == at, 'TIME_HOLD: original exact elapsed required')
        floor = _quantity(v['model_floor_area'], 'm2_floor')
        _need(floor == p['model_floor_area']['value'], 'BASIS_HOLD: original floor required')
        events = v['events']
        _need(type(events) is list and 1 <= len(events) <= 512-n,
              'CAPACITY_HOLD: nonempty batch and at most512 resulting leaves required')
        leaves, receipts, capacities, energies = [], [], [], []
        ids = {leaf['leaf_id'] for leaf in p['leaves']}
        event_ids = set()
        k = p['scenario']['parameters']['leaf_heat_capacity']['value']
        ref = p['scenario']['parameters']['reference_temperature']['value']
        for event in events:
            _closed(event, {'event_id', 'attachment_internode_id', 'incoming_temperature', 'leaf'})
            for key in ('event_id', 'attachment_internode_id'):
                resume.short.old.leaf_area._identifier(event[key])
            leaf, receipt = _new_leaf(event['leaf'])
            _need(leaf['leaf_id'] not in ids and event['event_id'] not in event_ids,
                  'EVENT_HOLD: unique new leaf and event IDs required')
            ids.add(leaf['leaf_id'])
            event_ids.add(event['event_id'])
            incoming = _quantity(event['incoming_temperature'], 'degC')
            numeric._temperature(incoming)
            area = receipt['state']['area']['value']
            cap = _rounded(Fraction.from_float(k)*Fraction.from_float(area)/Fraction.from_float(floor))
            energy = _rounded(Fraction.from_float(cap)*(Fraction.from_float(incoming)-Fraction.from_float(ref)))
            _need(cap > 0, 'CAPACITY_HOLD: positive incoming capacity required')
            leaves.append(leaf)
            receipts.append({'event_id': event['event_id'], 'attachment_internode_id': event['attachment_internode_id'],
                             'initialization': receipt, 'capacity_in': numeric._q(cap, numeric.CAPACITY),
                             'sensible_in': numeric._q(energy, numeric.ENERGY)})
            capacities.append(cap)
            energies.append(energy)
        masses = [leaf['initial_carbon']['value'] for leaf in leaves]
        structural, respiration, debit, buffer = _fund(y[0], masses, profiles['growth_profile'].values['cLeafG'])
        capacity = _rounded(sum(map(Fraction.from_float, capacities), Fraction(0)))
        energy = _rounded(sum(map(Fraction.from_float, energies), Fraction(0)))
        after_u = _rounded(Fraction.from_float(y[104])+Fraction.from_float(energy))
        _need(energy == 0 or after_u != y[104], 'NUMERIC_HOLD: nonzero incoming heat lost')
        base = list(y[:107])
        base[0], base[104] = buffer, after_u
        state = [*base, *y[107:107+n], *([0.]*len(leaves)), *y[107+n:107+2*n],
                 *(row['initialization']['state']['area']['value'] for row in receipts), *y[107+2*n:], *masses]
        after_program = {**deepcopy(p), 'leaves': [*deepcopy(p['leaves']), *leaves]}
        rates, current = resume.short._evaluate(after_program, tuple(state), profiles)
        gaps = [*anchors, *(numeric._q(0., 'm2') for _ in leaves)]
        sample = resume.short._sample(saved['step_index'], manifest['numerical']['step_seconds'], state, current, gaps)
        carbon_before = numeric._sum(y[0], y[1], *y[4:54], *y[107+2*n:])
        carbon_after = numeric._sum(state[0], state[1], *state[4:54], *state[107+2*(n+len(leaves)):])
        balances = {'buffer': _balance((buffer, -y[0], debit), MASS),
                    'new_stock': _balance((*masses, -structural), MASS),
                    'whole_carbon': _balance((carbon_after, -carbon_before, respiration), MASS),
                    'sensible': _balance((after_u, -y[104], -energy), numeric.ENERGY),
                    'capacity': _balance((sample['derived']['canopy_capacity']['value'],
                                -saved['last_confirmed']['derived']['canopy_capacity']['value'], -capacity), numeric.CAPACITY)}
        result = {'model_version': VERSION, 'policy': POLICY, 'code_sha256': CODE_SHA256,
                  'clock_code_sha256': CLOCK_CODE_SHA256, 'input_sha256': sha256(raw).hexdigest(),
                  'context_sha256': context_sha256, 'checkpoint_sha256': checkpoint_sha256,
                  'parent_manifest': manifest, 'inputs': v, 'before_checkpoint': saved,
                  'after_program': after_program, 'after_sample': sample, 'after_rates': list(rates),
                  'after_state_layout': resume.short._layout(after_program), 'birth_receipts': receipts,
                  'point_flows': {name: numeric._q(value, unit) for name, value, unit in (
                      ('structural_carbon', structural, MASS), ('growth_respiration', respiration, MASS),
                      ('buffer_debit', debit, MASS), ('capacity_in', capacity, numeric.CAPACITY),
                      ('sensible_in', energy, numeric.ENERGY))}, 'balances': balances,
                  'checkpoint_validation_stage_evaluations': 1, 'after_stage_evaluations': 1,
                  'elapsed_steps_advanced': 0, 'checkpoint': None, 'scope': 'software_research_only',
                  'claim_scope': 'synthetic_declared_new_structural_allocation_point_only', 'G0_G4': 'not_assessed'}
        result['calculation_sha256'] = sha256(_canonical(result)).hexdigest()
        _canonical(result)
        _fence()
        return result
    except FundedBirthHold:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise FundedBirthHold(str(error) if isinstance(error, ValueError)
                              else 'INPUT_HOLD: invalid point input/arithmetic') from None


def apply_births(*, context, raw_checkpoint, expected_sha256, inputs):
    try:
        _fence()
        _closed(inputs, FIELDS)
        cp = resume.restore_checkpoint(context, raw_checkpoint, expected_sha256=expected_sha256)
        p, seed, manifest = resume._context(context)
        return _apply_current(program=p, anchors=seed['evaluation']['curve_residuals'], manifest=manifest,
                              saved=cp.value, context_sha256=context.root_sha256, checkpoint_sha256=cp.sha256,
                              profiles=resume._profiles(context), inputs=inputs)
    except FundedBirthHold:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise FundedBirthHold(str(error) if isinstance(error, ValueError)
                              else 'INPUT_HOLD: invalid point input/arithmetic') from None
