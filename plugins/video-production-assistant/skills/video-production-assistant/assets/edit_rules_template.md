# House edit rules

Read before every edit. These rules override the skill defaults. Add a dated line when a rule changes, so the history stays clear. Only change a rule after the user agrees.

## Toolkit (filled in by the set-up check)
- Machine:
- FFmpeg:  | Whisper:  | Node 22+:  | HyperFrames CLI:  | Blender:  | yt-dlp:
- Python for the scripts: (system `python`, or `_tools/venv`)
- Connectors: ElevenLabs:  | vidIQ:  | HyperFrames (hosted):  | Shell connector:
- Video library folder:

## Transcripts
- Default: local Whisper (`transcribe_local.py`, model medium.en; small.en on 8 GB machines)
- Backup: ElevenLabs Scribe (connector or `transcribe_elevenlabs.py`), only with the user's yes each time - uses credits
- Names and terms to spell right:

## Brand
- Full sheet: _brand/brand.md
- Colours:
- Fonts:
- Logo file and position:
- Lower-third style:
- Intro / outro:

## Cutting
- Silence threshold: -35 dB
- Padding: 0.12 s
- Pause kept at joins: 0.15 s
- Remove fillers: um, uh, er, erm
- Retakes: keep the last complete take unless noted

## Audio
- Voice target: -14 LUFS, true peak -1 dBTP
- Music: 20 dB under voice, duck ratio 6, release 300 ms
- Noise reduction: on (light)

## Captions
- Burn in: yes for social, sidecar .srt for YouTube
- Style: bold sans-serif, white on dark box, max 2 lines, 32 characters per line
- Highlight words:

## Output
- Default shape: 16:9, 1920x1080, 30 fps
- File naming: YYYY-MM-DD_slug_vN.mp4

## Lessons learned (newest first)
<!-- - 2026-11-05: Raised padding to 0.18 s after clipped word at 1:45 (video: claude-skills-intro) -->
