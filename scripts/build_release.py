#!/usr/bin/env python3
"""Build release ZIPs for a plugin.

Usage:
  python scripts/build_release.py list
      Print a JSON array of {name, version, description, skills} for every plugin.
  python scripts/build_release.py build PLUGIN OUT_DIR
      Write PLUGIN-plugin.zip (the whole plugin, under PLUGIN-plugin/) and one
      SKILL-skill.zip per skill (the skill folder, under SKILL/) to OUT_DIR.

The ZIPs are reproducible: sorted entries, fixed timestamps, no local junk files.
Stdlib only.
"""

import json
import sys
import zipfile
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
        plugin, out_dir = argv[1], Path(argv[2])
        plugin_dir = PLUGINS / plugin
        if not (plugin_dir / "plugin.json").is_file():
            sys.exit(f"No such plugin: {plugin}")
        out_dir.mkdir(parents=True, exist_ok=True)
        write_zip(out_dir / f"{plugin}-plugin.zip", plugin_dir, f"{plugin}-plugin")
        for skill in skills_of(plugin_dir):
            write_zip(out_dir / f"{skill}-skill.zip", plugin_dir / "skills" / skill, skill)
        return 0
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
