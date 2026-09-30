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
                    raw = jobs._verified_input(collection)
                    value = CollectionInput.model_validate_json(raw)
                    if (value.research_job_id != str(research_job_id) or
                            value.research_input_sha256 != root['input_sha256'] or
                            SHA.fullmatch(collection['idempotency_key'].removeprefix(COLLECTION_KEY)) is None):
                        raise SourceHistoryHold('collection lineage differs')
                    review = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND "
                        "stage='collection_review' AND idempotency_key LIKE %s AND "
                        "convert_from(input_bytes,'UTF8')::jsonb->>'collection_job_id'=%s "
                        'ORDER BY created_at DESC, job_id DESC LIMIT 1').format(jobs._table('jobs')),
                        (tenant, REVIEW_KEY + '%', str(collection['job_id']))).fetchone()
                    if review is not None:
                        reviewed = json.loads(jobs._verified_input(review))
                        if (reviewed.get('input_version') != 'owned-collection-review-input-v1' or
                                reviewed.get('collection_job_id') != str(collection['job_id']) or
                                reviewed.get('collection_input_sha256') != collection['input_sha256'] or
                                SHA.fullmatch(review['idempotency_key'].removeprefix(REVIEW_KEY)) is None):
                            raise SourceHistoryHold('review lineage differs')
            self._guard(tenant, pointers)
            return SourceHistoryDetail(research=research,
                collection=public_job_status(collection) if collection else None,
                review=public_job_status(review) if review else None)
        finally:
            self._guard(tenant, pointers)
