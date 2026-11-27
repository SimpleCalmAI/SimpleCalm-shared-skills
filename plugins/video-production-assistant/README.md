<!-- Copyright 2026 SimpleCalm Labs Ltd and contributors. SPDX-License-Identifier: Apache-2.0 -->

# Video Production Assistant

An agent skill that turns raw recordings into a finished video. You record. Your AI agent cuts, assembles and renders with command-line tools, one approved step at a time.

It suits talking-head recordings, screen shares, voiceover over visuals, or a mix. It works with footage from any source, such as StreamYard, Zoom, Loom, OBS or a phone.

Paths in this file, such as `install/` and `scripts/`, are inside the skill folder: [`skills/video-production-assistant/`](skills/video-production-assistant/) here, or wherever your agent installed the skill.

## What you can do with it

### Edit

- Give it a recording and say what you want. It transcribes, plans the cut and edits. You approve at each key step, or tell it to "just do it".
- It removes long pauses, ums and ers, false starts and retakes. Each cut is checked against the real audio, so word endings are not clipped.
- You see a plain-English cut list before anything is rendered: the old length, the new length and what was removed.
- It makes its own word-by-word transcript, free and private, on your computer. ElevenLabs is an option for poor audio or several speakers.
- It handles talking head, screen share, voiceover over visuals, or a mix, from any source.
- It checks your footage first and reports problems: a wrong frame rate, low audio, mismatched sizes.

### Polish

- Titles, lower thirds, chapter cards and code callouts in your brand colours and fonts.
- Cutaways and picture-in-picture, placed on the exact spoken line.
- Simple animated diagrams, and 3D ones with Blender.
- Voice set to a standard loudness, light noise clean-up, and music that dips under speech automatically.
- Music from your own licensed tracks, with a licence log and a reminder of any credit line. Or music generated with ElevenLabs.
- Captions re-timed to the cut: burned in for social video, plus an `.srt` file for YouTube. Keywords can be highlighted.
- Landscape, vertical or square output.
- A quality check before you watch: loudness, peaks, black frames, length, and a contact sheet of frames.

### Plan before you record

- A script with a hook, chapters and a shot list.
- With vidIQ: what people search for, which videos beat their channel's average and why, and what viewers ask.
- A synthetic voiceover with ElevenLabs, if you want one.

### Gets better each time

- Your review notes become dated house rules, so the next video starts from them.
- With vidIQ, a monthly review of how your videos did, with proposed rule changes.

### You stay in control

- Your original recordings are never changed, moved or deleted. Each export is saved as a new version. Nothing is published, uploaded or sent unless you ask.
- It runs on your own computer. Nothing is uploaded by default.
- Paid services are used only after you say yes, each time. API keys stay out of the chat.
- It is free to start: only FFmpeg and Python are needed.
- Set-up help is included: a read-only tool check, installers that ask first, and an uninstaller.
- It works on Windows, Mac and Linux, with any agent that loads skills and can run commands.

### Why use it

- No video editor to learn, and no scrubbing through a timeline.
- The same look and sound on every video.
- Your footage stays private.
- One folder holds every video, your house rules and your brand.

### What it is not good at

Judgement calls, such as which of two takes is better, or comic timing. It flags these for you to decide.

## How it works

The agent edits by transcript. A word list with timings shows where the speech is, so pauses, filler words and retakes can be found and cut without scrubbing through the video. Every cut is checked against the real audio, and you see a plain-English cut list before anything is rendered.

| Step | What happens | You approve |
|---|---|---|
| 0 | Set-up check (once per computer) | |
| 1 | Brief and project folder | The brief |
| 2 | Plan and script (optional, before recording) | The script |
| 3 | Bring in footage and inspect it | |
| 4 | Transcript | |
| 5 | Rough cut plan: pauses, fillers, retakes | The cut list |
| 6 | Render the rough cut and preview it | The rough cut |
| 7 | B-roll and graphics | The plan |
| 8 | Audio polish: voice level, music, ducking | |
| 9 | Captions | |
| 10 | Final assembly and quality check | The final video |
| 11 | Your review notes become house edit rules | The rule changes |

## What you need

Essential:

- An AI agent that loads skills and can run commands on your computer, such as Claude Code.
- FFmpeg with ffprobe.
- Python 3.9 or later.

Optional, each for one job:

| Tool | Used for |
|---|---|
| Local Whisper (faster-whisper) | Free, private transcripts on your own computer |
| Node.js 22 or later | Titles, lower thirds and callouts with the HyperFrames CLI |
| Blender | 3D diagrams |
| yt-dlp | Outside clips you have the right to use |
| uv | Running the ElevenLabs connector on your computer |

## Install the skill

### Claude Code (as a plugin)

Inside Claude Code, run:

```
/plugin marketplace add SimpleCalmAI/SimpleCalm-shared-skills
/plugin install video-production-assistant@simplecalm-shared-skills
```

From a terminal, the same two steps are `claude plugin marketplace add SimpleCalmAI/SimpleCalm-shared-skills` and `claude plugin install video-production-assistant@simplecalm-shared-skills`. Start a new session, then ask Claude to edit a recording.

