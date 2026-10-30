#!/usr/bin/env python3
"""Validate the plugins and skills in this repository.

Usage:  python scripts/validate.py [REPO_ROOT]

Needs the packages in scripts/requirements.txt (jsonschema, PyYAML).
Exits 1 if any error is found; warnings never fail the run.

Checked against: Agent Plugins 1.0.0 (https://agent-plugins.org), the Agent
Skills specification (https://agentskills.io), the Claude Code marketplace
format, and the discovery rules of the skills CLI (https://github.com/vercel-labs/skills).
"""

import json
import re
import sys
from pathlib import Path

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError as exc:
    sys.exit(
        f"Missing dependency ({exc.name}). Install with: "
        "python3 -m pip install -r scripts/requirements.txt (a virtual environment is recommended)."
    )

SCRIPT_DIR = Path(__file__).resolve().parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED_PREFIXES = ("claude-", "anthropic-", "anthropics-", "cc-plugin-")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
VERSION_LINE = re.compile(r"^Version (\d+\.\d+\.\d+\S*?)\.?(?:\s|$)", re.MULTILINE)
CLAUDE_ONLY = ("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA", "CLAUDE_PROJECT_DIR")

errors: list[str] = []
warnings: list[str] = []


def error(where, message):
    errors.append(f"{where}: {message}")


def warn(where, message):
    warnings.append(f"{where}: {message}")


def load_json(path, root):
    rel = path.relative_to(root)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        error(rel, "file is missing")
    except json.JSONDecodeError as exc:
        error(rel, f"invalid JSON ({exc})")
    return None


def check_schema(instance, schema_file, rel):
    schema = json.loads((SCRIPT_DIR / "schemas" / schema_file).read_text(encoding="utf-8"))
    for problem in sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda e: list(e.path)):
        location = "/".join(str(p) for p in problem.path) or "(top level)"
        error(rel, f"schema violation at {location}: {problem.message}")


def parse_frontmatter(path, rel):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    if not match:
        error(rel, "SKILL.md has no YAML frontmatter")
        return None, text
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        error(rel, f"frontmatter is not valid YAML ({exc})")
        return None, text
    if not isinstance(data, dict):
        error(rel, "frontmatter is not a mapping")
        return None, text
    return data, text[match.end():]


def check_skill(skill_dir, root):
    """Validate one skill directory. Returns its name (or None)."""
    skill_md = skill_dir / "SKILL.md"
    rel = skill_md.relative_to(root)
    meta, body = parse_frontmatter(skill_md, rel)
    if meta is None:
        return None

    name = meta.get("name")
    if not isinstance(name, str) or not name:
        error(rel, "frontmatter 'name' is required")
        name = None
    else:
        if name != skill_dir.name:
            error(rel, f"name '{name}' must match its directory '{skill_dir.name}'")
        if len(name) > 64 or not SKILL_NAME.match(name):
            error(rel, f"name '{name}' must be 1-64 chars of a-z, 0-9 and single hyphens")

    description = meta.get("description")
    if not isinstance(description, str) or not 1 <= len(description) <= 1024:
        error(rel, "description is required and must be 1-1024 characters")

    compatibility = meta.get("compatibility")
    if compatibility is not None and (not isinstance(compatibility, str) or not 1 <= len(compatibility) <= 500):
        error(rel, "compatibility must be a string of 1-500 characters")

    metadata = meta.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()
        ):
            error(rel, "metadata must be a map of string keys to string values (quote versions)")
        elif "version" in metadata and not SEMVER.match(metadata["version"]):
            error(rel, f"metadata.version '{metadata['version']}' is not semver")

    if "allowed-tools" in meta:
        warn(rel, "'allowed-tools' is experimental and not honoured by every harness")
    lines = (body.count("\n") + 1)
    approx_tokens = len(body) // 4
    if lines > 500 or approx_tokens > 5000:
        warn(rel, f"SKILL.md body is {lines} lines / about {approx_tokens} tokens; "
                  "the Agent Skills guidance is under 500 lines and about 5,000 tokens (move detail to references/)")
    for path in skill_dir.rglob("*.md"):
        if any(token in path.read_text(encoding="utf-8", errors="ignore") for token in CLAUDE_ONLY):
            warn(path.relative_to(root), "mentions a Claude-only variable; keep skills harness-agnostic")
    return name


def check_links(path, root):
    in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for target in MD_LINK.findall(line):
            if re.match(r"^(?:[a-z][a-z0-9+.-]*:|#|/)", target, re.IGNORECASE):
                continue
            if not (path.parent / target.split("#")[0]).exists():
                error(f"{path.relative_to(root)}:{number}", f"relative link '{target}' does not resolve")


def discover_like_skills_cli(plugin_base):
    """Mimic the skills CLI: <plugin>/skills/<child>/SKILL.md, depth 1."""
    skills_dir = plugin_base / "skills"
    if not skills_dir.is_dir():
        return set()
    return {child.name for child in skills_dir.iterdir() if (child / "SKILL.md").is_file()}


