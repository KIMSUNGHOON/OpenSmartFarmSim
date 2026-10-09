"""Immutable synthetic harvest math, bound to currently readable crop results."""
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
from uuid import uuid4

from . import crop_harvest as harvest

current = harvest.current_query
files = current.server
_canonical = harvest._canonical
VERSION = 'crop-harvest-artifact-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
LIMITS = {'page_records': 64, 'page_bytes': 2 * 1024**2, 'root_bytes': 2 * 1024**2,
          'directory_bytes': 512 * 1024**2, 'files': 65536, 'pages': 16384}
_MODULES = {'harvest': harvest, 'current_query': current, 'files': files}
DEPENDENCY_SHA256 = {name: sha256(Path(module.__file__).read_bytes()).hexdigest() for name, module in _MODULES.items()}
_DECLARATIONS = _canonical([VERSION, CODE_SHA256, LIMITS, DEPENDENCY_SHA256])


class HarvestArtifactHold(ValueError):
    """No complete currently readable harvest artifact for this identity."""


def _need(condition):
    if not condition:raise HarvestArtifactHold('harvest research artifact unavailable')


def _pins():
    _need(_canonical([VERSION, CODE_SHA256, LIMITS, DEPENDENCY_SHA256]) == _DECLARATIONS
          and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
          and {name: sha256(Path(module.__file__).read_bytes()).hexdigest() for name, module in _MODULES.items()} == DEPENDENCY_SHA256)
    harvest._pins()


def _blob(fd, digest, maximum):
    _need(current.inputs._digest(digest))
    raw = files._read(fd, digest + '.json', maximum)
    _need(sha256(raw).hexdigest() == digest)
    value = current.inputs._json(raw);_need(_canonical(value) == raw)
    return value


def _put(fd, raw, maximum):
    _need(type(raw) is bytes and 0 < len(raw) <= maximum)
    size, count = files._usage(fd, 'artifact')
    _need(size + 2 * len(raw) <= LIMITS['directory_bytes'] and count + 2 <= LIMITS['files'])
    digest = sha256(raw).hexdigest()
    files._immutable(fd, digest + '.json', raw, maximum, '.blob-')
    return digest


def _head(fd):
    raw = files._read(fd, 'HEAD', 8192);value = current.inputs._json(raw)
    _need(type(value) is dict and set(value) == {'version', 'artifact_sha256'}
          and value['version'] == VERSION and current.inputs._digest(value['artifact_sha256']) and _canonical(value) == raw)
    return value['artifact_sha256']


def _publish(fd, digest, check):
    raw = _canonical({'version': VERSION, 'artifact_sha256': digest})
    if files._exists(fd, 'HEAD'):
        _need(_head(fd) == digest);check();return
    name = '.head-' + uuid4().hex + '.tmp'
    try:
        handle = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=fd)
        with os.fdopen(handle, 'wb') as stream:
            stream.write(raw);stream.flush();os.fchmod(stream.fileno(), 0o400);os.fsync(stream.fileno())
        check();files._usage(fd, 'artifact')
        os.replace(name, 'HEAD', src_dir_fd=fd, dst_dir_fd=fd);os.fsync(fd)
    finally:
        try:os.unlink(name, dir_fd=fd);os.fsync(fd)
        except FileNotFoundError:pass


