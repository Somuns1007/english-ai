# -*- coding: utf-8 -*-
"""
V2.0b assembly: build full 25-question candidate JSON for cet6_202606 set1/set2.

Sources per field (evidence hierarchy):
  options_en : rendered original exam pages (vision transcription)  <- FINAL evidence
  question   : analysis booklet text layer (candidate) + ASR cross-check vs audio
  transcript : analysis booklet text layer (candidate) + ASR cross-check vs audio
  answer     : official quick-key table x analysis booklet x old bank (3-source)
Everything machine_prechecked only; NEVER teacher_verified.
Authorized 2026-08-28 by product owner (injured) as temporary basis, human recheck deferred.
"""
import sys, io, json, re, os, hashlib, difflib, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\kimi-workspace\english-ai"
PILOT = ROOT + r"\backend\listening\data\v2_pilot"
OUTDIR = ROOT + r"\backend\listening\data\v2_full"
os.makedirs(OUTDIR, exist_ok=True)

sys.path.insert(0, BASE)
from v2b_options_en_data import (SET1_OPTIONS_EN, SET2_OPTIONS_EN,
                                 SET1_PAGE, SET2_PAGE, KEY_TABLE)

UNIT_META = [
    ("conversation_1", "A", "long_conversation", "Conversation One", 1, 4),
    ("conversation_2", "A", "long_conversation", "Conversation Two", 5, 8),
    ("passage_1", "B", "passage", "Passage One", 9, 11),
    ("passage_2", "B", "passage", "Passage Two", 12, 15),
    ("recording_1", "C", "recording", "Recording One", 16, 18),
    ("recording_2", "C", "recording", "Recording Two", 19, 21),
    ("recording_3", "C", "recording", "Recording Three", 22, 25),
]

def sha(t): return hashlib.sha256(t.encode("utf-8")).hexdigest()

# ---------------------------------------------------------------- stem cleaning
STEM_FIXES = [
    (r"\bWbat\b", "What"), (r"\bWby\b", "Why"), (r"\bWben\b", "When"),
    (r"\btbe\b", "the"), (r"\bspea kers\b", "speakers"), (r"\bmainl y\b", "mainly"),
    (r"\befTective\b", "effective"), (r"\bwiUpower\b", "willpower"),
    (r"\badver tisements\b", "advertisements"), (r"\bcηstals\b", "crystals"),
    (r"^明'hat\b", "What"), (r"\b由is\b", "this"), (r"\bWi出\b", "With"),
]

# stems unrecoverable from the booklet text layer; reconstructed from the
# audio question read-out (faster-whisper ASR), pending human verification.
ASR_DERIVED_STEMS = {
    ("set1", 24): "What is thought to be responsible for a fifth of road accidents across the European Union?",
}
def clean_stem(raw):
    cleaned = raw
    diffs = []
    for pat, rep in STEM_FIXES:
        new = re.sub(pat, rep, cleaned)
        if new != cleaned:
            diffs.append(f"{pat}→{rep}")
            cleaned = new
    normed = re.sub(r"\s+([,.?!])", r"\1", cleaned)
    normed = re.sub(r"\s+", " ", normed).strip()
    if normed != cleaned:
        diffs.append("whitespace/punctuation normalization")
        cleaned = normed
    return cleaned, diffs

# ------------------------------------------------------- transcript cleaning
TRANSCRIPT_RULES = [
    (r"ω", "to", "ω→to"),
    (r"由(?=[a-z])", "th", "由→th"),
    (r"(?<=\s)1(?=[a-z'])", "I", "1→I"),
    (r"(?<=\s)1\s", " I ", "standalone 1→I"),
    (r"\b0(?=[a-z])", "O", "leading 0→O"),
    (r"臼", "ee", "臼→ee"),
    (r"[ \t]+", " ", "space normalize"),
]
def clean_transcript_text(raw):
    t = raw
    applied = []
    for pat, rep, name in TRANSCRIPT_RULES:
        new = re.sub(pat, rep, t)
        if new != t:
            applied.append(name)
            t = new
    return t.strip(), applied

# ---------------------------------------------------------------- ASR check

