"""Admit a currently valid authored trajectory to the owned CLI review stage."""

from hashlib import sha256
import json

from .authored_thermal_candidate import calculate_authored_candidate
from .cli_contracts import (AuthoritySnapshot, DecisionContract, DecisionPlan,
                            ProposalHold)
from .farm_authoring_storage import FarmAuthoringService, READ_SCOPES
from .farm_inputs import canonical_farm_inputs
from .jobs import canonical_input_bytes, require_name
from .thermal_units import utc


INPUT_VERSION = 'farm-authored-review-input-v1'
ARTIFACT_VERSION = 'farm-authored-review-artifact-v1'
REVIEW_SCOPES = READ_SCOPES + ('collection_review_create',)
CONTEXT_FIELDS = ('decision_context_id', 'decision_at_utc', 'claim_mode',
                  'decision_time_kind')
BINDING_FIELDS = frozenset({'scenario_id', 'scenario_revision',
    'registration_sha256', 'farm_sha256', 'numeric_input_sha256',
    'rights_declaration_sha256', 'binding_sha256', 'base_snapshot_id',
    'base_source_sha256', 'context_sha256', 'candidate_id', 'code_sha256',
    'trace_sha256'})
INPUT_FIELDS = BINDING_FIELDS | frozenset({'input_version', 'tenant_id',
    *CONTEXT_FIELDS})


class FarmAuthoredReviewHold(ValueError):
    pass


def review_artifact(value, input_sha256):
    return canonical_input_bytes({'schema_version': ARTIFACT_VERSION,
        'input_sha256': input_sha256,
        'registration_sha256': value['registration_sha256'],
        'candidate_id': value['candidate_id'],
        'trace_sha256': value['trace_sha256'],
        'code_sha256': value['code_sha256'],
        'context_sha256': value['context_sha256']})


