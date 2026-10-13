"""Reopen an existing ventilation result through the actual user UI after restart."""
import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main(args):
    cfg = json.loads(args.config.read_bytes()); root = Path(cfg['source'])
    sys.path[:0] = list(map(str, (root/'backend', root/'backend/tests', root/'research')))
    pipe = module('replay_pipe', root/'research/crop-isolated-ventilation-pipe-reference.py')
    browser = module('replay_browser', root/'research/crop-ventilation-browser-supervisor.py')
    processes = module('replay_scope', root/'research/owned-research-process-scope.py')
    case = json.loads(args.case.read_bytes())
    runtime = json.loads((Path(cfg['runtime'])/'runtime.private.json').read_bytes())
    request = args.case.parent.parent/'completed.request.private.json'
    evidence = browser.BrowserEvidence(args.output, request=request, access=Path(cfg['access']),
        rights=Path(runtime['ventilation']['rights_file']),
        driver=root/'research/crop-isolated-ventilation-cdp-reference.mjs', chromium=Path(cfg['chromium']),
        mode='completed', origin='http://127.0.0.1:5174', job_id=case['job_id'])
    context = json.loads(evidence.context.read_bytes())
    original = (root/'research/crop-isolated-ventilation-cdp-reference.mjs').read_text()
    frame_js = original[original.index('function frameDOM('):original.index('const capture=')].strip()
    clone_js = original.split("Page.addScriptToEvaluateOnNewDocument',{source:`", 1)[1].split('`});', 1)[0]
    flush_js = original.split('const value=await evaluate(`', 1)[1].split('`);', 1)[0]
    profile = args.output/'chromium-profile'; profile.mkdir(mode=0o700)
    child_read, writer = os.pipe(); reader, child_write = os.pipe()
    owned = terminal = None
    rows = []
    started = time.monotonic()
    try:
        evidence.command = ['taskset', '-c', str(min(os.sched_getaffinity(0))), 'nice', '-n', '19',
            sys.executable, '-B', str(root/'research/crop-isolated-ventilation-pipe-reference.py'),
            'launch', str(child_read), str(child_write), str(evidence.context)]
        owned = browser.BrowserChild(evidence, processes=processes, env=os.environ.copy(), pass_fds=(child_read, child_write))
        os.close(child_read); child_read = None; os.close(child_write); child_write = None
        cdp = pipe.PipeCDP(reader, writer, owned, context)
        target = cdp.send('Target.createTarget', {'url': 'about:blank'}, attached=False)['targetId']
        cdp.session = cdp.send('Target.attachToTarget', {'targetId': target, 'flatten': True}, attached=False)['sessionId']
        for domain in ('Page', 'Runtime', 'Network'): cdp.send(domain+'.enable')
        cdp.send('Page.addScriptToEvaluateOnNewDocument', {'source': clone_js})
        cdp.send('Emulation.setDeviceMetricsOverride', {'width': 390, 'height': 844, 'deviceScaleFactor': .5, 'mobile': False})
        def flush():
            value = cdp.evaluate(flush_js); assert not value['errors']
            for row in value['entries']:
                assert row['method'] == 'GET', 'replay UI made a write request'
                rows.append(row)
                if row.get('body') is not None:
                    raw = row['body'].encode()
                    with (args.output/('wire-'+str(row['index'])+'.private.json')).open('xb') as stream:
                        os.fchmod(stream.fileno(), 0o400); stream.write(raw)
            return value
        def until(action, message):
            deadline = time.monotonic()+90
            while True:
                flush(); result = action()
                if result: return result
                evidence.poll()
                assert owned.child.poll() is None and time.monotonic()<deadline, message
                time.sleep(.2)
        def element(kind, text):
            return '''(()=>{const text=TEXT,kind=KIND;
              if(kind==='label'){const label=[...document.querySelectorAll('label')].find(e=>e.textContent.trim()===text);
                return label?.control||[...document.querySelectorAll('[aria-label]')].find(e=>e.getAttribute('aria-label')===text);}
              return [...document.querySelectorAll(kind==='button'?'button':'summary')].find(e=>e.textContent.trim()===text);})()'''.replace('TEXT', json.dumps(text)).replace('KIND', json.dumps(kind))
        def click(kind, text):
            point = until(lambda: cdp.evaluate('''(()=>{const e=ELEMENT;if(!e||e.disabled)return null;
              e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();
              return r.width&&r.height?{x:r.x+r.width/2,y:r.y+r.height/2}:null;})()'''.replace('ELEMENT', element(kind, text))), 'replay control unavailable')
            for event in ('mousePressed', 'mouseReleased'):
                cdp.send('Input.dispatchMouseEvent', {'type':event,'button':'left','clickCount':1,**point})
        def fill(label, value):
            click('label', label)
            for event in ('keyDown', 'keyUp'):
                cdp.send('Input.dispatchKeyEvent', {'type':event,'key':'a','code':'KeyA','modifiers':2,'windowsVirtualKeyCode':65})
            cdp.send('Input.insertText', {'text':value})
        cdp.send('Page.navigate', {'url':context['origin']+'/#ventilation-execution'})
        until(lambda: cdp.evaluate('Boolean('+element('label','접근 토큰')+')'), 'connection form missing')
        if not cdp.evaluate("document.querySelector('.connection')?.open"): click('summary','내부 시험 연결')
        fill('접근 토큰', context['token']); click('button','연결 설정')
        labels = {'job_id':'계산 작업 ID','scenario_id':'계산 농장 시나리오 ID','scenario_revision':'계산 농장 판본',
            'registration_sha256':'계산 농장 등록 SHA-256','crop_id':'계산 작물 ID'}
        for key,value in {'job_id':case['job_id'],**case['farm']}.items(): fill(labels[key],value)
        click('button','기존 계산 조회')
        click('button','같은 저장 결과 3D 열기')
        frame = until(lambda: cdp.evaluate('('+frame_js+')(false)'), 'stored replay WebGL missing')
        assert cdp.evaluate("document.querySelector('.ventilation-viewer').dataset.resultId") == case['result']['result_id']
        final = until(lambda: value if (value:=flush())['pending']==0 else None, 'replay response capture incomplete')
        assert not cdp.errors and not cdp.warnings
        assert len(rows)==final['count'] and all(row.get('body') is not None or row.get('aborted') for row in rows)
        pipe.close_page_and_browser(cdp,target)
        os.close(writer);writer=None;os.close(reader);reader=None
        owned.child.wait(timeout=15);terminal=owned.finish()
        assert terminal['actual_child_exit']==0 and not terminal['forced_kill'] and terminal['current_rights_restored']
        samples=json.loads(args.samples.read_bytes())['page']['records']
        reference=module('replay_frame_reference',root/'research/test_crop_greenhouse_ventilation_live_browser_reference.py')
        reference.check_frame(frame,samples[0])
        wired=[json.loads(row['body']) for row in rows if row.get('body') and row.get('status')==200 and 'view=samples' in row.get('query','')]
        assert any(value['page']['records']==samples for value in wired)
        proof={'same_stored_result_after_service_restart':True,'original_UTC_table_chart_WebGL':True,
            'samples':len(samples),'sample_wire_sha256':sha256(args.samples.read_bytes()).hexdigest(),
            'actual_browser_exit':0,'forced_kill':False,'API_writes':0,'response_clones_added_requests':0,
            'pageerrors':0,'warnings':0,'device_scale_factor':.5,'wall_seconds':time.monotonic()-started,
            'real_farm_runs':0,'G0_G4':'not_assessed'}
        with (args.output/'acceptance.private.json').open('x') as stream:
            os.fchmod(stream.fileno(),0o400);json.dump(proof,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
        print(json.dumps(proof,sort_keys=True))
    finally:
        if owned is not None and terminal is None:owned.finish('replay_interrupted')
        else:evidence.close()
        for fd in (child_read,child_write,reader,writer):
            if fd is not None:os.close(fd)
        shutil.rmtree(profile)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('config','case','samples','output'):parser.add_argument('--'+name,type=Path,required=True)
    main(parser.parse_args())
