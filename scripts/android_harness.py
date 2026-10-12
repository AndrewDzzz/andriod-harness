"""Stdlib Android observe/act harness. No on-device executable installation."""
import argparse
import hashlib
import json
import pathlib
import os
import tempfile
import re
import shlex
import struct
import subprocess
import sys
import time
import urllib.request
import uuid
import xml.etree.ElementTree as ET


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Keep the voice bearer token on the explicitly selected loopback endpoint."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HarnessError(RuntimeError):
    pass


def parse_foreground(raw):
    match = re.search(r'(?:topResumedActivity|mResumedActivity|ResumedActivity|Resumed:)[^\n]*?\bu\d+\s+([^\s}]+/[^\s}]+)', raw)
    if not match:
        raise HarnessError('Foreground activity unavailable; unlock the phone and observe again')
    return match.group(1)


def parse_nodes(xml):
    nodes = []
    for node in ET.fromstring(xml).iter('node'):
        a = node.attrib
        bounds = re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', a.get('bounds', ''))
        if not bounds:
            continue
        x1, y1, x2, y2 = map(int, bounds.groups())
        if x2 <= x1 or y2 <= y1:
            continue
        if not any(a.get(k) for k in ('text', 'content-desc', 'resource-id')) and not any(a.get(k) == 'true' for k in ('clickable', 'scrollable', 'focusable')):
            continue
        nodes.append({'id': len(nodes), 'text': '' if a.get('password') == 'true' else a.get('text', ''),
                      'description': '' if a.get('password') == 'true' else a.get('content-desc', ''), 'resource_id': a.get('resource-id', ''),
                      'class': a.get('class', ''), 'bounds': [x1, y1, x2, y2],
                      **{k: a.get(k) == 'true' for k in ('clickable', 'enabled', 'focused', 'scrollable', 'password')}})
    return nodes


