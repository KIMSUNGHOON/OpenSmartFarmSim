"""Explicit protected configuration for current ventilation result reads."""
import json
import os
import re

from . import operator_config as original

VERSION = 'operator-greenhouse-ventilation-api-config-v1'
EXECUTION_VERSION = 'operator-greenhouse-ventilation-execution-api-config-v1'
EXECUTION_FLAG = 'crop_greenhouse_ventilation_execution'
PREFIX_VERSION = 'operator-greenhouse-ventilation-prefix-api-config-v1'
PREFIX_FLAG = 'crop_greenhouse_ventilation_prefix'
MIXED_PREFIX_VERSION = 'operator-joint-ventilation-prefix-api-config-v1'
JOINT_EXECUTION_FLAG = 'crop_climate_joint_execution'
JOINT_PREFIX_FLAG = 'crop_climate_joint_prefix'
FLAG = original.VENTILATION_RESULT_FLAG
CALCULATION_FLAG = 'crop_cycle_calculation_result_storage'
POLICY_FIELDS = original.POLICY_FIELDS | {FLAG}


def load_ventilation_api_runtime(config_path):
    try:
        files = []

        def read(path, **options):
            raw = original._private_bytes(path, **options)
            files.append((path, options, raw))
            return raw

        def unchanged():
            for path, options, raw in files:
                if original._private_bytes(path, **options) != raw:
                    raise ValueError

        raw = read(config_path, maximum=65536)
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=original._object,
                           parse_constant=original._constant)
        if type(value) is not dict:
            raise ValueError
        mixed_version = value.get('config_version') == MIXED_PREFIX_VERSION
        prefix_version = value.get('config_version') in (PREFIX_VERSION, MIXED_PREFIX_VERSION)
        execution_version = value.get('config_version') in (EXECUTION_VERSION, PREFIX_VERSION, MIXED_PREFIX_VERSION)
        expected = (original.FIELDS | ({EXECUTION_FLAG} if execution_version else set()) |
                    ({PREFIX_FLAG} if prefix_version else set()) |
                    ({JOINT_EXECUTION_FLAG, JOINT_PREFIX_FLAG} if mixed_version else set()))
        required_policy = POLICY_FIELDS | ({original.JOINT_RESULT_FLAG} if mixed_version else set())
        if (value.keys() != expected or value['config_version'] not in (VERSION, EXECUTION_VERSION, PREFIX_VERSION, MIXED_PREFIX_VERSION) or
                type(value['policy']) is not dict or
                not required_policy <= value['policy'].keys() <=
                POLICY_FIELDS | original.OPTIONAL_POLICY_FIELDS | {CALCULATION_FLAG}):
            raise ValueError
        policy = value['policy']
        execution = value[EXECUTION_FLAG] if execution_version else False
        prefix = value[PREFIX_FLAG] if prefix_version else False
        joint_execution = value[JOINT_EXECUTION_FLAG] if mixed_version else False
        joint_prefix = value[JOINT_PREFIX_FLAG] if mixed_version else False
        flags = (FLAG, original.JOINT_RESULT_FLAG, CALCULATION_FLAG)
        if (policy.get(original.CO2_RESULT_FLAG, False) is not False or
                policy.get(original.SOLAR_RESULT_FLAG, False) is not False or
                type(execution) is not bool or type(prefix) is not bool or (prefix and not execution) or
                (execution and policy[FLAG] is not True) or
                type(joint_execution) is not bool or type(joint_prefix) is not bool or
                (joint_prefix and not joint_execution) or
                (joint_execution and policy[original.JOINT_RESULT_FLAG] is not True) or
                any(type(policy.get(flag, False)) is not bool for flag in flags) or
                (any(policy.get(flag, False) for flag in flags) and
                 policy.get('crop_cycle_result_storage') is not True)):
            raise ValueError
        reference = value['dependencies_factory']
        if type(reference) is not str or not re.fullmatch(
                r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*', reference, flags=re.ASCII):
            raise ValueError
        access = value['content_access']
        if access is not None:
            if type(access) is not dict or access.keys() != {'owner_uid', 'reader_gid'}:
                raise ValueError
            access = original.ContentAccess(**access)
        certificate = original._path(value['certificate'])
        private_key = original._path(value['private_key'])
        read(certificate, maximum=65536, certificate=True)
        read(private_key, maximum=65536)
        authored = value['authored_run_gate_key_file']
        config = original.ApiRuntimeConfig(
            policy=original.RuntimeLoginPolicy(**policy),
            dsn=read(value['dsn_file'], maximum=8192).decode('utf-8').strip(),
            artifact_root=original._path(value['artifact_root']),
            certificate=certificate, private_key=private_key,
            thermal_gate_key=read(value['thermal_gate_key_file'], minimum=32, maximum=4096),
            market_hold_key=read(value['market_hold_key_file'], minimum=32, maximum=4096),
            authored_run_gate_key=None if authored is None else read(authored, minimum=32, maximum=4096),
            content_access=access, host=value['host'], port=value['port'],
            crop_climate_joint_execution=joint_execution,
            crop_climate_joint_prefix=joint_prefix,
            crop_greenhouse_ventilation_execution=execution,
            crop_greenhouse_ventilation_prefix=prefix)
        module, attribute = reference.split(':')
        factory = getattr(original.importlib.import_module(module), attribute)
        dependencies = factory(config=config)
        if type(dependencies) is not original.ApiRuntimeDependencies:
            raise ValueError
        unchanged()
        runtime = original.ApiRuntime(config, dependencies)
        unchanged()
        return runtime
    except (Exception, SystemExit):
        raise original.OperatorConfigHold('operator_config_rejected') from None


def api_service():
    try:
        return load_ventilation_api_runtime(original._path(os.environ['OSSF_API_CONFIG'])).service
    except (Exception, SystemExit):
        raise original.OperatorConfigHold('operator_config_rejected') from None
