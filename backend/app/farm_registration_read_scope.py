"""Request-local reuse of reconstruction after fresh, ordered authority reads."""
import asyncio
from copy import deepcopy
from decimal import getcontext
from hashlib import sha256
import json
from pathlib import Path
import sys
from threading import get_ident

from . import economic_contracts, economics, farm_input_compiler, farm_inputs, market, market_scenario


MAX_LOOKUPS = 16384
MAX_VALUE_BYTES = 1048576
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_READS = frozenset({'tenant_is_authenticated', 'get_market_candidate',
    'get_economic_scenario', 'get_economic_scenario_pin', 'get_economic_input',
    'get_joint_shock', 'get_joint_shock_pin', 'get_input_rights',
    'get_settlement_applicability', 'get_settlement_evidence', 'get_prior_batch_cost',
    'get_market_hold_report', 'get_decision_context'})


class RegistrationScopeHold(ValueError):
    pass


def _need(value):
    if not value:
        raise RegistrationScopeHold('current farm registration scope unavailable')


def _execution():
    try: task = asyncio.current_task()
    except RuntimeError: task = None
    return get_ident(), task


def _decimal():
    ctx = getcontext()
    return (ctx.prec, ctx.rounding, ctx.Emin, ctx.Emax, ctx.capitals, ctx.clamp,
            tuple(sorted((signal.__name__, enabled) for signal, enabled in ctx.traps.items())))


def _fingerprint(value):
    raw = market_scenario._json(economic_contracts.untrusted_data(value)).encode()
    _need(len(raw) <= MAX_VALUE_BYTES)
    return sha256(raw).digest()


class _Recorder:
    def __init__(self, witness): self.witness = witness

    def __getattr__(self, name):
        if name == 'read_scope': return self.witness.repository.read_scope
        if name not in _READS: raise AttributeError(name)
        def lookup(*args):
            value = getattr(self.witness.repository, name)(*args)
            self.witness.record(name, args, value)
            return value
        return lookup


class RegistrationRead:
    def __init__(self, owner, args, slot, scopes):
        _need(len(args) == 4 and all(type(v) is str and 1 <= len(v) <= 200 for v in args)
              and len(args[3]) == 64 and all(c in '0123456789abcdef' for c in args[3]))
        self.owner, self.args, self.slot, self.scopes = owner, args, slot, scopes
        self.repository = owner.replay.candidates
        self.pointers, self.execution, self.decimal = owner._pointers(), _execution(), _decimal()
        self.active, self.loading, self.failed = True, False, False
        self.value, self.root, self.snapshot = None, None, None
        self.lookups = []
        self.recorder = _Recorder(self)
        self.code = self._code()

    def _code(self):
        module = sys.modules[type(self.owner).__module__]
        modules = (module, economic_contracts, economics, farm_input_compiler,
                   farm_inputs, market, market_scenario)
        methods = (self.owner._read_registration, self.owner._read, self.owner._prepare,
                   module.compile_farm_inputs, module.validate_economic_scope,
                   economics.EconomicLedger.calculate, economics.EconomicLedger._calculate_verified,
                   market_scenario.MarketScenarioService._prepare,
                   market_scenario.MarketScenarioService._check_caps,
                   market_scenario.MarketScenarioService._check_bindings)
        policy = (market_scenario._json(market_scenario._FIELDS),
                  tuple(sorted((k, tuple(sorted(v))) for k, v in market_scenario._DRIVER_GROUPS.items())),
                  module.READ_SCOPES)
        return (tuple(sha256(Path(m.__file__).read_bytes()).digest() for m in modules),
                methods, policy, sha256(Path(__file__).read_bytes()).hexdigest())

    def _guard(self):
        _need(self.active and not self.failed and self.slot.get() is self
              and self.owner._registration_read is self.slot
              and self.execution == _execution() and self.decimal == _decimal()
              and self._code() == self.code and self.code[-1] == CODE_SHA256)
        self.owner._guard(self.args[0], self.pointers, self.scopes)

    def record(self, name, args, value):
        _need(self.loading and name in _READS and len(self.lookups) < MAX_LOOKUPS
              and all(type(v) is str and len(v) <= 200 for v in args))
        self.lookups.append((name, args, _fingerprint(value)))

    def capture(self, root, snapshot):
        _need(self.loading and self.root is None and self.snapshot is None)
        self.root = (str(root['job_id']), root['input_sha256'], root['created_at'])
        self.snapshot = deepcopy(snapshot)

    def _current(self):
        tenant, scenario, revision, expected_sha = self.args
        row = self.owner._find(tenant, scenario, revision)
        _need(row is not None and row['input_sha256'] == expected_sha)
        farm = self.value['farm']; replay = self.owner.replay
        with replay.jobs.connect() as conn:
            root = replay.jobs._locked_job(conn, tenant, farm.research_job_id)
            _need(root is not None and root['stage'] == 'research'
                  and root['state'] not in ('canceled', 'failed'))
            research = json.loads(replay.jobs._verified_input(root))
        _need((str(root['job_id']), root['input_sha256'], root['created_at']) == self.root
              and replay.owned_research.authority_snapshot(root, research) is not None)
        _need(replay.thermal.runs.get_snapshot(tenant, farm.snapshot_id) == self.snapshot)
        with self.repository.read_scope(tenant):
            for name, args, expected in self.lookups:
                _need(_fingerprint(getattr(self.repository, name)(*args)) == expected)

    def read(self, *args):
        try:
            self._guard(); _need(args == self.args and not self.loading)
            if self.value is None:
                self.loading = True
                try: value = self.owner._read_registration(*args)
                finally: self.loading = False
                _need(self.root is not None and self.snapshot is not None and self.lookups)
                self.value = deepcopy(value)
            else:
                self._current()
            self._guard()
            return deepcopy(self.value)
        except Exception:
            self.failed = True
            raise

    def close(self):
        self.active = False
        self.value = self.root = self.snapshot = None
        self.lookups.clear()
