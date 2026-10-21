from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.content_access import ContentAccess
from app.crop_leaf_artifact_reader import read_leaf_area_frame
from app.crop_morphology_artifact_reader import _canonical
from app.crop_morphology_artifact_io import MorphologyBlobStore
from app.job_store import JobStore
import psycopg

calls={'JobStore.connect':0,'psycopg.connect':0,'subprocess.run':0,'subprocess.Popen':0,
       'artifact.put':0,'content_write':0,'write_open':0}
def forbidden(name):
    def fail(*a,**kw):calls[name]+=1;raise AssertionError('read-only boundary crossed')
    return fail
JobStore.connect=forbidden('JobStore.connect');psycopg.connect=forbidden('psycopg.connect')
subprocess.run=forbidden('subprocess.run');subprocess.Popen=forbidden('subprocess.Popen')
MorphologyBlobStore.put=forbidden('artifact.put');JobStore._durable_content=forbidden('content_write')
original_open=os.open
def readonly_open(path,flags,*a,**kw):
    if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
        calls['write_open']+=1;raise AssertionError('write open in reader')
    return original_open(path,flags,*a,**kw)
os.open=readonly_open
p=json.loads(Path(sys.argv[1]).read_bytes());access=ContentAccess(os.getuid(),os.getgid())
def snapshot():
    result={}
    for f in Path(p['directory']).iterdir():
        s=f.stat();result[f.name]=[s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,sha256(f.read_bytes()).hexdigest()]
    return result
before=snapshot()
for i,digest in enumerate(p['expected']):
    value=read_leaf_area_frame(Path(p['directory']),access,p['root'],index=i)
    assert sha256(_canonical(value)).hexdigest()==digest
growth=[name for name in sys.modules if name.startswith('app.crop_') and any(token in name for token in (
    'leaf_expansion','leaf_area_change','leaf_area','leaf_inventory','internode_elongation','internode_length',
    'morphology_thermal_clock','rational_morphology_clock','rational_internode','shoot_inventory','shoot_timeline','phytomer_emergence'))
    and 'artifact' not in name]
assert not growth
assert before==snapshot()
print(json.dumps({'frames':len(p['expected']),'growth_imports':growth,'calls':calls,'original_blob_metadata_and_bytes_preserved':len(before)}))
