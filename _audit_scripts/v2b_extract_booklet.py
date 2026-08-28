# -*- coding: utf-8 -*-
"""
V2.0b batch extractor: parse analysis booklets (解析册) into structured
unit / question / transcript candidates for both CET-6 sets.

Output: _audit_scripts/booklet_extract/{set1,set2}_booklet.json
Raw text is kept verbatim; OCR noise is flagged, not silently fixed.
"""
import json, re, os, hashlib

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "booklet_extract")
os.makedirs(OUT, exist_ok=True)

UNIT_PLAN = [
    ("conversation_1", "Conversation One", 1, 4, "conversation"),
    ("conversation_2", "Conversation Two", 5, 8, "conversation"),
    ("passage_1", "Passage One", 9, 11, "monologue"),
    ("passage_2", "Passage Two", 12, 15, "monologue"),
    ("recording_1", "Recording One", 16, 18, "monologue"),
    ("recording_2", "Recording Two", 19, 21, "monologue"),
    ("recording_3", "Recording Three", 22, 25, "monologue"),
]

FOOTER_RE = re.compile(r"2026\s*年\s*6\s*月大学英语六级考试真题答案详解.*$", re.M)

def clean_pages(raw: str) -> str:
    # join pages, drop page markers and footers
    raw = re.sub(r"===== PAGE \d+ =====", "\n", raw)
    raw = FOOTER_RE.sub("", raw)
    return raw

def find_listening_span(txt: str) -> str:
    start = txt.find("Part II Listening Comprehension")
    if start < 0:
        start = txt.find("Conversation One")
    # listening analysis ends where Part III reading analysis begins
    end_candidates = [m.start() for m in re.finditer(r"Part III", txt)]
    end = min((e for e in end_candidates if e > start), default=len(txt))
    return txt[start:end]

def split_units(span: str):
    """Return list of (unit_id, kind, q_lo, q_hi, unit_text)."""
    marks = []
    for uid, header, lo, hi, kind in UNIT_PLAN:
        idx = span.find(header)
        if idx < 0:
            raise RuntimeError(f"header not found: {header}")
        marks.append((idx, uid, lo, hi, kind))
    marks.sort()
    units = []
    for i, (idx, uid, lo, hi, kind) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(span)
        units.append((uid, kind, lo, hi, span[idx:end]))
    return units

def split_transcript_and_questions(unit_text: str, q_lo: int):
    """Transcript = text before the line starting with f'{q_lo}.'"""
    m = re.search(rf"^\s*{q_lo}\.\s", unit_text, re.M)
    if not m:
        raise RuntimeError(f"question {q_lo} start not found")
    return unit_text[:m.start()], unit_text[m.start():]

def parse_questions(qtext: str, q_lo: int, q_hi: int):
    """Split question blocks by leading 'N.' and parse each."""
    # find positions of each question number
    pos = {}
    for n in range(q_lo, q_hi + 1):
        m = re.search(rf"^\s*{n}\.\s", qtext, re.M)
        if not m:
            raise RuntimeError(f"question {n} not found")
        pos[n] = m.start()
    # end of block = start of next question or end of unit text
    questions = {}
    nums = list(range(q_lo, q_hi + 1))
    for i, n in enumerate(nums):
        end = pos[nums[i + 1]] if i + 1 < len(nums) else len(qtext)
        questions[n] = parse_one_question(qtext[pos[n]:end], n)
    return questions

STEM_SPLIT_RE = re.compile(r"(?<=[?.!])\s+(?=[\u4e00-\u9fff])")
OPT_TOKEN_RE = re.compile(r"([ABCD])\s*[)）]")
ANSWER_RE = re.compile(r"答案为\s*([ABCD])[^)）]{0,4}[)）]")

def repair_option_zone(zone: str) -> str:
    """Fix common OCR damage in the 2-column option zone.

    - '0)' (zero) is an OCR rendering of 'D)'.
    - '。 。' at a column break is an OCR rendering of '。 C)'.
    Only applied as fallback when the normal token scan fails.
    """
    fixed_lines = []
    for ln in zone.splitlines():
        if not OPT_TOKEN_RE.search(ln):
            fixed_lines.append(ln)
            continue
        # D as zero (may be preceded by whitespace, never by a digit/letter)
        ln2 = re.sub(r"(?<![0-9A-Za-z])0\s*[)）]", " D) ", ln)
        # C as bare '。': only when line has an A/B token and exactly one '。 。'
        if ln2.count("。 。") == 1 and re.search(r"[AB]\s*[)）]", ln2) and not re.search(r"C\s*[)）]", ln2):
            ln2 = ln2.replace("。 。", "。 C) ", 1)
        fixed_lines.append(ln2)
    return "\n".join(fixed_lines)

