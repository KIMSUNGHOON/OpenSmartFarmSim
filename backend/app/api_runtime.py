"""Operator assembly of implemented HTTPS routes and authenticated request stores."""

from dataclasses import dataclass, field
import hmac
import os
from pathlib import Path

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
from .break_even_verification import BreakEvenVerificationService
from .break_even_verified_result import BreakEvenVerifiedResultService
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
from .crop_result_store import CropResultStore
from .crop_coupled_result_store import CoupledCropResultStore
from .crop_startup_result_store import StartupCropResultStore


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
    crop_climate_joint_execution: bool = field(default=False, kw_only=True)
    crop_climate_joint_prefix: bool = field(default=False, kw_only=True)
    crop_greenhouse_ventilation_execution: bool = field(default=False, kw_only=True)
    crop_greenhouse_ventilation_prefix: bool = field(default=False, kw_only=True)
    crop_greenhouse_solar_execution: bool = field(default=False, kw_only=True)
    crop_greenhouse_solar_prefix: bool = field(default=False, kw_only=True)

    def __post_init__(self):
        if (type(self.policy) is not RuntimeLoginPolicy or not self.policy.break_even_calculation or
                self.policy.crop_greenhouse_co2_result_storage is not False or
                type(self.policy.crop_greenhouse_solar_result_storage) is not bool or
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
                type(self.port) is not int or not 0 <= self.port <= 65535 or
                type(self.crop_climate_joint_execution) is not bool or
                (self.crop_climate_joint_execution and not self.policy.crop_climate_joint_result_storage) or
                type(self.crop_climate_joint_prefix) is not bool or
                (self.crop_climate_joint_prefix and not self.crop_climate_joint_execution) or
                type(self.crop_greenhouse_ventilation_execution) is not bool or
                (self.crop_greenhouse_ventilation_execution and
                 not self.policy.crop_greenhouse_ventilation_result_storage) or
                type(self.crop_greenhouse_ventilation_prefix) is not bool or
                (self.crop_greenhouse_ventilation_prefix and not self.crop_greenhouse_ventilation_execution) or
                type(self.crop_greenhouse_solar_execution) is not bool or
                (self.crop_greenhouse_solar_execution and not self.policy.crop_greenhouse_solar_result_storage) or
                type(self.crop_greenhouse_solar_prefix) is not bool or
                (self.crop_greenhouse_solar_prefix and not self.crop_greenhouse_solar_execution)):
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
    crop_result_store_factory: object = field(default=None, repr=False)
    crop_coupled_result_store_factory: object = field(default=None, repr=False)
    crop_startup_result_store_factory: object = field(default=None, repr=False)
    crop_cycle_result_store_factory: object = field(default=None, repr=False)
    crop_cycle_current_query_factory: object = field(default=None, repr=False)
    crop_cycle_calculation_result_store_factory: object = field(default=None, repr=False)
    crop_cycle_calculation_current_query_factory: object = field(default=None, repr=False)
    crop_harvest_current_query_factory: object = field(default=None, repr=False)
    crop_climate_joint_result_store_factory: object = field(default=None, repr=False)
    crop_climate_joint_current_query_factory: object = field(default=None, repr=False)
    crop_greenhouse_ventilation_result_store_factory: object = field(default=None, repr=False)
    crop_greenhouse_ventilation_current_query_factory: object = field(default=None, repr=False)
    crop_greenhouse_solar_result_store_factory: object = field(default=None, repr=False)
    crop_greenhouse_solar_current_query_factory: object = field(default=None, repr=False)

    def __post_init__(self):
        if (type(self.research_registry) is not ResearchRegistry or
                type(self.bearer_registry) is not BearerRegistry or
                any(not callable(value) for value in (self.context_verifier, self.release_verifier,
                    self.market_scope_resolver, self.market_source_factory)) or
                (self.thermal_publisher_factory is not None and not callable(self.thermal_publisher_factory)) or
                (self.authored_run_store_factory is not None and not callable(self.authored_run_store_factory)) or
                (self.crop_result_store_factory is not None and not callable(self.crop_result_store_factory)) or
                (self.crop_coupled_result_store_factory is not None and not callable(self.crop_coupled_result_store_factory)) or
                (self.crop_startup_result_store_factory is not None and not callable(self.crop_startup_result_store_factory)) or
                (self.crop_cycle_result_store_factory is not None and not callable(self.crop_cycle_result_store_factory)) or
                (self.crop_cycle_current_query_factory is not None and not callable(self.crop_cycle_current_query_factory)) or
                (self.crop_cycle_calculation_result_store_factory is not None and not callable(self.crop_cycle_calculation_result_store_factory)) or
                (self.crop_cycle_calculation_current_query_factory is not None and not callable(self.crop_cycle_calculation_current_query_factory)) or
                (self.crop_harvest_current_query_factory is not None and not callable(self.crop_harvest_current_query_factory)) or
                (self.crop_climate_joint_result_store_factory is not None and not callable(self.crop_climate_joint_result_store_factory)) or
                (self.crop_climate_joint_current_query_factory is not None and not callable(self.crop_climate_joint_current_query_factory)) or
                (self.crop_greenhouse_ventilation_result_store_factory is not None and not callable(self.crop_greenhouse_ventilation_result_store_factory)) or
                (self.crop_greenhouse_ventilation_current_query_factory is not None and not callable(self.crop_greenhouse_ventilation_current_query_factory)) or
                (self.crop_greenhouse_solar_result_store_factory is not None and not callable(self.crop_greenhouse_solar_result_store_factory)) or
                (self.crop_greenhouse_solar_current_query_factory is not None and not callable(self.crop_greenhouse_solar_current_query_factory)) or
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
    economic_calculations: EconomicCalculationService | None = field(repr=False)
    farm_scenarios: FarmReplayScenarioService | None = field(repr=False)
    farm_authoring: FarmAuthoringService | None = field(repr=False)
    farm_reviews: FarmAuthoredReviewService | None = field(repr=False)
    authored_runs: AuthoredRunStore | None = field(repr=False)
    authored_simulation: AuthoredSimulationService | None = field(repr=False)
    crop_results: CropResultStore | None = field(repr=False)
    coupled_crop_results: CoupledCropResultStore | None = field(repr=False)
    joint_crop_results: object = field(repr=False)
    joint_crop_query: object = field(repr=False)
    ventilation_crop_results: object = field(repr=False)
    ventilation_crop_query: object = field(repr=False)
    solar_crop_results: object = field(repr=False)
    solar_crop_query: object = field(repr=False)
    solar_execution_admission: object = field(repr=False)
    solar_execution_checkpoints: object = field(repr=False)
    solar_execution_query: object = field(repr=False)
    solar_prefix_query: object = field(repr=False)
    ventilation_execution_admission: object = field(repr=False)
    ventilation_execution_checkpoints: object = field(repr=False)
    ventilation_execution_query: object = field(repr=False)
    ventilation_prefix_query: object = field(repr=False)
    joint_execution_admission: object = field(repr=False)
    joint_execution_checkpoints: object = field(repr=False)
    joint_execution_query: object = field(repr=False)
    joint_prefix_query: object = field(repr=False)

    def __init__(self, config, dependencies):
        try:
            if type(config) is not ApiRuntimeConfig or type(dependencies) is not ApiRuntimeDependencies:
                raise ValueError()
            if config.policy.crop_result_storage != (dependencies.crop_result_store_factory is not None):
                raise ValueError()
            if config.policy.crop_coupled_result_storage != (dependencies.crop_coupled_result_store_factory is not None):
                raise ValueError()
            if config.policy.crop_startup_result_storage != (dependencies.crop_startup_result_store_factory is not None):
                raise ValueError()
            if config.policy.crop_cycle_result_storage != (dependencies.crop_cycle_result_store_factory is not None):
                raise ValueError()
            if dependencies.crop_cycle_current_query_factory is not None and dependencies.crop_cycle_result_store_factory is None:
                raise ValueError()
            if (config.policy.crop_cycle_calculation_result_storage !=
                    (dependencies.crop_cycle_calculation_result_store_factory is not None) or
                    config.policy.crop_cycle_calculation_result_storage !=
                    (dependencies.crop_cycle_calculation_current_query_factory is not None) or
                    (config.policy.crop_cycle_calculation_result_storage and not config.policy.crop_cycle_result_storage)):
                raise ValueError()
            if dependencies.crop_harvest_current_query_factory is not None and not config.policy.crop_cycle_calculation_result_storage:
                raise ValueError()
            if (config.policy.crop_climate_joint_result_storage !=
                    (dependencies.crop_climate_joint_result_store_factory is not None) or
                    config.policy.crop_climate_joint_result_storage !=
                    (dependencies.crop_climate_joint_current_query_factory is not None) or
                    (config.policy.crop_climate_joint_result_storage and not config.policy.crop_cycle_result_storage)):
                raise ValueError()
            if (config.policy.crop_greenhouse_ventilation_result_storage !=
                    (dependencies.crop_greenhouse_ventilation_result_store_factory is not None) or
                    config.policy.crop_greenhouse_ventilation_result_storage !=
                    (dependencies.crop_greenhouse_ventilation_current_query_factory is not None) or
                    (config.policy.crop_greenhouse_ventilation_result_storage and not config.policy.crop_cycle_result_storage)):
                raise ValueError()
            if (config.policy.crop_greenhouse_solar_result_storage !=
                    (dependencies.crop_greenhouse_solar_result_store_factory is not None) or
                    config.policy.crop_greenhouse_solar_result_storage !=
                    (dependencies.crop_greenhouse_solar_current_query_factory is not None) or
                    (config.policy.crop_greenhouse_solar_result_storage and not config.policy.crop_cycle_result_storage)):
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
            break_even_verification = BreakEvenVerificationService(jobs, break_even) if source_admission is not None else None
            break_even_verified_results = BreakEvenVerifiedResultService(jobs, break_even) if source_admission is not None else None
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
            crop_results = None
            if dependencies.crop_result_store_factory is not None:
                if farm_authoring is None:
                    raise ValueError()
                crop_results = dependencies.crop_result_store_factory(farm_authoring_service=farm_authoring)
                if (type(crop_results) is not CropResultStore or crop_results.jobs is not jobs
                        or crop_results.farms is not farm_authoring):
                    raise ValueError()
                crop_results._guard_binding()
            coupled_crop_results = None
            if dependencies.crop_coupled_result_store_factory is not None:
                if farm_authoring is None:
                    raise ValueError()
                coupled_crop_results = dependencies.crop_coupled_result_store_factory(farm_authoring_service=farm_authoring)
                if (type(coupled_crop_results) is not CoupledCropResultStore or coupled_crop_results.jobs is not jobs
                        or coupled_crop_results.farms is not farm_authoring):
                    raise ValueError()
                coupled_crop_results._guard_binding()
            startup_crop_results = None
            if dependencies.crop_startup_result_store_factory is not None:
                if farm_authoring is None:
                    raise ValueError()
                startup_crop_results = dependencies.crop_startup_result_store_factory(farm_authoring_service=farm_authoring)
                if (type(startup_crop_results) is not StartupCropResultStore or startup_crop_results.jobs is not jobs
                        or startup_crop_results.farms is not farm_authoring):
                    raise ValueError()
                startup_crop_results._guard_binding()
            cycle_crop_results = None
            if dependencies.crop_cycle_result_store_factory is not None:
                from .crop_cycle_result_store import CycleCropResultStore
                if farm_authoring is None:
                    raise ValueError()
                cycle_crop_results = dependencies.crop_cycle_result_store_factory(farm_authoring_service=farm_authoring)
                if (type(cycle_crop_results) is not CycleCropResultStore or cycle_crop_results.jobs is not jobs
                        or cycle_crop_results.server.binding.farms is not farm_authoring
                        or cycle_crop_results.server.binding.jobs is not jobs
                        or jobs.principal_provider is not current_principal):
                    raise ValueError()
                cycle_crop_results._binding()
            cycle_crop_query = None
            if dependencies.crop_cycle_current_query_factory is not None:
                from .crop_cycle_current_query import CurrentCycleQuery
                cycle_crop_query = dependencies.crop_cycle_current_query_factory(result_store=cycle_crop_results)
                if type(cycle_crop_query) is not CurrentCycleQuery or cycle_crop_query.store is not cycle_crop_results:
                    raise ValueError()
                cycle_crop_query._binding()
            calculation_cycle_crop_results = None
            calculation_cycle_crop_query = None
            if dependencies.crop_cycle_calculation_result_store_factory is not None:
                from .crop_cycle_calculation_result_store import CalculationCycleCropResultStore
                from .crop_cycle_calculation_current_query import CalculationCurrentCycleQuery
                if farm_authoring is None:
                    raise ValueError()
                calculation_cycle_crop_results = dependencies.crop_cycle_calculation_result_store_factory(
                    farm_authoring_service=farm_authoring)
                if (type(calculation_cycle_crop_results) is not CalculationCycleCropResultStore or
                        calculation_cycle_crop_results.jobs is not jobs or
                        calculation_cycle_crop_results.server.binding.farms is not farm_authoring or
                        calculation_cycle_crop_results.server.binding.jobs is not jobs or
                        jobs.principal_provider is not current_principal):
                    raise ValueError()
                calculation_cycle_crop_results._binding()
                calculation_cycle_crop_query = dependencies.crop_cycle_calculation_current_query_factory(
                    result_store=calculation_cycle_crop_results)
                if (type(calculation_cycle_crop_query) is not CalculationCurrentCycleQuery or
                        calculation_cycle_crop_query.store is not calculation_cycle_crop_results):
                    raise ValueError()
                calculation_cycle_crop_query._binding()
            joint_crop_results = None
            joint_crop_query = None
            if dependencies.crop_climate_joint_result_store_factory is not None:
                from .crop_climate_joint_result_store import JointCropClimateResultStore
                from .crop_climate_joint_current_query import JointCropClimateCurrentQuery
                if farm_authoring is None:
                    raise ValueError()
                joint_crop_results = dependencies.crop_climate_joint_result_store_factory(
                    farm_authoring_service=farm_authoring)
                if (type(joint_crop_results) is not JointCropClimateResultStore or
                        joint_crop_results.jobs is not jobs or
                        joint_crop_results.server.binding.farms is not farm_authoring or
                        joint_crop_results.server.binding.jobs is not jobs or
                        jobs.principal_provider is not current_principal):
                    raise ValueError()
                joint_crop_results._binding()
                keys = (joint_crop_results.integrity_key, joint_crop_results.server.integrity_key,
                        joint_crop_results.server.binding.input_authority.integrity_key)
                if len(set(keys)) != 3:
                    raise ValueError()
                joint_crop_query = dependencies.crop_climate_joint_current_query_factory(
                    result_store=joint_crop_results)
                if (type(joint_crop_query) is not JointCropClimateCurrentQuery or
                        joint_crop_query.store is not joint_crop_results):
                    raise ValueError()
                joint_crop_query._binding()
            ventilation_crop_results = None
            ventilation_crop_query = None
            if dependencies.crop_greenhouse_ventilation_result_store_factory is not None:
                from .crop_greenhouse_ventilation_result_store import VentilationResultStore
                from .crop_greenhouse_ventilation_current_query import VentilationCurrentQuery
                if farm_authoring is None:
                    raise ValueError()
                ventilation_crop_results = dependencies.crop_greenhouse_ventilation_result_store_factory(
                    farm_authoring_service=farm_authoring)
                if (type(ventilation_crop_results) is not VentilationResultStore or
                        ventilation_crop_results.jobs is not jobs or
                        ventilation_crop_results.server.binding.farms is not farm_authoring or
                        ventilation_crop_results.server.binding.jobs is not jobs or
                        jobs.principal_provider is not current_principal):
                    raise ValueError()
                ventilation_crop_results._binding()
                keys = (ventilation_crop_results.integrity_key, ventilation_crop_results.server.integrity_key,
                        ventilation_crop_results.server.binding.input_authority.integrity_key)
                if len(set(keys)) != 3:
                    raise ValueError()
                ventilation_crop_query = dependencies.crop_greenhouse_ventilation_current_query_factory(
                    result_store=ventilation_crop_results)
                if (type(ventilation_crop_query) is not VentilationCurrentQuery or
                        ventilation_crop_query.store is not ventilation_crop_results):
                    raise ValueError()
                ventilation_crop_query._binding()
            solar_crop_results = None
            solar_crop_query = None
            if dependencies.crop_greenhouse_solar_result_store_factory is not None:
                from .crop_greenhouse_solar_result_store import SolarResultStore
                from .crop_greenhouse_solar_current_query import SolarCurrentQuery
                if farm_authoring is None:
                    raise ValueError()
                solar_crop_results = dependencies.crop_greenhouse_solar_result_store_factory(
                    farm_authoring_service=farm_authoring)
                if (type(solar_crop_results) is not SolarResultStore or
                        solar_crop_results.jobs is not jobs or
                        solar_crop_results.server.binding.farms is not farm_authoring or
                        solar_crop_results.server.binding.jobs is not jobs or
                        jobs.principal_provider is not current_principal):
                    raise ValueError()
                solar_crop_results._binding()
                keys = (solar_crop_results.integrity_key, solar_crop_results.server.integrity_key,
                        solar_crop_results.server.binding.input_authority.integrity_key)
                if len(set(keys)) != 3:
                    raise ValueError()
                solar_crop_query = dependencies.crop_greenhouse_solar_current_query_factory(
                    result_store=solar_crop_results)
                if (type(solar_crop_query) is not SolarCurrentQuery or
                        solar_crop_query.store is not solar_crop_results):
                    raise ValueError()
                solar_crop_query._binding()
            solar_execution_admission = None
            solar_execution_checkpoints = None
            solar_execution_query = None
            if config.crop_greenhouse_solar_execution:
                from .crop_greenhouse_solar_execution import SolarExecutionService
                from .crop_greenhouse_solar_execution_checkpoint import SolarExecutionCheckpointStore
                from .crop_greenhouse_solar_execution_query import SolarExecutionQuery
                server = solar_crop_results.server
                solar_execution_admission = SolarExecutionService(server.binding, input_resolver=server.input_resolver)
                solar_execution_checkpoints = SolarExecutionCheckpointStore(solar_execution_admission, server)
                solar_execution_query = SolarExecutionQuery(solar_execution_checkpoints, solar_crop_results)
            solar_prefix_query = None
            if config.crop_greenhouse_solar_prefix:
                from .crop_greenhouse_solar_prefix import SolarExecutionPrefixQuery
                solar_prefix_query = SolarExecutionPrefixQuery(solar_execution_query)
            ventilation_execution_admission = None
            ventilation_execution_checkpoints = None
            ventilation_execution_query = None
            if config.crop_greenhouse_ventilation_execution:
                from .crop_greenhouse_ventilation_execution import VentilationExecutionService
                from .crop_greenhouse_ventilation_execution_checkpoint import VentilationExecutionCheckpointStore
                from .crop_greenhouse_ventilation_execution_query import VentilationExecutionQuery
                server = ventilation_crop_results.server
                ventilation_execution_admission = VentilationExecutionService(
                    server.binding, input_resolver=server.input_resolver)
                ventilation_execution_checkpoints = VentilationExecutionCheckpointStore(
                    ventilation_execution_admission, server)
                ventilation_execution_query = VentilationExecutionQuery(
                    ventilation_execution_checkpoints, ventilation_crop_results)
            ventilation_prefix_query = None
            if config.crop_greenhouse_ventilation_prefix:
                from .crop_greenhouse_ventilation_prefix import VentilationExecutionPrefixQuery
                ventilation_prefix_query = VentilationExecutionPrefixQuery(ventilation_execution_query)
            joint_execution_admission = None
            joint_execution_checkpoints = None
            joint_execution_query = None
            if config.crop_climate_joint_execution:
                from .crop_climate_joint_execution import JointCropClimateExecutionService
                from .crop_climate_joint_execution_checkpoint import JointExecutionCheckpointStore
                from .crop_climate_joint_execution_query import JointExecutionQuery
                server = joint_crop_results.server
                joint_execution_admission = JointCropClimateExecutionService(
                    server.binding, input_resolver=server.input_resolver)
                joint_execution_checkpoints = JointExecutionCheckpointStore(joint_execution_admission, server)
                joint_execution_query = JointExecutionQuery(joint_execution_checkpoints, joint_crop_results)
            joint_prefix_query = None
            if config.crop_climate_joint_prefix:
                from .crop_climate_joint_prefix import JointExecutionPrefixQuery
                joint_prefix_query = JointExecutionPrefixQuery(joint_execution_query)
            harvest_crop_query = None
            harvest_crop_results = None
            if dependencies.crop_harvest_current_query_factory is not None:
                from .crop_harvest_current_query import HarvestCurrentQuery
                from .crop_harvest_registry import HarvestRegistry
                harvest_crop_query = dependencies.crop_harvest_current_query_factory(
                    calculation_current_query=calculation_cycle_crop_query)
                if type(harvest_crop_query) is not HarvestCurrentQuery:
                    raise ValueError()
                harvest_crop_results = harvest_crop_query.store
                if (type(harvest_crop_results) is not HarvestRegistry or
                        harvest_crop_results.query is not calculation_cycle_crop_query or
                        harvest_crop_results.role != harvest_crop_results.policy.reader or
                        harvest_crop_results.policy.database != config.policy.database or
                        harvest_crop_results.policy.schema == config.policy.schema):
                    raise ValueError()
                harvest_crop_query._binding()
                with jobs.connect() as parent_connection, harvest_crop_results._connection() as reader_connection:
                    if ((parent_connection.info.host, parent_connection.info.port, parent_connection.info.dbname) !=
                            (reader_connection.info.host, reader_connection.info.port, reader_connection.info.dbname)):
                        raise ValueError()
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
            economic_calculations = (EconomicCalculationService(jobs, results, farm_scenarios,
                authored_run_store=authored_runs) if source_admission is not None else None)
            assessments = (CalculationAssessmentService(jobs, thermal, results, scenarios, farm_scenarios,
                authored_run_store=authored_runs) if source_admission is not None else None)
            from .api import create_app
            app = create_app(jobs, holds, thermal, results, principal_provider=current_principal,
                location_research_service=research,
                break_even_store=break_even, thermal_scenario_store=scenarios,
                thermal_run_submission_service=submission, market_user_source_service=source_admission,
                economic_scenario_service=economic_scenarios, economic_calculation_service=economic_calculations,
                break_even_plan_service=break_even_plans, break_even_job_result_service=break_even_job_results,
                break_even_verification_service=break_even_verification,
                break_even_verified_result_service=break_even_verified_results,
                collection_service=collections, owned_collection_review_service=collection_reviews,
                assessment_service=assessments, farm_scenario_service=farm_scenarios,
                authored_run_store=authored_runs, farm_authoring_service=farm_authoring,
                farm_authored_review_service=farm_reviews,
                authored_simulation_service=authored_simulation, crop_result_store=crop_results,
                crop_coupled_result_store=coupled_crop_results, crop_startup_result_store=startup_crop_results,
                crop_cycle_result_store=cycle_crop_results,crop_cycle_current_query=cycle_crop_query,
                crop_cycle_calculation_result_store=calculation_cycle_crop_results,
                crop_cycle_calculation_current_query=calculation_cycle_crop_query,
                crop_harvest_current_query=harvest_crop_query,
                crop_climate_joint_result_store=joint_crop_results,
                crop_climate_joint_current_query=joint_crop_query,
                crop_climate_joint_execution_service=joint_execution_admission,
                crop_climate_joint_execution_query=joint_execution_query,
                crop_climate_joint_prefix_query=joint_prefix_query,
                crop_greenhouse_ventilation_result_store=ventilation_crop_results,
                crop_greenhouse_ventilation_current_query=ventilation_crop_query,
                crop_greenhouse_solar_result_store=solar_crop_results,
                crop_greenhouse_solar_current_query=solar_crop_query,
                crop_greenhouse_solar_execution_service=solar_execution_admission,
                crop_greenhouse_solar_execution_query=solar_execution_query,
                crop_greenhouse_solar_prefix_query=solar_prefix_query,
                crop_greenhouse_ventilation_execution_service=ventilation_execution_admission,
                crop_greenhouse_ventilation_execution_query=ventilation_execution_query,
                crop_greenhouse_ventilation_prefix_query=ventilation_prefix_query)
            service = HttpsApiService(PrincipalMiddleware(app, dependencies.bearer_registry),
                config.certificate, config.private_key, host=config.host, port=config.port)
        except (Exception, SystemExit):
            raise ValueError('API runtime assembly rejected') from None
        for name, value in (('service', service), ('jobs', jobs), ('thermal', thermal),
                ('market_holds', holds), ('market_candidates', candidates),
                ('market_results', results), ('break_even', break_even), ('thermal_scenarios', scenarios),
                ('collections', collections), ('collection_reviews', collection_reviews), ('research', research),
                ('assessments', assessments), ('farm_scenarios', farm_scenarios),
                ('economic_calculations', economic_calculations),
                ('farm_authoring', farm_authoring), ('farm_reviews', farm_reviews),
                ('authored_runs', authored_runs), ('authored_simulation', authored_simulation),
                ('crop_results', crop_results), ('coupled_crop_results', coupled_crop_results),
                ('startup_crop_results', startup_crop_results), ('cycle_crop_results', cycle_crop_results),
                ('cycle_crop_query', cycle_crop_query),
                ('calculation_cycle_crop_results', calculation_cycle_crop_results),
                ('calculation_cycle_crop_query', calculation_cycle_crop_query),
                ('harvest_crop_results', harvest_crop_results), ('harvest_crop_query', harvest_crop_query),
                ('joint_crop_results', joint_crop_results), ('joint_crop_query', joint_crop_query),
                ('ventilation_crop_results', ventilation_crop_results), ('ventilation_crop_query', ventilation_crop_query),
                ('solar_crop_results', solar_crop_results), ('solar_crop_query', solar_crop_query),
                ('solar_execution_admission', solar_execution_admission),
                ('solar_execution_checkpoints', solar_execution_checkpoints),
                ('solar_execution_query', solar_execution_query),
                ('solar_prefix_query', solar_prefix_query),
                ('ventilation_execution_admission', ventilation_execution_admission),
                ('ventilation_execution_checkpoints', ventilation_execution_checkpoints),
                ('ventilation_execution_query', ventilation_execution_query),
                ('ventilation_prefix_query', ventilation_prefix_query),
                ('joint_execution_admission', joint_execution_admission),
                ('joint_execution_checkpoints', joint_execution_checkpoints),
                ('joint_execution_query', joint_execution_query),
                ('joint_prefix_query', joint_prefix_query)):
            object.__setattr__(self, name, value)
