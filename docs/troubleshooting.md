# Troubleshooting

Start with `python android-harness.py --workspace PATH --doctor`.

| Symptom | Response |
| --- | --- |
| No ADB device | Check cable, unlock the phone and verify USB debugging. Device discovery is read-only. |
| unauthorized | Accept the USB debugging prompt on the phone. Do not replace device identity. |
| Locked or unknown lock state | Unlock manually. Unsupported OEM output needs a parser fixture and a tested fix. |
| Stale or changed UI | Observe again and reassess the target. Never reuse an old ID against a new screen. |
| No hierarchy | Request `screen_info(screenshot=True)` and inspect the image. Secure screens may remain unavailable. |
| Numeric tap rejected | Pass the node handle from `find()`, or supply the original observation token explicitly. |
| No focused EditText | Focus the intended field, re-observe, then type supported ASCII. |
| Workspace in use | Let the running invocation finish. Do not delete lock files or start competing controllers. |
| Timeout after an action | Inspect the device before retrying; the action may already have completed. |
| Host tool says blocked by policy | The execution environment rejected it. Inspect the reported reason; do not wrap the same action differently to bypass the rejection. |
| Background voice unavailable | Verify the separately installed service and token file. This repository does not install them. |

The runner uses existing ADB OS interfaces. A successful process exit establishes
only dispatch; verify the desired application state separately. Device updates and
reboots may interrupt USB transport and other independently installed services.
