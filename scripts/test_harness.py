"""Behavioral regression checks; no real device, network or phone mutation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from android_harness import AndroidHarness, HarnessError, parse_nodes, parse_foreground
from helpers import namespace
from run import lane, device_lane

XML = '<hierarchy><node text="Hello" resource-id="app:id/name" class="android.widget.EditText" bounds="[0,0][100,80]" enabled="true" focused="true"/></hierarchy>'


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'session.json').write_text(json.dumps({'kind': 'android-harness-v1', 'adb': 'fake', 'serial': 'phone'}))
        self.h = AndroidHarness(self.root)
        self.h.awake = lambda: True
        self.h.locked = lambda: False
        self.h.foreground = lambda: 'app/Main'
        self.h.hierarchy = lambda: XML
        self.calls = []
        self.h.shell = lambda *args, **kw: self.calls.append(args) or ''
        self.state = {'observation': 'fresh', 'observed_at': time.time(), 'foreground': 'app/Main',
                      'xml_hash': hashlib.sha256(XML.encode()).hexdigest(), 'width': 720, 'height': 1612,
                      'screenshot': str(self.root / 'screen.png'), 'nodes': parse_nodes(XML)}
        self.h.save(self.state)

    def tearDown(self):
        self.temp.cleanup()

    def test_state_write_rejects_symlink(self):
        target = self.root / 'unrelated.txt'
        target.write_text('keep')
        (self.root / 'state.json').unlink()
        try:
            (self.root / 'state.json').symlink_to(target)
        except OSError:
            self.skipTest('Symlink creation unavailable on this host')
        with self.assertRaises(HarnessError):
            self.h.save(self.state)
        self.assertEqual(target.read_text(), 'keep')

    def test_screenshot_write_rejects_symlink(self):
        target = self.root / 'unrelated.txt'
        target.write_text('keep')
        try:
            (self.root / 'screen.png').symlink_to(target)
        except OSError:
            self.skipTest('Symlink creation unavailable on this host')
        import struct
        self.h.run = lambda *a, **k: b'\x89PNG\r\n\x1a\n' + b'0' * 8 + struct.pack('>II', 720, 1612)
        with self.assertRaises(HarnessError):
            self.h.observe()
        self.assertEqual(target.read_text(), 'keep')

    def test_disabled_text_field_rejected(self):
        self.state['nodes'][0]['enabled'] = False
        self.h.save(self.state)
        with self.assertRaises(HarnessError):
            self.h.act('fresh', 'text', text='test')
        self.assertFalse(self.calls)

    def test_voice_does_not_follow_redirect_or_forward_token(self):
        import http.server
        import threading
        import urllib.error
        requests = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append((self.path, self.headers.get('Authorization')))
                self.send_response(302)
                self.send_header('Location', '/unexpected')
                self.end_headers()
            def do_GET(self):
                requests.append((self.path, self.headers.get('Authorization')))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{}')
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]
        token = self.root / 'voice-token'
        token.write_text('fixture-token')
        forwarded = []
        def run(*args, **kwargs):
            forwarded.append(args)
            return str(port).encode() if args == ('forward', 'tcp:0', 'tcp:18080') else b''
        self.h.run = run
        try:
            with self.assertRaises(urllib.error.HTTPError):
                self.h.voice(token, 'hello')
            self.assertEqual(requests, [('/speak', 'Bearer fixture-token')])
            self.assertEqual(forwarded[-1], ('forward', '--remove', 'tcp:' + str(port)))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_tap_consumes_observation(self):
        self.h.act('fresh', 'tap', node=0)
        self.assertEqual(self.calls, [('input', 'tap', 50, 40)])
        with self.assertRaises(HarnessError): self.h.act('fresh', 'tap', node=0)
        self.assertEqual(len(self.calls), 1)

    def test_foreground_vendor_formats(self):
        for label in ('topResumedActivity=', 'mResumedActivity:', 'ResumedActivity:', 'Resumed:'):
            self.assertEqual(parse_foreground(label+' ActivityRecord{abc u0 com.example/.Main t2 d0}'), 'com.example/.Main')

    def test_changed_page_blocks_input(self):
        self.h.hierarchy = lambda: XML.replace('Hello', 'Other')
        with self.assertRaises(HarnessError): self.h.act('fresh', 'tap', node=0)
        self.assertFalse(self.calls)

    def test_changed_activity_blocks_input(self):
        self.h.foreground = lambda: 'other/Main'
        with self.assertRaises(HarnessError): self.h.act('fresh', 'key', key='BACK')
        self.assertFalse(self.calls)

    def test_expired_snapshot(self):
        self.state['observed_at'] -= 100
        self.h.save(self.state)
        with self.assertRaises(HarnessError): self.h.act('fresh', 'tap', node=0)

    def test_screen_off_blocks_action(self):
        self.h.awake = lambda: False
        with self.assertRaises(HarnessError): self.h.act('fresh', 'tap', node=0)
        self.assertFalse(self.calls)

    def test_locked_and_unknown_block_actions(self):
        for locked in (True, None):
            self.h.locked = lambda: locked
            with self.assertRaises(HarnessError): self.h.act('fresh', 'tap', node=0)
        self.assertFalse(self.calls)

    def test_old_node_handle_cannot_rebind(self):
        scope = namespace(self.h, self.root)
        node = scope['find'](text='Hello')[0]
        self.state['observation'] = 'new'
        self.h.save(self.state)
        with self.assertRaises(HarnessError): scope['tap'](node)
        self.assertFalse(self.calls)

    def test_bare_numeric_id_rejected(self):
        with self.assertRaises(HarnessError): namespace(self.h, self.root)['tap'](0)
        self.assertFalse(self.calls)

    def test_coordinate_action_requires_image(self):
        self.state['screenshot'] = None
        self.h.save(self.state)
        with self.assertRaises(HarnessError): self.h.act('fresh', 'tap-xy', x=10, y=10)

    def test_structure_only_avoids_screenshot_and_removes_previous(self):
        (self.root / 'screen.png').write_bytes(b'old')
        self.h.run = lambda *a, **k: self.fail('Screenshot capture must not run')
        result = self.h.observe(screenshot=False)
        self.assertIsNone(result['screenshot'])
        self.assertFalse((self.root / 'screen.png').exists())

    def test_forget_preserves_other_files(self):
        (self.root / 'screen.png').write_bytes(b'old')
        (self.root / 'user-photo.jpg').write_bytes(b'keep')
        self.h.forget_observation()
        self.assertFalse((self.root / 'state.json').exists())
        self.assertTrue((self.root / 'session.json').exists())
        self.assertEqual((self.root / 'user-photo.jpg').read_bytes(), b'keep')

    def test_device_lock_across_workspaces(self):
        code = 'from run import device_lane\nwith device_lane("unit-test-phone"): print("unexpected")'
        with device_lane('unit-test-phone'):
            r = subprocess.run([sys.executable, '-c', code], cwd=Path(__file__).parent, capture_output=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(b'workspace is in use', r.stderr)

    def test_timeout_not_replayed(self):
        def timeout(*args): raise TimeoutError('transport interrupted')
        self.h.shell = timeout
        with self.assertRaises(TimeoutError): self.h.act('fresh', 'key', key='BACK')
        with self.assertRaises(HarnessError): self.h.act('fresh', 'key', key='BACK')

    def test_coordinates_checked(self):
        with self.assertRaises(HarnessError): self.h.act('fresh', 'tap-xy', x=900, y=10)
        self.assertFalse(self.calls)

    def test_text_requires_focused_field(self):
        self.state['nodes'][0]['focused'] = False
        self.h.save(self.state)
        with self.assertRaises(HarnessError): self.h.act('fresh', 'text', text='test')

    def test_text_unicode_rejected(self):
        with self.assertRaises(HarnessError): self.h.act('fresh', 'text', text='\u4f60\u597d')
        self.assertFalse(self.calls)

    def test_remote_shell_quotes_metacharacters(self):
        h = AndroidHarness(self.root)
        captured = []
        h.run = lambda *args, **kw: captured.append(args) or b''
        h.shell('input', 'text', "hi;$(id)'x")
        import shlex
        self.assertEqual(shlex.split(captured[0][1]), ['input', 'text', "hi;$(id)'x"])

    def test_password_masked(self):
        self.assertEqual(parse_nodes(XML.replace('focused="true"', 'password="true"'))[0]['text'], '')

    def test_helper_selectors_and_ambiguity(self):
        scope = namespace(self.h, self.root)
        exec((Path(__file__).parent.parent / 'assets/agent_helpers.py').read_text(), scope)
        self.assertEqual(scope['unique_node'](text='Hello')['id'], 0)
        with self.assertRaises(RuntimeError): scope['tap_unique'](text='Missing')
        self.assertFalse(self.calls)

    def test_workspace_lane_blocks_second_process(self):
        code = 'from pathlib import Path; from run import lane; import sys\nwith lane(Path(sys.argv[1])): print("unexpected")'
        with lane(self.root):
            r = subprocess.run([sys.executable, '-c', code, str(self.root)], cwd=Path(__file__).parent, capture_output=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(b'workspace is in use', r.stderr)


if __name__ == '__main__':
    unittest.main()