class FarmAuthoredReviewService:
    def __init__(self, authoring):
        if type(authoring) is not FarmAuthoringService:
            raise FarmAuthoredReviewHold('authored review authority unavailable')
        self.authoring = authoring
        self.authoring._binding()

    def _guard(self, tenant, pointers):
        self.authoring._guard(tenant, pointers, REVIEW_SCOPES)

    def prepare(self, tenant, scenario_id, revision, expected_sha256):
        pointers = self.authoring._pointers()
        guard = lambda: self._guard(tenant, pointers)
        guard()
        try:
            registration = self.authoring.read_registration(
                tenant, scenario_id, revision, expected_sha256)
            candidate = calculate_authored_candidate(
                self.authoring, tenant, scenario_id, revision, expected_sha256)
            farm = registration['farm']
            numeric = registration['compiled']
            binding = registration['binding']
            context = self.authoring.replay.thermal.runs.get_decision_context(
                tenant, farm.snapshot_id, farm.decision_context_id)
            if (context is None or context['context_sha256'] != binding['context_sha256'] or
                    context['claim_mode'] != 'ex_post_replay' or
                    context['snapshot_id'] != farm.snapshot_id or
                    context['decision_context_id'] != farm.decision_context_id or
                    utc(context['decision_at_utc']) != farm.decision_at or
                    registration['scenario_sha256'] != candidate.registration_sha256 or
                    numeric['farm_sha256'] !=
                    sha256(canonical_farm_inputs(farm)).hexdigest() or
                    sha256(registration['numeric_input_bytes']).hexdigest() !=
                    candidate.numeric_input_sha256 or
                    json.loads(candidate.trace_raws[0])['binding_sha256'] !=
                    sha256(canonical_input_bytes(binding)).hexdigest()):
                raise FarmAuthoredReviewHold('authored review context differs')
            value = {'input_version': INPUT_VERSION, 'tenant_id': tenant,
                'scenario_id': scenario_id, 'scenario_revision': revision,
                'registration_sha256': expected_sha256,
                'farm_sha256': numeric['farm_sha256'],
                'numeric_input_sha256': candidate.numeric_input_sha256,
                'rights_declaration_sha256': sha256(canonical_input_bytes(
                    registration['user_rights_declaration'].model_dump(mode='json'))).hexdigest(),
                'binding_sha256': sha256(canonical_input_bytes(binding)).hexdigest(),
                'base_snapshot_id': numeric['base_snapshot_id'],
                'base_source_sha256': numeric['base_source_sha256'],
                'context_sha256': context['context_sha256'],
                'candidate_id': candidate.candidate_id,
                'code_sha256': candidate.code_sha256,
                'trace_sha256': list(candidate.trace_sha256),
                **{key: context[key] for key in CONTEXT_FIELDS}}
            if set(value) != INPUT_FIELDS:
                raise FarmAuthoredReviewHold('authored review input differs')
            return value
        except PermissionError:
            raise
        except Exception:
            raise FarmAuthoredReviewHold('authored review inputs unavailable') from None
        finally:
            guard()

    def submit(self, tenant, scenario_id, revision, expected_sha256, idempotency_key):
        require_name(idempotency_key, 'idempotency_key')
        pointers = self.authoring._pointers()
        guard = lambda: self._guard(tenant, pointers)
        guard()
        value = self.prepare(tenant, scenario_id, revision, expected_sha256)
        original = canonical_input_bytes(value)

        def verify():
            guard()
            try:
                current = self.prepare(tenant, scenario_id, revision, expected_sha256)
                if canonical_input_bytes(current) != original:
                    raise FarmAuthoredReviewHold('authored review input changed')
            finally:
                guard()

        key = INPUT_VERSION + ':' + sha256(idempotency_key.encode()).hexdigest()
        try:
            return self.authoring.replay.jobs.submit(
                tenant, 'collection_review', value, key, commit_guard=verify)
        finally:
            guard()

    def verify_input(self, job, value):
        try:
            if (job.get('stage') != 'collection_review' or
                    type(value) is not dict or set(value) != INPUT_FIELDS or
                    value.get('input_version') != INPUT_VERSION or
                    value.get('tenant_id') != job.get('tenant_id') or
                    canonical_input_bytes(value) != job.get('input_bytes') or
                    sha256(job['input_bytes']).hexdigest() != job.get('input_sha256')):
                raise ValueError()
            current = self.prepare(job['tenant_id'], value['scenario_id'],
                value['scenario_revision'], value['registration_sha256'])
            if current != value:
                raise ValueError()
            return current
        except Exception:
            raise FarmAuthoredReviewHold('authored review input unavailable') from None


class FarmAuthoredReviewContract(DecisionContract):
    VERSION = 'farm-authored-review-server-v1'

    def __init__(self, service):
        if type(service) is not FarmAuthoredReviewService:
            raise ValueError('authored review service required')
        self.service = service
        super().__init__(self._authority, input_parser=self._parse_input)

    def binding_fields(self, job):
        return BINDING_FIELDS

    def _parse_input(self, job, value):
        try:
            self.service.verify_input(job, value)
        except Exception:
            raise ProposalHold('authored_review_input_hold') from None
        return {**value, 'candidate_ids': [value['candidate_id']],
                'evidence_refs': []}

    def _authority(self, job, value):
        current = self.service.verify_input(job, json.loads(job['input_bytes']))
        return AuthoritySnapshot(tenant_id=job['tenant_id'], stage='collection_review',
            input_sha256=job['input_sha256'],
            candidate_ids=frozenset({current['candidate_id']}), evidence={},
            allow_proceed=True, missing_evidence=(), approved_claims={},
            g3a_candidate_ids=frozenset(), g3b_ok=False,
            stage_bindings={key: current[key] for key in BINDING_FIELDS},
            decision_context_id=current['decision_context_id'],
            decision_at_utc=current['decision_at_utc'],
            claim_mode=current['claim_mode'],
            decision_time_kind=current['decision_time_kind'])

    def plan(self, job, final_output):
        plan = super().plan(job, final_output)
        if plan.disposition == 'hold':
            return plan
        value = self.service.verify_input(job, json.loads(job['input_bytes']))
        return DecisionPlan('proceed', review_artifact(value, job['input_sha256']),
                            plan.code)
