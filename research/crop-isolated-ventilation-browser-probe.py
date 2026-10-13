"""Observe the isolated API/consumer through the existing product UI."""
from hashlib import sha256
from pathlib import Path
import gc
import json
import os
import socket
import time
import urllib.request
from uuid import uuid4


def verify(directory, operator, body, mode, save, lifecycle, root):
    from pytest import MonkeyPatch
    from test_crop_greenhouse_ventilation_execution_query import forbid
    from app.crop_greenhouse_ventilation_execution_query import VentilationExecutionQuery
    from app.crop_greenhouse_ventilation_current_query import VentilationCurrentQuery
    from app.crop_greenhouse_ventilation_result_schema import TABLE
    from psycopg import sql
    reference = lifecycle.module('isolated_frame_reference',
        root/'research/test_crop_greenhouse_ventilation_live_browser_reference.py')
    result = json.loads((directory/'browser-result.private.json').read_bytes())
    assert result['running_frames'] and not result['pageerrors'] and not result['test_pause']
    assert result['response_capture']['requests_added'] == 0
    bodies = []
    for reply in result['responses']:
        if reply.get('aborted'):
            assert reply['method'] == 'GET' and reply['abort_reason'] == 'AbortError'
            assert 'wire_file' not in reply
            continue
        raw = (directory/reply['wire_file']).read_bytes()
        assert sha256(raw).hexdigest() == reply['body_sha256']
        if reply['status'] == 200: bodies.append((reply, json.loads(raw)))
    for frame in result['running_frames']:
        pages = [page for wire, page in bodies if wire['path'].endswith('/prefix/samples')
                 and page['reference'] == frame['reference']]
        rows = [row for page in pages for row in page['page']['records'] if row['time']['at'] == frame['at']]
        assert rows and frame['at'].endswith('Z')
        assert any(wire['path'].endswith('/prefix') and page['prefix_status'] == 'accepted'
                   and page['job']['state'] == 'simulating'
                   and page['reference']['selector'] == frame['reference']['selector'] for wire, page in bodies)
        reference.check_frame(frame, rows[0])
    worker = operator.worker().worker
    with worker.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
        state = conn.execute(sql.SQL('SELECT state,attempt_count,lease_until FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(worker.jobs._table('jobs')), ('tenant-1', result['job_id'])).fetchone()
        assert state['attempt_count'] == 1 and state['lease_until'] is None
    with MonkeyPatch.context() as patch:
        calls = forbid(patch)
        outcome = json.loads(VentilationExecutionQuery(worker.checkpoints, worker.results).read('tenant-1', result['job_id']))
        assert outcome['G0_G4'] == 'not_assessed'
        if mode == 'cancel':
            assert state['state'] == 'canceled' and outcome['result'] is None
            assert result['cancel_accepted'] and result['scene_cleared']
            with worker.jobs.connect() as conn:
                assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE study_id=%s AND revision=%s')
                    .format(sql.Identifier(worker.jobs.schema, TABLE)), (body['study_id'], body['revision'])).fetchone()['n'] == 0
            sample_count = event_count = 0
        else:
            selected = outcome['result']
            assert state['state'] == ('succeeded' if mode == 'completed' else 'hold')
            assert selected['status'] == mode and selected['result_id'] == result['result_id']
            current = VentilationCurrentQuery(worker.results)
            samples = json.loads(current.read('tenant-1', selected['result_id'], body['farm'],
                view='samples', offset=0, limit=64))['page']['records']
            events = json.loads(current.read('tenant-1', selected['result_id'], body['farm'],
                view='events', offset=0, limit=8))['page']['records']
            for frame in result['running_frames']:
                reference.check_frame(frame, next(row for row in samples if row['time']['at'] == frame['at']))
            reference.check_frame(result['terminal_frame'], samples[0])
            reference.check_frame(result['restored_frame'], samples[0])
            assert result['reconnected'] and result['rights_cleared'] and result['rights_restored']
            wired = [row for wire, page in bodies if 'view=samples' in wire['query']
                     and isinstance(page.get('page'), dict) for row in page['page']['records']]
            assert all(row in wired for row in samples)
            sample_count, event_count = len(samples), len(events)
        assert not any(calls.values())
    case = {'state': state['state'], 'attempt_count': state['attempt_count'], 'job_id': result['job_id'],
        'result': outcome['result'], 'farm': body['farm'], 'running_lease_observed': True,
        'running_WebGL_frames': len(result['running_frames']), 'samples': sample_count, 'events': event_count,
        'actual_HTTP_original_storage_equal': True, 'original_values_UTC_table_chart_WebGL': True,
        'reconnect_and_current_rights_scene_restore': mode != 'cancel',
        'cancel_scene_removed_without_result': mode == 'cancel', 'test_checkpoint_pause': False,
        'read_calculation_and_write_calls': calls, 'pageerrors': 0,
        'browser_warning_count': len(result['warnings'])}
    save(directory/'acceptance.private.json', case)
    return case


def exercise(directory, operator, requests, children, save, modes, config_file,
             api_port, certificate, access, lifecycle):
    root = Path(__file__).resolve().parents[1]
    cfg = json.loads(config_file.read_bytes())
    assert set(cfg) == {'nginx', 'original_nginx_config', 'chromium', 'dist'}
    browser = lifecycle.module('isolated_browser_owner', root/'research/crop-ventilation-browser-supervisor.py')
    processes = lifecycle.module('isolated_browser_scope', root/'research/owned-research-process-scope.py')
    web = directory/'web'; web.mkdir(mode=0o700)
    original_config = Path(cfg['original_nginx_config']).read_text()
    old_dir = str(Path(cfg['original_nginx_config']).parent)
    for name in ('client-temp', 'proxy-temp', 'fastcgi-temp', 'uwsgi-temp', 'scgi-temp'):
        (web/name).mkdir(mode=0o700)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0)); web_port = probe.getsockname()[1]
    text = original_config.replace(old_dir, str(web)).replace('listen 127.0.0.1:5174;', f'listen 127.0.0.1:{web_port};')
    import re
    text, replaced = re.subn(r'(?m)^        root [^;]+;', '        root '+cfg['dist']+';', text)
    assert replaced == 1 and (Path(cfg['dist'])/'index.html').is_file()
    # Keep the original backend's TLS trust while the new paths use their own certificate.
    text = text.replace(str(web/'cert.pem'), str(Path(old_dir)/'cert.pem'))
    text = text.replace(str(web/'key.pem'), str(Path(old_dir)/'key.pem'))
    marker = '        location ~ ^/(?:v1(?:/|$)|openapi\\.json$) {'
    assert text.count(marker) == 1
    start, end = text.index(marker), text.index('\n        location = /development-status.json')
    block = text[start:end]
    routes = '        location ~ ^/v1/(?:crop-greenhouse-ventilation-(?:executions|research-results)(?:/|$)|jobs/[^/]+/crop-greenhouse-ventilation-execution(?:/|$)) {'
    added = block.replace(marker, routes).replace('https://127.0.0.1:8446', f'https://127.0.0.1:{api_port}')
    added = added.replace(str(Path(old_dir)/'cert.pem'), str(certificate))
    text = text[:start]+added+'\n'+text[start:]
    save(web/'nginx.conf', text.encode(), raw=True)
    log = (web/'process.private.log').open('xb'); os.fchmod(log.fileno(), 0o600)
    import subprocess
    child = subprocess.Popen([cfg['nginx'], '-p', str(web), '-c', str(web/'nginx.conf'), '-g', 'daemon off;'],
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    cases = {}
    finished = []
    try:
        deadline = time.monotonic()+15
        while True:
            assert child.poll() is None
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{web_port}/', timeout=2) as reply:
                    assert reply.status == 200; reply.read()
                break
            except OSError:
                assert time.monotonic() < deadline; time.sleep(.1)
        for mode in modes:
            body = json.loads((requests/(mode+'.json')).read_bytes())
            body.update(study_id='isolated-browser-'+uuid4().hex, revision=mode+'-v1')
            request = directory/(mode+'.request.private.json'); save(request, body)
            evidence = browser.BrowserEvidence(directory/('browser-'+mode), request=request, access=access,
                rights=Path(operator.load()[0]['ventilation']['rights_file']),
                driver=root/'research/crop-isolated-ventilation-cdp-reference.mjs',
                chromium=Path(cfg['chromium']), mode=mode, origin=f'http://127.0.0.1:{web_port}')
            gc.collect()
            import ctypes
            ctypes.CDLL(None).malloc_trim(0)
            driver = lifecycle.module('isolated_pipe_browser', root/'research/crop-isolated-ventilation-pipe-reference.py')
            terminal = driver.exercise(evidence, processes=processes, supervisor_class=browser.BrowserChild)
            assert all(item.poll() is None for item in (*children, child))
            assert terminal['actual_child_exit'] == 0 and terminal['reason'] is None
            assert not terminal['owned_remaining'] and not terminal['forced_kill']
            assert terminal['current_rights_restored'] and terminal['cleanup_error_type'] is None
            finished.append((evidence.directory, body, mode))
        for evidence_directory, body, mode in finished:
            cases[mode] = verify(evidence_directory, operator, body, mode, save, lifecycle, root)
    finally:
        stopped = lifecycle.stop_owned_process(child, timeout=15)
        log.close(); save(web/'stopped.private.json', stopped)
    assert not stopped['forced'] and stopped['exit'] == 0
    save(directory/'browser-routing.private.json', {'separate_local_staging_origin': True,
        'model_paths_use_isolated_TLS_backend': True, 'other_paths_use_original_TLS_backend': True,
        'existing_user_nginx_config_unchanged': True, 'same_API_worker_across_cases': True,
        'staging_nginx_clean_exit': True, 'original_consumers_paused': False})
    return cases
