#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 SimpleCalm Labs Ltd and contributors.
"""Score the untrained base model, and optionally a trained model, on a test JSONL file.

Baseline before training:   python eval_laya.py test.jsonl results/
Comparison after training:  python eval_laya.py test.jsonl results/ --trained MODEL_DIR

Writes eval_untrained.csv, eval_trained.csv (with --trained) and eval_summary.json.
The trained model is run twice to check that the two result files are byte-identical.
The first run downloads the base model unless it is already cached.

Overall accuracy is the main result. "conf" is the probability of the chosen answer.
For each cut-off (0.5, 0.7, 0.85) the summary reports coverage (the share of answers at
or above the cut-off) and accuracy among those answers. If laya warns that a model's
temperatures were clamped, its confidence is uncalibrated and the summary says so:
treat cut-off results as advisory for that model.
"""
import argparse, csv, hashlib, json, sys, time, warnings
from importlib import metadata
from pathlib import Path
import laya

CUTS = (0.5, 0.7, 0.85)
MODEL_PARTS = ("model.safetensors", "rl_agent_config.json", "encoder", "tokenizer")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def version(pkg):
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return None


def progress(msg):
    print(msg, file=sys.stderr, flush=True)


def score(agent, rows, label):
    out, t0 = [], time.time()
    progress(f"Scoring {len(rows)} test questions with the {label} model...")
    for i, r in enumerate(rows, start=1):
        if i % 100 == 0:
            progress(f"  {i}/{len(rows)} done")
        text, qs, gold = json.loads(r["state"]), json.loads(r["questions"]), json.loads(r["gold"])
        ans = agent.predict(text, qs)["answers"]
        for qid in qs:
            p = ans[qid]["probabilities"]
            pred = ans[qid].get("choice")              # laya's own answer; fall back to the top probability
            if pred not in p:
                pred = max(p, key=p.get)
            out.append({"id": r["id"], "question": qid, "gold": gold[qid]["label"],
                        "pred": pred, "conf": float(p[pred])})
    progress(f"  finished in {time.time() - t0:.0f} seconds")
    return out


def write(path, res):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0]), lineterminator="\n")
        w.writeheader(); w.writerows(res)
    return sha256(path)


def summarise(res):
    s = {}
    for qid in sorted({x["question"] for x in res}):
        q = [x for x in res if x["question"] == qid]
        correct = sum(x["pred"] == x["gold"] for x in q)
        s[qid] = {"n": len(q), "correct": correct, "accuracy": round(correct / len(q), 4)}
        for c in CUTS:
            conf = [x for x in q if x["conf"] >= c]
            right = sum(x["pred"] == x["gold"] for x in conf)
            s[qid][f"answered_at_{c}"] = len(conf)
            s[qid][f"correct_at_{c}"] = right
            s[qid][f"coverage_at_{c}"] = round(len(conf) / len(q), 4)
            s[qid][f"accuracy_at_{c}"] = round(right / len(conf), 4) if conf else None
    return s


def load_with_warnings(load):
    """Load a model and report whether laya flagged its confidence as uncalibrated."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        agent = load()
    msgs = [str(w.message) for w in caught if "temperature" in str(w.message).lower()]
    for m in msgs:
        print("NOTE:", m, file=sys.stderr)
    return agent, msgs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("eval_file", help="test.jsonl in the build script's row format")
    ap.add_argument("out_dir")
    ap.add_argument("--trained", help="folder of the trained model; leave out for a baseline run")
    ap.add_argument("--base", default="convaiinnovations/laya", help="base model the notebook fine-tuned")
    ap.add_argument("--revision", help="base model revision; defaults to laya's reviewed pin for --base")
    ap.add_argument("--device", default="cpu", help="cpu, or cuda on a GPU machine")
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.eval_file, encoding="utf-8") if l.strip()]
    if not rows:
        sys.exit(f"STOPPED: {a.eval_file} has no rows")
    if a.trained:
        trained = Path(a.trained).expanduser().resolve()
        missing = [p for p in MODEL_PARTS if not (trained / p).exists()]
        if missing:
            sys.exit(f"STOPPED: {trained} is not a complete trained Laya model folder; missing {missing}. "
                     "Point --trained at the folder that holds model.safetensors.")
        a.trained = str(trained)
    revision = a.revision or laya.PINNED_REVISIONS.get(a.base)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    summary = {"laya_version": laya.__version__,
               "torch_version": version("torch"), "transformers_version": version("transformers"),
               "device": a.device, "base": a.base, "base_revision": revision,
               "eval_file": Path(a.eval_file).name, "eval_sha256": sha256(a.eval_file),
               "script_sha256": sha256(__file__), "calibration_warnings": {}}
    if a.trained:
        summary["trained_dir"] = a.trained
        summary["trained_config_sha256"] = sha256(Path(a.trained) / "rl_agent_config.json")
    models = [("untrained", lambda: laya.load(a.base, device=a.device, revision=revision))]
    if a.trained:
        models.append(("trained", lambda: laya.Agent(a.trained, device=a.device)))
    for name, load in models:
        progress(f"Loading the {name} model (the first run may download it)...")
        agent, notes = load_with_warnings(load)
        summary["calibration_warnings"][name] = notes
        agent.predict("warm up", {"x": {"type": "noul", "instructions": "Is this a test?"}})
        res = score(agent, rows, name)
        sha = write(out / f"eval_{name}.csv", res)
        summary[name] = summarise(res)
        if name == "trained":
            summary["trained_repeat_identical"] = sha == write(out / "eval_trained_run2.csv", score(agent, rows, "trained (repeat check)"))
    if a.trained:
        summary["change_in_points"] = {qid: round(100 * (summary["trained"][qid]["accuracy"]
                                                         - summary["untrained"][qid]["accuracy"]), 1)
                                       for qid in summary["untrained"]}
    summary["confidence_note"] = ("Overall accuracy is the main result. Cut-off results are advisory "
                                  "for any model listed under calibration_warnings.")
    (out / "eval_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
