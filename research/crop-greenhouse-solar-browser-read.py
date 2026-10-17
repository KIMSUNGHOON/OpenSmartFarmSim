"""Executed after the native current-query setup; never a standalone server or fixture fallback."""

import base64,importlib.util,http.server,mimetypes,shutil,subprocess,types,gc,ctypes
from urllib.parse import urlsplit,unquote,parse_qs
R=Path(os.environ['OSSF_SOLAR_BROWSER_SOURCE_ROOT']);web_build=Path(os.environ['OSSF_SOLAR_WEB_DIST'])
assert (web_build/'index.html').is_file()
asset_hashes={str(p.relative_to(web_build)):sha256(p.read_bytes()).hexdigest() for p in web_build.rglob('*') if p.is_file()}
assets={('/'+name):web_build/name for name in asset_hashes};assets['/']=web_build/'index.html'
actions=[];requests=[];frames=[];screens=[];proxy_errors=[];browser_exit=None;browser=None;pipe_fds=[];browser_scope=None
spki=base64.b64encode(sha256(key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)).digest()).decode()
upstream_context=ssl.create_default_context(cafile=str(cert))
thread=threading.Thread(target=server.run,daemon=True);thread.start()
deadline=time.monotonic()+10
while not server.started:assert thread.is_alive() and time.monotonic()<deadline;time.sleep(.01)
api_port=server.servers[0].sockets[0].getsockname()[1]
class Frontend(http.server.BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def log_message(self,*args):pass
 def do_GET(self):
  parsed=urlsplit(self.path)
  if parsed.path.startswith('/v1/'):
   assert parsed.path.startswith(PATH);assert len(requests)<64
   upstream=http.client.HTTPSConnection('127.0.0.1',api_port,context=upstream_context,timeout=45)
   try:
    upstream.request('GET',self.path,headers={'Authorization':self.headers.get('Authorization',''),'Accept':'application/json'})
    response=upstream.getresponse();wire=response.read(public.MAX_RESPONSE_BYTES+1);assert len(wire)<=public.MAX_RESPONSE_BYTES
    query_args=parse_qs(parsed.query);view=query_args.get('view',['summary'])[0]
    if response.status==200:assert wire==expected[view], 'proxy source body differs from immutable current response'
    record={'method':'GET','path':parsed.path,'query':parsed.query,'status':response.status,'bytes':len(wire),'wire_sha256':sha256(wire).hexdigest(),'view':view,'source_body_equal':response.status==200}
    requests.append(record)
    self.send_response(response.status)
    for name,value in response.getheaders():
     if name.lower() not in ('date','server','connection','transfer-encoding','content-length'):self.send_header(name,value)
    self.send_header('Content-Length',str(len(wire)));self.end_headers();self.wfile.write(wire)
   finally:upstream.close()
  else:
   asset=assets.get(unquote(parsed.path))
   if asset is None:
    self.send_response(204 if parsed.path=='/favicon.ico' else 404);self.send_header('Content-Length','0');self.end_headers();return
   wire=asset.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(asset.name)[0] or 'application/octet-stream');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(wire)));self.end_headers();self.wfile.write(wire)
 def do_POST(self):
  proxy_errors.append('unexpected_browser_write_attempt');self.send_response(405);self.send_header('Content-Length','0');self.end_headers()
