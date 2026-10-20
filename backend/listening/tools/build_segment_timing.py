"""Build per-segment millisecond timing from the checked machine alignment.

Usage: python build_segment_timing.py candidate.json segment_times.machine.json output.json
"""
import json
import sys
from pathlib import Path


def build(candidate, alignment):
    result = {
        "_meta": {
            "source": "faster-whisper base.en word timestamps + align_segments_to_asr.py",
            "status": "machine_aligned",
            "verified_by_human": False,
            "notes": "CET6 u2 seg013 uses an approximate split of an ASR dropout; listen and verify.",
        },
        "segments": {},
    }
    for unit in candidate["units"]:
        rows = alignment[unit["unit_id"]]
        sources = unit["transcript"]["segments"]
        if len(rows) != len(sources):
            raise ValueError(f"Count mismatch in {unit['unit_id']}")
        for source, (suffix, start, end, coverage) in zip(sources, rows):
            segment_id = source["segment_id"]
            if not segment_id.endswith(suffix) or start is None or end is None or end <= start:
                raise ValueError(f"Invalid alignment: {segment_id}")
            result["segments"][segment_id] = {
                "start_ms": max(0, round(start * 1000) - 300),
                "end_ms": round(end * 1000) + 300,
                "coverage": coverage,
                "needs_check": coverage < 0.85 or end - start < 1,
            }
    return result


def main():
    candidate = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    alignment = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    result = build(candidate, alignment)
    Path(sys.argv[3]).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(len(result["segments"]), "segments,",
          sum(item["needs_check"] for item in result["segments"].values()), "need checking")


if __name__ == "__main__":
    main()
