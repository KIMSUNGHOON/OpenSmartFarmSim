"""Saved economic references for the exact current owned source context."""

from datetime import date, datetime, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator
from psycopg import sql

from .api_economic_scenario import EconomicScenarioService
from .economic_contracts import utc
from .farm_replay_scenario import EconomicPin
from .jobs import require_digest
from .market import UnavailableMarketContext
from .market_scenario import MarketScenarioService
from .provenance import Digest, FrozenContract
from .source_farm_selection import (SourceFarmSelectionService, SourceFarmSelection,
    READ_SCOPES as SOURCE_SCOPES)


READ_SCOPES = (*SOURCE_SCOPES, 'market_source_read', 'market_candidate_read', 'market_hold_context_read')


class FarmEconomicCandidateHold(ValueError):
    pass


class FarmEconomicCandidateCursor(FrozenContract):
    recorded_at: datetime
    candidate_id: Digest
    _utc = field_validator('recorded_at')(utc)


class FarmEconomicCandidateSummary(FrozenContract):
    economic: EconomicPin
    market_context: UnavailableMarketContext
    period_start: date
    period_end: date
    recorded_at: datetime
    _utc = field_validator('recorded_at')(utc)


class FarmEconomicCandidatePage(FrozenContract):
    verification: Literal['requires_current_selection']
    source: SourceFarmSelection
    items: list[FarmEconomicCandidateSummary] = Field(max_length=50)
    next_cursor: FarmEconomicCandidateCursor | None


class FarmEconomicSelection(FarmEconomicCandidateSummary):
    verification: Literal['requires_registration_recheck']
    source: SourceFarmSelection


