# Game sounds

These original procedural effects are stored as mono 22,050 Hz, 16-bit PCM WAV files so desktop and mobile browsers can play them through standard HTML audio, like the existing cricket recording. They do not depend on a running Web Audio context.

Regenerate with `python3 tools/generate_sounds.py` (standard library only). No external samples or credentials are required. The existing embedded user-provided night and rain recordings in `index.html` are preserved.
