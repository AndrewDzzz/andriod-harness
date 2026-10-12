"""Run through android-harness.py --file; helpers are preloaded."""
import json

print(json.dumps(device_info(), ensure_ascii=True, indent=2))
state = screen_info()
print(json.dumps({
    'observation': state['observation'],
    'foreground': state['foreground'],
    'locked': state['locked'],
    'nodes': [n for n in state['nodes'] if n['text'] or n['description'] or n['clickable']],
}, ensure_ascii=True, indent=2))
