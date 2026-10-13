"""FD inheritance and bounded CDP framing, independently of the product UI."""
import importlib.util
import json
import os
from pathlib import Path
import select
import subprocess
import sys
from types import SimpleNamespace

import pytest

PATH = Path(__file__).with_name('crop-isolated-ventilation-pipe-reference.py')
spec = importlib.util.spec_from_file_location('pipe_reference_test', PATH)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def test_launch_preserves_both_pipes_across_exec(tmp_path):
    browser = tmp_path/'browser'
    browser.write_text('#!'+sys.executable+'\nimport os\nos.write(4,os.read(3,64))\n')
    browser.chmod(0o700)
    config = tmp_path/'context.json'
    config.write_text(json.dumps({'chromium': str(browser), 'directory': str(tmp_path)}))
    child_read, writer = os.pipe(); reader, child_write = os.pipe()
    try:
        with subprocess.Popen([sys.executable, '-B', str(PATH), 'launch', str(child_read), str(child_write), str(config)],
                pass_fds=(child_read, child_write), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL) as child:
            os.close(child_read); child_read = None
            os.close(child_write); child_write = None
            os.write(writer, b'owned-cdp-pipes\0')
            assert select.select([reader], [], [], 5)[0], 'exec did not retain the CDP descriptors'
            assert os.read(reader, 64) == b'owned-cdp-pipes\0'
            assert child.wait(timeout=5) == 0
    finally:
        for fd in (child_read, child_write, reader, writer):
            if fd is not None: os.close(fd)


@pytest.mark.parametrize('response,error', [
    ({'id': 1, 'result': {'value': '확인'}}, None),
    ({'id': 2, 'result': {}}, 'CDP command rejected'),
    ({'id': 1, 'error': {'message': 'invalid'}}, 'CDP command rejected'),
    (None, 'CDP pipe closed'),
])
def test_pipe_frames_unicode_events_and_rejects_protocol_failures(response, error):
    reader, reply_writer = os.pipe(); command_reader, writer = os.pipe()
    owned = SimpleNamespace(child=SimpleNamespace(poll=lambda: None), evidence=SimpleNamespace(poll=lambda: None))
    client = driver.PipeCDP(reader, writer, owned, {'origin': 'http://127.0.0.1:1'})
    try:
        event = {'method': 'Runtime.consoleAPICalled', 'params': {'type': 'warning'}}
        raw = json.dumps(event).encode()+b'\0'
        if response is not None: raw += json.dumps(response, ensure_ascii=False).encode()+b'\0'
        # Feed one byte at a time while the command consumes independently.
        from concurrent.futures import ThreadPoolExecutor
        def reply():
            assert b'Target.createTarget' in os.read(command_reader, 1024)
            for value in raw: os.write(reply_writer, bytes([value]))
            os.close(reply_writer)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(reply)
            if error:
                with pytest.raises(AssertionError, match=error): client.send('Target.createTarget', attached=False)
            else: assert client.send('Target.createTarget', attached=False) == response['result']
            future.result(timeout=5)
        assert client.warnings == ['warning']
    finally:
        for fd in (reader, command_reader, writer): os.close(fd)
