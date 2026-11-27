#!/usr/bin/env python3
"""Quality check a render: contact sheet, loudness, black frames, length.

Usage:
  python qa.py VIDEO --sheet sheet.jpg [--frames 16] [--cuts edl.json] [--loudness]
With --cuts, the sheet shows frames just before and after the first joins of the
rough cut (to spot jarring jump cuts) instead of evenly spaced frames.
Pillow (optional) adds time labels to the sheet.
"""
import argparse
import math
import os
import re
import shutil
import tempfile

from vpa_common import duration, ffmpeg_stderr, fmt_time, load_json, need, output_offsets, run


def frame_times(dur, n, cuts_edl):
    if cuts_edl:
        pairs, _ = output_offsets(load_json(cuts_edl))
        joins = [off for _, off in pairs[1:]]
        if joins:
            step = max(1, len(joins) // max(1, n // 2))
            picked = joins[::step][: n // 2]
            times = []
            for j in picked:
                times += [max(j - 0.2, 0), min(j + 0.2, dur - 0.05)]
            return times, [f"join {fmt_time(j)} {'before' if i % 2 == 0 else 'after'}"
                           for j in picked for i in range(2)]
    times = [dur * (i + 0.5) / n for i in range(n)]
    return times, [fmt_time(t) for t in times]


def contact_sheet(video, out, n, cuts):
    dur = duration(video)
    times, labels = frame_times(dur, n, cuts)
    tmp = tempfile.mkdtemp(prefix="vpa_qa_")
    paths = []
    for i, t in enumerate(times):
        p = os.path.join(tmp, f"f_{i:03d}.jpg")
        run([need("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", video,
             "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "4", p])
        paths.append(p)
    cols = 4
    rows = math.ceil(len(paths) / cols)
    try:
        from PIL import Image, ImageDraw
        ims = [Image.open(p) for p in paths]
        w, h = ims[0].size
        sheet = Image.new("RGB", (cols * w, rows * (h + 24)), "black")
        d = ImageDraw.Draw(sheet)
        for i, im in enumerate(ims):
            x, y = (i % cols) * w, (i // cols) * (h + 24)
            sheet.paste(im, (x, y + 24))
            d.text((x + 6, y + 5), labels[i], fill="white")
        sheet.save(out, quality=85)
    except ImportError:
        run([need("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-i", os.path.join(tmp, "f_%03d.jpg"),
             "-vf", f"tile={cols}x{rows}", "-frames:v", "1", out])
        print("Frame times (left to right, top to bottom): " + ", ".join(labels))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Contact sheet: {out} ({len(paths)} frames)")


def loudness(video):
    txt = ffmpeg_stderr(["-i", video, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
    summary = txt[txt.rfind("Summary:"):]
    i = re.search(r"I:\s*(-?[\d.]+) LUFS", summary)
    tp = re.search(r"Peak:\s*(-?[\d.]+) dBFS", summary)
    return (float(i.group(1)) if i else None, float(tp.group(1)) if tp else None)


def black_frames(video):
    txt = ffmpeg_stderr(["-i", video, "-an", "-vf", "blackdetect=d=0.3:pic_th=0.95", "-f", "null", "-"])
    return [(float(s), float(e)) for s, e in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", txt)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--sheet")
    ap.add_argument("--frames", type=int, default=16)
    ap.add_argument("--cuts")
    ap.add_argument("--loudness", action="store_true")
    ap.add_argument("--target", type=float, default=-14.0)
    a = ap.parse_args()

    print(f"Length: {fmt_time(duration(a.video))}")
    if a.sheet:
        contact_sheet(a.video, a.sheet, a.frames, a.cuts)
    if a.loudness:
        i, tp = loudness(a.video)
        ok_i = i is not None and abs(i - a.target) <= 1.0
        ok_tp = tp is not None and tp <= -0.9
        print(f"Loudness: {i} LUFS (target {a.target}) {'OK' if ok_i else 'CHECK'}")
        print(f"True peak: {tp} dBTP {'OK' if ok_tp else 'CHECK - above -1 dBTP'}")
        blacks = black_frames(a.video)
        if blacks:
            print("Black sections: " + ", ".join(f"{fmt_time(s)}-{fmt_time(e)}" for s, e in blacks))
        else:
            print("Black sections: none")


if __name__ == "__main__":
    main()