def parse_one_question(block: str, n: int):
    lines = block.strip().splitlines()
    # stem: from after 'N.' up to the first option-token line
    first_opt_line = None
    for i, ln in enumerate(lines):
        if OPT_TOKEN_RE.search(ln):
            first_opt_line = i
            break
    if first_opt_line is None:
        raise RuntimeError(f"no options found in Q{n}")
    stem_raw = " ".join(l.strip() for l in lines[:first_opt_line])
    stem_raw = re.sub(rf"^\s*{n}\.\s*", "", stem_raw).strip()
    # split EN / ZH: first CJK char that begins the Chinese translation, i.e.
    # a CJK char followed by another CJK char/punct (a lone leading CJK glyph
    # like 明 is OCR garbage inside the English stem, e.g. '明'hat' = 'What').
    m = re.search(r"[\u4e00-\u9fff](?=[\u4e00-\u9fff\uff0c\u3001\u3002\uff1f])", stem_raw)
    if m:
        stem_en = stem_raw[: m.start()].strip()
        stem_zh = stem_raw[m.start():].strip()
    else:
        stem_en, stem_zh = stem_raw, ""

    # options + analysis: from first option line onward
    rest = "\n".join(lines[first_opt_line:])
    # cut analysis part at the answer marker line
    ans_m = ANSWER_RE.search(rest)
    answer = ans_m.group(1) if ans_m else None
    opt_zone = rest[: ans_m.start()] if ans_m else rest
    analysis_zone = rest[ans_m.start():] if ans_m else ""

    # tokenize options A)..D)
    def tokenize(z):
        toks = list(OPT_TOKEN_RE.finditer(z))
        opts = {}
        for i, t in enumerate(toks):
            label = t.group(1)
            if label in opts:
                continue
            end = toks[i + 1].start() if i + 1 < len(toks) else len(z)
            txt = z[t.end():end].strip()
            txt = re.sub(r"\s+", " ", txt)
            opts[label] = txt
        return opts
    options_zh = tokenize(opt_zone)
    ocr_repaired = False
    if set(options_zh) != {"A", "B", "C", "D"}:
        repaired = repair_option_zone(opt_zone)
        opts2 = tokenize(repaired)
        if set(opts2) == {"A", "B", "C", "D"}:
            options_zh = opts2
            ocr_repaired = True
    return {
        "number": n,
        "stem_en_raw": stem_en,
        "stem_zh": stem_zh,
        "options_zh": options_zh,
        "options_ocr_repaired": ocr_repaired,
        "answer_booklet": answer,
        "analysis_raw": re.sub(r"\s+", " ", analysis_zone).strip(),
    }

OCR_NOISE_RE = re.compile(r"[由ω出臼伎谝♀]|(?<=[a-zA-Z])\d(?=[a-zA-Z])|ffi|ﬀ")

def segment_transcript(transcript: str, kind: str, uid: str):
    """Conversation: split by speaker turns. Monologue: split into sentences."""
    transcript = transcript.strip()
    segs = []
    if kind == "conversation":
        # find speaker markers M:/W: (allow spacing noise)
        toks = list(re.finditer(r"(?:^|\n)\s*([MW])\s*[:：]", transcript))
        for i, t in enumerate(toks):
            speaker = "man" if t.group(1) == "M" else "woman"
            end = toks[i + 1].start() if i + 1 < len(toks) else len(transcript)
            text = transcript[t.end():end].strip()
            text = re.sub(r"\s+", " ", text)
            if text:
                segs.append({"speaker": speaker, "text_raw": text})
    else:
        # sentence split on . ? ! followed by space+capital/quote
        parts = re.split(r"(?<=[.?!])\s+(?=[A-Z“\"[])", transcript.replace("\n", " "))
        buf = ""
        for p in parts:
            p = p.strip()
            if not p:
                continue
            buf = (buf + " " + p).strip()
            if len(buf) > 120:
                segs.append({"speaker": "narrator", "text_raw": buf})
                buf = ""
        if buf:
            segs.append({"speaker": "narrator", "text_raw": buf})
    for i, s in enumerate(segs):
        s["segment_id"] = f"{uid}_s{i+1:02d}"
        s["ocr_noise_flag"] = bool(OCR_NOISE_RE.search(s["text_raw"]))
        s["content_hash"] = hashlib.sha256(s["text_raw"].encode("utf-8")).hexdigest()[:16]
    return segs

def extract_set(setname: str):
    raw = open(os.path.join(BASE, f"analysis_{setname}_full.txt"), encoding="utf-8").read()
    span = find_listening_span(clean_pages(raw))
    data = {"exam_id": f"cet6_202606_{setname}", "units": []}
    for uid, kind, lo, hi, unit_text in split_units(span):
        transcript, qtext = split_transcript_and_questions(unit_text, lo)
        questions = parse_questions(qtext, lo, hi)
        segments = segment_transcript(transcript, kind, uid)
        data["units"].append({
            "unit_id": uid,
            "kind": kind,
            "q_range": [lo, hi],
            "transcript_segments": segments,
            "questions": [questions[n] for n in range(lo, hi + 1)],
        })
    out = os.path.join(OUT, f"{setname}_booklet.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # summary
    for u in data["units"]:
        noisy = sum(1 for s in u["transcript_segments"] if s["ocr_noise_flag"])
        qs = u["questions"]
        missing_opt = [q["number"] for q in qs if len(q["options_zh"]) != 4]
        missing_ans = [q["number"] for q in qs if not q["answer_booklet"]]
        missing_zh = [q["number"] for q in qs if not q["stem_zh"]]
        print(f"{setname} {u['unit_id']}: segs={len(segments)} noisy={noisy} "
              f"opt_missing={missing_opt} ans_missing={missing_ans} zh_missing={missing_zh}")

if __name__ == "__main__":
    extract_set("set1")
    extract_set("set2")
