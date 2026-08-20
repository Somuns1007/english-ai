# -*- coding: utf-8 -*-
"""Phase 7.6: 从 AMI 官方人工注释(NXT XML)提取教学目标片段候选。

输入: _extract_raw/ami_annotations/(words|dialogueActs)/ 下某会议的 4 通道 XML
输出: JSON 候选列表 —— 每个候选是一个 12~60s 的"交换窗口",
     含 start/end(秒)、gold transcript、出现的对话行为标签、参与说话人。

用法: python -m tools.ami_candidates ES2008a
注意: 这只是给教师审核用的"候选定位", 最终 clip 仍走 corpus 流水线 + 教师审核。
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "listening" / "data" / "_extract_raw"
ANN = RAW / "ami_annotations"

DA_MAP = {  # ami_da_N -> (label, 目标交际功能 or None)
    "ami_da_1": ("Backchannel", None),
    "ami_da_2": ("Stall", "uncertainty"),
    "ami_da_3": ("Fragment", None),
    "ami_da_4": ("Inform", None),
    "ami_da_5": ("Elicit-Inform", "clarification"),
    "ami_da_6": ("Suggest", "suggestion"),
    "ami_da_7": ("Offer", "suggestion"),
    "ami_da_8": ("Elicit-Offer-Or-Suggestion", "request"),
    "ami_da_9": ("Assess", "evaluation"),
    "ami_da_11": ("Elicit-Assessment", "request"),
    "ami_da_12": ("Comment-About-Understanding", "confirmation"),
    "ami_da_13": ("Elicit-Comment-Understanding", "clarification"),
    "ami_da_14": ("Be-Positive", "agreement"),
    "ami_da_15": ("Be-Negative", "disagreement"),
    "ami_da_16": ("Other", None),
}

NITE = "{http://nite.sourceforge.net/}"
ID_RE = re.compile(r"id\(([^)]+)\)(?:\.\.id\(([^)]+)\))?")


def parse_words(path: Path) -> dict:
    """word_id -> (text, start|None, end|None)。保留所有元素(含标点/无时间标注),
    因为 dialog-act 的范围引用可能落在它们上面; 无时间标注的词只贡献文本。"""
    words = {}
    root = ET.parse(path).getroot()
    for el in root:
        wid = el.get(f"{NITE}id")
        start, end = el.get("starttime"), el.get("endtime")
        text = (el.text or "").strip()
        if el.get("punc") == "true":
            text = ""
        words[wid] = (text, float(start) if start else None,
                      float(end) if end else None)
    return words


def parse_dacts(path: Path) -> list:
    """-> [(word_ids, da_label, comm_function)]"""
    out = []
    root = ET.parse(path).getroot()
    for dact in root:
        da_ref = None
        wid_lo = wid_hi = None
        for child in dact:
            if child.tag == f"{NITE}pointer" and child.get("role") == "da-aspect":
                da_ref = child.get("href", "").split("#id(")[-1].rstrip(")")
            elif child.tag == f"{NITE}child":
                m = ID_RE.search(child.get("href", ""))
                if m:
                    wid_lo, wid_hi = m.group(1), m.group(2) or m.group(1)
        if da_ref and wid_lo:
            label, func = DA_MAP.get(da_ref, ("?", None))
            out.append((wid_lo, wid_hi, label, func))
    return out


def main(meeting: str) -> None:
    dacts = []  # (start, end, speaker, label, func, text)
    for speaker in "ABCD":
        wpath = ANN / "words" / f"{meeting}.{speaker}.words.xml"
        dpath = ANN / "dialogueActs" / f"{meeting}.{speaker}.dialog-act.xml"
        if not wpath.exists() or not dpath.exists():
            continue
        words = parse_words(wpath)
        # words 文件内 id 顺序即时间顺序, 建索引做范围展开
        id_order = list(words.keys())
        id_pos = {wid: i for i, wid in enumerate(id_order)}
        for lo, hi, label, func in parse_dacts(dpath):
            i, j = id_pos.get(lo), id_pos.get(hi)
            if i is None or j is None or j < i:
                continue
            ws = [words[w] for w in id_order[i:j + 1]]
            text = " ".join(t for t, _, _ in ws if t)
            timed = [(s, e) for _, s, e in ws if s is not None and e is not None]
            if not text or not timed:
                continue
            dacts.append({
                "start": timed[0][0], "end": timed[-1][1], "speaker": speaker,
                "label": label, "func": func, "text": text,
            })
    dacts.sort(key=lambda d: d["start"])

    # 以目标 DA 为锚点聚合成交换窗口
    targets = [d for d in dacts if d["func"]]
    windows = []
    used_until = -1.0
    for t in targets:
        if t["start"] < used_until:
            continue
        w_start = max(0.0, t["start"] - 8.0)
        w_end = t["end"] + 8.0
        # 扩展窗口: 纳入时间上重叠/相邻(<=2s 间隙)的后续 DA, 上限 60s
        members = [d for d in dacts
                   if d["end"] >= w_start - 0.5 and d["start"] <= w_end + 2.0]
        while True:
            grown = False
            for d in dacts:
                if d["end"] < w_start - 0.5 or d["start"] > w_end + 2.0:
                    continue
                if d not in members:
                    if d["end"] + 8.0 - w_start <= 60.0:
                        members.append(d)
                        w_end = max(w_end, d["end"] + 8.0)
                        grown = True
            if not grown or w_end - w_start >= 60.0:
                break
        speakers = sorted({m["speaker"] for m in members})
        funcs = sorted({m["func"] for m in members if m["func"]})
        windows.append({
            "start_s": round(w_start, 2),
            "end_s": round(min(w_end, w_start + 60.0), 2),
            "duration_s": round(min(w_end, w_start + 60.0) - w_start, 2),
            "speakers": speakers,
            "comm_functions": funcs,
            "da_counts": {lb: sum(1 for m in members if m["label"] == lb)
                          for lb in sorted({m["label"] for m in members})},
            "transcript": " | ".join(
                f"[{m['speaker']}] {m['text']}" for m in
                sorted(members, key=lambda m: m["start"])
            )[:1200],
        })
        used_until = w_end

    # 优先多人交换窗口
    windows.sort(key=lambda w: (-len(w["speakers"]), -len(w["comm_functions"])))
    out = RAW / f"ami_{meeting.lower()}_candidates.json"
    out.write_text(json.dumps(windows, indent=2, ensure_ascii=False), encoding="utf-8")
    multi = sum(1 for w in windows if len(w["speakers"]) >= 2)
    print(f"{meeting}: {len(dacts)} DAs, {len(targets)} target DAs, "
          f"{len(windows)} candidate windows ({multi} multi-speaker)")
    print(f"-> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ES2008a")
