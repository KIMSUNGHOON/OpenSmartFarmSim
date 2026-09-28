"""Operator assembly of implemented HTTPS routes and authenticated request stores."""

from dataclasses import dataclass, field
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
from .thermal_run_submission import ThermalRunSubmissionService
from .api_market_source import MarketUserSourceService
from .market_source_store import MarketSourceStore


_SOURCE_METHODS = frozenset({'tenant_is_authenticated', 'get_economic_scenario',
    'get_economic_scenario_pin', 'get_economic_input', 'get_joint_shock', 'get_joint_shock_pin',
    'get_input_rights', 'get_settlement_applicability', 'get_settlement_evidence', 'get_prior_batch_cost'})


@dataclass(frozen=True)
class ApiRuntimeConfig:
    policy: RuntimeLoginPolicy = field(repr=False)
    dsn: str = field(repr=False)
    artifact_root: Path = field(repr=False)
    certificate: Path = field(repr=False)
    private_key: Path = field(repr=False)
    thermal_gate_key: bytes = field(repr=False)
    market_hold_key: bytes = field(repr=False)
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

    def __post_init__(self):
        if (type(self.research_registry) is not ResearchRegistry or
                type(self.bearer_registry) is not BearerRegistry or
                any(not callable(value) for value in (self.context_verifier, self.release_verifier,
                    self.market_scope_resolver, self.market_source_factory)) or
                (self.thermal_publisher_factory is not None and not callable(self.thermal_publisher_factory))):
            raise ValueError('API runtime dependencies rejected')


class _MarketSources:
    def __init__(self, source, holds):
        if any(not callable(getattr(source, name, None)) for name in _SOURCE_METHODS):
            raise ValueError('market source interface rejected')
        self._source, self._holds = source, holds

    def tenant_is_authenticated(self, tenant):
        principal = current_principal()
        return bool(principal is not None and principal['tenant_id'] == tenant and
                    self._source.tenant_is_authenticated(tenant) is True)

    def get_market_hold_report(self, report_id):
        return self._holds.get_market_hold_report(report_id)

    def get_decision_context(self, tenant, snapshot_id, context_id):
        return self._holds.get_decision_context(tenant, snapshot_id, context_id)

    def __getattr__(self, name):
        if name not in _SOURCE_METHODS:
            raise AttributeError(name)
        def scoped_read(*args):
            principal = current_principal()
            if principal is None or not self.tenant_is_authenticated(principal['tenant_id']):
                return None
            return getattr(self._source, name)(*args)
        return scoped_read


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

    def __init__(self, config, dependencies):
        try:
            if type(config) is not ApiRuntimeConfig or type(dependencies) is not ApiRuntimeDependencies:
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
            results = MarketResultStore(config.dsn, config.policy.schema, candidates,
                principal_provider=current_principal, runtime_identity=binding)
            break_even = BreakEvenStore(config.dsn, config.policy.schema, candidates,
                principal_provider=current_principal, runtime_identity=binding)
            scenarios = ThermalScenarioStore(thermal, holds) if config.policy.thermal_scenario_storage else None
            submission = None
            if dependencies.thermal_publisher_factory is not None:
                if scenarios is None:
                    raise ValueError()
                publisher = dependencies.thermal_publisher_factory(run_store=thermal, job_store=jobs)
                submission = ThermalRunSubmissionService(publisher, scenarios)
            app = create_app(jobs, holds, thermal, results, principal_provider=current_principal,
                location_research_service=LocationResearchService(jobs, dependencies.research_registry.scope_for_location),
                break_even_store=break_even, thermal_scenario_store=scenarios,
                thermal_run_submission_service=submission, market_user_source_service=source_admission)
            service = HttpsApiService(PrincipalMiddleware(app, dependencies.bearer_registry),
                config.certificate, config.private_key, host=config.host, port=config.port)
        except (Exception, SystemExit):
            raise ValueError('API runtime assembly rejected') from None
        for name, value in (('service', service), ('jobs', jobs), ('thermal', thermal),
                ('market_holds', holds), ('market_candidates', candidates),
                ('market_results', results), ('break_even', break_even), ('thermal_scenarios', scenarios)):
            object.__setattr__(self, name, value)
