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
    consent: Optional[dict] = None,
) -> dict:
    suffix = Path(filename).suffix.lower() or ".bin"
    asset_id = new_id("asset")
    CORPUS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    rel_path = f"corpus/audio/{asset_id}{suffix}"
    abs_path = DATA_DIR / rel_path
    abs_path.write_bytes(file_bytes)

    consent = consent or {}
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
        # 自建录音授权链(Phase 7.7): permission_status=owned 必须配 consent_id
        "consent_id": consent.get("consent_id"),
        "speaker_ids": consent.get("speaker_ids") or [],
        "commercial_permission": bool(consent.get("commercial_permission")),
        "editing_permission": bool(consent.get("editing_permission")),
        "ai_processing_permission": bool(consent.get("ai_processing_permission")),
        "recorded_at": consent.get("recorded_at"),
    }
    return student_repo.create_corpus_asset(asset)


def _consent_complete(asset: dict) -> bool:
    """permission_status=owned 的自建录音必须绑定已签署授权记录。"""
    if asset.get("permission_status") != "owned":
        return True
    return bool(asset.get("consent_id"))


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
            "origin": "auto",
            "created_at": _utc_now(),
        }
        student_repo.create_corpus_clip(clip)
        created.append(clip["clip_id"])

    student_repo.update_corpus_asset(asset_id, {
        "pipeline_status": "segmented",
        "pipeline_error": None,
    })
    return {"clips_created": len(created)}


# ---------- 3b. 教师手工 clip(注释/参考文本辅助定位, 仍走审核) ----------

def create_clip(
    asset_id: str,
    start_ms: int,
    end_ms: int,
    transcript: Optional[str] = None,
    speaker_info: Optional[str] = None,
) -> Optional[dict]:
    """教师按时间区间手工创建 clip(如用 AMI 官方注释定位教学目标交换段)。

    origin='manual', 不受 run_segmentation 重跑清除影响; 仍需审核才能进学生端。
    """
    asset = student_repo.get_corpus_asset(asset_id)
    if not asset:
        return None
    if end_ms <= start_ms:
        return {"error": "bad_range", "message": "end_ms 必须大于 start_ms"}
    if asset.get("duration_ms") and end_ms > asset["duration_ms"] + 500:
        return {"error": "bad_range", "message": "超出音频时长"}
    clip = {
        "clip_id": new_id("clip"),
        "asset_id": asset_id,
        "start_ms": int(start_ms),
        "end_ms": int(end_ms),
        "transcript": transcript,
        "context_before": None,
        "context_after": None,
        "speaker_info": speaker_info,
        "scenario_tags": "[]",
        "communicative_function": None,
        "difficulty": None,
        "expression_matches": "[]",
        "review_status": "pending_teacher",
        "revision": 1,
        "origin": "manual",
        "created_at": _utc_now(),
    }
    student_repo.create_corpus_clip(clip)
    return student_repo.get_corpus_clip(clip["clip_id"])


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
                 "communicative_function", "difficulty", "speaker_info",
                 "accent", "speaker_count", "speech_rate", "listening_features"}

ALLOWED_LISTENING_FEATURES = {
    "weak_form", "linking", "reduction", "hesitation", "self_correction",
    "interruption", "discourse_marker", "implicit_meaning", "paraphrase",
}