class AndroidHarness:
    def __init__(self, session):
        self.root = pathlib.Path(session).resolve(strict=True)
        self.config = json.loads((self.root / 'session.json').read_text(encoding='utf-8'))
        if self.config.get('kind') != 'android-harness-v1':
            raise HarnessError('Not an Android harness session')
        self.adb = self.config['adb']
        self.serial = self.config['serial']

    @staticmethod
    def devices(adb):
        r = subprocess.run([str(adb), 'devices', '-l'], capture_output=True, timeout=15, check=True)
        return [dict(serial=p[0], state=p[1], detail=' '.join(p[2:]))
                for line in r.stdout.decode('utf-8', errors='replace').splitlines()[1:]
                if len(p := line.split()) >= 2]

    @classmethod
    def create(cls, session, adb, serial):
        adb = str(pathlib.Path(adb).resolve(strict=True))
        if not any(d['serial'] == serial and d['state'] == 'device' for d in cls.devices(adb)):
            raise HarnessError('Selected device is not connected and authorized')
        root = pathlib.Path(session).resolve()
        root.mkdir(parents=True, exist_ok=False)
        (root / 'session.json').write_text(json.dumps({'kind': 'android-harness-v1', 'adb': adb, 'serial': serial}), encoding='utf-8')
        return cls(root)

    def run(self, *args, timeout=25):
        r = subprocess.run([self.adb, '-s', self.serial, *map(str, args)], capture_output=True, timeout=timeout)
        if r.returncode:
            raise HarnessError(r.stderr.decode('utf-8', errors='replace').strip() or 'ADB failed')
        return r.stdout

    def shell(self, *args, timeout=25):
        # ADB invokes a remote shell: quote each argument for that shell as well.
        return self.run('shell', ' '.join(shlex.quote(str(a)) for a in args), timeout=timeout).decode('utf-8', errors='replace').strip()

    def foreground(self):
        raw = self.shell('dumpsys', 'activity', 'activities')
        return parse_foreground(raw)

    def awake(self):
        return bool(re.search(r'mWakefulness=Awake\b', self.shell('dumpsys', 'power')))

    def locked(self):
        raw = self.shell('dumpsys', 'window', 'policy')
        match = re.search(r'^\s*(?:mIsShowing|showing)=(true|false)\s*$', raw, re.M)
        return match.group(1) == 'true' if match else None

    def require_interactive(self):
        if not self.awake():
            raise HarnessError('Screen is not awake; wake and observe before acting')
        if self.locked() is not False:
            raise HarnessError('Phone is locked or lock state is unknown; unlock manually before UI actions')

    def wake_screen(self):
        self.invalidate()
        self.shell('input', 'keyevent', 'KEYCODE_WAKEUP')
        time.sleep(0.3)
        return {'awake': self.awake(), 'unlocked': 'not checked; unlock manually if required'}

    def hierarchy(self):
        remote = '/data/local/tmp/android-harness-' + uuid.uuid4().hex + '.xml'
        try:
            self.shell('uiautomator', 'dump', remote, timeout=25)
            xml = self.shell('cat', remote)
            ET.fromstring(xml)
            return xml
        finally:
            # Remove only this invocation's temporary UI dump; report cleanup failure.
            self.shell('rm', '-f', remote)

    def status(self):
        return {'serial': self.serial, 'state': self.run('get-state').decode().strip(),
                'model': self.shell('getprop', 'ro.product.model'),
                'android': self.shell('getprop', 'ro.build.version.release'),
                'awake': self.awake(),
                'locked': self.locked(),
                'foreground': self.foreground()}

    def observe(self, screenshot=True):
        self.invalidate()
        before = self.foreground()
        warning = None if self.awake() else 'Screen is not awake; screenshot may be black. Wake before UI actions.'
        try:
            xml = self.hierarchy()
        except Exception as error:
            xml = None
            warning = 'UI hierarchy unavailable: ' + str(error)
        png = None
        if screenshot:
            png = self.run('exec-out', 'screencap', '-p')
            if not png.startswith(b'\x89PNG\r\n\x1a\n') or len(png) < 24:
                raise HarnessError('No valid screenshot; secure surfaces may not be capturable')
            width, height = struct.unpack('>II', png[16:24])
        else:
            if not xml:
                raise HarnessError('Hierarchy unavailable; explicitly request a screenshot observation')
            # UI bounds give current-coordinate extents, not physical display specs.
            bounds = [tuple(map(int, m)) for m in re.findall(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', xml)]
            width = max((b[2] for b in bounds), default=0)
            height = max((b[3] for b in bounds), default=0)
            self.remove_artifact('screen.png')
        after = self.foreground()
        if before != after:
            raise HarnessError('Foreground changed during observation; observe again')
        state = {'observation': uuid.uuid4().hex, 'observed_at': time.time(), 'serial': self.serial,
                 'foreground': after, 'width': width, 'height': height,
                 'screenshot': str(self.root / 'screen.png') if png else None,
                 'locked': self.locked(),
                 'xml_hash': hashlib.sha256(xml.encode()).hexdigest() if xml else None,
                 'screen_hash': hashlib.sha256(png).hexdigest() if png else None,
                 'nodes': parse_nodes(xml) if xml else [], 'warning': warning}
        if png:
            self.write_artifact('screen.png', png)
        self.save(state)
        return state

    def write_artifact(self, name, data):
        if name not in ('state.json', 'screen.png'):
            raise HarnessError('Not an observation artifact')
        path = self.root / name
        if path.is_symlink() or path.resolve().parent != self.root:
            raise HarnessError('Refusing an observation path outside the session')
        # Replace the directory entry atomically rather than following links or
        # truncating an existing hard-linked file. mkstemp uses private permissions.
        fd, temporary = tempfile.mkstemp(prefix='.observation-', dir=self.root)
        try:
            with os.fdopen(fd, 'wb') as output:
                output.write(data)
            os.replace(temporary, path)
        finally:
            pathlib.Path(temporary).unlink(missing_ok=True)

    def save(self, state):
        self.write_artifact('state.json', json.dumps(state, ensure_ascii=False).encode('utf-8'))

    def remove_artifact(self, name):
        if name not in ('state.json', 'screen.png'):
            raise HarnessError('Not a disposable observation artifact')
        path = self.root / name
        if path.is_symlink() or path.resolve().parent != self.root:
            raise HarnessError('Refusing an observation path outside the session')
        path.unlink(missing_ok=True)

    def forget_observation(self):
        for name in ('state.json', 'screen.png'):
            self.remove_artifact(name)
        return {'forgotten': ['state.json', 'screen.png'], 'session_preserved': True}

    def invalidate(self):
        path = self.root / 'state.json'
        if path.exists():
            state = json.loads(path.read_text(encoding='utf-8'))
            state['consumed'] = True
            self.save(state)

    def guard(self, observation):
        self.require_interactive()
        state = json.loads((self.root / 'state.json').read_text(encoding='utf-8'))
        if state.get('consumed') or state['observation'] != observation or not 0 <= time.time() - state['observed_at'] <= 90:
            raise HarnessError('Stale observation; observe again before acting')
        if state['foreground'] != self.foreground():
            raise HarnessError('Foreground changed; observe again')
        if state['xml_hash']:
            digest = hashlib.sha256(self.hierarchy().encode()).hexdigest()
            if digest != state['xml_hash']:
                raise HarnessError('UI changed; observe again')
        else:
            digest = hashlib.sha256(self.run('exec-out', 'screencap', '-p')).hexdigest()
            if digest != state['screen_hash']:
                raise HarnessError('Screen changed; observe again')
        return state

    def act(self, observation, action, **values):
        state = self.guard(observation)
        if action == 'tap':
            node = next((n for n in state['nodes'] if n['id'] == values.get('node')), None)
            if not node or not node['enabled']:
                raise HarnessError('No enabled node with that ID')
            x1, y1, x2, y2 = node['bounds']
            x, y = (x1 + x2) // 2, (y1 + y2) // 2
            args = ('input', 'tap', x, y)
        elif action == 'tap-xy':
            if not state.get('screenshot'):
                raise HarnessError('Coordinate taps require an explicit screenshot observation')
            x, y = int(values['x']), int(values['y'])
            args = ('input', 'tap', x, y)
        elif action == 'swipe':
            if not state.get('screenshot'):
                raise HarnessError('Swipes require an explicit screenshot observation')
            x, y, ex, ey = (int(values[k]) for k in ('x', 'y', 'end_x', 'end_y'))
            duration = int(values.get('duration', 350))
            if not 100 <= duration <= 2000 or not 0 <= ex < state['width'] or not 0 <= ey < state['height']:
                raise HarnessError('Invalid swipe endpoint or duration')
            args = ('input', 'swipe', x, y, ex, ey, duration)
        elif action == 'text':
            text = values['text']
            # Android input text does not reliably support Unicode or literal %s.
            if not isinstance(text, str) or not 0 < len(text) <= 1000 or any(ord(c) < 32 or ord(c) > 126 for c in text) or '%' in text:
                raise HarnessError('Text requires 1-1000 printable ASCII characters, without percent signs')
            focused = [n for n in state['nodes'] if n['focused'] and n['enabled'] and n['class'].endswith('EditText')]
            if len(focused) != 1:
                raise HarnessError('No unique focused EditText; inspect and focus the intended field')
            args = ('input', 'text', text.replace(' ', '%s'))
        elif action == 'key':
            key = values['key']
            if key not in ('BACK', 'HOME', 'ENTER', 'DEL', 'TAB'):
                raise HarnessError('Unsupported key')
            args = ('input', 'keyevent', 'KEYCODE_' + key)
        else:
            raise HarnessError('Unknown action')
        if action in ('tap', 'tap-xy', 'swipe') and not (0 <= x < state['width'] and 0 <= y < state['height']):
            raise HarnessError('Coordinates outside screenshot')
        # Consume before dispatch, including on timeout. Never auto-repeat a mutation.
        self.invalidate()
        self.shell(*args)
        return {'dispatched': True, 'verified': False, 'next': 'observe and verify the requested result'}

    def launch(self, package):
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+', package):
            raise HarnessError('Invalid package name')
        self.require_interactive()
        self.invalidate()
        output = self.shell('am', 'start', '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.LAUNCHER', '-p', package)
        for _ in range(8):
            if self.foreground().split('/')[0] == package:
                return {'foreground': self.foreground(), 'verified': True}
            time.sleep(0.25)
        raise HarnessError('Requested package not foreground: ' + output)

    def voice(self, token_file, text, generate=False, speak=True):
        if not isinstance(text, str) or not 0 < len(text) <= 4000:
            raise HarnessError('Voice text must contain 1-4000 characters')
        token = pathlib.Path(token_file).read_text(encoding='utf-8').strip()
        port = int(self.run('forward', 'tcp:0', 'tcp:18080').decode().strip())
        try:
            req = urllib.request.Request(f'http://127.0.0.1:{port}/' + ('chat' if generate else 'speak'),
                data=json.dumps({'text': text, 'speak': speak}).encode(),
                headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
            with urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect()).open(req, timeout=300) as response:
                return json.load(response)
        finally:
            self.run('forward', '--remove', 'tcp:' + str(port))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', help='Dedicated task-owned session directory')
    sub = parser.add_subparsers(dest='command', required=True)
    devices = sub.add_parser('devices'); devices.add_argument('--adb', required=True)
    init = sub.add_parser('init'); init.add_argument('--adb', required=True); init.add_argument('--serial', required=True)
    for cmd in ('status', 'observe'):
        sub.add_parser(cmd)
    launch = sub.add_parser('launch'); launch.add_argument('--package', required=True)
    act = sub.add_parser('act'); act.add_argument('--observation', required=True)
    act.add_argument('--action', choices=['tap', 'tap-xy', 'swipe', 'text', 'key'], required=True)
    act.add_argument('--values', default='{}', help='JSON keyword arguments; prefer Python API for complex strings')
    for cmd in ('speak', 'chat'):
        voice = sub.add_parser(cmd); voice.add_argument('--token-file', required=True); voice.add_argument('--text', required=True)
        if cmd == 'chat': voice.add_argument('--silent', action='store_true')
    args = parser.parse_args()
    if args.command == 'devices':
        result = AndroidHarness.devices(args.adb)
    else:
        if not args.session: parser.error('--session is required')
        h = AndroidHarness.create(args.session, args.adb, args.serial) if args.command == 'init' else AndroidHarness(args.session)
        if args.command in ('init', 'status'): result = h.status()
        elif args.command == 'observe': result = h.observe()
        elif args.command == 'launch': result = h.launch(args.package)
        elif args.command == 'act': result = h.act(args.observation, args.action, **json.loads(args.values))
        else: result = h.voice(args.token_file, args.text, args.command == 'chat', not getattr(args, 'silent', False))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'error': str(error), 'retry_mutation': False}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
