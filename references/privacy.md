# Privacy and visible automation effects

This harness minimizes extra components and retained task data. It does not promise
to hide automation from Android, apps, websites, ADB, the host, or the conversation.

Default behavior:

- No telemetry client, screen recorder, title marker, touch overlay, clipboard
  replacement, custom keyboard, browser extension or accessibility service.
- No phone binary or script deployment. ADB uses existing OS commands. UI hierarchy
  dumping does temporarily create an XML file, removed by exact path afterwards.
- `screen_info()` reads structure only; screenshot capture is explicit. Each new
  observation replaces the previous one rather than building a trajectory archive.
- `forget_observation()` removes this session's latest local UI state and image.
  Device configuration and agent-written helper source are preserved.
- No network listener is started by the harness. The optional voice adapter uses
  an authenticated temporary loopback USB forward and removes only its own forward.
- No random human-like timing, fingerprint spoofing, anti-bot bypass, hidden
  accessibility operation, log clearing, or changes to app security mechanisms.

Limits: UI text may contain private information even with password fields masked.
Screenshots can contain anything visible. Tool output may remain in the chat.
Android/app/browser logs and user-created media are not affected by local cleanup.
Installed Termux services and USB debugging remain visible; they are not hidden.
Trusted agent_helpers.py and submitted host Python can do more than the built-in
helpers, so review additions before treating these defaults as properties of them.

When evaluating whether an app detects automation, distinguish visible UI changes,
local data retention and actual anti-automation detection. This implementation has
not been benchmarked for detectability and makes no claim about it. Do not modify
the user's existing app/browser configuration just to conceal the controller.
