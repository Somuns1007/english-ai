# -*- coding: utf-8 -*-
"""
从解析 PDF 导出的纯文本构建结构化题库 JSON。

原则:
- 只提取,不编造。无法可靠提取的字段填 null 并标 needs_review。
- source 层内容(题干/选项/答案/原文/解析)按 PDF 原文保存。
- 英文选项在解析 PDF 中不存在(只有中文译项), text_en 一律 null。
"""
import json
import re
import sys
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "_extract_raw"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "exams"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CJK = re.compile(r"[一-鿿]")

SECTION_UNITS = {
    "A": [("conversation", "Conversation One"), ("conversation", "Conversation Two")],
    "B": [("passage", "Passage One"), ("passage", "Passage Two")],
    "C": [("recording", "Recording One"), ("recording", "Recording Two"), ("recording", "Recording Three")],
}

QUESTION_RANGES = {"A": (1, 8), "B": (9, 15), "C": (16, 25)}


def load_text(name: str) -> str:
    text = (RAW_DIR / f"{name}.txt").read_text(encoding="utf-8")
    # 去掉分页标记和页脚行
    text = re.sub(r"@@PAGE \d+@@", "\n", text)
    text = re.sub(r"2026 年 6 月大学英语六级考试真题答案详解[^\n]*", "", text)
    return text


def isolate_listening(text: str) -> str:
    # 容忍 OCR: "Part II" / "Part 11"
    m_start = re.search(r"Part\s*[I1l]{2}\s*Listening Comprehension", text)
    m_end = re.search(r"Part\s*(?:m|III|1II|111)\s*Reading Comprehension", text)
    if not m_start or not m_end:
        raise RuntimeError("无法定位听力部分边界")
    return text[m_start.end():m_end.start()]


def split_sections(body: str) -> dict:
    """按 Section A/B/C 切分(取听力部分内的前三个 Section 标记)。"""
    marks = list(re.finditer(r"^\s*Section\s+([ABC])\s*$", body, re.M))
    result = {}
    for i, m in enumerate(marks[:3]):
        end = marks[i + 1].start() if i + 1 < len(marks[:3]) else len(body)
        result[m.group(1)] = body[m.end():end]
    return result


def split_units(section_text: str, section: str) -> list:
    units = SECTION_UNITS[section]
    # 标题可能有 kern 噪声,如 "Recordin g One"
    patterns = []
    for _, title in units:
        words = title.split()
        pat = r"^\s*" + r"\s*".join(re.escape(w) + r"?" for w in words)
        # 允许单词内部被空格切开: Recordin g -> Recordin\s+g
        pat = r"^\s*" + r"\s*".join(
            re.escape(w).replace(r"\ ", r"\s*") for w in words
        )
        # 更宽松: 每个字母间允许可选空格
        letters = r"\s*".join(re.escape(c) for c in title.replace(" ", ""))
        patterns.append((title, re.compile(r"^\s*" + letters + r"\s*$", re.M | re.I)))
    found = []
    for title, rx in patterns:
        m = rx.search(section_text)
        if m:
            found.append((m.start(), m.end(), title))
    found.sort()
    result = []
    for i, (start, end, title) in enumerate(found):
        stop = found[i + 1][0] if i + 1 < len(found) else len(section_text)
        result.append((title, section_text[end:stop]))
    return result


def clean_stem(en: str) -> str:
    """最小机械清理: 合并多余空白; 合并被拆开的单字母(如 'i s' -> 'is')。"""
    en = re.sub(r"\s+", " ", en).strip()
    # 反复合并相邻单字母 token
    prev = None
    while prev != en:
        prev = en
        en = re.sub(r"\b([A-Za-z]) (?=[A-Za-z]\b)", r"\1", en)
    return en


def parse_questions(unit_text: str, lo: int, hi: int):
    """返回 (transcript, [question blocks])。"""
    q_marks = []
    for n in range(lo, hi + 1):
        # 容忍题号被空格拆开, 如 "1 7 . What..."
        if n < 10:
            pat = rf"^\s*{n}\.\s+"
        else:
            pat = rf"^\s*{n // 10}\s*{n % 10}\s*\.\s+"
        m = re.search(pat, unit_text, re.M)
        if m:
            q_marks.append((n, m.start(), m.end()))
    if not q_marks:
        return unit_text.strip(), []
    transcript = unit_text[: q_marks[0][1]].strip()
    blocks = []
    for i, (n, start, content_start) in enumerate(q_marks):
        stop = q_marks[i + 1][1] if i + 1 < len(q_marks) else len(unit_text)
        blocks.append((n, unit_text[content_start:stop].strip()))
    return transcript, blocks


