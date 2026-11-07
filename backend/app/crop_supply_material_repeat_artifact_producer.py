"""Validate one genuine selection, then publish it through renewed physical access."""
from contextlib import ExitStack
from hashlib import sha256
from pathlib import Path
from typing import NamedTuple
import os
import sys
import time

from . import crop_supply_material_repeat_artifact_reader as reader

owner, point = reader.owner, reader.point
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


class _Bundle(NamedTuple):
    root: str
    payloads: tuple
    sources: tuple
    handle_state: tuple
    workspace: tuple
    pins: tuple
    code_metadata: tuple
    parent_code_metadata: tuple
    rights_refs: tuple
    effective_rights: tuple
    deadline: float


def _runtime(metadata=None, code_metadata=None):
    reader._runtime(metadata, code_metadata)
    reader.need(_POLICY_FIELDS == ('completed-parent-verified-transfer-v1', 600),
                'CODE_HOLD: fixed artifact transfer policy required')
    reader.need(point._signature(sys.modules[__name__]) == _SELF_SIGNATURE,
                'CODE_HOLD: unchanged loaded repeat artifact producer required')
    reader.need(globals().get('time') is _CLOCK_FIELDS[0]
                and vars(_CLOCK_FIELDS[0]).get('monotonic') is _CLOCK_FIELDS[1],
                'CODE_HOLD: unchanged artifact monotonic clock required')


def _dispatch(store=None, signature=point._signature, signature_code=point._signature.__code__,
              capture=point._capture_acquisition, capture_code=point._capture_acquisition.__code__):
    if not (point._signature is signature and signature.__code__ is signature_code
            and point._capture_acquisition is capture and capture.__code__ is capture_code):
        raise reader.RepeatArtifactHold('CODE_HOLD: unchanged dispatch inspectors required')
    reader.need(signature(sys.modules[__name__]) == _SELF_SIGNATURE,
                'CODE_HOLD: unchanged artifact transfer dispatch required')
    reader.need(capture() == _GUARD_FIELDS[0], 'CODE_HOLD: original acquisition dispatch changed')
    for module, expected in _GUARD_FIELDS[1]:
        reader.need(signature(module) == expected, 'CODE_HOLD: current transfer dependency dispatch required')
    reader.need(globals().get('os') is _OS_FIELDS[0]
                and vars(_OS_FIELDS[0]).get('stat') is _OS_FIELDS[1]
                and vars(_OS_FIELDS[0]).get('fstat') is _OS_FIELDS[2]
                and globals().get('time') is _CLOCK_FIELDS[0]
                and vars(_CLOCK_FIELDS[0]).get('monotonic') is _CLOCK_FIELDS[1],
                'CODE_HOLD: unchanged physical access and clock primitives required')
    if store is not None:
        reader.need(type(store) is _GUARD_FIELDS[0][5], 'STORAGE_HOLD: actual original-class store required')
        state = object.__getattribute__(store, '__dict__')
        for name, expected in _GUARD_FIELDS[2]:
            method = getattr(store, name)
            reader.need(getattr(method, '__self__', None) is store and getattr(method, '__func__', None) is expected,
                        'CODE_HOLD: unchanged bound storage dispatch required')
        _access(state['_access'])


def _access(access, *, writer=False):
    reader.need(type(access) is _GUARD_FIELDS[0][8], 'STORAGE_HOLD: exact concrete access required')
    for name, expected in _GUARD_FIELDS[3]:
        method = getattr(access, name)
        reader.need(getattr(method, '__self__', None) is access and getattr(method, '__func__', None) is expected,
                    'CODE_HOLD: unchanged bound access dispatch required')
    if writer:
        access.require_writer()


def _state(handle):
    reader.need(type(handle) is owner.Handle and handle._token is owner._TOKEN,
                'CONTEXT_HOLD: genuine current repeat Handle required')
    return (handle._definition, handle.cursor_sha256, handle._current, handle._basis, handle._cursor)


