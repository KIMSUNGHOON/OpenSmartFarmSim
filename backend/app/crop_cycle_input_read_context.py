"""Versioned read-only input queries with original calculation provenance."""
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path

from . import crop_cycle_input_evidence as evidence
from . import crop_cycle_input_stream as inputs
from . import crop_cycle_stream_execution as engine

VERSION = 'crop-cycle-input-read-context-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES = {'input_evidence':evidence,'original_input':inputs,'original_grid':engine}
DEPENDENCY_SHA256 = {name:sha256(Path(module.__file__).read_bytes()).hexdigest()
                     for name,module in _MODULES.items()}
files = evidence.files


class InputReadContextHold(ValueError):
    """No verified read context; calculation and publication are not permitted."""


def _need(condition):
    if not condition:
        raise InputReadContextHold('crop input read context unavailable')


def _pins():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
          and {name:sha256(Path(module.__file__).read_bytes()).hexdigest()
               for name,module in _MODULES.items()} == DEPENDENCY_SHA256)


@dataclass(frozen=True)
class _IndexPage:
    cursor: bytes | None
    previous: str | None
    steps: int


class _InputPages:
    def __init__(self, fd, root_raw, root_sha256, plan, seconds):
        self._fd, self._raw, self.root_sha256 = fd, root_raw, root_sha256
        self._root = inputs._json(root_raw)
        self._plan, self._seconds, self._cache = deepcopy(plan), seconds, {}
        self._begin, self._end = (inputs.physical._utc(self._root['period'][key]) for key in ('start','end'))
        self.calculation_sha256 = inputs._hash({**self._root,
            'streams':{name:stream for name,stream in self._root['streams'].items() if name != 'outputs'}})

    @property
    def closed(self):
        return self._fd is None

    @property
    def manifest(self):
        return inputs._json(self._raw)

    @property
    def plan(self):
        return deepcopy(self._plan)

    def close(self):
        if self._fd is not None:
            os.close(self._fd); self._fd = None
        self._cache.clear()

    def _load(self, kind, block_index):
        _need(not self.closed)
        block = self._root['streams'][kind]['blocks'][block_index]
        fd = files._file(self._fd, block['sha256']+'.json')
        try:
            before = files._secure(fd)
            _need(0 < before.st_size <= inputs.MAX_BLOCK_BYTES)
            cached = self._cache.get(kind)
            metadata = files.operator_config._metadata(before)
            if cached is not None and cached[0] == block_index and cached[2] == metadata:
                return cached[1]
            with os.fdopen(fd, 'rb', closefd=False) as handle:
                raw = handle.read(inputs.MAX_BLOCK_BYTES+1)
            after = files._secure(fd)
            _need(len(raw) == before.st_size and metadata == files.operator_config._metadata(after)
                  and sha256(raw).hexdigest() == block['sha256'])
            records = inputs._json(raw)
            _need(type(records) is list and len(records) == block['count'])
            normalized = [inputs._normalise(kind, value) for value in records]
            _need(inputs._canonical(normalized) == raw
                  and block['first_at'] == inputs._time(kind, normalized[0])
                  and block['last_at'] == inputs._time(kind, normalized[-1]))
            self._cache[kind] = (block_index, normalized, metadata)
            return normalized
        finally:
            os.close(fd)

    _record = inputs.InputPacket._record
    record = inputs.InputPacket.record
    segment = inputs.InputPacket.segment
    _next_boundary = inputs.InputPacket._next_boundary
    _count_through = inputs.InputPacket._count_through
    _validate_cursor = inputs.InputPacket._validate_cursor
    cursor_bytes = inputs.InputPacket.cursor_bytes
    restore_cursor = inputs.InputPacket.restore_cursor
    boundary_page = inputs.InputPacket.boundary_page


