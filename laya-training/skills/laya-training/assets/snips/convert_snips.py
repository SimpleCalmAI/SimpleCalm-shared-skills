#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 SimpleCalm Labs Ltd and contributors.
"""Recreate snips_train.csv and snips_test.csv from a clone of github.com/sonos/nlu-benchmark.

Usage: python convert_snips.py PATH_TO_nlu-benchmark OUTDIR

Uses 2017-06-custom-intent-engines: train_<Intent>_full.json for training and
validate_<Intent>.json (100 per intent) as the final test. Joins the text pieces of
each request, normalises spaces, drops 6 invalid bytes in the PlayMusic source file,
and removes any training request that also appears in the test files.
"""
import collections, csv, glob, json, os, sys


def load(path):
    s = open(path, "rb").read().decode("utf-8", errors="replace")
    if "�" in s:
        print("dropped", s.count("�"), "invalid bytes in", path)
    return json.loads(s.replace("�", ""))


def rows(src, kind):
    res = []
    for d in sorted(glob.glob(f"{src}/2017-06-custom-intent-engines/*/")):
        intent = os.path.basename(d.rstrip("/"))
        f = f"{d}train_{intent}_full.json" if kind == "train" else f"{d}validate_{intent}.json"
        for ex in load(f)[intent]:
            t = " ".join("".join(p["text"] for p in ex["data"]).split())
            if t:
                res.append((t, intent))
    return res


def main(src, out):
    tr, te = rows(src, "train"), rows(src, "test")
    te_texts = {t.lower() for t, _ in te}
    tr = [(t, i) for t, i in tr if t.lower() not in te_texts]
    for name, data in (("snips_train.csv", tr), ("snips_test.csv", te)):
        with open(os.path.join(out, name), "w", encoding="utf-8-sig", newline="") as f:  # marker lets Excel show accents
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["text", "intent"])
            w.writerows(data)
        print(name, len(data), dict(collections.Counter(i for _, i in data)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
