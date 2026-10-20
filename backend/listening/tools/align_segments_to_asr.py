"""Align frozen transcript segments with word-level ASR timestamps.

Usage: python align_segments_to_asr.py words.json candidate.json output.json
The output keeps the original compact machine format (seconds). It is an
alignment aid, not a claim that the audio has been checked by a person.
"""
import difflib
import json
import re
import sys
from pathlib import Path


SMALL_NUMBERS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12",
}


def normalize(token):
    token = token.lower().replace("’", "'")
    token = re.sub(r"(?<=\d)[,.:](?=\d)", "", token)
    token = re.sub(r"[^a-z0-9']", "", token)
    return SMALL_NUMBERS.get(token, token)


def transcript_tokens(text):
    text = re.sub(r"\[\d+(?:-\d+)?\]", "", text)
    text = re.sub(r"^[WM]:\s*", "", text)
    # ASR writes £200 where the edited transcript says 200 pounds.
    text = re.sub(r"\b(\d[\d,]*)\s+pounds?\b", r"\1", text, flags=re.I)
    return [word for raw in re.split(r"[\s—–-]+", text)
            if (word := normalize(raw))]


def asr_tokens(words):
    tokens = []
    for start, end, raw, _confidence in words:
        raw = raw.strip()
        # Faster-whisper sometimes splits £170,000 / 7.3% into adjacent words.
        if tokens and re.fullmatch(r"[,.:]\d+[a-z%?]*", raw, flags=re.I) and tokens[-1][2].isdigit():
            old_start, _, old_word = tokens[-1]
            tokens[-1] = (old_start, end, normalize(old_word + raw))
            continue
        word = normalize(raw)
        if word:
            tokens.append((start, end, word))
    return tokens


def align(words, candidate):
    aw = asr_tokens(words)
    result = {}
    next_start = 0
    for unit in candidate["units"]:
        bounds = unit.get("learning_audio_bounds")
        lo, hi = ((bounds["start_ms"] / 1000, bounds["end_ms"] / 1000)
                  if bounds else (next_start, float("inf")))
        window = [word for word in aw if lo - 5 <= word[0] <= hi + 5]
        tokens, owner = [], []
        for i, segment in enumerate(unit["transcript"]["segments"]):
            for word in transcript_tokens(segment["text"]):
                tokens.append(word)
                owner.append(i)
        matcher = difflib.SequenceMatcher(None, tokens, [w[2] for w in window], autojunk=False)
        matches = {}
        for source, target, count in matcher.get_matching_blocks():
            for offset in range(count):
                matches[source + offset] = target + offset
        rows = []
        for i, segment in enumerate(unit["transcript"]["segments"]):
            positions = [k for k, owning in enumerate(owner) if owning == i]
            in_run = [
                matches[k] for k in positions if k in matches and
                all(k + delta not in matches or matches[k + delta] == matches[k] + delta
                    for delta in (-1, 1)
                    if 0 <= k + delta < len(tokens) and owner[k + delta] == i)
            ]
            chosen = in_run or [matches[k] for k in positions if k in matches]
            rows.append([
                segment["segment_id"][-6:],
                round(window[chosen[0]][0], 2) if chosen else None,
                round(window[chosen[-1]][1], 2) if chosen else None,
                round(len(chosen) / len(positions), 2) if positions else 0,
            ])
        # The ASR drops about six seconds at this speaker change and stretches
        # the word "in" across both turns. Split the damaged span by an
        # approximate speech-rate boundary; keep low coverage for human review.
        if unit["unit_id"] == "cet6_202606_set2_u2":
            rows[11][2] = 423.8
            rows[12][1] = 423.8
            rows[12][2] = 427.34
        result[unit["unit_id"]] = rows
        next_start = rows[-1][2] or next_start
    return result


def main():
    words = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    candidate = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    result = align(words, candidate)
    Path(sys.argv[3]).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for unit_id, rows in result.items():
        print(unit_id, len(rows), "min_coverage", min(row[3] for row in rows))


if __name__ == "__main__":
    main()
