# Existing local voice service

This adapter is optional. It requires the already installed authenticated Termux
background service, not just ADB. It does not install or start that service.
It allocates one temporary USB forward to phone loopback port 18080 and removes
only that forward on completion. No phone Activity is launched.

```text
python scripts/android_harness.py --session ABS_RUN speak --token-file ABS_PRIVATE_TOKEN --text "Hello"
python scripts/android_harness.py --session ABS_RUN chat --token-file ABS_PRIVATE_TOKEN --text "Say hello briefly"
python scripts/android_harness.py --session ABS_RUN chat --token-file ABS_PRIVATE_TOKEN --text "What is 17 plus 26?" --silent
```

Use `speak` for exact text and `chat` for model generation. Speech currently uses
the installed English voice. `speech_completed` means the speech API completed;
it does not prove the assistant heard the speaker. Do not retry a timed-out request
without checking whether the phone spoke already.

Configuration is local to the operator. Supply your own ADB path and select the
serial returned by device enumeration. Store the private token outside the repository
and pass its path using --token-file or AH_VOICE_TOKEN_FILE. Never print or commit it.

The adapter expects an existing service on phone loopback port 18080:
- POST /speak with JSON {"text": "Hello", "speak": true}
- POST /chat with JSON {"text": "Question", "speak": true or false}
- Authorization: Bearer TOKEN
- Response: JSON including text and speech_completed

This repository does not deploy that service, download a model, supply a TTS engine,
or implement continuous microphone listening. Normal UI control does not require it.

HTTP redirects are rejected. The bearer token is sent only to the allocated
loopback URL; a redirect is an error, not a request to forward authentication.
