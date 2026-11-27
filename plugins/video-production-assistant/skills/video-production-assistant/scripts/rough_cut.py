#!/usr/bin/env python3
"""Plan and render a rough cut from a transcript, checked against the real audio.

Two sub-commands:

  plan    Build an edit decision list (edl.json): which parts to keep and why.
  render  Cut the source to the kept parts and join them, with tiny audio fades.

Dual-pass method: speech spans come from the transcript (pass 1); every cut point
is then checked against FFmpeg silence detection (pass 2). If a cut lands while
sound is still going, it is moved to where the sound stops - but never into the
next or previous word. This is what stops clipped word tails.

Usage:
  python rough_cut.py plan  SOURCE --words words.json --out edl.json
         [--max-pause 0.4] [--keep-pause 0.15] [--pad 0.12] [--noise -35]
         [--keep-fillers] [--fillers "um,uh,er,erm"]
  python rough_cut.py render SOURCE --edl edl.json --out roughcut.mp4 [--fade-ms 10] [--best]
  python rough_cut.py find "open the skills folder" --words words.json --edl edl.json

You (or the assistant) can edit edl.json between plan and render: set
"keep": false on a segment to drop it (give a "reason"), or change its start/end.
"""
import argparse
import os
import re
import shutil
import string

from vpa_common import (duration, ffmpeg_stderr, fmt_time, fps_of, kept_segments, load_json, need, output_offsets, probe,
                        run, save_json, video_stream)

DEFAULT_FILLERS = "um,umm,uh,uhh,uhm,er,erm,ah,hmm,mm,mhm"


def norm(text):
    return text.lower().strip(string.punctuation + "’‘“” ")


def detect_silences(src, noise_db, min_dur):
    txt = ffmpeg_stderr(["-i", src, "-vn", "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?[\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*(-?[\d.]+)", txt)]
    sil = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else float("inf")
        sil.append((max(0.0, s), e))
    return sil


def in_silence(t, silences):
    return any(s <= t <= e for s, e in silences)


def next_silence_start(t, silences):
    later = [s for s, e in silences if s >= t]
    return min(later) if later else None


def prev_silence_end(t, silences):
    earlier = [e for s, e in silences if e <= t]
    return max(earlier) if earlier else None


