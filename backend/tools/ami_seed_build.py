# -*- coding: utf-8 -*-
"""Phase 7.6: 用 AMI ES2008a 真实音频走通完整 ingestion(经 HTTP API + 教师口令)。

分阶段执行: python -m tools.ami_seed_build <stage>
  upload   上传音频 + AMI attribution/许可元数据
  asr      触发 ASR(长任务, 后台轮询)
  segment  自动切分 + 规则匹配(自动候选, 供对照)
  clips    按 DA 候选窗口手工创建 14 个教学 clip(含标签)
  approve  教师审核: 批准 clip + asset, 确认 expression 匹配
  status   查看当前状态

服务器需已在 :8000 运行且配置 TEACHER_TOKEN(读 .env)。
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "http://localhost:8000/api/listening"
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "listening" / "data" / "_extract_raw"
CANDIDATES = json.loads((RAW / "ami_es2008a_candidates.json").read_text(encoding="utf-8"))

# 教师(开发者扮演)从 53 个 DA 候选窗口中选出的 14 个: 覆盖 8 类交际功能, 互不重叠
SELECTED = [0, 1, 2, 3, 4, 5, 6, 8, 11, 15, 25, 29, 31, 43]

TOKEN = None
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if line.startswith("TEACHER_TOKEN="):
        TOKEN = line.split("=", 1)[1].strip()
assert TOKEN, "backend/.env 缺少 TEACHER_TOKEN"

ASSET_TITLE = "AMI Meeting Corpus ES2008a (scenario meeting: design team kick-off)"


def req(method: str, path: str, body=None, timeout=280):
    url = BASE + path
    data = None
    headers = {"X-Teacher-Token": TOKEN}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def find_asset():
    assets = req("GET", "/teacher/corpus/assets")["data"]
    return next((a for a in assets if a["title"] == ASSET_TITLE), None)


def stage_upload():
    asset = find_asset()
    if asset:
        print("已存在:", asset["asset_id"])
        return
    wav = RAW / "ES2008a.Mix-Headset.wav"
    boundary = "----amiboundary"
    meta = {
        "title": ASSET_TITLE,
        "source_name": "AMI Meeting Corpus (Univ. of Edinburgh / Idiap / TNO / Brno)",
        "source_url": "https://groups.inf.ed.ac.uk/ami/corpus/",
        "license": "CC BY 4.0",
        "permission_status": "verified_open_license",
    }
    q = "&".join(f"{k}={urllib.parse.quote(v)}" for k, v in meta.items())
    file_bytes = wav.read_bytes()
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"ES2008a.Mix-Headset.wav\"\r\nContent-Type: audio/x-wav\r\n\r\n"
    ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()
    r = urllib.request.Request(
        f"{BASE}/teacher/corpus/assets?{q}", data=body, method="POST",
        headers={"X-Teacher-Token": TOKEN,
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(r, timeout=280) as resp:
        print(json.loads(resp.read().decode())["data"]["asset_id"])


def stage_asr():
    asset = find_asset()
    assert asset, "先 upload"
    if asset["pipeline_status"] != "uploaded":
        print("ASR 已做:", asset["pipeline_status"])
        return
    import threading

    def fire():
        try:
            req("POST", f"/teacher/corpus/assets/{asset['asset_id']}/run-asr", {}, timeout=1)
        except Exception:
            pass  # 客户端超时无所谓, 服务端继续处理

    threading.Thread(target=fire, daemon=True).start()
    print("ASR 已触发, 轮询状态…")
    for _ in range(120):
        time.sleep(10)
        a = find_asset()
        st = a["pipeline_status"]
        if st != "uploaded":
            print("ASR 完成:", st, "| segments:", len(a["asr_segments"]),
                  "| confidence:", a["asr_confidence"])
            return
        print(".", end="", flush=True)
    raise SystemExit("ASR 超时(20 分钟)")


def stage_segment():
    asset = find_asset()
    r = req("POST", f"/teacher/corpus/assets/{asset['asset_id']}/run-segmentation", {})
    print("自动切分:", r["data"])
    r = req("POST", f"/teacher/corpus/assets/{asset['asset_id']}/run-matching", {})
    print("自动匹配:", r["data"])


def _features_of(text: str) -> list:
    feats = set()
    if re.search(r"\b(um+|uh+|em+|erm)\b", text, re.I):
        feats.add("hesitation")
    if re.search(r"\b(well|so|okay|i mean|you know|like)\b", text, re.I):
        feats.add("discourse_marker")
    if re.search(r"\b(\w+) \1\b", text, re.I):  # "don don't" 类
        feats.add("self_correction")
    return sorted(feats)


def stage_clips():
    asset = find_asset()
    existing = {c["start_ms"] for c in
                req("GET", f"/teacher/corpus/assets/{asset['asset_id']}")["data"]["clips"]}
    for idx in SELECTED:
        w = CANDIDATES[idx]
        start_ms = int(w["start_s"] * 1000)
        # 音频实际时长可能略短于注释窗口, 收敛到素材时长内
        end_ms = min(int(w["end_s"] * 1000), (asset.get("duration_ms") or 0) - 100)
        if start_ms in existing:
            print(f"窗口 {idx} 已存在, 跳过")
            continue
        clip = req("POST", f"/teacher/corpus/assets/{asset['asset_id']}/clips", {
            "start_ms": start_ms,
            "end_ms": end_ms,
            "transcript": w["transcript"],
            "speaker_info": ",".join(w["speakers"]),
        })["data"]
        words = len(re.findall(r"[a-z']+", w["transcript"], re.I))
        wps = words / max(w["duration_s"], 1)
        req("PUT", f"/teacher/corpus/clips/{clip['clip_id']}", {
            "scenario_tags": ["workplace", "meeting"],
            "communicative_function": w["comm_functions"][0],
            "difficulty": "hard" if wps > 2.6 else "medium",
            "accent": "mixed_non_native",
            "speaker_count": len(w["speakers"]),
            "speech_rate": "fast" if wps > 2.6 else "normal",
            "listening_features": _features_of(w["transcript"]),
        })
        print(f"窗口 {idx}: clip {clip['clip_id']} {w['duration_s']}s "
              f"{w['comm_functions']} wps={wps:.1f}")


def stage_retag():
    """clips 已创建但标签未落库时(历史 bug), 按 start_ms 找回并补标签。"""
    asset = find_asset()
    clips = req("GET", f"/teacher/corpus/assets/{asset['asset_id']}")["data"]["clips"]
    by_start = {c["start_ms"]: c for c in clips if c.get("origin") == "manual"}
    for idx in SELECTED:
        w = CANDIDATES[idx]
        start_ms = int(w["start_s"] * 1000)
        clip = by_start.get(start_ms)
        if not clip:
            print(f"窗口 {idx}: 未找到 clip, 跳过")
            continue
        words = len(re.findall(r"[a-z']+", w["transcript"], re.I))
        wps = words / max(w["duration_s"], 1)
        req("PUT", f"/teacher/corpus/clips/{clip['clip_id']}", {
            "scenario_tags": ["workplace", "meeting"],
            "communicative_function": w["comm_functions"][0],
            "difficulty": "hard" if wps > 2.6 else "medium",
            "accent": "mixed_non_native",
            "speaker_count": len(w["speakers"]),
            "speech_rate": "fast" if wps > 2.6 else "normal",
            "listening_features": _features_of(w["transcript"]),
        })
        print(f"窗口 {idx}: retagged {clip['clip_id']}")


def stage_approve():
    asset = find_asset()
    detail = req("GET", f"/teacher/corpus/assets/{asset['asset_id']}")["data"]
    approved = 0
    for clip in detail["clips"]:
        if clip.get("origin") != "manual":
            continue  # 自动切分候选保持 pending, 不批量批准
        if clip["review_status"] == "approved":
            approved += 1
            continue
        for m in clip["expression_matches"]:
            if m.get("status") == "candidate":
                req("POST", f"/teacher/corpus/clips/{clip['clip_id']}/matches",
                    {"expression_id": m["expression_id"], "action": "approve"})
        req("POST", f"/teacher/corpus/clips/{clip['clip_id']}/review", {"action": "approve"})
        approved += 1
        print("approved:", clip["clip_id"], f"{clip['start_ms']}-{clip['end_ms']}")
    if asset["review_status"] != "approved":
        req("POST", f"/teacher/corpus/assets/{asset['asset_id']}/review", {"action": "approve"})
        print("asset approved")
    print(f"共 {approved} clips")


def stage_status():
    asset = find_asset()
    if not asset:
        print("无 asset")
        return
    detail = req("GET", f"/teacher/corpus/assets/{asset['asset_id']}")["data"]
    print("asset:", asset["asset_id"], asset["pipeline_status"], asset["review_status"])
    for c in detail["clips"]:
        matches = [f"{m['expression_id']}({m['status']})" for m in c["expression_matches"]]
        print(f"  {c['clip_id'][:16]} {c['start_ms']:>7}-{c['end_ms']:>7} "
              f"{c['origin']:>6} {c['review_status']:>15} cf={c['communicative_function']} "
              f"feat={c['listening_features']} match={matches}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "status"
    {
        "upload": stage_upload,
        "asr": stage_asr,
        "segment": stage_segment,
        "clips": stage_clips,
        "retag": stage_retag,
        "approve": stage_approve,
        "status": stage_status,
    }[stage]()
