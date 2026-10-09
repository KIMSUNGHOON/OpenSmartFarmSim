"""Current-rights metadata discovery; selection uses the existing verified reader."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from psycopg import sql

from . import crop_cycle_calculation_current_query as calculation
from . import crop_harvest_current_query as harvest
from .thermal_run_store import _canonical

VERSION = 'crop-research-result-catalog-v1'
MAX_LIMIT = 20
MAX_PAGE_BYTES = 64 * 1024
KINDS = ('calculation_cycle_v1', 'harvest_v1')
# Reviewed implementation determines which registration arguments may share a check.
REGISTRATION_CODE_SHA256 = '4f245271487b1e55422386b42221aa8d24906d28f52403626c474c62f14568a9'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_DECLARATIONS = (VERSION, MAX_LIMIT, MAX_PAGE_BYTES, KINDS, REGISTRATION_CODE_SHA256, CODE_SHA256)


class CropResultCatalogHold(ValueError):
    """No currently authorized metadata page; existing results remain unchanged."""


def _need(value):
    if not value:
        raise CropResultCatalogHold('stored crop result catalog unavailable')


def _request(kind, farm, limit, before):
    _need(type(kind) is str and kind in KINDS and type(limit) is int and 1 <= limit <= MAX_LIMIT)
    _need(type(farm) is dict and set(farm) == {
        'scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id'})
    _need(all(calculation.storage._name(farm[k]) for k in ('scenario_id', 'scenario_revision', 'crop_id'))
          and calculation.inputs._digest(farm['registration_sha256']))
    if before is not None:
        prefix = calculation.storage.VERSION if kind == KINDS[0] else harvest.registry.VERSION
        _need(type(before) is dict and set(before) == {'recorded_at', 'result_id'})
        _need(type(before['recorded_at']) is datetime and before['recorded_at'].tzinfo is not None
              and before['recorded_at'].utcoffset() is not None)
        _need(type(before['result_id']) is str and before['result_id'].startswith(prefix+':')
              and calculation.inputs._digest(before['result_id'][len(prefix)+1:]))


def _time(value):
    _need(type(value) is datetime and value.tzinfo is not None and value.utcoffset() is not None)
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


class CropResultCatalog:
    def __init__(self, calculation_query, harvest_query=None):
        _need(type(calculation_query) is calculation.CalculationCurrentCycleQuery)
        _need(harvest_query is None or type(harvest_query) is harvest.HarvestCurrentQuery
              and harvest_query.store.query is calculation_query)
        self.calculation, self.harvest = calculation_query, harvest_query
        self._fixed = self._pointers()
        self._binding()

    def _pointers(self):
        return (self.calculation, self.calculation._pointers(), self.harvest,
                None if self.harvest is None else self.harvest._fixed)

    def _binding(self):
        _need((VERSION, MAX_LIMIT, MAX_PAGE_BYTES, KINDS, REGISTRATION_CODE_SHA256, CODE_SHA256) == _DECLARATIONS
              and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
              and sha256(Path(calculation.server.farms.original.__file__).read_bytes()).hexdigest()
                  == REGISTRATION_CODE_SHA256
              and self._pointers() == self._fixed)
        self.calculation._binding()
        if self.harvest is not None:
            self.harvest._binding()

    def _guard(self, tenant, farm):
        self._binding()
        binding = self.calculation.store.server.binding
        binding._guard(tenant, False)
        registration = binding.farms.read_registration(tenant, farm['scenario_id'],
            farm['scenario_revision'], farm['registration_sha256'])
        _need(any(c.crop_id == farm['crop_id'] for c in registration['farm'].crops))
        return registration

    def _rows(self, tenant, kind, farm, limit, before):
        growth = kind == KINDS[0]
        store = self.calculation.store if growth else self.harvest.store
        args = [tenant, farm['scenario_id'], farm['scenario_revision'], farm['registration_sha256'], farm['crop_id']]
        cursor = sql.SQL('')
        if before is not None:
            cursor = sql.SQL(' AND (recorded_at,result_id)<(%s,%s)')
            args.extend((before['recorded_at'].astimezone(timezone.utc), before['result_id']))
        args.append(limit+1)
        crop = sql.SQL("convert_from(payload_raw,'UTF8')::jsonb #>> '{binding,request,farm,crop_id}'") if growth else sql.Identifier('crop_id')
        table = store.jobs._table(calculation.storage.schema.TABLE) if growth else sql.Identifier(store.policy.schema, harvest.registry.schema.TABLE)
        connection = store.jobs.connect if growth else store._connection
        with connection() as conn:
            return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND scenario_id=%s '
                'AND scenario_revision=%s AND registration_sha256=%s AND {}=%s{} '
                'ORDER BY recorded_at DESC,result_id DESC LIMIT %s').format(table, crop, cursor), args).fetchall()

    def _parent(self, tenant, result_id, farm, *, registration_checks):
        store = self.calculation.store
        row = store._find(tenant, result_id=result_id)
        packet = store._row(row, tenant, farm)
        binding = store.server.binding
        request, source = packet['binding']['request'], packet['binding']['input']
        key = _canonical({'tenant_id': tenant, 'farm': request['farm'],
            'available_at': request['rights']['available_at'], 'period': source['period']})
        if key not in registration_checks:
            registration_checks[key] = _canonical(binding._registration(tenant, request, source))
        _need(registration_checks[key] == _canonical(packet['binding']['registration'])
              and packet['policies']['input_rights_version'] == binding.input_rights.policy_version
              and packet['policies']['resolver_version'] == store.server.input_resolver.version
              and packet['policies']['notice_sha256'] == sha256(binding.notice_raw).hexdigest())
        binding._rights(tenant, request, source, False)
        store._guard(tenant)
        return row, packet

    def _item(self, tenant, kind, farm, row, *, registration_checks):
        growth = kind == KINDS[0]
        store = self.calculation.store if growth else self.harvest.store
        packet = store._row(row, tenant, farm)
        parent_row, parent = self._parent(tenant, row['result_id'] if growth else packet['parent_result_id'], farm,
                                        registration_checks=registration_checks)
        if growth:
            _need(store._record(parent_row) == store._record(row))
            detail = {'study_id': packet['study_id'], 'revision': packet['revision'],
                'period': deepcopy(packet['binding']['input']['period']),
                'sample_count': packet['artifact']['sample_count'], 'event_count': packet['artifact']['event_count']}
            status = packet['artifact']['status']
        else:
            source = packet['source']
            _need(source['result_id'] == parent['result_id'] and source['payload_sha256'] == parent_row['payload_sha256']
                  and source['input_root_sha256'] == parent['input_root_sha256']
                  and source['artifact_sha256'] == parent['artifact']['sha256']
                  and source['source_status'] == parent['artifact']['status'])
            detail = {'parent_result_id': packet['parent_result_id'], 'row_count': packet['artifact']['row_count']}
            status = source['source_status']
        return {'result_id': row['result_id'], 'recorded_at': _time(row['recorded_at']),
                'calculation_status': status, 'claim_scope': packet['claim_scope'], **detail}

    def read(self, tenant, kind, farm_ref, *, limit=10, before=None):
        with self.open(tenant, kind, farm_ref, limit=limit, before=before) as page:
            return page

    @contextmanager
    def open(self, tenant, kind, farm_ref, *, limit=10, before=None):
        try:
            _request(kind, farm_ref, limit, before)
            farm = deepcopy(farm_ref)
            _need(kind != KINDS[1] or self.harvest is not None)
            registration = self._guard(tenant, farm)
            rows = self._rows(tenant, kind, farm, limit, deepcopy(before))
            _need(len(rows) <= limit+1)
            keys = [(r['recorded_at'], r['result_id']) for r in rows]
            _need(keys == sorted(keys, reverse=True) and len(set(keys)) == len(keys)
                  and (before is None or all(key < (before['recorded_at'], before['result_id']) for key in keys)))
            registration_checks = {}
            items = [self._item(tenant, kind, farm, row, registration_checks=registration_checks) for row in rows]
            snapshots = deepcopy(rows)
            cursor = {k: items[limit-1][k] for k in ('recorded_at', 'result_id')} if len(items) > limit else None
            page = {'version': VERSION, 'scope': 'stored_research_metadata_only', 'kind': kind,
                'farm': farm, 'items': items[:limit], 'next_cursor': cursor,
                'selection_validation_required': True, 'rights_or_gate_approval': False}
            raw = _canonical(page)
            _need(len(raw) <= MAX_PAGE_BYTES)
            def recheck():
                _need(self._guard(tenant, farm) == registration)
                store = self.calculation.store if kind == KINDS[0] else self.harvest.store
                registration_checks = {}
                for row, item in zip(snapshots, items):
                    found = store._find(tenant, result_id=row['result_id']) if kind == KINDS[0] else store._find(tenant, row['result_id'])
                    _need(found == row and self._item(tenant, kind, farm, found,
                          registration_checks=registration_checks) == item)
                _need(self._guard(tenant, farm) == registration)
            recheck()
            yield deepcopy(page)
            recheck()
        except PermissionError:
            raise
        except Exception:
            raise CropResultCatalogHold('stored crop result catalog unavailable') from None
