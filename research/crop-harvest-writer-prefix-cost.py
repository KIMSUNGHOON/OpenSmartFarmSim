"""Measure a normal unpublished harvest prefix on an authenticated preserved parent."""
from contextlib import contextmanager
from decimal import localcontext
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import secrets
from time import perf_counter
from unittest.mock import patch

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


storage = module('harvest_prefix_storage', ROOT/'research/crop-harvest-storage-preservation.py')
capacity = module('harvest_prefix_capacity', ROOT/'research/crop-harvest-full-capacity.py')
backup, registry, harvest = storage.backup, storage.registry, storage.harvest
replay, canonical, need = registry.replay, storage.canonical, storage.need
VERSION = 'owned-harvest-writer-prefix-cost-v1'
PROFILE_REVISION = 'full166-preserved-parent-synthetic-v2'
PAGE_COUNT = 2


class PrefixStop(Exception):
    """The second normal immutable page was written, without publishing a root."""


def revise_profiles(mass_raw, allocation_raw):
    mass, _ = harvest._mass_parameters(mass_raw)
    allocation, _ = harvest._allocation_parameters(allocation_raw, harvest._mass_parameters(mass_raw))
    mass['revision'] = PROFILE_REVISION;mass_raw = canonical(mass)
    allocation['revision'] = PROFILE_REVISION
    allocation['mass_parameter_sha256'] = sha256(mass_raw).hexdigest()
    allocation_raw = canonical(allocation)
    harvest._allocation_parameters(allocation_raw, harvest._mass_parameters(mass_raw))
    return mass_raw, allocation_raw


class PrefixBoundary:
    def __init__(self, directory):
        self.directory = Path(directory);self.pages = [];self.stopped = False

    def __enter__(self):
        need(not self.directory.exists() or not any(self.directory.iterdir()))
        original = replay._put
        def bounded(fd, raw, maximum):
            if self.stopped:raise PrefixStop('owned normal two-page boundary')
            other = replay.files._open_directory_nofollow(self.directory)
            try:
                expected = replay.files._secure(other, directory=True);actual = replay.files._secure(fd, directory=True)
                need((expected.st_dev, expected.st_ino) == (actual.st_dev, actual.st_ino))
            finally:os.close(other)
            rows = replay.current.inputs._json(raw)
            need(type(rows) is list and 1 <= len(rows) <= replay.LIMITS['page_records']
                 and canonical(rows) == raw and maximum == replay.LIMITS['page_bytes'])
            started = perf_counter();digest = original(fd, raw, maximum)
            need(digest == sha256(raw).hexdigest())
            self.pages.append({'sha256': digest, 'count': len(rows), 'bytes': len(raw),
                'put_seconds': perf_counter()-started})
            if len(self.pages) == PAGE_COUNT:
                self.stopped = True;raise PrefixStop('owned normal two-page boundary')
            return digest
        self._patch = patch.object(replay, '_put', bounded);self._patch.__enter__()
        return self

    def __exit__(self, *args):return self._patch.__exit__(*args)


class QueryTrace:
    def __init__(self, query):
        self.query = query;self.original = None;self.phase = 'preparation'
        self.calls = [];self.samples = {};self.events = {}

    def __enter__(self):
        original = type(self.query).read
        def observed(instance, *args, **kwargs):
            need(instance is self.query);started = perf_counter()
            value = original(instance, *args, **kwargs);seconds = perf_counter()-started
            if self.original is None:self.original = value
            harvest._same(value, self.original)
            kind = kwargs.get('kind');page = value['page']
            self.calls.append({'phase': self.phase, 'kind': kind, 'start': kwargs.get('start', 0),
                'limit': kwargs.get('limit'), 'seconds': seconds,
                'count': len(page['records']) if page is not None else None})
            if self.phase == 'writer' and kind is not None:
                captured = self.samples if kind == 'samples' else self.events
                for offset, row in enumerate(page['records'], page['start']):
                    encoded = canonical(row)
                    need(offset not in captured or captured[offset] == encoded)
                    captured[offset] = encoded
                need(len(self.samples) <= 256 and len(self.events) <= 8)
            return value
        self._patch = patch.object(type(self.query), 'read', observed);self._patch.__enter__()
        return self

    def __exit__(self, *args):return self._patch.__exit__(*args)


