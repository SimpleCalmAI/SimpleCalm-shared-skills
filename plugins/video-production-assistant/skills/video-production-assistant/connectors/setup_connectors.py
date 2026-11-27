#!/usr/bin/env python3
"""Add the optional connectors you choose to an MCP config file. Writes no secrets.

Usage:
  python setup_connectors.py --list
  python setup_connectors.py --add elevenlabs,vidiq --print
  python setup_connectors.py --add elevenlabs,vidiq --target PATH/.mcp.json
  python setup_connectors.py --remove elevenlabs,vidiq --target PATH/.mcp.json

--print shows the entries without writing anything.
--target merges them into that file under "mcpServers" (the file is created if missing;
existing entries with other names are kept; an entry with the same name is left alone
unless you add --replace). A backup copy NAME.bak is made before an existing file changes.
--remove takes the named connectors' entries ('all' for every one in the catalog) back out of
--target and leaves every other entry alone.
"""
import argparse
import copy
import json
import os
import shutil
import sys
from pathlib import Path

CATALOG = Path(__file__).resolve().parent / "catalog.json"


def load_catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))["connectors"]


def entry_for(item):
    cfg = copy.deepcopy(item["config"])
    if cfg and item.get("wrap_npx_on_windows") and os.name == "nt" and cfg.get("command") == "npx":
        cfg = {**cfg, "command": "cmd", "args": ["/c", "npx"] + cfg.get("args", [])}
    return cfg


def chosen(cat, text):
    wanted = list(cat) if text.strip() == "all" else [k.strip() for k in text.split(",") if k.strip()]
    unknown = [k for k in wanted if k not in cat]
    if unknown:
        sys.exit(f"Unknown connector(s): {', '.join(unknown)}. Use --list.")
    return wanted


def remove(cat, text, target):
    if not target:
        sys.exit("--remove needs --target FILE: the MCP config file the entries were added to.")
    target = Path(target).expanduser()
    if not target.exists():
        print(f"{target} does not exist; nothing to remove.")
        return
    data = json.loads(target.read_text(encoding="utf-8") or "{}")
    servers = data.get("mcpServers", {})
    names = [cat[k]["server_name"] for k in chosen(cat, text) if cat[k]["server_name"]]
    gone = [n for n in names if n in servers]
    if not gone:
        print(f"None of those connectors are in {target}; nothing changed.")
        return
    shutil.copy2(target, target.with_name(target.name + ".bak"))
    for name in gone:
        del servers[name]
        print(f"removed: {name}")
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target} (backup: {target.name}.bak). Restart your agent to drop the connectors.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--add", default="", help="comma-separated connector ids, or 'all'")
    ap.add_argument("--target", help="MCP config file to merge into, e.g. ./.mcp.json")
    ap.add_argument("--print", dest="show", action="store_true")
    ap.add_argument("--replace", action="store_true")
    ap.add_argument("--remove", default="", help="comma-separated connector ids, or 'all', to take out of --target")
    a = ap.parse_args()
    cat = load_catalog()

    if a.remove:
        remove(cat, a.remove, a.target)
        return

    if a.list or not a.add:
        for key, item in cat.items():
            print(f"{key}\n  {item['title']}: {item['adds']}\n  Cost:  {item['cost']}\n  Needs: {item['needs']}\n")
        if not a.add:
            print("Choose with --add id1,id2 and either --print or --target FILE.")
        return

    wanted = chosen(cat, a.add)

    servers, notes = {}, []
    for key in wanted:
        item = cat[key]
        cfg = entry_for(item)
        if cfg is None:
            notes.append(f"{item['title']}: {item['needs']}")
        else:
            servers[item["server_name"]] = cfg
            notes.append(f"{item['title']}: {item['needs']}")

    if a.show or not a.target:
        print(json.dumps({"mcpServers": servers}, indent=2))
    else:
        target = Path(a.target).expanduser()
        data = {}
        if target.exists():
            data = json.loads(target.read_text(encoding="utf-8") or "{}")
            shutil.copy2(target, target.with_name(target.name + ".bak"))
        existing = data.setdefault("mcpServers", {})
        for name, cfg in servers.items():
            if name in existing and not a.replace:
                print(f"kept existing entry: {name} (use --replace to overwrite)")
                continue
            existing[name] = cfg
            print(f"added: {name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {target}. Restart your agent to load the connectors.")

    print("\nBefore first use:")
    for n in notes:
        print(f"  - {n}")


if __name__ == "__main__":
    main()
