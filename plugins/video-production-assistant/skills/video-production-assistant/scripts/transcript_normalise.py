#!/usr/bin/env python3
"""Convert a transcript with word timings into the one format the other scripts read.

Accepts: ElevenLabs speech-to-text JSON (words with type word/spacing/audio_event),
OpenAI Whisper / faster-whisper JSON (segments[].words[]), or a plain list of
{"word"|"text", "start", "end"}.

Output (words.json):
{"source": "...", "words": [{"text": "Hello", "start": 0.12, "end": 0.45, "type": "word"}, ...]}
type is "word" or "event" (laughter, music and other non-speech tags).

Usage: python transcript_normalise.py RAW.json --out words.json [--offset 0.0]
"""
import argparse

from vpa_common import load_json, save_json


def from_elevenlabs(data):
    out = []
    for w in data.get("words", []):
        kind = w.get("type", "word")
        if kind == "spacing":
            continue
        text = (w.get("text") or "").strip()
        if not text:
            continue
        out.append({"text": text, "start": float(w["start"]), "end": float(w["end"]),
                    "type": "event" if kind == "audio_event" else "word",
                    **({"speaker": w["speaker_id"]} if w.get("speaker_id") else {})})
    return out


def from_whisper(data):
    out = []
    for seg in data.get("segments", []):
        words = seg.get("words") or []
        if not words:  # segment-level only: spread evenly (rough, but usable for captions)
            toks = (seg.get("text") or "").split()
            if not toks:
                continue
            step = (seg["end"] - seg["start"]) / len(toks)
            for i, t in enumerate(toks):
                out.append({"text": t, "start": seg["start"] + i * step,
                            "end": seg["start"] + (i + 1) * step, "type": "word", "estimated": True})
            continue
        for w in words:
            text = (w.get("word") or w.get("text") or "").strip()
            if text and w.get("start") is not None:
                out.append({"text": text, "start": float(w["start"]), "end": float(w["end"]), "type": "word"})
    return out


def from_list(data):
    out = []
    for w in data:
        text = (w.get("word") or w.get("text") or "").strip()
        if text:
            out.append({"text": text, "start": float(w["start"]), "end": float(w["end"]),
                        "type": w.get("type", "word")})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw")
    ap.add_argument("--out", required=True)
    ap.add_argument("--offset", type=float, default=0.0, help="seconds to add to every time (if the transcript was made from a trimmed file)")
    a = ap.parse_args()

    data = load_json(a.raw)
    if isinstance(data, list):
        words, src = from_list(data), "list"
    elif "segments" in data:
        words, src = from_whisper(data), "whisper"
    elif "words" in data:
        words, src = (from_list(data["words"]), "words-list") if data["words"] and "word" in data["words"][0] else (from_elevenlabs(data), "elevenlabs")
    else:
        raise SystemExit("Unknown transcript format: expected 'words' or 'segments'.")

    for w in words:
        w["start"] = round(w["start"] + a.offset, 3)
        w["end"] = round(max(w["end"] + a.offset, w["start"] + 0.01), 3)
    words.sort(key=lambda w: w["start"])
    save_json({"source": src, "words": words}, a.out)
    n_est = sum(1 for w in words if w.get("estimated"))
    print(f"{len(words)} words from {src} transcript -> {a.out}")
    if n_est:
        print(f"WARNING: {n_est} words had no word-level timing; times are estimates. Re-run the transcript with word timestamps before cutting.")


if __name__ == "__main__":
    main()
