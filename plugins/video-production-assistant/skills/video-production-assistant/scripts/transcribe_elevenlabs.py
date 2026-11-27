#!/usr/bin/env python3
"""Transcript with ElevenLabs Scribe v2 through the web API. Costs ElevenLabs credits.

Permission gate: without --confirm this script only checks the file and the credit
balance, prints what it WOULD send, and stops. Nothing leaves the computer.
The agent adds --confirm only after the user says yes in the chat, for that file.

Only the audio is sent (extracted to a small mono MP3 first), never the video.
Calls the ElevenLabs web API directly, so the ElevenLabs Python SDK is not needed.
The API key is read from the ELEVENLABS_API_KEY environment variable, or from
.env.local / .env in the video library folder. It is never printed.

Output is ElevenLabs JSON that transcript_normalise.py reads.

Usage:
  python _tools/transcribe_elevenlabs.py IN.mp4 --out 02_work/scribe.json            (check only)
  python _tools/transcribe_elevenlabs.py IN.mp4 --out 02_work/scribe.json --confirm  (sends, uses credits)
Options: --diarize (several speakers)  --keyterms "Brand name,Product term"
"""
import argparse, json, os, subprocess, sys, tempfile
from pathlib import Path

import requests

LIB = Path(__file__).resolve().parent.parent
DEFAULT_TERMS = ""


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


API = "https://api.elevenlabs.io/v1"


def headers():
    return {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}


def balance():
    try:
        r = requests.get(f"{API}/user/subscription", headers=headers(), timeout=30)
        r.raise_for_status()
        s = r.json()
        return s["character_count"], s["character_limit"], s.get("tier", "?")
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    ap.add_argument("--confirm", action="store_true", help="the user has approved the credit spend for this file")
    ap.add_argument("--diarize", action="store_true")
    ap.add_argument("--keyterms", default=DEFAULT_TERMS)
    ap.add_argument("--language", default="eng")
    a = ap.parse_args()

    from dotenv import load_dotenv
    for name in (".env.local", ".env"):
        load_dotenv(LIB / name)
    if not os.environ.get("ELEVENLABS_API_KEY"):
        sys.exit("No ElevenLabs key found. The user puts ELEVENLABS_API_KEY=... in .env.local in the "
                 "video library folder themselves. Never paste the key into chat.")

    mins = duration(a.input) / 60
    bal = balance()
    print(f"File: {a.input}")
    print(f"Length: {mins:.1f} min  |  Model: scribe_v2  |  Speakers: {'several' if a.diarize else 'one'}")
    if bal:
        used, limit, tier = bal
        print(f"ElevenLabs plan: {tier}  |  credits used {used:,} of {limit:,} ({limit-used:,} left)")
    print("Cost: billed per minute of audio at your plan's speech-to-text rate. Check the usage page after.")

    if not a.confirm:
        print("\nCHECK ONLY - nothing sent. Ask the user. Re-run with --confirm after they say yes.")
        return

    with tempfile.TemporaryDirectory() as tmp:
        mp3 = os.path.join(tmp, "audio.mp3")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", a.input, "-vn", "-ac", "1",
                        "-ar", "16000", "-b:a", "64k", mp3], check=True)
        terms = [t.strip() for t in a.keyterms.split(",") if t.strip()][:100]
        form = [("model_id", "scribe_v2"), ("language_code", a.language), ("timestamps_granularity", "word"),
                ("tag_audio_events", "true"), ("diarize", "true" if a.diarize else "false")]
        form += [("keyterms", t) for t in terms]
        with open(mp3, "rb") as f:
            r = requests.post(f"{API}/speech-to-text", headers=headers(), data=form,
                              files={"file": ("audio.mp3", f, "audio/mpeg")}, timeout=3600)
        if r.status_code != 200:
            sys.exit(f"ElevenLabs error {r.status_code}: {r.text[:300]}")
        data = r.json()
    data["source"] = "elevenlabs:scribe_v2"
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=str)
    words = sum(1 for w in data.get("words", []) if w.get("type") == "word")
    after = balance()
    spent = f"  |  credits spent: {after[0]-bal[0]:,}" if (bal and after) else ""
    print(f"Done: {words} words -> {a.out}{spent}")


if __name__ == "__main__":
    main()
