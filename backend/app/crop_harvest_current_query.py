"""Current display authority for server-registered immutable harvest arithmetic."""
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path

from . import crop_harvest_registry as registry

replay, harvest, current = registry.replay, registry.harvest, registry.current
VERSION = 'crop-harvest-registered-current-query-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_RESULT_BYTES = 2 * 1024**2
_MODULES = {'registry':registry,'artifact':replay,'crop_query':current}
DEPENDENCY_SHA256 = {name:sha256(Path(module.__file__).read_bytes()).hexdigest() for name,module in _MODULES.items()}
_DECLARATIONS = registry._canonical([VERSION,CODE_SHA256,MAX_RESULT_BYTES,DEPENDENCY_SHA256])


class HarvestCurrentQueryHold(ValueError):
    """No currently displayable registered harvest calculation."""


def _need(condition):
    if not condition:raise HarvestCurrentQueryHold('current harvest research result unavailable')


def _pins():
    _need(registry._canonical([VERSION,CODE_SHA256,MAX_RESULT_BYTES,DEPENDENCY_SHA256]) == _DECLARATIONS
        and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
        and {name:sha256(Path(module.__file__).read_bytes()).hexdigest() for name,module in _MODULES.items()} == DEPENDENCY_SHA256)
    registry._pins()


def _request(result_id, farm, start, limit):
    _need(type(result_id) is str and result_id.startswith(registry.VERSION+':')
        and current.inputs._digest(result_id[len(registry.VERSION)+1:]))
    _need(type(farm) is dict and set(farm) == {'scenario_id','scenario_revision','registration_sha256','crop_id'}
        and all(current.storage._name(farm[k]) for k in ('scenario_id','scenario_revision','crop_id'))
        and current.inputs._digest(farm['registration_sha256']))
    _need(type(start) is int and start >= 0 and (limit is None and start == 0
        or type(limit) is int and 1 <= limit <= replay.LIMITS['page_records']))


def _bounded(value):
    record = value['record']
    encoded = {**value,'record':{'result_id':record['result_id'],'payload_raw_utf8':record['payload_raw'].decode('utf-8'),
        'payload_sha256':record['payload_sha256'],'recorded_at':record['recorded_at'].isoformat()}}
    _need(len(registry._canonical(encoded)) <= MAX_RESULT_BYTES)


class HarvestCurrentQuery:
    def __init__(self, store):
        try:
            _need(type(store) is registry.HarvestRegistry and store.role == store.policy.reader)
            self.store = store;self._fixed = store,store._pointers();self._binding()
        except Exception:raise HarvestCurrentQueryHold('current harvest query configuration unavailable') from None

    def _binding(self):
        _pins();_need((self.store,self.store._pointers()) == self._fixed and self.store.role == self.store.policy.reader)
        self.store._binding()

    def _guard(self, tenant):
        self._binding();self.store.query.store._guard(tenant)
        fd = registry.files._open_directory_nofollow(self.store.directory)
        try:registry._root_usage(fd)
        finally:os.close(fd)

    def _recheck(self, tenant, row, packet, reader, page=None, limit=None):
        self._guard(tenant);current_row = self.store._find(tenant,row['result_id'])
        _need(self.store._row(current_row,tenant,packet['farm']) == packet
            and self.store._record(current_row) == self.store._record(row))
        reader._guard();_need(reader._root['source'] == packet['source'])
        if page is not None:_need(reader.page(page['start'],limit) == page)
        self._guard(tenant)

    @contextmanager
    def _parent_read(self, tenant, result_id, farm):
        parent = self.store.query;active = True
        try:
            with parent.open(tenant,result_id,farm) as original:
                _need(original is not None)
                value = deepcopy(original);record = value['record'];packet = current.inputs._json(record['payload_raw'])
                request = packet['binding']['request'];source = packet['binding']['input']
                def read():
                    _need(active);parent._binding();parent.store._guard(tenant)
                    row = parent.store._find(tenant,result_id=result_id)
                    _need(parent.store._record(row) == record
                        and registry._canonical(parent.store._row(row,tenant,farm)) == registry._canonical(packet))
                    binding = parent.store.server.binding
                    registration = binding._registration(tenant,request,source)
                    _need(registry._canonical(registration) == registry._canonical(packet['binding']['registration'])
                        and binding.input_rights.policy_version == packet['policies']['input_rights_version']
                        and parent.store.server.input_resolver.version == packet['policies']['resolver_version']
                        and sha256(binding.notice_raw).hexdigest() == packet['policies']['notice_sha256'])
                    declaration = deepcopy(request['rights'])
                    _need(binding.input_rights(tenant,declaration,source['root_sha256'],'research_display') is True
                        and registry._canonical(declaration) == registry._canonical(request['rights']))
                    parent._binding();parent.store._guard(tenant)
                    return deepcopy(value)
                yield read
        finally:active = False

    def read(self, tenant, result_id, farm_ref, *, start=0, limit=None):
        with self.open(tenant,result_id,farm_ref,start=start,limit=limit) as value:return value

    @contextmanager
    def open(self, tenant, result_id, farm_ref, *, start=0, limit=None):
        try:
            self._guard(tenant);_request(result_id,farm_ref,start,limit)
            row = self.store._find(tenant,result_id)
            if row is None:
                self._guard(tenant);yield None;self._guard(tenant);return
            packet = self.store._row(row,tenant,farm_ref);artifact = packet['artifact']
            with self._parent_read(tenant,packet['parent_result_id'],farm_ref) as read_parent, \
                    replay._Reader(self.store.directory/artifact['key'],artifact['sha256'],read_parent) as reader:
                root = reader._root
                _need(root['source'] == packet['source'] and root['row_count'] == artifact['row_count']
                    and root['row_chain_sha256'] == artifact['row_chain_sha256']
                    and sha256(root['parameter_raw_utf8'].encode()).hexdigest() == packet['parameters']['mass_sha256']
                    and sha256(root['allocation_raw_utf8'].encode()).hexdigest() == packet['parameters']['allocation_sha256'])
                summary = reader.summary();page = None if limit is None else reader.page(start,limit)
                identity = {'version':VERSION,'code_sha256':CODE_SHA256,'dependency_sha256':deepcopy(DEPENDENCY_SHA256),
                    'result_id':result_id,'payload_sha256':row['payload_sha256'],'artifact_sha256':artifact['sha256'],
                    'parent_source':deepcopy(packet['source']),'rights_or_gate_approval':False}
                value = {'record':deepcopy(self.store._record(row)),'summary':summary,'page':page,'identity':identity}
                _bounded(value);self._recheck(tenant,row,packet,reader)
                yield value
                self._recheck(tenant,row,packet,reader,page,limit)
        except PermissionError:raise
        except Exception:raise HarvestCurrentQueryHold('current harvest research result unavailable') from None
