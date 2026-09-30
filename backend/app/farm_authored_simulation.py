"""Admit an owned authored farm and signed release to a simulation intent."""

from hashlib import sha256
import json
from uuid import UUID

from .farm_authored_run import AuthoredRunPreparer, PreparedAuthoredRun
from .farm_authored_run_store import AuthoredRunStore
from .job_store import JobStore, JobIntentConflict
from .jobs import canonical_input_bytes, require_name


INPUT_VERSION = 'authored-thermal-simulation-input-v1'


class AuthoredSimulationHold(ValueError):
    pass


class AuthoredSimulationService:
    """Register only an intent; a separate worker must publish the Run."""

    def __init__(self, preparer, run_store):
        self.preparer, self.run_store = preparer, run_store
        self._binding()

    def _binding(self):
        try:
            self.preparer._binding()
            jobs = self.preparer.release_store.jobs
            if (type(self.preparer) is not AuthoredRunPreparer or
                    type(self.run_store) is not AuthoredRunStore or
                    self.run_store.preparer is not self.preparer or
                    self.run_store.jobs is not jobs or
                    type(jobs) is not JobStore or
                    jobs.runtime_identity[1] != 'authority' or
                    not jobs.runtime_identity[0].authored_run_storage or
                    jobs.audit_runtime_grants is not True):
                raise ValueError()
        except Exception:
            raise AuthoredSimulationHold('authored simulation authority unavailable') from None

    def prepare(self, tenant, review_job_id, scenario_id, revision,
                registration_sha256):
        try:
            self._binding()
            jobs = self.run_store.jobs
            if (not jobs._has_scope(tenant, 'simulation_create') or
                    type(review_job_id) is not str or
                    str(UUID(review_job_id)) != review_job_id):
                raise ValueError()
            packet = self.preparer.prepare(tenant, review_job_id, scenario_id,
                                            revision, registration_sha256)
            if type(packet) is not PreparedAuthoredRun:
                raise ValueError()
            value = {'input_version': INPUT_VERSION, 'tenant_id': tenant,
                'review_job_id': review_job_id, 'scenario_id': scenario_id,
                'scenario_revision': revision,
                'registration_sha256': registration_sha256}
            raw = canonical_input_bytes(value)
            self.run_store._input(raw, tenant, review_job_id, scenario_id,
                                  revision, registration_sha256)
            report = json.loads(packet.report_raw)
            if (canonical_input_bytes(report) != packet.report_raw or
                    report['run_id'] != packet.run_id or
                    report['tenant_id'] != tenant or
                    report['review_job_id'] != review_job_id or
                    report['scenario_id'] != scenario_id or
                    report['scenario_revision'] != revision or
                    report['registration_sha256'] != registration_sha256 or
                    report['status'] != 'prepared_unpublished' or
                    report['trace_sha256'] != list(packet.trace_sha256)):
                raise ValueError()
            self._binding()
            return value, packet
        except Exception:
            raise AuthoredSimulationHold('authored simulation inputs unavailable') from None

    def submit(self, tenant, review_job_id, scenario_id, revision,
               registration_sha256, idempotency_key):
        require_name(idempotency_key, 'idempotency_key')
        value, packet = self.prepare(tenant, review_job_id, scenario_id,
                                      revision, registration_sha256)
        original = canonical_input_bytes(value)

        def verify():
            current, current_packet = self.prepare(tenant, review_job_id,
                scenario_id, revision, registration_sha256)
            if canonical_input_bytes(current) != original or current_packet != packet:
                raise AuthoredSimulationHold('authored simulation changed at admission')

        key = INPUT_VERSION + ':' + sha256(idempotency_key.encode()).hexdigest()
        try:
            return self.run_store.jobs.submit(tenant, 'simulation', value, key,
                                               commit_guard=verify)
        except JobIntentConflict:
            raise
        except Exception:
            raise AuthoredSimulationHold('authored simulation admission unavailable') from None
