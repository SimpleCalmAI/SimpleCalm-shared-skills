#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 SimpleCalm Labs Ltd and contributors.
"""Build Laya fine-tuning files from a labelled CSV.

Usage: python build_laya_dataset.py spec.json examples.csv OUTDIR [test.csv]

Writes test.jsonl (the final exam), train.jsonl, heldout.jsonl (a checking file)
and manifest.json. With test.csv, that whole file becomes the final test and its
texts are removed from the training pool. Without it, test_share of each label is
set aside first. Stops (exit 1) on any problem. Writes nothing until every check passes.
"""
import csv, hashlib, json, random, sys
from collections import defaultdict
from pathlib import Path

MAX_OPTIONS, MAX_WORDS, MIN_PER_OPTION = 20, 350, 30
# MAX_WORDS is a cautious warning, not a hard limit: the pinned notebook reads up to 1,024 tokens,
# and the question and option text use part of that budget.


def stop(msg):
    sys.exit(f"STOPPED: {msg}")


def read_rows(csv_path, qs, text_col, skip=frozenset()):
    """Return rows plus counts of what was dropped or flagged."""
    rows, first_label, stats = [], {}, {"duplicates_removed": 0, "conflicting_labels": 0,
                                         "removed_because_in_test": 0, "rows_over_word_limit": 0}
    first_q = next(iter(qs))
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if text_col not in (reader.fieldnames or []):
            stop(f"{csv_path}: no column named {text_col!r}; columns are {reader.fieldnames}")
        for n, r in enumerate(reader, start=2):
            text = (r.get(text_col) or "").strip()
            if not text:
                stop(f"{csv_path} line {n}: empty {text_col}")
            gold = {}
            for qid, q in qs.items():
                label = (r.get(q["label_column"]) or "").strip()
                if label not in q["criteria"]:
                    stop(f"{csv_path} line {n}: {qid} label {label!r} is not an option")
                gold[qid] = {"probabilities": {o: float(o == label) for o in q["criteria"]}, "label": label}
            key = text.lower()
            if key in skip:
                stats["removed_because_in_test"] += 1
                continue
            if key in first_label:                    # duplicates would leak across the split
                stats["duplicates_removed"] += 1
                if first_label[key] != gold[first_q]["label"]:
                    stats["conflicting_labels"] += 1  # same text, different answer: first one kept
                continue
            first_label[key] = gold[first_q]["label"]
            stats["rows_over_word_limit"] += len(text.split()) > MAX_WORDS
            public_qs = {qid: {k: v for k, v in q.items() if k != "label_column"} for qid, q in qs.items()}
            rows.append({"state": json.dumps(text, ensure_ascii=False),
                         "questions": json.dumps(public_qs, ensure_ascii=False),
                         "gold": json.dumps(gold, ensure_ascii=False),
                         "_strat": gold[first_q]["label"], "_key": key})
    return rows, stats


def main(spec_path, csv_path, outdir, test_csv=None):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    missing = [k for k in ("workflow", "text_column", "questions") if not spec.get(k)]
    if missing:
        stop(f"spec.json is missing {missing}")
    qs, text_col = spec["questions"], spec["text_column"]
    if len(qs) != 1:
        stop(f"spec.json has {len(qs)} questions; this script builds one decision at a time. "
             "For several questions per text, use Laya's own laya-train tooling (docs/finetune.md).")
    for qid, q in qs.items():
        for k in ("type", "instructions", "criteria", "label_column"):
            if k not in q:
                stop(f"question {qid!r} is missing {k!r}")
        if q["type"] != "choice":
            stop(f"{qid}: only choice questions are built here; see laya's docs/finetune.md for {q['type']} rows")
        if not isinstance(q["criteria"], dict):
            stop(f"{qid}: criteria must be a dict of option -> description (the notebook's metrics cell reads criteria.keys())")
        if len(q["criteria"]) > MAX_OPTIONS:
            stop(f"{qid}: {len(q['criteria'])} options; split the question or use a shortlist step")
    seed = spec.get("seed", 13)
    test_share, held_share = float(spec.get("test_share", 0.2)), float(spec.get("heldout_share", 0.25))
    if not (0 < test_share < 1 and 0 < held_share < 1):
        stop("test_share and heldout_share must be between 0 and 1")

    test, test_stats = [], {}
    if test_csv:
        test, test_stats = read_rows(test_csv, qs, text_col)
    rows, stats = read_rows(csv_path, qs, text_col, skip={r["_key"] for r in test})

    by_label = defaultdict(list)                      # stratified split on the first question
    for r in rows:
        by_label[r["_strat"]].append(r)
    rng = random.Random(seed)
    train, held = [], []
    for label in sorted(by_label):
        group = by_label[label]
        rng.shuffle(group)
        if not test_csv:
            t = max(1, round(len(group) * test_share))
            test += group[:t]; group = group[t:]
        if len(group) < 4:
            stop(f"label {label!r} has {len(group)} examples left for training and checking; need at least 4")
        k = max(1, round(len(group) * held_share))
        held += group[:k]; train += group[k:]

    counts = defaultdict(int)
    for r in train + held + test:
        counts[r["_strat"]] += 1
    first_q = next(iter(qs))
    unused = [o for o in qs[first_q]["criteria"] if counts.get(o, 0) == 0]
    thin = {o: counts.get(o, 0) for o in qs[first_q]["criteria"] if 0 < counts.get(o, 0) < MIN_PER_OPTION}

    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    wf = spec["workflow"]
    spec_copy = out / "spec.json"
    if Path(spec_path).resolve() != spec_copy.resolve():
        spec_copy.write_bytes(Path(spec_path).read_bytes())
    manifest = {"workflow": wf, "seed": seed, "heldout_share": held_share,
                "test_source": Path(test_csv).name if test_csv else f"test_share {test_share}",
                "spec_sha256": hashlib.sha256(spec_copy.read_bytes()).hexdigest(),
                "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "examples_per_option": dict(sorted(counts.items())),
                "examples_csv": stats, "files": {}}
    if test_csv:
        manifest["test_csv"] = test_stats
    for k in ("source", "licence", "licence_checked", "generating_model"):
        if spec.get(k):                               # optional record; kept with the files when given
            manifest[k] = spec[k]
    for name, part in (("train.jsonl", train), ("heldout.jsonl", held), ("test.jsonl", test)):
        p = out / name
        with p.open("w", encoding="utf-8", newline="\n") as f:
            for i, r in enumerate(part):
                row = {k: v for k, v in r.items() if not k.startswith("_")}
                f.write(json.dumps({"id": f"{name.split('.')[0]}-{i:05d}", "workflow": wf, **row},
                                   ensure_ascii=False) + "\n")
        manifest["files"][name] = {"rows": len(part), "bytes": p.stat().st_size,
                                   "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest["files"], indent=2))
    if thin:
        print(f"WARNING: fewer than {MIN_PER_OPTION} examples for {thin}; results for these options may be unreliable")
    if unused:
        print(f"WARNING: no examples at all for options {unused}")
    for label, s in (("examples", stats), ("test", test_stats)):
        if s.get("conflicting_labels"):
            print(f"WARNING: {s['conflicting_labels']} {label} texts appear with different labels; the first label was kept")
        if s.get("rows_over_word_limit"):
            print(f"WARNING: {s['rows_over_word_limit']} {label} rows exceed ~{MAX_WORDS} words; long texts may be cut short by the model")


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        sys.exit(__doc__)
    main(*sys.argv[1:])
