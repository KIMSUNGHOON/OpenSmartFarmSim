"""Actual bounded loopback HTTPS reads from an original preserved synthetic harvest."""
from contextlib import contextmanager, ExitStack
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import socket
import ssl
import sys
import threading
import time
from unittest.mock import patch

VERSION = 'owned-harvest-api-cost-v2'
MAX_BYTES = 2 * 1024**2
MAX_SECONDS = 30


def need(value):
    if not value:
        raise ValueError('harvest_api_cost_rejected')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def load_storage(source_root, code_sha256):
    root = Path(source_root).resolve(strict=True)
    path = root / 'research/crop-harvest-storage-preservation.py'
    need(sha256(path.read_bytes()).hexdigest() == code_sha256)
    backend = root / 'backend'
    for name, value in tuple(sys.modules.items()):
        if name == 'app' or name.startswith('app.'):
            origin = getattr(value, '__file__', None)
            if origin is not None:
                need(Path(origin).resolve().is_relative_to(backend / 'app'))
            else:
                paths = tuple(getattr(value, '__path__', ()))
                need(paths and all(Path(p).resolve() == backend / 'app' for p in paths))
        elif name.startswith('test_') and getattr(value, '__file__', None):
            need(Path(value.__file__).resolve().is_relative_to(backend / 'tests'))
    # A namespace package otherwise includes other checkouts present on PYTHONPATH.
    sys.path[:] = [str(backend), str(backend / 'tests'), *[
        p for p in sys.path if not (Path(p or os.getcwd()).resolve() / 'app').is_dir()
        and Path(p or os.getcwd()).resolve() != backend / 'tests']]
    return module('owned_harvest_cost_storage', path)


def compatible_dependencies(saved, original_root, runtime_root):
    original_root = Path(original_root).resolve(strict=True); runtime_root = Path(runtime_root).resolve(strict=True)
    changed = []
    for name, expected in saved['dependencies'].items():
        path = Path(name).resolve(strict=True); relative = path.relative_to(original_root)
        need(sha256(path.read_bytes()).hexdigest() == expected)
        target = (runtime_root / relative).resolve(strict=True)
        need(target.is_relative_to(runtime_root))
        actual = sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            need(relative.as_posix() == 'backend/app/crop_harvest_current_query.py')
            changed.append(relative.as_posix())
    return changed


def original_manifest(original_root, runtime_root, manifest, digest, directory):
    """Validate old absolute custody paths in a fresh exact-source Python, never another CLI."""
    import subprocess
    original_root = Path(original_root).resolve(strict=True); runtime_root = Path(runtime_root).resolve(strict=True)
    path = original_root / 'research/crop-harvest-storage-preservation.py'
    original_code = sha256(path.read_bytes()).hexdigest()
    need(sha256((runtime_root / path.relative_to(original_root)).read_bytes()).hexdigest() == original_code)
    output = directory / 'original-checked-manifest.private.json'
    script = '''import importlib.util,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('owned_original_manifest_check',sys.argv[1])
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
storage=tool.load_storage(Path(sys.argv[2]),sys.argv[3])
storage.checked(Path(sys.argv[4]),sys.argv[5])
storage.backup.write(Path(sys.argv[6]),storage.runtime.private_bytes(Path(sys.argv[4])))
print(sys.argv[5],flush=True)
'''
    argv = [sys.executable, '-B', '-c', script, str(Path(__file__).resolve()), str(original_root),
            original_code, str(manifest), digest, str(output)]
    sites = [str(Path(p).resolve()) for p in sys.path if Path(p or os.getcwd()).name in ('site-packages', 'dist-packages')]
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'MALLOC_ARENA_MAX': '2',
           'PYTHONPATH': os.pathsep.join([str(original_root / 'backend'), str(original_root / 'backend/tests'), *sites])}
    started = time.monotonic(); timed_out = False
    with (directory / 'original-validator.private.log').open('xb') as log:
        os.fchmod(log.fileno(), 0o600)
        try:
            result = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=log, timeout=60, check=False)
            exit_code, stdout = result.returncode, result.stdout
        except subprocess.TimeoutExpired as error:
            timed_out = True; exit_code = None; stdout = error.stdout or b''
    invocation = {'argv': argv, 'actual_exit_code': exit_code, 'timed_out': timed_out,
        'wall_seconds': time.monotonic() - started, 'stdout_sha256': sha256(stdout).hexdigest(),
        'stderr_sha256': sha256((directory / 'original-validator.private.log').read_bytes()).hexdigest()}
    operator_file(directory / 'original-validator-command.private.json', json.dumps(invocation, sort_keys=True).encode())
    need(not timed_out and exit_code == 0 and stdout == (digest + '\n').encode())
    raw = output.read_bytes(); need(sha256(raw).hexdigest() == digest)
    saved = json.loads(raw); changed = compatible_dependencies(saved, original_root, runtime_root)
    receipt = {'version': 'owned-original-harvest-reader-compatibility-v1', 'scope': 'owned_synthetic_only',
        'original_manifest_sha256': digest, 'original_storage_code_sha256': original_code,
        'original_source_root': str(original_root), 'runtime_source_root': str(runtime_root),
        'changed_dependency_relative_paths': changed, 'validator': invocation,
        'original_manifest_modified': False, 'new_result_or_proof_issued': False, 'G0_G4': 'not_assessed'}
    operator_file(directory / 'reader-compatibility.private.json', json.dumps(receipt, sort_keys=True).encode())
    return saved