class FarmEconomicCandidateService:
    def __init__(self, source, economic):
        self.source, self.economic = source, economic
        try:
            self._binding()
        except Exception:
            raise ValueError('farm economic candidate binding rejected') from None

    def _binding(self):
        if (type(self.source) is not SourceFarmSelectionService or
                type(self.economic) is not EconomicScenarioService):
            raise RuntimeError('farm economic candidate binding rejected')
        self.source._binding()
        self.economic._binding()
        if (self.economic.jobs is not self.source.research.store or
                self.economic.candidates._source._holds._context_store is not self.source.research.runs):
            raise RuntimeError('farm economic candidate binding rejected')

    def _pointers(self):
        candidates = self.economic.candidates
        holds = candidates._source._holds
        return (self.source, self.economic, self.source._pointers(), self.economic.jobs,
            candidates, candidates._source, candidates._source._source, holds,
            holds._context_store, holds._scope_resolver, holds._key)

    def _guard(self, tenant, pointers):
        self._binding()
        if self._pointers() != pointers:
            raise FarmEconomicCandidateHold('farm economic candidate references unavailable')
        self.source._guard(tenant, pointers[2])
        if not all(self.economic.jobs._has_scope(tenant, scope) for scope in READ_SCOPES):
            raise PermissionError('farm economic candidate access denied')

    def _source(self, tenant, research_id, collection_id):
        source = self.source.get(tenant, research_id, collection_id)
        if source is not None and source.claim_mode != 'ex_post_replay':
            raise FarmEconomicCandidateHold()
        return source

    @staticmethod
    def _dates(source):
        start = datetime.fromisoformat(source.period_start_utc).astimezone(ZoneInfo('Asia/Seoul')).date()
        end = (datetime.fromisoformat(source.period_end_utc) - timedelta(microseconds=1))
        return start, end.astimezone(ZoneInfo('Asia/Seoul')).date()

    @staticmethod
    def _summary(row):
        return FarmEconomicCandidateSummary(economic=EconomicPin(scenario_id=row['scenario_id'],
            revision=row['revision'], sha256=row['scenario_sha256'], candidate_id=row['candidate_id']),
            market_context=UnavailableMarketContext(kind='unavailable', hold_report_id=row['hold_report_id']),
            period_start=row['period_start'], period_end=row['period_end'],
            recorded_at=row['recorded_at'].astimezone(timezone.utc))

    def _rows(self, tenant, source, limit, before_recorded_at, before_candidate_id):
        candidates = self.economic.candidates
        holds = candidates._source._holds
        cursor = sql.SQL('')
        args = [tenant, source.snapshot_id, source.decision_context_id, source.context_sha256,
            source.decision_at_utc, source.claim_mode, source.decision_time_kind,
            datetime.fromisoformat(source.decision_at_utc), *self._dates(source)]
        if before_recorded_at is not None:
            cursor = sql.SQL(' AND (recorded_at, candidate_id) < (%s, %s)')
            args.extend((before_recorded_at, before_candidate_id))
        args.append(limit + 1)
        with candidates.connect() as conn:
            return conn.execute(sql.SQL("""
                WITH linked AS (
                    SELECT c.tenant_id, c.candidate_id, c.scenario_id, c.revision,
                        c.scenario_sha256, c.recorded_at,
                        convert_from(c.scenario_raw, 'UTF8')::jsonb AS scenario,
                        h.hold_report_id, h.snapshot_id, h.decision_context_id,
                        convert_from(h.payload_raw, 'UTF8')::jsonb AS report
                    FROM {candidates} c JOIN {holds} h ON h.tenant_id=c.tenant_id AND
                        h.hold_report_id=convert_from(c.record_raw, 'UTF8')::jsonb->>'market_hold_report_id'
                )
                SELECT candidate_id, scenario_id, revision, scenario_sha256, recorded_at, hold_report_id,
                    (scenario->>'period_start')::date AS period_start,
                    (scenario->>'period_end')::date AS period_end
                FROM linked WHERE tenant_id=%s AND snapshot_id=%s AND decision_context_id=%s AND
                    report->>'context_sha256'=%s AND report->>'decision_at_utc'=%s AND
                    report->>'claim_mode'=%s AND report->>'decision_time_kind'=%s AND
                    (scenario->>'decision_at')::timestamptz=%s AND
                    (scenario->>'period_start')::date<=%s AND (scenario->>'period_end')::date>=%s AND
                    scenario->'market_context'->>'kind'='unavailable' AND
                    scenario->'market_context'->>'hold_report_id'=hold_report_id AND
                    scenario->'scenario_market_context'=scenario->'market_context'
                    {cursor}
                ORDER BY recorded_at DESC, candidate_id DESC LIMIT %s
            """).format(candidates=candidates._table('market_candidate_pins'), holds=holds._table(),
                cursor=cursor), args).fetchall()

    def list(self, tenant, research_job_id, collection_job_id, *, limit=20,
             before_recorded_at=None, before_candidate_id=None):
        if (type(limit) is not int or not 1 <= limit <= 50 or
                (before_recorded_at is None) != (before_candidate_id is None)):
            raise ValueError('farm economic candidate cursor invalid')
        if before_recorded_at is not None:
            if type(before_recorded_at) is not datetime:
                raise ValueError('farm economic candidate cursor invalid')
            utc(before_recorded_at)
            require_digest(before_candidate_id)
        pointers = self._pointers()
        self._guard(tenant, pointers)
        try:
            source = self._source(tenant, research_job_id, collection_job_id)
            if source is None:
                return None
            rows = self._rows(tenant, source, limit, before_recorded_at, before_candidate_id)
            page = FarmEconomicCandidatePage(verification='requires_current_selection', source=source,
                items=[self._summary(row) for row in rows[:limit]],
                next_cursor=(FarmEconomicCandidateCursor(recorded_at=rows[limit-1]['recorded_at'].astimezone(timezone.utc),
                    candidate_id=rows[limit-1]['candidate_id']) if len(rows) > limit else None))
            if self._source(tenant, research_job_id, collection_job_id) != source:
                raise FarmEconomicCandidateHold()
            return page
        except PermissionError:
            raise
        except Exception:
            raise FarmEconomicCandidateHold('farm economic candidate references unavailable') from None
        finally:
            self._guard(tenant, pointers)

    def _current(self, tenant, source, row):
        _, scenario, record = MarketScenarioService(self.economic.candidates).validate_pinned(
            row['scenario_id'], row['revision'], tenant)
        hold = self.economic.candidates._source._holds.get_market_hold_report(scenario.market_context.hold_report_id)
        start, end = self._dates(source)
        if (record['candidate_id'] != row['candidate_id'] or
                record['economic_scenario_sha256'] != row['scenario_sha256'] or
                scenario.decision_at != datetime.fromisoformat(source.decision_at_utc) or
                not scenario.period_start <= start <= end <= scenario.period_end or hold is None or
                (hold['tenant_id'], hold['snapshot_id'], hold['decision_context_id'],
                 hold['decision_at'], hold['claim_mode'], hold['decision_time_kind']) !=
                (tenant, source.snapshot_id, source.decision_context_id,
                 datetime.fromisoformat(source.decision_at_utc), source.claim_mode, source.decision_time_kind)):
            raise FarmEconomicCandidateHold()
        return FarmEconomicSelection(verification='requires_registration_recheck', source=source,
            economic=EconomicPin(scenario_id=row['scenario_id'], revision=row['revision'],
                sha256=row['scenario_sha256'], candidate_id=row['candidate_id']),
            market_context=scenario.market_context, period_start=scenario.period_start,
            period_end=scenario.period_end, recorded_at=row['recorded_at'].astimezone(timezone.utc))

    def get(self, tenant, research_job_id, collection_job_id, candidate_id):
        require_digest(candidate_id)
        pointers = self._pointers()
        self._guard(tenant, pointers)
        try:
            source = self._source(tenant, research_job_id, collection_job_id)
            if source is None:
                return None
            candidates = self.economic.candidates
            with candidates.connect() as conn:
                row = conn.execute(sql.SQL('SELECT candidate_id, scenario_id, revision, scenario_sha256, '
                    'recorded_at FROM {} WHERE tenant_id=%s AND candidate_id=%s')
                    .format(candidates._table('market_candidate_pins')), (tenant, candidate_id)).fetchone()
            if row is None:
                return None
            selected = self._current(tenant, source, row)
            if self._current(tenant, source, row) != selected or self._source(
                    tenant, research_job_id, collection_job_id) != source:
                raise FarmEconomicCandidateHold()
            return selected
        except PermissionError:
            raise
        except Exception:
            raise FarmEconomicCandidateHold('farm economic candidate references unavailable') from None
        finally:
            self._guard(tenant, pointers)
