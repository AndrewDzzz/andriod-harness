# Android Harness

A small, agent-editable Android control harness: observe a connected phone, choose
an action, then verify the result. Inspired by the stable-core and editable-helper
design of [browser-harness](https://github.com/browser-use/browser-harness).

[中文说明](README.zh-CN.md) · [Agent skill](SKILL.md) · [API](references/api.md) · [Validation](docs/validation.md)

**Status: experimental.** Built and tested on a Windows host with an Android 14
phone. Runtime dependencies are Python and Android Platform Tools; no Python
packages or additional on-device automation app are required for UI control.

## What it does

- Reads the UI hierarchy and optionally captures a screenshot.
- Resolves elements by exact text, description, or resource ID.
- Performs guarded taps, ASCII typing, swipes, key presses and app launches.
- Rejects expired or consumed observations, changed UI, and locked phones.
- Preloads Python helpers and preserves an editable `agent_helpers.py` workspace.
- Serializes runner commands targeting the same phone on the same host.
- Supports an optional, already configured background voice service.

It does not include an LLM, autonomous task planner, MCP server, cloud service,
phone-side installer, Unicode input method, recording system, or anti-detection
feature. Your coding agent supplies the planning and can improve its host helpers.

## Quick start

Requirements: Python 3.10+, [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools),
USB debugging enabled and authorized on your own phone. Unlock the phone before
UI actions. Extract or clone this repository and run commands from its root.

```console
python android-harness.py --help
python scripts/android_harness.py devices --adb /absolute/path/to/adb
python android-harness.py --workspace work/my-phone --init --adb /absolute/path/to/adb --serial YOUR_DEVICE_SERIAL
python android-harness.py --workspace work/my-phone --doctor
python android-harness.py --workspace work/my-phone --file examples/inspect.py
```

On Windows use the full path to `adb.exe`; quote paths containing spaces. Reuse the
same workspace instead of initializing one for each command. `--init` preserves
existing helpers and rejects an attempt to switch an existing workspace's device.

The runner loads trusted Python from `--file` or stdin with these helpers ready:

```python
screen = screen_info()                # UI structure; no screenshot by default
print(screen)

# After reviewing a fresh observation and choosing a real target:
matches = find(resource_id="com.example:id/the_observed_button")
if len(matches) != 1:
    raise RuntimeError("Missing or ambiguous target")
tap(matches[0])                       # Handle carries its observation token
print(screen_info())                  # Verify the actual result
```

The package ID above is a placeholder, not a runnable demo target. To view layout,
use `screen_info(screenshot=True)` and open the returned local image. Coordinate
taps and swipes require this explicit screenshot observation.

PowerShell stdin example:

```powershell
@'
print(device_info())
print(screen_info())
'@ | python android-harness.py --workspace work/my-phone
```

Bash stdin example:

```bash
python android-harness.py --workspace work/my-phone <<'PY'
print(device_info())
print(screen_info())
PY
```

Use `AH_AGENT_WORKSPACE` instead of `--workspace` when convenient. Python variables
do not persist between invocations; workspace configuration, latest observation,
and helper source do.

## Extend it like browser-harness

```text
Stable core             scripts/android_harness.py
Preloaded helpers       scripts/helpers.py
Host runner             scripts/run.py
Agent-edited routines   work/my-phone/agent_helpers.py
Optional app notes      work/my-phone/app-skills/<package>/*.md
Latest observation      work/my-phone/session/
```

Add reusable app-specific routines to the workspace helper file. Changes load on
the next invocation. Test them against the observed UI and retain regression tests
for real failures. Set `AH_APP_SKILLS=1` to discover optional local per-app notes.
See [extension guidance](references/extending.md).

The harness never automatically rewrites code. "Repair" means the coding agent
inspects a failure, edits its helper, tests it, and verifies the result. Stable core
guards should not be disabled to force an operation through.

## Use as a skill

The repository root is a self-contained skill directory: `SKILL.md`, `scripts/`,
`references/` and `assets/`. Copy this source directory to your agent's supported
skills location, excluding `.git/`, `work/`, caches and local configuration. The
skill points to `scripts/run.py`, so it works independently of this root launcher.

## Privacy and limitations

Default inspection stores only the latest parsed UI state. Screenshots are opt-in;
a later structure-only observation removes the earlier screenshot. After verification:

```console
python android-harness.py --workspace work/my-phone --forget
```

This deletes only the last `state.json` and `screen.png`, retaining configuration
and helpers. It does not clear Android logs, browser history, user files, tool output
or chat records. It does not make automation undetectable.

- Text entry currently supports printable ASCII without percent signs.
- Accessibility dumps can omit custom-drawn or WebView content.
- Strict stale-UI checks can reject dynamic screens. Re-observe; do not blindly retry.
- The user and external ADB tools can still race with the runner.
- Trusted Python runs with normal host permissions; this is not a code sandbox.
- Optional voice requires a separately deployed authenticated service; see
  [voice adapter protocol](references/local-voice.md).
- A dispatch success is not evidence that a business action completed. Verify it.

Read [privacy details](references/privacy.md) and [troubleshooting](docs/troubleshooting.md).

## Development

```console
python scripts/test_harness.py
python -m compileall -q scripts android-harness.py examples
```

Tests use fixtures and subprocesses, not a physical phone. The GitHub Actions
workflow is configured for Windows, Linux and macOS on Python 3.10 and 3.13;
remote CI has not run until the repository is uploaded. See [validation](docs/validation.md)
for the narrower set of platforms and device actions actually verified.

## Attribution and license status

The architecture is inspired by browser-harness, reviewed at commit
`dbf0e4f3a37ebc31aaeaf9d378ab1760b5776c15`. This implementation was independently
written and does not include its source or depend on its runtime.

No redistribution license has been selected for this project yet. The project
owner should choose one before presenting it as an open-source release.
