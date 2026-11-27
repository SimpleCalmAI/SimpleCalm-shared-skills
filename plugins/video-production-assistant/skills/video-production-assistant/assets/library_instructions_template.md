# {{BRAND}} video production - library instructions

<!-- Written by init_library.py on {{DATE}}. This file is yours: edit it to suit how you work.
     AGENTS.md and CLAUDE.md hold the same text so that any agent finds it. Keep them in step. -->

## Purpose
Produce polished videos{{FOR_BRAND}}: training videos, social clips, talk recordings. Footage can come from any source (StreamYard, Zoom, OBS, phone, screen recorder).

## How to work
- Use the `video-production-assistant` skill for every edit, plan or script. Follow its steps and gates.
- Do the editing on the user's own computer, inside this folder. Do not upload large recordings to the cloud unless the user agrees.
- Read `edit_rules.md` before any edit. Its rules beat the skill defaults. Create it from the skill template if it is missing.
- Change `edit_rules.md` only after the user agrees. Add the date to each change.

## Folder layout
```
<this folder>/
  AGENTS.md, CLAUDE.md  these instructions
  edit_rules.md      house style and lessons learned
  _tools/            the skill's scripts (copied {{DATE}})
  _inbox/            the user drops new recordings here
  _brand/            logos, fonts, intro/outro, brand.md
  _music/            licensed music only (note the licence in _music/LICENCES.md)
  _templates/        brief template
  _archive/          finished video folders, moved here by the user
  YYYY-MM-DD_slug/   one folder per video
    01_raw/          originals - never change or delete
    02_work/         transcripts, cut lists, test renders
    03_assets/       B-roll, graphics, music, logos
    04_exports/      finished videos, _v1, _v2 ...
    brief.md         the agreed brief
```

## Starting a new video
1. Make `YYYY-MM-DD_slug/` with the four sub-folders.
2. Copy `_templates/brief_template.md` to `brief.md` and fill it in with the user.
3. Copy (do not move) the recordings from `_inbox/` into `01_raw/`.
4. After the copy is checked, tell the user. They remove the `_inbox` copy themselves.

## Rules
- The user approves before each costly step: cut list, rough cut, B-roll plan, final.
- Never change, move or delete files in `01_raw`.
- Never overwrite an export. Save each version as a new file.
- Never publish, upload or send a video. The user does that.
- Use only the user's own footage, licensed music and media, or graphics made here. No downloads of other creators' videos.
- Ask before using paid credits (ElevenLabs, vidIQ, HeyGen or any other paid service).
- Keep API keys in `.env.local`. Never ask for a key in chat, print one or commit one.
- Use the brand in `_brand/` (colours, fonts, logo) for titles and lower thirds, once `_brand/brand.md` is filled in.

## Talking to the user
<!-- Defaults. Change the length limit and tone to taste. -->
- Start with a short plain-English overview. Lead with what it means for the video.
- Narrate as you go: before each action, one line on what you are about to do and why; after it, one line on what happened. At each approval point, say what you need from the user.
- Keep replies to one paragraph of 100 words or fewer unless the user asks for more.
- Short sentences. One action per step. Explain any technical term.
- Challenge weak ideas. If unsure, say so and ask one question.
