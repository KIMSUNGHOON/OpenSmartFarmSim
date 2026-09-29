"""Bind a completed owned collection, staged snapshot and existing signed context."""

from hashlib import sha256
import json

from .cli_contracts import DecisionContract, DecisionPlan, ProposalHold
from .jobs import canonical_input_bytes, require_name
from .owned_fixture_collection import CollectionService
from .thermal_publisher import collection_review_input, collection_review_proposal, CONTEXT_FIELDS
from .thermal_review_contract import ThermalReviewContract
from .thermal_run_store import ThermalRunStore, snapshot_id_for


INPUT_VERSION = 'owned-collection-review-input-v1'
COLLECTION_FIELDS = frozenset({'collection_job_id', 'collection_attempt',
    'collection_input_sha256', 'collection_record_sha256'})
REVIEW_SCOPES = ('metadata', 'artifact', 'collection_read', 'collection_review_create',
    'thermal_snapshot_read', 'thermal_snapshot_write', 'decision_context_read')


class OwnedCollectionReviewService:
    def __init__(self, collection, runs):
        self.collection, self.runs = collection, runs
        try:
            self._binding()
        except Exception:
            raise ValueError('collection review binding rejected') from None

    def _binding(self):
        if type(self.collection) is not CollectionService or type(self.runs) is not ThermalRunStore:
            raise RuntimeError('collection review binding rejected')
        self.collection._binding()
        jobs = self.collection.jobs
        if (self.runs.runtime_identity != jobs.runtime_identity or self.runs.dsn != jobs._dsn or
                self.runs.schema != jobs.schema or self.runs._principal_provider is not jobs.principal_provider or
                not callable(self.runs._context_verifier)):
            raise RuntimeError('collection review binding rejected')

    def _pointers(self):
        return (self.collection, self.runs, *self.collection._pointers(), self.runs.dsn,
            self.runs.runtime_identity, self.runs._principal_provider, self.runs._context_verifier)

    def _guard(self, tenant, pointers):
        self._binding()
        if self._pointers() != pointers:
            raise RuntimeError('collection review binding changed')
        if not all(self.collection.jobs._has_scope(tenant, scope) for scope in REVIEW_SCOPES):
            raise PermissionError('collection review access denied')

    def prepare(self, tenant, collection_job_id):
        pointers = self._pointers()
        guard = lambda: self._guard(tenant, pointers)
        guard()
        try:
            record = self.collection.read_record(tenant, collection_job_id)
            manifest, _ = self.collection.registry._read()
            sources = {row['metadata']['fixture_id']:row['raw_utf8'].encode('utf-8')
                for row in record['sources']}
            raws = (manifest, sources['synthetic-weather-v1'], sources['synthetic-thermal-parameters-v1'])
            snapshot = {'snapshot_id': snapshot_id_for(*raws),
                **dict(zip(('manifest_sha256', 'weather_sha256', 'thermal_sha256'),
                           (sha256(raw).hexdigest() for raw in raws)))}
            context = self.runs.get_decision_context(tenant, snapshot['snapshot_id'], record['decision_context_id'])
            if context is None or any(context[key] != record[key] for key in CONTEXT_FIELDS):
                raise ValueError()
            jobs = self.collection.jobs
            with jobs.connect() as conn:
                job = jobs._locked_job(conn, tenant, collection_job_id)
                if job is None or job['state'] != 'succeeded' or job['stage'] != 'collection':
                    raise ValueError()
            value = {**collection_review_input(snapshot, context), 'input_version': INPUT_VERSION,
                'collection_job_id': collection_job_id, 'collection_attempt': job['attempt_count'],
                'collection_input_sha256': job['input_sha256'],
                'collection_record_sha256': sha256(jobs.read_artifact(tenant, job['job_id'])).hexdigest()}
            return value, raws, context
        except PermissionError:
            raise
        except Exception:
            raise ValueError('collection review inputs unavailable') from None
        finally:
            guard()

    def submit(self, tenant, collection_job_id, idempotency_key):
        require_name(idempotency_key, 'idempotency_key')
        pointers = self._pointers()
        guard = lambda: self._guard(tenant, pointers)
        value, raws, _ = self.prepare(tenant, collection_job_id)
        original = canonical_input_bytes(value)
        def verify():
            guard()
            try:
                current, current_raws, _ = self.prepare(tenant, collection_job_id)
                if canonical_input_bytes(current) != original or current_raws != raws:
                    raise ValueError('collection review inputs changed')
            finally:
                guard()
        def stage(conn):
            verify()
            if self.runs._pin_snapshot_in_transaction(conn, tenant, *raws) != value['snapshot_id']:
                raise ValueError('collection review snapshot changed')
        key = 'owned-collection-review-v1:'+sha256(idempotency_key.encode()).hexdigest()
        try:
            return self.collection.jobs.submit(tenant, 'collection_review', value, key,
                admission_prepare=stage, commit_guard=verify)
        except PermissionError:
            raise
        except Exception:
            raise ValueError('collection review admission unavailable') from None

    def verify_input(self, job, value):
        pointers = self._pointers()
        self._guard(job['tenant_id'], pointers)
        try:
            if (type(value) is not dict or value.get('input_version') != INPUT_VERSION or
                    job.get('stage') != 'collection_review' or
                    canonical_input_bytes(value) != job.get('input_bytes') or
                    sha256(job['input_bytes']).hexdigest() != job.get('input_sha256')):
                raise ValueError()
            expected, raws, context = self.prepare(job['tenant_id'], value.get('collection_job_id'))
            snapshot = self.runs.get_snapshot(job['tenant_id'], expected['snapshot_id'])
            if (value != expected or snapshot is None or
                    tuple(snapshot[key] for key in ('manifest_raw', 'weather_raw', 'thermal_raw')) != raws):
                raise ValueError()
            return snapshot, context
        finally:
            self._guard(job['tenant_id'], pointers)


class OwnedCollectionReviewContract(DecisionContract):
    VERSION = 'owned-collection-review-server-v1'
    BINDING_FIELDS = ThermalReviewContract.BINDING_FIELDS | COLLECTION_FIELDS

    def __init__(self, service, authority_resolver):
        if type(service) is not OwnedCollectionReviewService:
            raise ValueError('collection review service required')
        self.service = service
        super().__init__(authority_resolver, input_parser=self._parse_input)

    def binding_fields(self, job):
        return self.BINDING_FIELDS

    def _parse_input(self, job, value):
        try:
            self.service.verify_input(job, value)
        except Exception:
            raise ProposalHold('owned_collection_review_hold') from None
        return {**value, 'candidate_ids':[value['snapshot_id']], 'evidence_refs':[]}

    def plan(self, job, final_output):
        plan = super().plan(job, final_output)
        if plan.disposition == 'hold':
            return plan
        snapshot, context = self.service.verify_input(job, json.loads(job['input_bytes']))
        return DecisionPlan('proceed', canonical_input_bytes(collection_review_proposal(snapshot, context)), plan.code)
