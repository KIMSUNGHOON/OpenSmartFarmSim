"""Independent OS lock semantics for the existing secure file helper."""
import os
import subprocess
import sys
import pytest
from app import crop_cycle_server_custody as files

LOCK_PROBE = '''
import fcntl,os,sys
fd=os.open(sys.argv[1],os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
try:
 try:fcntl.flock(fd,(fcntl.LOCK_SH if sys.argv[2]=='shared' else fcntl.LOCK_EX)|fcntl.LOCK_NB)
 except BlockingIOError:sys.exit(2)
finally:os.close(fd)
'''


def probe(path, mode):
    result = subprocess.run([sys.executable, '-B', '-c', LOCK_PROBE, str(path), mode],
        stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
    assert result.returncode in (0, 2)
    return result.returncode


def test_default_exclusive_and_shared_locks_use_independent_open_descriptions(tmp_path):
    root = os.open(tmp_path, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    first = second = None
    try:
        first = files._file(root, 'mutex', lock=True)
        assert probe(tmp_path/'mutex', 'shared') == probe(tmp_path/'mutex', 'exclusive') == 2
        os.close(first);first = None
        first = files._file(root, 'mutex', lock=True, shared=True)
        second = files._file(root, 'mutex', lock=True, shared=True)
        assert probe(tmp_path/'mutex', 'shared') == 0
        assert probe(tmp_path/'mutex', 'exclusive') == 2
        os.close(first);first = None
        assert probe(tmp_path/'mutex', 'exclusive') == 2
        os.close(second);second = None
        assert probe(tmp_path/'mutex', 'exclusive') == 0
    finally:
        if first is not None: os.close(first)
        if second is not None: os.close(second)
        os.close(root)


def test_shared_file_mode_never_creates_a_missing_file(tmp_path):
    root = os.open(tmp_path, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        with pytest.raises(FileNotFoundError): files._file(root, 'missing', lock=True, shared=True)
        with pytest.raises(ValueError): files._file(root, 'missing', shared=True)
        assert not list(tmp_path.iterdir())
    finally: os.close(root)


