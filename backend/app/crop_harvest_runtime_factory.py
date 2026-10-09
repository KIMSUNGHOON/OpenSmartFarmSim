"""Explicit private configuration for the existing harvest reader dependency."""
from hashlib import sha256
import json
import os
from pathlib import Path

from psycopg.conninfo import conninfo_to_dict

from . import operator_config as private

VERSION = 'crop-harvest-reader-config-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
FIELDS = frozenset({'config_version','policy','directory','reader_dsn_file','integrity_key_file'})
_DECLARATIONS = VERSION, CODE_SHA256, FIELDS


class HarvestRuntimeConfigHold(ValueError):
    """No safe explicitly configured harvest reader factory."""


def load_harvest_current_query_factory(config_path):
    try:
        path = private._path(config_path)
        raw = private._private_bytes(path, maximum=65536)
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=private._object, parse_constant=private._constant)
        if type(value) is not dict or set(value) != FIELDS or value['config_version'] != VERSION:
            raise ValueError()
        from . import crop_harvest_current_query as current
        registry = current.registry
        if type(value['policy']) is not dict or set(value['policy']) != {'schema','owner','publisher','reader','database'}:
            raise ValueError()
        policy = registry.schema.HarvestRegistryPolicy(**value['policy'])
        directory = private._path(value['directory'])
        dsn_path = private._path(value['reader_dsn_file']); key_path = private._path(value['integrity_key_file'])
        dsn_raw = private._private_bytes(dsn_path, maximum=8192)
        key = private._private_bytes(key_path, minimum=32, maximum=4096)
        dsn = dsn_raw.decode('utf-8').strip(); params = conninfo_to_dict(dsn)
        if (params.get('user') != policy.reader or params.get('dbname') != policy.database or
                not params.get('host') or params['host'].startswith('/') or 'password' in params or
                not params.get('passfile')):
            raise ValueError()
        passfile = private._path(params['passfile']); password_raw = private._private_bytes(passfile, maximum=8192)
        if len({path,dsn_path,key_path,passfile}) != 4:
            raise ValueError()
        def root_identity():
            fd = registry.files._open_directory_nofollow(directory)
            try:
                info = registry.files._secure(fd, directory=True)
                return info.st_dev, info.st_ino
            finally:
                os.close(fd)
        identity = root_identity()
        captured = ((path,raw,1,65536),(dsn_path,dsn_raw,1,8192),
                    (key_path,key,32,4096),(passfile,password_raw,1,8192))
        def check():
            if ((VERSION,CODE_SHA256,FIELDS) != _DECLARATIONS or
                    sha256(Path(__file__).read_bytes()).hexdigest() != CODE_SHA256 or root_identity() != identity):
                raise ValueError()
            current._pins()
            for file,expected,minimum,maximum in captured:
                if private._private_bytes(file, minimum=minimum, maximum=maximum) != expected:
                    raise ValueError()
        def factory(*, calculation_current_query):
            try:
                check()
                reader = registry.HarvestRegistry(calculation_current_query, policy, directory,
                    dsn=dsn, integrity_key=key)
                result = current.HarvestCurrentQuery(reader)
                check()
                return result
            except (Exception,SystemExit):
                raise HarvestRuntimeConfigHold('harvest_reader_config_rejected') from None
        check()
        factory.version = VERSION
        factory.config_sha256 = sha256(raw).hexdigest()
        return factory
    except (Exception,SystemExit):
        raise HarvestRuntimeConfigHold('harvest_reader_config_rejected') from None
