#!/usr/bin/env python3
"""Polish the voice and lay a ducked music bed under it.

Voice chain: high-pass 80 Hz -> light noise reduction (optional) -> two-pass
loudness normalisation to the target (default -14 LUFS, true peak -1 dBTP).
Music: looped or trimmed to length, set about 20 dB under the voice, faded in
and out, and pushed down further while speech is on (side-chain ducking).
The final mix is measured and normalised again, so the file hits the target.

Usage:
  python audio_mix.py --voice roughcut.mp4 --out mix.wav
         [--music music.mp3] [--target -14] [--music-db 20]
         [--duck-ratio 6] [--release 300] [--no-denoise] [--music-fade 2]
"""
import argparse
import json
import os
import re
import tempfile

from vpa_common import duration, ffmpeg_stderr, need, run


def measure(path, target, tp, extra_filter=""):
    chain = (extra_filter + "," if extra_filter else "") + f"loudnorm=I={target}:TP={tp}:LRA=11:print_format=json"
    txt = ffmpeg_stderr(["-i", path, "-vn", "-af", chain, "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", txt, re.S)
    if not m:
        raise RuntimeError("Could not measure loudness:\n" + txt[-800:])
    return json.loads(m.group(0))


def loudnorm_two_pass(src, dst, target, tp, pre_filter=""):
    st = measure(src, target, tp, pre_filter)
    ln = (f"loudnorm=I={target}:TP={tp}:LRA=11:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
          f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true")
    chain = (pre_filter + "," if pre_filter else "") + ln
    run([need("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-vn", "-af", chain,
         "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", dst])
    return st


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--voice", required=True, help="video or audio with the voice track")
    ap.add_argument("--music")
    ap.add_argument("--out", required=True)
    ap.add_argument("--target", type=float, default=-14.0, help="integrated loudness, LUFS")
    ap.add_argument("--tp", type=float, default=-1.0, help="true peak ceiling, dBTP")
    ap.add_argument("--music-db", type=float, default=20.0, help="music level below voice, dB")
    ap.add_argument("--duck-ratio", type=float, default=6.0)
    ap.add_argument("--release", type=float, default=300.0, help="ms for music to come back up after speech")
    ap.add_argument("--music-fade", type=float, default=2.0)
    ap.add_argument("--no-denoise", action="store_true")
    a = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="vpa_audio_")
    pre = "highpass=f=80" + ("" if a.no_denoise else ",afftdn=nf=-25")
    voice = os.path.join(tmp, "voice.wav")
    st = loudnorm_two_pass(a.voice, voice, a.target, a.tp, pre)
    print(f"Voice: measured {float(st['input_i']):.1f} LUFS -> target {a.target} LUFS")

    if not a.music:
        os.replace(voice, a.out)
        print(f"Voice only -> {a.out}")
        return

    dur = duration(voice)
    music_target = a.target - a.music_db
    music = os.path.join(tmp, "music.wav")
    fade_out_start = max(dur - a.music_fade * 1.5, 0)
    run([need("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-stream_loop", "-1", "-i", a.music,
         "-t", f"{dur:.3f}", "-af", f"afade=t=in:d={a.music_fade},afade=t=out:st={fade_out_start:.3f}:d={a.music_fade * 1.5}",
         "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", os.path.join(tmp, "music_raw.wav")])
    loudnorm_two_pass(os.path.join(tmp, "music_raw.wav"), music, music_target, a.tp - 3)

    mixed = os.path.join(tmp, "mixed.wav")
    fc = (f"[1:a]asplit=2[sc][v];"
          f"[0:a][sc]sidechaincompress=threshold=0.04:ratio={a.duck_ratio}:attack=20:release={a.release}:makeup=1[duck];"
          f"[v][duck]amix=inputs=2:duration=first:normalize=0[out]")
    run([need("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-i", music, "-i", voice,
         "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-c:a", "pcm_s16le", mixed])
    final = loudnorm_two_pass(mixed, a.out, a.target, a.tp, "alimiter=limit=0.89:level=false")
    print(f"Music bed at about {music_target:.0f} LUFS before ducking (ratio {a.duck_ratio}, release {a.release} ms)")
    print(f"Mix: measured {float(final['input_i']):.1f} LUFS -> {a.target} LUFS -> {a.out}")


if __name__ == "__main__":
    main()