### Codex and other coding agents

Run this in a terminal (Git Bash, PowerShell, Terminal), not inside the agent. It needs [Node.js](https://nodejs.org); see the [skills installer](https://github.com/vercel-labs/skills) for details.

```
npx skills add SimpleCalmAI/SimpleCalm-shared-skills --skill video-production-assistant -g
```

Choose your agents when asked. The `-g` installs the skill for your whole user account. Restart your agent afterwards.

### By hand

Copy the [`skills/video-production-assistant/`](skills/video-production-assistant/) folder into a place your agent reads skills from, keeping the folder name.

- Claude Code, for all your projects: `~/.claude/skills/video-production-assistant/`
- Claude Code, for one project: `<project>/.claude/skills/video-production-assistant/`
- Other agents: `.agents/skills/video-production-assistant/`, or the skills folder your agent documents.

Skills load when a session starts. Open a new session after installing.

The skill edits on your own computer, where your recordings are, so it works best in an agent that can run commands there, such as Claude Code or Codex. A skill ZIP for the Claude app is on the [releases page](https://github.com/SimpleCalmAI/SimpleCalm-shared-skills/releases), but there it needs a shell connector such as Desktop Commander, or your agreement to upload files to a cloud workspace.

## Install the tools

You can install the tools yourself with the single lines in `references/tools-setup.md`, or use the installers. Always start with the dry run. It only reads, and prints what would happen.

Windows (PowerShell, uses winget):

```powershell
install\install.ps1 -DryRun
install\install.ps1
```

Mac (Homebrew) and Debian or Ubuntu Linux (apt):

```sh
sh install/install.sh --dry-run
sh install/install.sh
```

Add options with `-With node,uv,blender,ytdlp` (Windows) or `--with node,uv,blender,ytdlp` (Mac and Linux).

What the installers do and do not do:

- They ask before each install and show the command first. With no one at the terminal they install nothing unless given `-Yes` or `--yes`.
- They never install a second copy. A tool you already have is left alone, including tools held by version managers such as NVM, fnm, Volta, pyenv or conda.
- They never upgrade or replace anything. A tool that is too old gets a message with the fix, and nothing else happens.
- They list what they installed in `installed.txt` in your own user folder, so the uninstaller removes only those tools.

To see the state of your tools at any time without changing anything:

```sh
python scripts/doctor.py
```

### Windows: winget source terms

On Windows, `doctor.py`, the dry run and the uninstaller ask winget what is installed, using `winget list --accept-source-agreements`. That accepts the terms of winget's package sources for you, even on a run that installs nothing. A real install also passes `--accept-package-agreements` for the package you said yes to.

## First use

Ask your agent to edit a recording, for example: "Edit my StreamYard recording into a training video."

On first use the agent offers to set up your video library. This is one folder that holds every video, your house edit rules and a copy of the scripts. It asks first, and it never overwrites a file that is already there.

## Paid services (all optional)

The skill works with FFmpeg and local Whisper alone. These services add to it, and each costs money or credits:

| Service | Adds |
|---|---|
| ElevenLabs | Better word timings, voice clean-up, music, text-to-speech |
| vidIQ | YouTube keyword and competitor research |
| HeyGen HyperFrames (hosted) | Cloud rendering of graphics |

See `references/connectors.md` for what each costs and how to add it. API keys go in `.env.local` in your video library or in your agent's own settings. Never paste a key into a chat.

## What leaves your computer

- By default, nothing. Editing runs on your own computer because recordings are large.
- Local Whisper downloads a speech model once (0.5 to 1.5 GB). Your audio stays on your computer.
- ElevenLabs transcription sends the audio, never the video, and only after you say yes for that file.
- Other connectors send what you ask them to. The agent says what it will send before the first call.

## Use only media you have rights to

The skill is written to use your own footage, music you have a licence for, and graphics made on your computer. It keeps a log of music licences. It uses yt-dlp only for your own channel, clips whose licence allows reuse, or clips you have written permission to use. The rules are in `references/sources.md`.

You are responsible for the rights to everything in your videos.

## Removing it

```powershell
install\uninstall.ps1
```

```sh
sh install/uninstall.sh
```

The uninstaller removes only the tools the installers added, asking before each one. It then prints what it leaves for you to remove by hand: local Whisper files in each video library, connector entries, download caches and the skill folder itself. Details are in `references/tools-setup.md`.

## Status

This is an early release. The installers are new and have had little testing on real Macs. Start with the dry run and read what it prints before you agree to anything.

## Licence

Version 0.1.0. Copyright 2026 SimpleCalm Labs Ltd (trading as SimpleCalm AI) and contributors.

Apache License 2.0. See the [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE) files.

The skill installs or calls other software, including FFmpeg, Python, Node.js, Blender, yt-dlp, uv, faster-whisper and HyperFrames. Each comes from its own source under its own licence. None of it is bundled here.

This project is not affiliated with or endorsed by StreamYard, ElevenLabs, vidIQ or HeyGen. Their names are used only to say what the skill works with.
