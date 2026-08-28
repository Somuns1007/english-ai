# -*- coding: utf-8 -*-
"""V2.0b semantics fix (status/method labels ONLY, no content text change):
  machine_verified               -> machine_prechecked
  machine_verified_with_warnings -> machine_prechecked_with_warnings
  manual_clean_with_asr_evidence -> model_cleaned_with_asr_evidence
Then freeze baseline: SHA256 of the 5 source artifacts + release gate.
"""
import sys, io, json, os, hashlib, re, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"D:\kimi-workspace\english-ai"
FULL = ROOT + r"\backend\listening\data\v2_full"

RENAMES = [
    ("machine_verified_with_warnings", "machine_prechecked_with_warnings"),
    ("machine_verified", "machine_prechecked"),
    ("manual_clean_with_asr_evidence", "model_cleaned_with_asr_evidence"),
]

FILES = [
    FULL + r"\cet6_202606_set1.candidate.json",
    FULL + r"\cet6_202606_set2.candidate.json",
    FULL + r"\machine_precheck_full.json",
    FULL + r"\payload_assert_report.json",
    FULL + r"\payload_preview\cet6_202606_set1.exam_payload.json",
    FULL + r"\payload_preview\cet6_202606_set2.exam_payload.json",
]

def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

def rename_in_obj(o, counts):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str):
                nv = v
                for old, new in RENAMES:
                    if old in nv:
                        counts[old] += nv.count(old)
                        nv = nv.replace(old, new)
                if nv != v:
                    o[k] = nv
            else:
                rename_in_obj(v, counts)
    elif isinstance(o, list):
        for v in o:
            rename_in_obj(v, counts)

for path in FILES:
    if not os.path.exists(path):
        continue
    counts = {old: 0 for old, _ in RENAMES}
    data = json.load(open(path, encoding="utf-8"))
    rename_in_obj(data, counts)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(os.path.basename(path), {k: v for k, v in counts.items() if v})

# ---- freeze baseline
baseline = {
    "baseline_id": "v2.0b",
    "frozen_at": str(datetime.datetime.now()),
    "semantics": {
        "machine_prechecked": "模型/脚本多源自动核对一致;绝不等于 teacher_verified",
        "teacher_verified": "仅真人教师确认,当前无",
        "model_cleaned_with_asr_evidence": "模型依据 ASR+解析册完成的候选清洗,非人类教师手动修改",
        "rename_decision": "2026-08-28 状态语义修正:machine_verified→machine_prechecked;manual_clean_with_asr_evidence→model_cleaned_with_asr_evidence;未改变任何文本内容",
    },
    "release_gate": {
        "student_release_allowed": False,
        "reasons": [
            "英文选项尚未完成最终真人逐字复核",
            "部分 transcript 尚有 check 项",
            "部分 question stem/transcript 使用 ASR 辅助重建",
        ],
        "note": "数据可用于 V2.1 本地开发与验收;不得因页面完成自动视为 teacher_verified。",
    },
    "artifacts": {},
}
for path in FILES:
    if os.path.exists(path):
        baseline["artifacts"][os.path.relpath(path, ROOT)] = sha256(path)

out = FULL + r"\V2_0B_BASELINE.json"
json.dump(baseline, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nbaseline written:", out)
for k, v in baseline["artifacts"].items():
    print(f"  {v[:16]}…  {k}")
