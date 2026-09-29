"""Owned fixture collection planning under existing stored signed contexts."""

from hashlib import sha256
from types import MappingProxyType

from .cli_contracts import AuthoritySnapshot, _canonical, _id, parse_stage_input
from .job_store import JobStore
from .orchestration import LocationRequest, ResearchRequestRejected
from .owned_fixture_registry import OwnedFixtureRegistry, collection_record_bytes
from .research_registry import ResearchRegistry, PREFIX, _scope_key
from .runtime_roles import RuntimeLoginPolicy
from .thermal_run_store import ThermalRunStore, snapshot_id_for


READ_SCOPES = ('metadata', 'decision_context_read')
ADMISSION_SCOPES = ('location_create', *READ_SCOPES)
CONTEXT_FIELDS = ('decision_context_id','decision_at_utc','claim_mode','decision_time_kind')


class OwnedResearchService:
    def __init__(self, store, runs, catalog, registry, context_ids):
        self.store,self.runs,self.catalog,self.registry=store,runs,catalog,registry
        try:
            self._binding()
            if (type(context_ids) is not dict or not 1 <= len(context_ids) <= 64 or
                    any(key not in catalog._scopes or not _id(value) for key,value in context_ids.items())):
                raise ValueError()
            self._contexts=MappingProxyType(dict(context_ids))
        except Exception:
            raise ValueError('owned research binding rejected') from None

    def _binding(self):
        if (type(self.store) is not JobStore or type(self.runs) is not ThermalRunStore or
                type(self.catalog) is not ResearchRegistry or type(self.registry) is not OwnedFixtureRegistry):
            raise RuntimeError('owned research binding rejected')
        binding=self.store.runtime_identity
        if (type(binding) is not tuple or len(binding)!=2 or type(binding[0]) is not RuntimeLoginPolicy or
                binding[1]!='authority' or binding[0].schema!=self.store.schema or
                self.store.audit_runtime_grants is not True or not callable(self.store.principal_provider) or
                self.runs.runtime_identity!=binding or self.runs.dsn!=self.store._dsn or
                self.runs.schema!=self.store.schema or self.runs._principal_provider is not self.store.principal_provider or
                not callable(self.runs._context_verifier)):
            raise RuntimeError('owned research binding rejected')

    def _pointers(self):
        return (self.store,self.runs,self.catalog,self.registry,self._contexts,self.catalog.sha256,
            self.registry._root,self.registry.provider_id,self.store._dsn,self.store.schema,
            self.store.artifact_root,self.store.runtime_identity,self.store.principal_provider,
            self.store.content_access,self.runs._context_verifier)

    def _guard(self,tenant,pointers,scopes):
        self._binding()
        if self._pointers()!=pointers:
            raise RuntimeError('owned research binding changed')
        if not all(self.store._has_scope(tenant,scope) for scope in scopes):
            raise PermissionError('owned research access denied')

    def prepare(self,tenant,body,*,scopes=READ_SCOPES):
        pointers=self._pointers()
        guard=lambda:self._guard(tenant,pointers,scopes)
        guard()
        try:
            if type(body) is not LocationRequest:
                raise ValueError()
            scope=self.catalog.scope_for_location(tenant,body)
            key=_scope_key(tenant,(body.latitude,body.longitude),body.period_start_utc,body.period_end_utc,body.goal_id)
            context_id=self._contexts.get(key)
            if scope is None or context_id is None or scope.provider_ids!=(self.registry.provider_id,):
                raise ValueError()
            manifest,sources=self.registry._read()
            originals={row['metadata']['fixture_id']:row['raw_utf8'].encode() for row in sources}
            snapshot_id=snapshot_id_for(manifest,originals['synthetic-weather-v1'],originals['synthetic-thermal-parameters-v1'])
            context=self.runs.get_decision_context(tenant,snapshot_id,context_id)
            if context is None:
                raise ValueError()
            bundle=self.registry.read_bundle(context['decision_at_utc'],context['claim_mode'])
            if (bundle['start_utc'],bundle['end_utc'])!=(scope.period_start_utc,scope.period_end_utc):
                raise ValueError()
            value={'input_version':'research_input_v1','tenant_id':tenant,
                'point':{'latitude':body.latitude,'longitude':body.longitude},
                'period_start_utc':body.period_start_utc,'period_end_utc':body.period_end_utc,
                'goal_id':body.goal_id,'provider_ids':list(scope.provider_ids),
                'candidate_ids':[self.registry.provider_id,PREFIX+self.catalog.sha256,
                    'owned-bundle-sha256:'+sha256(collection_record_bytes(bundle)).hexdigest(),
                    'context-sha256:'+context['context_sha256']], 'evidence_refs':[],
                **{name:context[name] for name in CONTEXT_FIELDS}}
            raw=_canonical(value)
            parse_stage_input(raw,{'tenant_id':tenant,'stage':'research','input_sha256':sha256(raw).hexdigest()})
            return value,context
        except PermissionError:
            raise
        except Exception:
            raise ResearchRequestRejected('owned research inputs unavailable') from None
        finally:
            guard()

    def submit(self,tenant,body):
        pointers=self._pointers()
        value,_=self.prepare(tenant,body,scopes=ADMISSION_SCOPES)
        raw=_canonical(value)
        def final_guard():
            self._guard(tenant,pointers,ADMISSION_SCOPES)
            current,_=self.prepare(tenant,body,scopes=ADMISSION_SCOPES)
            if _canonical(current)!=raw:
                raise ResearchRequestRejected('owned research inputs changed')
            self._guard(tenant,pointers,ADMISSION_SCOPES)
        row=self.store.submit(tenant,'research',value,body.idempotency_key,commit_guard=final_guard)
        point=value['point']
        location='location-v1-'+sha256(_canonical({'tenant_id':tenant,'point':point})).hexdigest()
        return location,point,row

    def authority_snapshot(self,job,value):
        if job.get('stage')!='research':
            return None
        checked=parse_stage_input(job['input_bytes'],job)
        if checked!=value:
            return None
        body=LocationRequest.model_validate({**checked['point'],
            **{name:checked[name] for name in ('period_start_utc','period_end_utc','goal_id')},
            'idempotency_key':'authority-verification'})
        current,context=self.prepare(job['tenant_id'],body)
        if current!=checked or context['recorded_at']>job['created_at']:
            return None
        return AuthoritySnapshot(job['tenant_id'],'research',job['input_sha256'],
            frozenset(current['candidate_ids']),{},True,(),{},frozenset(),False,
            {name:current[name] for name in ('point','period_start_utc','period_end_utc','goal_id','provider_ids')},
            **{name:current[name] for name in CONTEXT_FIELDS})
