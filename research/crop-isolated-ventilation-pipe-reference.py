"""Drive actual Chromium over its CDP pipes inside the existing probe owner."""
from base64 import b64decode
from hashlib import sha256
import json
import os
from pathlib import Path
import select
import shutil
import sys
import time
from urllib.parse import urlsplit


def launch():
    incoming, outgoing = map(int, sys.argv[2:4])
    config = json.loads(Path(sys.argv[4]).read_bytes())
    # Duplicate both before assigning 3/4: either source may already be 3 or 4.
    a, b = os.dup(incoming), os.dup(outgoing)
    os.dup2(a, 3, inheritable=True); os.dup2(b, 4, inheritable=True)
    os.set_inheritable(3, True); os.set_inheritable(4, True)
    for fd in {incoming, outgoing, a, b}-{3, 4}: os.close(fd)
    flags = ['--headless', '--no-sandbox', '--disable-dev-shm-usage',
        '--disable-background-networking', '--disable-extensions', '--disable-component-update', '--disable-sync',
        '--disable-gpu-rasterization', '--disable-gpu-compositing',
        '--disable-features=Translate,OptimizationHints,MediaRouter', '--enable-unsafe-swiftshader',
        '--single-process', '--no-zygote', '--num-raster-threads=1', '--use-gl=angle', '--use-angle=swiftshader-webgl',
        '--js-flags=--jitless --max-old-space-size=24 --max-semi-space-size=1 --expose-gc',
        '--user-data-dir='+config['directory']+'/chromium-profile', '--remote-debugging-pipe', 'about:blank']
    if config.get('spki'):
        assert len(b64decode(config['spki'], validate=True)) == 32
        flags.insert(-1, '--ignore-certificate-errors-spki-list='+config['spki'])
    os.execv(config['chromium'], [config['chromium'], *flags])


class PipeCDP:
    def __init__(self, reader, writer, owned, config):
        self.reader, self.writer, self.owned, self.config = reader, writer, owned, config
        self.sequence = 0
        self.session = None
        self.buffer = bytearray()
        self.network, self.methods, self.errors, self.warnings = [], {}, [], []
        self.started = time.monotonic()

    def send(self, method, params=None, *, attached=True):
        assert time.monotonic()-self.started < 660, 'browser case deadline expired'
        self.sequence += 1
        message = {'id': self.sequence, 'method': method, 'params': params or {}}
        if attached: message['sessionId'] = self.session
        raw = memoryview(json.dumps(message).encode()+b'\0')
        while raw:
            written = os.write(self.writer, raw); raw = raw[written:]
        deadline = time.monotonic()+60
        while True:
            if b'\0' not in self.buffer:
                if not select.select([self.reader], [], [], .25)[0]:
                    self.owned.evidence.poll()
                    assert self.owned.child.poll() is None, 'Chromium exited'
                    assert time.monotonic() < deadline, 'CDP command deadline expired'
                    continue
                data = os.read(self.reader, 65536)
                assert data, 'CDP pipe closed'
                self.buffer.extend(data)
                assert len(self.buffer) <= 8*1024**2, 'CDP message exceeds bound'
                continue
            raw, _, remaining = self.buffer.partition(b'\0'); self.buffer = bytearray(remaining)
            value = json.loads(raw)
            if 'id' in value:
                assert value['id'] == self.sequence and 'error' not in value, 'CDP command rejected'
                return value.get('result', {})
            self.event(value)

    def event(self, value):
        method, p = value.get('method'), value.get('params', {})
        if method == 'Network.requestWillBeSent': self.methods[p['requestId']] = p['request']['method']
        elif method == 'Network.responseReceived':
            url = urlsplit(p['response']['url'])
            if not url.path.startswith('/v1/'): return
            assert url.scheme+'://'+url.netloc == self.config['origin'], 'unexpected API origin'
            self.network.append({'path': url.path, 'query': '?'+url.query if url.query else '',
                'status': p['response']['status'], 'method': self.methods.get(p['requestId']), 'requestId': p['requestId']})
        elif method == 'Network.loadingFailed':
            for row in self.network:
                if row['requestId'] == p['requestId']: row.update(failed=True, canceled=bool(p.get('canceled')))
        elif method == 'Runtime.exceptionThrown': self.errors.append(p['exceptionDetails']['text'])
        elif method == 'Runtime.consoleAPICalled' and p['type'] in ('warning', 'error'): self.warnings.append(p['type'])

    def evaluate(self, expression):
        value = self.send('Runtime.evaluate', {'expression': expression, 'returnByValue': True, 'awaitPromise': True})
        assert 'exceptionDetails' not in value, 'browser evaluation failed'
        return value['result'].get('value')


