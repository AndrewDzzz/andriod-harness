"""Small preloaded API; keep app-specific routines in agent_helpers.py."""
import json
import os
import time
from android_harness import HarnessError


def namespace(harness, workspace):
    def current():
        try:
            return json.loads((harness.root / 'state.json').read_text(encoding='utf-8'))
        except FileNotFoundError:
            raise HarnessError('Call screen_info() first')

    def screen_info(screenshot=False):
        state = harness.observe(screenshot=screenshot)
        package = state['foreground'].split('/')[0]
        root = workspace / 'app-skills' / package
        state['app_skills'] = [str(p) for p in sorted(root.glob('*.md'))[:10]] if os.environ.get('AH_APP_SKILLS') == '1' else []
        return state

    def find(text=None, resource_id=None, description=None):
        if text is None and resource_id is None and description is None:
            raise HarnessError('Supply at least one exact selector')
        selectors = {'text': text, 'resource_id': resource_id, 'description': description}
        state = current()
        return [dict(n, observation=state['observation']) for n in state['nodes'] if all(v is None or n[k] == v for k, v in selectors.items())]

    def dispatch(action, **values):
        return harness.act(current()['observation'], action, **values)

    def tap(node, observation=None):
        if isinstance(node, dict):
            return harness.act(node['observation'], 'tap', node=node['id'])
        if not observation:
            raise HarnessError('Pass a node from find(), or a numeric ID plus observation=TOKEN')
        return harness.act(observation, 'tap', node=node)

    def tap_xy(x, y):
        return dispatch('tap-xy', x=x, y=y)

    def type_text(text):
        return dispatch('text', text=text)

    def press(key):
        return dispatch('key', key=key)

    def swipe(x, y, end_x, end_y, duration=350):
        return dispatch('swipe', x=x, y=y, end_x=end_x, end_y=end_y, duration=duration)

    def wait_for(text=None, resource_id=None, description=None, timeout=20):
        if not 0 < timeout <= 60:
            raise HarnessError('Wait timeout must be between 0 and 60 seconds')
        if text is None and resource_id is None and description is None:
            raise HarnessError('Supply a selector')
        deadline = time.monotonic() + timeout
        while True:
            screen_info()
            result = find(text, resource_id, description)
            if result:
                return result
            if time.monotonic() >= deadline:
                raise HarnessError('Element not observed before timeout; no action performed')
            time.sleep(0.3)

    def speak(text, token_file=None):
        path = token_file or os.environ.get('AH_VOICE_TOKEN_FILE')
        if not path:
            raise HarnessError('Set AH_VOICE_TOKEN_FILE to an existing private token file')
        return harness.voice(path, text)

    def chat(text, speak=True, token_file=None):
        path = token_file or os.environ.get('AH_VOICE_TOKEN_FILE')
        if not path:
            raise HarnessError('Set AH_VOICE_TOKEN_FILE to an existing private token file')
        return harness.voice(path, text, generate=True, speak=speak)

    return dict(screen_info=screen_info, device_info=harness.status, find=find, tap=tap,
                tap_xy=tap_xy, type_text=type_text, press=press, swipe=swipe,
                open_app=harness.launch, wake_screen=harness.wake_screen, wait_for=wait_for, speak=speak, chat=chat,
                forget_observation=harness.forget_observation)
