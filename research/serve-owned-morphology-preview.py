"""Serve explicitly owned synthetic fixtures; this is not a production data factory."""
import argparse
from contextvars import ContextVar
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import signal
import stat
import sys
from threading import Event, Thread

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from app import crop_morphology_execution as execution
from app.crop_morphology_execution_query import MorphologyExecutionQuery
from app.crop_morphology_execution_worker import MorphologyExecutionWorker
from app.deterministic_work import DeterministicWorkerLoop
from app.content_access import ContentAccess
from app.http_identity import BearerGrant, BearerRegistry, PrincipalMiddleware, current_principal, token_digest
from app.https_service import HttpsApiService
from app.job_store import _open_directory_nofollow
from app import api_crop_morphology_execution as wire

# This fixture-only factory keeps the known synthetic market-context verifier outside app defaults.
from morphology_farm_fresh import (RuntimeLoginPolicy, JobStore, MarketSourceStore, ThermalRunStore, MarketHoldStore,
    _MarketSources, MarketCandidateStore, ResearchRegistry, OwnedResearchService, OwnedFixtureRegistry,
    FarmReplayScenarioService, ThermalScenarioStore, FarmAuthoringService, context_verifier)


def private_raw(value, maximum=2*1024**2):
    path = Path(value)
    if not path.is_absolute() or '..' in path.parts: raise ValueError('private input rejected')
    parent = _open_directory_nofollow(path.parent)
    try:
        info = os.fstat(parent)
        if info.st_uid != os.getuid() or info.st_mode & 0o077: raise ValueError('private directory rejected')
        fd = os.open(path.name, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC, dir_fd=parent)
        try:
            before = os.fstat(fd)
            if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid() or before.st_nlink != 1
                    or before.st_mode & 0o077 or not 0 < before.st_size <= maximum): raise ValueError('private file rejected')
            raw = bytearray()
            while len(raw) <= maximum:
                chunk = os.read(fd, min(65536, maximum+1-len(raw)))
                if not chunk: break
                raw.extend(chunk)
            after = os.fstat(fd)
            fields = ('st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
            if len(raw) != before.st_size or any(getattr(after,k) != getattr(before,k) for k in fields):
                raise ValueError('private file changed')
            return bytes(raw)
        finally: os.close(fd)
    finally: os.close(parent)


def _error(status, code, message):
    return JSONResponse({'error': {'code': code, 'message': message}}, status_code=status,
        headers={'Cache-Control': 'no-store'})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--config', required=True); args = parser.parse_args()
    config_raw = private_raw(args.config); p = json.loads(config_raw)
    if p['mode'] != 'owned_synthetic_morphology_preview_v1': raise ValueError('owned fixture mode required')
    for path, digest in p['frozen_code_sha256'].items():
        if sha256(Path(path).read_bytes()).hexdigest() != digest: raise ValueError('frozen source differs')
    policy = RuntimeLoginPolicy(**p['policy']); identity = (policy, 'authority')
    grant = BearerGrant(token_digest(private_raw(p['auth']['token_file'])), p['auth']['tenant_id'],
        frozenset(p['auth']['scopes']), datetime.fromisoformat(p['auth']['not_before']), datetime.fromisoformat(p['auth']['expires_at']))
    registry = BearerRegistry((grant,)); background = ContextVar('owned_morphology_background', default=False)
    def provider():
        if background.get():
            return {'authenticated': True, 'tenant_id': grant.tenant_id, 'scopes': grant.scopes} if registry.valid(grant) else None
        return current_principal()
    kw = {'runtime_identity': identity, 'principal_provider': provider}; dsn = p['dsn']; schema = policy.schema
    jobs = JobStore(dsn, schema, Path(p['artifacts']), audit_runtime_grants=True, **kw)
    sources = MarketSourceStore(dsn, schema, **kw)
    runs = ThermalRunStore(dsn, schema, gate_key=b'synthetic-gate-key-32-bytes-long!', release_verifier=lambda *_: None,
        context_verifier=context_verifier, **kw)
    holds = MarketHoldStore(dsn, schema, context_store=runs, scope_resolver=lambda *_: deepcopy(p['scope']),
        signing_key=b'synthetic-market-hold-key-32bytes!!', **kw)
    candidates = MarketCandidateStore(dsn, schema, _MarketSources(sources, holds, principal_provider=provider), **kw)
    research = ResearchRegistry(p['registry_raw'].encode(), p['registry_sha256'])
    owned = OwnedResearchService(jobs, runs, research, OwnedFixtureRegistry(Path(p['root'])), {next(iter(research._scopes)): 'context-1'})
    farms = FarmAuthoringService(FarmReplayScenarioService(jobs, ThermalScenarioStore(runs, holds), candidates, research, owned_research=owned))
    authority = execution.signed.farms.evidence.MorphologyInputEvidenceAuthority(integrity_key=private_raw(p['input_key_file']),
        issuer_id=p['issuer_id'], key_id=p['key_id'], review_resolver=lambda _: json.loads(private_raw(p['review_file'])))
    request_raw = execution.signed.reader._canonical(wire.ExecutionRequest.model_validate(p['preview']['request']).model_dump(mode='json'))
    request = json.loads(request_raw)
    class Rights:
        policy_version = 'owned-morphology-preview-rights-v1'
        def __call__(self, tenant, declaration, source, use):
            current = json.loads(private_raw(p['rights_file']))
            return (current == {'schema_version': self.policy_version, 'status': 'allowed_for_software_validation',
                'tenant_id': grant.tenant_id, 'declaration': request['rights'], 'source_sha256': request['input']['source_sha256']}
                and tenant == grant.tenant_id and declaration == request['rights'] and source == request['input']['source_sha256']
                and use in ('research_calculation', 'research_display'))
    binding = execution.signed.farms.MorphologyFarmBinding(farms, authority, input_rights=Rights())
    signed = execution.signed.MorphologyArtifactAuthority(binding, directory=Path(p['signed']['directory']),
        access=ContentAccess(os.getuid(), os.getgid()), integrity_key=private_raw(p['signed']['key_file']),
        issuer_id=p['signed']['issuer_id'], key_id=p['signed']['key_id'])
    class Resolver:
        version = p['resolver_version']
        def __call__(self, tenant, references):
            if tenant != grant.tenant_id: raise PermissionError('owned input access denied')
            return {name: private_raw(path, 16*1024**2) for name, path in p['packet_files'].items()}
    admission = execution.MorphologyExecutionService(signed, input_resolver=Resolver()); query = MorphologyExecutionQuery(admission)
    worker = MorphologyExecutionWorker(admission, tenant_id=grant.tenant_id)
    loop = DeterministicWorkerLoop(worker, input_versions=frozenset({execution.INPUT_VERSION}), poll_seconds=1, page_size=50)
    app = FastAPI(title='OpenSmartFarmSim owned morphology preview', version='1', openapi_version='3.1.0')
    def authorized(*scopes):
        principal = current_principal()
        if principal is None: return None, _error(401, 'unauthenticated', 'Authentication required')
        if not set(scopes) <= principal['scopes']: return None, _error(403, 'forbidden', 'Resource access denied')
        return principal['tenant_id'], None
    def access(scopes):
        return {'security': [{'ServiceBearer': []}], 'x-ossf-required-scopes': list(scopes)}
    @app.exception_handler(RequestValidationError)
    async def invalid(*_): return _error(422, 'invalid_request', 'Invalid request')
    wire.install_morphology_execution_routes(app, jobs=jobs, farms=farms, admission=admission, query=query,
        principal_provider=provider, authorized_tenant=authorized, error=_error, access=access)
    loops = [loop]
    if p.get('leaf_population') is not None:
        from owned_leaf_population_preview import attach_leaf_population
        leaf_loop = attach_leaf_population(app, config=p['leaf_population'], parent_query=query,
            tenant_id=grant.tenant_id, read_private=private_raw, authorized=authorized, access=access, error=_error)
        loops.append(leaf_loop)
    @app.get('/preview-input', include_in_schema=False)
    async def preview(http_request: Request):
        def identity_ok():
            principal = current_principal()
            return principal is not None and principal['tenant_id'] == grant.tenant_id and set(wire.SUBMIT_SCOPES) <= principal['scopes']
        if not identity_ok(): return _error(403, 'forbidden', 'Owned preview access denied')
        if http_request.query_params: return _error(422, 'invalid_request', 'Invalid request')
        async for chunk in http_request.stream():
            if chunk: return _error(422, 'invalid_request', 'Invalid request')
        def current():
            packet = admission._resolve(grant.tenant_id, request)
            first = binding.prepare(grant.tenant_id, request_raw, **packet)
            value = {'schema_version': 'owned-morphology-preview-input-v1', **execution.signed.reader.FLAGS,
                'label': p['preview']['label'], 'request': json.loads(request_raw)}
            if binding.current(grant.tenant_id, request_raw, first, **packet, write=True) != first: raise ValueError()
            return execution.signed.reader._canonical(value)
        try: raw = await run_in_threadpool(current)
        except PermissionError: return _error(403, 'forbidden', 'Owned preview access denied')
        except Exception: return _error(422, 'morphology_execution_hold', 'Owned preview input unavailable')
        if not identity_ok(): return _error(403, 'forbidden', 'Owned preview access denied')
        return Response(raw, media_type='application/json', headers={'Cache-Control':'no-store'})
    service = HttpsApiService(PrincipalMiddleware(app, registry), p['TLS']['certificate'], p['TLS']['key'], port=p['TLS']['port'])
    server = service.server(); stop = Event()
    def consume(current_loop):
        token = background.set(True)
        try:
            current_loop.run(stop, emit=lambda event: print(json.dumps(event, sort_keys=True), flush=True))
        except Exception:
            stop.set()
            print('{"event":"consumer_hold","scope":"software_research_only"}', flush=True); server.should_exit = True
        finally: background.reset(token)
    consumers = [Thread(target=consume, args=(current_loop,), daemon=True) for current_loop in loops]
    def stop_service(*_):
        stop.set(); server.should_exit = True
    previous_signals = {sig:signal.signal(sig, stop_service) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        for consumer in consumers: consumer.start()
        print(json.dumps({'event':'owned_preview_starting','config_sha256':sha256(config_raw).hexdigest(),
            'consumer_input_versions': sorted(v for current_loop in loops for v in current_loop.discovery.input_versions),
            'scope':'software_research_only','gates':'not_assessed','actual_farm_Runs':0}), flush=True)
        server.run()
    finally:
        stop.set()
        try:
            for consumer in consumers:
                if consumer.ident is not None: consumer.join(30)
        finally:
            for sig, handler in previous_signals.items(): signal.signal(sig, handler)
        stopped = not any(consumer.is_alive() for consumer in consumers)
        print(json.dumps({'event':'owned_preview_stopped','consumers_stopped':stopped,
            'consumer_count':len(consumers)}), flush=True)
        if not stopped: raise RuntimeError('owned consumer shutdown incomplete')


if __name__ == '__main__':
    try: main()
    except Exception:
        print('{"event":"owned_preview_unavailable"}', file=sys.stderr, flush=True); raise SystemExit(1) from None
