"""Foreground loopback HTTPS transport for an operator-assembled authenticated API."""

from contextlib import ExitStack
from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
import ssl
import stat

from fastapi import FastAPI
import uvicorn

from .http_identity import PrincipalMiddleware


class _ServiceFormatter(logging.Formatter):
    def format(self, _record):
        return '{"version":1,"ok":false,"code":"api_transport_event"}'


def _tls_context(certificate, private_key):
    try:
        with ExitStack() as stack:
            descriptors = []
            for raw, secret in ((certificate, False), (private_key, True)):
                path = Path(raw)
                if not path.is_absolute() or ".." in path.parts:
                    raise ValueError()
                parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
                stack.callback(os.close, parent)
                info = os.fstat(parent)
                if info.st_uid != os.getuid() or info.st_mode & 0o077:
                    raise ValueError()
                descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                                     dir_fd=parent)
                stack.callback(os.close, descriptor)
                info = os.fstat(descriptor)
                if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                        not 0 < info.st_size <= 65536 or info.st_mode & (0o077 if secret else 0o022)):
                    raise ValueError()
                descriptors.append(f"/proc/self/fd/{descriptor}")
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(*descriptors, password=lambda: b"")
            return context
    except Exception:
        raise ValueError("API TLS configuration rejected") from None


@dataclass(frozen=True, init=False)
class HttpsApiService:
    app: PrincipalMiddleware = field(repr=False)
    _tls: ssl.SSLContext = field(repr=False)
    host: str
    port: int

    def __init__(self, app, certificate, private_key, *, host="127.0.0.1", port=8443):
        if (type(app) is not PrincipalMiddleware or type(app.app) is not FastAPI or
                type(host) is not str or host not in ("127.0.0.1", "::1") or
                type(port) is not int or not 0 <= port <= 65535):
            raise ValueError("API service configuration rejected")
        context = _tls_context(certificate, private_key)
        for name, value in (("app", app), ("_tls", context), ("host", host), ("port", port)):
            object.__setattr__(self, name, value)

    def server(self):
        logging_config = {"version": 1, "disable_existing_loggers": False,
            "formatters": {"bounded": {"()": _ServiceFormatter}},
            "handlers": {"bounded": {"class": "logging.StreamHandler", "formatter": "bounded",
                                      "stream": "ext://sys.stderr"}},
            "loggers": {"uvicorn": {"handlers": ["bounded"], "level": "WARNING", "propagate": False},
                        "uvicorn.error": {"handlers": [], "level": "WARNING", "propagate": True},
                        "uvicorn.access": {"handlers": [], "propagate": False}}}
        config = uvicorn.Config(self.app, host=self.host, port=self.port,
            loop="asyncio", http="h11", ws="none", interface="asgi3", lifespan="on",
            workers=1, reload=False, proxy_headers=False, forwarded_allow_ips="",
            access_log=False, server_header=False, log_config=logging_config,
            ssl_context_factory=lambda _config, _default: self._tls,
            limit_concurrency=64, backlog=128, h11_max_incomplete_event_size=8192,
            timeout_keep_alive=5, timeout_graceful_shutdown=10, limit_max_requests=10000,
            reset_contextvars=True)
        return uvicorn.Server(config)

    def serve(self):
        self.server().run()
