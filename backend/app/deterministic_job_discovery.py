"""Bounded advisory discovery with closed simulation and collection profiles."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from uuid import UUID

from psycopg import sql

from .job_store import JobStore
from .jobs import MAX_INPUT_BYTES, canonical_input_bytes, require_name
from .runtime_roles import RuntimeLoginPolicy, audit_runtime_roles


INPUT_VERSIONS = frozenset({
    'economic-calculation-input-v1', 'economic-calculation-input-v2',
    'economic-calculation-input-v3', 'break-even-calculation-input-v1',
    'break-even-verification-input-v1',
})


class DiscoveryHold(ValueError):
    """A closed discovery failure with a fixed public reason."""


@dataclass(frozen=True)
class DiscoveryCursor:
    created_at: datetime
    job_id: str

    def __post_init__(self):
        try:
            if (type(self.created_at) is not datetime or self.created_at.tzinfo is None or
                    self.created_at.utcoffset() != timedelta(0) or
                    type(self.job_id) is not str or str(UUID(self.job_id)) != self.job_id):
                raise ValueError
        except Exception:
            raise DiscoveryHold('discovery_page_rejected') from None


@dataclass(frozen=True)
class DiscoveredJob:
    job_id: str
    input_version: str


@dataclass(frozen=True)
class DiscoveryPage:
    jobs: tuple[DiscoveredJob, ...]
    scanned_count: int
    next_cursor: DiscoveryCursor | None


class DeterministicJobDiscovery:
    def _profile(self):
        if type(self) is DeterministicJobDiscovery:
            return ('simulation', 'simulating', INPUT_VERSIONS,
                    frozenset({'metadata', 'simulation_execute'}))
        if type(self) is CollectionJobDiscovery:
            return ('collection', 'collecting', frozenset({'owned-fixture-collection-input-v1'}),
                    frozenset({'metadata', 'artifact', 'collection_execute'}))
        raise DiscoveryHold('discovery_binding_rejected')

    def __init__(self, jobs, *, tenant_id, input_versions):
        try:
            require_name(tenant_id, 'tenant_id')
            self._profile_bound = self._profile()
            if (type(tenant_id) is not str or type(jobs) is not JobStore or
                    type(input_versions) is not frozenset or not input_versions or
                    any(type(value) is not str for value in input_versions) or
                    not input_versions <= self._profile_bound[2]):
                raise ValueError
            self.jobs = jobs
            self.tenant_id = tenant_id
            self.input_versions = input_versions
            self._bound = (jobs, tenant_id, input_versions, jobs._dsn, jobs.schema,
                           jobs.runtime_identity, jobs.principal_provider)
            self._binding()
        except Exception:
            raise DiscoveryHold('discovery_binding_rejected') from None

    def _binding(self):
        jobs, tenant, versions, dsn, schema, identity, provider = self._bound
        if (self._profile() != self._profile_bound or self.jobs is not jobs or self.tenant_id != tenant or
                type(self.input_versions) is not frozenset or self.input_versions != versions or type(jobs) is not JobStore or
                type(dsn) is not str or not dsn or jobs._dsn != dsn or jobs.schema != schema or
                type(identity) is not tuple or len(identity) != 2 or
                type(identity[0]) is not RuntimeLoginPolicy or identity[1] != 'authority' or
                identity[0].schema != schema or jobs.runtime_identity != identity or
                jobs.principal_provider is not provider or not callable(provider) or
                jobs.audit_runtime_grants is not True):
            raise DiscoveryHold('discovery_binding_rejected')

    def _access(self):
        self._binding()
        scopes = self.jobs._principal_scopes(self.tenant_id)
        self._binding()
        if not self._profile_bound[3] <= scopes:
            raise DiscoveryHold('discovery_access_rejected')

    @staticmethod
    def _version(row):
        try:
            raw = JobStore._verified_input(row)
            if not 1 <= len(raw) <= MAX_INPUT_BYTES:
                raise ValueError
            value = json.loads(raw)
            if canonical_input_bytes(value) != raw:
                raise ValueError
            version = value.get('input_version')
            return version if type(version) is str else None
        except Exception:
            raise DiscoveryHold('discovery_input_rejected') from None

    def page(self, *, cursor=None, limit=25):
        if type(limit) is not int or not 1 <= limit <= 50 or (
                cursor is not None and type(cursor) is not DiscoveryCursor):
            raise DiscoveryHold('discovery_page_rejected')
        if cursor is not None:
            cursor.__post_init__()
        self._access()
        try:
            after = sql.SQL('')
            stage, active = self._profile_bound[:2]
            params = [self.tenant_id, stage, active]
            if cursor is not None:
                after = sql.SQL('AND (created_at, job_id) > (%s, %s)')
                params.extend((cursor.created_at, UUID(cursor.job_id)))
            params.append(limit)
            with self.jobs.connect() as conn:
                conn.execute('SET TRANSACTION READ ONLY')
                rows = conn.execute(sql.SQL("""
                    SELECT job_id, created_at, input_sha256, input_bytes FROM {}
                    WHERE tenant_id = %s AND stage = %s AND (
                        (state = 'queued' AND next_attempt_at <= clock_timestamp()) OR
                        (state = %s AND lease_until <= clock_timestamp())
                    ) {} ORDER BY created_at, job_id LIMIT %s
                """).format(self.jobs._table('jobs'), after), params).fetchall()
                matches = []
                last = None
                for row in rows:
                    created_at = row['created_at']
                    if type(created_at) is not datetime or created_at.tzinfo is None:
                        raise DiscoveryHold('discovery_read_rejected')
                    last = DiscoveryCursor(created_at.astimezone(timezone.utc), str(row['job_id']))
                    version = self._version(row)
                    if version in self.input_versions:
                        matches.append(DiscoveredJob(last.job_id, version))
                self._access()
                audit_runtime_roles(conn, self.jobs.runtime_identity[0])
                self._binding()
            return DiscoveryPage(tuple(matches), len(rows), last if len(rows) == limit else None)
        except DiscoveryHold:
            raise
        except Exception:
            raise DiscoveryHold('discovery_read_rejected') from None


class CollectionJobDiscovery(DeterministicJobDiscovery):
    def __init__(self, jobs, *, tenant_id):
        super().__init__(jobs, tenant_id=tenant_id,
                         input_versions=frozenset({'owned-fixture-collection-input-v1'}))
