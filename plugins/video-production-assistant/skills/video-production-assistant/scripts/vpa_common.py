"""Shared helpers for the video production assistant scripts.

Plain Python 3.9+, standard library only. Works on Windows, macOS and Linux.
"""
import json
import os
import shutil
import subprocess
import sys


def need(tool):
    """Return the full path of a command-line tool, or stop with a clear message."""
    path = shutil.which(tool)
    if not path:
        sys.exit(f"ERROR: '{tool}' is not installed or not on PATH. Run doctor.py for install help.")
    return path


def run(cmd, capture=False, cwd=None):
    """Run a command. Raise with the tail of stderr if it fails."""
    res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                         stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        tail = "\n".join(res.stderr.strip().splitlines()[-15:])
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(map(str, cmd[:6]))} ...\n{tail}")
    return res


def ffmpeg_stderr(args):
    """Run ffmpeg for analysis (output to null) and return its stderr text."""
    cmd = [need("ffmpeg"), "-hide_banner", "-nostats"] + args
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                         text=True, encoding="utf-8", errors="replace")
    return res.stderr


def probe(path):
    """ffprobe a file and return its JSON description."""
    res = run([need("ffprobe"), "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", str(path)], capture=True)
    return json.loads(res.stdout)


def duration(path):
    info = probe(path)
    d = info.get("format", {}).get("duration")
    if d is None:
        for s in info.get("streams", []):
            if s.get("duration"):
                return float(s["duration"])
        raise RuntimeError(f"Could not read duration of {path}")
    return float(d)


def video_stream(info):
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic", 0) == 0:
            return s
    return None


def audio_stream(info):
    for s in info.get("streams", []):
        if s.get("codec_type") == "audio":
            return s
    return None


def fps_of(stream, default=30.0):
    if not stream:
        return default
    for key in ("avg_frame_rate", "r_frame_rate"):
        val = stream.get(key, "0/0")
        try:
            num, den = val.split("/")
            if float(den) > 0 and float(num) > 0:
                return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            pass
    return default


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def fmt_time(t):
    """Seconds -> m:ss.s for humans."""
    t = max(0.0, float(t))
    m, s = divmod(t, 60)
    h, m = divmod(int(m), 60)
    if h:
        return f"{h}:{m:02d}:{s:04.1f}"
    return f"{m}:{s:04.1f}"


def kept_segments(edl):
    segs = [s for s in edl.get("segments", []) if s.get("keep", True)]
    return sorted(segs, key=lambda s: s["start"])


def output_offsets(edl):
    """For each kept segment, return (segment, start_on_output_timeline)."""
    out, t = [], 0.0
    for s in kept_segments(edl):
        out.append((s, t))
        t += s["end"] - s["start"]
    return out, t
