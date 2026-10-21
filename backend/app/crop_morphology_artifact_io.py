"""Private morphology research blobs using the existing JobStore POSIX writer.

File transport only; no database, tenant authorization or farm Run custody.
"""
import fcntl
from hashlib import sha256
import os
from pathlib import Path
import re

from .content_access import ContentAccess
from .job_store import JobStore


MAX_BLOB_BYTES = 16 * 1024**2
MAX_DIRECTORY_BYTES = 64 * 1024**2
MAX_FILES = 4096
DIGEST = re.compile(r'[0-9a-f]{64}\Z')


class MorphologyArtifactHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise MorphologyArtifactHold(reason)


def _maximum(maximum):
    _need(type(maximum) is int and 1 <= maximum <= MAX_BLOB_BYTES, 'CAPACITY_HOLD: explicit bounded blob size required')


def _metadata(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class MorphologyBlobStore:
    def __init__(self, directory, access, *, write=False):
        self._fd = None
        try:
            _need(type(access) is ContentAccess and type(write) is bool, 'STORAGE_HOLD: explicit file policy required')
            directory = Path(directory)
            _need(directory.is_absolute() and '..' not in directory.parts, 'STORAGE_HOLD: absolute artifact path required')
            self._access, self._write = access, write
            self._jobs = JobStore('not-used-for-morphology-files', 'morphology_research', directory, content_access=access)
            self._fd = self._jobs._content_directory(create=write)
            if write:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._guard()
        except (OSError, ValueError, TypeError):
            self.close()
            raise MorphologyArtifactHold('STORAGE_HOLD: owned artifact directory unavailable') from None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def _guard(self):
        _need(self._fd is not None, 'STORAGE_HOLD: artifact store closed')
        self._access.validate(self._fd, directory=True)
        current = self._jobs._content_directory()
        try:
            held, opened = os.fstat(self._fd), os.fstat(current)
            _need((held.st_dev, held.st_ino) == (opened.st_dev, opened.st_ino), 'STORAGE_HOLD: artifact directory replaced')
        finally:
            os.close(current)

    def _file_metadata(self, fd):
        self._access.validate(fd, directory=False)
        info = os.fstat(fd)
        _need(info.st_nlink == 1, 'STORAGE_HOLD: single-link blob required')
        return info

    def _usage(self):
        names = os.listdir(self._fd)
        _need(len(names) <= MAX_FILES, 'CAPACITY_HOLD: artifact file count')
        size = 0
        for name in names:
            _need(DIGEST.fullmatch(name), 'STORAGE_HOLD: unexpected artifact entry')
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=self._fd)
            try:
                size += self._file_metadata(fd).st_size
            finally:
                os.close(fd)
        _need(size <= MAX_DIRECTORY_BYTES, 'CAPACITY_HOLD: artifact directory bytes')
        return size, len(names)

    def get(self, digest, *, maximum):
        try:
            _maximum(maximum)
            _need(type(digest) is str and DIGEST.fullmatch(digest), 'HASH_HOLD: blob SHA-256 required')
            self._guard()
            fd = os.open(digest, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=self._fd)
            try:
                before = self._file_metadata(fd)
                _need(1 <= before.st_size <= maximum, 'CAPACITY_HOLD: bounded nonempty blob required')
                with os.fdopen(fd, 'rb', closefd=False) as handle:
                    raw = handle.read(maximum + 1)
                after = self._file_metadata(fd)
                _need(_metadata(before) == _metadata(after) and len(raw) == before.st_size
                      and sha256(raw).hexdigest() == digest, 'HASH_HOLD: original stable blob required')
            finally:
                os.close(fd)
            self._guard()
            return raw
        except MorphologyArtifactHold:
            raise
        except (OSError, ValueError, TypeError):
            raise MorphologyArtifactHold('STORAGE_HOLD: original blob unavailable') from None

    def put(self, raw, *, maximum):
        try:
            _maximum(maximum)
            _need(self._write and type(raw) is bytes and 1 <= len(raw) <= maximum,
                  'STORAGE_HOLD: bounded bytes and writer required')
            self._guard()
            digest = sha256(raw).hexdigest()
            try:
                os.stat(digest, dir_fd=self._fd, follow_symlinks=False)
            except FileNotFoundError:
                size, count = self._usage()
                _need(size + 2 * len(raw) <= MAX_DIRECTORY_BYTES and count + 2 <= MAX_FILES,
                      'CAPACITY_HOLD: artifact temporary-file budget')
                self._jobs._durable_content(raw, digest)
            _need(self.get(digest, maximum=maximum) == raw, 'HASH_HOLD: original immutable bytes required')
            return digest
        except MorphologyArtifactHold:
            raise
        except (OSError, ValueError, TypeError):
            raise MorphologyArtifactHold('STORAGE_HOLD: blob publication unavailable') from None