def audit_prefix(directory, pages, samples, events, mass_raw, allocation_raw):
    mass = harvest._mass_parameters(mass_raw)
    allocation = harvest._allocation_parameters(allocation_raw, mass)
    need(len(pages) == PAGE_COUNT and samples and set(samples) == set(range(len(samples))))
    source_rows = [(i, json.loads(raw)) for i, raw in sorted(samples.items())]
    event_rows = [(i, json.loads(raw)) for i, raw in sorted(events.items())
                  if json.loads(raw)['at'] <= source_rows[-1][1]['at']]
    references = capacity.removals(iter(source_rows), iter(event_rows), mass[0]['source'])
    fd = replay.files._open_directory_nofollow(Path(directory));chain = sha256();count = 0
    try:
        with localcontext() as context:
            context.prec = 2200;checker = capacity.QuantityAudit(mass[0], allocation[0])
            for descriptor in pages:
                rows = replay._blob(fd, descriptor['sha256'], replay.LIMITS['page_bytes'])
                need(type(rows) is list and len(rows) == descriptor['count'])
                for row in rows:
                    _, reference = next(references);checker.add(row, reference)
                    chain.update(canonical(row)+b'\n');count += 1
            balances = {}
            for kind, fields in checker.balance.items():
                balances[kind] = {}
                for key, values in fields.items():
                    residual = abs(values['rounded']-values['original']);need(residual <= values['budget'])
                    balances[kind][key] = {'absolute_residual_decimal': str(residual),
                        'half_ULP_sum_budget_decimal': str(values['budget']), 'within_budget': True}
            need(count == checker.rows == sum(p['count'] for p in pages)
                 and chain.hexdigest() == checker.chain.hexdigest())
            return {'scope': 'two_unpublished_pages_only', 'rows': count,
                'terminal_rows': checker.terminal_count, 'event_rows': checker.event_count,
                'row_chain_sha256': chain.hexdigest(), 'decimal_precision': context.prec,
                'every_prefix_row_independently_checked': True, 'balances': balances,
                'whole_crop_totals_and_observations_evaluated': False}
    finally:references.close();os.close(fd)


@contextmanager
def registration(context, directory, current):
    directory = Path(directory);directory.mkdir(mode=0o700)
    policy, dsns = storage.install(context, directory)
    root = directory/'artifacts';root.mkdir(mode=0o700)
    try:
        yield registry.HarvestRegistry(current, policy, root, dsn=dsns['publisher'], integrity_key=secrets.token_bytes(32))
    finally:
        with psycopg.connect(context['admin']) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(policy.schema)))
            for role in (policy.publisher, policy.reader):
                conn.execute(sql.SQL('REVOKE CONNECT ON DATABASE {} FROM {}').format(
                    sql.Identifier(policy.database), sql.Identifier(role)))
            for role in (policy.publisher, policy.reader, policy.owner):
                conn.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
        for name in ('publisher.pgpass','reader.pgpass','publisher-dsn.private','reader-dsn.private'):
            (directory/name).unlink()
        with psycopg.connect(context['admin']) as conn:
            schemas = conn.execute('SELECT count(*) FROM pg_namespace WHERE nspname=%s', (policy.schema,)).fetchone()[0]
            roles = conn.execute('SELECT count(*) FROM pg_roles WHERE rolname=ANY(%s)',
                ([policy.publisher, policy.reader, policy.owner],)).fetchone()[0]
        need(schemas == roles == 0)
        backup.write(directory/'cleanup.private.json',canonical({'schemas_after': schemas, 'roles_after': roles, 'passfiles_after': 0}))


