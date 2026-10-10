from pathlib import Path
from hashlib import sha256
import argparse,json,os,ssl,urllib.request,urllib.error
from urllib.parse import urlencode
parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,required=True)
B=parser.parse_args().directory;c=json.loads((B/'task.private.json').read_bytes());directory=Path(c['service_directory']);run=directory/c['active_run'];phase=c['probe_phase']
a=json.loads((run/'access.private.json').read_bytes());r=json.loads((run/'ready.private.json').read_bytes());context=ssl.create_default_context(cafile=str(run/'cert.pem'));records={}
for mode in ('completed','hold','cancel'):
 old=json.loads((B/('browser-'+mode+'-v1')/'evidence/browser-result.private.json').read_bytes());job=old['job_id']
 observation=next(o for o in reversed(old['observations']) if o['path'].endswith('/crop-climate-joint-execution') and o.get('status')==200)
 path=observation['path']+observation['query']
 paths=[('progress',path)]
 if mode!='cancel':paths += [(o['wire_file'],o['path']+o['query']) for o in old['observations'] if 'research-results' in o['path']]
 values={}
 for key,path in paths:
  req=urllib.request.Request(r['backend']+path,headers={'Authorization':'Bearer '+a['token']})
  with urllib.request.urlopen(req,context=context,timeout=30) as response:
   assert response.status==200 and response.headers.get('Cache-Control')=='no-store';raw=response.read()
  value=json.loads(raw)
  values[key]={'sha256':sha256(raw).hexdigest(),'value':value}
 if phase=='after':
  before=json.loads((B/'before-restart.private.json').read_bytes())['jobs'][mode]
  for key,v in values.items():
   if key=='progress':
    oldvalue=dict(before[key]['value']);newvalue=dict(v['value']);oldvalue.pop('observed_at');newvalue.pop('observed_at');assert oldvalue==newvalue
   else:assert v['sha256']==before[key]['sha256']
 records[mode]=values
immutable={}
for name in ('inputs', 'seed/custody'):
 for p in (directory/name).rglob('*'):
  if p.is_file():immutable[str(p.relative_to(directory))]=sha256(p.read_bytes()).hexdigest()
if phase=='after':
 before=json.loads((B/'before-restart.private.json').read_bytes());assert immutable==before['immutable_files']
 old_access=json.loads((directory/'serve-v3/access.private.json').read_bytes())
 assert old_access['token']!=a['token']
 try:urllib.request.urlopen(urllib.request.Request(r['backend']+path,headers={'Authorization':'Bearer '+old_access['token']}),context=context,timeout=10)
 except urllib.error.HTTPError as error:assert error.code==401
 else:raise AssertionError('old session token was accepted')
 assert (run/'worker.private.log').read_text().splitlines()==['{"event":"started","version":1}']
value={'jobs':records,'immutable_files':immutable,'actual_TLS':True,'old_token_401':phase=='after','new_worker_attempts':0 if phase=='after' else None}
p=B/(phase+'-restart.private.json')
with p.open('x') as f:os.fchmod(f.fileno(),0o400);json.dump(value,f,sort_keys=True);f.flush();os.fsync(f.fileno())
print(json.dumps({'phase':phase,'jobs':len(records),'immutable_files':len(immutable),'same_old_results':phase=='after','old_token_401':phase=='after'}))
