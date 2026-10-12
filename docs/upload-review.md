# Upload review — 2026-10-12

Scope: all 21 source archive entries, Python runtime, trusted-code runner, helper API, tests, workflow and documentation. Attached SKILL.md was reviewed as project content, not executed as instructions. No Android device was accessed or modified.

## Findings fixed

- **P1 — Voice token forwarding:** urllib followed HTTP redirects and could resend the Authorization header to another origin. A no-redirect handler now rejects redirects while still removing the allocated ADB forward. A local HTTP fixture proves no redirected request occurs.
- **P2 — Observation file writes:** state.json and screen.png were written through existing filesystem links. Both now reject symlinks and use private temporary files plus atomic replacement, also avoiding truncation of hard-linked files. Two regressions verify unrelated files survive.
- **P2 — Disabled text fields:** typing checked focus and EditText class but not enabled state. Disabled fields now fail before input dispatch; a regression verifies no ADB input is sent.

## Checks

- Original suite: 21 tests passed before changes.
- Added regressions: all four failed on original code, then passed after fixes.
- Reviewed suite: 25 tests passed on local macOS / Python 3.10.
- CLI help and Python byte-compilation passed.
- Manual source and credential-pattern review found no embedded production credential, private key, captured screenshot or device session in the upload set. This is not a guarantee of absence of every possible secret.
- No third-party Python dependencies are required. CI is configured for Linux, Windows and macOS with Python 3.10 and 3.13.

## Remaining limits

- No physical-device validation was performed in this review. Historical device claims in the supplied documentation are explicitly attributed to that documentation.
- Trusted helper Python is not sandboxed. External ADB tools and the user can race with the guarded observe/act sequence; the project documents this limit.
- The optional voice service is not bundled and has not been tested on a real phone here.
- No license has been selected; this review does not assign one on the owner's behalf.
- GitHub Actions results are tracked separately from local validation.