# Manual corrections for segments whose booklet text layer is too damaged for
# rule-based cleaning. Every entry is reconstructed against the ASR read-out
# (timestamps noted) + surviving booklet fragments; recorded as
# model_cleaned_with_asr_evidence. Still machine_prechecked, NOT teacher_verified.
MANUAL_SEG_FIX = {
    ("set1", "passage_2", 4):
        "No wonder people hope to make changes without it. [13] I define willpower as using "
        "only the thought of your motivators to control your actions. Let's say your "
        "motivators are preventing diabetes and reaching a healthy weight.",
    ("set1", "passage_1", 4):
        "Women rating women with makeup said they would be more jealous of them and thought "
        "they would be more attractive to men than their non-make-up-wearing counterparts. "
        "Cosmetic products are good for more than just giving you a pretty face.",
    ("set1", "recording_1", 8):
        "The goal is to make it easier for mothers-to-be to feel confident about the type of "
        "seafood they include in their diets. The new advice recommends consumers choose a "
        "variety of fish to eat and it comes with an easy-to-understand illustration of what "
        "an appropriate portion size should be: 4 ounces for an adult and 2 ounces for "
        "children aged 4 to 7.",
    ("set2", "conversation_2", 11):
        "We review all of their medications and make sure they're taking them as prescribed. "
        "We also look for any potential drug interactions or side effects. Patient response "
        "has so far been very positive. Some have reported seeing improvements in their "
        "health, which is really rewarding to see.",
    ("set2", "conversation_2", 14):
        "It's a great idea. [8] Medication non-adherence is a big problem, especially for "
        "older patients.",
    ("set2", "conversation_2", 15):
        "We're still in the early stages of the program, but I'm hopeful that it will make "
        "a real difference for our patients.",
    ("set2", "passage_2", 3):
        "[12] A pattern in nature is any regularly repeated arrangement of shapes or colors. "
        "Some of the most striking examples include the six-sided arrays of rocks at Giant's "
        "Causeway in the United Kingdom and the colorful stripes and spots on tropical fish.",
    ("set2", "recording_3", 5):
        "However, time is of the essence as parental influence is most likely to be effective "
        "during the critical time period before age ten. [23] During adolescence, children "
        "tend to gravitate away from their parents' choices and are more influenced by their peers.",
    ("set2", "recording_3", 8):
        "[24] Dr. Egermann claims introducing children to a variety of musical styles is the "
        "key to fostering good taste in later life. By playing children a variety of genres "
        "before this critical period, research on familiarization suggests they will enjoy "
        "lots of different types of music as adults, he added.",
}
def norm(t):
    t = t.lower()
    t = re.sub(r"\[?\d+(-\d+)?\]", " ", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def best_match_ratio(candidate, asr_text):
    """Anchor containment: try ALL head/tail anchor pairs, keep the best-scoring
    window; also run a sliding-window fallback. Robust to repeated question
    prefixes like 'what does the woman ...'."""
    c = norm(candidate)
    if not c:
        return 0.0, ""
    a = norm(asr_text)
    words = c.split()
    head, tail = " ".join(words[:4]), " ".join(words[-4:])
    best, bestwin = 0.0, ""
    # all head occurrences
    starts, k = [], a.find(head)
    while k >= 0 and len(starts) < 50:
        starts.append(k)
        k = a.find(head, k + 1)
    for i in starts:
        j = a.find(tail, i)
        if j < 0:
            continue
        win = a[i:j + len(tail)]
        if len(win) > 3 * len(c) + 80:
            continue
        r = difflib.SequenceMatcher(None, c, win).ratio()
        if r > best:
            best, bestwin = r, win
    # sliding-window fallback (coarse + refine around best)
    n = len(c)
    step = max(n // 6, 15)
    coarse_best, coarse_pos = best, -1
    for k in range(0, max(len(a) - 1, 1), step):
        win = a[k:k + n]
        r = difflib.SequenceMatcher(None, c, win).ratio()
        if r > coarse_best:
            coarse_best, coarse_pos = r, k
    if coarse_pos >= 0:
        lo = max(coarse_pos - step, 0)
        for k in range(lo, min(coarse_pos + step, max(len(a) - 1, 1)), 4):
            for extra in (0, 6, -6):
                win = a[k:k + n + extra]
                r = difflib.SequenceMatcher(None, c, win).ratio()
                if r > best:
                    best, bestwin = r, win
    return round(best, 3), bestwin[:200]

THRESH_OK, THRESH_WARN = 0.75, 0.55
def status_of(r):
    return "consistent" if r >= THRESH_OK else ("check" if r >= THRESH_WARN else "MISMATCH")

# ---------------------------------------------------------------- old bank
def old_answers(setname):
    d = json.load(open(ROOT + rf"\backend\listening\data\exams\cet6_202606_{setname}.json", encoding="utf-8"))
    out = {}
    for u in d["units"]:
        for q in u["questions"]:
            out[q["number"]] = q["correct_answer"]
    return out

# ---------------------------------------------------------------- build
def build_set(setname):
    exam_id = f"cet6_202606_{setname}"
    booklet = json.load(open(os.path.join(BASE, "booklet_extract", f"{setname}_booklet.json"), encoding="utf-8"))
    pilot = json.load(open(PILOT + rf"\{exam_id}_conv1.candidate.json", encoding="utf-8"))
    opts_en = SET1_OPTIONS_EN if setname == "set1" else SET2_OPTIONS_EN
    pages = SET1_PAGE if setname == "set1" else SET2_PAGE
    keys = KEY_TABLE[setname]
    old = old_answers(setname)
    asr = json.load(open(PILOT + rf"\review_pack\machine_precheck\{exam_id}.asr.json", encoding="utf-8"))
    asr_full = " ".join(s["text"] for s in asr["segments"])

    audio_file = "2026年6月英语六级听力第1套.mp3" if setname == "set1" else "2026年6月英语六级听力第2套.m4a"
    audio_rel = f"audio/cet6_202606_{setname}." + ("mp3" if setname == "set1" else "m4a")
    analysis_pdf = f"2026年6月英语六级解析第{1 if setname=='set1' else 2}套.pdf"

    units_out, questions_out, machine = [], [], {}
    booklet_units = {u["unit_id"]: u for u in booklet["units"]}

    for idx, (uid_short, section, utype, title, lo, hi) in enumerate(UNIT_META):
        unit_id = f"{exam_id}_u{idx+1}"
        if idx == 0:
            # reuse pilot unit 1 (already vision/ASR machine-checked) verbatim
            pu = dict(pilot["unit"])
            pu["transcript"] = dict(pu["transcript"])
            pu["transcript"]["review_status"] = "machine_prechecked"
            pu["transcript"]["review_note"] = ("沿用 v2_pilot;该 unit 已经 machine_precheck 全项一致"
                                               "(选项视觉复核+ASR 锚定)。仍为 machine_prechecked,非 teacher_verified。")
            units_out.append(pu)
            for q in pilot["questions"]:
                qq = dict(q)
                qq["review_status"] = "machine_prechecked"
                qq["review_note"] = ("沿用 v2_pilot 内容;该 pilot 已经 machine_precheck 44/44 一致"
                                     "(32 选项视觉复核+8 题干/20 话轮 ASR+8 答案双源)。仍为 machine_prechecked,非 teacher_verified。")
                questions_out.append(qq)
                machine[qq["question_id"]] = {"note": "reused from v2_pilot (machine_precheck 44/44 consistent)",
                                              "machine_status": "consistent"}
            # register pilot transcript segments into machine report
            for seg in pu["transcript"]["segments"]:
                machine[seg["segment_id"]] = {"note": "reused from v2_pilot", "machine_status": "consistent"}
            continue

        bu = booklet_units[uid_short]
        # ---- transcript
        segs = []
        seg_statuses = []
        for s_i, s in enumerate(bu["transcript_segments"], start=1):
            manual = MANUAL_SEG_FIX.get((setname, uid_short, s_i))
            if manual is not None:
                cleaned, applied = manual, ["model_cleaned_with_asr_evidence"]
            else:
                cleaned, applied = clean_transcript_text(s["text_raw"])
            speaker = {"man": "M", "woman": "W", "narrator": "N"}[s["speaker"]]
            prefix = f"{speaker}: " if speaker in ("M", "W") else ""
            text = prefix + cleaned
            ratio, win = best_match_ratio(cleaned, asr_full)
            st = status_of(ratio)
            seg_statuses.append(st)
            sid = f"{unit_id}_seg{len(segs)+1:03d}"
            segs.append({"segment_id": sid, "speaker": speaker, "text": text,
                         "revision": 1, "content_hash": sha(text)})
            machine[sid] = {"kind": "transcript_segment", "candidate": cleaned,
                            "asr_similarity": ratio,
                            "machine_status": st, "ocr_noise_flag": s["ocr_noise_flag"],
                            "manual_clean": manual is not None,
                            "asr_window": win}
        n_bad = sum(1 for x in seg_statuses if x == "MISMATCH")
        n_warn = sum(1 for x in seg_statuses if x == "check")
        t_status = ("machine_prechecked" if n_bad == 0 and n_warn == 0
                    else "needs_review" if n_bad else "machine_prechecked_with_warnings")
        units_out.append({
            "unit_id": unit_id, "section": section, "type": utype, "title": title,
            "audio_path": audio_rel,
            "audio_provenance": {"source_document": audio_file, "extraction_method": "direct_copy",
                                 "review_status": "machine_prechecked"},
            "transcript": {
                "review_status": t_status,
                "provenance": {"source_document": analysis_pdf,
                               "section": f"Part II Listening Comprehension / Section {section} / {title}",
                               "extraction_method": "text_layer+rule_clean",
                               "note": "解析册文字为 candidate;机器规则清洗+ASR 锚定比对;verified 前需与录音逐句人工核对。"},
                "raw_extracted_text": " ".join(s["text_raw"] for s in bu["transcript_segments"]),
                "cleaning_diffs": ["ω→to", "由→th", "1→I", "0→O", "臼→ee", "space normalize"],
                "segments": segs,
                "revision": 1,
                "content_hash": sha(json.dumps([s["text"] for s in segs], ensure_ascii=False)),
            },
            "timing_status": "unverified_disabled",
            "timing_note": "V2.0 不提供题目级/句子级时间戳;旧 evidence_start_ms=0 一律作废。",
        })

        # ---- questions
        for q in bu["questions"]:
            n = q["number"]
            qid = f"{exam_id}_q{n:03d}"
            stem_clean, stem_diffs = clean_stem(q["stem_en_raw"])
            asr_derived = (setname, n) in ASR_DERIVED_STEMS
            if asr_derived:
                stem_clean = ASR_DERIVED_STEMS[(setname, n)]
                stem_diffs = stem_diffs + [f"booklet stem unrecoverable ({q['stem_en_raw'][:30]!r}); ASR-derived from audio read-out"]
            stem_ok = bool(re.match(r"^(What|Why|How|Which|When|Where|Who|According)", stem_clean))
            s_ratio, s_win = best_match_ratio(stem_clean, asr_full) if stem_clean else (0.0, "")
            s_st = status_of(s_ratio) if stem_clean else "MISMATCH"

            key_ans = keys[n - 1]
            booklet_ans = q["answer_booklet"]
            old_ans = old.get(n)
            ans_agree = (key_ans == booklet_ans == old_ans)
            if not ans_agree:
                print(f"!! ANSWER CONFLICT {exam_id} Q{n}: key={key_ans} booklet={booklet_ans} old={old_ans}")

            em = re.search(r"句\s*\[\s*(\d+(?:-\d+)?)\s*\]", q["analysis_raw"])
            options = []
            for li, label in enumerate("ABCD"):
                o_en = opts_en[n][li]
                o_zh = q["options_zh"].get(label, "")
                oid = f"{qid}_{label}"
                options.append({"label": label, "text_en": o_en, "text_zh": o_zh,
                                "option_id": oid, "revision": 1, "content_hash": sha(o_en)})

            field_ok = stem_ok and s_st == "consistent" and ans_agree
            q_status = "machine_prechecked" if field_ok else "needs_review"
            reasons = []
            if not stem_ok: reasons.append("stem OCR 损坏超出规则修复能力")
            if s_st != "consistent": reasons.append(f"stem-ASR {s_st}({s_ratio})")
            if not ans_agree: reasons.append("answer 三源不一致")

            questions_out.append({
                "number": n,
                "question_delivery": "audio_only",
                "options": options,
                "correct_answer": key_ans,
                "question_text": stem_clean,
                "question_text_zh": q["stem_zh"],
                "evidence_marker": f"[{em.group(1)}]" if em else None,
                "review_status": q_status,
                "review_note": "; ".join(reasons) if reasons else "机器多源核对一致",
                "provenance": {
                    "options_en": {"source_document": "2026年6月英语六级真题3套全.pdf", "page": pages[n],
                                   "extraction_method": "vision_transcription_from_rendered_page",
                                   "cleaning": "模型视觉转录;需日后真人对照原页复核"},
                    "options_zh": {"source_document": analysis_pdf, "section": f"听力 Q{n}",
                                   "extraction_method": "text_layer+rule_repair" if q.get("options_ocr_repaired") else "text_layer",
                                   "usage": "复盘辅助,考试阶段不下发"},
                    "question_text": {"source_document": analysis_pdf if not asr_derived else audio_file,
                                      "section": f"听力 Q{n}",
                                      "extraction_method": "asr_derived_from_question_readout" if asr_derived else "text_layer+rule_clean",
                                      "cleaning": "; ".join(stem_diffs) if stem_diffs else "无需修改",
                                      "asr_similarity": s_ratio,
                                      "note": "最终证据为录音" if asr_derived else "解析文本为候选;最终证据为录音"},
                    "correct_answer": {"source_document": "2026年6月英语六级真题3套全.pdf", "page": 23,
                                       "section": f"答案速查表 第{1 if setname=='set1' else 2}套",
                                       "cross_check": f"速查表={key_ans} / 解析册={booklet_ans} / 旧库={old_ans} -> {'一致' if ans_agree else '冲突'}"},
                },
                "question_id": qid,
                "revision": 1,
                "field_hashes": {
                    "options": sha(json.dumps([o["text_en"] for o in options], ensure_ascii=False)),
                    "question_text": sha(stem_clean),
                    "question_text_zh": sha(q["stem_zh"]),
                    "correct_answer": sha(key_ans),
                },
            })
            machine[qid + ".question_text"] = {"kind": "question_text", "candidate": stem_clean,
                                               "asr_similarity": s_ratio, "machine_status": s_st,
                                               "asr_window": s_win}
            machine[qid + ".correct_answer"] = {"kind": "correct_answer",
                                                "machine_status": "consistent" if ans_agree else "MISMATCH",
                                                "three_source": [key_ans, booklet_ans, old_ans]}

    record = {
        "_meta": {
            "schema": "v2_full_exam_record/0.1",
            "review_status": "machine_prechecked",
            "review_note": ("全部内容为机器多源核对(machine_prechecked),绝不冒充 teacher_verified。"
                            "2026-08-28 产品负责人因伤无法人工验收,授权机器核对为临时依据;"
                            "真人复核后置,review_pack verdict 槽保留供补 PASS。"),
            "source_level": "published_exam_collection",
            "source_level_note": "来源为市面出版真题整理资料,非官方数字源,不标记 official。",
            "generated_at": str(datetime.date.today()),
            "timing_policy": "V2.0 不重做时间戳;timing_status=unverified_disabled。",
            "pack_revision": 1,
            "question_delivery": "audio_only(试卷面无题干,题干仅由音频朗读;考试模式 payload 不得含题干/transcript/答案/解析)",
        },
        "exam_id": exam_id,
        "units": units_out,
        "questions": sorted(questions_out, key=lambda q: q["number"]),
    }
    return record, machine

all_machine = {}
for setname in ("set1", "set2"):
    record, machine = build_set(setname)
    out = os.path.join(OUTDIR, f"cet6_202606_{setname}.candidate.json")
    json.dump(record, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    all_machine.update(machine)
    n_q = len(record["questions"])
    n_mv = sum(1 for q in record["questions"] if q["review_status"] == "machine_prechecked")
    print(f"{setname}: questions={n_q} machine_prechecked={n_mv} needs_review={n_q-n_mv}")
    print(f"  wrote {out}")
    for q in record["questions"]:
        if q["review_status"] != "machine_prechecked":
            print(f"  needs_review Q{q['number']}: {q.get('review_note', '(pilot reuse)')}")

mpath = os.path.join(OUTDIR, "machine_precheck_full.json")
json.dump({"schema": "v2b_machine_precheck/0.1", "generated_at": str(datetime.date.today()),
           "status_meaning": "machine cross-check only; NOT teacher_verified",
           "fields": all_machine}, open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
c = Counter(v.get("machine_status", "n/a") for v in all_machine.values())
print("\nmachine_status:", dict(c))
print("wrote", mpath)
