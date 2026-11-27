#!/usr/bin/env python3
"""Make captions from words.json, re-timed to the rough cut.

Writes a styled .ass file (for burning in) and/or a plain .srt (for YouTube/LinkedIn upload).

Usage:
  python captions.py words.json --edl edl.json --ass captions.ass --srt captions.srt
         [--size 1920x1080] [--max-chars 32] [--max-lines 2] [--highlight "Claude,skills"]
         [--font "Arial"] [--font-size 0 (auto)] [--position bottom|top] [--upper]
Without --edl, times are taken as-is (use for a video that was not cut).
"""
import argparse
import re

from vpa_common import load_json, output_offsets


def remap(words, edl):
    if not edl:
        return [dict(w) for w in words]
    pairs, _ = output_offsets(edl)
    out = []
    for w in words:
        mid = (w["start"] + w["end"]) / 2
        for seg, off in pairs:
            if seg["start"] - 0.01 <= mid <= seg["end"] + 0.01:
                s = off + max(w["start"], seg["start"]) - seg["start"]
                e = off + min(w["end"], seg["end"]) - seg["start"]
                out.append({**w, "start": s, "end": max(e, s + 0.05)})
                break
    return out


def chunk(words, max_chars, max_lines, max_dur=5.0, gap_break=0.6):
    """Group words into caption cues of up to max_lines lines of max_chars."""
    cues, cur = [], []

    def lines_of(ws):
        lines, line = [], ""
        for w in ws:
            t = w["text"]
            cand = (line + " " + t).strip()
            if len(cand) > max_chars and line:
                lines.append(line)
                line = t
            else:
                line = cand
        if line:
            lines.append(line)
        return lines

    for w in words:
        if cur:
            gap = w["start"] - cur[-1]["end"]
            too_long = len(lines_of(cur + [w])) > max_lines
            if gap > gap_break or too_long or w["end"] - cur[0]["start"] > max_dur:
                cues.append(cur)
                cur = []
        cur.append(w)
        if re.search(r"[.!?]$", w["text"]) and len(" ".join(x["text"] for x in cur)) > max_chars * 0.6:
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    out = []
    for i, c in enumerate(cues):
        start = c[0]["start"]
        end = c[-1]["end"] + 0.15
        if i + 1 < len(cues):
            end = min(end, cues[i + 1][0]["start"] - 0.02)
        out.append({"start": start, "end": max(end, start + 0.4), "lines": lines_of(c), "words": c})
    return out


def ts_srt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ts_ass(t):
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def ass_escape(text):
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words")
    ap.add_argument("--edl")
    ap.add_argument("--ass")
    ap.add_argument("--srt")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--max-chars", type=int, default=0, help="0 = auto (32 landscape, 22 vertical)")
    ap.add_argument("--max-lines", type=int, default=2)
    ap.add_argument("--highlight", default="", help="comma-separated words to show in yellow")
    ap.add_argument("--font", default="Arial")
    ap.add_argument("--font-size", type=int, default=0)
    ap.add_argument("--position", choices=["bottom", "top"], default="bottom")
    ap.add_argument("--upper", action="store_true", help="UPPER CASE captions")
    a = ap.parse_args()
    if not (a.ass or a.srt):
        raise SystemExit("Give --ass and/or --srt.")

    w, h = (int(x) for x in a.size.lower().split("x"))
    vertical = h > w
    max_chars = a.max_chars or (22 if vertical else 32)
    font_size = a.font_size or int(h * (0.045 if not vertical else 0.035))
    words = [x for x in load_json(a.words)["words"] if x.get("type", "word") == "word"]
    fillers = {"um", "umm", "uh", "uhh", "uhm", "er", "erm", "ah", "hmm", "mm"}
    words = [x for x in words if x["text"].lower().strip(".,!?") not in fillers]
    edl = load_json(a.edl) if a.edl else None
    words = remap(words, edl)
    cues = chunk(words, max_chars, a.max_lines)
    hl = {x.strip().lower() for x in a.highlight.split(",") if x.strip()}

    if a.srt:
        with open(a.srt, "w", encoding="utf-8") as f:
            for i, c in enumerate(cues, 1):
                text = "\n".join(c["lines"])
                f.write(f"{i}\n{ts_srt(c['start'])} --> {ts_srt(c['end'])}\n{text.upper() if a.upper else text}\n\n")
    if a.ass:
        align = 2 if a.position == "bottom" else 8
        margin_v = int(h * (0.06 if not vertical else 0.18))
        # Colours are &HAABBGGRR. White text, dark 30%-transparent box (BorderStyle 3).
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{a.font},{font_size},&H00FFFFFF,&H0000FFFF,&H4D000000,&H4D000000,1,0,0,0,100,100,0,0,3,{max(4, font_size // 6)},0,{align},{int(w * 0.08)},{int(w * 0.08)},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(a.ass, "w", encoding="utf-8") as f:
            f.write(header)
            for c in cues:
                out_lines = []
                for line in c["lines"]:
                    toks = []
                    for tok in line.split(" "):
                        t = ass_escape(tok.upper() if a.upper else tok)
                        if tok.lower().strip(".,!?:;") in hl:
                            t = "{\\c&H0000FFFF&}" + t + "{\\c&H00FFFFFF&}"
                        toks.append(t)
                    out_lines.append(" ".join(toks))
                body = "\\N".join(out_lines)  # built outside the f-string for Python < 3.12
                f.write(f"Dialogue: 0,{ts_ass(c['start'])},{ts_ass(c['end'])},Default,,0,0,0,,{body}\n")
    print(f"{len(cues)} caption cues from {len(words)} words" + (" (re-timed to the cut)" if edl else ""))


if __name__ == "__main__":
    main()
