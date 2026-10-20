"""Objective checks for post-listening learning notes (CET-4 sets 1/2, CET-6 set 2).

Written independently of the content author. Run from backend/:
    python -m listening.tools.check_learning_notes            # full report
    python -m listening.tools.check_learning_notes --strict   # exit 1 on any error

Checks:
  * vocabulary / guidance counts and anchors (anchor must sit inside one segment)
  * extension fields: collocations / more_examples / pitfalls (vocab),
    pattern / examples / pitfalls (guidance)
  * SOUND_NOTES: allowed types only, anchors inside the named segment, and
    phonetic preconditions verified with CMUdict (pip install cmudict):
      连读   word1 ends in consonant + word2 starts with vowel, or vowel + vowel
      失爆   word1 ends in a plosive (p b t d k g) + word2 starts with a consonant
      同化   word1 ends in t/d/s/z + word2 starts with /j/ (you, your, year ...)
      喉塞化 word1 ends in /t/ + word2 starts with a vowel
      闪音   /t/ or /d/ after a vowel (or r) and before an UNSTRESSED vowel
      弱读   function word from WEAK_FORMS, weak form must match the table
    Notes must not contain long phonetic strings (only short symbols like /t/).
"""
import json
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from listening import learning_content as lc  # noqa: E402

CANDIDATES = {
    "cet4_202606_set1": BACKEND / "listening/data/v2_full/cet4_202606_set1.candidate.json",
    "cet6_202606_set2": BACKEND / "listening/data/v2_full/cet6_202606_set2.candidate.json",
    "cet4_202606_set2": BACKEND / "listening/data/v2_full/cet4_202606_set2.candidate.json",
}
ALLOWED_TYPES = {"连读", "失爆", "同化", "喉塞化", "闪音", "弱读"}
WEAK_FORMS = {
    "to": "/tə/", "of": "/əv/", "than": "/ðən/", "and": "/ən/", "for": "/fə/",
    "have": "/əv/", "has": "/əz/", "had": "/əd/", "a": "/ə/", "the": "/ðə/",
    "can": "/kən/", "at": "/ət/", "from": "/frəm/", "was": "/wəz/", "were": "/wə/",
    "them": "/ðəm/", "her": "/ə/", "him": "/ɪm/", "some": "/səm/", "but": "/bət/",
    "as": "/əz/", "are": "/ə/", "do": "/də/", "does": "/dəz/", "you": "/jə/",
    "your": "/jə/", "that": "/ðət/", "there": "/ðə/", "could": "/kəd/",
    "would": "/wəd/", "should": "/ʃəd/", "will": "/əl/", "must": "/məst/",
}
PLOSIVES = {"P", "B", "T", "D", "K", "G"}
CJK = re.compile(r"[一-鿿]")
LATIN = re.compile(r"[A-Za-z]{2,}")
LONG_IPA = re.compile(r"/[^/\s]{5,}[^/]*/")

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def load_cmu():
    try:
        import cmudict
    except ImportError:
        warn("cmudict 未安装，跳过音系检查（pip install cmudict）")
        return None
    return cmudict.dict()


def is_vowel(ph):
    return ph[-1].isdigit()


def phones(cmu, word):
    w = word.lower().replace("’", "'").strip(".,!?;:\"“”")
    return cmu.get(w, [None])[0]


def segments_by_unit():
    out = {}
    for key, path in CANDIDATES.items():
        data = json.loads(path.read_text(encoding="utf-8"))
        for unit in data["units"]:
            out[unit["unit_id"]] = {s["segment_id"]: s["text"] for s in unit["transcript"]["segments"]}
    return out


def bilingual(text):
    return bool(CJK.search(text or "")) and bool(LATIN.search(text or ""))


def check_vocab_and_guidance(segs):
    for uid, seg_texts in segs.items():
        texts = list(seg_texts.values())
        vocab = lc.CONTENT.get(uid, {}).get("vocabulary", [])
        guide = lc.GUIDANCE.get(uid, [])
        if len(vocab) != 6:
            err(f"{uid}: 生词应为 6 个，实际 {len(vocab)}")
        if len(guide) != 2:
            err(f"{uid}: 难句应为 2 条，实际 {len(guide)}")
        for v in vocab:
            if not any(v["anchor"].lower() in t.lower() for t in texts):
                err(f"{v['id']}: 生词锚点不在任何句段内: {v['anchor']}")
            cols = v.get("collocations")
            if not isinstance(cols, list) or not 2 <= len(cols) <= 4:
                err(f"{v['id']}: collocations 应为 2–4 条")
            exs = v.get("more_examples")
            if not isinstance(exs, list) or len(exs) != 2 or not all(bilingual(e) for e in exs):
                err(f"{v['id']}: more_examples 应为 2 条英中对照例句")
            pits = v.get("pitfalls")
            if not isinstance(pits, list) or not 1 <= len(pits) <= 2:
                err(f"{v['id']}: pitfalls 应为 1–2 条")
        for g in guide:
            if not any(g["anchor"] in t for t in texts):
                err(f"{g['id']}: 难句锚点不在任何句段内（区分大小写）: {g['anchor'][:60]}")
            pattern = g.get("pattern", "")
            blanks = pattern.count("___")
            if not 1 <= blanks <= 2:
                err(f"{g['id']}: pattern 应为整句模板且只留 1–2 个 ___ 空位")
            exs = g.get("examples")
            if not isinstance(exs, list) or len(exs) != 2 or not all(bilingual(e) for e in exs):
                err(f"{g['id']}: examples 应为 2 条英中对照例句")
            if not g.get("pitfalls"):
                err(f"{g['id']}: 缺 pitfalls")


