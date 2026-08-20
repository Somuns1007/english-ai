# -*- coding: utf-8 -*-
"""Phase 7: Authentic Corpus Ingestion 最小链路。

流水线(每步独立状态, 失败可重试, 不做黑箱):
    uploaded → asr_done → segmented → matched → (clips) → approved corpus

纪律:
- 只处理用户拥有合法使用权的内容: permission_status=unverified 的 asset 不能被 approve。
- ASR 结果不视为可靠 transcript: raw_asr_text 保留, 教师修改产生新 revision, 不覆盖原始 ASR。
- 切片保留上下文(context_before/after), 按停顿/语义边界切, 不按固定秒数硬切。
- Expression 匹配只做规则匹配(match_type: exact_expression/target_surface/related_expression;
  match_method: verbatim/normalized; 每条命中带 confidence), 命中为 candidate,
  教师审核后才算正式关联(目前先标注, 不自动生效)。
- authentic_clip 与 official_exam / ai_generated 严格区分, source_type 独立。
"""
import json
import re
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .expression_service import expression_repo
from .repository import DATA_DIR, new_id, student_repo

CORPUS_DIR = DATA_DIR / "corpus"
CORPUS_AUDIO_DIR = CORPUS_DIR / "audio"

ALLOWED_PERMISSION = {"verified_open_license", "owned"}
PIPELINE_STEPS = ("uploaded", "asr_done", "segmented", "matched")

# 切分规则参数(不按固定秒数硬切)
PAUSE_SPLIT_MS = 800      # 段间停顿 ≥0.8s 且当前 clip 够长 → 切
CLIP_MIN_MS = 6000        # clip 最短 6s(再短的停顿不切)
CLIP_TARGET_MAX_MS = 25000  # clip 超过 25s 时, 遇到停顿优先切
CLIP_HARD_MAX_MS = 40000  # 40s 强制切(保底)

_whisper_model = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_model():
    """懒加载并缓存 Whisper 模型(tiny.en, CPU)。"""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        _whisper_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    return _whisper_model


def _audio_duration_ms(path: Path) -> Optional[int]:
    try:
        if path.suffix == ".wav":
            with wave.open(str(path), "rb") as w:
                return int(w.getnframes() / w.getframerate() * 1000)
        import av

        with av.open(str(path)) as c:
            if c.duration:
                return int(c.duration / 1000)
    except Exception:
        return None
    return None


# ---------- 1. 上传 ----------

def create_asset(
    file_bytes: bytes,
    filename: str,
    title: str,
    source_name: str,
    source_url: Optional[str],
    license_: str,
    permission_status: str,
) -> dict:
    suffix = Path(filename).suffix.lower() or ".bin"
    asset_id = new_id("asset")
    CORPUS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    rel_path = f"corpus/audio/{asset_id}{suffix}"
    abs_path = DATA_DIR / rel_path
    abs_path.write_bytes(file_bytes)

    asset = {
        "asset_id": asset_id,
        "title": title,
        "source_name": source_name,
        "source_url": source_url,
        "license": license_,
        "permission_status": permission_status,
        "source_type": "authentic_clip",
        "file_path": rel_path,
        "duration_ms": _audio_duration_ms(abs_path),
        "uploaded_at": _utc_now(),
        "review_status": "pending_teacher",
        "pipeline_status": "uploaded",
        "transcript_status": "none",
    }
    return student_repo.create_corpus_asset(asset)


def asset_audio_path(asset_id: str) -> Optional[Path]:
    asset = student_repo.get_corpus_asset(asset_id)
    if not asset or not asset.get("file_path"):
        return None
    path = (DATA_DIR / asset["file_path"]).resolve()
    if not str(path).startswith(str(CORPUS_DIR.resolve())):
        return None
    return path if path.exists() else None


# ---------- 2. ASR ----------

