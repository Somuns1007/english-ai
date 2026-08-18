# -*- coding: utf-8 -*-
"""
为 3 个验收案例题(第2套 Q3/Q9/Q10)写入教师标注。
标注内容全部来自解析 PDF 的"答案解析 + 干扰项排除"原文, 人工核对后 review_status 置 reviewed。
"""
import json
from pathlib import Path

EXAM_DIR = Path(__file__).resolve().parent.parent / "data" / "exams"
PATH = EXAM_DIR / "cet6_202606_set2.json"

CURATED = {
    3: {
        "question_text": "What does the woman suggest the man do?",
        "teacher_annotation": {
            "evidence_text": (
                "if you are going for a whole week, why don't you do a couple of nights "
                "in somewhere really glamorous and then do the rest of the week "
                "a bit further up the coast where the accommodation is cheaper?"
            ),
            "key_locators": ["题干对象: woman suggest", "录音句[3]"],
            "paraphrase": [
                {
                    "source": "do a couple of nights in somewhere really glamorous and then do the rest of the week ... where the accommodation is cheaper",
                    "option": "B",
                    "note": "对录音建议整体的同义转述",
                }
            ],
            "distractors": [
                {
                    "option": "A",
                    "source_hook": "rent a car",
                    "logic": ["speaker_confusion", "later_info_interference"],
                    "note": "租车是男士听完女士建议后自己联想到的内容, 并非女士给出的建议",
                },
                {
                    "option": "C",
                    "source_hook": "all inclusive",
                    "logic": ["speaker_confusion", "later_info_interference"],
                    "note": "全包式住宿同样是男士后续的联想, 属于说话人归属混淆",
                },
                {
                    "option": "D",
                    "source_hook": "a bit further up the coast where the accommodation is cheaper",
                    "logic": ["scope_shift"],
                    "note": "女士建议的是豪华几晚+便宜几晚的组合方案, 并非只选远离海岸的便宜酒店",
                },
            ],
        },
        "ai_annotation": {
            "review_status": "pending_review",
            "generated_by": "seed_from_teacher_example",
            "generated_at": None,
            "diagnosis_candidates": [
                {"code": "speaker_confusion", "confidence": 0.84, "reason": "学生选择的信息属于男士后续补充"},
                {"code": "later_info_interference", "confidence": 0.77, "reason": "正确建议出现后又出现高表面相关信息"},
                {"code": "question_target_missed", "confidence": 0.65, "reason": "题干问的是女士的建议而非男士的想法"},
            ],
            "dictation_template": None,
            "chunking": [],
        },
    },
    9: {
        "question_text": "What are passionate people considered likely to do in America?",
        "teacher_annotation": {
            "evidence_text": (
                "On the whole, passionate people are thought of in a positive light "
                "and considered likely to achieve their goals."
            ),
            "key_locators": ["题干对象: passionate people considered likely to do", "录音句[9]"],
            "paraphrase": [
                {
                    "source": "considered likely to achieve their goals",
                    "option": "A",
                    "note": "对 achieve their goals 的同义转述",
                }
            ],
            "distractors": [
                {
                    "option": "B",
                    "source_hook": "are thought of in a positive light",
                    "logic": ["subject_swap"],
                    "note": "被动结构: 是别人以积极的眼光看待有激情的人(他人是评价主体), 而不是他们积极看待事物——主客体关系误判",
                },
                {
                    "option": "C",
                    "source_hook": "the importance of passion been overstated",
                    "logic": ["object_swap"],
                    "note": "被讨论是否夸大的是激情的重要性, 不是有激情的人的重要性",
                },
                {
                    "option": "D",
                    "source_hook": "job descriptions and in interviews",
                    "logic": ["inference_overreach"],
                    "note": "激情在面试中被提及, 不等于有激情的人在面试中占据主导, 属于过度推断",
                },
            ],
        },
        "ai_annotation": {
            "review_status": "pending_review",
            "generated_by": "seed_from_teacher_example",
            "generated_at": None,
            "diagnosis_candidates": [
                {"code": "subject_swap", "confidence": 0.86, "reason": "被动句评价主体误判: 把'被别人积极评价'理解成'自己积极看待事物'"},
                {"code": "lexical_overlap_trap", "confidence": 0.6, "reason": "positive/light 等原词复现吸引"},
            ],
            "dictation_template": None,
            "chunking": [],
        },
    },
    10: {
        "question_text": "What does a new study from Stanford show about the importance of passion in predicting achievement?",
        "teacher_annotation": {
            "evidence_text": (
                "passion may be less important in certain cultures, and the fact that "
                "passion is often seen as a key to achievement may reflect "
                "a distinctly Western model of motivation."
            ),
            "key_locators": ["题干对象: new study from Stanford / importance of passion", "录音句[10]"],
            "paraphrase": [
                {
                    "source": "less important in certain cultures",
                    "option": "C",
                    "note": "'某些文化中不那么重要'可概括为'重要性因文化而异'",
                }
            ],
            "distractors": [
                {
                    "option": "A",
                    "source_hook": "fulfilling obligations to others",
                    "logic": ["information_crosswire"],
                    "note": "对他人负责是集体主义文化人群的特点, 不是激情的重要性的体现",
                },
                {
                    "option": "B",
                    "source_hook": "a distinctly Western model of motivation",
                    "logic": ["scope_shift"],
                    "note": "录音强调这是西方模式而非普遍模式, 选项把局部说成普遍, 属于范围扩大",
                },
                {
                    "option": "D",
                    "source_hook": "overstated",
                    "logic": ["mention_vs_claim"],
                    "note": "录音说的是重要性可能被夸大(overstated), 而非被低估",
                },
            ],
        },
        "ai_annotation": {
            "review_status": "pending_review",
            "generated_by": "seed_from_teacher_example",
            "generated_at": None,
            "diagnosis_candidates": [
                {"code": "scope_shift", "confidence": 0.88, "reason": "把'西方模式'误当成'普遍模式', 范围扩大"},
                {"code": "paraphrase_missed", "confidence": 0.55, "reason": "未识别 less important in certain cultures 与'因文化而异'的概括关系"},
            ],
            "dictation_template": None,
            "chunking": [],
        },
    },
}


def main():
    data = json.loads(PATH.read_text(encoding="utf-8"))
    patched = 0
    for unit in data["units"]:
        for q in unit["questions"]:
            if q["number"] in CURATED:
                c = CURATED[q["number"]]
                q["question_text"] = c["question_text"]
                q["teacher_annotation"] = c["teacher_annotation"]
                q["ai_annotation"] = c["ai_annotation"]
                q["review_status"] = "reviewed"
                patched += 1
    PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"patched {patched} questions in {PATH.name}")
    assert patched == 3, "应恰好修正 3 道验收案例题"


if __name__ == "__main__":
    main()
