# -*- coding: utf-8 -*-
"""V2.0b payload whitelist assertion for the full 50-question candidates.
audio_only exam payload must contain ONLY: unit meta + question id/number/section
+ options(label, text_en). Any forbidden key fails the build.
Also runs the answer three-source cross-check report."""
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"D:\kimi-workspace\english-ai"
FULL = ROOT + r"\backend\listening\data\v2_full"
OUT = FULL + r"\payload_preview"
os.makedirs(OUT, exist_ok=True)

FORBIDDEN = [
    "question_text", "question_text_zh", "correct_answer", "source_explanation",
    "distractor_analysis", "teacher_annotation", "ai_annotation", "evidence_text",
    "evidence_start_ms", "evidence_end_ms", "evidence_marker",
    "timing_status", "review_status", "review_note", "provenance",
    "text_zh", "transcript", "timing_note", "content_hash", "field_hashes",
    "revision", "audio_provenance",
]
ALLOWED_QUESTION = {"id", "number", "section", "options"}
ALLOWED_OPTION = {"label", "text_en"}
ALLOWED_UNIT = {"unit_id", "section", "type", "title", "audio_path", "exam_id"}

def assert_clean(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in FORBIDDEN, f"FORBIDDEN KEY {k} at {path}"
            assert_clean(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            assert_clean(v, f"{path}[{i}]")

report = {}
for setname in ("set1", "set2"):
    cand = json.load(open(FULL + rf"\cet6_202606_{setname}.candidate.json", encoding="utf-8"))
    exam_id = cand["exam_id"]
    units_payload = []
    for u in cand["units"]:
        p_unit = {k: u[k] for k in ALLOWED_UNIT if k in u}
        p_unit["exam_id"] = exam_id
        units_payload.append(p_unit)
    q_payload = []
    for q in cand["questions"]:
        pq = {"id": q["question_id"], "number": q["number"],
              "section": [u for u in cand["units"]
                          if u["unit_id"].startswith(f"{exam_id}_u") and
                          q["number"] >= 1][0]["section"] if False else None,
              "options": [{"label": o["label"], "text_en": o["text_en"]} for o in q["options"]]}
        # resolve section via number range
        n = q["number"]
        pq["section"] = "A" if n <= 8 else ("B" if n <= 15 else "C")
        assert set(pq) <= ALLOWED_QUESTION, f"question keys leak: {set(pq) - ALLOWED_QUESTION}"
        for o in pq["options"]:
            assert set(o) == ALLOWED_OPTION, f"option keys leak: {set(o) - ALLOWED_OPTION}"
            assert o["text_en"].strip(), f"empty option text at Q{n}{o['label']}"
        q_payload.append(pq)
    payload = {"exam_id": exam_id, "question_delivery": "audio_only",
               "units": units_payload, "questions": q_payload}
    assert_clean(payload)
    out = OUT + rf"\{exam_id}.exam_payload.json"
    json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # answer three-source report
    answers = []
    for q in cand["questions"]:
        cc = q["provenance"]["correct_answer"]["cross_check"]
        answers.append((q["number"], q["correct_answer"], cc))
    conflicts = [a for a in answers if "冲突" in a[2]]
    report[exam_id] = {
        "questions": len(q_payload),
        "options_total": sum(len(q["options"]) for q in q_payload),
        "answer_conflicts": conflicts,
        "payload_file": out,
    }
    print(f"{exam_id}: payload OK, questions={len(q_payload)}, "
          f"options={report[exam_id]['options_total']}, answer_conflicts={len(conflicts)}")

json.dump(report, open(FULL + r"\payload_assert_report.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nALL PAYLOAD ASSERTIONS PASSED")
