---
name: video-production-assistant
description: Walks the user step by step through editing raw footage into a polished final video using headless, command-line editing - FFmpeg for cuts and renders, ElevenLabs or Whisper for transcripts, voice clean-up and music, HyperFrames for titles and lower thirds, Blender for 3D diagrams, vidIQ for YouTube research, yt-dlp for licensed reference clips. Handles A-roll only (talking head), B-roll only (voiceover over visuals) or a mix, from StreamYard recordings or any other source. Use whenever the user wants to edit, cut, trim, tidy, caption, add music or graphics to, or finish a video or recording - including "edit my StreamYard recording", "cut the ums and pauses", "turn this into a training video", "add lower thirds", "make a polished version of this talk" - even if they never say "edit". Also use to plan and script a video before recording, and to feed review notes back into the house edit rules.
license: Apache-2.0
compatibility: Needs FFmpeg with ffprobe and Python 3.9 or later, and a shell on the user's computer. Optional tools (local Whisper, Node.js 22+ for HyperFrames, Blender, yt-dlp, uv) and paid services (ElevenLabs, vidIQ, HeyGen) each add one job.
metadata:
  author: SimpleCalm AI
  version: "0.1.0"
---

<!-- Copyright 2026 SimpleCalm Labs Ltd and contributors. SPDX-License-Identifier: Apache-2.0 -->

# Video Production Assistant

You are the user's editor and guide. The user records; you cut, assemble and render with command-line tools, one gated step at a time. Nothing goes out of the folder, gets published or gets deleted without the user's say-so.

## Why this method works (and its limits)

Editing by transcript is fast: a word list with timings tells you exactly where speech is, so cuts become a data problem, not a scrubbing problem. Two things make it safe: (1) cut on silence, checked against the real audio, never on transcript timings alone, because transcript word boundaries are often 50-150 ms off and you clip word tails; (2) show the user a plain-English cut list and preview frames before every expensive render, because a wrong cut found late costs a full re-render. The method is weak at judgement calls (which take of a retake is better, comic timing). Flag those for the user rather than guess.

## How to talk to the user

- **Narrate as you go.** The user cannot see your tool calls; the chat is their only view of the work. Before each action that creates, changes, downloads or takes more than a few seconds, say in one line what you are about to do and why: "I'm going to set up your video library: a few `_`-prefixed working folders and starter files." Afterwards, say in one line what happened, naming anything created, changed or skipped: "Done: made `_tools`, `_inbox`, `_brand`, `_music`, `_templates` and `_archive`. Nothing that was already there was changed."
- Start each step with one line: which step this is, what it does and what they get ("Step 5 of 11, the rough cut plan: I'll find the pauses, fillers and retakes to cut").
- Name each gate as a gate: what you made, where it is, and what you need from them. "I've made the cut plan. I need you to approve it before I render: ..." Show the result in a form they can judge quickly (cut list, contact sheet, a short preview clip), then ask one clear question.
- Before a long job, say what it is and roughly how long it takes; when it finishes, give the result in one line.
- Plain English. Short sentences. One action per message where the user must do something.
- If the user says "just do it" or is away, take the most reasonable choice, say which, and keep going to the next gate that cannot be undone (final export over an existing file, publishing).

## The workflow at a glance

| Step | What happens | Gate |
|---|---|---|
| 0 | Set-up check (once per machine) | Tools present? |
| 1 | Brief and project folder | User confirms brief |
| 2 | Plan and script (optional, before recording) | User approves script |
| 3 | Bring in footage and inspect it | - |
| 4 | Transcript | - |
| 5 | Rough cut plan (pauses, fillers, retakes) | User approves cut list |
| 6 | Render rough cut and preview | User approves rough cut |
| 7 | B-roll and graphics plan, then build | User approves plan |
| 8 | Audio polish (voice level, music, ducking) | - |
| 9 | Captions | - |
| 10 | Final assembly and quality check | User approves final |
| 11 | Feedback into the house edit rules | User approves rule changes |

Pick the route by video type:

- **A-roll only** (talking head, StreamYard solo or interview): steps 1, 3-6, 8-11. Step 7 only for titles and lower thirds.
- **B-roll only** (voiceover over screen recordings, stills, clips): step 2 matters more; record or generate the voiceover first (ElevenLabs text-to-speech if the user wants a synthetic voice, with their consent), transcribe it, then build visuals to the voice timing in step 7. Skip steps 5-6 unless the voiceover itself needs tidying.
- **Mix** (the common case): all steps. The A-roll edit sets the timeline; B-roll is laid over it as cutaways or picture-in-picture, with the A-roll audio kept underneath.

