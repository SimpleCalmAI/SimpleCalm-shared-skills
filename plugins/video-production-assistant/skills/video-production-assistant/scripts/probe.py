#!/usr/bin/env python3
"""Inspect video/audio files and flag problems before editing.

Usage: python probe.py FILE [FILE ...] [--out probe.json]
Flags: variable frame rate, no audio, mono, very quiet audio, mismatched sizes.
"""
import argparse
import glob
import re

from vpa_common import audio_stream, ffmpeg_stderr, fmt_time, fps_of, probe, save_json, video_stream


def quick_loudness(path, seconds=120):
    txt = ffmpeg_stderr(["-t", str(seconds), "-i", path, "-vn", "-af", "volumedetect", "-f", "null", "-"])
    mean = re.search(r"mean_volume:\s*(-?[\d.]+) dB", txt)
    peak = re.search(r"max_volume:\s*(-?[\d.]+) dB", txt)
    return (float(mean.group(1)) if mean else None, float(peak.group(1)) if peak else None)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()

    files = []
    for f in a.files:  # expand globs on Windows too
        files.extend(sorted(glob.glob(f)) or [f])

    report, sizes = [], set()
    for f in files:
        info = probe(f)
        v, au = video_stream(info), audio_stream(info)
        dur = float(info.get("format", {}).get("duration", 0) or 0)
        item = {"file": f, "duration": dur, "issues": []}
        if v:
            r = fps_of({"avg_frame_rate": v.get("r_frame_rate")})
            avg = fps_of(v)
            item.update(width=v.get("width"), height=v.get("height"), fps=round(avg, 3), vcodec=v.get("codec_name"))
            sizes.add((v.get("width"), v.get("height")))
            if abs(r - avg) > 0.05 * max(r, 1):
                item["issues"].append(f"variable frame rate (nominal {r:.2f}, average {avg:.2f}) - convert to constant before cutting")
        else:
            item["issues"].append("no video stream")
        if au:
            item.update(acodec=au.get("codec_name"), channels=au.get("channels"), sample_rate=au.get("sample_rate"))
            mean, peak = quick_loudness(f)
            item.update(mean_db=mean, peak_db=peak)
            if au.get("channels") == 1:
                item["issues"].append("mono audio (fine for voice; output will be made stereo)")
            if mean is not None and mean < -40:
                item["issues"].append(f"very quiet audio (mean {mean} dB) - check the right track is used")
            if peak is not None and peak >= -0.1:
                item["issues"].append("audio reaches 0 dB - may be clipped in the recording")
        else:
            item["issues"].append("no audio stream")
        report.append(item)

    if len(sizes) > 1:
        for item in report:
            item["issues"].append(f"files have different frame sizes: {sorted(sizes)} - assemble.py will scale to the output size")

    for item in report:
        vid = f"{item.get('width')}x{item.get('height')} @ {item.get('fps')} fps" if item.get("width") else "audio only"
        aud = f"{item.get('channels')} ch, mean {item.get('mean_db')} dB" if item.get("acodec") else "no audio"
        print(f"{item['file']}: {fmt_time(item['duration'])} | {vid} | {aud}")
        for issue in item["issues"]:
            print(f"   ! {issue}")
    if a.out:
        save_json(report, a.out)


if __name__ == "__main__":
    main()