def check_plugin(plugin_dir, root):
    rel_dir = plugin_dir.relative_to(root)
    version = None

    manifest_path = plugin_dir / "plugin.json"
    manifest = load_json(manifest_path, root)
    if manifest is not None:
        rel = manifest_path.relative_to(root)
        check_schema(manifest, "plugin.schema.json", rel)
        name = manifest.get("name")
        if name != plugin_dir.name:
            error(rel, f"name '{name}' must match the directory '{plugin_dir.name}'")
        if isinstance(name, str) and name.lower().startswith(RESERVED_PREFIXES):
            error(rel, f"name '{name}' uses a prefix Claude Code reserves")
        version = manifest.get("version")
        if not isinstance(version, str) or not SEMVER.match(version):
            error(rel, "version is required and must be semver (x.y.z)")
            version = None

        compat = plugin_dir / ".claude-plugin" / "plugin.json"
        if not compat.is_file():
            error(compat.relative_to(root), "Claude compatibility manifest is missing (copy plugin.json here)")
        elif compat.read_bytes() != manifest_path.read_bytes():
            error(compat.relative_to(root), "must be byte-identical to plugin.json (copy plugin.json over it)")

    mcp = plugin_dir / "mcp.json"
    if mcp.is_file():
        data = load_json(mcp, root)
        if data is not None:
            check_schema(data, "mcp.schema.json", mcp.relative_to(root))
        if not (plugin_dir / ".mcp.json").is_file():
            warn(mcp.relative_to(root), "no Claude '.mcp.json' beside it; Claude Code will not load these servers "
                                        "(its transport names differ, e.g. 'http' for 'streamable-http')")

    readme = plugin_dir / "README.md"
    if readme.is_file() and version:
        match = VERSION_LINE.search(readme.read_text(encoding="utf-8"))
        if not match:
            warn(readme.relative_to(root), "no 'Version x.y.z' line found to check against plugin.json")
        elif match.group(1) != version:
            error(readme.relative_to(root), f"says version {match.group(1)} but plugin.json says {version}")

    skills_dir = plugin_dir / "skills"
    names = {}
    if skills_dir.is_dir():
        for child in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            if not (child / "SKILL.md").is_file():
                warn(child.relative_to(root), "directory has no SKILL.md, so it is not a skill")
                continue
            name = check_skill(child, root)
            if name:
                names[name] = child
    else:
        warn(rel_dir, "plugin has no skills/ directory")

    for path in plugin_dir.rglob("SKILL.md"):
        if path.parent.parent != skills_dir:
            error(path.relative_to(root), "SKILL.md must sit directly at skills/<name>/ (clients do not search deeper)")

    for md in [readme, *skills_dir.rglob("*.md")] if skills_dir.is_dir() else [readme]:
        if md.is_file():
            check_links(md, root)
    return names


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else SCRIPT_DIR.parent
    marketplace_path = root / ".claude-plugin" / "marketplace.json"
    marketplace = load_json(marketplace_path, root)
    plugins_root = root / "plugins"

    if (root / "SKILL.md").exists():
        error("SKILL.md", "a SKILL.md at the repository root would make the skills CLI install only that skill")

    all_skill_names = {}
    plugin_dirs = sorted(p for p in plugins_root.iterdir() if p.is_dir()) if plugins_root.is_dir() else []
    if not plugin_dirs:
        error("plugins/", "no plugin directories found")
    for plugin_dir in plugin_dirs:
        for name, path in check_plugin(plugin_dir, root).items():
            if name in all_skill_names:
                error(path.relative_to(root), f"skill name '{name}' is also used by "
                                              f"{all_skill_names[name].relative_to(root)}; skill names must be unique across plugins")
            all_skill_names[name] = path

    check_links(root / "README.md", root)

    if marketplace is not None:
        rel = marketplace_path.relative_to(root)
        for field in ("name", "owner", "plugins"):
            if field not in marketplace:
                error(rel, f"missing required field '{field}'")
        listed = set()
        discovered = set()
        for entry in marketplace.get("plugins", []):
            entry_name, source = entry.get("name"), entry.get("source")
            if not isinstance(entry_name, str) or not isinstance(source, str) or not source.startswith("./"):
                error(rel, f"plugin entry {entry!r} needs a name and a './' relative source")
                continue
            target = (root / source).resolve()
            if not target.is_dir() or plugins_root.resolve() not in target.parents:
                error(rel, f"source '{source}' must be an existing directory under plugins/")
                continue
            listed.add(target)
            manifest = target / "plugin.json"
            if manifest.is_file() and json.loads(manifest.read_text(encoding="utf-8")).get("name") != entry_name:
                error(rel, f"entry name '{entry_name}' must equal the name in {manifest.relative_to(root)}")
            discovered |= discover_like_skills_cli(target)
        for plugin_dir in plugin_dirs:
            if plugin_dir.resolve() not in listed:
                error(rel, f"plugins/{plugin_dir.name} is not listed, so Claude Code and the skills CLI cannot find it")
        if discovered != set(all_skill_names):
            error(rel, "skills CLI discovery would find "
                       f"{sorted(discovered)} but the repository contains {sorted(all_skill_names)}")

    for line in warnings:
        print(f"warning: {line}")
    for line in errors:
        print(f"error: {line}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s); "
          f"{len(plugin_dirs)} plugin(s), {len(all_skill_names)} skill(s) checked")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
