"""Actual current read, serialized response and source/witness mutation checks."""
import json
import os
from pathlib import Path

import pytest

from test_crop_greenhouse_solar_prefix import (
    setup, producer_setup, progress_setup, worker_setup, authoring, profiles,
    login_database, original_login_scope, login_scope, query_cleanup,
    model as current, reference, read, selector, advance, writable)

pytestmark=[reference.reference.pytestmark,pytest.mark.usefixtures('query_cleanup')]


def save(name,value):
    root=os.environ.get('OSSF_SOLAR_PREFIX_PROJECTION_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as f:
            os.fchmod(f.fileno(),0o400);json.dump(value,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())


def test_selected_page_changed_after_serialization_is_held(setup,monkeypatch):
    query,worker,job_id,raw,value=setup
    lease=reference.confirm(worker,job_id);advance(worker,job_id,raw,lease,8)
    reference.readonly(value);record=query.read('tenant-1',job_id)
    pin=selector(json.loads(record.payload_raw));record=query.read('tenant-1',job_id,selector=pin,view='samples')
    _,artifact,_=reference.reference.producer.locations(worker.server,raw)
    head=json.loads((artifact/'HEAD').read_bytes())
    commit=json.loads((artifact/(head['latest_commit_sha256']+'.json')).read_bytes())
    path=artifact/(commit['pages']['samples'][0]['sha256']+'.json')
    original=path.read_bytes();mode=path.stat().st_mode&0o777
    try:
        path.chmod(0o600);path.write_bytes(original+b' ');path.chmod(mode)
        with monkeypatch.context() as patch:
            calls=reference.forbid(patch)
            with pytest.raises(current.SolarPrefixHold):query._after_projection('tenant-1',job_id,record)
            assert not any(calls.values())
    finally:path.chmod(0o600);path.write_bytes(original);path.chmod(mode)
    query._after_projection('tenant-1',job_id,record)
    save('after-serialization-page',{'actual_owned_selected_page_changed_after_original_read':True,
        'rejected_and_original_restored':True,'calls':calls})