class Observation:
    """Hash actual outgoing ASGI bodies independently of the TLS client."""
    def __init__(self, app):
        self.app = app; self.responses = []; self.active = self.peak = 0
        self.condition = threading.Condition()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not scope['path'].startswith('/v1/crop-harvest-research-results/'):
            return await self.app(scope, receive, send)
        item = {'status': None, 'bytes': 0, 'complete': False,
                'target': scope['path'] + '?' + scope['query_string'].decode('ascii')}
        digest = sha256(); start = time.monotonic()
        with self.condition:
            self.active += 1; self.peak = max(self.peak, self.active)
        async def observed(message):
            if message['type'] == 'http.response.start': item['status'] = message['status']
            if message['type'] == 'http.response.body':
                raw = message.get('body', b''); item['bytes'] += len(raw); digest.update(raw)
            await send(message)
            if message['type'] == 'http.response.body' and not message.get('more_body', False):
                item['complete'] = True
        try:
            return await self.app(scope, receive, observed)
        finally:
            item.update(seconds=time.monotonic() - start, sha256=digest.hexdigest())
            with self.condition:
                self.responses.append(item); self.active -= 1; self.condition.notify_all()

    def take(self, index, target):
        with self.condition:
            need(self.condition.wait_for(lambda: len(self.responses) > index, timeout=5))
            need(self.active == 0 and len(self.responses) == index + 1 and self.responses[index]['target'] == target)
            return dict(self.responses[index])


class ReadHold(ValueError):
    def __init__(self, reason, *, seconds, size):
        super().__init__('harvest_api_read_hold')
        self.report = {'reason': reason, 'seconds': seconds, 'bytes': size}


