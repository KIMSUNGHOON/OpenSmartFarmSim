"""Readonly DB-accepted joint pages; internal records, before public projection."""
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
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
VERSION = 'joint-crop-climate-prefix-read-v2'
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
class PrefixRead:
    payload_raw: bytes = field(repr=False)
    payload_sha256: str


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

    @contextmanager
    def _session(self, tenant, request_raw, binding_raw):
        self._guard(tenant)
        server = self.server
        server.binding._guard(tenant, False)
        request = server.binding._request(request_raw)
        files = custody.files
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
                value = server.input_resolver(tenant, request['input']['source_sha256'], request['input']['evidence_sha256'])
                _need(type(value) is tuple and len(value) == 2 and isinstance(value[0], (str, Path)) and type(value[1]) is bytes)
                return server.binding.current(tenant, request_raw, value[0], value[1], binding_raw, write=False)
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

    def _ancestry(self, session, live_head, selected):
        proof, digest = session._selected(live_head)
        target = selected['custody_sequence']
        for _ in range(checkpoints.MAX_EVENTS):
            _need(proof['sequence'] >= target)
            if proof['sequence'] == target:
                _need(custody._head(proof['head']) == selected['head_sha256'] and digest == selected['proof_sha256'])
                return
            parent = proof['parent']
            raw = custody.files._read(session.proofs, parent['head_sha256'] + '.json', custody.LIMITS['proof_bytes'])
            value = custody._checked(raw, self.server.integrity_key, custody.PROOF_DOMAIN, custody.LIMITS['proof_bytes'])
            proof, digest = session._proof(value['head'])
            _need(digest == parent['proof_sha256'])
        raise JointPrefixHold('joint prefix ancestry unavailable')

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
            live_head, live_sha = reader._head()
            self._ancestry(session, live_head, latest['reason'])
            if chosen != latest:
                self._ancestry(session, live_head, p)
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
            if reader._head()[1] != live_sha:
                raise JointPrefixPending('joint prefix changed during read')
        session._guard()
        return {'selection': {'checkpoint': p, 'checkpoint_recorded_at': execution._utc(chosen['recorded_at']),
                    'checkpoint_attempt': chosen['attempt']},
            'binding': binding, 'manifest': context['manifest'], 'time_binding': header['binding'],
            'summary': summary if view == 'summary' else None, 'page': page}, live_sha

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
            with self.jobs.connect() as conn, ExitStack() as opened:
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
                session = live_sha = None
                if chosen is not None:
                    session = opened.enter_context(self._session(tenant, raw, binding_raw))
                    result, live_sha = self._accepted(session, chosen, latest, job, binding_raw, view, start, limit)
                self.query._current(tenant, value, raw, binding_raw)
                with self.jobs.connect() as probe:
                    probe.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                    if not execution._same(self.query._bundle(probe, tenant, job_id), bundle):
                        raise JointPrefixPending('joint prefix changed during read')
                    if chosen is not None:
                        frozen = {k: chosen['reason'][k] for k in ('publication_sequence', 'head_sha256', 'proof_sha256')}
                        if not execution._same(self._chosen(probe, tenant, job, latest, frozen), chosen):
                            raise JointPrefixPending('joint prefix changed during read')
                    at = execution._utc(probe.execute('SELECT clock_timestamp() AS at').fetchone()['at'])
                self.query._current(tenant, value, raw, binding_raw)
                if session is not None:
                    session._guard()
                    with storage._Files(session.path) as check:
                        if check._head()[1] != live_sha:
                            raise JointPrefixPending('joint prefix changed during read')
                result.update(version=VERSION, scope=custody.SCOPE, claim_scope=CLAIM_SCOPE, G0_G4='not_assessed',
                    job=execution.jobs_public.public_job_status(job).model_dump(mode='json'), cancel_requested=job['cancel_requested'],
                    observed_at=at, prefix_status='closed' if closed else 'none' if chosen is None else 'accepted')
                payload = storage._canonical(result)
                _need(1 <= len(payload) <= MAX_READ_BYTES)
            self.query._current(tenant, value, raw, binding_raw)
            self._guard(tenant)
            return PrefixRead(payload, sha256(payload).hexdigest())
        except (PermissionError, RolePolicyHold, JointPrefixPending, JointPrefixSelectionConflict, JointPrefixRequestRejected):
            raise
        except (custody.JointCustodyPending, execution.JointExecutionQueryPending):
            raise JointPrefixPending('joint prefix temporarily unavailable') from None
        except Exception:
            raise JointPrefixHold('joint prefix evidence unavailable') from None