OPTION_SPLIT = re.compile(r"([A-DO0])\s*\)\s*")


def parse_question_block(block: str):
    """解析单题块: 题干EN/中文译题/选项/答案/解析。"""
    # 容忍 "答 案 为" 带空格
    m_ans = re.search(r"答\s*案\s*为\s*[^A-D]{0,8}([A-D])", block)
    answer = m_ans.group(1) if m_ans else None

    pre = block[: m_ans.start()] if m_ans else block
    post = block[m_ans.start():] if m_ans else ""

    # 选项区域: pre 中从第一个 "X)" 开始
    m_opt = OPTION_SPLIT.search(pre)
    stem_part = pre[: m_opt.start()] if m_opt else pre
    opt_part = pre[m_opt.start():] if m_opt else ""

    # 题干: 以"连续4个及以上中文字符"的起点作为中英文分界
    # (英文题干可能混入零星 OCR 噪声汉字, 如 "明'hat"/"do 由i s")
    stem_lines = stem_part.splitlines()
    en_parts, zh_parts = [], []
    zh_started = False
    cjk_run = re.compile(r"[一-鿿]{4,}")
    for line in stem_lines:
        line = line.strip()
        if not line:
            continue
        m_cjk = cjk_run.search(line)
        if not zh_started and m_cjk:
            en_seg = line[: m_cjk.start()].strip()
            zh_seg = line[m_cjk.start():].strip()
            if en_seg:
                en_parts.append(en_seg)
            if zh_seg:
                zh_parts.append(zh_seg)
            zh_started = True
        elif not zh_started:
            en_parts.append(line)
        else:
            zh_parts.append(line)
    question_text = clean_stem(" ".join(p for p in en_parts if p))
    question_text_zh = re.sub(r"\s+", "", "".join(zh_parts)).strip("。 ") or None

    # 选项: 按标签切分(容忍 OCR 把 D 识别成 0/O)
    label_map = {"O": "D", "0": "D"}
    labels_found = {label_map.get(m.group(1), m.group(1)) for m in OPTION_SPLIT.finditer(opt_part)}
    if opt_part and "C" not in labels_found:
        # OCR 常把 "C)" 识别成 "。", 尝试修复后再切分
        fixed = re.sub(r"。\s*。(?=\s*[一-鿿])", "。 C) ", opt_part, count=1)
        if fixed == opt_part:
            fixed = re.sub(r"(^|\n)\s*。(?=\s*[一-鿿])", r"\1C) ", opt_part, count=1)
        opt_part = fixed
    options = []
    matches = list(OPTION_SPLIT.finditer(opt_part))
    seen = set()
    for i, m in enumerate(matches):
        label = label_map.get(m.group(1), m.group(1))
        if label in seen:
            continue
        seen.add(label)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(opt_part)
        text = opt_part[m.end():end]
        text = re.sub(r"\s+", "", text).strip("。 ;")
        options.append({"label": label, "text": text, "text_en": None})
    options = [o for o in options if o["text"]]
    options.sort(key=lambda o: o["label"])
    if options:
        # 最后一项常混入答案框的 OCR 噪声(如 "。匮E" "。匾蜀" "。匮丑")
        t = options[-1]["text"]
        m_noise = re.search(r"[匮匾匣堕囧]", t)
        if m_noise and m_noise.start() >= len(t) - 8:
            options[-1]["text"] = t[: m_noise.start()].rstrip("。 ")

    # 解析正文: 答案依据 + 干扰项排除
    explanation, distractor_analysis = None, None
    m_dis = re.search(r"干扰项排除", post)
    ans_body = post
    if m_dis:
        ans_body = post[: m_dis.start()]
        distractor_analysis = re.sub(r"\s+", " ", post[m_dis.start():]).strip()
    explanation = re.sub(r"\s+", " ", ans_body).strip() or None

    return {
        "question_text": question_text or None,
        "question_text_zh": question_text_zh,
        "options": options,
        "correct_answer": answer,
        "source_explanation": explanation,
        "distractor_analysis": distractor_analysis,
    }


EV_MARK = re.compile(r"\[\s*(\d{1,2})\s*(?:[-–~]\s*(\d{1,2}))?\s*\]")


