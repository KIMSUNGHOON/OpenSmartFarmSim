"""Verified research selection to an owned record under an actual fenced lease."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal
from uuid import UUID

from psycopg import sql
from pydantic import Field

from .cli_contracts import parse_stage_input, _utc
from .job_store import JobStore
from .jobs import canonical_input_bytes, require_name, require_seconds, require_digest
from .owned_fixture_registry import OwnedFixtureRegistry, collection_record_bytes
from .provenance import FrozenContract
from .runtime_roles import RuntimeLoginPolicy
from .thermal_publisher import runtime_digests


COLLECTION_SCOPES = ('metadata', 'artifact', 'collection_execute')
COLLECTION_READ_SCOPES = ('metadata', 'artifact', 'collection_read')
UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
SHA_PATTERN = r'^[0-9a-f]{64}$'


class CollectionInput(FrozenContract):
    input_version: Literal['owned-fixture-collection-input-v1']
    provider_id: Literal['project-fixture:manifest-v2']
    research_job_id: str = Field(pattern=UUID_PATTERN)
    research_attempt: int = Field(strict=True, ge=1)
    research_decision_id: str = Field(pattern=UUID_PATTERN)
    research_input_sha256: str = Field(pattern=SHA_PATTERN)
    research_artifact_sha256: str = Field(pattern=SHA_PATTERN)
    registry_sha256: str = Field(pattern=SHA_PATTERN)
    bundle_sha256: str = Field(pattern=SHA_PATTERN)
    decision_context_id: str
    decision_at_utc: str
    claim_mode: Literal['ex_ante', 'ex_post_replay']
    decision_time_kind: Literal['actual', 'hypothetical']


class CollectionHold(ValueError):
    pass


class _LeaseLost(ValueError):
    pass


class CollectionService:
    def __init__(self, jobs, registry):
        self.jobs, self.registry = jobs, registry
        try:
            self._binding()
        except Exception:
            raise ValueError('collection binding rejected') from None

    def _binding(self):
        binding = self.jobs.runtime_identity
        if (type(self.jobs) is not JobStore or type(self.registry) is not OwnedFixtureRegistry or
                type(binding) is not tuple or len(binding) != 2 or type(binding[0]) is not RuntimeLoginPolicy or
                binding[1] != 'authority' or binding[0].schema != self.jobs.schema or
                self.jobs.audit_runtime_grants is not True or not callable(self.jobs.principal_provider)):
            raise RuntimeError('collection binding rejected')

    def _pointers(self):
        jobs = self.jobs
        return (jobs, self.registry, self.registry._root, self.registry.provider_id,
            jobs._dsn, jobs.schema, jobs.artifact_root, jobs.runtime_identity,
            jobs.principal_provider, jobs.content_access)

    def _guard(self, tenant, pointers, scopes=COLLECTION_SCOPES):
        self._binding()
        if self._pointers() != pointers:
            raise RuntimeError('collection binding changed')
        if not all(self.jobs._has_scope(tenant, scope) for scope in scopes):
            raise PermissionError('collection access denied')

    def read_record(self, tenant, job_id):
        pointers = self._pointers()
        guard = lambda: self._guard(tenant, pointers, COLLECTION_READ_SCOPES)
        guard()
        try:
            if type(job_id) is not str or str(UUID(job_id)) != job_id:
                raise CollectionHold()
            with self.jobs.connect() as conn:
                job = self.jobs._locked_job(conn, tenant, job_id)
                if job is None or job['stage'] != 'collection' or job['state'] != 'succeeded':
                    raise CollectionHold()
                raw_input = self.jobs._verified_input(job)
            value = CollectionInput.model_validate_json(raw_input)
            if canonical_input_bytes(value.model_dump(mode='json')) != raw_input:
                raise CollectionHold()
            prepared, bundle = self._prepare(tenant, value.research_job_id)
            if canonical_input_bytes(prepared.model_dump(mode='json')) != raw_input:
                raise CollectionHold()
            publication = self.jobs.get_publication(tenant, job['job_id'])
            if (publication is None or type(publication['artifact_size']) is not int or
                    not 1 <= publication['artifact_size'] <= 131072):
                raise CollectionHold()
            raw = self.jobs.read_artifact(tenant, job['job_id'])
            if type(raw) is not bytes or not 1 <= len(raw) <= 131072:
                raise CollectionHold()
            record = json.loads(raw)
            if type(record) is not dict or collection_record_bytes(record) != raw:
                raise CollectionHold()
            for key in ('code_sha256', 'environment_sha256'):
                require_digest(record.get(key))
            retrieved = _utc(record.get('retrieved_at_utc'))
            expected = {'record_version': 'owned-fixture-collection-record-v1',
                'claim_scope': 'software_fixture_only', 'assessment_status': 'hold',
                'g0_status': 'not_accepted', 'g1_status': 'not_accepted',
                **value.model_dump(mode='json'), 'sources': bundle['sources'], 'qc': bundle['qc'],
                **{key: record[key] for key in ('retrieved_at_utc', 'code_sha256', 'environment_sha256')}}
            digest = sha256(raw).hexdigest()
            manifest = {'schema_version': '1', 'job_id': str(job['job_id']), 'stage': 'collection',
                'input_sha256': job['input_sha256'], 'attempt': job['attempt_count'], 'artifact_sha256': digest}
            if (record != expected or publication['tenant_id'] != tenant or
                    publication['job_id'] != job['job_id'] or publication['decision_id'] is not None or
                    publication['attempt'] != job['attempt_count'] or
                    publication['artifact_sha256'] != digest or publication['artifact_size'] != len(raw) or
                    canonical_input_bytes(publication['manifest']) != canonical_input_bytes(manifest) or
                    not job['created_at'] <= retrieved <= publication['published_at']):
                raise CollectionHold()
            return record
        except PermissionError:
            raise
        except Exception:
            raise CollectionHold('collected record unavailable') from None
        finally:
            guard()

    def _prepare(self, tenant, research_job_id):
        try:
            if type(research_job_id) is not str or str(UUID(research_job_id)) != research_job_id:
                raise ValueError()
            with self.jobs.connect() as conn:
                job = self.jobs._locked_job(conn, tenant, research_job_id)
                if job is None or job['stage'] != 'research' or job['state'] != 'succeeded':
                    raise CollectionHold()
                publication = self.jobs.get_publication(tenant, job['job_id'])
                if (publication is None or publication['decision_id'] is None or
                        publication['attempt'] != job['attempt_count'] or
                        not self.jobs._verify_decision_final(conn, job, publication['attempt'],
                            publication['decision_id'], publication['artifact_sha256'])):
                    raise CollectionHold()
                value = parse_stage_input(self.jobs._verified_input(job), job)
            raw = self.jobs.read_artifact(tenant, job['job_id'])
            if type(raw) is not bytes or not 1 <= len(raw) <= 65536:
                raise CollectionHold()
            projection = json.loads(raw)
            if type(projection) is not dict:
                raise CollectionHold()
            selected, rejected = projection.get('selected_ids'), projection.get('rejected_ids')
            if (type(projection) is not dict or raw != canonical_input_bytes(projection) or
                    type(selected) is not list or selected != [self.registry.provider_id] or
                    type(rejected) is not list or len(set(rejected)) != len(rejected) or
                    not set(rejected) <= set(value['candidate_ids']) or set(selected) & set(rejected) or
                    self.registry.provider_id not in value['provider_ids']):
                raise CollectionHold()
            expected = {'schema_version': 'decision_validated_v1', 'stage': 'research',
                'input_sha256': job['input_sha256'], 'selected_ids': selected, 'rejected_ids': rejected,
                **{key: value[key] for key in ('decision_context_id', 'decision_at_utc',
                                              'claim_mode', 'decision_time_kind')}}
            digest = sha256(raw).hexdigest()
            manifest = {'schema_version': '1', 'job_id': str(job['job_id']), 'stage': 'research',
                'input_sha256': job['input_sha256'], 'attempt': job['attempt_count'],
                'artifact_sha256': digest, 'decision_id': str(publication['decision_id'])}
            if (projection != expected or publication['tenant_id'] != tenant or
                    publication['job_id'] != job['job_id'] or publication['artifact_sha256'] != digest or
                    publication['artifact_size'] != len(raw) or
                    canonical_input_bytes(publication['manifest']) != canonical_input_bytes(manifest)):
                raise CollectionHold()
            bundle = self.registry.read_bundle(value['decision_at_utc'], value['claim_mode'])
            if (bundle['start_utc'], bundle['end_utc']) != (value['period_start_utc'], value['period_end_utc']):
                raise CollectionHold()
            prepared = CollectionInput(input_version='owned-fixture-collection-input-v1',
                provider_id=self.registry.provider_id, research_job_id=str(job['job_id']),
                research_attempt=job['attempt_count'], research_decision_id=str(publication['decision_id']),
                research_input_sha256=job['input_sha256'], research_artifact_sha256=digest,
                registry_sha256=bundle['registry_sha256'],
                bundle_sha256=sha256(collection_record_bytes(bundle)).hexdigest(),
                **{key: value[key] for key in ('decision_context_id', 'decision_at_utc',
                                              'claim_mode', 'decision_time_kind')})
            return prepared, bundle
        except (PermissionError, CollectionHold):
            raise
        except ValueError:
            raise CollectionHold('collection input unavailable') from None

    def submit(self, tenant, research_job_id, idempotency_key):
        require_name(idempotency_key, 'idempotency_key')
        pointers = self._pointers()
        guard = lambda: self._guard(tenant, pointers)
        guard()
        try:
            value, _ = self._prepare(tenant, research_job_id)
        finally:
            guard()
        raw = canonical_input_bytes(value.model_dump(mode='json'))
        def final_guard():
            guard()
            try:
                current, _ = self._prepare(tenant, research_job_id)
                if canonical_input_bytes(current.model_dump(mode='json')) != raw:
                    raise CollectionHold()
            finally:
                guard()
        key = 'owned-fixture-collection-v1:'+sha256(idempotency_key.encode()).hexdigest()
        return self.jobs.submit(tenant, 'collection', value.model_dump(mode='json'), key, commit_guard=final_guard)


@dataclass(frozen=True)
class CollectionOutcome:
    job_id: UUID
    attempt: int
    state: str
    reason_code: str
    record_sha256: str | None = None


class CollectionWorker:
    def __init__(self, service, *, tenant_id, lease_seconds=300):
        if type(service) is not CollectionService:
            raise ValueError('collection service rejected')
        require_name(tenant_id, 'tenant_id')
        require_seconds(lease_seconds, 'lease_seconds')
        service._binding()
        self.service, self.tenant_id, self.lease_seconds = service, tenant_id, lease_seconds

    def _close(self, lease, kind, reason):
        jobs = self.service.jobs
        try:
            closed = jobs.fail(self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'],
                kind, reason, termination_reason=reason)
            job = jobs.get_job(self.tenant_id, lease['job_id']) if closed else None
        except Exception:
            job = None
        return CollectionOutcome(lease['job_id'], lease['attempt'], job['state'] if job else 'unclosed', reason)

    def run_once(self, job_id):
        service, tenant = self.service, self.tenant_id
        pointers = service._pointers()
        service._guard(tenant, pointers)
        if type(job_id) is not str or str(UUID(job_id)) != job_id:
            raise ValueError('collection job ID rejected')
        jobs = service.jobs
        with jobs.connect() as conn:
            job = jobs._locked_job(conn, tenant, job_id)
            if job is None or job['stage'] != 'collection' or job['state'] not in ('queued', 'collecting'):
                return None
            data = json.loads(jobs._verified_input(job))
            if type(data) is not dict or data.get('input_version') != 'owned-fixture-collection-input-v1':
                return None
        lease = jobs.claim(self.lease_seconds, tenant_id=tenant, allowed_stages=('collection',), job_id=job_id)
        if lease is None:
            return None
        try:
            digests = runtime_digests(Path(__file__).resolve().parents[2])
            raw = jobs.read_input(tenant, lease['job_id'], lease['attempt'], lease['lease_token'])
            if raw is None:
                raise _LeaseLost()
            value = CollectionInput.model_validate_json(raw)
            if canonical_input_bytes(value.model_dump(mode='json')) != raw:
                raise CollectionHold()
            def check():
                service._guard(tenant, pointers)
                if runtime_digests(Path(__file__).resolve().parents[2]) != digests:
                    raise RuntimeError('collection implementation changed')
                if not jobs.renew(tenant, lease['job_id'], lease['attempt'], lease['lease_token'], self.lease_seconds):
                    raise _LeaseLost()
            check()
            try:
                prepared, bundle = service._prepare(tenant, value.research_job_id)
            finally:
                check()
            if canonical_input_bytes(prepared.model_dump(mode='json')) != raw:
                raise CollectionHold()
            artifact = collection_record_bytes({'record_version': 'owned-fixture-collection-record-v1',
                'claim_scope': 'software_fixture_only', 'assessment_status': 'hold',
                'g0_status': 'not_accepted', 'g1_status': 'not_accepted',
                **value.model_dump(mode='json'), 'sources': bundle['sources'], 'qc': bundle['qc'],
                'retrieved_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'code_sha256': digests[0], 'environment_sha256': digests[1]})
            if len(artifact) > 131072:
                raise CollectionHold()
            digest = sha256(artifact).hexdigest()
            jobs._durable_artifact(artifact, digest)
            with jobs.connect() as conn:
                job = jobs._locked_job(conn, tenant, lease['job_id'])
                if (not jobs._owns_live_lease(job, lease['attempt'], lease['lease_token']) or
                        job['cancel_requested'] or job['stage'] != 'collection' or jobs._verified_input(job) != raw):
                    raise _LeaseLost()
                def final_guard():
                    service._guard(tenant, pointers)
                    if runtime_digests(Path(__file__).resolve().parents[2]) != digests:
                        raise RuntimeError('collection implementation changed')
                    current, _ = service._prepare(tenant, value.research_job_id)
                    if canonical_input_bytes(current.model_dump(mode='json')) != raw:
                        raise CollectionHold()
                    service._guard(tenant, pointers)
                final_guard()
                updated = conn.execute(sql.SQL("""
                    UPDATE {} SET state='succeeded', reason=NULL, lease_token=NULL, lease_until=NULL,
                        updated_at=clock_timestamp() WHERE tenant_id=%s AND job_id=%s AND state='collecting'
                        AND stage='collection' AND attempt_count=%s AND lease_token=%s
                        AND lease_until>clock_timestamp() AND NOT cancel_requested
                """).format(jobs._table('jobs')), (tenant, lease['job_id'], lease['attempt'], lease['lease_token']))
                if updated.rowcount != 1:
                    raise _LeaseLost()
                manifest = {'schema_version': '1', 'job_id': str(lease['job_id']), 'stage': 'collection',
                    'input_sha256': job['input_sha256'], 'attempt': lease['attempt'], 'artifact_sha256': digest}
                jobs._insert_publication(conn, tenant, lease['job_id'], lease['attempt'], None, digest, len(artifact), manifest)
                jobs._event(conn, tenant, lease['job_id'], 'succeeded', lease['attempt'])
                jobs._outcome(conn, tenant, lease['job_id'], lease['attempt'], 'succeeded', termination_reason='completed')
                final_guard()
            return CollectionOutcome(lease['job_id'], lease['attempt'], 'succeeded', 'completed', digest)
        except _LeaseLost:
            try:
                canceled = jobs.ack_cancel(tenant, lease['job_id'], lease['attempt'], lease['lease_token'])
            except Exception:
                canceled = False
            return CollectionOutcome(lease['job_id'], lease['attempt'], 'canceled' if canceled else 'unclosed',
                'canceled_by_request' if canceled else 'collection_lease_lost')
        except (CollectionHold, ValueError, PermissionError):
            return self._close(lease, 'hold', 'collection_input_hold')
        except Exception:
            return self._close(lease, 'transient', 'collection_runtime_failure')
