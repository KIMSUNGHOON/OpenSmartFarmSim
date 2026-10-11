"""Readonly DB-accepted joint pages; internal records, before public projection."""
from contextlib import ExitStack, contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from uuid import UUID

from psycopg import sql

from . import crop_climate_joint_execution_query as execution
from .runtime_roles import RolePolicyHold

checkpoints = execution.checkpoints
custody = execution.custody
storage = custody.storage
VERSION = 'joint-crop-climate-prefix-read-v5'
CLAIM_SCOPE = 'synthetic_joint_crop_climate_confirmed_prefix_only'
MAX_READ_BYTES = storage.LIMITS['page_bytes'] + 2 * checkpoints.execution.MAX_INPUT_BYTES + storage.LIMITS['metadata_bytes']
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES = {'execution_query': execution, 'storage': storage, 'custody': custody, 'checkpoints': checkpoints}
_DEPENDENCIES = {k: sha256(Path(v.__file__).read_bytes()).hexdigest() for k, v in _MODULES.items()}
_FIXED = (VERSION, CLAIM_SCOPE, MAX_READ_BYTES, CODE_SHA256, storage._canonical(_DEPENDENCIES))


class JointPrefixHold(ValueError):
    pass


class JointPrefixPending(ValueError):
    pass


class JointPrefixSelectionConflict(ValueError):
    pass


class JointPrefixRequestRejected(ValueError):
    pass


@dataclass(frozen=True)
class _ReadWitness:
    owner: object = field(repr=False)
    tenant: str = field(repr=False)
    job_id: str = field(repr=False)
    bundle: tuple = field(repr=False)
    payload_sha256: str = field(repr=False)
    chosen: dict | None = field(default=None, repr=False)
    observed_head: dict | None = field(default=None, repr=False)


@dataclass(frozen=True)
class PrefixRead:
    payload_raw: bytes = field(repr=False)
    payload_sha256: str
    _witness: _ReadWitness | None = field(default=None, repr=False, compare=False)


def _same_job_datetimes(before, after, ignored=()):
    try:
        for key in before:
            if key in ignored: continue
            a, b = before[key], after[key]
            if type(a) is datetime or type(b) is datetime:
                if (type(a) is not datetime or type(b) is not datetime
                        or a.utcoffset() is None or b.utcoffset() is None
                        or a.astimezone(timezone.utc) != b.astimezone(timezone.utc)):
                    return False
        return True
    except (TypeError, ValueError, OverflowError):
        return False


def _same_job_row(before, after):
    if type(before) is not dict or type(after) is not dict or before.keys() != after.keys():
        return False
    if not (before.get('state') == after.get('state') == 'simulating'
            and before.get('cancel_requested') is after.get('cancel_requested') is False):
        return execution._same(before, after) and _same_job_datetimes(before, after)
    try:
        if (before['stage'] != 'simulation' or type(before['attempt_count']) is not int or before['attempt_count'] < 1
                or type(before['lease_token']) is not str or not before['lease_token']):
            return False
        times = ('lease_until', 'updated_at')
        for key in times:
            a, b = before[key], after[key]
            if (type(a) is not datetime or type(b) is not datetime
                    or a.utcoffset() is None or b.utcoffset() is None
                    or b.astimezone(timezone.utc) < a.astimezone(timezone.utc)):
                return False
        return (execution._same({k: v for k, v in before.items() if k not in times},
            {k: v for k, v in after.items() if k not in times}) and _same_job_datetimes(before, after, times))
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def _same_bundle(before, after):
    return (type(before) is type(after) is tuple and len(before) == len(after) == 6
        and _same_job_row(before[0], after[0]) and execution._same(before[1:], after[1:]))


def _need(value):
    if not value:
        raise JointPrefixHold('joint prefix evidence unavailable')


def _selector(value):
    if (type(value) is not dict or set(value) != {'publication_sequence', 'head_sha256', 'proof_sha256'}
            or type(value['publication_sequence']) is not int
            or not 1 <= value['publication_sequence'] <= checkpoints.MAX_EVENTS
            or not all(custody._digest(value[k]) for k in ('head_sha256', 'proof_sha256'))):
        raise JointPrefixRequestRejected('joint prefix selector rejected')
    return dict(value)


