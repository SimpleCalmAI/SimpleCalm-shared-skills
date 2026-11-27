#!/usr/bin/env python3
"""Assemble the final video from timeline.json.

Lays cutaways (full-frame B-roll), overlays (lower thirds, logos, callouts,
picture-in-picture) and burned-in captions over the base video, and swaps in
the polished audio. See references/timeline-format.md for the format.

Usage: python assemble.py --timeline 02_work/timeline.json --out 04_exports/name_v1.mp4
       [--project FOLDER] [--best] [--preview 0:30-1:00]
Paths in the timeline are relative to the project folder (default: the folder
above the timeline file's folder, i.e. the one holding 01_raw, 02_work ...).
"""
import argparse
import os
import shutil

from vpa_common import audio_stream, duration, fmt_time, load_json, need, probe, run, video_stream

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def parse_range(text):
    def secs(x):
        parts = [float(p) for p in x.split(":")]
        t = 0.0
        for p in parts:
            t = t * 60 + p
        return t
    a, b = text.split("-")
    return secs(a), secs(b)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--project")
    ap.add_argument("--best", action="store_true", help="slow preset (better compression, 2-3x longer)")
    ap.add_argument("--preview", help="render only this range of the output, e.g. 0:30-1:00")
    a = ap.parse_args()

    tl_path = os.path.abspath(a.timeline)
    tl = load_json(tl_path)
    project = os.path.abspath(a.project or os.path.dirname(os.path.dirname(tl_path)))

    def P(rel):
        return rel if os.path.isabs(rel) else os.path.join(project, rel)

    base = P(tl["base"])
    W, H = tl.get("size", [1920, 1080])
    fps = tl.get("fps", 30)
    total = duration(base)
    inputs, filters = ["-i", base], []
    filters.append(f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,"
                   f"setsar=1,fps={fps},format=yuv420p[base0]")
    last, idx = "base0", 1

    def add_layer(item, full_frame):
        nonlocal last, idx
        src = P(item["src"])
        if not os.path.exists(src):
            raise SystemExit(f"Missing asset: {src}")
        at, dur = float(item["at"]), float(item["dur"])
        ext = os.path.splitext(src)[1].lower()
        if ext in IMAGE_EXT:
            inputs.extend(["-loop", "1", "-t", f"{dur:.3f}", "-i", src])
        else:
            inputs.extend(["-ss", f"{float(item.get('src_in', 0)):.3f}", "-t", f"{dur:.3f}", "-i", src])
        lbl = f"l{idx}"
        if full_frame:
            fit = item.get("fit", "contain")
            if fit == "cover":
                sc = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
            else:
                sc = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black"
            chain = f"[{idx}:v]{sc},setsar=1,fps={fps},format=yuv420p"
            x, y = "0", "0"
        else:
            w = item.get("w")
            sc = f"scale={int(w)}:-2," if w else ""
            chain = f"[{idx}:v]{sc}fps={fps},format=rgba"
            x, y = str(item.get("x", 0)), str(item.get("y", 0))
        fade = float(item.get("fade", 0.25 if not full_frame else 0))
        if fade > 0:
            chain += f",fade=t=in:st=0:d={fade}:alpha=1,fade=t=out:st={max(dur - fade, 0):.3f}:d={fade}:alpha=1"
        chain += f",setpts=PTS-STARTPTS+{at:.3f}/TB[{lbl}]"
        filters.append(chain)
        out = f"v{idx}"
        filters.append(f"[{last}][{lbl}]overlay=x={x}:y={y}:eof_action=pass:enable='between(t,{at:.3f},{at + dur:.3f})'[{out}]")
        last = out
        idx += 1

    for c in tl.get("cutaways", []):
        add_layer(c, True)
    for o in tl.get("overlays", []):
        add_layer(o, False)

    cwd = None
    if tl.get("captions"):
        ass = P(tl["captions"])
        cwd = os.path.dirname(ass)  # relative name avoids Windows drive-letter escaping in the filter
        filters.append(f"[{last}]subtitles={os.path.basename(ass)}[vsub]")
        last = "vsub"

    audio_map = "0:a"
    if tl.get("audio"):
        inputs.extend(["-i", P(tl["audio"])])
        audio_map = f"{idx}:a"
    elif audio_stream(probe(base)) is None:
        audio_map = None

    out_path = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [need("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error"]
    if a.preview:
        s, e = parse_range(a.preview)
        filters.append(f"[{last}]trim=start={s}:end={e},setpts=PTS-STARTPTS[vprev]")
        last = "vprev"
    cmd += inputs + ["-filter_complex", ";".join(filters), "-map", f"[{last}]"]
    if audio_map:
        if a.preview:
            cmd += ["-map", audio_map, "-af", f"atrim=start={s}:end={e},asetpts=PTS-STARTPTS"]
        else:
            cmd += ["-map", audio_map]
        cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    cmd += ["-c:v", "libx264", "-preset", "slow" if a.best else "veryfast", "-crf", str(tl.get("crf", 18)),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-t", f"{(e - s) if a.preview else total:.3f}", out_path]
    if os.path.exists(out_path) and not a.preview:
        print(f"Note: replacing existing {out_path}")
    run(cmd, cwd=cwd)
    print(f"Final: {a.out}  ({fmt_time(duration(out_path))}, {W}x{H} @ {fps} fps, "
          f"{len(tl.get('cutaways', []))} cutaways, {len(tl.get('overlays', []))} overlays, "
          f"captions {'on' if tl.get('captions') else 'off'})")


if __name__ == "__main__":
    main()
