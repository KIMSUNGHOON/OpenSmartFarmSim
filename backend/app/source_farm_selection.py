"""Read existing owned source pins for a later independently checked farm intent."""

from hashlib import sha256
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from .api_contracts import LocationPoint
from .cli_contracts import parse_stage_input
from .jobs import require_name
from .orchestration import IDENTIFIER, UTC_PATTERN
from .owned_fixture_collection import CollectionService, UUID_PATTERN
from .owned_fixture_registry import collection_record_bytes
from .owned_research import CONTEXT_FIELDS, OwnedResearchService
from .provenance import Digest, FrozenContract
from .thermal_run_store import snapshot_id_for


READ_SCOPES = ('metadata', 'artifact', 'collection_read',
    'thermal_snapshot_read', 'decision_context_read')
JobId = Annotated[str, Field(pattern=UUID_PATTERN)]
UtcText = Annotated[str, Field(pattern=UTC_PATTERN, max_length=27)]


class SourceFarmSelectionHold(ValueError):
    pass


class SourceFarmSelection(FrozenContract):
    selection_version: Literal['owned-source-farm-selection-v1']
    claim_scope: Literal['software_fixture_only']
    assessment_status: Literal['hold']
    g0_status: Literal['not_accepted']
    g1_status: Literal['not_accepted']
    requires_registration_recheck: Literal[True]
    research_job_id: JobId
    research_attempt: int = Field(ge=1)
    research_decision_id: JobId
    research_input_sha256: Digest
    research_artifact_sha256: Digest
    collection_job_id: JobId
    collection_attempt: int = Field(ge=1)
    collection_input_sha256: Digest
    collection_record_sha256: Digest
    point: LocationPoint
    period_start_utc: UtcText
    period_end_utc: UtcText
    goal_id: Literal['historical-thermal-replay']
    provider_id: Literal['project-fixture:manifest-v2']
    registry_sha256: Digest
    bundle_sha256: Digest
    snapshot_id: str = Field(pattern=r'^thermal-snapshot-v1:[0-9a-f]{64}$')
    manifest_sha256: Digest
    weather_sha256: Digest
    thermal_sha256: Digest
    decision_context_id: str = Field(pattern=IDENTIFIER, max_length=200)
    context_sha256: Digest
    decision_at_utc: UtcText
    claim_mode: Literal['ex_ante', 'ex_post_replay']
    decision_time_kind: Literal['actual', 'hypothetical']


class SourceFarmSelectionService:
    def __init__(self, research, collection):
        self.research, self.collection = research, collection
        try:
            self._binding()
        except Exception:
            raise ValueError('source farm selection binding rejected') from None

    def _binding(self):
        if (type(self.research) is not OwnedResearchService or
                type(self.collection) is not CollectionService):
            raise RuntimeError('source farm selection binding rejected')
        self.research._binding()
        self.collection._binding()
        if (self.collection.jobs is not self.research.store or
                self.collection.registry is not self.research.registry):
            raise RuntimeError('source farm selection binding rejected')

    def _pointers(self):
        return (self.research, self.collection,
            self.research._pointers(), self.collection._pointers())

    def _guard(self, tenant, pointers):
        self._binding()
        if self._pointers() != pointers:
            raise SourceFarmSelectionHold('source farm references unavailable')
        self.research._guard(tenant, pointers[2], READ_SCOPES)
        self.collection._guard(tenant, pointers[3], READ_SCOPES)

    def _read(self, tenant, research_id, collection_id):
        jobs, runs = self.research.store, self.research.runs
        with jobs.connect() as conn:
            root = jobs._locked_job(conn, tenant, research_id)
            child = jobs._locked_job(conn, tenant, collection_id)
            if (root is None or child is None or root['stage'] != 'research' or
                    child['stage'] != 'collection'):
                return None
            if root['state'] != 'succeeded' or child['state'] != 'succeeded':
                raise SourceFarmSelectionHold()
            raw = jobs._verified_input(root)
            jobs._verified_input(child)
        value = parse_stage_input(raw, root)
        if (value['goal_id'] != 'historical-thermal-replay' or
                self.research.authority_snapshot(dict(root, input_bytes=raw), value) is None):
            raise SourceFarmSelectionHold()
        record = self.collection.read_record(tenant, str(collection_id))
        if (record['research_job_id'] != str(research_id) or
                record['research_attempt'] != root['attempt_count'] or
                record['research_input_sha256'] != root['input_sha256'] or
                any(record[key] != value[key] for key in CONTEXT_FIELDS)):
            raise SourceFarmSelectionHold()
        manifest, _ = self.collection.registry._read()
        sources = {row['metadata']['fixture_id']: row['raw_utf8'].encode('utf-8')
            for row in record['sources']}
        raws = (manifest, sources['synthetic-weather-v1'], sources['synthetic-thermal-parameters-v1'])
        snapshot_id = snapshot_id_for(*raws)
        snapshot = runs.get_snapshot(tenant, snapshot_id)
        context = runs.get_decision_context(tenant, snapshot_id, record['decision_context_id'])
        if (snapshot is None or context is None or
                tuple(snapshot[key] for key in ('manifest_raw', 'weather_raw', 'thermal_raw')) != raws or
                any(context[key] != record[key] for key in CONTEXT_FIELDS) or
                'context-sha256:' + context['context_sha256'] not in value['candidate_ids'] or
                'owned-bundle-sha256:' + record['bundle_sha256'] not in value['candidate_ids']):
            raise SourceFarmSelectionHold()
        return SourceFarmSelection(selection_version='owned-source-farm-selection-v1',
            claim_scope='software_fixture_only', assessment_status='hold',
            g0_status='not_accepted', g1_status='not_accepted', requires_registration_recheck=True,
            **{key: record[key] for key in ('research_job_id', 'research_attempt',
                'research_decision_id', 'research_input_sha256', 'research_artifact_sha256',
                'provider_id', 'registry_sha256', 'bundle_sha256', *CONTEXT_FIELDS)},
            collection_job_id=str(collection_id), collection_attempt=child['attempt_count'],
            collection_input_sha256=child['input_sha256'],
            collection_record_sha256=sha256(collection_record_bytes(record)).hexdigest(),
            **{key: value[key] for key in ('point', 'period_start_utc', 'period_end_utc', 'goal_id')},
            snapshot_id=snapshot_id,
            **{key: snapshot[key] for key in ('manifest_sha256', 'weather_sha256', 'thermal_sha256')},
            context_sha256=context['context_sha256'])

    def get(self, tenant, research_job_id, collection_job_id):
        require_name(tenant, 'tenant_id')
        if type(research_job_id) is not UUID or type(collection_job_id) is not UUID:
            raise ValueError('source farm job IDs invalid')
        pointers = self._pointers()
        self._guard(tenant, pointers)
        try:
            selected = self._read(tenant, research_job_id, collection_job_id)
            if selected is None:
                return None
            if self._read(tenant, research_job_id, collection_job_id) != selected:
                raise SourceFarmSelectionHold()
            return selected
        except PermissionError:
            raise
        except Exception:
            raise SourceFarmSelectionHold('source farm references unavailable') from None
        finally:
            self._guard(tenant, pointers)
