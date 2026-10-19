"""Pure current-source verification; no result escapes its audited lifetime."""
import asyncio
from hashlib import sha256
from pathlib import Path
from threading import get_ident

from .economic_contracts import untrusted_data
from .market_scenario import _json


MAX_LOOKUPS = 16384
MAX_VALUE_BYTES = 1048576
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
READS = frozenset({'tenant_is_authenticated', 'get_market_candidate',
    'get_economic_scenario', 'get_economic_scenario_pin', 'get_economic_input',
    'get_joint_shock', 'get_joint_shock_pin', 'get_input_rights',
    'get_settlement_applicability', 'get_settlement_evidence', 'get_prior_batch_cost',
    'get_market_hold_report', 'get_decision_context'})


def _need(value):
    if not value:
        raise ValueError('current reference verification unavailable')


def fingerprint(value):
    raw = _json(untrusted_data(value)).encode()
    _need(len(raw) <= MAX_VALUE_BYTES)
    return sha256(raw).digest()


def _execution():
    try: task = asyncio.current_task()
    except RuntimeError: task = None
    return get_ident(), task


class _Bundle:
    def __init__(self, owner, tenant, slot, reader):
        self.owner, self.tenant, self.slot, self.reader = owner, tenant, slot, reader
        self.references = owner._scoped_references.get()
        self.execution = _execution()
        self.active, self.failed = True, False
        self.token = None

    def check(self, owner, tenant):
        try:
            _need(self.active and not self.failed and owner is self.owner and tenant == self.tenant
                  and owner._reference_bundle is self.slot and self.slot.get() is self
                  and self.references is owner._scoped_references.get()
                  and self.execution == _execution())
            _need(self.token is not None)
            self.slot.reset(self.token)
            self.token = self.slot.set(self)
        except Exception:
            self.failed = True
            raise

    def guard(self, owner, tenant):
        try:
            self.check(owner, tenant)
            current = owner._reference_reader(tenant)
            _need((current is None and self.reader is None) or
                  (current is not None and self.reader is not None
                   and len(current) == len(self.reader) == 2
                   and all(a is b for a, b in zip(current, self.reader))))
            return current
        except Exception:
            self.failed = True
            raise

    def close(self):
        self.active = False
        if self.token is not None:
            self.slot.reset(self.token)
            self.token = None
        self.references = self.reader = None


def verify(owner, tenant, lookups):
    _need(type(tenant) is str and 1 <= len(tenant) <= 200
          and type(lookups) in (list, tuple) and 1 <= len(lookups) <= MAX_LOOKUPS)
    trace = tuple(lookups)
    for item in trace:
        _need(type(item) is tuple and len(item) == 3)
        name, args, digest = item
        _need(type(name) is str and name in READS and type(args) is tuple and 1 <= len(args) <= 3
              and all(type(a) is str and len(a) <= 200 for a in args)
              and type(digest) is bytes and len(digest) == 32)
    slot = owner._reference_bundle
    existing = slot.get()
    if existing is not None:
        if type(existing) is _Bundle: existing.failed = True
        raise ValueError('nested current reference verification unavailable')
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256)
    with owner.read_scope(tenant):
        bundle = _Bundle(owner, tenant, slot, owner._reference_guard(tenant))
        bundle.token = slot.set(bundle)
        try:
            for name, args, digest in trace:
                bundle.check(owner, tenant)
                _need(fingerprint(getattr(owner, name)(*args)) == digest)
            bundle.check(owner, tenant)
        finally:
            bundle.close()
            owner._reference_guard(tenant)
            _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256)