def _write(directory, read, parameter_raw, allocation_raw):
    _pins();parameters = harvest._mass_parameters(parameter_raw)
    allocation = harvest._allocation_parameters(allocation_raw, parameters)
    original = read();harvest._allocation_scope(allocation[0], original)
    fd = files._open_directory_nofollow(Path(directory));lock = None
    try:
        files._secure(fd, directory=True);lock = files._file(fd, '.writer-lock', lock=True)
        identity = os.fstat(fd);descriptors = [];count = 0;page = [];page_bytes = 2
        def check():
            _pins();harvest._same(read(), original)
            other = files._open_directory_nofollow(Path(directory))
            try:
                info = files._secure(other, directory=True)
                _need((info.st_dev, info.st_ino) == (identity.st_dev, identity.st_ino))
            finally:os.close(other)
        def flush():
            nonlocal page, count, page_bytes
            if not page:return
            _need(len(descriptors) < LIMITS['pages'])
            digest = _put(fd, b'[' + b','.join(page) + b']', LIMITS['page_bytes'])
            descriptors.append({'sha256': digest, 'start': count, 'count': len(page)})
            count += len(page);page = [];page_bytes = 2
        def stream():
            nonlocal page_bytes
            for row in harvest._read_allocations(read, parameter_raw, allocation_raw):
                raw = _canonical(row);_need(len(raw) + 2 <= LIMITS['page_bytes'])
                if page and (len(page) == LIMITS['page_records'] or page_bytes + len(raw) + 1 > LIMITS['page_bytes']):flush()
                page_bytes += len(raw) + bool(page);page.append(raw)
                yield row
            flush()
        summary = harvest._allocation_totals(stream(), allocation)
        root = {'version': VERSION, 'code_sha256': CODE_SHA256, 'dependency_sha256': DEPENDENCY_SHA256,
                'limits': LIMITS, 'source': harvest._source(original), 'query_identity': deepcopy(original['identity']),
                'parameter_raw_utf8': parameter_raw.decode('utf-8'), 'allocation_raw_utf8': allocation_raw.decode('utf-8'),
                'pages': descriptors, 'row_count': count, 'row_chain_sha256': summary['row_chain_sha256'], 'summary': summary}
        digest = _put(fd, _canonical(root), LIMITS['root_bytes'])
        check();_publish(fd, digest, check);check();files._usage(fd, 'artifact')
        return {'artifact_sha256': digest, 'artifact_id': VERSION + ':' + digest, 'row_count': count,
                'row_chain_sha256': root['row_chain_sha256'], 'claim_scope': summary['claim_scope'], 'rights_or_gate_approval': False}
    finally:
        if lock is not None:os.close(lock)
        os.close(fd)


def write_harvest_artifact(directory, query, tenant, result_id, farm_ref, parameter_raw, allocation_raw):
    try:
        _need(type(query) is current.CalculationCurrentCycleQuery)
        return _write(directory, lambda **kwargs: query.read(tenant, result_id, farm_ref, **kwargs), parameter_raw, allocation_raw)
    except PermissionError:raise
    except Exception:raise HarvestArtifactHold('harvest research artifact unavailable') from None


