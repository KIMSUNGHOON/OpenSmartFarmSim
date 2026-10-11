#!/usr/bin/env python3
"""Publish a reviewed development record to the local static status feed."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile


def validate(raw):
    if len(raw) > 16384:
        raise ValueError('status exceeds 16KiB')
    value = json.loads(raw)
    expected = {'schema_version', 'reported_at', 'stages', 'remaining_focused_hours',
                'new_model_deployed', 'real_farm_runs', 'full_product_completion'}
    if type(value) is not dict or set(value) != expected or value['schema_version'] != 'development-status-v1':
        raise ValueError('status format rejected')
    stamp = value['reported_at']
    if type(stamp) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z', stamp):
        raise ValueError('status timestamp rejected')
    when = datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
    if (when-datetime.now(timezone.utc)).total_seconds() > 60:
        raise ValueError('future status rejected')
    hours = value['remaining_focused_hours']
    if (type(hours) is not dict or set(hours) != {'min', 'max'} or
            any(type(hours[k]) is not int for k in hours) or not 0 <= hours['min'] <= hours['max'] <= 100):
        raise ValueError('status estimate rejected')
    stages = value['stages']
    ids = ['growth', 'storage', 'api', 'execution_3d', 'activation']
    if type(stages) is not list or len(stages) != len(ids):
        raise ValueError('status stages rejected')
    for expected_id, stage in zip(ids, stages):
        if (type(stage) is not dict or set(stage) != {'id', 'state', 'evidence'} or
                stage['id'] != expected_id or stage['state'] not in ('completed', 'next', 'pending') or
                type(stage['evidence']) is not str or not 1 <= len(stage['evidence']) <= 240):
            raise ValueError('status stage rejected')
    if (type(value['new_model_deployed']) is not bool or type(value['real_farm_runs']) is not int or
            value['real_farm_runs'] < 0 or value['full_product_completion'] is not None):
        raise ValueError('status scope rejected')
    return value


def publish(source, directory):
    raw = source.read_bytes()
    value = validate(raw)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    current = directory/'current.json'
    if current.exists():
        old = current.read_bytes()
        if old == raw:
            return sha256(raw).hexdigest()
        if value['reported_at'] <= validate(old)['reported_at']:
            raise ValueError('an older or conflicting status cannot replace the current record')
    versions = directory/'versions'
    versions.mkdir(mode=0o700, exist_ok=True)
    digest = sha256(raw).hexdigest()
    version = versions/(digest+'.json')
    if version.exists():
        if version.read_bytes() != raw:
            raise ValueError('status version mismatch')
    else:
        with version.open('xb') as stream:
            os.fchmod(stream.fileno(), 0o400)
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    fd, name = tempfile.mkstemp(prefix='.status-', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o400)
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, current)
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        Path(name).unlink(missing_ok=True)
    return digest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1]/'web/public/development-status.json')
    parser.add_argument('--published-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({'sha256': publish(args.source, args.published_dir)}, sort_keys=True))