def request(port, certificate, target, token):
    """The whole TLS/body deadline is enforced across every receive, without retries."""
    import http.client
    start = time.monotonic(); raw = bytearray()
    response = transport = None
    client = http.client.HTTPSConnection('127.0.0.1', port, timeout=MAX_SECONDS,
        context=ssl.create_default_context(cafile=str(certificate)))
    def remaining(*, update_socket=True):
        left = MAX_SECONDS - (time.monotonic() - start)
        if left <= 0: raise TimeoutError()
        if update_socket:
            if transport is not None: transport.settimeout(left)
            else: client.timeout = left
    try:
        remaining(); client.connect(); transport = client.sock; remaining()
        client.request('GET', target, headers={'Authorization': 'Bearer ' + token.decode(), 'Connection': 'close'})
        remaining(); response = client.getresponse()
        while True:
            remaining()
            block = response.read1(min(65536, MAX_BYTES + 1 - len(raw)))
            raw.extend(block)
            if len(raw) > MAX_BYTES:
                raise ReadHold('response_bytes', seconds=time.monotonic() - start, size=len(raw))
            if not block or response.isclosed(): break
        remaining(update_socket=False)
        return {'raw': bytes(raw), 'status': response.status,
                'headers': {k.lower(): v for k, v in response.getheaders()}, 'seconds': time.monotonic() - start}
    except (TimeoutError, socket.timeout):
        raise ReadHold('request_timeout', seconds=time.monotonic() - start, size=len(raw)) from None
    except ReadHold:
        raise
    except Exception:
        raise ReadHold('transport_failed', seconds=time.monotonic() - start, size=len(raw)) from None
    finally:
        if response is not None: response.close()
        client.close()


@contextmanager
def serving(service):
    api = service.server(); observed = Observation(api.config.app); api.config.app = observed
    thread = threading.Thread(target=api.run, daemon=True); thread.start()
    try:
        deadline = time.monotonic() + 15
        while not api.started:
            need(thread.is_alive() and time.monotonic() < deadline); time.sleep(.05)
        port = api.servers[0].sockets[0].getsockname()[1]
        yield observed, port
    finally:
        with observed.condition:
            drained = observed.condition.wait_for(lambda: observed.active == 0, timeout=90)
        api.should_exit = True; thread.join(timeout=15)
        need(drained and not thread.is_alive())


def certificate(backup, directory):
    import ipaddress
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    key = ec.generate_private_key(ec.SECP256R1()); now = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Owned harvest loopback only')])
    value = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(hours=2)).add_extension(x509.SubjectAlternativeName([
            x509.IPAddress(ipaddress.ip_address('127.0.0.1')), x509.DNSName('localhost')]), False).sign(key, hashes.SHA256()))
    cert = directory / 'api-cert.pem'; secret = directory / 'api-key.pem'
    backup.write(cert, value.public_bytes(serialization.Encoding.PEM))
    backup.write(secret, key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                         serialization.NoEncryption()))
    return cert, secret


