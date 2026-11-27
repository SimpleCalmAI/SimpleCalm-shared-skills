#!/usr/bin/env python3
"""Set up a video library folder for the video production assistant.

Makes the folders, copies the bundled scripts in as _tools/, and writes the starter files
(AGENTS.md, CLAUDE.md, edit_rules.md, brief template, brand sheet, music licence log,
.env.example, .gitignore). Safe to re-run: it never overwrites a file that already exists.

Usage:
  python init_library.py "PATH/TO/VIDEO LIBRARY" [--brand "Brand name"] [--venv] [--update-tools]
  python init_library.py "PATH/TO/VIDEO LIBRARY" --new-video my-video-slug

Options:
  --brand NAME     name used in the starter files (default: none)
  --venv           also create _tools/venv and install local Whisper (large download; asks first)
  --yes            with --venv: go ahead without asking (for agents, after the user said yes in chat)
  --update-tools   refresh the scripts in _tools/ from this skill (the only thing ever overwritten)
  --new-video SLUG make today's project folder YYYY-MM-DD_SLUG with its four sub-folders and brief.md
"""
import argparse
import datetime
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
FOLDERS = ["_tools", "_inbox", "_brand/logos", "_brand/fonts", "_brand/intro-outro",
           "_music", "_templates", "_archive"]
PROJECT_FOLDERS = ["01_raw", "02_work", "03_assets", "04_exports"]


def write_new(path, text, made, kept):
    if path.exists():
        kept.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    made.append(path)


def template(name, brand, today):
    text = (ASSETS / name).read_text(encoding="utf-8")
    return (text.replace("{{BRAND}}", brand or "Video")
                .replace("{{FOR_BRAND}}", f" for {brand}" if brand else "")
                .replace("{{DATE}}", today))


def ask(question):
    """True only for a yes typed at a terminal."""
    if not sys.stdin.isatty():
        print("No one at a terminal to ask, so nothing was installed. If the user agrees, run again with --yes.")
        return False
    return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")


def setup_whisper(tools, yes):
    """Local Whisper lives entirely inside the library: the venv and the speech models."""
    venv = tools / "venv"
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    print()
    print("Local Whisper gives free, private transcripts. It is optional: ElevenLabs (paid) or")
    print("'npx hyperframes transcribe' can make transcripts instead. Setting it up downloads:")
    print(f"  - faster-whisper and its libraries into {venv} (a few hundred MB)")
    print(f"  - a speech model into {tools / 'models'} on the first transcript")
    print("    (about 0.5 GB for small.en, 1.5 GB for medium.en)")
    print("Nothing is installed anywhere else. To remove it all, delete those two folders.")
    if not (yes or ask("Set up local Whisper now?")):
        print("Local Whisper was not set up. Run again with --venv when you want it.")
        return
    if not py.exists():
        print("Creating _tools/venv ...")
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    print("Installing local Whisper and helpers (this can take a few minutes) ...")
    pip = [str(py), "-m", "pip", "install", "--no-cache-dir", "--disable-pip-version-check"]
    subprocess.run(pip + ["--upgrade", "pip"], check=False)
    subprocess.run(pip + ["-r", str(tools / "requirements.txt")], check=True)
    print(f"Run the scripts with: {py}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("library")
    ap.add_argument("--brand", default="")
    ap.add_argument("--venv", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--update-tools", action="store_true")
    ap.add_argument("--new-video", metavar="SLUG")
    a = ap.parse_args()

    lib = Path(a.library).expanduser().resolve()
    today = datetime.date.today().isoformat()
    made, kept = [], []

    if a.new_video:
        if not (lib / "edit_rules.md").exists():
            sys.exit(f"{lib} is not a video library yet. Run init_library.py on it first.")
        proj = lib / f"{today}_{a.new_video.strip().lower().replace(' ', '-')}"
        for sub in PROJECT_FOLDERS:
            (proj / sub).mkdir(parents=True, exist_ok=True)
        brief = lib / "_templates" / "brief_template.md"
        src = brief if brief.exists() else ASSETS / "brief_template.md"
        text = src.read_text(encoding="utf-8") if src.exists() else "# Brief - <video title>\n"
        write_new(proj / "brief.md", text, made, kept)
        print(f"Project folder ready: {proj}")
        print("Next: fill in brief.md with the user, then copy (not move) recordings from _inbox/ into 01_raw/.")
        return

    if not ASSETS.is_dir():
        sys.exit("Starter files not found. Run the copy of init_library.py inside the skill's scripts/ folder "
                 "(the copy in _tools/ only handles --new-video).")
    if HERE == lib / "_tools":
        sys.exit("Run the copy of init_library.py inside the skill, not the one in this library's _tools/.")
    lib.mkdir(parents=True, exist_ok=True)
    for sub in FOLDERS:
        (lib / sub).mkdir(parents=True, exist_ok=True)

    tools = lib / "_tools"
    for src in sorted(HERE.iterdir()):
        if src.suffix not in (".py", ".txt"):
            continue
        dst = tools / src.name
        if dst.exists() and not a.update_tools:
            kept.append(dst)
        else:
            shutil.copy2(src, dst)
            made.append(dst)

    instructions = template("library_instructions_template.md", a.brand, today)
    write_new(lib / "AGENTS.md", instructions, made, kept)
    write_new(lib / "CLAUDE.md", instructions, made, kept)
    write_new(lib / "edit_rules.md", template("edit_rules_template.md", a.brand, today), made, kept)
    write_new(lib / "_templates" / "brief_template.md", template("brief_template.md", a.brand, today), made, kept)
    write_new(lib / "_brand" / "brand.md", template("brand_template.md", a.brand, today), made, kept)
    write_new(lib / "_music" / "LICENCES.md", template("music_licences_template.md", a.brand, today), made, kept)
    write_new(lib / ".env.example", template("env.example", a.brand, today), made, kept)
    write_new(lib / ".gitignore", template("gitignore.template", a.brand, today), made, kept)

    print(f"Video library: {lib}")
    print(f"  written: {len(made)} files   left alone (already there): {len(kept)} files")
    for p in kept:
        print(f"    kept  {p.relative_to(lib)}")

    if a.venv:
        setup_whisper(tools, a.yes)

    print("Next: run doctor.py from _tools/ and record the result in edit_rules.md under Toolkit.")


if __name__ == "__main__":
    main()
