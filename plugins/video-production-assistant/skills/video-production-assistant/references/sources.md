# Footage sources, recording tips and rights

## StreamYard

- **What to download.** Prefer per-person local recordings if the user's plan offers them: each speaker's camera and audio as a separate high-quality file, recorded on their own machine, so internet glitches do not reach the file. Otherwise download the composed recording (the layout viewers saw) and, if offered, the audio-only file.
- **Screen share.** In a composed recording the screen share is already in the layout. For a clean edit, ask the user to also record the screen locally (OBS, Windows Snipping Tool video, QuickTime) so you can cut to it full-frame.
- **Layouts.** A composed recording with a screen share and a small camera bubble cannot be split back into separate pictures. Crop to the screen area for cutaways if needed: `-vf crop=w:h:x:y` (find the box from a frame grab).
- **Multiple guests.** With separate tracks, the edit timeline is the guest switch; with one composed file, cut as usual.
- **Quiet voice tracks.** Individual voice tracks are often much quieter than the composed mix (speech around -48 dB RMS is common). The default -35 dB silence threshold then cuts soft words. Measure first (`ffmpeg -i track.wav -af volumedetect -f null -`), then pass a lower threshold to `rough_cut.py plan`, for example `--noise -58`, and note it in `edit_rules.md`.
- **Sync.** Separate local files start at slightly different times. Line them up by the first loud sound (a clap at the start helps) before editing.

## Recording tips to pass on (before recording)

- Keep the recording running through mistakes; pause, then repeat the whole sentence. A clean pause makes the retake easy to find.
- Clap once at the start if there will be separate tracks.
- Ten seconds of room silence at the start helps noise reduction.
- Record screen at the output size (1920x1080) and enlarge text in apps (browser zoom 125-150%) so it reads on a phone.

## Other sources

| Source | Watch for | Fix |
|---|---|---|
| Phone video | Variable frame rate; portrait | Convert to constant frame rate; choose 9:16 output or blur-fill for 16:9 |
| Zoom / Teams | Low bitrate, speaker view switching | Use "record separate audio file per participant" if available |
| Loom / browser recorders | Variable frame rate, WebM | Convert to MP4 constant frame rate |
| OBS | Usually clean; may record MKV | Remux: `ffmpeg -i in.mkv -c copy out.mp4` |
| Podcast audio + stills | No video | Use B-roll-only route; stills as cutaways with slow zoom |
| Existing edited video | Already cut | Skip steps 5-6; captions without `--edl` |

## Rights rules for outside material (yt-dlp, web images, music)

Use outside clips only when one of these is true, and note which in `03_assets/sources.txt`:
1. It is the user's own published material.
2. The licence allows reuse in this kind of video (for example Creative Commons BY with credit shown on screen or in the description; public domain).
3. The user has written permission from the owner.
4. It is stock or generated media the user has a licence for.

Do not download other creators' YouTube videos for B-roll by default. YouTube's terms restrict downloading, and reusing a clip can trigger a copyright claim on the user's channel. "Fair use" (US) and "fair dealing" (UK) are narrow and decided case by case; do not rely on them for the user. If the user insists, explain the risk in one sentence and suggest: their own screen recording of the same software, a still screenshot with credit, or a short quote shown as text.

Documentation and product demos: recording your own screen while using the product is almost always the better and safer B-roll.
