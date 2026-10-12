# Android Harness

Control an Android phone from Python through ADB. Built for coding agents: **observe → act → verify**.

[中文](README.zh-CN.md) · [Agent skill](SKILL.md) · [API](references/api.md) · [Troubleshooting](docs/troubleshooting.md)

## Features

- Read UI elements and take screenshots on request.
- Tap, swipe, type ASCII text, press keys and launch apps.
- Reject stale observations, repeated actions and input on locked phones.
- Keep reusable app routines in an editable `agent_helpers.py` workspace.

UI control uses only Python's standard library and ADB. No extra phone app is required.

## Quick start

Install Python 3.10+ and [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools). Connect your phone, authorize USB debugging and unlock it.

```sh
git clone https://github.com/AndrewDzzz/andriod-harness.git
cd andriod-harness
python scripts/android_harness.py devices --adb /absolute/path/to/adb
python android-harness.py --workspace work/my-phone --init --adb /absolute/path/to/adb --serial YOUR_DEVICE_SERIAL
python android-harness.py --workspace work/my-phone --file examples/inspect.py
```

Replace the ADB path and device serial with your own. On Windows, use the full path to `adb.exe`. The last command prints the current app and UI elements without taking a screenshot.

Reuse the same workspace for later commands:

```sh
python android-harness.py --workspace work/my-phone --file examples/screenshot.py
python android-harness.py --workspace work/my-phone --forget
```

The first command captures a screenshot and prints its path. The second removes the latest observation and screenshot, keeping configuration and helpers.

## Use with an agent

See [SKILL.md](SKILL.md) for the agent workflow. The runner preloads helpers such as `screen_info()`, `find()`, `tap()` and `swipe()`. Add app-specific routines to the workspace's `agent_helpers.py`; see [extending the harness](references/extending.md).

## Status and limits

Experimental. Text input supports printable ASCII without `%`; some custom UI elements may be absent from observations. Host Python is trusted code, not a sandbox. Verify the result after every action.

[Privacy](references/privacy.md) · [Validation](docs/validation.md) · [Contributing](CONTRIBUTING.md) · [Optional voice service](references/local-voice.md)

Run the tests with `python scripts/test_harness.py`.

Inspired by [browser-harness](https://github.com/browser-use/browser-harness). No redistribution license has been selected yet.
