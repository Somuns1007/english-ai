# -*- coding: utf-8 -*-
"""Phase 6: 用 edge-tts 为 AI 场景批量生成训练音频。

设计约束(按 Phase 6 硬性要求第 6 条):
- TTS 仅作为 AI 场景训练音频, 不冒充真实人类语料。
- 每条音频记录 voice_id / provider / speed / generated_at / source_type=ai_generated_tts。
- V1 为单嗓音朗读整段对话(A:/B: 前缀在朗读前去除), 非双人分角色合成。

用法:
  python -m listening.tools.generate_scenario_audio            # 全部生成
  python -m listening.tools.generate_scenario_audio --only scn_xxx scn_yyy
  python -m listening.tools.generate_scenario_audio --force    # 已存在也重新生成
"""
import argparse
import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import edge_tts

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCENARIOS_PATH = DATA_DIR / "expressions" / "scenarios.json"
AUDIO_DIR = DATA_DIR / "expressions" / "audio"
AUDIO_INDEX_PATH = DATA_DIR / "expressions" / "audio_index.json"

PROVIDER = "edge_tts"
SOURCE_TYPE = "ai_generated_tts"
SPEED = "+0%"
# 英语母语嗓音轮换, 避免全部场景同一个声音
VOICES = [
    "en-US-JennyNeural",
    "en-US-GuyNeural",
    "en-GB-SoniaNeural",
    "en-US-AriaNeural",
]


def text_to_speech_text(text: str) -> str:
    """去掉 A:/B: 角色前缀, 保留句子本身。"""
    lines = [re.sub(r"^[AB]:\s*", "", ln).strip() for ln in text.split("\n")]
    return " ".join(ln for ln in lines if ln)


async def generate_one(scenario_id: str, text: str, voice: str, out_path: Path) -> None:
    communicate = edge_tts.Communicate(text, voice, rate=SPEED)
    await communicate.save(str(out_path))


async def run(only: list, force: bool) -> None:
    doc = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    scenarios = doc["scenarios"]
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    if AUDIO_INDEX_PATH.exists():
        index = json.loads(AUDIO_INDEX_PATH.read_text(encoding="utf-8"))
    else:
        index = {}

    todo = []
    for i, s in enumerate(scenarios):
        sid = s["scenario_id"]
        if only and sid not in only:
            continue
        out = AUDIO_DIR / f"{sid}.mp3"
        if out.exists() and not force:
            continue
        todo.append((i, s, out))

    print(f"待生成 {len(todo)} 条音频(总场景 {len(scenarios)})")
    failed = []
    for n, (i, s, out) in enumerate(todo, 1):
        sid = s["scenario_id"]
        voice = VOICES[i % len(VOICES)]
        tts_text = text_to_speech_text(s["text"])
        try:
            await generate_one(sid, tts_text, voice, out)
            index[sid] = {
                "scenario_id": sid,
                "file": f"audio/{sid}.mp3",
                "voice_id": voice,
                "provider": PROVIDER,
                "speed": SPEED,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_type": SOURCE_TYPE,
            }
            # 每条成功后立即落盘, 防止批量任务中断导致索引丢失
            AUDIO_INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"[{n}/{len(todo)}] OK {sid} voice={voice} bytes={out.stat().st_size}")
        except Exception as exc:  # noqa: BLE001 - 批量任务记录失败并继续
            failed.append(sid)
            print(f"[{n}/{len(todo)}] FAIL {sid}: {exc}")

    AUDIO_INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"audio_index.json 共 {len(index)} 条; 本次失败 {len(failed)} 条")
    if failed:
        print("失败列表:", failed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=[])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.only, args.force))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
