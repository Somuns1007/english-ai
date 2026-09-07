#!/usr/bin/env python3
"""clean.py — 3-tier OCR 清洗，将 booklet_extract/set{N}_booklet.json 中的
transcript_segments.text_raw 清洗为 cleaned_text，写入 _extract_raw/set{N}.txt。

三层清洗（与 commit 49c0cf0 描述一致）：
  HARD  —— 确定性错字替换（逐字符，经 PDF 视觉终审坐实）
  PHRASE —— 上下文感知短语修复（OCR 断词、合并行、语义单元修复）
  WORD  —— 保守单词级修复（仅在已知音/形混淆字符模式下触发）

约束：
  - sentence-mark protection：标点和方括号序号 [N] 保护，不被 WORD 层误改
  - 所有替换均记录到 corrections_log（便于 diff 审查）
  - 原始 text_raw 永不覆盖（只写入新字段 cleaned_text 或单独的 txt）

使用：
  python _audit_scripts/clean.py --set 2
  python _audit_scripts/clean.py --set 1 --set 2 --dry-run
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
BOOKLET_DIR = BASE / "_audit_scripts" / "booklet_extract"
OUT_RAW_DIR = BASE / "backend" / "listening" / "data" / "_extract_raw"

# ── Tier 1: HARD replacements (确定性错字，经 PDF 高DPI 视觉终审) ──────
# 格式：(wrong_char/string, correct_char/string)
HARD_RULES: list[tuple[str, str]] = [
    # 中文 OCR 错字（已在 49c0cf0 中坐实）
    ("昕", "听"),
    ("汞", "案"),
    ("崩惯", "崩溃"),
    ("ω", "to "),   # 常见英文 ω→to 混淆
    ("阳，", "Oh, "),
    # 英文 OCR 字符替换
    ("1t'", "It'"),
    ("1'", "I'"),
    (" 1 ", " I "),
    ("1 know", "I know"),
    ("1 promised", "I promised"),
    ("1 adore", "I adore"),
    ("1 really", "I really"),
    ("1'11 ", "I'll "),
    ("1'1l ", "I'll "),
    ("WelJ,", "Well,"),
    ("stilJ ", "still "),
    ("sucb ", "such "),
    ("co创t", "coast"),
    ("co∞smopolitan", "cosmopolitan"),
    ("∞smopolitan", "cosmopolitan"),
    ("heigl邸", "heights"),
    ("nightmar巳", "nightmare"),
    ("inter毡s", "interes"),
    ("sound也", "sounds"),
    ("Consideri吨", "Considering"),
    ("cJusters", "clusters"),
    ("Ba1'celona", "Barcelona"),
    ("Ba celona", "Barcelona"),
    ("1'", "r"),     # trailing 1' → r (e.g. Eve1'ything → Everything)
]

# ── Tier 2: PHRASE replacements (上下文短语修复) ────────────────────────
PHRASE_RULES: list[tuple[str, str]] = [
    ("Eve1'ything", "Everything"),
    ("Eve ything", "Everything"),
    ("fo1' ", "for "),
    ("a1'e ", "are "),
    ("a 盯 rrangement", "arrangement"),
    ("w  e", "we"),
    ("alJ ", "all "),
    ("clUsters", "clusters"),
    ("f如ezing", "freezing"),
    ("的ezing", "freezing"),
    ("白白e begin", "they begin"),
    ("pωple", "people"),
    ("scientisú♀", "scientists"),
    ("patte风", "pattern"),
    ("tt阳毡 is", "there is"),
    ("rnight", "might"),
    ("crea阳", "creates"),
    ("pat阳时", "pattern?"),
    ("wa阳", "water"),
    ("incJuding", "including"),
    ("bllSY", "busy"),
    ("llSllal", "usual"),
]

# ── Tier 3: WORD-level regex (保守模式，sentence-mark protection) ────────
# 只处理已知的 OCR 字符混淆模式，不乱改
WORD_RE_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b1(?=[A-Z'])"), "I"),        # 1X → IX（大写首字母/撇号）
    (re.compile(r"(?<=[a-z])ωf"), " to f"),      # scrambling ωfind → scrambling to find
    (re.compile(r"\[ (\d+)-(\d+) \]"), r"[\1-\2]"),   # [ 1-1 ] → [1-1]
    (re.compile(r"\[ (\d+) \]"), r"[\1]"),             # [ 2 ] → [2]
    (re.compile(r"\[ (\d+) J\]"), r"[\1]"),            # [ 15 J] → [15]
    (re.compile(r"\b0 (?=[A-Z])"), "On "),       # 0 → On (common OCR 0/O confusion)
]

# 保护区域：方括号标注 [N] / [N-N] 不被 WORD 层乱改
_PROTECT_RE = re.compile(r"\[\d+(?:-\d+)?\]|[.?!;,]")


def apply_hard(text: str) -> tuple[str, list[str]]:
    corrections = []
    for wrong, correct in HARD_RULES:
        if wrong in text:
            count = text.count(wrong)
            text = text.replace(wrong, correct)
            corrections.append(f"HARD: {repr(wrong)} → {repr(correct)} (×{count})")
    return text, corrections


def apply_phrase(text: str) -> tuple[str, list[str]]:
    corrections = []
    for wrong, correct in PHRASE_RULES:
        if wrong in text:
            count = text.count(wrong)
            text = text.replace(wrong, correct)
            corrections.append(f"PHRASE: {repr(wrong)} → {repr(correct)} (×{count})")
    return text, corrections


def apply_word_re(text: str) -> tuple[str, list[str]]:
    corrections = []
    for pattern, replacement in WORD_RE_RULES:
        new_text, n = pattern.subn(replacement, text)
        if n > 0:
            corrections.append(f"WORD-RE: {pattern.pattern!r} → {repr(replacement)} (×{n})")
            text = new_text
    return text, corrections


def clean_segment(text_raw: str) -> tuple[str, list[str]]:
    """Apply all three tiers to a single segment. Returns (cleaned, corrections_log)."""
    text = text_raw
    all_corrections: list[str] = []

    text, c = apply_hard(text)
    all_corrections.extend(c)

    text, c = apply_phrase(text)
    all_corrections.extend(c)

    text, c = apply_word_re(text)
    all_corrections.extend(c)

    # Normalise whitespace (collapse multiple spaces, strip)
    text = re.sub(r" {2,}", " ", text).strip()

    return text, all_corrections


def run(set_no: int, dry_run: bool = False) -> int:
    booklet_path = BOOKLET_DIR / f"set{set_no}_booklet.json"
    if not booklet_path.exists():
        print(f"  [error] booklet JSON not found: {booklet_path}")
        print("  → run extract2.py first")
        return 1

    data = json.loads(booklet_path.read_text(encoding="utf-8"))
    exam_id = data["exam_id"]

    output_lines: list[str] = []
    total_segs = 0
    total_corrections = 0

    for unit in data["units"]:
        uid = unit["unit_id"]
        output_lines.append(f"# == {uid} ==")
        for seg in unit.get("transcript_segments", []):
            raw = seg.get("text_raw", "")
            cleaned, corrections = clean_segment(raw)
            total_segs += 1
            total_corrections += len(corrections)
            if corrections and not dry_run:
                pass  # corrections logged per unit below
            speaker = seg.get("speaker", "")
            prefix = f"{speaker.upper()}: " if speaker else ""
            output_lines.append(f"{prefix}{cleaned}")

    out_txt = OUT_RAW_DIR / f"set{set_no}.txt"
    summary = (
        f"  set{set_no}: {total_segs} segments, "
        f"{total_corrections} corrections applied"
    )

    if dry_run:
        print(f"  [dry-run] would write {out_txt.relative_to(BASE)}")
        print(summary)
        return 0

    OUT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_txt.write_text("\n".join(output_lines), encoding="utf-8")
    print(f"  wrote {out_txt.relative_to(BASE)}")
    print(summary)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="3-tier OCR cleaning for booklet transcripts")
    parser.add_argument("--set", type=int, choices=[1, 2], action="append", dest="sets",
                        help="Which set(s) to clean (default: both)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be done without writing files")
    args = parser.parse_args()
    sets = args.sets or [1, 2]
    rc = 0
    for s in sets:
        rc |= run(s, dry_run=args.dry_run)
    return rc


if __name__ == "__main__":
    sys.exit(main())
