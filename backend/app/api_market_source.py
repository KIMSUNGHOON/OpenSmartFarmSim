"""Atomic HTTP intake of existing typed user assumptions; no calculation or G0."""

from datetime import datetime
from hashlib import sha256
from typing import Any, Literal

from pydantic import Field

from .api_contracts import JobStatus, public_job_status
from .job_store import JobStore
from .jobs import canonical_input_bytes
from .market_source_store import MarketSourceStore, _KINDS
from .market import UnavailableMarketContext
from .provenance import FrozenContract
from .runtime_roles import RuntimeLoginPolicy
from .thermal_scenario_store import IDENTIFIER
from .http_identity import current_principal


_SOURCE_METHODS = frozenset({'tenant_is_authenticated', 'get_economic_scenario',
    'get_economic_scenario_pin', 'get_economic_input', 'get_joint_shock', 'get_joint_shock_pin',
    'get_input_rights', 'get_settlement_applicability', 'get_settlement_evidence', 'get_prior_batch_cost'})


class _MarketSources:
    def __init__(self, source, holds, *, principal_provider=current_principal):
        if (not callable(principal_provider) or
                any(not callable(getattr(source, name, None)) for name in _SOURCE_METHODS)):
            raise ValueError('market source interface rejected')
        self._source, self._holds = source, holds
        self._principal_provider = principal_provider

    def tenant_is_authenticated(self, tenant):
        principal = self._principal_provider()
        return bool(principal is not None and principal['tenant_id'] == tenant and
                    self._source.tenant_is_authenticated(tenant) is True)

    def get_market_hold_report(self, report_id):
        return self._holds.get_market_hold_report(report_id)

    def get_decision_context(self, tenant, snapshot_id, context_id):
        return self._holds.get_decision_context(tenant, snapshot_id, context_id)

    def __getattr__(self, name):
        if name not in _SOURCE_METHODS:
            raise AttributeError(name)
        def scoped_read(*args):
            principal = self._principal_provider()
            if principal is None or not self.tenant_is_authenticated(principal['tenant_id']):
                return None
            return getattr(self._source, name)(*args)
        return scoped_read


SourceKind = Literal['economic_scenario', 'economic_input', 'joint_shock', 'input_rights',
                     'settlement_applicability', 'settlement_evidence', 'prior_batch_cost']
SOURCE_SCOPES = ('market_source_write', 'market_source_read', 'metadata')


class MarketUserSourceRequest(FrozenContract):
    kind: SourceKind
    input: dict[str, Any]
    idempotency_key: str = Field(pattern=IDENTIFIER, max_length=200)


class MarketUserSourceSummary(FrozenContract):
    kind: SourceKind
    record_id: str = Field(min_length=1, max_length=200)
    revision: str = Field(min_length=1, max_length=200)
    payload_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    admission_kind: Literal['contract_valid_user_assumption']
    recorded_at: datetime
    intent_job: JobStatus


def _inline_schema(model):
    schema = model.model_json_schema()
    definitions = schema.pop('$defs', {})
    def inline(value, trail=()):
        if type(value) is list:
            return [inline(item, trail) for item in value]
        if type(value) is not dict:
            return value
        if '$ref' in value:
            ref = value['$ref']
            if not ref.startswith('#/$defs/') or ref in trail:
                raise ValueError('source request schema reference invalid')
            name = ref[len('#/$defs/'):].replace('~1', '/').replace('~0', '~')
            return inline(definitions[name], trail+(ref,)) | {
                key: inline(item, trail) for key, item in value.items() if key != '$ref'}
        result = {key: inline(item, trail) for key, item in value.items()}
        if 'properties' in result:
            result['required'] = list(result['properties'])
        return result
    return inline(schema)


def market_user_source_schema():
    variants = []
    key = MarketUserSourceRequest.model_json_schema()['properties']['idempotency_key']
    for kind, (model, _, _) in _KINDS.items():
        payload = _inline_schema(model)
        payload['properties'].pop('tenant_id')
        payload['required'].remove('tenant_id')
        if kind == 'economic_scenario':
            for field in ('market_context', 'scenario_market_context'):
                payload['properties'][field] = UnavailableMarketContext.model_json_schema()
        variants.append({'type': 'object', 'additionalProperties': False,
            'required': ['kind', 'input', 'idempotency_key'], 'properties': {
                'kind': {'const': kind, 'type': 'string'}, 'input': payload, 'idempotency_key': key}})
    return {'oneOf': variants}


class MarketUserSourceService:
    def __init__(self, jobs, sources):
        self.jobs, self.sources = jobs, sources
        try:
            self._binding()
        except RuntimeError:
            raise ValueError('market user source binding rejected') from None

    def _binding(self):
        binding = getattr(self.jobs, 'runtime_identity', None)
        if (type(self.jobs) is not JobStore or type(self.sources) is not MarketSourceStore or
                type(binding) is not tuple or len(binding) != 2 or type(binding[0]) is not RuntimeLoginPolicy or
                binding[1] != 'authority' or binding[0].market_source_storage is not True or
                binding[0].schema != self.jobs.schema or type(self.jobs._dsn) is not str or not self.jobs._dsn or
                self.sources.runtime_identity != binding or self.sources.schema != self.jobs.schema or
                self.sources.dsn != self.jobs._dsn or self.jobs.audit_runtime_grants is not True or
                not callable(self.jobs.principal_provider) or
                self.sources._principal_provider is not self.jobs.principal_provider):
            raise RuntimeError('market user source binding rejected')

    def _access(self, tenant):
        if not all(self.jobs._has_scope(tenant, scope) for scope in SOURCE_SCOPES):
            raise PermissionError('market user source admission denied')

    def submit(self, tenant, body):
        self._access(tenant)
        self._binding()
        body = MarketUserSourceRequest.model_validate(body.model_dump(mode='json'))
        if 'tenant_id' in body.input:
            raise ValueError('market user source input rejected')
        data = body.input | {'tenant_id': tenant}
        self.sources._model(body.kind, tenant, canonical_input_bytes(data))
        admitted = []
        sources, jobs = self.sources, self.jobs
        def guard():
            self._access(tenant)
            self._binding()
            if self.sources is not sources or self.jobs is not jobs:
                raise RuntimeError('market user source binding rejected')
        def adopt(conn, row):
            guard()
            _, record = sources._adopt_in_transaction(conn, tenant, body.kind, str(row['job_id']))
            admitted.append(record)
            guard()
        intent = 'market-user-source-v1:'+sha256(canonical_input_bytes({
            'kind': body.kind, 'idempotency_key': body.idempotency_key})).hexdigest()
        job = jobs.submit(tenant, 'collection', data, intent, admission_action=adopt, commit_guard=guard)
        record = admitted[0]
        return MarketUserSourceSummary(kind=body.kind, record_id=record['record_id'],
            revision=record['revision'], payload_sha256=record['payload_sha256'],
            admission_kind=record['admission_kind'], recorded_at=record['recorded_at'],
            intent_job=public_job_status(job))