def operator_file(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def assemble(storage, saved, manifest_path, context, base, tokens, certificate, private_key, port):
    from app.api_runtime import ApiRuntime, ApiRuntimeConfig
    from app.runtime_roles import RuntimeLoginPolicy
    from app.http_identity import BearerGrant, BearerRegistry, token_digest
    from app.crop_result_store import READ_SCOPES
    from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
    from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
    from app.crop_cycle_farm_binding import CycleFarmBinding
    from app import crop_cycle_calculation_current_query as current
    from app import crop_cycle_calculation_result_store as result_storage
    from app import crop_cycle_result_store as legacy
    from app.crop_harvest_runtime_factory import load_harvest_current_query_factory, VERSION as reader_version
    from app.market_source_store import MarketSourceStore
    from app.research_registry import ResearchRegistry
    from app.owned_fixture_registry import OwnedFixtureRegistry
    from test_api_runtime import dependencies
    from test_crop_cycle_artifact import PROFILES, NOTICE
    backup = storage.backup; h = backup.runtime; base = Path(base); path = Path(manifest_path)
    parent_path = Path(saved['parent_backup'])
    original = backup.current_query(parent_path, saved['parent_backup_sha256'], context)
    doc = json.loads(h.private_bytes(context['config'])); h.load_runtime(context['config'], context['config_sha256'])
    def crop_factory(*, farm_authoring_service):
        authority = original.store.server.binding.input_authority
        binding = CalculationFarmBinding(farm_authoring_service, authority, input_rights=h.Rights(doc['rights_file']))
        server = result_storage.server.CalculationServerCustody(binding, Path(doc['server_directory']),
            input_resolver=h.Resolver(doc['input'], doc['resolver_version']), integrity_key=h.private_bytes(doc['keys']['server']))
        return result_storage.CalculationCycleCropResultStore(server, integrity_key=h.private_bytes(parent_path.parent/'DB-key.private'))
    def query_factory(*, result_store):
        authority = CalculationResultEvidenceAuthority(result_store.server.binding.input_authority,
            integrity_key=h.private_bytes(parent_path.parent/'result-key.private'), issuer_id='owned-parent-backup-result', key_id='result-v1')
        return current.CalculationCurrentCycleQuery(result_store, authority, evidence_resolver=original.evidence_resolver)
    class Unused:
        version = 'owned-harvest-full-api-unused-legacy-v1'
        def __call__(self, *_, **__):
            raise AssertionError('harvest API attempted legacy calculation')
    (base/'unused-legacy').mkdir(mode=0o700); (base/'job-artifacts').mkdir(mode=0o700)
    def legacy_factory(*, farm_authoring_service):
        binding = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE, input_rights=h.Rights(doc['rights_file']))
        server = legacy.server.CycleServerCustody(binding, base/'unused-legacy', input_resolver=Unused(), integrity_key=h.private_bytes(doc['keys']['server']))
        return legacy.CycleCropResultStore(server, integrity_key=h.private_bytes(parent_path.parent/'DB-key.private'))
    dsn_raw = h.private_bytes(path.parent/'reader-dsn.private')
    _, dsn, secret = backup.retarget({'dsn_file': 'old', 'static_sha256': {'old': sha256(dsn_raw).hexdigest()}},
        source_dsn_raw=dsn_raw, passfile_raw=h.private_bytes(path.parent/'reader.pgpass'), port=context['port'],
        dsn_file=base/'harvest-dsn.private', passfile_file=base/'harvest.pgpass')
    storage.pgpass(base/'harvest.pgpass', secret); operator_file(base/'harvest-dsn.private', dsn)
    operator_file(base/'harvest-key.private', h.private_bytes(path.parent/'harvest-key.private'))
    config = {'config_version': reader_version, 'policy': saved['policy'],
        'directory': saved['registry_directory'], 'reader_dsn_file': str(base/'harvest-dsn.private'),
        'integrity_key_file': str(base/'harvest-key.private')}
    operator_file(base/'harvest-reader.private.json', backup.canonical(config))
    harvest_factory = load_harvest_current_query_factory(base/'harvest-reader.private.json')
    cfg = ApiRuntimeConfig(policy=RuntimeLoginPolicy(**doc['policy']), dsn=h.private_bytes(doc['dsn_file']).decode(),
        artifact_root=base/'job-artifacts', certificate=certificate, private_key=private_key,
        thermal_gate_key=h.private_bytes(doc['keys']['thermal']), market_hold_key=h.private_bytes(doc['keys']['market']), port=port)
    def sources(*, principal_provider):
        return MarketSourceStore(cfg.dsn, cfg.policy.schema, principal_provider=principal_provider, runtime_identity=(cfg.policy, 'authority'))
    catalog = ResearchRegistry(h.private_bytes(doc['registry_file']), doc['registry_sha256']); now = datetime.now(timezone.utc)
    grants = tuple(BearerGrant(token_digest(tokens[name]), tenant, frozenset(scopes), now-timedelta(seconds=1), now+timedelta(hours=1))
        for name, tenant, scopes in [('owner', 'tenant-1', READ_SCOPES), ('denied', 'tenant-1', READ_SCOPES[:-1]), ('foreign', 'tenant-foreign', READ_SCOPES)])
    deps = dependencies(research_registry=catalog, bearer_registry=BearerRegistry(grants),
        owned_fixture_registry=OwnedFixtureRegistry(Path(doc['owned_fixture_root'])),
        owned_research_contexts={next(iter(catalog._scopes)): doc['owned_context_id']},
        market_scope_resolver=lambda *_: json.loads(h.private_bytes(doc['market_scope_file'])), market_source_factory=sources,
        crop_cycle_result_store_factory=legacy_factory, crop_cycle_calculation_result_store_factory=crop_factory,
        crop_cycle_calculation_current_query_factory=query_factory, crop_harvest_current_query_factory=harvest_factory)
    return ApiRuntime(cfg, deps), original, doc, cfg


