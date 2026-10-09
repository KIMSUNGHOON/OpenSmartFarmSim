"""Serialize original joint results while their custody and current rights are held."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from . import api_crop_climate_joint_replay as public
from .runtime_roles import RolePolicyHold

storage = public.storage
server = storage.server
artifact = storage.artifact
VERSION = 'joint-crop-climate-current-query-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES = {'result_store': storage, 'projection': public}
DEPENDENCY_SHA256 = {k: sha256(Path(m.__file__).read_bytes()).hexdigest() for k, m in _MODULES.items()}
_FIXED = (VERSION, CODE_SHA256, storage._canonical(DEPENDENCY_SHA256))


class JointCurrentQueryHold(ValueError):
    """No original result can currently be returned to this caller."""


def _need(condition):
    if not condition: raise JointCurrentQueryHold('current joint research unavailable')


def _pins():
    _need((VERSION, CODE_SHA256, storage._canonical(DEPENDENCY_SHA256)) == _FIXED
        and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
        and {k: sha256(Path(m.__file__).read_bytes()).hexdigest() for k, m in _MODULES.items()} == DEPENDENCY_SHA256)
    storage._pins()


class JointCropClimateCurrentQuery:
    def __init__(self, store):
        try:
            _need(type(store) is storage.JointCropClimateResultStore)
            self.store = store
            self._fixed = (store, store._pointers())
            self._binding()
        except Exception: raise JointCurrentQueryHold('current joint authority unavailable') from None

    def _binding(self):
        _pins()
        _need((self.store, self.store._pointers()) == self._fixed)
        self.store._binding()

    def _record(self, tenant, record, packet, farm):
        self._binding(); self.store._guard(tenant)
        row = self.store._find(tenant, result_id=record['result_id'])
        _need(row is not None)
        checked = self.store._row(row, tenant, farm)
        _need(self.store._record(row) == record and storage._canonical(checked) == storage._canonical(packet))

    def read(self, tenant, result_id, farm_ref, *, view='summary', offset=0, limit=None):
        try:
            self._binding(); self.store._guard(tenant)
            _need(type(view) is str and view in ('summary', 'samples', 'events')
                and type(offset) is int and 0 <= offset <= (128 if view == 'events' else 512))
            if view == 'summary': _need(offset == 0 and limit is None)
            else:
                limit = (64 if view == 'samples' else 8) if limit is None else limit
                _need(type(limit) is int and 1 <= limit <= (64 if view == 'samples' else 8))
            _need(type(farm_ref) is dict and set(farm_ref) == {'scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id'}
                and all(storage._name(farm_ref[k]) for k in ('scenario_id', 'scenario_revision', 'crop_id'))
                and server._digest(farm_ref['registration_sha256']))
            farm = deepcopy(farm_ref)
            with self.store._read(tenant, result_id, farm) as (row, packet, session):
                if row is None:
                    self._binding(); self.store._guard(tenant)
                    return None
                record = deepcopy(self.store._record(row))
                with artifact.open_artifact(session.path, packet['artifact']['sha256']) as reader:
                    terminal = deepcopy({**reader.summary, 'manifest': reader._context['manifest'],
                        'time_binding': reader._header['binding']})
                    page = None if view == 'summary' else reader.page(view, start=offset, limit=limit)
                    self._record(tenant, record, packet, farm)
                    projected = public.project_joint_result(record, terminal, view=view, page=page, limit=limit)
                    raw = public._public_bytes(projected)
                    _need(type(raw) is bytes and 1 <= len(raw) <= public.MAX_RESPONSE_BYTES
                        and farm_ref == farm)
                    reader._check()
                    self._record(tenant, record, packet, farm)
            self._binding(); self.store._guard(tenant)
            return raw
        except (PermissionError, RolePolicyHold, server.JointCustodyPending): raise
        except Exception: raise JointCurrentQueryHold('current joint research unavailable') from None
