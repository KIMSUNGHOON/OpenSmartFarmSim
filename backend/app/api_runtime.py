"""Operator assembly of implemented HTTPS routes and authenticated request stores."""

from dataclasses import dataclass, field
import hmac
import os
from pathlib import Path

from .api import create_app
from .break_even_store import BreakEvenStore
from .content_access import ContentAccess
from .http_identity import BearerRegistry, PrincipalMiddleware, current_principal
from .https_service import HttpsApiService
from .job_store import JobStore
from .market_candidate_store import MarketCandidateStore
from .market_hold_store import MarketHoldStore
from .market_result_store import MarketResultStore
from .orchestration import LocationResearchService
from .research_registry import ResearchRegistry
from .runtime_roles import RuntimeLoginPolicy
from .thermal_run_store import ThermalRunStore
from .thermal_scenario_store import ThermalScenarioStore
from .farm_replay_scenario import FarmReplayScenarioService
from .thermal_run_submission import ThermalRunSubmissionService
from .api_market_source import MarketUserSourceService, _MarketSources, _SOURCE_METHODS
from .market_source_store import MarketSourceStore
from .api_economic_scenario import EconomicScenarioService
from .api_economic_calculation import EconomicCalculationService
from .api_job_break_even_result import BreakEvenJobResultService
from .break_even_plan_submission import BreakEvenPlanSubmissionService
from .owned_fixture_registry import OwnedFixtureRegistry
from .owned_fixture_collection import CollectionService
from .owned_collection_review import OwnedCollectionReviewService
from .owned_research import OwnedResearchService
from .calculation_assessment import CalculationAssessmentService
from .farm_authoring_storage import FarmAuthoringService
from .farm_authored_review import FarmAuthoredReviewService
from .farm_authored_run_store import AuthoredRunStore
from .farm_authored_simulation import AuthoredSimulationService


@dataclass(frozen=True)
class ApiRuntimeConfig:
    policy: RuntimeLoginPolicy = field(repr=False)
    dsn: str = field(repr=False)
    artifact_root: Path = field(repr=False)
    certificate: Path = field(repr=False)
    private_key: Path = field(repr=False)
    thermal_gate_key: bytes = field(repr=False)
    market_hold_key: bytes = field(repr=False)
    authored_run_gate_key: bytes | None = field(default=None, repr=False)
    content_access: ContentAccess | None = field(default=None, repr=False)
    host: str = '127.0.0.1'
    port: int = 8443

    def __post_init__(self):
        if (type(self.policy) is not RuntimeLoginPolicy or not self.policy.break_even_calculation or
                type(self.dsn) is not str or not self.dsn or
                any(not isinstance(path, Path) or not path.is_absolute() or '..' in path.parts
                    for path in (self.artifact_root, self.certificate, self.private_key)) or
                any(type(key) is not bytes or not 32 <= len(key) <= 4096
                    for key in (self.thermal_gate_key, self.market_hold_key)) or
                (self.authored_run_gate_key is not None and
                    (type(self.authored_run_gate_key) is not bytes or
                     not 32 <= len(self.authored_run_gate_key) <= 4096)) or
                (self.content_access is not None and type(self.content_access) is not ContentAccess) or
                type(self.host) is not str or self.host not in ('127.0.0.1', '::1') or
                type(self.port) is not int or not 0 <= self.port <= 65535):
            raise ValueError('API runtime configuration rejected')


@dataclass(frozen=True)
class ApiRuntimeDependencies:
    research_registry: ResearchRegistry = field(repr=False)
    bearer_registry: BearerRegistry = field(repr=False)
    context_verifier: object = field(repr=False)
    release_verifier: object = field(repr=False)
    market_scope_resolver: object = field(repr=False)
    market_source_factory: object = field(repr=False)
    thermal_publisher_factory: object = field(default=None, repr=False)
    authored_run_store_factory: object = field(default=None, repr=False)
    owned_fixture_registry: OwnedFixtureRegistry | None = field(default=None, repr=False)
    owned_research_contexts: dict | None = field(default=None, repr=False)

    def __post_init__(self):
        if (type(self.research_registry) is not ResearchRegistry or
                type(self.bearer_registry) is not BearerRegistry or
                any(not callable(value) for value in (self.context_verifier, self.release_verifier,
                    self.market_scope_resolver, self.market_source_factory)) or
                (self.thermal_publisher_factory is not None and not callable(self.thermal_publisher_factory)) or
                (self.authored_run_store_factory is not None and not callable(self.authored_run_store_factory)) or
                (self.owned_fixture_registry is not None and type(self.owned_fixture_registry) is not OwnedFixtureRegistry) or
                (self.owned_research_contexts is not None and
                    (type(self.owned_research_contexts) is not dict or self.owned_fixture_registry is None))):
            raise ValueError('API runtime dependencies rejected')


