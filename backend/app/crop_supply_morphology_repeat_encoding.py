"""Lossless, bounded receipt references to the genuine immediate parent seed."""
from copy import deepcopy
from hashlib import sha256
import json

VERSION = 'supply-morphology-parent-referenced-receipt-v1'
MAX_BYTES = 2 * 1024**2
MAX_DEPTH = 64
MIN_REFERENCE_BYTES = 64
FIELDS = {'version', 'receipt_sha256', 'source_code_set_sha256', 'body'}


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _canonical(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: 2MiB encoded/expanded receipt required')
    return raw


def _hash(value):
    return sha256(_canonical(value)).hexdigest()


def pack(parent, receipt, pins):
    _canonical(parent)
    original = _canonical(receipt)
    lookup = {}

    def index(value, source, path):
        _need(len(path) <= MAX_DEPTH, 'CAPACITY_HOLD: bounded parent reference depth required')
        raw = _canonical(value)
        if len(raw) >= MIN_REFERENCE_BYTES:
            digest = sha256(raw).hexdigest()
            previous = lookup.get(digest)
            if previous is None or len(_canonical([2, source, path])) < len(_canonical([2, previous[1], previous[2]])):
                lookup[digest] = (raw, source, path)
        if type(value) is dict:
            _need(all(type(key) is str for key in value), 'ENCODING_HOLD: JSON object keys required')
            for key in sorted(value):
                index(value[key], source, [*path, key])
        elif type(value) is list:
            for key, item in enumerate(value):
                index(item, source, [*path, key])

    index(pins, 1, [])
    index(parent, 0, [])

    def encode(value, depth):
        _need(depth <= MAX_DEPTH, 'CAPACITY_HOLD: bounded receipt depth required')
        raw = _canonical(value)
        match = lookup.get(sha256(raw).hexdigest()) if len(raw) >= MIN_REFERENCE_BYTES else None
        if match is not None and match[0] == raw and len(_canonical([2, match[1], match[2]])) < len(raw):
            return [2, match[1], match[2]]
        if type(value) is dict:
            _need(all(type(key) is str for key in value), 'ENCODING_HOLD: JSON object keys required')
            return [0, {key: encode(item, depth + 1) for key, item in value.items()}]
        if type(value) is list:
            return [1, [encode(item, depth + 1) for item in value]]
        _need(type(value) in (str, int, float, bool, type(None)), 'ENCODING_HOLD: JSON values required')
        return value

    packed = {'version': VERSION, 'receipt_sha256': sha256(original).hexdigest(),
              'source_code_set_sha256': _hash(pins), 'body': encode(receipt, 0)}
    _canonical(packed)
    return packed


def unpack(parent, packed, pins):
    _canonical(parent)
    _canonical(packed)
    _need(type(packed) is dict and set(packed) == FIELDS and packed['version'] == VERSION
          and packed['source_code_set_sha256'] == _hash(pins),
          'ENCODING_HOLD: exact version/current source code set required')
    used = 0
    sizes = {}

    def consume(count):
        nonlocal used
        used += count
        _need(used <= MAX_BYTES, 'CAPACITY_HOLD: expanded receipt exceeds2MiB')

    def reference(source, path):
        _need(type(source) is int and source in (0, 1) and type(path) is list and len(path) <= MAX_DEPTH,
              'REFERENCE_HOLD: bounded actual parent/source reference required')
        value = parent if source == 0 else pins
        for key in path:
            if type(value) is dict:
                _need(type(key) is str and key in value, 'REFERENCE_HOLD: actual parent object path required')
            else:
                _need(type(value) is list and type(key) is int and 0 <= key < len(value),
                      'REFERENCE_HOLD: actual parent array path required')
            value = value[key]
        key = (source, tuple(path))
        if key not in sizes:
            sizes[key] = len(_canonical(value))
        consume(sizes[key])
        return deepcopy(value)

    def decode(value, depth):
        _need(depth <= MAX_DEPTH, 'CAPACITY_HOLD: bounded encoded receipt depth required')
        if type(value) is not list:
            _need(type(value) in (str, int, float, bool, type(None)), 'ENCODING_HOLD: JSON primitive required')
            consume(len(_canonical(value)))
            return value
        _need(len(value) in (2, 3) and type(value[0]) is int, 'ENCODING_HOLD: exact tagged node required')
        if value[0] == 2:
            _need(len(value) == 3, 'REFERENCE_HOLD: exact parent reference required')
            return reference(value[1], value[2])
        _need(len(value) == 2, 'ENCODING_HOLD: exact container node required')
        if value[0] == 0:
            items = value[1]
            _need(type(items) is dict and all(type(key) is str for key in items),
                  'ENCODING_HOLD: exact object node required')
            consume(2 + max(0, len(items) - 1) + sum(len(_canonical(key)) + 1 for key in items))
            return {key: decode(item, depth + 1) for key, item in items.items()}
        _need(value[0] == 1 and type(value[1]) is list, 'ENCODING_HOLD: exact array node required')
        consume(2 + max(0, len(value[1]) - 1))
        return [decode(item, depth + 1) for item in value[1]]

    receipt = decode(packed['body'], 0)
    raw = _canonical(receipt)
    _need(len(raw) == used and sha256(raw).hexdigest() == packed['receipt_sha256'],
          'PROOF_HOLD: exact original canonical receipt bytes required')
    return receipt
