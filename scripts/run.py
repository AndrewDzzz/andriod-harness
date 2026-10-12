"""Browser-harness-style host Python runner with a persistent device workspace."""
import argparse
from contextlib import contextmanager
import json
import hashlib
import os
from pathlib import Path
import sys
import tempfile
from android_harness import AndroidHarness, HarnessError
from helpers import namespace

SKILL = Path(__file__).resolve().parent.parent


@contextmanager
def lane(workspace, name='.lane.lock'):
    # OS lock is released on process exit, including crashes. The file is metadata only.
    with (workspace / name).open('a+b') as file:
        file.seek(0, 2)
        if file.tell() == 0:
            file.write(b'0'); file.flush()
        file.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise HarnessError('This workspace is in use; wait for the existing command')
        try:
            yield
        finally:
            file.seek(0)
            if os.name == 'nt':
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(file.fileno(), fcntl.LOCK_UN)


@contextmanager
def device_lane(serial):
    root = Path(tempfile.gettempdir()) / 'android-harness-locks'
    root.mkdir(exist_ok=True)
    with lane(root, hashlib.sha256(serial.encode()).hexdigest() + '.lock'):
        yield


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default=os.environ.get('AH_AGENT_WORKSPACE', str(Path.cwd() / 'work/android-harness')))
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--init', action='store_true')
    group.add_argument('--doctor', action='store_true')
    group.add_argument('--skill', action='store_true')
    group.add_argument('--forget', action='store_true', help='Delete only the last observation; preserve helpers and session')
    group.add_argument('--file', type=Path, help='Trusted host Python file; otherwise read stdin')
    parser.add_argument('--adb')
    parser.add_argument('--serial')
    args = parser.parse_args()
    if args.skill:
        print((SKILL / 'SKILL.md').read_text(encoding='utf-8')); return
    workspace = Path(args.workspace).resolve()
    if args.init:
        if not args.adb or not args.serial:
            parser.error('--init requires --adb and --serial')
        workspace.mkdir(parents=True, exist_ok=True)
        with lane(workspace):
            session = workspace / 'session'
            if session.exists():
                h = AndroidHarness(session)
                if h.serial != args.serial or Path(h.adb) != Path(args.adb).resolve():
                    raise HarnessError('Workspace belongs to another device/configuration; use an explicit new workspace')
            else:
                h = AndroidHarness.create(session, args.adb, args.serial)
            helper = workspace / 'agent_helpers.py'
            if not helper.exists():
                helper.write_text((SKILL / 'assets/agent_helpers.py').read_text(encoding='utf-8'), encoding='utf-8')
            (workspace / 'app-skills').mkdir(exist_ok=True)
            print(json.dumps({'workspace': str(workspace), 'device': h.status()})); return
    if not (workspace / 'session/session.json').exists():
        raise HarnessError('Initialize this workspace with --init --adb PATH --serial SERIAL')
    h = AndroidHarness(workspace / 'session')
    with lane(workspace), device_lane(h.serial):
        if args.forget:
            print(json.dumps(h.forget_observation())); return
        if args.doctor:
            print(json.dumps({'ready': True, 'workspace': str(workspace), 'device': h.status(),
                              'helpers': str(workspace / 'agent_helpers.py'), 'app_skills_enabled': os.environ.get('AH_APP_SKILLS') == '1',
                              'privacy': {'telemetry': False, 'screen_recording': False, 'default_screenshots': False,
                                          'retention': 'last observation until replaced or --forget'}})); return
        scope = {'__name__': '__harness__', **namespace(h, workspace)}
        namespace_snapshot = dict(scope)
        helper = workspace / 'agent_helpers.py'
        # This is trusted agent-authored HOST code, not a sandbox or phone injection.
        exec(compile(helper.read_text(encoding='utf-8'), str(helper), 'exec'), scope)
        if any(scope.get(name) is not value for name, value in namespace_snapshot.items()):
            raise HarnessError('Agent helpers must not replace core helper names')
        code = args.file.read_text(encoding='utf-8') if args.file else sys.stdin.read()
        if not code.strip():
            raise HarnessError('Provide Python on stdin or --file')
        exec(compile(code, str(args.file or '<android-harness>'), 'exec'), scope)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'error': str(error), 'retry_mutation': False}), file=sys.stderr)
        sys.exit(1)