class JointExecutionPrefixQuery:
    def __init__(self, query):
        _need(type(query) is execution.JointExecutionQuery)
        self.query, self.jobs, self.server = query, query.jobs, query.server
        self._fixed = (query, query._pointers(), self.jobs, self.server)
        self._binding()

    def _binding(self):
        _need((self.query, self.query._pointers(), self.jobs, self.server) == self._fixed
            and (VERSION, CLAIM_SCOPE, MAX_READ_BYTES, CODE_SHA256, storage._canonical(_DEPENDENCIES)) == _FIXED
            and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
            and {k: sha256(Path(v.__file__).read_bytes()).hexdigest() for k, v in _MODULES.items()} == _DEPENDENCIES)
        self.query._binding()

    def _guard(self, tenant):
        self._binding()
        self.query._guard(tenant)
        self._binding()

    def _witness_for(self, tenant, job_id, record):
        if type(record) is not PrefixRead or type(record._witness) is not _ReadWitness:
            return None
        w = record._witness
        valid = (w.owner is self and w.tenant == tenant and w.job_id == job_id
            and type(record.payload_raw) is bytes
            and w.payload_sha256 == record.payload_sha256 == sha256(record.payload_raw).hexdigest()
            and type(w.bundle) is tuple and len(w.bundle) == 6 and type(w.bundle[0]) is dict
            and w.bundle[0].get('tenant_id') == tenant
            and str(w.bundle[0].get('job_id')) == job_id)
        return w if valid else None

    def _unchanged(self, tenant, job_id, record, bundle):
        w = self._witness_for(tenant, job_id, record)
        return w is not None and _same_bundle(w.bundle, bundle)

    def _after_projection(self, tenant, job_id, record):
        self._guard(tenant)
        w = self._witness_for(tenant, job_id, record)
        if w is None:
            raise JointPrefixPending('joint prefix changed during response')
        payload = json.loads(record.payload_raw)
        if w.chosen is None:
            if payload['selection'] is not None or w.observed_head is not None:
                raise JointPrefixPending('joint prefix changed during response')
        elif (type(w.chosen) is not dict or type(w.observed_head) is not dict
                or not execution._same(payload['selection'], {
                    'checkpoint': w.chosen['reason'], 'checkpoint_attempt': w.chosen['attempt'],
                    'checkpoint_recorded_at': execution._utc(w.chosen['recorded_at'])})):
            raise JointPrefixPending('joint prefix changed during response')
        with self.jobs.connect() as conn:
            conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            bundle = self.query._bundle(conn, tenant, job_id)
            if bundle is None:
                raise JointPrefixPending('joint prefix changed during response')
            value, raw, binding = self.query.checkpoints._input(tenant, bundle[0])
            self.query._current(tenant, value, raw, binding)
            if w.chosen is None:
                if not self._unchanged(tenant, job_id, record, bundle):
                    raise JointPrefixPending('joint prefix changed during response')
            else:
                with self._session(tenant, raw, binding) as session:
                    self._refresh(conn, tenant, w.bundle, bundle, w.chosen, session, w.observed_head, binding)
            self.query._current(tenant, value, raw, binding)
        self._guard(tenant)

    @contextmanager
    def _session(self, tenant, request_raw, binding_raw):
        self._guard(tenant)
        server = self.server
        server.binding._guard(tenant, False)
        request = server.binding._request(request_raw)
        files = custody.files
        binding = files.inputs._json(binding_raw)
        _need(binding['tenant_id'] == tenant and execution._same(binding['request'], request))
        with ExitStack() as opened:
            def keep(fd):
                opened.callback(os.close, fd)
                return fd
            root = keep(files.job_store._open_directory_nofollow(server.directory))
            identity = custody._intent_id(tenant, request)
            intent = keep(files._directory(root, identity, create=False))
            intent_raw = files._read(intent, 'intent.json', custody.LIMITS['intent_bytes'])
            signed = custody._checked(intent_raw, server.integrity_key, custody.INTENT_DOMAIN, custody.LIMITS['intent_bytes'])
            expected = {'version': custody.INTENT_VERSION, 'scope': custody.SCOPE, 'G0_G4': 'not_assessed',
                'tenant_id': tenant, 'intent_id': identity, 'request_sha256': custody._hash(request_raw),
                'binding': files.inputs._json(binding_raw), 'resolver_version': server.input_resolver.version,
                'custody_code_sha256': custody.CODE_SHA256, 'dependency_sha256': custody.DEPENDENCY_SHA256,
                'limits': custody.LIMITS}
            _need(execution._same(signed, expected))
            proofs = keep(files._directory(intent, 'proofs', create=False))
            artifact = keep(files._directory(intent, 'artifact', create=False))
            def current():
                server._binding()
                binder = server.binding
                binder._guard(tenant, False)
                value = server.input_resolver(tenant, request['input']['source_sha256'], request['input']['evidence_sha256'])
                _need(type(value) is tuple and len(value) == 2 and isinstance(value[0], (str, Path)) and type(value[1]) is bytes)
                source = binder._input(request, value[0], value[1])
                _need(execution._same(source, binding['input'])
                    and binding['rights_policy_version'] == binder.input_rights.policy_version)
                binder._rights(tenant, request, source, False)
                binder._guard(tenant, False)
                binder._rights(tenant, request, source, False)
                _need(execution._same(binder._input(request, value[0], value[1]), source))
                binder._guard(tenant, False)
                return binding_raw
            session = custody._Session(server, root, intent, proofs, artifact, identity, intent_raw, binding_raw, current)
            session._guard()
            yield session
            session._guard()

    def _chosen(self, conn, tenant, job, latest, selector):
        if selector is None:
            return latest
        rows = conn.execute(sql.SQL('SELECT event_id,attempt,reason,recorded_at FROM {} '
            'WHERE tenant_id=%s AND job_id=%s AND kind=%s AND reason->>\'publication_sequence\'=%s LIMIT 2')
            .format(self.jobs._table('job_events')),
            (tenant, job['job_id'], checkpoints.EVENT_KIND, str(selector['publication_sequence']))).fetchall()
        if len(rows) != 1 or any(rows[0]['reason'][k] != selector[k] for k in selector):
            raise JointPrefixSelectionConflict('joint prefix selection unavailable')
        return rows[0]

    def _ancestry(self, session, live_head, *selected):
        proof, digest = session._selected(live_head)
        observed = {'custody_sequence': proof['sequence'],
            'head_sha256': custody._head(live_head), 'proof_sha256': digest}
        pending = {(p['custody_sequence'], p['head_sha256'], p['proof_sha256']) for p in selected}
        _need(pending and all(type(n) is int and 0 <= n < checkpoints.MAX_EVENTS
            and custody._digest(h) and custody._digest(d) for n, h, d in pending))
        for _ in range(checkpoints.MAX_EVENTS):
            _need(proof['sequence'] >= min(p[0] for p in pending))
            current = (proof['sequence'], custody._head(proof['head']), digest)
            _need(all(p == current for p in pending if p[0] == current[0]))
            pending.discard(current)
            if not pending:
                return observed
            parent = proof['parent']
            raw = custody.files._read(session.proofs, parent['head_sha256'] + '.json', custody.LIMITS['proof_bytes'])
            value = custody._checked(raw, self.server.integrity_key, custody.PROOF_DOMAIN, custody.LIMITS['proof_bytes'])
            previous_sequence = proof['sequence']
            proof, digest = session._proof(value['head'])
            _need(digest == parent['proof_sha256'] and custody._head(proof['head']) == parent['head_sha256']
                and proof['sequence'] == previous_sequence - 1)
        raise JointPrefixHold('joint prefix ancestry unavailable')

    def _current_head(self, session, *selected):
        with storage._Files(session.path) as reader:
            head, _ = reader._head()
            return self._ancestry(session, head, *selected)

    def _refresh(self, conn, tenant, before, after, chosen, session, observed_head, binding):
        if (type(before) is not tuple or type(after) is not tuple or len(before) != 6 or len(after) != 6
                or not _same_job_row(before[0], after[0]) or not execution._same(before[2:], after[2:])):
            raise JointPrefixPending('joint prefix changed during read')
        previous, latest = before[1], after[1]
        _need(previous is not None and latest is not None)
        if latest['reason']['publication_sequence'] < previous['reason']['publication_sequence']:
            raise JointPrefixHold('joint prefix history unavailable')
        for event in (chosen, previous):
            pin = {k: event['reason'][k] for k in ('publication_sequence', 'head_sha256', 'proof_sha256')}
            try:
                current = self._chosen(conn, tenant, after[0], latest, pin)
            except JointPrefixSelectionConflict:
                raise JointPrefixPending('joint prefix changed during read') from None
            if not execution._same(current, event) or not _same_job_datetimes(current, event):
                raise JointPrefixPending('joint prefix changed during read')
        changed = not execution._same(previous, latest) or not _same_job_datetimes(previous, latest)
        active = before[0]['state'] == 'simulating' and before[0]['cancel_requested'] is False
        if changed and (not active or latest['reason']['publication_sequence'] == previous['reason']['publication_sequence']):
            raise JointPrefixPending('joint prefix changed during read')
        session._guard()
        head = self._current_head(session, observed_head, chosen['reason'], previous['reason'], latest['reason'])
        if changed:
            _, verified = self._accepted(session, latest, latest, after[0], binding, 'summary', 0, None)
            head = self._current_head(session, head, verified)
        if not active and not execution._same(head, observed_head):
            raise JointPrefixPending('joint prefix changed during read')
        session._guard()
        return head

    @staticmethod
    def _page(reader, data, kind, start, limit):
        header, context, _, _, _, _, index, counts = data
        if start > counts[kind]:
            raise JointPrefixRequestRejected('joint prefix range rejected')
        end = min(counts[kind], start + limit)
        records = []
        for d in index[kind]:
            if d['start'] >= end or d['start'] + d['count'] <= start:
                continue
            reader._blob(d['commit_sha256'], storage.LIMITS['metadata_bytes'])
            descriptor = {k: v for k, v in d.items() if k not in ('start', 'commit_sha256')}
            values, times = reader._records(kind, [descriptor], header['binding'], context['program'])
            lo, hi = max(0, start-d['start']), min(d['count'], end-d['start'])
            records.extend({'value': values[i], 'time': times[i]} for i in range(lo, hi))
        page = {'kind': kind, 'start': start, 'limit': limit, 'total': counts[kind],
            'next_offset': end if end < counts[kind] else None, 'records': records}
        _need(len(records) == end-start and len(storage._canonical(page)) <= storage.LIMITS['page_bytes'])
        return page

    def _accepted(self, session, chosen, latest, job, binding_raw, view, start, limit):
        p = checkpoints._payload(chosen['reason'])
        _need(session.binding_raw == binding_raw and p['input_sha256'] == job['input_sha256']
            and p['farm_binding_sha256'] == session.binding_sha256 and p['intent_sha256'] == session.intent_sha256)
        binding = json.loads(binding_raw)
        _need(all(p[k] == binding['input'][k] for k in ('source_sha256', 'context_sha256', 'time_binding_sha256')))
        raw = custody.files._read(session.proofs, p['head_sha256'] + '.json', custody.LIMITS['proof_bytes'])
        signed = custody._checked(raw, self.server.integrity_key, custody.PROOF_DOMAIN, custody.LIMITS['proof_bytes'])
        head = signed['head']
        proof, digest = session._selected(head)
        _need(custody._head(head) == p['head_sha256'] and digest == p['proof_sha256']
            and proof['sequence'] == p['custody_sequence'] and head['header_sha256'] == p['header_sha256']
            and head['artifact_sha256'] == p['artifact_sha256'])
        with storage._Files(session.path) as reader:
            live_head, _ = reader._head()
            observed = self._ancestry(session, live_head, latest['reason'], p)
            data = reader._load(head)
            header, context, commits, cp, last, times, index, counts = data
            status = 'ready' if last is None else last['status']
            _need(header['context_sha256'] == p['context_sha256'] and header['binding_sha256'] == p['time_binding_sha256']
                and status == p['status'] and counts == p['counts']
                and p['planned_steps'] == context['program']['step_count']
                and p['steps'] == (0 if last is None else last['steps'])
                and p['computed_through_utc'] == (None if times is None else times['last_confirmed']['at']))
            if head['artifact_sha256'] is not None:
                root, _ = reader._blob(head['artifact_sha256'], storage.LIMITS['root_bytes'])
                _need(root == {'version': storage.VERSION, 'header_sha256': head['header_sha256'],
                    'commits': commits, 'status': status, 'counts': counts,
                    'final_checkpoint_sha256': None if cp is None else cp['sha256']})
            summary = {'counts': counts, **{'last_'+k[:-1]+'_utc': rows[-1]['last_at'] if rows else None for k, rows in index.items()}}
            page = None if view == 'summary' else self._page(reader, data, view, start, limit)
            head = self._ancestry(session, reader._head()[0], observed, latest['reason'], p)
            if job['state'] != 'simulating' and not execution._same(head, observed):
                raise JointPrefixPending('joint prefix changed during read')
        session._guard()
        return {'selection': {'checkpoint': p, 'checkpoint_recorded_at': execution._utc(chosen['recorded_at']),
                    'checkpoint_attempt': chosen['attempt']},
            'binding': binding, 'manifest': context['manifest'], 'time_binding': header['binding'],
            'summary': summary if view == 'summary' else None, 'page': page}, head

    def read(self, tenant, job_id, selector=None, view='summary', start=0, limit=None):
        try:
            if type(job_id) is not str or str(UUID(job_id)) != job_id:
                raise ValueError()
        except Exception:
            raise JointPrefixRequestRejected('joint prefix job ID rejected') from None
        selector = None if selector is None else _selector(selector)
        if (view not in ('summary', 'samples', 'events') or type(start) is not int or start < 0
                or (view == 'summary' and (start != 0 or limit is not None))
                or (view != 'summary' and selector is None)):
            raise JointPrefixRequestRejected('joint prefix request rejected')
        if view != 'summary':
            maximum = storage.LIMITS[view+'_per_page']
            limit = maximum if limit is None else limit
            if type(limit) is not int or not 1 <= limit <= maximum:
                raise JointPrefixRequestRejected('joint prefix limit rejected')
        try:
            self._guard(tenant)
            with ExitStack() as opened:
                with self.jobs.connect() as conn:
                    conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                    bundle = self.query._bundle(conn, tenant, job_id)
                    if bundle is None:
                        self._guard(tenant)
                        return None
                    job, latest = bundle[:2]
                    if job['stage'] != 'simulation' or json.loads(self.jobs._verified_input(job)).get('input_version') != checkpoints.execution.INPUT_VERSION:
                        self._guard(tenant)
                        return None
                    value, raw, binding_raw = self.query.checkpoints._input(tenant, job)
                    self.query._current(tenant, value, raw, binding_raw)
                    if latest:
                        p = latest['reason']; source = value['request']['input']
                        _need(p['farm_binding_sha256'] == value['farm_binding_sha256']
                            and all(p[k] == source[k] for k in ('source_sha256', 'context_sha256', 'time_binding_sha256')))
                    closed = job['cancel_requested'] or job['state'] not in ('queued', 'simulating')
                    chosen = None if closed else self._chosen(conn, tenant, job, latest, selector)
                if chosen is None and view != 'summary':
                    raise JointPrefixSelectionConflict('joint prefix selection unavailable')
                result = dict.fromkeys(('selection', 'binding', 'manifest', 'time_binding', 'summary', 'page'))
                session = observed_head = None
                if chosen is not None:
                    session = opened.enter_context(self._session(tenant, raw, binding_raw))
                    result, observed_head = self._accepted(session, chosen, latest, job, binding_raw, view, start, limit)
                self.query._current(tenant, value, raw, binding_raw)
                with self.jobs.connect() as probe:
                    probe.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                    probe_bundle = self.query._bundle(probe, tenant, job_id)
                    if chosen is not None:
                        observed_head = self._refresh(probe, tenant, bundle, probe_bundle, chosen,
                            session, observed_head, binding_raw)
                    elif not _same_bundle(bundle, probe_bundle):
                        raise JointPrefixPending('joint prefix changed during read')
                    at = execution._utc(probe.execute('SELECT clock_timestamp() AS at').fetchone()['at'])
                    job = probe_bundle[0]
                self.query._current(tenant, value, raw, binding_raw)
                if session is not None:
                    session._guard()
                    observed_head = self._current_head(session, observed_head, chosen['reason'], probe_bundle[1]['reason'])
                result.update(version=VERSION, scope=custody.SCOPE, claim_scope=CLAIM_SCOPE, G0_G4='not_assessed',
                    job=execution.jobs_public.public_job_status(job).model_dump(mode='json'), cancel_requested=job['cancel_requested'],
                    observed_at=at, prefix_status='closed' if closed else 'none' if chosen is None else 'accepted')
                payload = storage._canonical(result)
                _need(1 <= len(payload) <= MAX_READ_BYTES)
            self.query._current(tenant, value, raw, binding_raw)
            self._guard(tenant)
            digest = sha256(payload).hexdigest()
            return PrefixRead(payload, digest, _ReadWitness(self, tenant, job_id, deepcopy(probe_bundle), digest,
                deepcopy(chosen), deepcopy(observed_head)))
        except (PermissionError, RolePolicyHold, JointPrefixPending, JointPrefixSelectionConflict, JointPrefixRequestRejected):
            raise
        except (custody.JointCustodyPending, execution.JointExecutionQueryPending):
            raise JointPrefixPending('joint prefix temporarily unavailable') from None
        except Exception:
            raise JointPrefixHold('joint prefix evidence unavailable') from None
