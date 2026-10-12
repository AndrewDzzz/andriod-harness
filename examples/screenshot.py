"""Explicit screenshot request; open the returned image before choosing coordinates."""
import json

state = screen_info(screenshot=True)
print(json.dumps({k: state[k] for k in ('observation', 'screenshot', 'width', 'height', 'locked')}))
