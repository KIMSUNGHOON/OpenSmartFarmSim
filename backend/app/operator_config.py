"""Protected operator files for the existing authenticated HTTPS assembly."""

import importlib
import json
import os
from pathlib import Path
import re
import stat

from .api_runtime import ApiRuntime, ApiRuntimeConfig, ApiRuntimeDependencies
from .content_access import ContentAccess
from .job_store import _open_directory_nofollow
from .runtime_roles import RuntimeLoginPolicy


FIELDS = frozenset({'config_version', 'policy', 'dsn_file', 'artifact_root', 'certificate',
    'private_key', 'thermal_gate_key_file', 'market_hold_key_file', 'authored_run_gate_key_file',
    'content_access', 'host', 'port', 'dependencies_factory'})
POLICY_FIELDS = frozenset({'schema', 'owner', 'prefix', 'database', 'connection_limit',
    'market_calculation', 'break_even_calculation', 'market_source_storage',
    'thermal_scenario_storage', 'authored_release_storage', 'authored_run_storage'})
OPTIONAL_POLICY_FIELDS = frozenset({'crop_result_storage', 'crop_coupled_result_storage'})


class OperatorConfigHold(ValueError):
    """A fixed operator error that contains no private configuration details."""


def _path(value):
    if not isinstance(value, (str, Path)):
        raise ValueError
    path = Path(value)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError
    return path


def _no_acl(descriptor):
    if {'system.posix_acl_access', 'system.posix_acl_default'} & set(os.listxattr(descriptor)):
        raise ValueError


def _metadata(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _private_bytes(raw_path, *, maximum, minimum=1, certificate=False):
    path = _path(raw_path)
    parent = _open_directory_nofollow(path.parent)
    descriptor = None
    try:
        info = os.fstat(parent)
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError
        _no_acl(parent)
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                             dir_fd=parent)
        before = os.fstat(descriptor)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.geteuid() or before.st_nlink != 1 or
                stat.S_IMODE(before.st_mode) not in ({0o600, 0o644} if certificate else {0o600}) or
                not minimum <= before.st_size <= maximum):
            raise ValueError
        _no_acl(descriptor)
        raw = os.read(descriptor, maximum + 1)
        after = os.fstat(descriptor)
        _no_acl(descriptor)
        if len(raw) != before.st_size or _metadata(before) != _metadata(after):
            raise ValueError
        return raw
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent)


def _object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError
        result[name] = value
    return result


def _constant(_value):
    raise ValueError


def load_api_runtime(config_path):
    try:
        raw = _private_bytes(config_path, maximum=65536)
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        if (type(value) is not dict or value.keys() != FIELDS or
                value['config_version'] != 'operator-api-config-v1' or
                type(value['policy']) is not dict or
                not POLICY_FIELDS <= value['policy'].keys() <= POLICY_FIELDS | OPTIONAL_POLICY_FIELDS):
            raise ValueError
        reference = value['dependencies_factory']
        if type(reference) is not str or not re.fullmatch(
                r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*', reference, flags=re.ASCII):
            raise ValueError
        access = value['content_access']
        if access is not None:
            if type(access) is not dict or access.keys() != {'owner_uid', 'reader_gid'}:
                raise ValueError
            access = ContentAccess(**access)
        certificate, private_key = _path(value['certificate']), _path(value['private_key'])
        _private_bytes(certificate, maximum=65536, certificate=True)
        _private_bytes(private_key, maximum=65536)
        authored = value['authored_run_gate_key_file']
        config = ApiRuntimeConfig(policy=RuntimeLoginPolicy(**value['policy']),
            dsn=_private_bytes(value['dsn_file'], maximum=8192).decode('utf-8').strip(),
            artifact_root=_path(value['artifact_root']), certificate=certificate, private_key=private_key,
            thermal_gate_key=_private_bytes(value['thermal_gate_key_file'], minimum=32, maximum=4096),
            market_hold_key=_private_bytes(value['market_hold_key_file'], minimum=32, maximum=4096),
            authored_run_gate_key=None if authored is None else _private_bytes(authored, minimum=32, maximum=4096),
            content_access=access, host=value['host'], port=value['port'])
        module, attribute = reference.split(':')
        factory = getattr(importlib.import_module(module), attribute)
        dependencies = factory(config=config)
        if type(dependencies) is not ApiRuntimeDependencies:
            raise ValueError
        return ApiRuntime(config, dependencies)
    except (Exception, SystemExit):
        raise OperatorConfigHold('operator_config_rejected') from None


def api_service():
    try:
        return load_api_runtime(_path(os.environ['OSSF_API_CONFIG'])).service
    except (Exception, SystemExit):
        raise OperatorConfigHold('operator_config_rejected') from None
