"""Actual unpaused public prefix pages compared with original terminal records."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlencode

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend/tests'))
import test_crop_climate_joint_prefix_runtime as reference
from app import crop_climate_joint_prefix as prefix

spec = importlib.util.spec_from_file_location('forward_lease_reference',
    ROOT / 'research/crop-climate-joint-prefix-lease-guard-reference.py')
fixture_reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_reference)
login_database = fixture_reference.login_database
pytest_plugins = ['test_crop_climate_joint_prefix_runtime']


@reference.LOGIN
def test_unpaused_public_pages_match_original_terminal(prefix_native, tmp_path, monkeypatch):
    c = prefix_native
    pack, factory = reference.unpaused_consumer(c, tmp_path)
    observations = []
    matches = []
    terminal_matches = False
    worker_exit = None

    def get(send, view, path, selector=None):
        endpoint = path + '/prefix' + ('' if view == 'summary' else '/' + view + '?' + urlencode(selector))
        status, raw = send('GET', endpoint)
        value = json.loads(raw)
        observations.append({'view': view, 'status': status, 'selector': selector,
            'wire_utf8': raw.decode(), 'wire_sha256': sha256(raw).hexdigest()})
        assert status in (200, 409, 503)
        if status == 200 and selector is not None:
            assert value['reference']['selector'] == selector
        return status, value

    try:
        with reference.served(c.prefix_runtime, c.config.certificate) as (send, replies):
            status, raw = send('POST', reference.POST, c.raw)
            assert status == 202
            job = json.loads(raw)['job_id']
            path = '/v1/jobs/' + job + '/crop-climate-joint-execution'
            with reference.consumer.legacy.process_consumer(tmp_path, 'joint_operator:build') as (process, events, errors):
                deadline = time.monotonic() + 240
                with monkeypatch.context() as patch:
                    calls = reference.progress.forbid(patch)
                    while True:
                        assert time.monotonic() < deadline and process.poll() is None and len(observations) < 80
                        status, value = get(send, 'summary', path)
                        if status == 200 and value['prefix_status'] == 'closed':
                            break
                        if status == 200 and value['prefix_status'] == 'accepted':
                            selector = value['reference']['selector']
                            for view in ('events', 'samples'):
                                get(send, view, path, selector)
                    assert not any(calls.values())
                reference.consumer.legacy.wait_for(lambda: bool(list(tmp_path.glob('attempt-*.private.json'))), process, timeout=30)
            worker_exit = process.returncode
            assert worker_exit == 0 and errors == [''] and events[-1]['event'] == 'stopped'
            attempts = reference.proofs(tmp_path)
            assert attempts[-1]['state'] == 'succeeded'
            with monkeypatch.context() as patch:
                calls = reference.progress.forbid(patch)
                status, raw = send('GET', path)
                assert status == 200
                selected = json.loads(raw)['result']
                assert selected['status'] == 'completed'
                farm = json.loads(c.raw)['farm']
                query = reference.current.JointCropClimateCurrentQuery(c.worker.results)
                expected = query.read('tenant-1', selected['result_id'], farm)
                status, terminal = send('GET', '/v1/crop-climate-joint-research-results/' + selected['result_id'] + '?' + urlencode(farm))
                assert status == 200 and terminal == expected
                terminal_matches = True
                for observation in observations:
                    if observation['status'] != 200 or observation['view'] == 'summary':
                        continue
                    value = json.loads(observation['wire_utf8'])
                    assert value['job']['state'] == 'simulating' and value['prefix_status'] == 'accepted'
                    records = value['page']['records']
                    saved = json.loads(query.read('tenant-1', selected['result_id'], farm,
                        view=observation['view'], offset=0, limit=max(1, len(records))))
                    original = saved['page']['records'][:len(records)]
                    assert prefix.storage._canonical(records) == prefix.storage._canonical(original)
                    matches.append({'view': observation['view'], 'selector': observation['selector'],
                        'records': len(records), 'canonical_records_sha256': sha256(prefix.storage._canonical(records)).hexdigest(),
                        'original_terminal_records_sha256': sha256(prefix.storage._canonical(original)).hexdigest(),
                        'same_binary64_and_UTC': True})
                assert not any(calls.values())
        assert any(row['view'] == 'samples' and row['records'] > 0 for row in matches)
        assert any(a['view'] == 'events' and b['view'] == 'samples' and a['selector'] == b['selector']
            for a in matches for b in matches)
    finally:
        reference.save('unpaused-forward-public-pages', {'reader_version': prefix.VERSION,
            'actual_SCRAM_reader_and_worker': True, 'verified_TLS': True,
            'worker_pause_or_delay': False, 'API_or_worker_tracing': False,
            'worker_chunk_budget': 8, 'selector_origin': 'public_accepted_summary_only',
            'observations': observations, 'matches': matches, 'worker_exit': worker_exit,
            'original_terminal_summary_matches': terminal_matches,
            'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest()})
        pack.unlink()
        (tmp_path / 'proof.private.json').unlink()


@reference.LOGIN
@pytest.mark.parametrize('setup', ['hold'], indirect=True)
def test_unpaused_forward_hold(prefix_native, tmp_path, monkeypatch):
    reference.test_actual_unpaused_worker_prefix_to_original_terminal(prefix_native, tmp_path, monkeypatch, 'hold')


@reference.LOGIN
def test_unpaused_forward_cancel(prefix_native, tmp_path, monkeypatch):
    reference.test_actual_unpaused_cancel_closes_prefix(prefix_native, tmp_path, monkeypatch)