def _stat(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _locations(workspace):
    old = workspace.original_material_workspace
    forcing = old.forcing_workspace; base = forcing.source_workspace
    return (('original', base.source_directory, base.access, False),
            ('base', base.archive_directory, base.access, True),
            ('forcing', forcing.archive_directory, forcing.access, True),
            ('material', old.archive_directory, old.access, True),
            ('repeat', workspace.repeat_archive_directory, workspace.access, True))


def _target(directory, workspace):
    target = Path(directory)
    old = workspace.original_material_workspace
    forcing = old.forcing_workspace; base = forcing.source_workspace
    parents = [Path(v).resolve() for v in (base.source_directory, base.archive_directory,
        forcing.archive_directory, old.archive_directory, workspace.repeat_archive_directory)]
    reader.need(target.is_absolute() and '..' not in target.parts and target.resolve() == target
        and not target.is_symlink() and all(target != p and target not in p.parents and p not in target.parents for p in parents),
        'STORAGE_HOLD: physically separate nonsymlink artifact output required')
    return target


def _preflight(store, payloads, root, transfer):
    transfer.edge(store); total, count = store._usage(); transfer.edge(store)
    order = [(h, data, maximum) for h, (data, maximum) in sorted(payloads.items()) if h != root]
    order.append((root, *payloads[root]))
    for h, data, maximum in order:
        transfer.edge(store)
        try:
            _OS_FIELDS[1](h, dir_fd=store._fd, follow_symlinks=False)
        except FileNotFoundError:
            transfer.edge(store)
            reader.need(count + 2 <= reader.FILES and total + 2*len(data) <= reader.TOTAL,
                        'CAPACITY_HOLD: artifact temporary budget exceeded')
            count += 1; total += len(data)
        else:
            transfer.edge(store)
            actual = store.get(h, maximum=maximum); transfer.edge(store)
            reader.need(actual == data, 'HASH_HOLD: exact existing immutable output required')
    return order


def _readback(store, h, expected, maximum, transfer):
    transfer.edge(store); store._guard(); transfer.edge(store)
    before = _stat(_OS_FIELDS[1](h, dir_fd=store._fd, follow_symlinks=False)); transfer.edge(store)
    actual = store.get(h, maximum=maximum); transfer.edge(store)
    after = _stat(_OS_FIELDS[1](h, dir_fd=store._fd, follow_symlinks=False)); transfer.edge(store)
    reader.need(type(actual) is bytes and actual == expected and before == after
                and sha256(actual).hexdigest() == h, 'HASH_HOLD: actual immutable output readback differs')
    return actual, before


def _validate(handle, deadline):
    _runtime(); _dispatch()
    meter = point._Meter()
    meter.fence()
    expected = _state(handle)
    workspace = owner._snapshot(handle._workspace)
    code_metadata = reader._file_metadata(); pins = reader._pins(metadata=meter.code_metadata)
    _runtime(meter.code_metadata, code_metadata)
    with owner._session(handle._definition, handle._workspace, meter) as session:
        original = session.original; forcing = original.parent; base = forcing.origin
        stores = {'original': base.source, 'base': base.archive, 'forcing': forcing.archive,
                  'material': original.archive, 'repeat': session.archive}
        witnessed = {kind: {} for kind in stores}
        def fetch(h, kind, maximum):
            return reader._read_blob(stores[kind], h, witnessed[kind], maximum,
                                     meter=meter, code_metadata=code_metadata)
        manifest, selected, frames, restored = reader._build(handle._definition, handle.cursor_sha256,
            stores, fetch, meter, admitted=session, pins=pins, code_metadata=code_metadata)
        reader.need((reader.raw(restored.basis), reader.raw(frames[-1]['snapshot']))
                    == (handle._basis, reader.raw(handle.current['numeric']['last_confirmed'])),
                    'CONTEXT_HOLD: actual Handle basis and confirmed sample required')
        reader.need(manifest['source']['final'] == {'current': reader.reference(handle._current),
            'basis': reader.reference(handle._basis), 'cursor': reader.reference(handle._cursor)},
            'CONTEXT_HOLD: exact actual Handle raw3 required')
        reader.need(pins['backend/app/crop_supply_material_repeat_artifact_producer.py'] == CODE_SHA256,
                    'CODE_HOLD: actual loaded artifact producer required')
        payloads = {}
        for kind in reader.KINDS:
            for h, data in selected[kind].items():
                maximum = 16777216 if kind == 'original' else reader.MAX
                reader.need(0 < len(data) <= maximum and sha256(data).hexdigest() == h,
                            'CAPACITY_HOLD: actual bounded selected payload required')
                if h in payloads:
                    reader.need(payloads[h][0] == data, 'HASH_HOLD: same digest has one physical payload')
                    maximum = min(maximum, payloads[h][1])
                payloads[h] = (data, maximum)
        root_data = reader.raw(manifest)
        reader.need(len(root_data) <= reader.MAX, 'CAPACITY_HOLD: bounded artifact root required')
        root = sha256(root_data).hexdigest()
        reader.need(root not in payloads, 'HASH_HOLD: root is not its own closure')
        payloads[root] = (root_data, reader.MAX)
        reader.need(len(payloads) <= reader.FILES and sum(len(v[0]) for v in payloads.values()) <= reader.TOTAL,
                    'CAPACITY_HOLD: complete artifact physical limits exceeded')
        source_rows = []
        for kind, path, access, write in _locations(handle._workspace):
            store = stores[kind]
            reader._fence(store, pins, witnessed[kind], complete=True, meter=meter, code_metadata=code_metadata)
            _dispatch(store)
            observed = dict(witnessed[kind])
            if kind == 'original':
                for h, value in base.source_witnesses.items():
                    reader.need(h not in observed or observed[h] == value, 'SOURCE_HOLD: same original witness required')
                    observed[h] = value
            rows = []
            for h, data in sorted(selected[kind].items()):
                reader.need(h in observed and observed[h][0] == data, 'SOURCE_HOLD: actual validated source bytes required')
                metadata = observed[h][1]
                reader.need(_stat(_OS_FIELDS[1](h, dir_fd=store._fd, follow_symlinks=False)) == metadata,
                            'STORAGE_HOLD: source changed while preparing read set')
                rows.append((h, data, metadata))
            info = _OS_FIELDS[2](store._fd)
            source_rows.append((kind, str(path), access, write, (info.st_dev, info.st_ino), tuple(rows)))
        source = manifest['source']
        rights_refs = (source['base']['definition']['sha256'], source['forcing']['definition']['sha256'],
            source['material']['definition']['sha256'], source['original_root']['sha256'],
            source['final']['current']['sha256'],
            tuple(row['point']['witness']['sha256'] for row in manifest['transitions'] if row['kind'] == 'material_adoption'))
        meter.fence(); _runtime(meter.code_metadata, code_metadata)
        reader.need(_state(handle) == expected and owner._snapshot(handle._workspace) == workspace,
                    'CONTEXT_HOLD: source Handle or workspace changed during validation')
    # The bundle does not exist until all genuine parent exits have succeeded.
    meter.fence(); _runtime(meter.code_metadata, code_metadata)
    reader.need(_CLOCK_FIELDS[1]() <= deadline, 'WALL_HOLD: artifact deadline exhausted after validation')
    return _Bundle(root, tuple((h, data, maximum) for h, (data, maximum) in sorted(payloads.items())),
        tuple(source_rows), expected, workspace, tuple(sorted(pins.items())), code_metadata,
        meter.code_metadata, rights_refs, tuple(sorted(manifest['effective_rights'].items())), deadline)


class _Transfer:
    def __init__(self, bundle, handle, access, deadline, access_state):
        reader.need(type(bundle) is _Bundle and type(deadline) is float and deadline <= bundle.deadline,
                    'CONTEXT_HOLD: actual completed validation and unextended artifact deadline required')
        self.bundle, self.handle, self.access, self.deadline = bundle, handle, access, deadline
        reader.need((id(access), tuple(vars(access).items())) == access_state,
                    'STORAGE_HOLD: API-entry output policy changed before transfer')
        self.access_state = access_state
        self.code_metadata = bundle.parent_code_metadata
        self.stores, self.output, self.output_identity = {}, None, None

    def edge(self, store=None):
        _dispatch(store)
        reader.need(_CLOCK_FIELDS[1]() <= self.deadline, 'WALL_HOLD: whole artifact deadline exhausted')

    def bindings(self):
        reader.need(_state(self.handle) == self.bundle.handle_state
                    and owner._snapshot(self.handle._workspace) == self.bundle.workspace,
                    'CONTEXT_HOLD: source Handle or workspace changed during transfer')
        reader.need((id(self.access), tuple(vars(self.access).items())) == self.access_state,
                    'STORAGE_HOLD: output policy changed during transfer')
        _access(self.access, writer=True)

    def rights(self, live):
        bd, fd, md, original, current, witnesses = self.bundle.rights_refs
        bd = reader._document(live['base'][bd]); fd = reader._document(live['forcing'][fd])
        md = reader._document(live['material'][md]); original = reader._document(live['original'][original])
        grants = [reader._rights(bd['rights']), reader._rights(fd['rights']), reader._rights(md['inputs']['rights'])]
        grants.extend(reader._rights(span['rights']) for span in fd['spans'])
        for grant in original['source_rights'].values():
            reader.old.legacy._rights(grant)
        grants.append({'use': True, 'display': True, 'redistribute': original['redistribution_authorized']})
        for reference in witnesses:
            grants.append(reader._rights(reader._document(live['repeat'][reference])['inputs']['rights']))
        rights = {name: all(grant[name] for grant in grants) for name in ('use', 'display', 'redistribute')}
        reader.need(tuple(sorted(reader._rights(rights).items())) == self.bundle.effective_rights
                    and reader._document(live['repeat'][current])['effective_rights'] == rights,
                    'RIGHTS_HOLD: current original/plan/material/repeat grants differ')

    def fence(self, stage=None):
        self.edge(); _runtime(self.code_metadata, self.bundle.code_metadata); self.edge(); self.bindings(); self.edge()
        ready = len(self.stores) == 5
        reader.need(set(self.stores) <= {row[0] for row in self.bundle.sources}
                    and (self.output is None or ready), 'STORAGE_HOLD: actual complete source family set required')
        live = {}
        for kind, path, access, write, identity, rows in self.bundle.sources:
            if kind not in self.stores:
                continue
            store = self.stores[kind]; self.edge(store)
            state = object.__getattribute__(store, '__dict__')
            info = _OS_FIELDS[2](state['_fd'])
            reader.need(state['_access'] is access and state['_write'] is write
                        and (info.st_dev, info.st_ino) == identity,
                        'STORAGE_HOLD: renewed actual source directory/policy differs')
            store._guard(); self.edge(store)
            if ready:
                total, count = store._usage(); self.edge(store)
                reader.need(total <= reader.TOTAL and count <= reader.FILES, 'CAPACITY_HOLD: source directory limits exceeded')
                live[kind] = {}
                for h, expected, metadata in rows:
                    self.edge(store)
                    before = _stat(_OS_FIELDS[1](h, dir_fd=state['_fd'], follow_symlinks=False))
                    reader.need(before == metadata, 'STORAGE_HOLD: renewed source metadata differs')
                    self.edge(store)
                    data = store.get(h, maximum=max(reader.MAX, len(expected))); self.edge(store)
                    after = _stat(_OS_FIELDS[1](h, dir_fd=state['_fd'], follow_symlinks=False)); self.edge(store)
                    reader.need(type(data) is bytes and data == expected and before == after
                                and sha256(data).hexdigest() == h, 'SOURCE_HOLD: renewed full source bytes differ')
                    live[kind][h] = data
        if ready:
            self.edge(); self.rights(live); self.edge()
        if self.output is not None:
            self.edge(self.output); self.output._guard(); self.edge(self.output)
            total, count = self.output._usage(); self.edge(self.output)
            reader.need(total <= reader.TOTAL and count <= reader.FILES, 'CAPACITY_HOLD: output directory limits exceeded')
        self.bindings(); self.edge(); _runtime(self.code_metadata, self.bundle.code_metadata); self.edge()

    def finish(self, target):
        self.edge(); _runtime(self.code_metadata, self.bundle.code_metadata); self.edge(); self.bindings()
        reader.need(all(object.__getattribute__(s, '__dict__')['_fd'] is None for s in self.stores.values())
                    and self.output is not None and object.__getattribute__(self.output, '__dict__')['_fd'] is None,
                    'STORAGE_HOLD: actual transfer and output resources must be closed')
        reader.need(point._directory(target) == self.output_identity, 'STORAGE_HOLD: output changed during cleanup')
        reader.need(reader._pins(metadata=self.code_metadata) == dict(self.bundle.pins), 'CODE_HOLD: final artifact code changed')
        self.edge(); self.bindings(); self.edge()


def _publish(target, access, handle, bundle, deadline, access_state):
    transfer = _Transfer(bundle, handle, access, deadline, access_state)
    transfer.fence()
    with ExitStack() as stack:
        # This is renewed real file access, not a continued numerical owner session.
        for kind, path, policy, write, identity, rows in reversed(bundle.sources):
            transfer.stores[kind] = stack.enter_context(reader._store(Path(path), policy, write=write,
                meter=transfer, code_metadata=bundle.code_metadata))
        reader.need(len(transfer.stores) == 5, 'STORAGE_HOLD: all real source stores required before output access')
        transfer.fence()
        with reader._store(target, access, write=True, meter=transfer, code_metadata=bundle.code_metadata) as output:
            transfer.output = output
            info = _OS_FIELDS[2](output._fd)
            transfer.output_identity = (str(target), info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid)
            transfer.fence()
            payloads = {h: (data, maximum) for h, data, maximum in bundle.payloads}
            order = _preflight(output, payloads, bundle.root, transfer); transfer.fence()
            output_witnesses = {}
            for h, data, maximum in order:
                transfer.fence(); transfer.edge(output)
                reader.need(output.put(data, maximum=maximum) == h, 'HASH_HOLD: actual physical publication identity required')
                transfer.edge(output)
                output_witnesses[h] = _readback(output, h, data, maximum, transfer)
                transfer.fence()
            for h, (data, metadata) in output_witnesses.items():
                reader.need(_readback(output, h, data, max(reader.MAX, len(data)), transfer) == (data, metadata),
                            'STORAGE_HOLD: output changed before final publication fence')
            transfer.fence()
            reader.need(reader._pins(metadata=transfer.code_metadata) == dict(bundle.pins), 'CODE_HOLD: final held publication code changed')
            transfer.edge(output)
    transfer.finish(target)
    return bundle.root


def produce_repeat_material_artifact(directory, access, *, handle):
    entered = _CLOCK_FIELDS[1]()
    try:
        _runtime(); _dispatch()
        deadline = entered + _POLICY_FIELDS[1]
        _state(handle)
        reader.need(type(access) is reader.ContentAccess, 'STORAGE_HOLD: concrete output file policy required')
        access_state = (id(access), tuple(vars(access).items()))
        _access(access, writer=True)
        target = _target(directory, handle._workspace)
        bundle = _validate(handle, deadline)
        root = _publish(target, access, handle, bundle, deadline, access_state)
        _dispatch(); _runtime(bundle.parent_code_metadata, bundle.code_metadata); _dispatch()
        reader.need(_state(handle) == bundle.handle_state and owner._snapshot(handle._workspace) == bundle.workspace,
                    'CONTEXT_HOLD: source Handle/workspace changed before root return')
        _dispatch(); _access(access, writer=True)
        reader.need((id(access), tuple(vars(access).items())) == access_state,
                    'STORAGE_HOLD: API-entry output policy changed before root return')
        reader.need(_CLOCK_FIELDS[1]() <= deadline, 'WALL_HOLD: whole artifact deadline exhausted before return')
        return root
    except reader.RepeatArtifactHold:
        raise
    except (OSError, ValueError, TypeError, KeyError, OverflowError, ZeroDivisionError, RecursionError) as error:
        message = str(error)
        raise reader.RepeatArtifactHold(message if '_HOLD:' in message else 'ARTIFACT_HOLD: invalid or unavailable selected source') from None


_POLICY_FIELDS = ('completed-parent-verified-transfer-v1', 600)
_CLOCK_FIELDS = (time, time.monotonic)
_OS_FIELDS = (os, os.stat, os.fstat)
_GUARD_FIELDS = (point._ACQUISITION_FIELDS,
    tuple((module, point._signature(module)) for module in (
        reader, point, *[item[0] for item in reader._HELPER_FIELDS],
        sys.modules[reader.MorphologyBlobStore.__module__], sys.modules[reader.ContentAccess.__module__], point.jobs)),
    tuple((name, getattr(reader.MorphologyBlobStore, name)) for name in ('get', 'put', '_guard', '_usage')),
    tuple((name, getattr(reader.ContentAccess, name)) for name in ('validate', 'prepare_new', 'require_writer')))
_SELF_SIGNATURE = point._signature(sys.modules[__name__])
