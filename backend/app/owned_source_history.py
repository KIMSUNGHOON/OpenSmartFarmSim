"""Tenant-scoped history of the owned research, collection and review path."""

from datetime import datetime
import json
import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from psycopg import sql

from .api_contracts import JobStatus, LocationPoint, public_job_status
from .cli_contracts import parse_stage_input
from .owned_fixture_collection import CollectionInput
from .owned_research import OwnedResearchService, READ_SCOPES


COLLECTION_KEY = 'owned-fixture-collection-v1:'
REVIEW_KEY = 'owned-collection-review-v1:'
SHA = re.compile(r'^[0-9a-f]{64}$')


class SourceHistoryHold(ValueError):
    pass


class SourceHistoryCursor(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    created_at: datetime
    job_id: UUID


class SourceResearchSummary(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    job: JobStatus
    point: LocationPoint
    period_start_utc: datetime
    period_end_utc: datetime
    goal_id: str
    current_authority: Literal['available', 'hold']


class SourceHistoryPage(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    items: list[SourceResearchSummary]
    next_cursor: SourceHistoryCursor | None


class SourceHistoryDetail(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    research: SourceResearchSummary
    collection: JobStatus | None
    review: JobStatus | None


class SourceActivityItem(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    kind: Literal['collection', 'review']
    job: JobStatus
    collection_job: JobStatus | None


class SourceActivityPage(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    research_job_id: UUID
    items: list[SourceActivityItem]
    next_cursor: SourceHistoryCursor | None


class OwnedSourceHistoryService:
    def __init__(self, research: OwnedResearchService):
        if type(research) is not OwnedResearchService:
            raise ValueError('owned research service required')
        self.research = research
        self.research._binding()

    def _guard(self, tenant, pointers):
        if self.research._pointers() != pointers:
            raise SourceHistoryHold('source history authority changed')
        self.research._guard(tenant, pointers, READ_SCOPES)

    def _research(self, tenant, row):
        jobs = self.research.store
        raw = jobs._verified_input(row)
        try:
            value = parse_stage_input(raw, {'tenant_id': tenant, 'stage': 'research',
                'input_sha256': row['input_sha256']})
            ids = value['candidate_ids']
            if (value.get('input_version') != 'research_input_v1' or
                    not any(item.startswith('owned-bundle-sha256:') for item in ids) or
                    not any(item.startswith('context-sha256:') for item in ids)):
                return None
        except (KeyError, TypeError, ValueError):
            return None
        try:
            current = self.research.authority_snapshot(dict(row, input_bytes=raw), value)
        except (PermissionError, RuntimeError):
            raise
        except Exception:
            current = None
        return SourceResearchSummary(job=public_job_status(row), point=value['point'],
            period_start_utc=value['period_start_utc'], period_end_utc=value['period_end_utc'],
            goal_id=value['goal_id'], current_authority='available' if current else 'hold')

    def list(self, tenant, *, limit=20, before_created_at=None, before_job_id=None):
        if (type(limit) is not int or not 1 <= limit <= 50 or
                (before_created_at is None) != (before_job_id is None) or
                (before_created_at is not None and
                 (type(before_created_at) is not datetime or before_created_at.tzinfo is None or
                  type(before_job_id) is not UUID))):
            raise ValueError('source history cursor invalid')
        pointers = self.research._pointers()
        self._guard(tenant, pointers)
        try:
            jobs = self.research.store
            cursor = sql.SQL('')
            args = [tenant]
            if before_created_at is not None:
                cursor = sql.SQL(' AND (created_at, job_id) < (%s, %s)')
                args.extend((before_created_at, before_job_id))
            args.append(limit + 1)
            with jobs.connect() as conn:
                rows = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND stage='research'{} "
                    'ORDER BY created_at DESC, job_id DESC LIMIT %s').format(jobs._table('jobs'), cursor),
                    args).fetchall()
            items = [item for row in rows[:limit] if (item := self._research(tenant, row)) is not None]
            self._guard(tenant, pointers)
            next_cursor = (SourceHistoryCursor(created_at=rows[limit-1]['created_at'],
                job_id=rows[limit-1]['job_id']) if len(rows) > limit else None)
            return SourceHistoryPage(items=items, next_cursor=next_cursor)
        finally:
            self._guard(tenant, pointers)

    def get(self, tenant, research_job_id: UUID):
        if type(research_job_id) is not UUID:
            raise ValueError('source history job ID invalid')
        pointers = self.research._pointers()
        self._guard(tenant, pointers)
        try:
            jobs = self.research.store
            with jobs.connect() as conn:
                root = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s "
                    "AND stage='research'").format(jobs._table('jobs')),
                    (tenant, research_job_id)).fetchone()
                if root is None or (research := self._research(tenant, root)) is None:
                    return None
                collection = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND "
                    "stage='collection' AND idempotency_key LIKE %s AND "
                    "convert_from(input_bytes,'UTF8')::jsonb->>'research_job_id'=%s "
                    'ORDER BY created_at DESC, job_id DESC LIMIT 1').format(jobs._table('jobs')),
                    (tenant, COLLECTION_KEY + '%', str(research_job_id))).fetchone()
                review = None
                if collection is not None:
                    self._check_collection(jobs, root, collection)
                    review = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND "
                        "stage='collection_review' AND idempotency_key LIKE %s AND "
                        "convert_from(input_bytes,'UTF8')::jsonb->>'collection_job_id'=%s "
                        'ORDER BY created_at DESC, job_id DESC LIMIT 1').format(jobs._table('jobs')),
                        (tenant, REVIEW_KEY + '%', str(collection['job_id']))).fetchone()
                    if review is not None:
                        self._check_review(jobs, collection, review)
            self._guard(tenant, pointers)
            return SourceHistoryDetail(research=research,
                collection=public_job_status(collection) if collection else None,
                review=public_job_status(review) if review else None)
        finally:
            self._guard(tenant, pointers)

    def activity(self, tenant, research_job_id: UUID, *, limit=20,
                 before_created_at=None, before_job_id=None):
        if (type(research_job_id) is not UUID or type(limit) is not int or
                not 1 <= limit <= 50 or
                (before_created_at is None) != (before_job_id is None) or
                (before_created_at is not None and
                 (type(before_created_at) is not datetime or before_created_at.tzinfo is None or
                  type(before_job_id) is not UUID))):
            raise ValueError('source activity cursor invalid')
        pointers = self.research._pointers()
        self._guard(tenant, pointers)
        try:
            jobs = self.research.store
            cursor = sql.SQL('')
            args = [tenant, COLLECTION_KEY + '%', str(research_job_id),
                    tenant, REVIEW_KEY + '%']
            if before_created_at is not None:
                cursor = sql.SQL(' AND (j.created_at, j.job_id) < (%s, %s)')
                args.extend((before_created_at, before_job_id))
            args.append(limit + 1)
            with jobs.connect() as conn:
                root = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s "
                    "AND stage='research'").format(jobs._table('jobs')),
                    (tenant, research_job_id)).fetchone()
                if root is None or self._research(tenant, root) is None:
                    return None
                rows = conn.execute(sql.SQL("""
                    WITH linked AS (
                        SELECT job_id FROM {jobs}
                        WHERE tenant_id=%s AND stage='collection' AND idempotency_key LIKE %s
                          AND convert_from(input_bytes,'UTF8')::jsonb->>'research_job_id'=%s
                    )
                    SELECT j.* FROM {jobs} AS j
                    WHERE j.tenant_id=%s AND (
                        (j.stage='collection' AND j.job_id IN (SELECT job_id FROM linked)) OR
                        (j.stage='collection_review' AND j.idempotency_key LIKE %s AND
                         EXISTS (SELECT 1 FROM linked WHERE linked.job_id::text =
                           convert_from(j.input_bytes,'UTF8')::jsonb->>'collection_job_id'))
                    ){cursor}
                    ORDER BY j.created_at DESC, j.job_id DESC LIMIT %s
                """).format(jobs=jobs._table('jobs'), cursor=cursor),
                    args).fetchall()
                items = []
                for row in rows[:limit]:
                    if row['stage'] == 'collection':
                        self._check_collection(jobs, root, row)
                        items.append(SourceActivityItem(kind='collection',
                            job=public_job_status(row), collection_job=None))
                        continue
                    value = json.loads(jobs._verified_input(row))
                    try:
                        parent_id = UUID(value['collection_job_id'])
                    except (KeyError, TypeError, ValueError):
                        raise SourceHistoryHold('source activity parent invalid') from None
                    parent = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s "
                        "AND job_id=%s AND stage='collection'").format(jobs._table('jobs')),
                        (tenant, parent_id)).fetchone()
                    if parent is None:
                        raise SourceHistoryHold('source activity parent unavailable')
                    self._check_collection(jobs, root, parent)
                    self._check_review(jobs, parent, row, value)
                    items.append(SourceActivityItem(kind='review',job=public_job_status(row),
                        collection_job=public_job_status(parent)))
            self._guard(tenant, pointers)
            next_cursor = (SourceHistoryCursor(created_at=rows[limit-1]['created_at'],
                job_id=rows[limit-1]['job_id']) if len(rows) > limit else None)
            return SourceActivityPage(research_job_id=research_job_id,
                items=items, next_cursor=next_cursor)
        finally:
            self._guard(tenant, pointers)

    @staticmethod
    def _check_collection(jobs, research, row):
        value = CollectionInput.model_validate_json(jobs._verified_input(row))
        if (value.research_job_id != str(research['job_id']) or
                value.research_input_sha256 != research['input_sha256'] or
                not row['idempotency_key'].startswith(COLLECTION_KEY) or
                SHA.fullmatch(row['idempotency_key'][len(COLLECTION_KEY):]) is None):
            raise SourceHistoryHold('collection lineage differs')

    @staticmethod
    def _check_review(jobs, collection, row, value=None):
        if value is None:
            value = json.loads(jobs._verified_input(row))
        if (type(value) is not dict or
                value.get('input_version') != 'owned-collection-review-input-v1' or
                value.get('collection_job_id') != str(collection['job_id']) or
                value.get('collection_input_sha256') != collection['input_sha256'] or
                not row['idempotency_key'].startswith(REVIEW_KEY) or
                SHA.fullmatch(row['idempotency_key'][len(REVIEW_KEY):]) is None):
            raise SourceHistoryHold('review lineage differs')
