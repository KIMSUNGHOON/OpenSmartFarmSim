from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.content_access import ContentAccess
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from app.thermal_run_store import _canonical
from test_crop_rational_morphology_artifact import program


SCRIPT = Path(__file__).resolve().parents[2] / 'research/export-rational-morphology-replay.py'


def exporter():
    spec = importlib.util.spec_from_file_location('morphology_exporter', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_requires_explicit_redistribution_and_creates_no_output_on_denial(tmp_path):
    p = program(); p['rights']['redistribute'] = False
    root = produce_rational_morphology_artifact(tmp_path/'artifact', ContentAccess(os.getuid(),os.getgid()), program_raw=_canonical(p))
    with pytest.raises(ValueError,match='RIGHTS_HOLD'):
        exporter().export(tmp_path/'artifact',root,tmp_path/'public')
    assert not (tmp_path/'public').exists()


def test_fresh_export_imports_no_growth_modules_or_DB_and_preserves_exact_bytes(tmp_path):
    root = produce_rational_morphology_artifact(tmp_path/'artifact', ContentAccess(os.getuid(),os.getgid()), program_raw=_canonical(program()))
    code = '''import importlib.util,json,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('exporter',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from app.job_store import JobStore
JobStore.connect=lambda *a,**k: (_ for _ in ()).throw(AssertionError('DB forbidden'))
names=['crop_rational_shoot_inventory','crop_rational_new_internodes','crop_rational_internode_length','crop_rational_morphology_clock','crop_shoot_inventory','crop_new_internodes','crop_shoot_timeline','crop_phytomer_emergence','crop_internode_length','crop_internode_length_change','crop_morphology_thermal_clock','crop_internode_elongation']
assert all('app.'+n not in sys.modules for n in names)
result=m.export(Path(sys.argv[2]),sys.argv[3],Path(sys.argv[4]))
assert all('app.'+n not in sys.modules for n in names)
print(json.dumps(result))
'''
    public=tmp_path/'public'
    done=subprocess.run([sys.executable,'-c',code,str(SCRIPT),str(tmp_path/'artifact'),root,str(public)],capture_output=True,text=True,timeout=10)
    assert done.returncode==0,done.stderr
    proof=json.loads(done.stdout);assert proof['frames']==3
    assert sha256((public/'root.json').read_bytes()).hexdigest()==root
    assert sha256((public/'index.json').read_bytes()).hexdigest()==proof['index_sha256']
    assert (public/'input.json').read_bytes()==_canonical(program())
    for descriptor in json.loads((public/'index.json').read_bytes())['frames']:
        raw=(public/descriptor['path']).read_bytes()
        assert len(raw)==descriptor['bytes'] and sha256(raw).hexdigest()==descriptor['sha256']
        value=json.loads(raw);assert value['at']==descriptor['at'] and value['result_sha256']==descriptor['result_sha256']


def test_export_does_not_merge_into_existing_public_directory(tmp_path):
    root=produce_rational_morphology_artifact(tmp_path/'artifact',ContentAccess(os.getuid(),os.getgid()),program_raw=_canonical(program()))
    public=tmp_path/'public';public.mkdir();(public/'index.json').write_bytes(b'original')
    with pytest.raises(FileExistsError):exporter().export(tmp_path/'artifact',root,public)
    assert list(public.iterdir())==[public/'index.json'] and (public/'index.json').read_bytes()==b'original'
