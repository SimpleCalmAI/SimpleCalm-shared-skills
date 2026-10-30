#!/usr/bin/env python3
"""Build release ZIPs for a plugin.

Usage:
  python scripts/build_release.py list
      Print a JSON array of {name, version, description, skills} for every plugin.
  python scripts/build_release.py build PLUGIN OUT_DIR
      Write PLUGIN-plugin.zip (the whole plugin, under PLUGIN-plugin/) and one
      SKILL-skill.zip per skill (the skill folder, under SKILL/) to OUT_DIR.
  python scripts/build_release.py build-all OUT_DIR
      Do that for every plugin.
  python scripts/build_release.py plan TAGS_FILE
      Given a file of existing tag names, print JSON: the release tag (vYYYY.MM.DD, with
      .2, .3 ... for later releases the same day), title, notes body, and the
      <plugin>-v<version> tags that do not exist yet (publish only if there are any).

The ZIPs are reproducible: sorted entries, fixed timestamps, no local junk files.
Everything except `plan` is stdlib only; `plan` also needs PyYAML.
"""

import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
SKIP_NAMES = {".DS_Store", "Thumbs.db"}
SKIP_DIRS = {"__pycache__", ".git"}
SKIP_SUFFIXES = {".pyc", ".zip"}
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def plugin_dirs():
    return sorted(p for p in PLUGINS.iterdir() if (p / "plugin.json").is_file())


def skills_of(plugin_dir):
    skills = plugin_dir / "skills"
    return sorted(p.name for p in skills.iterdir() if (p / "SKILL.md").is_file()) if skills.is_dir() else []


def files_under(directory):
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if (path.is_file() and path.name not in SKIP_NAMES and path.suffix not in SKIP_SUFFIXES
                and not SKIP_DIRS.intersection(relative.parts)):
            yield path, relative


def write_zip(zip_path, source_dir, top_folder):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, relative in files_under(source_dir):
            info = zipfile.ZipInfo(f"{top_folder}/{relative.as_posix()}", FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def main(argv):
    if argv[:1] == ["list"]:
        out = []
        for plugin_dir in plugin_dirs():
            manifest = json.loads((plugin_dir / "plugin.json").read_text(encoding="utf-8"))
            out.append({"name": manifest["name"], "version": manifest["version"],
                        "description": manifest.get("description", ""), "skills": skills_of(plugin_dir)})
        print(json.dumps(out))
        return 0
    if len(argv) == 3 and argv[0] == "build":
        if not (PLUGINS / argv[1] / "plugin.json").is_file():
            sys.exit(f"No such plugin: {argv[1]}")
        build_plugin(PLUGINS / argv[1], Path(argv[2]))
        return 0
    if len(argv) == 2 and argv[0] == "build-all":
        for plugin_dir in plugin_dirs():
            build_plugin(plugin_dir, Path(argv[1]))
        return 0
    if len(argv) == 2 and argv[0] == "plan":
        print(json.dumps(plan(Path(argv[1]).read_text(encoding="utf-8").split())))
        return 0
    sys.exit(__doc__)


def build_plugin(plugin_dir, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    write_zip(out_dir / f"{plugin_dir.name}-plugin.zip", plugin_dir, f"{plugin_dir.name}-plugin")
    for skill in skills_of(plugin_dir):
        write_zip(out_dir / f"{skill}-skill.zip", plugin_dir / "skills" / skill, skill)


def skill_version(skill_md):
    import yaml  # only needed for planning; installed in CI from scripts/requirements.txt

    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", skill_md.read_text(encoding="utf-8"), re.DOTALL)
    metadata = (yaml.safe_load(match.group(1)) or {}).get("metadata") if match else None
    return metadata.get("version", "unversioned") if isinstance(metadata, dict) else "unversioned"


def plan(existing_tags):
    """Decide what to publish. `existing_tags` are the repository's tag names."""
    tags = set(existing_tags)
    plugins = []
    for plugin_dir in plugin_dirs():
        manifest = json.loads((plugin_dir / "plugin.json").read_text(encoding="utf-8"))
        skills = [{"name": s, "version": skill_version(plugin_dir / "skills" / s / "SKILL.md")}
                  for s in skills_of(plugin_dir)]
        plugins.append({"name": manifest["name"], "version": manifest["version"],
                        "description": manifest.get("description", ""), "skills": skills,
                        "tag": f"{manifest['name']}-v{manifest['version']}"})
    new = [p for p in plugins if p["tag"] not in tags]

    today = datetime.now(timezone.utc)
    tag, title, count = f"v{today:%Y.%m.%d}", f"SimpleCalm shared skills {today:%Y-%m-%d}", 1
    while tag in tags:
        count += 1
        tag, title = f"v{today:%Y.%m.%d}.{count}", f"SimpleCalm shared skills {today:%Y-%m-%d} ({count})"

    lines = ["## Plugins and skills in this release", ""]
    for p in plugins:
        marker = " (new)" if p in new else ""
        lines.append(f"- **{p['name']}** {p['version']}{marker}: {p['description']}")
        for s in p["skills"]:
            lines.append(f"  - skill `{s['name']}` {s['version']}")
    lines += ["", "Each plugin has its own README with instructions, in `plugins/<plugin>/README.md`.", "",
              "## Downloads", "",
              "- `<plugin>-plugin.zip`: a whole plugin, with its skills.",
              "- `<skill>-skill.zip`: a single skill, for example to upload in the Claude app.", ""]
    return {"release_tag": tag, "title": title, "body": "\n".join(lines),
            "new_plugin_tags": [p["tag"] for p in new]}


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
