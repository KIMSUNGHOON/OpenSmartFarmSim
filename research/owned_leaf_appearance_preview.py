"""Explicit owned synthetic leaf dependencies for the existing preview server."""
from contextlib import nullcontext
from copy import deepcopy
import json
from pathlib import Path

from fastapi import Request, Response
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect

from app import api_crop_leaf_appearance_execution as wire
from app import crop_leaf_appearance_execution as execution
from app.crop_leaf_appearance_execution_query import LeafAppearanceExecutionQuery
from app.crop_leaf_appearance_execution_worker import LeafAppearanceExecutionWorker
from app.deterministic_work import DeterministicWorkerLoop


VERSION = 'owned-leaf-appearance-preview-v1'
RIGHTS_VERSION = 'owned-leaf-appearance-preview-rights-v1'
PACKET_NAMES = frozenset({'program_raw', 'source_raw', 'evidence_raw'})


def _configuration(value):
    try:
        fields = {'schema_version', 'request', 'label', 'input_key_file', 'review_file', 'rights_file',
            'issuer_id', 'key_id', 'packet_files', 'signed'}
        if (type(value) is not dict or set(value) != fields or value['schema_version'] != VERSION
                or type(value['label']) is not str or not 0 < len(value['label']) <= 160
                or type(value['packet_files']) is not dict or set(value['packet_files']) != PACKET_NAMES
                or type(value['signed']) is not dict
                or set(value['signed']) != {'directory', 'key_file', 'issuer_id', 'key_id'}):
            raise ValueError()
        request = wire.LeafAppearanceExecutionRequest.model_validate(value['request']).model_dump(mode='json')
        if request != value['request']: raise ValueError()
        for name in ('issuer_id', 'key_id'):
            if not execution.signed.farms.evidence.stem._identifier(value[name]): raise ValueError()
            if not execution.signed.farms.evidence.stem._identifier(value['signed'][name]): raise ValueError()
        paths = [value[k] for k in ('input_key_file', 'review_file', 'rights_file')]
        paths += list(value['packet_files'].values())+[value['signed']['directory'], value['signed']['key_file']]
        if any(type(p) is not str or not Path(p).is_absolute() or '..' in Path(p).parts for p in paths):
            raise ValueError()
        return deepcopy(value)
    except Exception:
        raise ValueError('owned leaf preview configuration rejected') from None


class OwnedLeafResolver:
    version = 'owned-leaf-appearance-preview-resolver-v1'

    def __init__(self, config, *, tenant_id, read_private):
        self.files = dict(config['packet_files'])
        self.reference = deepcopy(config['request']['input'])
        self.tenant_id, self.read_private = tenant_id, read_private

    def __call__(self, tenant, reference):
        if tenant != self.tenant_id or reference != self.reference:
            raise PermissionError('owned leaf input unavailable')
        return {name: self.read_private(path, 16*1024**2) for name, path in self.files.items()}


class OwnedLeafRights:
    policy_version = RIGHTS_VERSION

    def __init__(self, config, *, tenant_id, read_private):
        self.file = config['rights_file']
        self.request = deepcopy(config['request'])
        self.tenant_id, self.read_private = tenant_id, read_private

    def __call__(self, tenant, declaration, source, use):
        current = json.loads(self.read_private(self.file))
        return (current == {'schema_version': self.policy_version, 'status': 'allowed_for_software_validation',
            'tenant_id': self.tenant_id, 'declaration': self.request['rights'],
            'source_sha256': self.request['input']['source_sha256']}
            and tenant == self.tenant_id and declaration == self.request['rights']
            and source == self.request['input']['source_sha256']
            and use in ('research_calculation', 'research_display'))


def attach_leaf_appearance(app, *, config, parent_query, tenant_id, read_private, authorized, access, error):
    if config is None: return None
    config = _configuration(config)
    parent = parent_query.service.authority
    evidence = execution.signed.farms.evidence.LeafAppearanceInputEvidenceAuthority(
        integrity_key=read_private(config['input_key_file']), issuer_id=config['issuer_id'], key_id=config['key_id'],
        review_resolver=lambda _:json.loads(read_private(config['review_file'])),
        stem_input_authority=parent.farm_binding.input_authority)
    binding = execution.signed.farms.LeafAppearanceFarmBinding(parent_query, evidence,
        input_rights=OwnedLeafRights(config, tenant_id=tenant_id, read_private=read_private))
    authority = execution.signed.LeafAppearanceArtifactAuthority(binding,
        directory=Path(config['signed']['directory']), access=parent.access,
        integrity_key=read_private(config['signed']['key_file']),
        issuer_id=config['signed']['issuer_id'], key_id=config['signed']['key_id'])
    admission = execution.LeafAppearanceExecutionService(authority,
        input_resolver=OwnedLeafResolver(config, tenant_id=tenant_id, read_private=read_private))
    query = LeafAppearanceExecutionQuery(admission)
    worker = LeafAppearanceExecutionWorker(admission, tenant_id=tenant_id)
    loop = DeterministicWorkerLoop(worker, input_versions=frozenset({execution.INPUT_VERSION}), poll_seconds=1, page_size=50)
    wire.install_leaf_appearance_execution_routes(app, jobs=admission.jobs, farms=parent.farm_binding.farms,
        admission=admission, query=query, principal_provider=admission.jobs.principal_provider,
        authorized_tenant=authorized, error=error, access=access)
    request_raw = execution.signed.reader._canonical(config['request'])

    @app.get('/leaf-appearance-preview-input', include_in_schema=False)
    async def preview(request: Request):
        tenant, denied = authorized(*wire.SUBMIT_SCOPES)
        if denied is not None: return denied
        if tenant != tenant_id: return error(403, 'forbidden', 'Owned preview access denied')
        if request.query_params: return error(422, 'invalid_request', 'Invalid request')
        try:
            async for chunk in request.stream():
                if chunk: return error(422, 'invalid_request', 'Invalid request')
        except ClientDisconnect: return error(422, 'invalid_request', 'Invalid request')
        def current():
            farms = parent.farm_binding.farms
            ref = config['request']['farm']
            scope = (farms.registration_read_scope(tenant, ref['scenario_id'], ref['scenario_revision'],
                ref['registration_sha256']) if farms._registration_read.get() is None else nullcontext())
            with scope:
                packet = admission._resolve(tenant, config['request'])
                first = binding.prepare(tenant, request_raw, **packet)
                value = {'schema_version': 'owned-leaf-appearance-preview-input-v1', **execution.signed.FLAGS,
                    'label': config['label'], 'request': json.loads(request_raw)}
                if binding.current(tenant, request_raw, first, **packet, write=True) != first: raise ValueError()
                return execution.signed.reader._canonical(value)
        raw = None; failure = None
        try: raw = await run_in_threadpool(current)
        except PermissionError: failure = error(403, 'forbidden', 'Owned preview access denied')
        except Exception: failure = error(422, 'leaf_appearance_execution_hold', 'Owned preview input unavailable')
        observed, denied = authorized(*wire.SUBMIT_SCOPES)
        if denied is not None: return denied
        if observed != tenant: return error(403, 'forbidden', 'Owned preview access denied')
        if failure is not None: return failure
        if not raw or len(raw) > wire.MAX_RESPONSE_BYTES:
            return error(503, 'leaf_appearance_execution_unavailable', 'Owned preview unavailable')
        return Response(raw, media_type='application/json', headers={'Cache-Control': 'no-store'})
    return loop