def measure(parent_path, parent_sha, stage):
    stage = Path(stage);stage.mkdir(mode=0o700);parent = backup.checked(parent_path, parent_sha)
    before_fd = capacity.fd_inventory();before_put = replay._put
    before_read = replay.current.CalculationCurrentCycleQuery.read
    with backup.readonly_guard(), backup.restored(parent_path, parent_sha, stage/'database') as context:
        current = backup.current_query(parent_path, parent_sha, context)
        def parent_counts():
            with current.store.jobs.connect() as conn:
                return {name: conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                    current.store.jobs._table(name))).fetchone()['n']
                    for name in ('jobs','job_events','crop_cycle_verified_research_results','thermal_g1_runs')}
        db_before = parent_counts()
        with QueryTrace(current) as trace:
            source, old_mass, old_allocation = storage.profiles(current, parent['original_record']['result_id'], parent['farm'])
            original = trace.original;packet = json.loads(original['record']['payload_raw'])
            need(packet['artifact']['sample_count'] >= 130 and original['terminal']['status'] == 'completed')
            mass_raw, allocation_raw = revise_profiles(old_mass, old_allocation)
            backup.write(stage/'mass.private.json',mass_raw);backup.write(stage/'allocation.private.json',allocation_raw)
            with registration(context, stage/'registration', current) as store:
                mass_sha = sha256(mass_raw).hexdigest();allocation_sha = sha256(allocation_raw).hexdigest()
                base = registry._base('tenant-1',parent['original_record']['result_id'],parent['farm'],source,
                    {'mass_sha256': mass_sha, 'allocation_sha256': allocation_sha})
                directory = store.directory/registry._key(base)
                def count():
                    with store._connection() as conn:
                        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                            sql.Identifier(store.policy.schema,registry.schema.TABLE))).fetchone()['n']
                need(count() == 0)
                rights = current.store.server.binding.input_rights;rights_call = type(rights).__call__
                def denied(instance, tenant, declaration, root, use):
                    if instance is rights and use == 'research_calculation':return False
                    return rights_call(instance, tenant, declaration, root, use)
                trace.phase = 'calculation-right-denied'
                with PrefixBoundary(directory) as refused, patch.object(type(rights), '__call__', denied):
                    try:store.put('tenant-1',parent['original_record']['result_id'],parent['farm'],mass_raw,allocation_raw)
                    except registry.HarvestRegistrationHold:pass
                    else:raise AssertionError('calculation right denial published')
                need(not refused.pages and not directory.exists() and count() == 0)
                trace.phase = 'writer';started = perf_counter()
                with PrefixBoundary(directory) as boundary:
                    try:store.put('tenant-1',parent['original_record']['result_id'],parent['farm'],mass_raw,allocation_raw)
                    except registry.HarvestRegistrationHold:need(boundary.stopped)
                    else:raise AssertionError('bounded prefix unexpectedly published')
                seconds = perf_counter()-started
                need(boundary.stopped and len(boundary.pages) == PAGE_COUNT and count() == 0)
                need(set(os.listdir(directory)) == {'.writer-lock', *(p['sha256']+'.json' for p in boundary.pages)})
                audit = audit_prefix(directory,boundary.pages,trace.samples,trace.events,mass_raw,allocation_raw)
                trace.phase = 'post-stop';need(current.read('tenant-1',parent['original_record']['result_id'],parent['farm']) == original)
                result = {'version': VERSION, 'scope': 'owned_synthetic_unpublished_prefix_only',
                    'source': source, 'profile_revision': PROFILE_REVISION, 'mass_sha256': mass_sha,
                    'allocation_sha256': allocation_sha, 'normal_registry_prefix_seconds': seconds,
                    'pages': boundary.pages, 'query_calls': trace.calls, 'audit': audit,
                    'source_sample_count': packet['artifact']['sample_count'], 'source_event_count': packet['artifact']['event_count'],
                    'HEAD_and_DB_unpublished': True, 'scoped_calculation_right_denied_and_restored': True,
                    'shared_rights_or_principal_files_modified': False, 'full_RHS_or_crop_publication_proof_calls': 0}
                with store._connection() as conn:need(conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256')
        need(parent_counts() == db_before)
    need(not (stage/'database/data/postmaster.pid').exists())
    need(capacity.fd_inventory() == before_fd and replay._put is before_put
         and replay.current.CalculationCurrentCycleQuery.read is before_read)
    result.update(FD_before_after=[len(before_fd),len(capacity.fd_inventory())],
        parent_DB_counts_before_after=[db_before,db_before], source_schema_role_passfile_cleanup=True,
        fresh_postmaster_absent=True, normal_methods_restored=True)
    backup.write(stage/'measured.private.json',canonical(result))
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser();parser.add_argument('--backup',required=True,type=Path)
    parser.add_argument('--sha256',required=True);parser.add_argument('--stage',required=True,type=Path)
    args = parser.parse_args();measure(args.backup,args.sha256,args.stage)


if __name__ == '__main__':main()