def run_asr(asset_id: str) -> Optional[dict]:
    """faster-whisper 转写。结果只是原始 ASR, 不视为可靠 transcript。"""
    asset = student_repo.get_corpus_asset(asset_id)
    if not asset:
        return None
    path = asset_audio_path(asset_id)
    if not path:
        student_repo.update_corpus_asset(asset_id, {"pipeline_error": "音频文件缺失"})
        return {"error": "音频文件缺失"}

    model = _get_model()
    segments_raw, info = model.transcribe(str(path), language="en")
    segments = []
    logprobs = []
    for seg in segments_raw:
        segments.append({
            "start_ms": int(seg.start * 1000),
            "end_ms": int(seg.end * 1000),
            "text": seg.text.strip(),
            "avg_logprob": round(seg.avg_logprob, 3),
            "no_speech_prob": round(seg.no_speech_prob, 3),
        })
        logprobs.append(seg.avg_logprob)
    raw_text = " ".join(s["text"] for s in segments)
    confidence = None
    if logprobs:
        import math

        confidence = round(sum(math.exp(lp) for lp in logprobs) / len(logprobs), 3)

    student_repo.update_corpus_asset(asset_id, {
        "asr_segments": segments,
        "raw_asr_text": raw_text,
        "asr_confidence": confidence,
        "transcript_status": "asr_raw",
        "pipeline_status": "asr_done",
        "pipeline_error": None,
    })
    return {"segments": len(segments), "confidence": confidence, "language": info.language}


# ---------- 3. 语义/停顿切分 ----------

def run_segmentation(asset_id: str) -> Optional[dict]:
    """按停顿与长度规则切分候选 clip, 保留上下文。重跑时清除未审核旧候选。"""
    asset = student_repo.get_corpus_asset(asset_id)
    if not asset:
        return None
    segments = asset.get("asr_segments") or []
    if not segments:
        return {"error": "请先运行 ASR"}

    student_repo.delete_corpus_clips(asset_id)

    clips: list[list[dict]] = []
    current: list[dict] = []
    for i, seg in enumerate(segments):
        current.append(seg)
        clip_dur = seg["end_ms"] - current[0]["start_ms"]
        next_seg = segments[i + 1] if i + 1 < len(segments) else None
        pause = (next_seg["start_ms"] - seg["end_ms"]) if next_seg else None
        should_split = False
        if next_seg is None:
            should_split = True
        elif clip_dur >= CLIP_HARD_MAX_MS:
            should_split = True
        elif pause is not None and pause >= PAUSE_SPLIT_MS and clip_dur >= CLIP_MIN_MS:
            should_split = True
        elif clip_dur >= CLIP_TARGET_MAX_MS and pause is not None and pause > 200:
            should_split = True
        if should_split:
            clips.append(current)
            current = []

    created = []
    for idx, group in enumerate(clips):
        transcript = " ".join(s["text"] for s in group)
        context_before = " ".join(s["text"] for s in clips[idx - 1]) if idx > 0 else ""
        context_after = " ".join(s["text"] for s in clips[idx + 1]) if idx + 1 < len(clips) else ""
        clip = {
            "clip_id": new_id("clip"),
            "asset_id": asset_id,
            "start_ms": group[0]["start_ms"],
            "end_ms": group[-1]["end_ms"],
            "transcript": transcript,
            "context_before": context_before[-300:],
            "context_after": context_after[:300],
            "speaker_info": None,
            "scenario_tags": "[]",
            "communicative_function": None,
            "difficulty": None,
            "expression_matches": "[]",
            "review_status": "pending_teacher",
            "revision": 1,
            "created_at": _utc_now(),
        }
        student_repo.create_corpus_clip(clip)
        created.append(clip["clip_id"])

    student_repo.update_corpus_asset(asset_id, {
        "pipeline_status": "segmented",
        "pipeline_error": None,
    })
    return {"clips_created": len(created)}


# ---------- 4. Expression 规则匹配 ----------

_WORD_RE = re.compile(r"[a-z']+")