def update_clip(clip_id: str, fields: dict) -> Optional[dict]:
    """教师编辑 clip。

    Phase 7.7 起 revision 拆分为两条线:
    - content_revision: 只在实质修改(transcript/start_ms/end_ms, 影响学生实际
      接收内容)时 +1, 同时回落 pending_teacher。学生历史 attempt 绑定此号。
    - metadata_revision: 标签类修改(difficulty/tags/accent/speaker_count 等)
      只 bump 此号, 不影响内容版本, 不打断已批准状态。
    旧 revision 列继续与 content_revision 同步(向后兼容)。
    原始 ASR 在 asset.raw_asr_text 中保留, 不被覆盖。
    """
    clip = student_repo.get_corpus_clip(clip_id)
    if not clip:
        return None
    updates = {k: v for k, v in fields.items() if k in CLIP_EDITABLE and v is not None}
    if not updates:
        return {"error": "no_fields"}
    if "listening_features" in updates:
        bad = set(updates["listening_features"]) - ALLOWED_LISTENING_FEATURES
        if bad:
            return {"error": "bad_listening_features",
                    "message": f"未知 listening_features: {sorted(bad)}"}
    if "start_ms" in updates or "end_ms" in updates:
        start = updates.get("start_ms", clip["start_ms"])
        end = updates.get("end_ms", clip["end_ms"])
        if end <= start:
            return {"error": "bad_range", "message": "end_ms 必须大于 start_ms"}

    substantive = {"transcript", "start_ms", "end_ms"} & set(updates)
    content_rev = (clip.get("content_revision") or clip["revision"] or 1)
    metadata_rev = (clip.get("metadata_revision") or 1)
    log = clip.get("revisions_log") or []
    if substantive:
        content_rev += 1
        bump = "content"
        # 实质修改后必须重新审核
        updates["review_status"] = "pending_teacher"
    else:
        metadata_rev += 1
        bump = "metadata"
    log.append({
        "content_revision": content_rev,
        "metadata_revision": metadata_rev,
        "edited_at": _utc_now(),
        "changed_fields": sorted(updates.keys()),
        "bump": bump,
    })
    updates["content_revision"] = content_rev
    updates["metadata_revision"] = metadata_rev
    updates["revision"] = content_rev  # 旧列保持 = content_revision
    updates["revisions_log"] = log
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
    if action == "approve" and asset and not _consent_complete(asset):
        return {"error": "permission",
                "message": "自建录音缺少已签署授权记录(consent_id), 不允许批准"}
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
    if action == "approve" and not _consent_complete(asset):
        return {"error": "permission",
                "message": "自建录音缺少已签署授权记录(consent_id), 不允许批准"}
    student_repo.update_corpus_asset(asset_id, {
        "review_status": "approved" if action == "approve" else "rejected",
        "reviewed_at": _utc_now(),
    })
    return student_repo.get_corpus_asset(asset_id)


def update_asset_metadata(asset_id: str, fields: dict) -> Optional[dict]:
    """教师修改素材元数据(许可/来源/授权链等)。许可变更为 unverified 时回落待审核。"""
    allowed = {"title", "source_name", "source_url", "license", "permission_status",
               "consent_id", "speaker_ids", "commercial_permission",
               "editing_permission", "ai_processing_permission", "recorded_at"}
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


# ---------- 6. Expression 匹配确认(candidate → 正式关联) ----------

def review_clip_match(clip_id: str, expression_id: str, action: str) -> Optional[dict]:
    """教师确认/否决某条候选匹配。确认后才算正式关联(status=approved)。

    只能处理 run_matching 写入的 candidate; 不允许凭空添加匹配。
    """
    if action not in ("approve", "reject"):
        return {"error": "bad_action"}
    clip = student_repo.get_corpus_clip(clip_id)
    if not clip:
        return None
    matches = clip.get("expression_matches") or []
    target = None
    for m in matches:
        if m.get("expression_id") == expression_id and m.get("status") == "candidate":
            target = m
            break
    if target is None:
        return {"error": "no_candidate", "message": "该表达没有待审核的候选匹配"}
    target["status"] = "approved" if action == "approve" else "rejected"
    target["reviewed_at"] = _utc_now()
    student_repo.update_corpus_clip(clip_id, {"expression_matches": matches})
    return student_repo.get_corpus_clip(clip_id)


# 教师可手动建立的匹配类型(规则匹配器永不自动产生 communicative_equivalent)
TEACHER_MATCH_TYPES = {"exact_expression", "target_surface",
                       "related_expression", "communicative_equivalent"}


def add_clip_match(clip_id: str, expression_id: str, matched_text: str,
                   match_type: str, note: str = "") -> Optional[dict]:
    """教师基于教学判断手动建立 clip ↔ Expression 关联, 直接 approved。

    主要场景: communicative_equivalent —— 真人自然说出的功能等价表达
    (如 "we don't have any rooms available" ≈ fully booked), 规则匹配器
    无法发现, 只能由教师听完后判断建立。match_method 记为 teacher_judgement,
    与规则候选(verbatim/normalized)明确区分, 便于后续审计证据来源。
    """
    if match_type not in TEACHER_MATCH_TYPES:
        return {"error": "bad_match_type",
                "message": f"match_type 必须是 {sorted(TEACHER_MATCH_TYPES)} 之一"}
    clip = student_repo.get_corpus_clip(clip_id)
    if not clip:
        return None
    expr_ids = {e["expression_id"] for e in expression_repo.list_expressions()}
    if expression_id not in expr_ids:
        return {"error": "no_expression", "message": "expression_id 不存在"}
    matches = clip.get("expression_matches") or []
    for m in matches:
        if (m.get("expression_id") == expression_id
                and m.get("status") in ("candidate", "approved")):
            return {"error": "duplicate",
                    "message": "该表达在此 clip 已有候选或正式匹配, 请先审核已有记录"}
    matches.append({
        "expression_id": expression_id,
        "matched_text": matched_text,
        "match_type": match_type,
        "match_method": "teacher_judgement",
        "confidence": 0.5 if match_type == "communicative_equivalent" else 0.8,
        "status": "approved",
        "note": note,
        "reviewed_at": _utc_now(),
    })
    student_repo.update_corpus_clip(clip_id, {"expression_matches": matches})
    return student_repo.get_corpus_clip(clip_id)


