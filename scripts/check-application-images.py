"""Build and exercise application images in a disposable Docker environment."""

import ast
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import ssl
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]


def command(*args, input=None, timeout=600, check=True):
    result = subprocess.run(args, input=input, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode:
        # Build inputs are public source; all other output may describe private fixtures.
        if args[:2] == ('docker', 'build'):
            print(result.stdout, end='')
            print(result.stderr, end='')
        raise RuntimeError('application_image_check_failed')
    return result


def event(name, **values):
    print(json.dumps({'check': name, **values}, sort_keys=True), flush=True)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run_options(name):
    return ['docker', 'run', '--name', name, '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--pids-limit', '64', '--memory', '768m',
            '--cpus', '1', '--tmpfs', '/tmp:rw,noexec,nosuid,size=32m,mode=1777']


def private_directory(path, uid, files):
    path.mkdir(mode=0o700)
    for source, name in files:
        shutil.copyfile(source, path / name)
        (path / name).chmod(0o600)
    command('sudo', 'chown', '-R', f'{uid}:{uid}', str(path))


def certificates(directory):
    command('openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
            '-subj', '/CN=Image Test CA', '-keyout', str(directory / 'ca.key'),
            '-out', str(directory / 'ca.pem'))
    (directory / 'ca.key').chmod(0o600)
    for name, san in [('web', 'DNS:localhost,IP:127.0.0.1'),
                      ('api', 'DNS:localhost,IP:127.0.0.1'),
                      ('wrong-name', 'DNS:unrelated.invalid')]:
        command('openssl', 'req', '-newkey', 'rsa:2048', '-nodes', '-subj', f'/CN={name}',
                '-keyout', str(directory / f'{name}.key'), '-out', str(directory / f'{name}.csr'))
        (directory / f'{name}.key').chmod(0o600)
        extension = directory / f'{name}.ext'
        extension.write_text(f'subjectAltName={san}\nextendedKeyUsage=serverAuth\n')
        command('openssl', 'x509', '-req', '-in', str(directory / f'{name}.csr'),
                '-CA', str(directory / 'ca.pem'), '-CAkey', str(directory / 'ca.key'),
                '-CAcreateserial', '-days', '1', '-extfile', str(extension),
                '-out', str(directory / f'{name}.pem'))


def image_checks(directory, prefix, images):
    context = directory / 'context'
    context.mkdir()
    tracked = command('git', '-C', str(ROOT), 'ls-files', '-z').stdout.split('\0')
    for name in filter(None, tracked):
        source = ROOT / name
        if source.is_file():
            target = context / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    poison = ['.env.image-probe', 'backend/app/private/probe.py',
              'backend/app/credentials/probe.py', 'backend/app/probe.key',
              'contracts/image-probe.json', 'fixtures/image-probe.json',
              'LICENSES/image-probe.txt',
              'web/src/private/probe.ts', 'web/src/probe.pem',
              'web/src/assets/crop-design/private/probe.svg',
              'web/src/assets/crop-design/image-probe.svg',
              'web/src/assets/crop-design/image-probe.webp',
              'web/demo/private/probe.ts',
              'web/public/licenses/private/probe.txt', 'web/node_modules/probe.js',
              'data/raw/probe.json', '.codex/probe.json']
    for name in poison:
        path = context / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('excluded synthetic build-boundary probe\n')
    exported = directory / 'exported'
    command('docker', 'build', '--quiet', '--file', '-', '--output',
            f'type=local,dest={exported}', str(context), input='FROM scratch\nCOPY . /context\n')
    for name in poison:
        assert not (exported / 'context' / name).exists(), f'build_exclusion_failed:{name}'
    assert (exported / 'context/backend/app/api_runtime.py').is_file()
    assert (exported / 'context/fixtures/crop-growth-reference-parameters-v1.json').is_file()
    fruit_profile = 'fixtures/crop-fruit-transport-reference-parameters-v1.json'
    assert digest(exported / 'context' / fruit_profile) == digest(ROOT / fruit_profile)
    cohort_profile = 'fixtures/crop-fruit-cohort-reference-parameters-v1.json'
    assert digest(exported / 'context' / cohort_profile) == digest(ROOT / cohort_profile)
    assert (exported / 'context/LICENSES/GreenLight-BSD-3-Clause-Clear.txt').is_file()
    assert not (exported / 'context/fixtures/crop-growth-reference-cases-v1.json').exists()
    assert not (exported / 'context/fixtures/crop-fruit-transport-reference-cases-v1.json').exists()
    assert not (exported / 'context/fixtures/crop-fruit-cohort-reference-cases-v1.json').exists()
    assert (exported / 'context/web/src/assets/cutout-15-b6376be1ea78.png').is_file()
    for name in ['crop-research-leaf.png', 'crop-result-empty.png', 'crop-design/leaf.svg',
                 'crop-design/plant-seedling.svg', 'crop-design/clock.svg',
                 'crop-design/line-chart.svg', 'crop-design/database.svg',
                 'crop-design/magnifying-glass.svg', 'crop-design/research-hold.png',
                 'crop-design/crop-research-clean-plate.webp']:
        assert digest(exported / 'context/web/src/assets' / name) == digest(ROOT / 'web/src/assets' / name)
    assert digest(exported / 'context/web/e2e/crop-fixture.ts') == digest(ROOT / 'web/e2e/crop-fixture.ts')
    assert not (exported / 'context/web/demo').exists()
    event('actual_build_context', excluded_probes=len(poison),
          fruit_transport_profile_sha256=digest(exported / 'context' / fruit_profile),
          fruit_cohort_profile_sha256=digest(exported / 'context' / cohort_profile))
    for service in ('backend', 'web'):
        image = f'{prefix}-{service}:test'
        images[service] = image
        event('image_build_started', service=service)
        command('docker', 'build', '--progress', 'plain', '--target', f'{service}-app', '--file',
                str(context / service / 'Dockerfile'), '--tag', image, str(context))
        info = json.loads(command('docker', 'image', 'inspect', image).stdout)[0]
        expected_uid = '11001:11010' if service == 'backend' else '11002:11002'
        assert info['Config']['User'] == expected_uid
        event('image_built', service=service, image_id=info['Id'], uid=expected_uid)


def backend_checks(image, name, containers):
    containers.append(name)
    tree = ast.parse((ROOT / 'backend/app/thermal_publisher.py').read_text())
    code_files = next(ast.literal_eval(node.value) for node in tree.body
                      if isinstance(node, ast.Assign) and any(
                          isinstance(target, ast.Name) and target.id == 'CODE_FILES'
                          for target in node.targets))
    code = {name: digest(ROOT / name) for name in code_files}
    expected = [sha256(json.dumps(code, sort_keys=True, separators=(',', ':'),
                                ensure_ascii=False, allow_nan=False).encode()).hexdigest(),
                digest(ROOT / 'backend/uv.lock')]
    probe = '''import importlib.util, json, os, pathlib, shutil
from hashlib import sha256
from app.api_runtime import ApiRuntime
from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.deterministic_work import DeterministicWorkerLoop
from app.thermal_publisher import runtime_digests
assert (os.geteuid(), os.getegid()) == (11001, 11010)
assert importlib.util.find_spec('pytest') is None
assert shutil.which('uv') is None
assert not pathlib.Path('/app/backend/tests').exists()
assert pathlib.Path('/app/.venv/bin/python').exists()
assert pathlib.Path('/app/LICENSE').is_file()
assert pathlib.Path('/app/fixtures/manifest-v2.json').is_file()
crop_profile = ReferenceParameters(pathlib.Path('/app/fixtures/crop-growth-reference-parameters-v1.json').read_bytes())
assert crop_profile.profile_id == 'vanthoor-greenlight-reference-rates-v1'
fruit_profile = ReferenceFruitTransportParameters(pathlib.Path('/app/fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes())
assert fruit_profile.profile_id == 'vanthoor-fruit-transport-reference-v1'
assert fruit_profile.stages == 50
cohort_profile = ReferenceFruitCohortParameters(pathlib.Path('/app/fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes())
assert cohort_profile.profile_id == 'vanthoor-explicit-entry-cohort-reference-v1'
assert cohort_profile.stages == 50
assert sha256(pathlib.Path('/app/LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()).hexdigest() == '96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a'
try:
    pathlib.Path('/app/backend/image-write-probe').write_text('probe')
except OSError:
    pass
else:
    raise AssertionError('writable_runtime_root')
print(json.dumps(runtime_digests('/app')))
'''
    options = run_options(name)
    actual = command(*options, '--rm', '--network', 'none', image, 'python', '-c', probe)
    assert json.loads(actual.stdout) == expected
    rejected = command(*options, '--rm', '--network', 'none', image, check=False)
    assert rejected.returncode == 2 and not rejected.stdout
    assert json.loads(rejected.stderr) == {'version': 1, 'ok': False, 'code': 'api_startup_rejected'}
    event('backend_readonly_imports_and_closed_startup', code_sha256=expected[0],
          environment_sha256=expected[1],
          fruit_cohort_profile_sha256=digest(ROOT / 'fixtures/crop-fruit-cohort-reference-parameters-v1.json'))


def https(origin, context, path, headers=None):
    request = urllib.request.Request(origin + path, headers=headers or {})
    try:
        with urllib.request.urlopen(request, context=context, timeout=5) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as response:
        return response.code, dict(response.headers), response.read()


def web_checks(images, directory, prefix, containers):
    containers.extend([prefix + '-web-check', prefix + '-missing-tls'])
    command(*run_options(prefix + '-web-check'), '--rm', '--network', 'none',
        '--entrypoint', 'sh', images['web'], '-ceu',
        'if command -v node || command -v npm; then exit 1; fi; '
        'test ! -e /app/src; test ! -e /app/e2e; '
        'test ! -e /usr/share/nginx/html/demo; '
        'if grep -rqF --include="*.js" synthetic-demo-token-only /usr/share/nginx/html/assets; then exit 1; fi; '
        'test ! -e /usr/share/nginx/html/50x.html; '
        'if touch /usr/share/nginx/html/image-write-probe; then exit 1; fi')
    rejected = command(*run_options(prefix + '-missing-tls'), '--rm', '--network', 'none',
                       images['web'], check=False)
    assert rejected.returncode != 0
    private_directory(directory / 'web-tls', 11002,
        [(directory / 'web.pem', 'cert.pem'), (directory / 'web.key', 'key.pem'),
         (directory / 'ca.pem', 'api-ca.pem')])
    probe = '''import json, ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def do_GET(self):
        raw = json.dumps({'authorization': self.headers.get('Authorization'),
            'forwarded': self.headers.get('Forwarded'),
            'x_forwarded_for': self.headers.get('X-Forwarded-For')}).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store'); self.send_header('Content-Length', str(len(raw)))
        self.end_headers(); self.wfile.write(raw)
server = HTTPServer(('127.0.0.1', 8443), Handler)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('/run/probe/cert.pem', '/run/probe/key.pem')
server.socket = context.wrap_socket(server.socket, server_side=True)
server.serve_forever()
'''
    for leaf, expected_status in [('api', 200), ('wrong-name', 502)]:
        tls = directory / f'{leaf}-tls'
        private_directory(tls, 11001, [(directory / f'{leaf}.pem', 'cert.pem'),
                                     (directory / f'{leaf}.key', 'key.pem'),
                                     (directory / 'ca.pem', 'ca.pem')])
        upstream, web = f'{prefix}-{leaf}-upstream', f'{prefix}-{leaf}-web'
        containers.extend([upstream, web])
        command(*run_options(upstream), '-d', '--publish', '127.0.0.1::8444',
                '--mount', f'type=bind,src={tls},dst=/run/probe,readonly',
                images['backend'], 'python', '-c', probe)
        server_name = 'localhost' if leaf == 'api' else 'unrelated.invalid'
        readiness = f'''import socket, ssl, time
context = ssl.create_default_context(cafile='/run/probe/ca.pem')
for attempt in range(30):
    try:
        with socket.create_connection(('127.0.0.1', 8443), timeout=2) as connection:
            with context.wrap_socket(connection, server_hostname={server_name!r}) as secured:
                secured.sendall(b'GET /v1/probe HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n')
                assert b'200' in secured.recv(4096).split(b'\\r\\n')[0]
        break
    except OSError:
        if attempt == 29: raise
        time.sleep(0.1)
'''
        command('docker', 'exec', upstream, 'python', '-c', readiness, timeout=15)
        command(*run_options(web), '-d', '--network', f'container:{upstream}',
                '--mount', f'type=bind,src={directory / "web-tls"},dst=/run/operator/web,readonly',
                images['web'])
        port = command('docker', 'port', upstream, '8444/tcp').stdout.strip().rsplit(':', 1)[1]
        origin = f'https://127.0.0.1:{port}'
        ca = ssl.create_default_context(cafile=str(directory / 'ca.pem'))
        deadline = time.monotonic() + 30
        while True:
            try:
                status, headers, body = https(origin, ca, '/')
                break
            except (OSError, urllib.error.URLError):
                if time.monotonic() >= deadline:
                    raise RuntimeError('web_tls_start_failed') from None
                time.sleep(0.25)
        assert status == 200 and headers['Cache-Control'] == 'no-store'
        assert b'<div id="root">' in body
        asset = re.search(rb'"(/assets/[^" ]+\.js)"', body).group(1).decode()
        status, headers, asset_body = https(origin, ca, asset)
        assert status == 200 and asset_body and 'immutable' in headers['Cache-Control']
        assert https(origin, ca, '/assets/not-present.js')[0] == 404
        for notice in (ROOT / 'web/public/licenses').glob('*.txt'):
            status, _, content = https(origin, ca, '/licenses/' + notice.name)
            assert status == 200 and sha256(content).hexdigest() == digest(notice)
        status, headers, body = https(origin, ca, '/v1/image-proxy-probe',
            {'Authorization': 'Bearer synthetic-image-probe', 'Forwarded': 'for=untrusted',
             'X-Forwarded-For': 'untrusted'})
        assert status == expected_status
        if status == 200:
            assert json.loads(body) == {'authorization': 'Bearer synthetic-image-probe',
                                       'forwarded': None, 'x_forwarded_for': None}
            assert headers['Cache-Control'] == 'no-store'
        # This upstream is an explicit HTTPS fixture, not the product API or CLI.
        event('web_static_tls_and_fixture_proxy', certificate=leaf, proxy_status=status)
        command('docker', 'stop', '--time', '5', web, upstream)
        command('docker', 'rm', web, upstream)
        containers.remove(web)
        containers.remove(upstream)


def main():
    prefix = 'ossf-image-' + uuid4().hex[:12]
    directory = Path(tempfile.mkdtemp(prefix=prefix + '-'))
    containers, images = [], {}
    try:
        command('docker', 'version')
        image_checks(directory, prefix, images)
        backend_checks(images['backend'], prefix + '-backend-check', containers)
        certificates(directory)
        web_checks(images, directory, prefix, containers)
    finally:
        cleanup_ok = True
        for container in containers:
            if command('docker', 'container', 'inspect', container, check=False).returncode == 0:
                cleanup_ok &= command('docker', 'rm', '--force', container, check=False).returncode == 0
        for image in images.values():
            if command('docker', 'image', 'inspect', image, check=False).returncode == 0:
                cleanup_ok &= command('docker', 'image', 'rm', image, check=False).returncode == 0
        command('sudo', 'chown', '-R', f'{os.getuid()}:{os.getgid()}', str(directory))
        shutil.rmtree(directory)
        assert cleanup_ok and not directory.exists(), 'application_image_cleanup_failed'
        event('cleanup', temporary_files_removed=True, containers_removed=True, image_tags_removed=True)


if __name__ == '__main__':
    main()