def _normalize(text: str) -> str:
    """小写 + 去标点 + 折叠空白, 供 normalized matching。"""
    return " ".join(_WORD_RE.findall(text.lower()))


def _expression_match_index() -> list:
    """构造匹配索引: exact expression / target_surface / related_expressions。"""
    index = []
    for e in expression_repo.list_expressions():
        entries = [(e["expression"], "exact_expression")]
        entries += [(r, "related_expression") for r in e.get("related_expressions", [])]
        for s in expression_repo.scenarios_for(e["expression_id"]):
            surface = s.get("target_surface") or s["target_expression"]
            entries.append((surface, "target_surface"))
        seen = set()
        for text, mtype in entries:
            norm = _normalize(text)
            if norm and norm not in seen:
                seen.add(norm)
                index.append({
                    "expression_id": e["expression_id"],
                    "matched_text": text,
                    "match_type": mtype,
                    "norm": norm,
                })
    return index


_CONFIDENCE = {
    # (match_type, match_method) -> confidence
    ("exact_expression", "verbatim"): 1.0,
    ("exact_expression", "normalized"): 0.9,
    ("target_surface", "verbatim"): 0.85,
    ("target_surface", "normalized"): 0.75,
    ("related_expression", "verbatim"): 0.6,
    ("related_expression", "normalized"): 0.5,
}


def _find_match(raw_text: str, entry: dict) -> Optional[str]:
    """先尝试原文逐字命中(词边界), 再退到 normalized; 返回 match_method 或 None。"""
    pattern = r"(?<![a-z'])" + re.escape(entry["matched_text"].lower()) + r"(?![a-z'])"
    if re.search(pattern, raw_text.lower()):
        return "verbatim"
    if f" {entry['norm']} " in f" {_normalize(raw_text)} ":
        return "normalized"
    return None


def run_matching(asset_id: str) -> Optional[dict]:
    """规则匹配: 命中只作为 candidate(带 match_type/match_method/confidence), 教师审核后才算正式关联。"""
    asset = student_repo.get_corpus_asset(asset_id)
    if not asset:
        return None
    clips = student_repo.list_corpus_clips(asset_id)
    if not clips:
        return {"error": "请先运行切分"}
    index = _expression_match_index()

    total_hits = 0
    for clip in clips:
        raw = clip["transcript"] or ""
        matches = []
        for entry in index:
            method = _find_match(raw, entry)
            if method:
                matches.append({
                    "expression_id": entry["expression_id"],
                    "matched_text": entry["matched_text"],
                    "match_type": entry["match_type"],
                    "match_method": method,
                    "confidence": _CONFIDENCE[(entry["match_type"], method)],
                    "status": "candidate",
                })
        # 同表达去重, 保留优先级最高的匹配(类型优先, 同级 verbatim 优先)
        best: dict = {}
        priority = {"exact_expression": 0, "target_surface": 1, "related_expression": 2}
        for m in matches:
            cur = best.get(m["expression_id"])
            if cur is None or (priority[m["match_type"]], -m["confidence"]) < \
                    (priority[cur["match_type"]], -cur["confidence"]):
                best[m["expression_id"]] = m
        matches = sorted(best.values(), key=lambda m: (-m["confidence"], m["expression_id"]))
        total_hits += len(matches)
        student_repo.update_corpus_clip(clip["clip_id"], {"expression_matches": matches})

    student_repo.update_corpus_asset(asset_id, {
        "pipeline_status": "matched",
        "pipeline_error": None,
    })
    return {"clips": len(clips), "matches": total_hits}


# ---------- 5. 教师审核 ----------

CLIP_EDITABLE = {"start_ms", "end_ms", "transcript", "scenario_tags",
                 "communicative_function", "difficulty", "speaker_info"}