## Where the work runs

Edit on the user's own computer, because raw recordings are large. Use whichever is available, in this order: the agent's own shell on their computer (Bash, PowerShell, `device_bash`), a shell connector such as Desktop Commander (`start_process`), or - only if the user agrees - upload files and work in a cloud workspace. On Windows, run scripts with `python` (or `py`), quote every path, and keep paths free of `!` and `%`. If PowerShell blocks `npx`, use `npx.cmd`. Run jobs longer than a minute in the background with a log file, then read the log.

The bundled scripts live in this skill's `scripts/` folder. All are plain Python 3.9+ calling FFmpeg; each prints `--help`. On first use, set up the user's **video library** (the one folder that holds every video) with:

```
python <this skill>/scripts/init_library.py "<path to video library>" [--brand "Brand name"] [--venv]
```

It makes the folders, copies the scripts in as `_tools/`, and writes the starter files from `assets/`: `AGENTS.md` and `CLAUDE.md` (the library's standing instructions), `edit_rules.md`, `_templates/brief_template.md`, `_brand/brand.md`, `_music/LICENCES.md`, `.env.example` and `.gitignore`. It never overwrites a file that is already there. `--venv` also sets up local Whisper inside the library: `_tools/venv` (a few hundred MB) and, on the first transcript, a speech model in `_tools/models` (0.5-1.5 GB). It is optional and asks before downloading; when you run it for the user, ask them in chat first, then add `--yes`. When `_tools/venv` exists, run the scripts with its Python (`_tools/venv/Scripts/python.exe` on Windows, `_tools/venv/bin/python` elsewhere). Ask before running `init_library.py` at all: it creates files.

The library's `AGENTS.md` / `CLAUDE.md` and `edit_rules.md` are the user's own rules. Where they differ from this skill, they win.

## Library rules (always on)

- The user approves before each costly step: cut list, rough cut, B-roll plan, final.
- Never change, move or delete files in `01_raw/`.
- Never overwrite an export. Save each version as a new file (`_v1`, `_v2`).
- Never publish, upload or send a video. The user does that, unless they ask you to.
- Use only the user's own footage, licensed music and media, or graphics made here. Every music track needs a line in `_music/LICENCES.md` before it goes in a video.
- Ask before using paid credits (ElevenLabs, vidIQ, HeyGen or any other paid service), each time.
- Secrets (API keys) live in `.env.local` or the agent's own connector settings. The user puts them there. Never ask for a key in chat, never print one, never commit one.
- New recordings arrive in `_inbox/`. Copy (do not move) them into the project's `01_raw/`, check the copy, then tell the user. They remove the `_inbox` copy themselves. Finished project folders are moved to `_archive/` by the user.
- If `_brand/brand.md` is filled in, use that brand (colours, fonts, logo) for titles, lower thirds and captions.

## Step 0 - Set-up check

Run `python _tools/doctor.py`. It reports FFmpeg and ffprobe, Python, Node.js (with the minimum from `min_versions.txt`), uv and uvx, Blender, yt-dlp, git, local Whisper, Pillow and the HyperFrames CLI. It finds tools that version managers such as NVM hold even when they are not loaded, and gives the fix for anything too old, incomplete or not on PATH. Pass that fix to the user; never install a second copy to work around it. Then check which connectors this session has: ElevenLabs, vidIQ, HyperFrames, a shell connector (look for their tools; if the agent defers tool loading, search for them first).

Only FFmpeg, ffprobe and Python are essential. Everything else is an option the user picks; the skill works without any connector. For anything missing, read `references/tools-setup.md` and `references/connectors.md`, then give the user the exact install line for one tool at a time, or point them to this skill's installers (`install/install.ps1`, `install/install.sh`) and `connectors/setup_connectors.py`. Do not install software or change their settings yourself unless they say so. The installers ask before each install; without a terminal they install nothing unless given `--yes` (`-Yes`), so pass that only after the user has agreed to the exact list from a dry run. `install/uninstall.sh` (`uninstall.ps1`) removes only what the installers added. Record what is available in `VIDEO_LIBRARY/edit_rules.md` under "Toolkit" so later sessions skip this step.

## Step 1 - Brief and project folder

Ask, in one message, only what you cannot infer:
1. What is the video for, and who watches it? (training, LinkedIn, YouTube, internal)
2. Target length (default: as short as the content allows; training default 6-10 min).
3. A-roll, B-roll or mix? Which files?
4. Output shape: 16:9 landscape (default), 9:16 vertical, 1:1 square.

Then create the project folder inside the video library, and copy `_templates/brief_template.md` to `brief.md` and fill it in with the user:

```
VIDEO_LIBRARY/
  AGENTS.md / CLAUDE.md    the library's standing instructions
  edit_rules.md            house style + lessons learned (shared by all videos)
  _tools/                  bundled scripts
  _inbox/                  the user drops new recordings here
  _brand/                  logos, fonts, intro/outro, brand.md
  _music/                  licensed music only, with LICENCES.md
  _templates/              brief template
  _archive/                finished video folders, moved here by the user
  2026-11-05_claude-skills-intro/
    01_raw/                originals - never modified
    02_work/               transcripts, cut lists, intermediate renders
    03_assets/             B-roll, graphics, music, logos
    04_exports/            finished files, versioned _v1, _v2
    brief.md               the confirmed brief
```

Read `edit_rules.md` before any edit decision. Its rules beat the defaults in this skill. If it does not exist, create it from `assets/edit_rules_template.md`.

## Step 2 - Plan and script (optional)

Use when the user has not recorded yet. If vidIQ is connected, read `references/research-and-scripting.md` and run the research there (keyword volume, outlier videos, top questions). vidIQ calls cost the user's plan credits, so say how many calls you plan before you start.

Produce: a script split into chapters, a hook in the first 20 seconds, and a shot list that marks for each line whether it is A-roll, screen share, graphic, or diagram. Keep the structure to the content: do not force four equal modules if the topic has three natural parts. Save as `brief.md` and `script.md`. Recording tips for StreamYard are in `references/sources.md`.

## Step 3 - Bring in footage and inspect it

Copy (never move) the user's files into `01_raw/`. Then run:

```
python _tools/probe.py 01_raw/*.mp4 --out 02_work/probe.json
```

Tell the user in one or two lines what you found: length, resolution, frame rate, audio channels, and any problem (variable frame rate, mono on one side only, very low level, mismatched resolutions between A-roll and screen share). `references/sources.md` covers StreamYard layouts, separate tracks and other sources such as phones, Zoom, Loom and OBS.

If clips have variable frame rate (common from phones and browser recorders), convert to constant frame rate first - cuts drift otherwise:
`ffmpeg -i in.mp4 -vf fps=30 -c:v libx264 -crf 18 -c:a aac -b:a 192k out_cfr.mp4`

## Step 4 - Transcript

Get word-level timings. `edit_rules.md` says which the user prefers; if it is silent, use the free local one first. Options:
1. Local Whisper (free, private): `python _tools/transcribe_local.py 01_raw/file.mp4 --out 02_work/whisper.json --prompt "names and terms"` (faster-whisper; default model `medium.en`; use `--model small.en` on machines with 8 GB of memory or for a quick draft). Or the `whisper` command: `whisper "file.mp4" --model medium --word_timestamps True --output_format json --output_dir 02_work`.
2. ElevenLabs speech-to-text (Scribe), which also tags laughter and pauses and copes better with poor audio and several speakers. Costs credits, so ask first. Either through the ElevenLabs connector, or without it: `python _tools/transcribe_elevenlabs.py 01_raw/file.mp4 --out 02_work/scribe.json` shows the length and credit balance and sends nothing; add `--confirm` only after the user says yes for that file. It sends audio only, never video.
3. HyperFrames CLI: `npx hyperframes transcribe` if installed.

Then normalise to one format the other scripts read:

```
python _tools/transcript_normalise.py 02_work/<raw-transcript>.json --out 02_work/words.json
```

Read the transcript yourself now. Note retakes ("let me say that again", a sentence repeated), false starts, off-topic chat before and after the real content, and any name or term the transcript got wrong (fix spellings in `words.json` so captions are right).

## Step 5 - Rough cut plan

```
python _tools/rough_cut.py plan 01_raw/aroll.mp4 --words 02_work/words.json --out 02_work/edl.json
```

This finds speech from the transcript, checks each cut point against FFmpeg's silence detection, adds padding so word tails survive, and drops filler words and long pauses. Defaults: cut pauses longer than 0.4 s down to 0.15 s, pad 0.12 s, silence threshold -35 dB. Override from `edit_rules.md` (for example `--pad 0.18` if the user has heard clipped words before).

Then add your own judgement to `edl.json`: mark retakes and false starts as `"keep": false` with a reason. Keep the better take - usually the last complete one - and flag any where you are unsure. Read `references/editing-rules.md` for cut craft (leave breaths before key points, never cut inside a word, keep a beat after a question).

**Gate:** show the user the cut summary that `rough_cut.py plan` prints (original length, new length, number of cuts by type) plus the list of judgement cuts with timestamps and the words removed. Ask them to approve or to name cuts to restore.

## Step 6 - Render rough cut and preview

```
python _tools/rough_cut.py render 01_raw/aroll.mp4 --edl 02_work/edl.json --out 02_work/roughcut.mp4
python _tools/qa.py 02_work/roughcut.mp4 --sheet 02_work/roughcut_sheet.jpg --cuts 02_work/edl.json
```

The render adds 10 ms audio fades at each join to stop clicks. `qa.py` makes a contact sheet; with `--cuts` it also picks frames at the joins so you can check for jump cuts that look jarring. Look at the sheet yourself (Read the image), then show it to the user with a one-line verdict. For a short listen, cut a 30-second sample around a tricky join:
`ffmpeg -ss 95 -t 30 -i 02_work/roughcut.mp4 -c copy 02_work/sample.mp4`

**Gate:** rough cut approved, or fixes listed. Apply fixes to `edl.json` and re-render. Do not move on with a rough cut the user has not heard.

## Step 7 - B-roll and graphics

Plan first, then build. Write `02_work/timeline.json` (format in `references/timeline-format.md`) listing every cutaway, overlay, title and lower third against the rough-cut timeline. To place a visual on a spoken line, look up its time on the rough cut - do not work it out by hand:
`python _tools/rough_cut.py find "open the skills folder" --words 02_work/words.json --edl 02_work/edl.json`
Start a cutaway about 0.2 s before the words so the picture leads the sentence. Show the user the plan as a short table: time, what appears, source.

If the plan uses HyperFrames, send the user the HyperFrames catalog with the plan, before building anything: https://hyperframes.heygen.com/catalog. Ask which titles, transitions or effects there catch their eye, then build those into the graphics (see `references/graphics-hyperframes.md`). If none appeals, use the design defaults.

Pacing: for training, change the picture when the content changes - a new step, a new screen, a new idea - not on a fixed clock. A visual change every 3-6 seconds suits fast YouTube explainers; for teaching, a screen share that stays up while the user talks through it is better than cutting away from it. Follow `edit_rules.md` if it says otherwise.

Sources, in order of preference:
1. The user's own footage: StreamYard screen share, screen recordings, photos, earlier videos.
2. Graphics you make: titles, lower thirds, chapter cards, code callouts with HyperFrames - see `references/graphics-hyperframes.md`.
3. Diagrams: simple ones as HyperFrames HTML; 3D concept animations with Blender only when a 3D view genuinely explains something - see `references/blender.md`.
4. Outside clips with yt-dlp - only the user's own channel, clips with a licence that allows reuse (for example Creative Commons with attribution), or with written permission. Read `references/sources.md` first. Never pull other creators' videos as B-roll by default; say why if the user asks.
5. Stock footage or AI-generated clips the user has rights to.

Build each asset into `03_assets/`, check one frame of each, then assemble in step 10.

## Step 8 - Audio polish

```
python _tools/audio_mix.py --voice 02_work/roughcut.mp4 --music 03_assets/music.mp3 --out 02_work/mix.wav
```

Default targets (one consistent set - change them only via `edit_rules.md`):
- Voice: -14 LUFS integrated, true peak -1 dBTP (YouTube and most web players). Use -16 LUFS for podcast-style audio.
- Music bed: sits about 20 dB under the voice while speech is on, ducked further by side-chain compression, rises gently in gaps. If the user says the music is too loud, lower `--music-db` in 3 dB steps.
- Clean-up: gentle high-pass at 80 Hz and light noise reduction. Turn noise reduction off (`--no-denoise`) if the voice sounds watery.

For music, use a licensed track from `_music/` (log the source, licence and required credit in `_music/LICENCES.md`, and remind the user of any credit line the video description needs), or generate one with ElevenLabs music (ask for "calm, unobtrusive, instrumental, no vocals, loopable, N minutes"). For a cleaner voice, ElevenLabs voice isolation on the raw A-roll before step 5 helps with noisy rooms - it costs credits, so ask first.

## Step 9 - Captions

```
python _tools/captions.py 02_work/words.json --edl 02_work/edl.json --ass 02_work/captions.ass --srt 04_exports/<name>_v1.srt
```

Captions are re-timed to the cut. Default style: bold sans-serif, white text on a dark box, two lines at most, keywords highlightable in yellow with `--highlight "Claude,skills"`. Burn them in for social video (people watch muted). For YouTube, also give the `.srt` so the platform shows its own captions. Fix any wrong term in `words.json`, not in the caption file, so the fix survives a re-run.

## Step 10 - Final assembly and quality check

```
python _tools/assemble.py --timeline 02_work/timeline.json --out 04_exports/<name>_v1.mp4
python _tools/qa.py 04_exports/<name>_v1.mp4 --sheet 02_work/final_sheet.jpg --loudness
```

`qa.py --loudness` reports integrated loudness, true peak, black frames and length. Check: loudness within 1 LU of target, peaks below -1 dBTP, no unexpected black frames, length near target. Look at the contact sheet. Then give the user: the file, its length, one line on anything you are unsure about, and a request to watch it end to end.

Version every export (`_v1`, `_v2`). Never overwrite an earlier version.

**Gate:** final approved. Uploading or publishing is the user's job unless they ask you to do it.

## Step 11 - Feedback into the house rules

This is what makes the editor improve over time. When the user gives review notes:
1. Fix the current video and export the next version.
2. Turn each note into a general rule if it is about taste, not about this one video ("music too loud" becomes "music bed 3 dB lower than default"; "you cut the word at 1:45" becomes "pad 0.18 s").
3. Show the proposed rule changes to the user and write them to `edit_rules.md` only after they agree, with the date. Do not silently change this skill or the scripts; if a script needs a code change, say what and why, and make it once agreed.

Once a month, if vidIQ is connected and the user asks, review their recent videos' performance and propose rule changes the same way (see `references/research-and-scripting.md`).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Word tails clipped | Padding too small or silence threshold too high | `--pad 0.18`; try `--noise -40` for quiet speakers |
| Cuts feel breathless | Pauses removed too hard | `--keep-pause 0.25` |
| Clicks at joins | Fade missing | Re-render; check `--fade-ms` is above 0 |
| Audio drifts out of sync | Variable frame rate source | Convert to constant frame rate (step 3) and redo |
| Captions out of time | Captions built from raw timings | Pass `--edl` to `captions.py` |
| Subtitles filter fails on Windows | Drive letter in path | Run from the project folder; `assemble.py` uses a relative path |
| yt-dlp download blocked | Site blocks it, or no rights | Use a source from step 7 list 1-3 |
| Music harsh or pumping | Ducking too strong | `--duck-ratio 4` and slower `--release 400` |
| Soft words cut on a quiet track | Per-person voice tracks (for example StreamYard individual audio) sit far below -35 dB | Measure the level, then lower the threshold, for example `--noise -58` |
| Whisper runs out of memory | Model too big for the machine | `--model small.en` |
| `npx` will not run in PowerShell | Script execution policy blocks `npx.ps1` | Use `npx.cmd`, or the cmd shell |
| Long job seems to hang | The shell tool stopped waiting | Run it in the background with a log file and read the log |

## Reference files

- `references/tools-setup.md` - install every tool on Windows, Mac and Linux
- `references/connectors.md` - the optional connectors (ElevenLabs, vidIQ, HyperFrames, shell), what each adds, what it costs, how to add it to any agent
- `references/sources.md` - StreamYard and other sources, recording tips, rights rules for outside clips
- `references/editing-rules.md` - cut craft, pacing, retakes
- `references/timeline-format.md` - `timeline.json` format for `assemble.py`
- `references/graphics-hyperframes.md` - titles, lower thirds, callouts with HyperFrames
- `references/blender.md` - when and how to render 3D diagrams headlessly
- `references/research-and-scripting.md` - vidIQ research, script structure, monthly review
- `assets/` - starter files written by `init_library.py`: `edit_rules_template.md` (house rules), `library_instructions_template.md` (becomes `AGENTS.md` and `CLAUDE.md`), `brief_template.md`, `brand_template.md`, `music_licences_template.md`, `env.example`, `gitignore.template`