class _Reader:
    def __init__(self, directory, expected, read):
        self._fd = None;self._directory = Path(directory);self._read = read;self._expected = expected
        try:
            _pins();self._fd = files._open_directory_nofollow(self._directory)
            self._identity = files._secure(self._fd, directory=True);_need(_head(self._fd) == expected)
            self._root = _blob(self._fd, expected, LIMITS['root_bytes']);self._original = read()
            root = self._root
            _need(type(root) is dict and set(root) == {'version', 'code_sha256', 'dependency_sha256', 'limits',
                'source', 'query_identity', 'parameter_raw_utf8', 'allocation_raw_utf8', 'pages', 'row_count', 'row_chain_sha256', 'summary'}
                and root['version'] == VERSION and root['code_sha256'] == CODE_SHA256
                and root['dependency_sha256'] == DEPENDENCY_SHA256 and root['limits'] == LIMITS
                and root['source'] == harvest._source(self._original) and root['query_identity'] == self._original['identity'])
            parameters = harvest._mass_parameters(root['parameter_raw_utf8'].encode('utf-8'))
            profile, digest = harvest._allocation_parameters(root['allocation_raw_utf8'].encode('utf-8'), parameters)
            harvest._allocation_scope(profile, self._original)
            _need(type(root['pages']) is list and len(root['pages']) <= LIMITS['pages'])
            cursor = 0
            for descriptor in root['pages']:
                _need(type(descriptor) is dict and set(descriptor) == {'sha256', 'start', 'count'}
                      and current.inputs._digest(descriptor['sha256']) and type(descriptor['start']) is int
                      and descriptor['start'] == cursor and type(descriptor['count']) is int
                      and 1 <= descriptor['count'] <= LIMITS['page_records'])
                cursor += descriptor['count']
            summary = root['summary']
            _need(type(root['row_count']) is int and root['row_count'] == cursor == summary['row_count']
                  and current.inputs._digest(root['row_chain_sha256']) and root['row_chain_sha256'] == summary['row_chain_sha256']
                  and summary['source'] == root['source'] and summary['allocation_parameters'] == profile
                  and summary['allocation_sha256'] == digest and summary['rights_or_gate_approval'] is False
                  and summary['claim_scope'] == 'synthetic_harvest_allocation_math_only')
            self._guard()
        except BaseException:self.close();raise

    def close(self):
        if self._fd is not None:os.close(self._fd);self._fd = None

    def __enter__(self):return self
    def __exit__(self, *args):self.close()

    def _guard(self):
        _pins();_need(self._fd is not None)
        other = files._open_directory_nofollow(self._directory)
        try:
            info = files._secure(other, directory=True)
            _need((info.st_dev, info.st_ino) == (self._identity.st_dev, self._identity.st_ino))
        finally:os.close(other)
        harvest._same(self._read(), self._original)
        _need(_head(self._fd) == self._expected and _blob(self._fd, self._expected, LIMITS['root_bytes']) == self._root)
        files._usage(self._fd, 'artifact')

    def _operation(self, action):
        try:
            self._guard();value = action();self._guard();return value
        except PermissionError:self.close();raise
        except Exception:self.close();raise HarvestArtifactHold('harvest research artifact unavailable') from None

    def summary(self):
        return self._operation(lambda: deepcopy(self._root['summary']))

    def verify_all_rows(self):
        def verified():
            chain = sha256();count = 0;page_start = 0;page_bytes = 0
            for descriptor in self._root['pages']:
                values = _blob(self._fd, descriptor['sha256'], LIMITS['page_bytes'])
                _need(type(values) is list and len(values) == descriptor['count']
                      and descriptor['start'] == count)
                for row in values:
                    raw = _canonical(row);chain.update(raw + b'\n')
                    page_bytes += len(raw) + (count > page_start);count += 1
                    if count - page_start == LIMITS['page_records'] or count == self._root['row_count']:
                        envelope = {'start': page_start, 'next': count, 'total': self._root['row_count'], 'records': []}
                        _need(len(_canonical(envelope)) + page_bytes <= LIMITS['page_bytes'])
                        page_start = count;page_bytes = 0
            digest = chain.hexdigest()
            _need(count == self._root['row_count'] and digest == self._root['row_chain_sha256'])
            return {'row_count': count, 'row_chain_sha256': digest}
        return self._operation(verified)

    def page(self, start=0, limit=64):
        def selected():
            total = self._root['row_count']
            _need(type(start) is int and 0 <= start <= total and type(limit) is int and 1 <= limit <= LIMITS['page_records'])
            stop = min(start + limit, total);rows = []
            for descriptor in self._root['pages']:
                left = descriptor['start'];right = left + descriptor['count']
                if right <= start:continue
                if left >= stop:break
                values = _blob(self._fd, descriptor['sha256'], LIMITS['page_bytes'])
                _need(type(values) is list and len(values) == descriptor['count'])
                rows.extend(values[max(start-left, 0):min(stop-left, len(values))])
            value = {'start': start, 'next': stop, 'total': total, 'records': rows}
            _need(len(rows) == stop - start and len(_canonical(value)) <= LIMITS['page_bytes'])
            return value
        return self._operation(selected)


def open_harvest_artifact(directory, expected_artifact_sha256, query, tenant, result_id, farm_ref):
    try:
        _need(type(query) is current.CalculationCurrentCycleQuery)
        return _Reader(directory, expected_artifact_sha256, lambda **kwargs: query.read(tenant, result_id, farm_ref, **kwargs))
    except PermissionError:raise
    except Exception:raise HarvestArtifactHold('harvest research artifact unavailable') from None