@dataclass(frozen=True, init=False)
class ApiRuntime:
    service: HttpsApiService = field(repr=False)
    jobs: JobStore = field(repr=False)
    thermal: ThermalRunStore = field(repr=False)
    market_holds: MarketHoldStore = field(repr=False)
    market_candidates: MarketCandidateStore = field(repr=False)
    market_results: MarketResultStore = field(repr=False)
    break_even: BreakEvenStore = field(repr=False)
    thermal_scenarios: ThermalScenarioStore | None = field(repr=False)
    collections: CollectionService | None = field(repr=False)
    collection_reviews: OwnedCollectionReviewService | None = field(repr=False)
    research: LocationResearchService | OwnedResearchService = field(repr=False)
    assessments: CalculationAssessmentService | None = field(repr=False)
    farm_scenarios: FarmReplayScenarioService | None = field(repr=False)
    farm_authoring: FarmAuthoringService | None = field(repr=False)
    farm_reviews: FarmAuthoredReviewService | None = field(repr=False)
    authored_runs: AuthoredRunStore | None = field(repr=False)
    authored_simulation: AuthoredSimulationService | None = field(repr=False)

    def __init__(self, config, dependencies):
        try:
            if type(config) is not ApiRuntimeConfig or type(dependencies) is not ApiRuntimeDependencies:
                raise ValueError()
            authored_option = (config.authored_run_gate_key is not None or
                dependencies.authored_run_store_factory is not None)
            if authored_option and (not config.policy.authored_run_storage or
                    config.authored_run_gate_key is None or
                    dependencies.authored_run_store_factory is None):
                raise ValueError()
            binding = config.policy, 'authority'
            jobs = JobStore(config.dsn, config.policy.schema, config.artifact_root,
                runtime_identity=binding, principal_provider=current_principal,
                content_access=config.content_access, audit_runtime_grants=True)
            if config.content_access is not None:
                config.content_access.require_writer()
            descriptor = jobs._content_directory()
            os.close(descriptor)
            with jobs.connect():
                pass
            thermal = ThermalRunStore(config.dsn, config.policy.schema,
                gate_key=config.thermal_gate_key, release_verifier=dependencies.release_verifier,
                context_verifier=dependencies.context_verifier,
                principal_provider=current_principal, runtime_identity=binding)
            holds = MarketHoldStore(config.dsn, config.policy.schema, context_store=thermal,
                scope_resolver=dependencies.market_scope_resolver, signing_key=config.market_hold_key,
                principal_provider=current_principal, runtime_identity=binding)
            source = dependencies.market_source_factory(principal_provider=current_principal)
            source_admission = MarketUserSourceService(jobs, source) if type(source) is MarketSourceStore else None
            candidates = MarketCandidateStore(config.dsn, config.policy.schema, _MarketSources(source, holds),
                principal_provider=current_principal, runtime_identity=binding)
            economic_scenarios = EconomicScenarioService(jobs, candidates) if source_admission is not None else None
            results = MarketResultStore(config.dsn, config.policy.schema, candidates,
                principal_provider=current_principal, runtime_identity=binding)
            break_even = BreakEvenStore(config.dsn, config.policy.schema, candidates,
                principal_provider=current_principal, runtime_identity=binding)
            break_even_plans = BreakEvenPlanSubmissionService(jobs, break_even) if source_admission is not None else None
            break_even_job_results = BreakEvenJobResultService(jobs, break_even) if source_admission is not None else None
            scenarios = ThermalScenarioStore(thermal, holds) if config.policy.thermal_scenario_storage else None
            collections = (CollectionService(jobs, dependencies.owned_fixture_registry)
                if dependencies.owned_fixture_registry is not None else None)
            collection_reviews = OwnedCollectionReviewService(collections, thermal) if collections is not None else None
            research = (OwnedResearchService(jobs, thermal, dependencies.research_registry,
                dependencies.owned_fixture_registry, dependencies.owned_research_contexts)
                if dependencies.owned_research_contexts is not None else
                LocationResearchService(jobs, dependencies.research_registry.scope_for_location))
            farm_scenarios = (FarmReplayScenarioService(jobs, scenarios, candidates, dependencies.research_registry,
                research if type(research) is OwnedResearchService else None)
                if scenarios is not None and source_admission is not None else None)
            farm_authoring = (FarmAuthoringService(farm_scenarios)
                if farm_scenarios is not None and farm_scenarios.owned_research is not None else None)
            farm_reviews = FarmAuthoredReviewService(farm_authoring) if farm_authoring is not None else None
            assessments = (CalculationAssessmentService(jobs, thermal, results, scenarios, farm_scenarios)
                if source_admission is not None else None)
            economic_calculations = (EconomicCalculationService(jobs, results, farm_scenarios)
                if source_admission is not None else None)
            submission = None
            if dependencies.thermal_publisher_factory is not None:
                if scenarios is None:
                    raise ValueError()
                publisher = dependencies.thermal_publisher_factory(run_store=thermal, job_store=jobs)
                submission = ThermalRunSubmissionService(publisher, scenarios, farm_scenarios)
            authored_runs = None
            if authored_option:
                if (farm_scenarios is None or type(research) is not OwnedResearchService or
                        farm_scenarios.owned_research is not research):
                    raise ValueError()
                authored_runs = dependencies.authored_run_store_factory(
                    job_store=jobs, farm_scenario_service=farm_scenarios,
                    gate_key=config.authored_run_gate_key)
                if (type(authored_runs) is not AuthoredRunStore or
                        authored_runs.jobs is not jobs or
                        type(authored_runs.preparer.authoring) is not FarmAuthoringService or
                        authored_runs.preparer.authoring.replay is not farm_scenarios or
                        authored_runs.preparer.release_store.jobs is not jobs or
                        not hmac.compare_digest(authored_runs.gate_key,
                            config.authored_run_gate_key)):
                    raise ValueError()
            authored_simulation = (AuthoredSimulationService(authored_runs.preparer,authored_runs)
                if authored_runs is not None else None)
            app = create_app(jobs, holds, thermal, results, principal_provider=current_principal,
                location_research_service=research,
                break_even_store=break_even, thermal_scenario_store=scenarios,
                thermal_run_submission_service=submission, market_user_source_service=source_admission,
                economic_scenario_service=economic_scenarios, economic_calculation_service=economic_calculations,
                break_even_plan_service=break_even_plans, break_even_job_result_service=break_even_job_results,
                collection_service=collections, owned_collection_review_service=collection_reviews,
                assessment_service=assessments, farm_scenario_service=farm_scenarios,
                authored_run_store=authored_runs, farm_authoring_service=farm_authoring,
                farm_authored_review_service=farm_reviews,
                authored_simulation_service=authored_simulation)
            service = HttpsApiService(PrincipalMiddleware(app, dependencies.bearer_registry),
                config.certificate, config.private_key, host=config.host, port=config.port)
        except (Exception, SystemExit):
            raise ValueError('API runtime assembly rejected') from None
        for name, value in (('service', service), ('jobs', jobs), ('thermal', thermal),
                ('market_holds', holds), ('market_candidates', candidates),
                ('market_results', results), ('break_even', break_even), ('thermal_scenarios', scenarios),
                ('collections', collections), ('collection_reviews', collection_reviews), ('research', research),
                ('assessments', assessments), ('farm_scenarios', farm_scenarios),
                ('farm_authoring', farm_authoring), ('farm_reviews', farm_reviews),
                ('authored_runs', authored_runs), ('authored_simulation', authored_simulation)):
            object.__setattr__(self, name, value)
