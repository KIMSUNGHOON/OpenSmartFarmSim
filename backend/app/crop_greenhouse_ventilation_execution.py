"""Admit a current ventilation crop/climate input to one immutable simulation job."""
from hashlib import sha256
import json
from pathlib import Path

from psycopg import sql
from psycopg.types.json import Jsonb

from .crop_greenhouse_ventilation_farm_binding import VentilationFarmBinding
from .job_store import JobStore, JobIntentConflict
from .jobs import canonical_input_bytes, MAX_INPUT_BYTES, TERMINAL_STATES
from . import crop_result_store as permissions
from . import thermal_run_store as documents


INPUT_VERSION = 'joint-ventilation-execution-input-v1'
INTENT_DOMAIN = b'ossf-joint-ventilation-execution-intent-v1\0'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_CONTRACT = (INPUT_VERSION, INTENT_DOMAIN, MAX_INPUT_BYTES)


class VentilationExecutionHold(ValueError):
    pass


class VentilationExecutionService:
    def __init__(self, binding, *, input_resolver):
        try:
            if (type(binding) is not VentilationFarmBinding or not callable(input_resolver)
                    or not permissions._name(input_resolver.version)):
                raise ValueError()
            self.binding, self.input_resolver = binding, input_resolver
            self.jobs = binding.jobs
            self._fixed = self._pointers()
            self._binding()
        except Exception:
            raise VentilationExecutionHold('ventilation execution authority unavailable') from None

    def _pointers(self):
        return (self.binding, self.binding._pointers(), self.jobs,
                self.jobs.principal_provider, self.input_resolver, self.input_resolver.version)

    def _binding(self):
        self.binding._binding()
        if (self._pointers() != self._fixed or self.binding.jobs is not self.jobs
                or type(self.jobs) is not JobStore
                or (INPUT_VERSION, INTENT_DOMAIN, MAX_INPUT_BYTES) != _CONTRACT
                or sha256(Path(__file__).read_bytes()).hexdigest() != CODE_SHA256):
            raise VentilationExecutionHold('ventilation execution authority unavailable')

    def _guard(self, tenant):
        self._binding()
        if not self.jobs._has_scope(tenant, 'simulation_create'):
            raise PermissionError('ventilation execution access denied')
        self.binding._guard(tenant, True)
        self._binding()
        if not self.jobs._has_scope(tenant, 'simulation_create'):
            raise PermissionError('ventilation execution access denied')

    def _resolve(self, tenant, request):
        self._binding()
        source = request['input']
        resolved = self.input_resolver(tenant, source['source_sha256'], source['evidence_sha256'])
        self._binding()
        if (type(resolved) is not tuple or len(resolved) != 2
                or not isinstance(resolved[0], (str, Path)) or type(resolved[1]) is not bytes):
            raise VentilationExecutionHold('ventilation execution input unavailable')
        return resolved

    def cancel(self, tenant, job_id):
        if self.jobs is not self._fixed[2] or self.jobs.principal_provider is not self._fixed[3]:
            raise VentilationExecutionHold('ventilation cancellation authority unavailable')
        if not self.jobs._has_scope(tenant, 'cancel'): return False
        with self.jobs.connect() as conn:
            row = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s '
                'FOR NO KEY UPDATE').format(self.jobs._table('jobs')), (tenant, job_id)).fetchone()
            if row is None or row['stage'] != 'simulation': return False
            raw = self.jobs._verified_input(row); value = json.loads(raw)
            if type(value) is not dict or value.get('input_version') != INPUT_VERSION: return False
            if canonical_input_bytes(value) != raw:
                raise VentilationExecutionHold('ventilation cancellation input unavailable')
            if row['state'] in TERMINAL_STATES: return False
            if row['state'] == 'queued':
                conn.execute(sql.SQL("UPDATE {} SET state='canceled',reason=%s,updated_at=clock_timestamp() "
                    'WHERE tenant_id=%s AND job_id=%s').format(self.jobs._table('jobs')),
                    (Jsonb({'code': 'canceled_by_request'}), tenant, job_id))
                self.jobs._event(conn, tenant, job_id, 'canceled')
            elif not row['cancel_requested']:
                conn.execute(sql.SQL('UPDATE {} SET cancel_requested=true,updated_at=clock_timestamp() '
                    'WHERE tenant_id=%s AND job_id=%s').format(self.jobs._table('jobs')), (tenant, job_id))
                self.jobs._event(conn, tenant, job_id, 'cancel_requested', row['attempt_count'])
            if not self.jobs._has_scope(tenant, 'cancel'):
                raise PermissionError('ventilation cancellation access denied')
            return True

    def submit(self, tenant, request_raw):
        try:
            self._guard(tenant)
            documents._document(request_raw, max_size=MAX_INPUT_BYTES)
            request = self.binding._request(request_raw)
            directory, evidence = self._resolve(tenant, request)
            binding_raw = self.binding.prepare(tenant, request_raw, directory, evidence)
            value = {'input_version': INPUT_VERSION, 'request': request,
                     'farm_binding': json.loads(binding_raw),
                     'farm_binding_sha256': sha256(binding_raw).hexdigest(),
                     'input_resolver_version': self.input_resolver.version}
            raw = canonical_input_bytes(value)
            self._guard(tenant)

            def verify():
                self._guard(tenant)
                current_directory, current_evidence = self._resolve(tenant, request)
                self.binding.current(tenant, request_raw, current_directory,
                                     current_evidence, binding_raw, write=True)
                self._guard(tenant)
                if canonical_input_bytes(value) != raw:
                    raise VentilationExecutionHold('ventilation execution changed at admission')

            identity = documents._canonical([request['study_id'], request['revision']])
            key = INPUT_VERSION + ':' + sha256(INTENT_DOMAIN + identity).hexdigest()
            return self.jobs.submit(tenant, 'simulation', value, key, commit_guard=verify)
        except PermissionError:
            raise PermissionError('ventilation execution access denied') from None
        except JobIntentConflict:
            raise JobIntentConflict('ventilation execution revision conflict') from None
        except Exception:
            raise VentilationExecutionHold('ventilation execution admission unavailable') from None