def close_page_and_browser(cdp, target):
    cdp.send('Page.navigate', {'url': 'about:blank'})
    deadline = time.monotonic()+10
    while cdp.evaluate('document.URL') != 'about:blank':
        assert time.monotonic() < deadline, 'browser page did not unload'
        time.sleep(.05)
    cdp.send('HeapProfiler.collectGarbage')
    assert cdp.send('Target.closeTarget', {'targetId': target}, attached=False)['success']
    cdp.send('Browser.close', attached=False)


def exercise(evidence, *, processes, supervisor_class):
    cfg = json.loads(evidence.context.read_bytes())
    request = json.loads(Path(cfg['request_file']).read_bytes())
    directory = evidence.directory
    source = (Path(__file__).with_name('crop-isolated-ventilation-cdp-reference.mjs')).read_text()
    frame_js = source[source.index('function frameDOM('):source.index('const capture=')].strip()
    clone_js = source.split("Page.addScriptToEvaluateOnNewDocument',{source:`", 1)[1].split('`});', 1)[0]
    flush_js = source.split('const value=await evaluate(`', 1)[1].split('`);', 1)[0]
    assert 'const entries=source.entries.flatMap' in flush_js and '__ownedHTTPCloneEvidence' in clone_js
    def save(name, value):
        with (directory/name).open('xb') as f:
            os.fchmod(f.fileno(), 0o400)
            f.write(json.dumps(value).encode()); f.flush(); os.fsync(f.fileno())
    profile = directory/'chromium-profile'; profile.mkdir(mode=0o700)
    child_read, writer = os.pipe(); reader, child_write = os.pipe()
    owned = None
    started = time.monotonic()
    responses, frames, job_id, terminal = [], [], None, None
    cdp = None
    try:
        evidence.command = ['taskset', '-c', str(min(os.sched_getaffinity(0))), 'nice', '-n', '19',
            sys.executable, '-B', str(Path(__file__).resolve()), 'launch', str(child_read), str(child_write), str(evidence.context)]
        owned = supervisor_class(evidence, processes=processes, env=os.environ.copy(), pass_fds=(child_read, child_write))
        os.close(child_read); child_read = None
        os.close(child_write); child_write = None
        cdp = PipeCDP(reader, writer, owned, cfg)
        target = cdp.send('Target.createTarget', {'url': 'about:blank'}, attached=False)
        cdp.session = cdp.send('Target.attachToTarget', {'targetId': target['targetId'], 'flatten': True}, attached=False)['sessionId']
        for domain in ('Page', 'Runtime'): cdp.send(domain+'.enable')
        cdp.send('Network.enable', {'maxTotalBufferSize': 1, 'maxResourceBufferSize': 1})
        cdp.send('Page.addScriptToEvaluateOnNewDocument', {'source': clone_js})
        def viewport(width, height): cdp.send('Emulation.setDeviceMetricsOverride',
            {'width': width, 'height': height, 'deviceScaleFactor': 0.5, 'mobile': False})
        viewport(390, 600); cdp.send('Emulation.setTimezoneOverride', {'timezoneId': 'Asia/Seoul'})
        def flush():
            value = cdp.evaluate(flush_js)
            assert not value['errors'], 'actual fetch response clone failed'
            for entry in value['entries']:
                entry = dict(entry); index = entry.pop('index'); body = entry.pop('body', None); entry.pop('flushed', None)
                if body is not None:
                    raw = body.encode(); name = 'wire-'+str(index)+'.private.json'
                    with (directory/name).open('xb') as f: os.fchmod(f.fileno(), 0o400); f.write(raw)
                    entry.update(wire_file=name, body_sha256=sha256(raw).hexdigest())
                else: assert entry.get('aborted') and entry['method'] == 'GET'
                while len(responses) <= index: responses.append(None)
                responses[index] = entry
            return value
        def until(action, message, seconds=45):
            deadline = time.monotonic()+seconds
            while True:
                flush(); value = action()
                if value: return value
                evidence.poll(); assert owned.child.poll() is None, 'Chromium exited'
                assert time.monotonic() < deadline, message
                time.sleep(.2)
        def element(kind, text):
            return '''(()=>{const text=TEXT,kind=KIND;
              if(kind==='label'){const label=[...document.querySelectorAll('label')].find(e=>e.textContent.trim()===text);
                return label?.control||[...document.querySelectorAll('[aria-label]')].find(e=>e.getAttribute('aria-label')===text);}
              const selector=kind==='button'?'button':kind==='heading'?'h1,h2,h3,h4,[role=heading]':'summary';
              return [...document.querySelectorAll(selector)].find(e=>e.textContent.trim()===text);})()'''.replace('TEXT', json.dumps(text)).replace('KIND', json.dumps(kind))
        def has(kind, text): return cdp.evaluate('Boolean('+element(kind, text)+')')
        def click(kind, text):
            point = until(lambda: cdp.evaluate('''(()=>{const e=ELEMENT;if(!e||e.disabled)return null;
              e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();
              return r.width&&r.height?{x:r.x+r.width/2,y:r.y+r.height/2}:null;})()'''.replace('ELEMENT', element(kind, text))), 'control unavailable: '+text)
            for event in ('mousePressed', 'mouseReleased'): cdp.send('Input.dispatchMouseEvent',
                {'type': event, 'button': 'left', 'clickCount': 1, **point})
        def fill(label, value):
            click('label', label)
            for event in ('keyDown', 'keyUp'): cdp.send('Input.dispatchKeyEvent',
                {'type': event, 'key': 'a', 'code': 'KeyA', 'modifiers': 2, 'windowsVirtualKeyCode': 65})
            cdp.send('Input.insertText', {'text': value})
        def input_value(label): return cdp.evaluate('('+element('label', label)+')?.value')
        def capture(prefix=True): return cdp.evaluate('('+frame_js+')('+json.dumps(prefix)+')')
        def screenshot(name):
            cdp.send('HeapProfiler.collectGarbage')
            cdp.evaluate("document.querySelector('.coupled-top-grid')?.scrollIntoView({block:'start'})")
            raw = b64decode(cdp.send('Page.captureScreenshot', {'format': 'png'})['data'])
            with (directory/(name+'.private.png')).open('xb') as f: os.fchmod(f.fileno(), 0o600); f.write(raw)
        def rights(name):
            fd = os.open(directory/name, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600); os.close(fd)
            evidence.poll(); assert (directory/(name+'-ack')).exists()
        cdp.send('Page.navigate', {'url': cfg['origin']+'/#ventilation-execution'})
        until(lambda: has('label', '접근 토큰'), 'product connection form missing')
        if not cdp.evaluate("document.querySelector('.connection')?.open"): click('summary', '내부 시험 연결')
        fill('접근 토큰', cfg['token']); click('button', '연결 설정')
        assert input_value('계산 모델') == 'ventilation'
        def file_input():
            doc = cdp.send('DOM.getDocument'); value = cdp.send('DOM.querySelector',
                {'nodeId': doc['root']['nodeId'], 'selector': 'input[type=file]'})
            return value.get('nodeId')
        node = until(file_input, 'product request file input missing')
        cdp.send('DOM.setFileInputFiles', {'nodeId': node, 'files': [cfg['request_file']]}); click('button', '계산 접수')
        import re
        job_id = until(lambda: value if re.fullmatch('[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', value := input_value('계산 작업 ID') or '') else None,
            'admitted job not displayed')
        canceled = reached_terminal = False
        deadline = time.monotonic()+480
        while time.monotonic() < deadline:
            flush(); frame = capture()
            if frame and not any(old['at'] == frame['at'] and old['reference']['selector']['publication_sequence'] ==
                    frame['reference']['selector']['publication_sequence'] for old in frames):
                frame.update(selection='automatic_latest'); frames.append(frame); save('observed-frame-'+str(len(frames))+'.private.json', frame)
                if len(frames) == 1:
                    if cfg['mode'] == 'cancel':
                        click('button', '서버 계산 취소')
                        until(lambda: cdp.evaluate("Boolean([...document.querySelectorAll('[role=status]')].find(e=>/^취소 요청 수락 · 취소 응답 당시:/.test(e.textContent.trim())))"), 'cancellation not accepted')
                        until(lambda: has('heading', '취소됨'), 'cancellation not settled', 90)
                        assert cdp.evaluate("document.querySelectorAll('.coupled-canvas').length") == 0
                        canceled = True; break
                    screenshot('running')
            if has('button', '같은 저장 결과 3D 열기'): reached_terminal = True; break
            evidence.poll(); cdp.send('HeapProfiler.collectGarbage'); time.sleep(.3)
        assert frames and not cdp.errors, 'no running WebGL frame or JavaScript failure'
        result = {'mode': cfg['mode'], 'job_id': job_id, 'running_frames': frames, 'selection_verified': False,
            'cancel_accepted': canceled, 'scene_cleared': canceled, 'pageerrors': cdp.errors, 'responses': responses,
            'warnings': cdp.warnings, 'test_pause': False}
        if cfg['mode'] != 'cancel':
            assert reached_terminal, 'terminal result missing'
            click('button', '같은 저장 결과 3D 열기'); result['terminal_frame'] = until(lambda: capture(False), 'terminal WebGL missing')
            result_id = cdp.evaluate("document.querySelector('.ventilation-viewer').dataset.resultId"); result['result_id'] = result_id
            viewport(800, 600); screenshot('terminal')
            click('button', '조회 연결 해제')
            labels = {'job_id': '계산 작업 ID', 'scenario_id': '계산 농장 시나리오 ID', 'scenario_revision': '계산 농장 판본',
                'registration_sha256': '계산 농장 등록 SHA-256', 'crop_id': '계산 작물 ID'}
            for key, value in {'job_id': job_id, **request['farm']}.items(): fill(labels[key], value)
            click('button', '기존 계산 조회')
            until(lambda: has('button', '같은 저장 결과 3D 열기'), 'same job reconnect missing')
            click('button', '같은 저장 결과 3D 열기'); until(lambda: capture(False), 'reconnected WebGL missing')
            assert cdp.evaluate("document.querySelector('.ventilation-viewer').dataset.resultId") == result_id
            result['reconnected'] = True
            rights('rights-revoke'); click('button', '현재 권리 다시 조회')
            until(lambda: cdp.evaluate("document.querySelectorAll('[role=alert]').length"), 'current rights alert missing')
            assert any(row['status'] == 422 and row['path'].startswith('/v1/crop-greenhouse-ventilation-research-results/') for row in cdp.network)
            assert cdp.evaluate("document.querySelectorAll('.coupled-canvas').length") == 0
            result['rights_cleared'] = True; screenshot('rights-blocked')
            rights('rights-restore'); click('button', '저장 연구 조회')
            result['restored_frame'] = until(lambda: capture(False), 'restored WebGL missing')
            assert cdp.evaluate("document.querySelector('.ventilation-viewer').dataset.resultId") == result_id
            result['rights_restored'] = True
            viewport(390, 844); assert cdp.evaluate('document.documentElement.scrollWidth<=innerWidth+1'); screenshot('mobile')
        else: assert canceled
        captured = until(lambda: value if (value := flush())['pending'] == 0 else None, 'HTTP body capture incomplete', 15)
        assert len(responses) == captured['count'] and all(row and ('wire_file' in row or row.get('aborted')) for row in responses)
        assert not cdp.errors
        result.update(network_responses=[{k:v for k,v in row.items() if k != 'requestId'} for row in cdp.network],
            response_capture={'mechanism': 'actual fetch Response.clone; CDP pipes in existing owner', 'requests_added': 0,
                'bytes': captured['bytes'], 'product_aborted_GETs': sum(bool(row.get('aborted')) for row in responses), 'device_scale_factor': 0.5},
            wall_seconds=time.monotonic()-started)
        save('browser-result.private.json', result)
        close_page_and_browser(cdp, target['targetId'])
        os.close(writer); writer = None
        os.close(reader); reader = None
        owned.child.wait(timeout=15)
        terminal = owned.finish()
        return terminal
    except BaseException as error:
        save('browser-failure.private.json', {'error_type': type(error).__name__, 'message': str(error),
            'running_frames': frames, 'pageerrors': cdp.errors if cdp else [], 'job_id': job_id})
        raise
    finally:
        if owned and terminal is None: owned.finish('browser_probe_interrupted')
        else: evidence.close()
        for fd in (child_read, child_write, reader, writer):
            if fd is not None: os.close(fd)
        shutil.rmtree(profile)


if __name__ == '__main__':
    assert sys.argv[1] == 'launch'
    launch()