def find_evidence(transcript: str, q_number: int):
    """在原文中定位 [n] 标记所在句子, 作为 evidence_text(原文原样)。"""
    for m in EV_MARK.finditer(transcript):
        if int(m.group(1)) == q_number:
            start = transcript.rfind(".", 0, m.start()) + 1
            nxt = transcript.find(".", m.end())
            end = nxt + 1 if nxt != -1 else len(transcript)
            return re.sub(r"\s+", " ", transcript[start:end]).strip()
    return None


def build(name: str, set_no: int, audio_file: str, duration_ms):
    text = isolate_listening(load_text(name))
    sections = split_sections(text)
    exam_id = f"cet6_202606_set{set_no}"
    exam = {
        "id": exam_id,
        "exam_type": "cet6",
        "title": f"2026年6月英语六级听力 第{set_no}套",
        "year": 2026,
        "month": 6,
        "set_no": set_no,
        "audio_path": f"audio/{audio_file}",
        "duration_ms": duration_ms,
        "status": "published",
        "units": [],
    }
    order = 0
    for section in ["A", "B", "C"]:
        if section not in sections:
            print(f"[warn] {name} 缺少 Section {section}")
            continue
        lo, hi = QUESTION_RANGES[section]
        for utype, utitle, unit_text in [
            (t, ti, tx) for (t, ti), (_, tx) in zip(
                SECTION_UNITS[section],
                split_units(sections[section], section),
            )
        ]:
            order += 1
            transcript, qblocks = parse_questions(unit_text, lo, hi)
            unit = {
                "id": f"{exam_id}_u{order}",
                "exam_id": exam_id,
                "section": section,
                "type": utype,
                "order": order,
                "title": utitle,
                "audio_start_ms": None,
                "audio_end_ms": None,
                "timing_status": "needs_review",
                "transcript": transcript or None,
                "transcript_status": "needs_review",
                "questions": [],
            }
            for n, block in qblocks:
                q = parse_question_block(block)
                qid = f"{exam_id}_q{n}"
                q.update({
                    "id": qid,
                    "unit_id": unit["id"],
                    "exam_id": exam_id,
                    "section": section,
                    "number": n,
                    "evidence_text": find_evidence(transcript, n) if transcript else None,
                    "evidence_start_ms": None,
                    "evidence_end_ms": None,
                    "timing_status": "needs_review",
                    "review_status": "needs_review",
                    "teacher_annotation": {
                        "evidence_text": None,
                        "key_locators": [],
                        "paraphrase": [],
                        "distractors": [],
                    },
                    "ai_annotation": {
                        "review_status": "pending_review",
                        "generated_by": None,
                        "generated_at": None,
                        "diagnosis_candidates": [],
                        "dictation_template": None,
                        "chunking": [],
                    },
                })
                unit["questions"].append(q)
            exam["units"].append(unit)
    exam["question_count"] = sum(len(u["questions"]) for u in exam["units"])
    out = OUT_DIR / f"{exam_id}.json"
    out.write_text(json.dumps(exam, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] {out.name}: units={len(exam['units'])} questions={exam['question_count']}")
    for u in exam["units"]:
        qs = [q["number"] for q in u["questions"]]
        missing_ans = [q["number"] for q in u["questions"] if not q["correct_answer"]]
        bad_opt = [q["number"] for q in u["questions"] if len(q["options"]) != 4]
        print(f"  {u['title']}: Q{qs[0] if qs else '?'}-Q{qs[-1] if qs else '?'} "
              f"({len(qs)}题) 缺答案:{missing_ans or '无'} 选项异常:{bad_opt or '无'}")


if __name__ == "__main__":
    durations = {}
    try:
        from mutagen import File as MutagenFile
        for set_no, f in [(1, r"D:\kimi-workspace\english-ai\backend\listening\data\audio\cet6_202606_set1.mp3"),
                          (2, r"D:\kimi-workspace\english-ai\backend\listening\data\audio\cet6_202606_set2.m4a")]:
            audio = MutagenFile(f)
            if audio and audio.info:
                durations[set_no] = int(audio.info.length * 1000)
                print(f"[audio] set{set_no}: {durations[set_no]} ms")
    except ImportError:
        print("[warn] mutagen 不可用, duration_ms 置 null")

    build("set1", 1, "cet6_202606_set1.mp3", durations.get(1))
    build("set2", 2, "cet6_202606_set2.m4a", durations.get(2))
