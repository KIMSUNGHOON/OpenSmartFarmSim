"""Bounded stored-result queries retaining original calculation provenance."""
from bisect import bisect_right
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path

from . import crop_cycle_calculation_result_evidence as evidence

VERSION = 'crop-cycle-verified-result-read-context-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
DEPENDENCY_SHA256 = {'result_evidence':evidence.CODE_SHA256}
files, inputs, artifact = evidence.files, evidence.inputs, evidence.artifact
MAX_PAGE_BYTES = artifact.LIMITS['page_bytes']
_DECLARATIONS = (VERSION, CODE_SHA256, tuple(sorted(DEPENDENCY_SHA256.items())), MAX_PAGE_BYTES)


class CalculationResultReadContextHold(ValueError):
    """No current stored-result query; farm and publication are not approved."""


def _need(condition):
    if not condition:
        raise CalculationResultReadContextHold('crop result read context unavailable')


def _pins():
    _need((VERSION, CODE_SHA256, tuple(sorted(DEPENDENCY_SHA256.items())), MAX_PAGE_BYTES) == _DECLARATIONS
          and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
          and sha256(Path(evidence.__file__).read_bytes()).hexdigest() == DEPENDENCY_SHA256['result_evidence'])


class CalculationResultReadContext:
    def __init__(self, result_directory, artifact_sha256, input_directory, input_root_sha256,
                 input_evidence_raw, result_evidence_raw, *, authority):
        self._fd, self._cache = None, {}
        try:
            _pins(); _need(type(authority) is evidence.CalculationResultEvidenceAuthority)
            self._authority = authority
            self._args = (Path(result_directory), artifact_sha256, Path(input_directory),
                          input_root_sha256, input_evidence_raw, result_evidence_raw)
            verified = authority.verify(*self._args)
            self._summary_raw = inputs._canonical(verified.summary)
            self._context_raw = inputs._canonical(verified.context)
            self._identity_raw = inputs._canonical(verified.identity)
            self._index = verified.index
            self._counts = verified.summary['counts']
            self._starts = {kind:tuple(page['start'] for page in index) for kind,index in self._index.items()}
            snapshot = inputs._json(result_evidence_raw)['payload']['snapshot']
            self._inode = tuple(snapshot['inode'])
            self._fd = files.job_store._open_directory_nofollow(self._args[0])
            current = files._secure(self._fd, directory=True)
            _need((current.st_dev,current.st_ino) == self._inode)
            self.recheck()
        except Exception:
            self.close()
            raise CalculationResultReadContextHold('crop result read context unavailable') from None

    def __enter__(self):
        try:
            self.recheck(); return self
        except Exception:
            self.close()
            raise CalculationResultReadContextHold('crop result read context unavailable') from None

    def __exit__(self, *args):
        self.close()

    @property
    def closed(self):
        return self._fd is None

    def _open(self):
        _need(not self.closed)
        _pins()

    def close(self):
        if self._fd is not None:
            fd, self._fd = self._fd, None
            os.close(fd)
        self._cache.clear()

    def recheck(self):
        try:
            self._open()
            current = files._secure(self._fd, directory=True)
            _need((current.st_dev,current.st_ino) == self._inode)
            verified = self._authority.verify(*self._args)
            _need(tuple(evidence._inode(self._args[0])) == self._inode
                  and inputs._canonical(verified.summary) == self._summary_raw
                  and inputs._canonical(verified.context) == self._context_raw
                  and inputs._canonical(verified.identity) == self._identity_raw
                  and verified.index == self._index)
        except Exception:
            self.close()
            raise CalculationResultReadContextHold('crop result read context unavailable') from None

    def _copy(self, raw):
        try:
            self._open(); value = inputs._json(raw)
            self.recheck()
            return value
        except Exception:
            self.close()
            raise CalculationResultReadContextHold('crop result read context unavailable') from None

    def facts(self):
        try:
            self._open()
            value = {'summary': inputs._json(self._summary_raw),
                     'context': inputs._json(self._context_raw),
                     'identity': inputs._json(self._identity_raw)}
            value['identity'].update(read_context_version=VERSION, read_code_sha256=CODE_SHA256,
                                     read_dependency_sha256=dict(DEPENDENCY_SHA256))
            self.recheck()
            return value
        except Exception:
            self.close()
            raise CalculationResultReadContextHold('crop result read context unavailable') from None

    @property
    def summary(self):
        return self._copy(self._summary_raw)

    @property
    def manifest(self):
        return self.summary['manifest']

    @property
    def context_record(self):
        return self._copy(self._context_raw)

    @property
    def identity(self):
        value = self._copy(self._identity_raw)
        return {**value,'read_context_version':VERSION,'read_code_sha256':CODE_SHA256,
                'read_dependency_sha256':dict(DEPENDENCY_SHA256)}

    @property
    def rights_or_gate_approval(self):
        return False

    def _load(self, kind, descriptor):
        fd = files._file(self._fd, descriptor['sha256']+'.json')
        try:
            before = files._secure(fd)
            _need(0 < before.st_size <= MAX_PAGE_BYTES)
            metadata = files.operator_config._metadata(before)
            cached = self._cache.get(kind)
            if cached is not None and cached[0] == descriptor['sha256'] and cached[2] == metadata:
                return cached[1]
            with os.fdopen(fd,'rb',closefd=False) as handle:
                raw = handle.read(MAX_PAGE_BYTES+1)
            after = files._secure(fd)
            _need(metadata == files.operator_config._metadata(after) and len(raw) == before.st_size
                  and sha256(raw).hexdigest() == descriptor['sha256'])
            rows = inputs._json(raw)
            _need(type(rows) is list and len(rows) == descriptor['count'] and inputs._canonical(rows) == raw
                  and all(type(row) is dict and 'at' in row for row in rows)
                  and rows[0]['at'] == descriptor['first_at'] and rows[-1]['at'] == descriptor['last_at'])
            self._cache[kind] = (descriptor['sha256'],rows,metadata)
            return rows
        finally:
            os.close(fd)

    def page(self, kind, start=0, limit=None, *, max_bytes=MAX_PAGE_BYTES):
        try:
            self._open()
            _need(kind in self._index)
            maximum = 64 if kind == 'samples' else 8
            limit = maximum if limit is None else limit
            total = self._counts[kind]
            _need(type(start) is int and 0 <= start <= total
                  and type(limit) is int and 1 <= limit <= maximum
                  and type(max_bytes) is int and 1 <= max_bytes <= MAX_PAGE_BYTES)
            rows, position, block, values = [], start, None, None
            while position < min(start+limit,total):
                at = bisect_right(self._starts[kind],position)-1
                descriptor = self._index[kind][at]
                if block != at:
                    values = self._load(kind,descriptor); block = at
                value = values[position-descriptor['start']]
                candidate = {'kind':kind,'start':start,'next':position+1,'total':total,'records':rows+[value]}
                if len(inputs._canonical(candidate)) > max_bytes:
                    _need(bool(rows)); break
                rows.append(value); position += 1
            result = {'kind':kind,'start':start,'next':position,'total':total,'records':deepcopy(rows)}
            _need(len(inputs._canonical(result)) <= max_bytes)
            self.recheck()
            return result
        except Exception:
            self.close()
            raise CalculationResultReadContextHold('crop result read context unavailable') from None


def open_calculation_result_read_context(result_directory, artifact_sha256, input_directory, input_root_sha256,
                             input_evidence_raw, result_evidence_raw, *, authority):
    return CalculationResultReadContext(result_directory, artifact_sha256, input_directory, input_root_sha256,
                             input_evidence_raw, result_evidence_raw, authority=authority)
