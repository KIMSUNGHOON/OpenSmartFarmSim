"""Main-thread signal stop with interruptible waits and owned descriptor cleanup."""

from contextlib import contextmanager
import os
import select
import signal
from threading import Event
import time


class SignalStop(Event):
    def __init__(self):
        super().__init__()
        self.requested = False
        self.reader, self.writer = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)

    def set(self):
        self.requested = True

    def is_set(self):
        return self.requested

    def wait(self, seconds):
        deadline = time.monotonic() + seconds
        while not self.requested:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            if select.select([self.reader], [], [], remaining)[0]:
                os.read(self.reader, 4096)
        return self.requested

    def close(self):
        os.close(self.reader)
        os.close(self.writer)


@contextmanager
def process_stop():
    stop = SignalStop()
    previous, handlers = None, {}
    try:
        previous = signal.set_wakeup_fd(stop.writer, warn_on_full_buffer=False)
        for sig in (signal.SIGTERM, signal.SIGINT):
            handlers[sig] = signal.signal(sig, lambda *_: stop.set())
        yield stop
    finally:
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
        if previous is not None:
            signal.set_wakeup_fd(previous)
        stop.close()