def update_clip(clip_id: str, fields: dict) -> Optional[dict]:
    """教师编辑 clip。实质修改(transcript/时间区间)→ 新 revision, 回落 pending_teacher。

    原始 ASR 在 asset.raw_asr_text 中保留, 不被覆盖。
    """
    clip = student_repo.get_corpus_clip(clip_id)
    if not clip:
        return None
    updates = {k: v for k, v in fields.items() if k in CLIP_EDITABLE and v is not None}
    if not updates:
        return {"error": "no_fields"}
    if "start_ms" in updates or "end_ms" in updates:
        start = updates.get("start_ms", clip["start_ms"])
        end = updates.get("end_ms", clip["end_ms"])
        if end <= start:
            return {"error": "bad_range", "message": "end_ms 必须大于 start_ms"}

    substantive = {"transcript", "start_ms", "end_ms"} & set(updates)
    new_revision = clip["revision"] + 1
    log = clip.get("revisions_log") or []
    log.append({
        "revision": new_revision,
        "edited_at": _utc_now(),
        "changed_fields": sorted(updates.keys()),
        "substantive": bool(substantive),
    })
    updates["revision"] = new_revision
    updates["revisions_log"] = log
    if substantive:
        # 实质修改后必须重新审核
        updates["review_status"] = "pending_teacher"
    student_repo.update_corpus_clip(clip_id, updates)
    if "transcript" in updates:
        # 教师改过 transcript: asset 状态联动为 teacher_edited,
        # cleaned_text 由全部 clip 按时间序重组; raw_asr_text 永远保留不覆盖。
        clips = student_repo.list_corpus_clips(clip["asset_id"])
        cleaned = " ".join(
            (c["transcript"] or "").strip()
            for c in sorted(clips, key=lambda c: c["start_ms"])
            if (c["transcript"] or "").strip()
        )
        student_repo.update_corpus_asset(clip["asset_id"], {
            "transcript_status": "teacher_edited",
            "cleaned_text": cleaned,
        })
    return student_repo.get_corpus_clip(clip_id)


def review_clip(clip_id: str, action: str) -> Optional[dict]:
    if action not in ("approve", "reject"):
        return {"error": "bad_action"}
    clip = student_repo.get_corpus_clip(clip_id)
    if not clip:
        return None
    asset = student_repo.get_corpus_asset(clip["asset_id"])
    if action == "approve" and asset and asset["permission_status"] not in ALLOWED_PERMISSION:
        return {"error": "permission", "message": "素材许可状态不明确, 不允许批准进入正式语料"}
    student_repo.update_corpus_clip(clip_id, {
        "review_status": "approved" if action == "approve" else "rejected",
        "reviewed_at": _utc_now(),
    })
    return student_repo.get_corpus_clip(clip_id)


def review_asset(asset_id: str, action: str) -> Optional[dict]:
    if action not in ("approve", "reject"):
        return {"error": "bad_action"}
    asset = student_repo.get_corpus_asset(asset_id)
    if not asset:
        return None
    if action == "approve" and asset["permission_status"] not in ALLOWED_PERMISSION:
        return {"error": "permission", "message": "素材许可状态不明确, 不允许批准"}
    student_repo.update_corpus_asset(asset_id, {
        "review_status": "approved" if action == "approve" else "rejected",
        "reviewed_at": _utc_now(),
    })
    return student_repo.get_corpus_asset(asset_id)


def update_asset_metadata(asset_id: str, fields: dict) -> Optional[dict]:
    """教师修改素材元数据(许可/来源等)。许可变更为 unverified 时回落待审核。"""
    allowed = {"title", "source_name", "source_url", "license", "permission_status"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return {"error": "no_fields"}
    asset = student_repo.get_corpus_asset(asset_id)
    if not asset:
        return None
    if updates.get("permission_status") not in ALLOWED_PERMISSION and "permission_status" in updates:
        updates["review_status"] = "pending_teacher"
    updates["revision"] = asset["revision"] + 1
    student_repo.update_corpus_asset(asset_id, updates)
    return student_repo.get_corpus_asset(asset_id)
