# Tools set-up

Give the user one tool at a time: what it does, the one install line, how to check it worked. Do not run installs yourself unless they ask. After set-up, record the toolkit in `edit_rules.md`.

Everything here is free software. The paid, optional services are in `connectors.md`.

## The quick way: this skill's installers

This skill ships two installers in its `install/` folder. Both install the essentials by default, take a list of options, and have a dry-run mode that only prints what they would do.

- Windows (PowerShell, uses winget), from the skill folder: `install\install.ps1 -DryRun`, then `install\install.ps1`, or `install\install.ps1 -With node,uv,blender,ytdlp`, or `-All`.
- Mac and Linux (uses Homebrew, or apt on Debian and Ubuntu): `sh install/install.sh --dry-run`, then `sh install/install.sh`, or `--with node,uv,blender,ytdlp`, or `--all`.

What the installers will and will not do:
- **One set of rules.** `scripts/doctor.py` does every check; the installers only act on its answers. Minimum versions (Node.js 22, Python 3.9) are in `scripts/min_versions.txt`.
- **Never a second copy.** A tool already present by any method is left alone: on PATH (on Windows as a program or a `.cmd`/`.bat` launcher, such as `npx.cmd` or pyenv-win's `python.bat`); in a version manager (NVM, nvm-windows, fnm, mise, asdf, Volta, n, pyenv), even when it is not loaded in the shell; in conda, `~/.local/bin`, pip `--user` (`~/Library/Python/3.x/bin` on a Mac); as a Python module (`yt-dlp`); or installed by the package manager but not on PATH. If any Node version manager is present, Node is never installed with Homebrew or apt: the installer gives the version manager's command instead.
- **Minimum versions are checked**: Node.js, Python, FFmpeg with ffprobe (and a note if the `subtitles` filter is missing), uv with `uvx` beside it, git that actually runs.
- **Nothing is upgraded or replaced.** A tool that is too old, incomplete or not on PATH gets `[too old]`, `[incomplete]` or `[not on PATH]` with the fix (for example `nvm install 22`), and nothing else happens. Pass that advice to the user; do not work around it by installing another copy.
- **Asks first.** Before each install it shows the command and what the package manager would add, and waits for a yes. With no terminal (for example when an agent runs it) it installs nothing unless given `--yes` (`-Yes`).
- **Homebrew stays as it is.** Installs run with `HOMEBREW_NO_AUTO_UPDATE`, `HOMEBREW_NO_INSTALL_UPGRADE`, `HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK` and `HOMEBREW_NO_INSTALL_CLEANUP`, so Homebrew does not update itself, upgrade your other formulae or delete old versions. It can still upgrade a shared library the new tool needs; the preview shows that before you say yes.
- **Apple's placeholders are left alone.** Without the Xcode Command Line Tools, `/usr/bin/python3` and `/usr/bin/git` only open Apple's installer, so they are never run and count as missing.
- **Dry-run only reads.** A second real run changes nothing.

`doctor.py` is the read-only way to see the state at any time.

## Removing everything

The installers list each tool they install in `installed.txt` in the user's own folder: `~/.local/state/video-production-assistant/` on Mac and Linux, `%LOCALAPPDATA%\video-production-assistant\` on Windows. It is kept outside the skill folder so that updating the skill does not lose it. `sh install/uninstall.sh` (Windows: `install\uninstall.ps1`) removes only those, asking before each one, then offers to remove libraries Homebrew or apt pulled in only for them. Tools the user had before are never on the list. If other apt packages have since come to depend on a tool, removing it would remove them too: that is asked at the terminal and `--yes` does not cover it. It also prints what it cannot remove safely on its own: each library's `_tools/venv` and `_tools/models`, connector entries (`setup_connectors.py --remove all --target FILE`), uv's and npx's download caches, and the skill folder itself.

Or give the user the single lines below. Before any of them, check the tool is not already there in an older version or under a version manager; if it is, upgrade it the way it was installed.

## Essential

### FFmpeg (cuts, renders, audio, captions)
- Windows: `winget install --id Gyan.FFmpeg -e` then open a new terminal. Check: `ffmpeg -version`.
- Mac: `brew install ffmpeg`. Linux: `sudo apt install ffmpeg`.
- The `subtitles` filter needs an FFmpeg build with libass. The Gyan "full" and "essentials" builds have it. Check: `ffmpeg -filters | findstr subtitles` (Windows) or `| grep subtitles`.

### Python 3.9+ (runs the bundled scripts)
- Windows: `winget install --id Python.Python.3.12 -e`. Check: `python --version` or `py --version`.
- Mac: `brew install python`. Linux: `sudo apt install python3 python3-venv`.
- Optional: `python -m pip install pillow` for labelled contact sheets.

## Optional, by job

### Transcripts - local Whisper (free, private)
- Optional. Without it, transcripts come from ElevenLabs (paid) or `npx hyperframes transcribe`.
- Recommended: let `init_library.py --venv` make `_tools/venv` and install `faster-whisper` from `_tools/requirements.txt` into it. It says what it will download and asks first. Then run `transcribe_local.py` with that Python.
- By hand, keeping it inside the library: `python -m venv _tools/venv`, then `_tools/venv/bin/python -m pip install --no-cache-dir -r _tools/requirements.txt` (Windows: `_tools\venv\Scripts\python.exe`). Do not install it into the system Python.
- First run downloads the model into `_tools/models` (about 1.5 GB for `medium`, 0.5 GB for `small`). On a machine with 8 GB of memory use `small.en`. Deleting `_tools/venv` and `_tools/models` removes local Whisper completely. A model that an earlier version of the skill already downloaded to `~/.cache/huggingface/hub` is used from there and not downloaded again.

### Graphics - HyperFrames (HeyGen, open source)
Writes titles, lower thirds, chapter cards and callouts as HTML and renders them to video.
- Needs Node.js 22+; check `node --version`. If the user has NVM (or fnm, Volta): `nvm install 22`, never a second Node from Homebrew or winget. Otherwise: Windows `winget install --id OpenJS.NodeJS.LTS -e`; Mac `brew install node`.
- Local CLI (used by this skill, nothing to install first): `npx hyperframes init <name>`, `npx hyperframes preview`, `npx hyperframes render`. The agent skills can be added with `npx skills add heygen-com/hyperframes`.
- In Windows PowerShell, if `npx` is blocked by the script policy, type `npx.cmd` instead.

### 3D diagrams - Blender
- Windows: `winget install --id BlenderFoundation.Blender -e`. Mac: `brew install --cask blender`. Add the install folder to PATH or call it by full path. Check: `blender --version`.
- Only worth installing if the user wants 3D concept animations. Most training diagrams are clearer as flat HyperFrames graphics.

### Outside clips - yt-dlp
- `python -m pip install -U yt-dlp` (or `winget install yt-dlp.yt-dlp`, `brew install yt-dlp`). Check: `yt-dlp --version`.
- Read the rights rules in `sources.md` before using it.

### uv (only to run the ElevenLabs connector on the user's computer)
- Windows: `winget install --id astral-sh.uv -e`. Mac: `brew install uv`. Check: `uv --version` and `uvx --version` (a uv without `uvx` is too old; update it the way it was installed).

## Where the work runs

- **Shell on the user's computer** (the agent's own shell, or a shell connector such as Desktop Commander): preferred. Large files stay local.
- **Cloud workspace**: only if the user agrees to upload. Upload limits make it a poor fit for recordings over a few hundred MB. Outbound internet is often restricted there, so ElevenLabs and yt-dlp may only work through connectors.
- Slow machines: a laptop without a dedicated graphics card renders at roughly real time or slower. Run long jobs in the background with a log file. Note the machine and its limits in `edit_rules.md` under Toolkit.