def measure(runtime, saved, farm, tokens, cert, check):
    from app import crop_harvest_current_query as current, api_crop_harvest_replay as public
    codes = {'query_version': current.VERSION, 'query_code_sha256': current.CODE_SHA256,
             'query_dependency_sha256': current.DEPENDENCY_SHA256, 'projection_code_sha256': public.CODE_SHA256}
    found = []; denials = []
    with serving(runtime.service) as (observed, port):
        def probe(label, subject='owner', expected=200):
            target = check.target(saved, farm, label)
            need(observed.active == 0); index = len(observed.responses)
            response = None
            try:
                response = request(port, cert, target, tokens[subject]); emission = observed.take(index, target)
                need(response['status'] == emission['status'] == expected and emission['complete']
                     and emission['bytes'] == len(response['raw']) and emission['sha256'] == sha256(response['raw']).hexdigest()
                     and response['headers']['cache-control'] == 'no-store')
                if expected == 200:
                    found.append(check.reconcile(saved, farm, codes, label, emission=emission, **response))
                else:
                    denials.append({'subject': subject, 'status': expected, 'seconds': response['seconds'],
                                   'bytes': len(response['raw']), 'sha256': emission['sha256']})
            except (ReadHold, ValueError) as exc:
                hold = exc if isinstance(exc, ReadHold) else ReadHold('wire_or_stored_values',
                    seconds=response['seconds'] if response else 0, size=len(response['raw']) if response else 0)
                hold.report.update(label=label, subject=subject, completed=found,
                                   server_responses=observed.responses, peak_active_reads=observed.peak)
                raise hold from None
        for label in ('summary', 'first', 'last'): probe(label)
        probe('summary', 'denied', 403); probe('summary', 'foreign', 404)
        rights = runtime.harvest_crop_query.store.query.store.server.binding.input_rights
        original_call = type(rights).__call__
        def denied(instance, *args):
            return False if instance is rights else original_call(instance, *args)
        with patch.object(type(rights), '__call__', denied): probe('summary', 'owner', 422)
        probe('summary')
        need(observed.active == 0 and observed.peak == 1 and len(observed.responses) == 7)
    return {'HTTPS': found, 'HTTPS_denials': denials, 'peak_active_reads': observed.peak,
            'HTTPS_closed': True, 'shared_control_files_changed': False}


