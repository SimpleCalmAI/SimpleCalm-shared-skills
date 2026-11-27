#!/usr/bin/env python3
"""Free local transcript with word timings, using faster-whisper on the CPU.

Output is Whisper-style JSON (segments[].words[]) that transcript_normalise.py reads.
Needs: pip install -r requirements.txt (faster-whisper, numpy). If the video library has its
own Python environment (_tools/venv), run this script with that Python.
The speech model is downloaded once into a models/ folder next to this script (in a library,
_tools/models), so nothing lands in the user's home folder. Delete that folder to remove it.
A model that an earlier version of this skill already downloaded to the Hugging Face cache
(~/.cache/huggingface/hub) is used from there, so it is not downloaded a second time.

Example: python _tools/transcribe_local.py IN.mp4 --out 02_work/whisper.json

Usage: transcribe_local.py INPUT --out OUT.json [--model medium.en] [--language en] [--prompt "Names, product terms"]
"""
import argparse, json, os, subprocess, time
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel

MODELS = Path(__file__).resolve().parent / "models"


def model_folder(name):
    """Folder to load the speech model from: models/ next to this script, or None for the
    Hugging Face cache when an earlier version of this skill already downloaded the model there."""
    repo = "models--Systran--faster-whisper-" + name
    if (MODELS / repo).is_dir():
        return str(MODELS)
    hub = os.environ.get("HF_HUB_CACHE") or os.path.join(
        os.environ.get("HF_HOME") or os.path.join(Path.home(), ".cache", "huggingface"), "hub")
    if list(Path(hub, repo, "snapshots").glob("*/model.bin")):
        print(f"Using the {name} model already in {hub} (downloaded by an earlier version of this skill).", flush=True)
        return None
    return str(MODELS)


def load_audio(path, sr=16000):
    """Decode any audio/video file to 16 kHz mono float32 with FFmpeg (avoids PyAV version clashes)."""
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("input")
ap.add_argument("--out", required=True)
ap.add_argument("--model", default="medium.en", help="tiny.en, base.en, small.en, medium.en, large-v3 (use small.en on 8 GB machines)")
ap.add_argument("--language", default="en")
ap.add_argument("--prompt", default="", help="names and terms to help spelling")
ap.add_argument("--threads", type=int, default=0)
a = ap.parse_args()

t0 = time.time()
model = WhisperModel(a.model, device="cpu", compute_type="int8", cpu_threads=a.threads, download_root=model_folder(a.model))
segs, info = model.transcribe(load_audio(a.input), language=a.language, word_timestamps=True, vad_filter=False,
                              initial_prompt=a.prompt or None, condition_on_previous_text=False)
out = {"source": "faster-whisper:" + a.model, "language": info.language, "duration": info.duration, "segments": []}
for s in segs:
    out["segments"].append({"start": s.start, "end": s.end, "text": s.text.strip(),
                            "words": [{"word": w.word.strip(), "start": w.start, "end": w.end, "probability": w.probability} for w in (s.words or [])]})
    print(f"[{s.start:7.1f}s] {s.text.strip()}", flush=True)
with open(a.out, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
el = time.time() - t0
print(f"Done: {info.duration:.0f}s of audio in {el:.0f}s ({info.duration/el:.2f}x real time) -> {a.out}")
