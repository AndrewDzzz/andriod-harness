# API

## Preferred browser-harness-style runner

```powershell
# Use the absolute installed skill path for RUN_PY.
python RUN_PY --workspace ABS_WORKSPACE --init --adb ABS_ADB --serial SERIAL
python RUN_PY --workspace ABS_WORKSPACE --doctor
python RUN_PY --workspace ABS_WORKSPACE --file ABS_HOST_SCRIPT
python RUN_PY --workspace ABS_WORKSPACE --forget
```

Alternatively pipe Python source on stdin. Scripts receive the helpers listed in
SKILL.md and functions from the workspace's agent_helpers.py. The workspace path
can also be supplied using AH_AGENT_WORKSPACE. The interpreter namespace is fresh
per invocation; selected device, last observation and helper source persist on disk.
No second host daemon is installed. A host OS lock serializes runner commands for
the same serial, even across workspaces. External ADB and low-level API callers
are not covered. Lock files contain one byte, with a hashed serial filename in
the host temporary directory; the OS releases locks when a process exits.

`screen_info()` defaults to structure-only and removes the prior screenshot.
`screen_info(screenshot=True)` explicitly captures one. `find(...)` returns handles
containing their observation token; pass a handle to `tap(node)`, or pass a numeric
ID with an explicit observation token. Bare numeric IDs are rejected.
`forget_observation()` deletes only the last local observation, without phone calls.

## Low-level API

Requires Python 3.10+ and authorized ADB. The module uses only the Python standard library.
Invoke the script by its absolute path; all examples below abbreviate it as `harness.py`.

```text
python harness.py devices --adb ABS_ADB
python harness.py --session ABS_NEW_RUN init --adb ABS_ADB --serial SERIAL
python harness.py --session ABS_RUN status
python harness.py --session ABS_RUN observe
python harness.py --session ABS_RUN launch --package com.android.chrome
```

For actions, use the Python API to avoid host-shell JSON escaping:

```python
import sys
sys.path.insert(0, ABS_SKILL_SCRIPTS_DIRECTORY)
from android_harness import AndroidHarness
h = AndroidHarness(ABS_RUN_DIRECTORY)
snapshot = h.observe()
# Inspect snapshot and screenshot before choosing an actual node.
matches = [n for n in snapshot['nodes'] if n['resource_id'] == OBSERVED_RESOURCE_ID]
if len(matches) != 1:
    raise RuntimeError('Target is missing or ambiguous')
h.act(snapshot['observation'], 'tap', node=matches[0]['id'])
after = h.observe()
# Check the task-specific result in after, not merely the dispatch return value.
```

`act(token, action, **values)` accepts:

| Action | Values |
| --- | --- |
| tap | node: current numeric node ID |
| tap-xy | x, y: screenshot pixel coordinates |
| swipe | x, y, end_x, end_y; optional duration in milliseconds, 100-2000 |
| text | text: 1-1000 printable ASCII characters, no percent signs |
| key | key: BACK, HOME, ENTER, DEL or TAB |

Observations expire after 90 seconds and are consumed before mutation. Launch invalidates any saved observation. Observe immediately before acting and again afterwards. The harness does not retry mutations, automatically click consent dialogs, infer a successful photo from a tap, or change device settings.

`observe` returns absolute screenshot path, width/height, foreground component, serial,
observation token, timestamp, nodes, and optional hierarchy warning. Each node includes
id, text, description, resource_id, class, bounds and boolean UI attributes.
Hidden WebView or canvas content may not appear in the hierarchy. Screenshot checks
are strict and may reject camera previews or animation. Low-level API clients must
serialize their own operations; use the runner for its device lock. Structure-only
width/height come from UI bounds; coordinate operations require screenshot dimensions.

CLI `act` accepts `--observation TOKEN --action ACTION --values JSON` for clients that
can pass structured argument strings safely. Do not embed untrusted text in shell code.

Success is JSON on stdout; failures are JSON on stderr with nonzero exit and
`retry_mutation: false`. Inspect before retrying. Subprocess and HTTP timeouts are
bounded, but device disconnects can prevent remote temp-file or port-forward cleanup.