def run(source_root, storage_code_sha256, manifest, digest, directory, *, original_source_root=None):
    import secrets
    directory = Path(directory); directory.mkdir(mode=0o700)
    need(directory.stat().st_mode & 0o777 == 0o700)
    preverified = None if original_source_root is None else original_manifest(
        original_source_root, source_root, manifest, digest, directory)
    storage = load_storage(source_root, storage_code_sha256); backup = storage.backup; h = backup.runtime
    from crop_harvest_storage_preservation_smoke import source_inventory
    from test_api_crop_cycle_calculation_tls import fd_inventory
    from psycopg import sql
    # This code stays separate from the frozen storage helper and its dependency identities.
    check = module('owned_harvest_cost_http_check', Path(__file__).with_name('crop-harvest-http-reconciliation.py'))
    manifest = Path(manifest); saved = storage.checked(manifest, digest) if preverified is None else preverified
    parent = backup.checked(saved['parent_backup'], saved['parent_backup_sha256'])
    original_doc = json.loads(h.private_bytes(Path(saved['parent_backup']).parent / 'original-runtime.private'))
    roots = [manifest.parent, Path(original_doc['input']['directory']), Path(original_doc['server_directory']),
             Path(original_doc['rights_file']), Path(original_doc['principal_file'])]
    before = source_inventory(roots); fds = fd_inventory()
    cert, secret = certificate(backup, directory)
    tokens = {name: secrets.token_urlsafe(40).encode() for name in ('owner', 'denied', 'foreign')}
    def forbidden(*_, **__): raise AssertionError('harvest HTTPS read attempted calculation or proof')
    result = None; hold = None
    with ExitStack() as stack:
        stack.enter_context(backup.readonly_guard()); stack.enter_context(storage.read_guard())
        stack.enter_context(patch.object(h.engine.evidence.InputEvidenceAuthority, 'issue', forbidden))
        stack.enter_context(patch.object(storage.query.current.storage.server.CalculationServerCustody, 'advance', forbidden))
        context = stack.enter_context(storage.restored_storage(saved, directory / 'database'))
        runtime, original, doc, cfg = assemble(storage, saved, manifest, context, directory, tokens, cert, secret, 0)
        need(runtime.harvest_crop_query.store.query is runtime.calculation_cycle_crop_query
             and runtime.calculation_cycle_crop_query.store.jobs is runtime.jobs
             and runtime.calculation_cycle_crop_query.store.server.binding.farms is runtime.farm_authoring)
        endpoints = []
        for connect in (runtime.jobs.connect, runtime.harvest_crop_query.store._connection):
            with connect() as conn:
                need(conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256')
                endpoints.append((conn.info.host, conn.info.port, conn.info.dbname))
        need(endpoints[0] == endpoints[1])
        def counts():
            with runtime.jobs.connect() as conn:
                value = {name: conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                    runtime.jobs._table(name))).fetchone()['n'] for name in (
                        'jobs', 'job_events', 'crop_cycle_verified_research_results', 'thermal_g1_runs')}
            with runtime.harvest_crop_query.store._connection() as conn:
                value['harvest'] = conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                    sql.Identifier(saved['policy']['schema'], storage.registry.schema.TABLE))).fetchone()['n']
            return value
        before_counts = counts()
        try: result = measure(runtime, saved, parent['farm'], tokens, cert, check)
        except ReadHold as exc: hold = {**exc.report, 'HTTPS_closed': True}
        need(counts() == before_counts)
    need(source_inventory(roots) == before and not (directory / 'database/data/postmaster.pid').exists())
    deadline = time.monotonic() + 5
    while fd_inventory() != fds and time.monotonic() < deadline: time.sleep(.05)
    need(fd_inventory() == fds)
    report = {'version': VERSION, 'scope': 'owned_synthetic_only', 'accepted': hold is None,
        'hold': hold, 'measurement': result, 'same_actual_SCRAM_DB': True, 'DB_counts_before_after': [before_counts, before_counts],
        'original_sources_preserved': True, 'source_entries': len(before), 'FD_before_after': [len(fds), len(fd_inventory())],
        'owned_postmaster_absent': True, 'guarded_RHS_harvest_generation_registration_proof_calls': 0,
        'original_manifest_sha256': digest, 'storage_code_sha256': storage_code_sha256,
        'reader_compatibility_receipt_sha256': sha256((directory / 'reader-compatibility.private.json').read_bytes()).hexdigest()
            if preverified is not None else None,
        'realtime_progress': False, 'actual_crop_Runs': 0, 'G0_G4': 'not_assessed'}
    backup.write(directory / 'cost.private.json', backup.canonical(report))
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--storage-code-sha256', required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--original-source-root', type=Path)
    args = parser.parse_args()
    result = run(args.source_root, args.storage_code_sha256, args.manifest, args.sha256, args.directory,
                 original_source_root=args.original_source_root)
    print(json.dumps({'accepted': result['accepted'], 'scope': result['scope'], 'hold': result['hold']}), flush=True)
    raise SystemExit(0 if result['accepted'] else 2)


if __name__ == '__main__': main()