def plan(a):
    src_dur = duration(a.source)
    words = [w for w in load_json(a.words)["words"] if w.get("type", "word") == "word"]
    if not words:
        raise SystemExit("No words in transcript.")
    fillers = set() if a.keep_fillers else {f.strip().lower() for f in a.fillers.split(",") if f.strip()}

    keep_words, removed = [], []
    for w in words:
        if norm(w["text"]) in fillers:
            removed.append({"start": w["start"], "end": w["end"], "reason": "filler", "text": w["text"]})
        else:
            keep_words.append(w)

    # Pass 1: group kept words into speech spans, splitting at long pauses.
    spans, cur = [], [keep_words[0]]
    for w in keep_words[1:]:
        if w["start"] - cur[-1]["end"] > a.max_pause:
            spans.append(cur)
            cur = [w]
        else:
            cur.append(w)
    spans.append(cur)

    # Filler words sitting inside a span would be kept by the span; split spans around them.
    split_spans = []
    filler_times = [(r["start"], r["end"]) for r in removed]
    for sp in spans:
        part = [sp[0]]
        for w in sp[1:]:
            gap_has_filler = any(part[-1]["end"] <= fs and fe <= w["start"] for fs, fe in filler_times)
            if gap_has_filler:
                split_spans.append(part)
                part = [w]
            else:
                part.append(w)
        split_spans.append(part)

    # Pass 2: pad and snap each cut point to real silence.
    silences = detect_silences(a.source, a.noise, 0.05)
    all_starts = sorted(w["start"] for w in words)
    all_ends = sorted(w["end"] for w in words)
    pad_out = max(a.pad, a.keep_pause / 2)
    segs, snapped = [], 0
    for sp in split_spans:
        s0, e0 = sp[0]["start"], sp[-1]["end"]
        # never extend into a neighbouring word (kept or removed)
        nxt = min([t for t in all_starts if t > e0 + 0.001], default=src_dur)
        prv = max([t for t in all_ends if t < s0 - 0.001], default=0.0)
        end = min(e0 + pad_out, nxt - 0.02)
        start = max(s0 - pad_out, prv + 0.02)
        if not in_silence(end, silences):
            ns = next_silence_start(end, silences)
            if ns is not None and ns - end <= a.max_extend and ns < nxt - 0.02:
                end, snapped = ns + 0.03, snapped + 1
        if not in_silence(start, silences):
            pe = prev_silence_end(start, silences)
            if pe is not None and start - pe <= a.max_extend and pe > prv + 0.02:
                start, snapped = pe - 0.03, snapped + 1
        start, end = max(0.0, start), min(src_dur, end)
        if end - start > 0.05:
            segs.append({"start": round(start, 3), "end": round(end, 3),
                         "text": " ".join(w["text"] for w in sp)})

    # merge overlaps
    merged = []
    for s in segs:
        if merged and s["start"] <= merged[-1]["end"] + 0.01:
            merged[-1]["end"] = max(merged[-1]["end"], s["end"])
            merged[-1]["text"] += " " + s["text"]
        else:
            merged.append(dict(s))

    # record removed gaps (pauses, lead-in, tail)
    t = 0.0
    for s in merged:
        if s["start"] - t > 0.05:
            reason = "lead-in" if t == 0.0 else "pause"
            removed.append({"start": round(t, 3), "end": s["start"], "reason": reason, "text": ""})
        t = s["end"]
    if src_dur - t > 0.05:
        removed.append({"start": round(t, 3), "end": round(src_dur, 3), "reason": "tail", "text": ""})

    for i, s in enumerate(merged):
        s.update(id=i, keep=True, reason="speech")
    edl = {"source": os.path.abspath(a.source), "source_duration": round(src_dur, 3),
           "settings": {"max_pause": a.max_pause, "keep_pause": a.keep_pause, "pad": a.pad,
                        "noise_db": a.noise, "fillers_removed": sorted(fillers)},
           "segments": merged, "removed": sorted(removed, key=lambda r: r["start"])}
    save_json(edl, a.out)

    new_dur = sum(s["end"] - s["start"] for s in merged)
    counts = {}
    for r in removed:
        counts[r["reason"]] = counts.get(r["reason"], 0) + 1
    print(f"Source length:   {fmt_time(src_dur)}")
    print(f"Rough cut length: {fmt_time(new_dur)}  (saves {fmt_time(src_dur - new_dur)}, {100 * (1 - new_dur / src_dur):.0f}%)")
    print(f"Kept segments:   {len(merged)}")
    print("Removed:         " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    print(f"Cut points moved to real silence: {snapped}")
    print("Next: read the transcript for retakes and false starts; set keep=false on those segments in", a.out)


def render(a):
    edl = load_json(a.edl)
    segs = kept_segments(edl)
    if not segs:
        raise SystemExit("No kept segments in EDL.")
    info = probe(a.source)
    fps = fps_of(video_stream(info))
    has_video = video_stream(info) is not None
    work = os.path.join(os.path.dirname(os.path.abspath(a.out)), "_segments")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    fade = a.fade_ms / 1000.0
    preset = "slow" if a.best else "veryfast"
    listfile = os.path.join(work, "list.txt")
    with open(listfile, "w", encoding="utf-8") as lf:
        for i, s in enumerate(segs):
            # snap to the frame grid so audio and picture stay locked
            st = round(s["start"] * fps) / fps
            en = round(s["end"] * fps) / fps
            dur = max(en - st, 1.0 / fps)
            af = f"afade=t=in:d={fade},afade=t=out:st={max(dur - fade, 0)}:d={fade}" if fade > 0 else "anull"
            seg = os.path.join(work, f"seg_{i:04d}.mkv")
            cmd = [need("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{st:.3f}", "-i", a.source,
                   "-t", f"{dur:.3f}"]
            if has_video:
                cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                        "-r", f"{fps:.6f}"]
            cmd += ["-af", af, "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", seg]
            run(cmd)
            lf.write(f"file '{os.path.basename(seg)}'\n")
            if (i + 1) % 25 == 0:
                print(f"  rendered {i + 1}/{len(segs)} segments")
    run([need("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", os.path.abspath(a.out)], cwd=work)
    if not a.keep_segments:
        shutil.rmtree(work, ignore_errors=True)
    print(f"Rough cut: {a.out}  ({fmt_time(duration(a.out))}, {len(segs)} segments)")


def find(a):
    """Print where a phrase is spoken: raw time and time on the rough cut."""
    edl = load_json(a.edl)
    words = [w for w in load_json(a.words)["words"] if w.get("type", "word") == "word"]
    target = [norm(t) for t in a.phrase.split()]
    pairs, _ = output_offsets(edl)
    hits = 0
    for i in range(len(words) - len(target) + 1):
        if [norm(w["text"]) for w in words[i:i + len(target)]] == target:
            t_raw = words[i]["start"]
            out = next((off + t_raw - s["start"] for s, off in pairs if s["start"] <= t_raw <= s["end"]), None)
            where = f"rough cut {fmt_time(out)} ({out:.2f} s)" if out is not None else "CUT (not in rough cut)"
            print(f"raw {fmt_time(t_raw)} ({t_raw:.2f} s) -> {where}")
            hits += 1
    if not hits:
        print("Phrase not found. Check spelling against words.json.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find", help="where is a phrase on the rough-cut timeline?")
    f.add_argument("phrase")
    f.add_argument("--words", required=True)
    f.add_argument("--edl", required=True)
    p = sub.add_parser("plan")
    p.add_argument("source")
    p.add_argument("--words", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-pause", type=float, default=0.4, help="pauses longer than this are shortened (s)")
    p.add_argument("--keep-pause", type=float, default=0.15, help="silence left at each join (s)")
    p.add_argument("--pad", type=float, default=0.12, help="minimum padding around speech (s)")
    p.add_argument("--max-extend", type=float, default=0.3, help="how far a cut may move to reach silence (s)")
    p.add_argument("--noise", type=float, default=-35.0, help="silence threshold (dB)")
    p.add_argument("--keep-fillers", action="store_true")
    p.add_argument("--fillers", default=DEFAULT_FILLERS)
    r = sub.add_parser("render")
    r.add_argument("source")
    r.add_argument("--edl", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--fade-ms", type=float, default=10.0)
    r.add_argument("--crf", type=int, default=18)
    r.add_argument("--best", action="store_true", help="slower, slightly smaller/better encode")
    r.add_argument("--keep-segments", action="store_true")
    a = ap.parse_args()
    {"plan": plan, "render": render, "find": find}[a.cmd](a)


if __name__ == "__main__":
    main()
