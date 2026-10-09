"""Linux ownership checks for local research test controllers."""
import os
from pathlib import Path
import signal
from typing import NamedTuple


class Identity(NamedTuple):
    pid: int
    start_ticks: int
    boot_id: str


def identity(pid):
    fields = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
    return Identity(pid, int(fields[19]), Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def live(expected):
    try:
        return identity(expected.pid) == expected and _fields(expected.pid)[0] != 'Z'
    except (FileNotFoundError, ProcessLookupError):
        return False


def _fields(pid):
    return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()


def _tree(root, excluded=()):
    found = {}
    pending = [(root.pid, None)]
    while pending:
        pid, parent = pending.pop()
        if pid in found:
            continue
        try:
            current = identity(pid)
            fields = _fields(pid)
            if current in excluded:
                continue
            if parent is None:
                if current != root:
                    continue
            elif int(fields[1]) != parent.pid or identity(parent.pid) != parent:
                continue
            children = set()
            for thread in Path('/proc', str(pid), 'task').iterdir():
                children.update(map(int, (thread / 'children').read_text().split()))
            if identity(pid) != current:
                continue
            found[pid] = (current, max(0, int(fields[21])) * os.sysconf('SC_PAGE_SIZE'))
            pending.extend((child, current) for child in children)
        except (FileNotFoundError, ProcessLookupError):
            continue
    return found


class OwnedProcessScope:
    def __init__(self, protected=()):
        if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
            raise RuntimeError('Linux pidfd support is required')
        self.controller = identity(os.getpid())
        self._protected = set(protected)
        if any(not isinstance(item, Identity) or not live(item) for item in self._protected):
            raise ValueError('live original protected identities are required')
        self._owned = set()
        self.sample()

    def _protection(self):
        records = {}
        for root in tuple(self._protected):
            records.update(_tree(root))
        self._protected.update(item for item, _ in records.values())
        if self.controller in self._protected:
            raise PermissionError('controller is inside a protected tree')
        return records

    def sample(self):
        protected = self._protection()
        owned = {}
        for root in (self.controller, *tuple(self._owned)):
            owned.update(_tree(root, excluded=self._protected))
        self._owned.update(item for item, _ in owned.values()
                           if item != self.controller and item not in self._protected)
        self._owned.difference_update(self._protected)
        observed = {**protected, **owned}
        return {pid: rss for pid, (_, rss) in observed.items()}

    def remaining(self):
        self.sample()
        return frozenset(item for item in self._owned if live(item))

    def signal_owned(self, signum):
        if signum not in (signal.SIGTERM, signal.SIGKILL):
            raise ValueError('only bounded TERM/KILL cleanup is supported')
        self.sample()
        sent = []
        for target in sorted(self._owned, reverse=True):
            self._protection()
            if target == self.controller or target in self._protected:
                raise PermissionError('protected process cleanup refused')
            if not live(target):
                continue
            fd = None
            try:
                fd = os.pidfd_open(target.pid)
                self._protection()
                if target in self._protected or not live(target):
                    continue
                signal.pidfd_send_signal(fd, signum)
                sent.append(target)
            except ProcessLookupError:
                pass
            finally:
                if fd is not None:
                    os.close(fd)
        return tuple(sent)