web=http.server.ThreadingHTTPServer(('127.0.0.1',0),Frontend)
# The public static frontend forwards API bytes over independently verified TLS.
web_tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);web_tls.minimum_version=ssl.TLSVersion.TLSv1_2;web_tls.load_cert_chain(cert,private);web.socket=web_tls.wrap_socket(web.socket,server_side=True)
web_thread=threading.Thread(target=web.serve_forever,daemon=True);web_thread.start();origin='https://127.0.0.1:'+str(web.server_port)
for path in ('/','/assets/'):
 if path=='/assets/':continue
 connection=http.client.HTTPSConnection('127.0.0.1',web.server_port,context=upstream_context,timeout=10)
 try:connection.request('GET',path);r=connection.getresponse();assert r.status==200 and r.read()==assets[path].read_bytes()
 finally:connection.close()

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
pipe=module('solar_pipe',R/'research/crop-isolated-ventilation-pipe-reference.py');processes=module('solar_scope',R/'research/owned-research-process-scope.py')
profile=root/'solar-browser';profile.mkdir(mode=0o700);(profile/'chromium-profile').mkdir(mode=0o700)
context={'origin':origin,'directory':str(profile),'chromium':os.environ['OSSF_SOLAR_CHROMIUM'],'spki':spki}
context_file=profile/'context.private.json'
with context_file.open('x') as f:os.fchmod(f.fileno(),0o400);json.dump(context,f)
def save(name,value):
 with (Path(os.environ['OSSF_SOLAR_HTTP_EVIDENCE'])/name).open('x') as f:os.fchmod(f.fileno(),0o400);json.dump(value,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
def phase(name):
 target=Path(os.environ['OSSF_SOLAR_HTTP_EVIDENCE'])/'browser-phase.private.json';temporary=target.with_suffix('.tmp')
 with temporary.open('w') as f:os.fchmod(f.fileno(),0o400);json.dump({'stage':name,'API_RSS':int(next(v.split()[1] for v in Path('/proc/self/status').read_text().splitlines() if v.startswith('VmRSS:')))*1024},f)
 os.replace(temporary,target)
phase('before_browser');gc.collect();ctypes.CDLL(None).malloc_trim(0)
read_child,write_driver=os.pipe();read_driver,write_child=os.pipe();pipe_fds=[read_child,write_driver,read_driver,write_child]
error_file=(profile/'chromium.stderr.private.log').open('x');os.fchmod(error_file.fileno(),0o600)
try:
 browser_env={k:os.environ[k] for k in ('PATH','LANG','LD_LIBRARY_PATH','TMPDIR') if k in os.environ};browser_env['PYTHONDONTWRITEBYTECODE']='1';browser_env['XDG_CACHE_HOME']=str(profile/'cache');(profile/'cache').mkdir(mode=0o700)
 browser=owned_transport_Popen(['taskset','-c',str(min(os.sched_getaffinity(0))),'nice','-n','19',sys.executable,'-B',str(R/'research/crop-isolated-ventilation-pipe-reference.py'),'launch',str(read_child),str(write_child),str(context_file)],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=error_file,pass_fds=(read_child,write_child),env=browser_env)
 os.close(read_child);pipe_fds.remove(read_child);os.close(write_child);pipe_fds.remove(write_child)
 browser_scope=processes.OwnedProcessScope();browser_scope.sample()
 owner=types.SimpleNamespace(child=browser,evidence=types.SimpleNamespace(poll=lambda:None))
 cdp=pipe.PipeCDP(read_driver,write_driver,owner,context);target=cdp.send('Target.createTarget',{'url':'about:blank'},attached=False)['targetId'];cdp.session=cdp.send('Target.attachToTarget',{'targetId':target,'flatten':True},attached=False)['sessionId']
 for domain in ('Page','Runtime','Network'):cdp.send(domain+'.enable',{'maxTotalBufferSize':1,'maxResourceBufferSize':1} if domain=='Network' else None)
 cdp.send('Emulation.setDeviceMetricsOverride',{'width':1024,'height':768,'deviceScaleFactor':.5,'mobile':False});cdp.send('Emulation.setTimezoneOverride',{'timezoneId':'Asia/Seoul'})
 def until(action,reason,seconds=60):
  end=time.monotonic()+seconds
  while True:
   value=action()
   if value:return value
   browser_scope.sample();assert browser.poll() is None and time.monotonic()<end,reason;time.sleep(.1)
 def element(kind,text):
  return r"""(()=>{const text=__CONTROL_TEXT__,kind=__CONTROL_KIND__,normalize=v=>v.replace(/\s+/g,' ').trim();
   if(kind==='label'){const label=[...document.querySelectorAll('label')].find(e=>normalize([...e.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).map(n=>n.textContent).join(' '))===text);return label?.control||[...document.querySelectorAll('[aria-label]')].find(e=>e.getAttribute('aria-label')===text);}
   return [...document.querySelectorAll(kind==='button'?'button':'summary')].find(e=>normalize(e.textContent)===text||e.getAttribute('aria-label')===text);})()""".replace('__CONTROL_TEXT__',json.dumps(text)).replace('__CONTROL_KIND__',json.dumps(kind))
 def click(kind,text):
  point=until(lambda:cdp.evaluate("""(()=>{const e=ELEMENT;if(!e||e.disabled)return null;e.scrollIntoView({block:'center',behavior:'instant'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);return r.width&&r.height?{x,y,hit:!!hit&&(hit===e||e.contains(hit)),hit_tag:hit?.tagName,viewport:[innerWidth,innerHeight],screen:[screen.width,screen.height],outer:[outerWidth,outerHeight]}:null})()""".replace('ELEMENT',element(kind,text))),'control unavailable: '+text)
  actions.append({'control':text,'point':point});assert point['hit'],'control center is not hit: '+text
  coordinates={k:point[k] for k in ('x','y')}
  cdp.send('Input.dispatchMouseEvent',{'type':'mouseMoved',**coordinates})
  for event in ('mousePressed','mouseReleased'):cdp.send('Input.dispatchMouseEvent',{'type':event,'button':'left','clickCount':1,**coordinates})
  actions[-1]['active']=cdp.evaluate("({tag:document.activeElement?.tagName,type:document.activeElement?.getAttribute('type'),name:document.activeElement?.getAttribute('name')})")
 def fill(label,value):
  click('label',label)
  for event in ('keyDown','keyUp'):cdp.send('Input.dispatchKeyEvent',{'type':event,'key':'a','code':'KeyA','modifiers':2,'windowsVirtualKeyCode':65})
  cdp.send('Input.insertText',{'text':value})
 def key(name,code):
  for event in ('keyDown','keyUp'):cdp.send('Input.dispatchKeyEvent',{'type':event,'key':name,'code':name,'windowsVirtualKeyCode':code})
 def connect():
  until(lambda:cdp.evaluate('Boolean('+element('label','접근 토큰')+')'),'connection input missing')
  if not cdp.evaluate("document.querySelector('.connection')?.open"):click('summary','내부 시험 연결')
  cdp.evaluate('document.fonts.ready.then(()=>true)')
  fill('접근 토큰',TOKEN.decode());click('button','연결 설정')
  until(lambda:cdp.evaluate('Boolean('+element('button','연결 해제')+')'),'connection was not accepted')
  click('button','08 성장 연구 3D');click('label','저장 결과 판본');key('End',35);key('ArrowUp',38);key('Enter',13)
  until(lambda:cdp.evaluate('('+element('label','저장 결과 판본')+').value')=='solar','Solar format not selected')
 def load():
  if not cdp.evaluate("document.querySelector('.solar-replay .crop-lookup')?.open"):click('summary','저장 연구 결과 조회')
  labels={'result_id':'저장 연구 결과 ID','scenario_id':'농장 시나리오 ID','scenario_revision':'농장 판본','registration_sha256':'등록 SHA-256','crop_id':'작물 ID'}
  for field,value in {'result_id':result_id,**farm}.items():fill(labels[field],value)
  click('button','저장 연구 조회')
 frame_js=r"""(()=>{const root=document.querySelector('.solar-viewer');if(!root)return null;const canvas=root.querySelector('.coupled-canvas'),at=root.dataset.selectedAt;if(!canvas||canvas.dataset.sceneAt!==at||Number(canvas.dataset.drawCalls)<=0||!root.querySelector('.joint-history svg'))return null;
 const quantities=label=>Object.fromEntries([...root.querySelectorAll('dl[aria-label="'+label+'"] [data-metric]')].map(e=>[e.dataset.metric,{value:Number(e.dataset.rawValue),unit:e.querySelector('small').textContent}]));
 const gl=canvas.getContext('webgl2');return {at,scene_at:canvas.dataset.sceneAt,reference:JSON.parse(root.dataset.reference),farm:JSON.parse(root.dataset.farm),result_id:root.dataset.resultId,
 quantities:quantities('작물·기후 원값'),cohorts:[...root.querySelectorAll('.coupled-cohort-table tbody tr')].map(row=>[...row.querySelectorAll('td')].map(e=>Number(e.dataset.rawValue))),
 ledgers:quantities('누적41장부'),events:quantities('관리 사건 누적'),residuals:quantities('수지 잔차'),budgets:quantities('잔차 허용 한도'),
 ventilation:JSON.parse(root.querySelector('[data-ventilation]').dataset.ventilation),solar_heat:JSON.parse(root.querySelector('[data-solar-heat]').dataset.solarHeat),solar_PAR:JSON.parse(root.querySelector('[data-solar-par]').dataset.solarPar),solar_NIR:JSON.parse(root.querySelector('[data-solar-nir]').dataset.solarNir),
 draw_calls:Number(canvas.dataset.drawCalls),leaf_area:Number(canvas.dataset.leafSurfaceArea),drawing:JSON.parse(canvas.dataset.cohortDrawing),temperatures:JSON.parse(canvas.dataset.temperatureDrawing),WebGL2:!!gl&&!gl.isContextLost(),GL_version:gl?.getParameter(gl.VERSION),
 charts:{history:JSON.parse(root.querySelector('.joint-history .coupled-plot').dataset.values),selected:{value:Number(root.querySelector('.joint-history').dataset.selectedValue),unit:root.querySelector('.joint-history').dataset.selectedUnit},distributions:Object.fromEntries([...root.querySelectorAll('[data-distribution]')].map(e=>[e.dataset.distribution,JSON.parse(e.querySelector('.coupled-plot').dataset.values)])),SVGs:root.querySelectorAll('.coupled-plot svg').length},selected_UTCs:[...root.querySelectorAll('[data-selected-at]')].map(e=>e.dataset.selectedAt)};})()"""
 samples=json.loads(expected['samples'])['page']['records'];events=json.loads(expected['events'])['page']['records']
 def frame(index):
  row=samples[index];value=until(lambda: v if (v:=cdp.evaluate(frame_js)) and v['at']==row['time']['at'] else None,'actual saved WebGL frame missing')
  assert value['WebGL2'] and value['draw_calls']>0 and value['scene_at']==row['time']['at'];assert all(at==value['at'] for at in value['selected_UTCs'])
  assert value['reference']==summary['reference'] and value['farm']==summary['farm'] and value['result_id']==result_id
  state=row['value'];assert value['quantities']=={**state['plant_state'],**state['climate_state'],**state['derived']}
  assert value['cohorts']==[[c['value'],n['value']] for c,n in zip(state['cohort_state']['fruit_carbohydrate'],state['cohort_state']['fruit_number'])]
  for name,source in [('ledgers','integrated_transfers'),('events','event_totals'),('residuals','balance_residuals'),('budgets','balance_budgets'),('ventilation','ventilation'),('solar_heat','solar_heat_composition'),('solar_PAR','solar_par'),('solar_NIR','solar_nir')]:assert value[name]==state[source],name
  assert abs(value['leaf_area']-state['derived']['leaf_area_index']['value'])<1e-6
  assert [v['value'] for v in value['drawing']['carbon']]==[q['value'] for q in state['cohort_state']['fruit_carbohydrate']]
  assert [v['value'] for v in value['drawing']['number']]==[q['value'] for q in state['cohort_state']['fruit_number']]
  for kind,q in {'canopy':state['derived']['canopy_temperature'],'air':state['climate_state']['air_temperature']}.items():
   marker=next(m for m in value['temperatures']['markers'] if m['kind']==kind);assert {'value':marker['value'],'unit':marker['unit']}==q
  assert value['charts']['history']==[r['value']['derived']['leaf_area_index']['value'] for r in samples]
  assert value['charts']['selected']==state['derived']['leaf_area_index'] and value['charts']['SVGs']==3
  assert value['charts']['distributions']=={kind:[q['value'] for q in values] for kind,values in state['cohort_state'].items()}
  for drawing_kind,state_kind in (('carbon','fruit_carbohydrate'),('number','fruit_number')):
   assert [d['unit'] for d in value['drawing'][drawing_kind]]==[q['unit'] for q in state['cohort_state'][state_kind]]
  frames.append(value);save('browser-frame-'+str(len(frames))+'.private.json',value);return value
 cdp.send('Page.navigate',{'url':origin+'/'});phase('page');connect();phase('connected');load();frame(0);phase('first_frame')
 for index in range(1,len(samples)):click('button','다음 저장 성장 시점');frame(index)
 phase('last_frame');cdp.send('HeapProfiler.collectGarbage')
 cdp.evaluate("document.querySelector('.coupled-top-grid').scrollIntoView({block:'start'})")
 image=cdp.send('Page.captureScreenshot',{'format':'png'});path=Path(os.environ['OSSF_SOLAR_HTTP_EVIDENCE'])/'solar-'+status+'.private.png'
 with path.open('xb') as f:os.fchmod(f.fileno(),0o400);f.write(base64.b64decode(image['data']))
 screens.append({'name':path.name,'sha256':sha256(path.read_bytes()).hexdigest()})
 click('button','관리 사건 보기');until(lambda:cdp.evaluate("document.querySelectorAll('.cycle-events article').length")==len(events),'management events missing');assert cdp.evaluate("document.querySelectorAll('.solar-viewer').length")==0
 event_DOM=cdp.evaluate("[...document.querySelectorAll('.cycle-events article')].map(e=>({text:e.querySelector('h3').textContent,values:[...e.querySelectorAll('pre')].map(p=>JSON.parse(p.textContent))}))")
 for item,event in zip(event_DOM,events):assert event['time']['at'] in item['text'] and item['values']==[{'before':event['value']['solar_before'],'after':event['value']['solar_after']},event['value']['management']]
 click('button','저장 시점 보기');frame(0)
 rights.allowed=False;click('button','현재 권리 다시 조회');until(lambda:cdp.evaluate("Boolean(document.querySelector('.solar-replay [role=alert]'))"),'rights denial not displayed');assert cdp.evaluate("document.querySelectorAll('.solar-viewer,.solar-replay .joint-evidence,.solar-replay .cycle-events').length")==0;assert requests[-1]['status']==422;phase('rights_denied');rights.allowed=True
 load();frame(0);click('summary','내부 시험 연결');click('button','연결 해제');until(lambda:cdp.evaluate("document.querySelectorAll('.solar-viewer').length")==0,'disconnect retained frame');connect();load();frame(0);phase('reconnected')
 assert not cdp.errors and not cdp.warnings and not proxy_errors
 assert len(cdp.network)==len(requests) and all(row['method']=='GET' for row in cdp.network)
 pipe.close_page_and_browser(cdp,target);browser.wait(timeout=15);browser_exit=browser.returncode;assert browser_exit==0
 for fd in list(pipe_fds):os.close(fd);pipe_fds.remove(fd)
 browser_scope.sample();browser_scope.signal_owned(__import__('signal').SIGTERM)
except BaseException as error:
 try:
  diagnostic={'error_type':type(error).__name__,'reason':str(error),'HTTP':requests,'frames_saved':len(frames),'native_actions':actions}
  if browser is not None and browser.poll() is None:
   diagnostic['controls']=cdp.evaluate("({labels:[...document.querySelectorAll('label')].map(e=>[...e.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).map(n=>n.textContent).join(' ').trim()),buttons:[...document.querySelectorAll('button')].map(e=>({text:e.textContent,aria:e.getAttribute('aria-label'),disabled:e.disabled})),alerts:[...document.querySelectorAll('[role=alert]')].map(e=>e.textContent),format:document.querySelector('.crop-format select')?.value})")
  save('browser-failure.private.json',diagnostic)
 except Exception:pass
 raise
finally:
 rights.allowed=True
 if browser is not None and browser.poll() is None:
  browser_scope.sample();browser_scope.signal_owned(__import__('signal').SIGTERM);browser.wait(timeout=15)
 for fd in pipe_fds:os.close(fd)
 error_file.flush()
 with (Path(os.environ['OSSF_SOLAR_HTTP_EVIDENCE'])/'chromium.stderr.private.log').open('xb') as f:os.fchmod(f.fileno(),0o400);f.write((profile/'chromium.stderr.private.log').read_bytes())
 error_file.close();web.shutdown();web.server_close();web_thread.join(15);server.should_exit=True;thread.join(15);assert not thread.is_alive() and not web_thread.is_alive()
 assert {str(p.relative_to(web_build)):sha256(p.read_bytes()).hexdigest() for p in web_build.rglob('*') if p.is_file()}==asset_hashes
 shutil.rmtree(profile)
mode['preparing']=True
assert browser_exit==0 and inventory()==baseline and current_principal() is None and counts(service)==before and all(v==0 for v in calls.values())
with jobs.connect() as conn:assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(result_model.schema.TABLE))).fetchone()['n']==rows
print(json.dumps({'PID':os.getpid(),'status':status,'actual_scram':True,'verified_TLS':True,'actual_TypeScript_SDK':True,'actual_WebGL_browser':True,'browser_exit_code':browser_exit,'browser_TLS_trust':'owned SPKI pin; upstream Python SSL validates CA/name/time','shared_market_reader_observed':shared_reader_observed,'held_context_reader_observed':shared_reader_observed,'owned_shared_buffers_actual':buffer_actual,'native_fetch_mocked':False,'response_bytes_forwarded_unchanged':True,'current_rights_scene_removed':True,'reconnect_same_original_result':True,'device_scale_factor':.5,'frames':frames,'screenshots':screens,'actual_HTTP':requests,'native_actions':actions,'calls':calls,'counts_unchanged':True,'FD_before_after':[len(baseline),len(inventory())],'actual_crop_Runs':0,'G0_G4':'not_assessed','rights_or_gate_approval':False}))