def pair_in_anchor(pair, anchor):
    def norm(s):
        s = re.sub(r"\[\d+(?:-\d+)?\]", " ", s.lower().replace("’", "'"))
        return re.sub(r"[^a-z0-9' ]", " ", s)
    return f" {' '.join(norm(pair[0]).split())} {' '.join(norm(pair[1]).split())} " in f" {' '.join(norm(anchor).split())} "


def check_sound_notes(segs, cmu):
    notes = getattr(lc, "SOUND_NOTES", None)
    if notes is None:
        err("learning_content 里还没有 SOUND_NOTES")
        return
    for uid, seg_texts in segs.items():
        unit_notes = notes.get(uid, [])
        covered = {n.get("segment_id") for n in unit_notes}
        missing = [sid for sid in seg_texts if sid not in covered]
        if len(missing) > len(seg_texts) * 0.2:
            err(f"{uid}: {len(missing)}/{len(seg_texts)} 个句段没有发音提示（允许最多 20% 无提示）")
        per_seg = {}
        for n in unit_notes:
            nid, sid, kind = n.get("id"), n.get("segment_id"), n.get("type")
            per_seg[sid] = per_seg.get(sid, 0) + 1
            if sid not in seg_texts:
                err(f"{nid}: segment_id 不存在 {sid}")
                continue
            if n.get("anchor", "") not in seg_texts[sid]:
                err(f"{nid}: anchor 不在该句段内（区分大小写）: {n.get('anchor')}")
            if kind not in ALLOWED_TYPES:
                err(f"{nid}: 类型 {kind} 不在允许范围 {sorted(ALLOWED_TYPES)}")
                continue
            if LONG_IPA.search(n.get("note", "")):
                err(f"{nid}: note 里出现长音标串，只允许 /t/ 这类单个音或弱读表里的形式")
            if not CJK.search(n.get("note", "")):
                err(f"{nid}: note 应为中文说明")
            if kind == "弱读":
                word = (n.get("word") or "").lower()
                if word not in WEAK_FORMS:
                    err(f"{nid}: 弱读词 {word} 不在弱读表里")
                elif n.get("weak") != WEAK_FORMS[word]:
                    err(f"{nid}: {word} 弱读形式应为 {WEAK_FORMS[word]}")
                if not re.search(rf"\b{re.escape(word)}\b", n.get("anchor", ""), re.I):
                    err(f"{nid}: anchor 里没有弱读词 {word}")
                continue
            pair = n.get("pair")
            if kind == "闪音" and n.get("word"):
                pair = None
            if pair is not None:
                if not (isinstance(pair, list) and len(pair) == 2):
                    err(f"{nid}: pair 应为相邻两个词")
                    continue
                if not pair_in_anchor(pair, n.get("anchor", "")):
                    err(f"{nid}: pair {pair} 在 anchor 中不相邻")
            if cmu is None:
                continue
            if pair is None:
                p = phones(cmu, n.get("word", ""))
                if not p:
                    warn(f"{nid}: CMUdict 查不到 {n.get('word')}，需人工核")
                    continue
                ok = any(p[i] in ("T", "D") and (is_vowel(p[i - 1]) or p[i - 1] == "R")
                         and is_vowel(p[i + 1]) and p[i + 1].endswith("0")
                         for i in range(1, len(p) - 1))
                if not ok:
                    err(f"{nid}: {n.get('word')} 不满足闪音条件（t/d 在元音间且后接非重读元音）")
                continue
            a, b = phones(cmu, pair[0]), phones(cmu, pair[1])
            if not a or not b:
                warn(f"{nid}: CMUdict 查不到 {pair}，需人工核")
                continue
            last, first = a[-1], b[0]
            if kind == "连读" and not ((not is_vowel(last) and is_vowel(first)) or (is_vowel(last) and is_vowel(first))):
                err(f"{nid}: {pair} 不是 辅+元 或 元+元，不能叫连读（{last}+{first}）")
            elif kind == "失爆" and not (last in PLOSIVES and not is_vowel(first)):
                err(f"{nid}: {pair} 不满足失爆（前词爆破音结尾+后词辅音开头）（{last}+{first}）")
            elif kind == "同化" and not (last in ("T", "D", "S", "Z") and first == "Y"):
                err(f"{nid}: {pair} 不满足同化（t/d/s/z + /j/）（{last}+{first}）")
            elif kind == "喉塞化" and not (last == "T" and is_vowel(first)):
                err(f"{nid}: {pair} 不满足喉塞化（/t/ + 元音）（{last}+{first}）")
            elif kind == "闪音" and not (last in ("T", "D") and len(a) > 1 and (is_vowel(a[-2]) or a[-2] == "R")
                                       and is_vowel(first) and first.endswith("0")):
                err(f"{nid}: {pair} 不满足闪音（元音后 t/d + 非重读元音）（{last}+{first}）")
        for sid, count in per_seg.items():
            if count > 3:
                err(f"{uid}/{sid}: 一个句段最多 3 条发音提示，实际 {count}")


def main():
    segs = segments_by_unit()
    if "--unit" in sys.argv:
        index = sys.argv.index("--unit")
        unit_id = sys.argv[index + 1]
        if unit_id not in segs:
            raise SystemExit(f"Unknown unit: {unit_id}")
        segs = {unit_id: segs[unit_id]}
    cmu = load_cmu()
    if "--sounds-only" not in sys.argv:
        check_vocab_and_guidance(segs)
    check_sound_notes(segs, cmu)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    total_notes = sum(len(getattr(lc, "SOUND_NOTES", {}).get(uid, [])) for uid in segs)
    print(f"units={len(segs)} sound_notes={total_notes} errors={len(errors)} warnings={len(warnings)}")
    if "--strict" in sys.argv and errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
