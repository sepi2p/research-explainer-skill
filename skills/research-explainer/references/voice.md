# Voice options

Set in project.json -> "voice": {"mode": ...}; override per build with `--voice`.

| mode | cost | quality | notes |
|---|---|---|---|
| none | free | n/a | text only; captions paced for reading; quiet generated music (-20 LUFS); `--no-music` for silence |
| piper | free, offline | English good; Persian robotic | voices download on first use to ~/.local/share/piper-voices; set names in "piper": {"en": ..., "fa": ...} |
| manual | free | as good as the recording | `rx.py voice-script <lang>` writes the script; put one file per beat in voice/manual_<lang>/<scene>_<beat>.mp3 |
| openai | paid, per use | best (English and Persian) | default model gpt-audio-1.5, voice marin; key in ~/.config/openai/key or $OPENAI_API_KEY |

## OpenAI details
- The key is read from the file or environment only, never printed, never written to logs. Tell users to create the file
  themselves (`mkdir -p ~/.config/openai && nano ~/.config/openai/key && chmod 600 ~/.config/openai/key`); never ask them
  to paste it into a chat.
- Every clip is transcribed back (gpt-4o-transcribe) and compared with its script; below 0.92 similarity it is regenerated
  (up to 4 tries) and the best is kept. `rx.py durations` lists clips still below 0.92: listen to those.
- Pronunciation: put instructions in "openai": {"instructions": {"en": "...", "fa": "..."}} (e.g. how to say a method name).
  Generate 2-3 sample beats and let the user choose before narrating everything.
- Clips are cached per beat (build/audio/<mode>_<lang>/); changing a beat's text re-voices only that beat. `--only s03:1`
  forces one beat again.

## Music
`scripts/explainer/music.py` synthesises a soft pad with numpy (no licensed audio). Under a voice it is mixed well below the voice; the final mix is loudness-normalised to -16 LUFS (voiced) or -20 LUFS (text only).