class InputReadContext:
    def __init__(self, directory, root_sha256, evidence_raw, *, authority):
        self.reader, self._cache = None, {}
        fd = None
        try:
            _pins()
            _need(type(authority) is evidence.InputEvidenceAuthority)
            verified = authority.verify(directory, root_sha256, evidence_raw)
            self._authority, self._directory = authority, Path(directory)
            self._evidence_raw, self._input_root_sha256 = evidence_raw, root_sha256
            self._record_raw = inputs._canonical(verified.context)
            record = verified.context
            self.root_sha256 = record['context_sha256']
            self.planned_steps, self.boundary_count = record['planned_steps'], record['boundary_count']
            self.index = tuple(_IndexPage(None if page['cursor'] is None else inputs._canonical(page['cursor']),
                page['previous'], page['steps']) for page in record['index'])
            fd = files.job_store._open_directory_nofollow(self._directory)
            info = files._secure(fd, directory=True)
            self._inode = (info.st_dev, info.st_ino)
            root_raw = files._read(fd, 'root.json', inputs.MAX_ROOT_BYTES)
            _need(sha256(root_raw).hexdigest() == root_sha256)
            self.reader = _InputPages(fd, root_raw, root_sha256, record['plan'],
                authority.profiles['growth_profile'].values['seconds_per_day'])
            fd = None
            _need(self.reader.calculation_sha256 == record['manifest']['calculation_sha256'])
            self.recheck()
        except Exception:
            self.close()
            raise InputReadContextHold('crop input read context unavailable') from None
        finally:
            if fd is not None:
                os.close(fd)

    def __enter__(self):
        self._open(); return self

    def __exit__(self, *args):
        self.close()

    def _open(self):
        _need(self.reader is not None and not self.reader.closed)

    def close(self):
        if self.reader is not None:
            self.reader.close()
        self._cache.clear()

    @property
    def context_record(self):
        self._open(); return inputs._json(self._record_raw)

    @property
    def manifest(self):
        return self.context_record['manifest']

    @property
    def identity(self):
        self._open()
        return {'read_context_version':VERSION,'read_code_sha256':CODE_SHA256,
                'dependency_sha256':dict(DEPENDENCY_SHA256),'evidence_sha256':sha256(self._evidence_raw).hexdigest(),
                'input_root_sha256':self._input_root_sha256,'math_context_sha256':self.root_sha256,
                'scope':'synthetic_input_read_only'}

    @property
    def rights_or_gate_approval(self):
        return False

    def recheck(self):
        fd = None
        try:
            self._open(); _pins()
            fd = files.job_store._open_directory_nofollow(self._directory)
            info = files._secure(fd, directory=True)
            _need((info.st_dev, info.st_ino) == self._inode)
            files._secure(self.reader._fd, directory=True)
            current = self._authority.verify(self._directory, self._input_root_sha256, self._evidence_raw)
            _need(inputs._canonical(current.context) == self._record_raw)
        except Exception:
            self.close()
            raise InputReadContextHold('crop input read context unavailable') from None
        finally:
            if fd is not None:
                os.close(fd)

    def _call(self, method, *args, **kwargs):
        try:
            self._open()
            return method(*args, **kwargs)
        except Exception:
            self.close()
            raise InputReadContextHold('crop input read context unavailable') from None

    def record(self, kind, index):
        return self._call(self.reader.record, kind, index)

    def segment(self, index):
        return self._call(self.reader.segment, index)

    def boundary_page(self, cursor=None, limit=inputs.BLOCK_RECORDS):
        return self._call(self.reader.boundary_page, cursor, limit)

    def cursor_bytes(self, cursor):
        return self._call(self.reader.cursor_bytes, cursor)

    def restore_cursor(self, raw):
        return self._call(self.reader.restore_cursor, raw)

    def boundary(self, index):
        return deepcopy(self._call(engine._boundary, self, index))


def open_input_read_context(directory, root_sha256, evidence_raw, *, authority):
    return InputReadContext(directory, root_sha256, evidence_raw, authority=authority)
