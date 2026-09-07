#!/usr/bin/env python3
"""G5: sync_derived_v2.py — 同步 V2.1 派生工件，使其与 candidate.json 保持一致。

背景（GPT-6 审核坐实）：
  commit 49c0cf0 修正了 candidate.json 中 Set2 Q2 opt B 的 text_en
  （"go to at" → "go at"），但 payload_preview 未同步 → 派生层漂移。
  本脚本从 candidate 读取 text_en，同步写入 payload_preview，并重算
  V2_0B_BASELINE 中受影响文件的 sha256。

修复内容：
  1. payload_preview/cet6_202606_set2.exam_payload.json  — Q2 opt B text_en
  2. V2_0B_BASELINE.json — 重算上述文件的 sha256

幂等性：二次运行若内容已一致则跳过写文件（仍重算 hash 以验证）。

使用：
  cd backend && python _audit_scripts/sync_derived_v2.py
"""

import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
V2_DIR = BASE / "listening" / "data" / "v2_full"
CAND_SET2 = V2_DIR / "cet6_202606_set2.candidate.json"
PAYLOAD_SET2 = V2_DIR / "payload_preview" / "cet6_202606_set2.exam_payload.json"
BASELINE = V2_DIR / "V2_0B_BASELINE.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []

    # ── 1. Load candidate (source of truth) ──────────────────────────
    cand = json.loads(CAND_SET2.read_text(encoding="utf-8"))
    # Build (qno, label) → text_en from candidate
    cand_opts: dict[tuple[int, str], str] = {}
    for q in cand.get("questions", []):
        for opt in q.get("options", []):
            te = opt.get("text_en")
            if te:
                cand_opts[(q["number"], opt["label"])] = te

    # ── 2. Sync payload_preview ────────────────────────────────────────
    payload = json.loads(PAYLOAD_SET2.read_text(encoding="utf-8"))
    changed = []
    for q in payload.get("questions", []):
        for opt in q.get("options", []):
            key = (q["number"], opt["label"])
            cand_te = cand_opts.get(key)
            if cand_te is None:
                continue
            cur = opt.get("text_en")
            if cur != cand_te:
                changed.append((key, cur, cand_te))
                opt["text_en"] = cand_te

    if changed:
        for key, old, new in changed:
            print(f"  [fix] payload_preview Q{key[0]} opt {key[1]}: {repr(old)} → {repr(new)}")
        PAYLOAD_SET2.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  wrote {PAYLOAD_SET2.relative_to(BASE)}")
    else:
        print(f"  payload_preview already in sync (no changes needed)")

    # ── 3. Re-verify: full diff candidate vs payload_preview ──────────
    payload_reload = json.loads(PAYLOAD_SET2.read_text(encoding="utf-8"))
    pay_opts: dict[tuple[int, str], str] = {}
    for q in payload_reload.get("questions", []):
        for opt in q.get("options", []):
            te = opt.get("text_en")
            if te:
                pay_opts[(q["number"], opt["label"])] = te

    remaining = {k: (cand_opts[k], pay_opts.get(k)) for k in cand_opts
                 if cand_opts[k] != pay_opts.get(k)}
    if remaining:
        for k, (c, p) in remaining.items():
            errors.append(f"Q{k[0]} opt {k[1]}: candidate={repr(c)} != payload={repr(p)}")
    else:
        print(f"  post-fix diff: 0 mismatches ✓")

    # ── 4. Recompute sha256 in V2_0B_BASELINE ─────────────────────────
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    artifacts = baseline["artifacts"]

    # Map artifact keys (Windows backslash paths) → actual Path
    rel_to_file = {
        "backend\\listening\\data\\v2_full\\payload_preview\\cet6_202606_set2.exam_payload.json":
            PAYLOAD_SET2,
        "backend\\listening\\data\\v2_full\\cet6_202606_set2.candidate.json":
            CAND_SET2,
    }

    baseline_changed = False
    for art_key, fpath in rel_to_file.items():
        if art_key not in artifacts:
            print(f"  [warn] artifact key not found in baseline: {art_key}")
            continue
        old_hash = artifacts[art_key]
        new_hash = sha256_file(fpath)
        if old_hash != new_hash:
            print(f"  [hash] {art_key.split(chr(92))[-1]}: {old_hash[:16]}… → {new_hash[:16]}…")
            artifacts[art_key] = new_hash
            baseline_changed = True
        else:
            print(f"  [hash] {art_key.split(chr(92))[-1]}: unchanged {old_hash[:16]}…")

    if baseline_changed:
        BASELINE.write_text(
            json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  wrote {BASELINE.relative_to(BASE)}")
    else:
        print(f"  V2_0B_BASELINE: no hash changes needed")

    # ── 5. Report ──────────────────────────────────────────────────────
    if errors:
        print("\nERRORS:")
        for e in errors:
            print(" ", e)
        return 1
    print("\nG5 sync complete — all derived artifacts in sync with candidate ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
