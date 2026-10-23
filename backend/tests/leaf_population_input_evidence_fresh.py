"""Separate-process, instrumented source evidence probe over the original owned fixture."""
from hashlib import sha256
import builtins
import importlib.abc
import io
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.job_store import JobStore
from app.crop_morphology_artifact_io import MorphologyBlobStore
import psycopg

FORBIDDEN = {'app.'+name for name in ('crop_leaf_expansion','crop_leaf_area_change','crop_leaf_area',
    'crop_rational_leaf_area','crop_leaf_inventory','crop_declared_leaf_births','crop_leaf_population',
    'crop_leaf_stem_binding','crop_leaf_population_artifact_producer','crop_leaf_artifact_producer',
    'crop_internode_elongation','crop_internode_length','crop_internode_length_change',
    'crop_morphology_thermal_clock','crop_rational_morphology_clock','crop_rational_internode_length',
    'crop_rational_new_internodes','crop_rational_shoot_inventory','crop_shoot_inventory',
    'crop_shoot_timeline','crop_phytomer_emergence')}
assert not FORBIDDEN.intersection(sys.modules)
imports = []
class NoGrowth(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in FORBIDDEN:
            imports.append(fullname)
            raise AssertionError('growth import in structural source verification')
sys.meta_path.insert(0, NoGrowth())
calls = {k:0 for k in ('JobStore.connect','psycopg.connect','subprocess.run','subprocess.Popen',
    'artifact.put','content_write','os.write_open','builtins.write_open','io.write_open')}
def forbidden(name):
    def fail(*args, **kwargs):
        calls[name] += 1
        raise AssertionError('source evidence crossed a readonly boundary')
    return fail
JobStore.connect = forbidden('JobStore.connect'); psycopg.connect = forbidden('psycopg.connect')
subprocess.run = forbidden('subprocess.run'); subprocess.Popen = forbidden('subprocess.Popen')
MorphologyBlobStore.put = forbidden('artifact.put'); JobStore._durable_content = forbidden('content_write')
original_os_open = os.open
def readonly_os_open(path, flags, *args, **kwargs):
    if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
        return forbidden('os.write_open')()
    return original_os_open(path, flags, *args, **kwargs)
os.open = readonly_os_open
def readonly_open(original, name):
    def open_file(file, mode='r', *args, **kwargs):
        if any(flag in mode for flag in 'wax+'):
            return forbidden(name)()
        return original(file, mode, *args, **kwargs)
    return open_file
builtins.open = readonly_open(builtins.open, 'builtins.write_open')
io.open = readonly_open(io.open, 'io.write_open')

configuration = json.loads(Path(sys.argv[1]).read_bytes())
directory = Path(configuration['population_directory'])
def snapshot():
    result = {}
    for file in directory.iterdir():
        stat = file.stat()
        result[file.name] = [stat.st_dev,stat.st_ino,stat.st_uid,stat.st_gid,stat.st_mode,stat.st_nlink,
            stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,sha256(file.read_bytes()).hexdigest()]
    return result
before = snapshot(); fd_before = len(os.listdir('/proc/self/fd'))
from app import crop_leaf_population_input_evidence as model
from test_crop_leaf_population_input_evidence import ROOT, source_for, review, configured
raw = (ROOT/'fixtures/crop-leaf-population-software-program-v1.json').read_bytes()
raw, source = source_for(raw); current = review(source)
server, arguments = configured(model, raw, source, leaf_resolver=lambda _: dict(current))
evidence = server.issue(**arguments); result = server.verify(evidence_raw=evidence, **arguments)
assert result.program_sha256 == sha256(raw).hexdigest()
assert not result.metadata['stem_artifact_root_verified'] and not result.rights_or_gate_approval
current['status'] = 'revoked'
try:
    server.verify(evidence_raw=evidence, **arguments)
except model.LeafPopulationInputEvidenceHold:
    pass
else:
    raise AssertionError('revoked source remained visible')
fd_after = len(os.listdir('/proc/self/fd'))
assert fd_before == fd_after and before == snapshot() and not any(calls.values()) and not imports
assert not FORBIDDEN.intersection(sys.modules)
print(json.dumps({'program_sha256':result.program_sha256,'source_sha256':result.source_sha256,
    'evidence_sha256':result.evidence_sha256,'metadata_sha256':sha256(result._metadata_raw).hexdigest(),
    'variable_count':result.metadata['variable_count'],'parent_program_sha256':result.metadata['parent_stem_program_sha256'],
    'stem_artifact_root_verified':False,'rights_or_gate_approval':False,'revocation_held':True,
    'growth_import_attempts':imports,'calls':calls,'FD_before_after':[fd_before,fd_after],
    'original_blob_metadata_and_bytes_preserved':len(before),'actual_farm_Runs':0,'G0_G4':'not_assessed'}))
