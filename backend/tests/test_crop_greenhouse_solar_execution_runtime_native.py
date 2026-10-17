"""Sequential preparation and actual configured Solar API assembly over TLS."""
import ast

import test_crop_greenhouse_solar_runtime_native as saved


def native_script():
    assembly=saved.ASSEMBLE
    needle='market_hold_key=HOLD_KEY,port=0)'
    assert assembly.count(needle)==1
    assembly=assembly.replace(needle, 'market_hold_key=HOLD_KEY,port=0,\n crop_greenhouse_solar_execution=True,crop_greenhouse_solar_prefix=True)')
    needle="document={'config_version':loader.VERSION,'policy':asdict(policy),"
    assert assembly.count(needle)==1
    assembly=assembly.replace(needle,"document={'config_version':loader.PREFIX_VERSION,loader.EXECUTION_FLAG:True,loader.PREFIX_FLAG:True,'policy':asdict(policy),")
    needle='assert runtime.ventilation_crop_results is runtime.joint_crop_results is None'
    assert assembly.count(needle)==1
    assembly=assembly.replace(needle,needle+'''
from app import crop_greenhouse_solar_execution_query as execution_current
from app.crop_greenhouse_solar_prefix import SolarExecutionPrefixQuery
assert type(runtime.solar_execution_admission) is execution_current.checkpoints.execution.SolarExecutionService
assert type(runtime.solar_execution_checkpoints) is execution_current.checkpoints.SolarExecutionCheckpointStore
assert type(runtime.solar_execution_query) is execution_current.SolarExecutionQuery
assert type(runtime.solar_prefix_query) is SolarExecutionPrefixQuery
assert runtime.solar_execution_admission.jobs is runtime.jobs
assert runtime.solar_execution_admission.binding is runtime.solar_crop_results.server.binding
assert runtime.solar_execution_admission.input_resolver is runtime.solar_crop_results.server.input_resolver
assert runtime.solar_execution_checkpoints.admission is runtime.solar_execution_admission
assert runtime.solar_execution_checkpoints.server is runtime.solar_crop_results.server
assert runtime.solar_execution_query.checkpoints is runtime.solar_execution_checkpoints
assert runtime.solar_execution_query.results is runtime.solar_crop_results
assert runtime.solar_prefix_query.query is runtime.solar_execution_query
paths={route.path for route in runtime.service.app.app.routes if hasattr(route,'path')}
assert '/v1/crop-greenhouse-solar-executions' in paths
assert all('/v1/jobs/{job_id}/crop-greenhouse-solar-execution/prefix'+suffix in paths for suffix in ('','/samples','/events'))
''')
    previous=saved.ASSEMBLE
    try:
        saved.ASSEMBLE=assembly
        script=saved.native_script()
    finally:
        saved.ASSEMBLE=previous
    script=script.replace("'runtime_assembled':True", "'runtime_assembled':True,'solar_execution_and_prefix_assembled':True")
    ast.parse(script)
    return script


def exercise(tmp_path,case):
    previous=saved.base.HTTP_READ
    preparation=saved.base.PREPARE
    needle='script.write_text(t.FRESH_SCRIPT)'
    assert preparation.count(needle)==1
    try:
        saved.base.PREPARE=preparation.replace(needle,
            "script.write_text(t.FRESH_SCRIPT.replace('original(conn)', 'original(conn);__import__(\"ctypes\").CDLL(None).malloc_trim(0)'))")
        saved.base.HTTP_READ=native_script()
        saved.base.exercise(tmp_path,case)
    finally:
        saved.base.HTTP_READ=previous
        saved.base.PREPARE=preparation


def test_owned_execution_runtime_completed_original_TLS(tmp_path):
    exercise(tmp_path,None)


def test_owned_execution_runtime_hold_original_TLS(tmp_path):
    exercise(tmp_path,'hold')
