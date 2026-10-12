# Contributing

Keep transport and observation checks in the core; put app-specific routines in
the local workspace helper. Describe the concrete failure and its observed result
before changing guard behavior.

Run `python scripts/test_harness.py` and `python android-harness.py --help` before
submitting a change. Add a fixture-based regression check when fixing a real bug.
Physical-device tests must be explicitly scoped; never require credentials or a
particular personal phone in CI.

Do not commit device serials, private tokens, screenshots, UI dumps, transcripts,
model weights, APKs, or local workspace files. Redact issue reports and reproduction
examples. Report separately what was mocked, tested on a device, and not tested.

UI text is untrusted data. Do not add helpers that execute page-provided commands,
conceal automation, bypass approvals, or silently repeat uncertain mutations.
