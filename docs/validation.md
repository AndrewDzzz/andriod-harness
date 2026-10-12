# Validation scope

## Local automated checks

The reviewed version contains 25 fixture/subprocess tests. They cover stale observations,
foreground changes, consumed actions, timeout behavior, coordinate checks,
text-field checks, shell quoting, password masking, exact selectors, workspace
and per-device locks, keyguard checks, bound node handles, structure-only capture,
and cleanup preserving unrelated files. Four added regressions cover symlink-safe
state/image writes, disabled text fields, and preventing voice HTTP redirects.

Run them with `python scripts/test_harness.py`. They do not contact a phone.

## Physical-device observations

The supplied project documentation reports that on a Windows host and a nubia
Focus 5G running Android 14, an earlier workflow
verified connection/status, screen wake, screenshot capture, UI hierarchy parsing,
lockscreen rejection, observation cleanup, Chrome/Firefox/YouTube launches,
ASCII text entry (`ni hao`), scrolling through a Google results page, and taps in
the Play Store update/install flow. YouTube playback was separately verified via
Android media-session state.

Some task operations used direct, separately authorized ADB commands rather than
this harness. In particular, store deep links, package version checks and media
session checks are not exposed as high-level harness helpers. Do not represent
them as built-in or fully covered end-to-end workflows.

The optional new voice wrapper has not received a dedicated real-device test.
Older, separate phone speech tooling worked, but that is not proof for this wrapper.
The repository does not bundle phone model/service deployments.

## Not established

Cross-platform physical-device behavior, arbitrary OEM compatibility, unattended
long-running reliability, unrestricted Unicode input, secure-screen capture and
automation detectability have not been established. GitHub Actions is configured
but has not run on a remote repository yet.
