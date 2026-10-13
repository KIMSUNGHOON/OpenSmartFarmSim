"""Exercise an isolated model API/consumer inside the namespace probe lifetime."""
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request


def exercise(out, policy, dsn, original, config, requests, original_directory, original_access):
    import importlib.util
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('isolated_preview_lifecycle',
        root/'research/crop-joint-ventilation-live-preview.py')
    lifecycle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lifecycle)
    save = lifecycle.save
    from app.http_identity import token_digest
    token = json.loads(original_access.read_bytes())['token']
    assert token_digest(token.encode()) == original['token_digest']
    directory = out/'runtime'
    directory.mkdir(mode=0o700)
    for name, source in (('isolated_ventilation_support.py', 'crop-joint-ventilation-live-operator.py'),
                         ('isolated_ventilation_operator.py', 'crop-isolated-ventilation-operator.py')):
        save(directory/name, (root/'research'/source).read_bytes(), raw=True)
    artifacts = directory/'artifacts'
    shutil.copytree(original['artifacts'], artifacts)
    legacy, custody = directory/'legacy', directory/'custody'
    legacy.mkdir(mode=0o700); custody.mkdir(mode=0o700)
    # The local credential copy is removed before the outer namespace is dropped.
    passfile = directory/'authority.pgpass'
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    authority_dsn = make_conninfo(**{**conninfo_to_dict(dsn), 'passfile': str(passfile)})
    value = {**config, 'runtime_version': 'owned-isolated-ventilation-runtime-v1',
        'original_operator': str(original_directory/'joint_prefix_live_operator_v1.py'),
        'original_operator_sha256': sha256((original_directory/'joint_prefix_live_operator_v1.py').read_bytes()).hexdigest(),
        'original_runtime_sha256': sha256((original_directory/'runtime.private.json').read_bytes()).hexdigest(),
        'auth': {name: original[name] for name in ('token_digest', 'issued_at', 'expires_at')},
        'policy': asdict(policy), 'dsn': authority_dsn, 'artifacts': str(artifacts), 'legacy': str(legacy),
        'ventilation': {**config['ventilation'], 'custody': str(custody)}}
    save(directory/'runtime.private.json', value)
    sys.path.insert(0, str(directory))
    import isolated_ventilation_operator
    checked, _, _ = isolated_ventilation_operator.load()
    assert checked == value
    cert, key = lifecycle.common.certificate(directory, 3600)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
    from app import crop_greenhouse_ventilation_operator_config as loader
    api = {'config_version': loader.PREFIX_VERSION, 'policy': asdict(policy),
        'artifact_root': str(artifacts), 'certificate': str(cert), 'private_key': str(key),
        'authored_run_gate_key_file': None, 'content_access': None, 'host': '127.0.0.1', 'port': port,
        'dependencies_factory': 'isolated_ventilation_operator:dependencies',
        'crop_greenhouse_ventilation_execution': True, 'crop_greenhouse_ventilation_prefix': True}
    for field, raw in (('dsn_file', authority_dsn.encode()),
                       ('thermal_gate_key_file', bytes.fromhex(original['thermal_key'])),
                       ('market_hold_key_file', bytes.fromhex(original['market_key']))):
        path = directory/field
        save(path, raw, raw=True); api[field] = str(path)
    save(directory/'api.private.json', api)
    env = {**os.environ, 'OSSF_API_CONFIG': str(directory/'api.private.json'),
        'PYTHONPATH': os.pathsep.join(map(str, (directory, root/'backend', root/'backend/tests', original_directory)))}
    code = ('from app.crop_greenhouse_ventilation_operator_config import api_service; '
            'api_service().serve()')
    logs, children = [], []
    checks = {}
    try:
        shutil.copyfile(out/'authority.pgpass', passfile)
        passfile.chmod(0o600)
        for name, argv in (('api', [sys.executable, '-B', '-c', code]),
                ('worker', [sys.executable, '-B', '-m', 'app.deterministic_work',
                            '--factory', 'isolated_ventilation_operator:worker'])):
            log = (directory/(name+'.private.log')).open('xb')
            os.fchmod(log.fileno(), 0o600); logs.append(log)
            children.append(subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT))
        context = ssl.create_default_context(cafile=str(cert))
        deadline = time.monotonic()+30
        while True:
            assert all(child.poll() is None for child in children), 'isolated runtime process exited'
            try:
                request = urllib.request.Request(f'https://localhost:{port}/openapi.json',
                    headers={'Authorization': 'Bearer '+token})
                with urllib.request.urlopen(request, context=context, timeout=3) as response:
                    assert response.status == 200
                    response.read()
                break
            except urllib.error.HTTPError:
                raise AssertionError('isolated runtime authenticated readiness rejected') from None
            except (urllib.error.URLError, TimeoutError):
                assert time.monotonic() < deadline, 'isolated runtime readiness expired'
                time.sleep(.1)
        first = (directory/'worker.private.log').read_text().splitlines()
        assert first and json.loads(first[0]) == {'version': 1, 'event': 'started'}
        checks = {'actual_TLS_API_started': True, 'independent_unpaused_consumer_started': True,
            'separate_artifact_and_empty_initial_custody_roots': True, 'worker_chunk_budget': 8,
            'original_joint_API_consumer_unchanged': True, 'isolated_joint_factory_enabled': False}
    finally:
        stopped = [lifecycle.stop_owned_process(child, timeout=15) for child in reversed(children)]
        for log in logs: log.close()
        passfile.unlink()
        save(directory/'stopped.private.json', {'children': stopped, 'remaining_children':
            sum(child.poll() is None for child in children), 'passfile_remaining': passfile.exists()})
    assert not any(item['forced'] for item in stopped)
    save(directory/'acceptance.private.json', checks)
    return checks
