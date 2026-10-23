"""Classify positions in a caller-declared synthetic phytomer sequence."""
from copy import deepcopy
from hashlib import sha256
import json
import re


MODEL_VERSION = 'phytomer-kind-research-v1'
POLICY_KEYS = {'origin', 'sequence_basis', 'policy_id', 'shoot_id', 'schedule_id',
               'first_generative_sequence', 'vegetative_between_generative'}


class PhytomerKindHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise PhytomerKindHold(reason)


def _identifier(value):
    _need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', value),
          'INPUT_HOLD: bounded ASCII identifier required')


def _index(value):
    _need(type(value) is int and 0 <= value <= 2**31-1,
          'INPUT_HOLD: bounded nonnegative integer required')


def _digest(value):
    return sha256(json.dumps({'model_version': MODEL_VERSION, **value}, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def classify_phytomer_sequences(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'policy', 'sequences'},
          'INPUT_HOLD: closed phytomer kind input required')
    _identifier(inputs['input_id'])
    policy = inputs['policy']
    _need(type(policy) is dict and set(policy) == POLICY_KEYS, 'INPUT_HOLD: explicit closed policy required')
    _need(type(policy['origin']) is str and policy['origin'] == 'synthetic'
          and type(policy['sequence_basis']) is str and policy['sequence_basis'] == 'explicit_emergence_schedule',
          'INPUT_HOLD: synthetic emergence schedule required')
    for field in ('policy_id', 'shoot_id', 'schedule_id'):
        _identifier(policy[field])
    first, between = policy['first_generative_sequence'], policy['vegetative_between_generative']
    _index(first); _index(between)
    sequences = inputs['sequences']
    _need(type(sequences) is list, 'INPUT_HOLD: explicit sequence list required')
    _need(len(sequences) <= 512, 'CAPACITY_HOLD: at most512 phytomer positions')
    previous = None
    for sequence in sequences:
        _index(sequence)
        _need(previous is None or sequence == previous+1, 'INPUT_HOLD: ordered contiguous sequences required')
        previous = sequence
    phytomers = [{'sequence': n, 'kind': 'generative'
                 if n >= first and (n-first) % (between+1) == 0 else 'vegetative'} for n in sequences]
    return {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
            'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
            'input_sha256': _digest({'inputs': inputs}), 'policy_sha256': _digest({'policy': policy}),
            'policy': deepcopy(policy), 'phytomers': phytomers}
