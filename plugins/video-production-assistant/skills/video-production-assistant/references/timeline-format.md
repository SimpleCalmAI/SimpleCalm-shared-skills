# timeline.json (read by assemble.py)

All times are seconds on the **rough-cut timeline** (after pauses are removed), not the raw recording. To find when a line is spoken: `python _tools/rough_cut.py find "the words" --words 02_work/words.json --edl 02_work/edl.json`. Paths are relative to the project folder.

```json
{
  "base": "02_work/roughcut.mp4",
  "audio": "02_work/mix.wav",
  "captions": "02_work/captions.ass",
  "size": [1920, 1080],
  "fps": 30,
  "crf": 18,
  "cutaways": [
    {"src": "03_assets/screen_share.mp4", "at": 12.4, "dur": 9.0, "src_in": 3.0, "fit": "contain"},
    {"src": "03_assets/diagram.png", "at": 40.0, "dur": 5.0, "fit": "cover"}
  ],
  "overlays": [
    {"src": "03_assets/lower_third.mov", "at": 2.0, "dur": 5.0, "x": 80, "y": 860, "fade": 0.3},
    {"src": "03_assets/logo.png", "at": 0, "dur": 9999, "x": "W-w-40", "y": 40, "w": 160, "fade": 0},
    {"src": "02_work/aroll_crop.mp4", "at": 12.4, "dur": 9.0, "x": "W-w-40", "y": "H-h-40", "w": 420, "fade": 0.2}
  ]
}
```

- `base`: the rough cut. Its length sets the video length.
- `audio`: polished mix from `audio_mix.py`. Leave out to keep the base audio.
- `captions`: `.ass` file from `captions.py`. Leave out for no burned-in captions.
- `cutaways`: full-frame B-roll. The voice continues underneath. Video or image. `src_in` = where to start inside a video clip. `fit`: `contain` (letterbox) or `cover` (fill and crop).
- `overlays`: drawn on top, with transparency kept. PNG, WebM (VP9 alpha) or MOV (ProRes 4444) keep transparency; MP4 does not. `x`, `y` accept numbers or FFmpeg expressions (`W`, `H` = frame size, `w`, `h` = overlay size). `w` resizes the overlay. `fade` in seconds.
- Picture-in-picture: put the screen share as a cutaway and the speaker as an overlay at the same time (the third overlay above), or the other way round.
- Layers are drawn in order: cutaways first, then overlays, then captions on top.

Preview a section before the full render: `python assemble.py --timeline ... --out 02_work/preview.mp4 --preview 0:10-0:40`.
