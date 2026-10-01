"""Assemble the implemented owned routes over one protected service binding."""

from .calculation_assessment import (CalculationAssessmentService, CalculationAssessmentContract,
    AuthoredCalculationAssessmentContract, INPUT_VERSION, FARM_INPUT_VERSION, AUTHORED_INPUT_VERSION)
from .cli_contract_router import CliContractRouter
from .cli_contracts import DecisionContract, ProposalHold
from .farm_authored_review import (FarmAuthoredReviewService, FarmAuthoredReviewContract,
    INPUT_VERSION as FARM_REVIEW_INPUT_VERSION)
from .owned_collection_review import OwnedCollectionReviewService, OwnedCollectionReviewContract
from .owned_collection_review import INPUT_VERSION as REVIEW_INPUT_VERSION
from .owned_research import OwnedResearchService


class OwnedCliContractRouter(CliContractRouter):
    VERSION = 'owned-cli-contract-router-v3'

    def __init__(self, research, reviews, assessments, review_authority,
                 authored_review=None):
        try:
            if (type(research) is not OwnedResearchService or
                    type(reviews) is not OwnedCollectionReviewService or
                    type(assessments) is not CalculationAssessmentService or
                    not callable(review_authority) or
                    authored_review is not None and
                    type(authored_review) is not FarmAuthoredReviewService):
                raise ValueError()
            self.research, self.reviews, self.assessments = research, reviews, assessments
            self.authored_review = authored_review
            self._cohesion()
            assessment_contract = CalculationAssessmentContract(assessments)
            routes = {
                ('research', 'research_input_v1'):DecisionContract(research.authority_snapshot),
                ('collection_review', REVIEW_INPUT_VERSION):OwnedCollectionReviewContract(reviews, review_authority),
                ('assessment', INPUT_VERSION):assessment_contract,
                ('assessment', FARM_INPUT_VERSION):assessment_contract,
                ('assessment', AUTHORED_INPUT_VERSION):AuthoredCalculationAssessmentContract(assessments)}
            if authored_review is not None:
                routes[('collection_review', FARM_REVIEW_INPUT_VERSION)] = \
                    FarmAuthoredReviewContract(authored_review)
            super().__init__(routes)
            self._original = self._pointers()
        except Exception:
            raise ValueError('owned CLI contract assembly rejected') from None

    def _cohesion(self):
        self.research._binding()
        self.reviews._binding()
        self.assessments._binding()
        if (self.research.store is not self.reviews.collection.jobs or
                self.research.store is not self.assessments.jobs or
                self.research.runs is not self.reviews.runs or
                self.research.runs is not self.assessments.runs or
                self.research.registry is not self.reviews.collection.registry):
            raise ValueError('owned CLI service bindings differ')
        if self.authored_review is not None:
            self.authored_review.authoring._binding()
            replay = self.authored_review.authoring.replay
            if (replay.jobs is not self.research.store or
                    replay.owned_research is not self.research or
                    replay.registry is not self.research.catalog or
                    replay.thermal.runs is not self.reviews.runs or
                    replay.candidates is not self.assessments.results._candidates or
                    self.assessments.farm_scenario_service is not replay):
                raise ValueError('authored review service bindings differ')

    def _pointers(self):
        return (self.research, self.reviews, self.assessments, self.authored_review,
            self.research._pointers(), self.reviews._pointers(), self.assessments._pointers(),
            self.authored_review.authoring._pointers() if self.authored_review else None,
            tuple((key, contract, contract.authority_resolver, contract.input_parser)
                  for key, contract in self._routes.items()))

    def _guard(self):
        try:
            self._cohesion()
            if self._pointers() != self._original:
                raise ValueError()
        except Exception:
            raise ProposalHold('owned_cli_binding_hold') from None

    def _checked(self, operation, *args):
        self._guard()
        try:
            return operation(*args)
        finally:
            self._guard()

    def binding_fields(self, job):
        return self._checked(super().binding_fields, job)

    def input_context(self, job):
        return self._checked(super().input_context, job)

    def plan(self, job, final_output):
        return self._checked(super().plan, job, final_output)

    def __call__(self, job, final_output, proposed_artifact):
        try:
            return self._checked(super().__call__, job, final_output, proposed_artifact)
        except ProposalHold as exc:
            return {'passed':False, 'version':self.VERSION, 'code':exc.code, 'disposition':None}