# ---------- 7. 学生端(只读 approved, 带 attribution, 服务端切片) ----------

def list_approved_clips() -> list[dict]:
    """学生端语料列表: 只出 approved clip 且所属 asset 也 approved 且有许可。

    自建录音(permission_status=owned)额外要求 consent_id 已绑定 ——
    未完成授权的录音不得进入学生端。
    """
    out = []
    for asset in student_repo.list_corpus_assets():
        if asset["review_status"] != "approved":
            continue
        if asset["permission_status"] not in ALLOWED_PERMISSION:
            continue
        if not _consent_complete(asset):
            continue
        for clip in student_repo.list_corpus_clips(asset["asset_id"]):
            if clip["review_status"] != "approved":
                continue
            out.append({
                "clip_id": clip["clip_id"],
                "start_ms": clip["start_ms"],
                "end_ms": clip["end_ms"],
                "transcript": clip["transcript"],
                "scenario_tags": clip["scenario_tags"],
                "communicative_function": clip["communicative_function"],
                "difficulty": clip["difficulty"],
                "accent": clip.get("accent"),
                "speaker_count": clip.get("speaker_count"),
                "speech_rate": clip.get("speech_rate"),
                "listening_features": clip.get("listening_features") or [],
                "expression_matches": [
                    m for m in (clip["expression_matches"] or [])
                    if m.get("status") == "approved"
                ],
                "attribution": {
                    "asset_id": asset["asset_id"],
                    "title": asset["title"],
                    "source_name": asset["source_name"],
                    "source_url": asset["source_url"],
                    "license": asset["license"],
                    "source_type": asset["source_type"],
                },
            })
    out.sort(key=lambda c: (c["attribution"]["asset_id"], c["start_ms"]))
    return out


def clip_audio_slice(clip_id: str) -> Optional[bytes]:
    """服务端按 clip 的 start/end 精确切出 WAV 字节(学生只能拿到批准区间)。

    WAV 走快路径; 其他格式用 PyAV 解码后按采样点切, 再编码为 16kHz WAV。
    """
    import io

    clip = student_repo.get_corpus_clip(clip_id)
    if not clip or clip["review_status"] != "approved":
        return None
    asset = student_repo.get_corpus_asset(clip["asset_id"])
    if not asset or asset["review_status"] != "approved":
        return None
    if asset["permission_status"] not in ALLOWED_PERMISSION:
        return None
    if not _consent_complete(asset):
        return None
    path = DATA_DIR / asset["file_path"]
    if not path.exists():
        return None
    start_s, end_s = clip["start_ms"] / 1000.0, clip["end_ms"] / 1000.0

    if path.suffix == ".wav":
        with wave.open(str(path), "rb") as w:
            rate, width, ch = w.getframerate(), w.getsampwidth(), w.getnchannels()
            w.setpos(min(int(start_s * rate), w.getnframes()))
            frames = w.readframes(max(0, int((end_s - start_s) * rate)))
        buf = io.BytesIO()
        with wave.open(buf, "wb") as out:
            out.setnchannels(ch)
            out.setsampwidth(width)
            out.setframerate(rate)
            out.writeframes(frames)
        return buf.getvalue()

    import av  # 非 wav: 全量解码后按采样点切(素材量级为分钟, 可接受)
    import numpy as np

    samples = []
    rate = 16000
    with av.open(str(path)) as c:
        stream = c.streams.audio[0]
        for frame in c.decode(stream):
            arr = frame.to_ndarray()
            samples.append(arr.mean(axis=0) if arr.ndim > 1 else arr[0])
            rate = frame.sample_rate
    if not samples:
        return None
    pcm = np.concatenate(samples)
    pcm = pcm[int(start_s * rate):int(end_s * rate)]
    pcm16 = (np.clip(pcm, -1.0, 1.0) * 32767).astype(np.int16) \
        if pcm.dtype != np.int16 else pcm
    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(pcm16.tobytes())
    return buf.getvalue()
