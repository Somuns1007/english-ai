# -*- coding: utf-8 -*-
"""Regression checks for the CET-4 Set 1 exam payload and grading key."""
import importlib.util
import unittest
from pathlib import Path

service_path = Path(__file__).resolve().parent.parent / "listening/v2_exam_service.py"
spec = importlib.util.spec_from_file_location("cet4_set1_exam_service", service_path)
exams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exams)


EXAM_ID = "cet4_202606_set1_v2"
PUBLISHED_KEY = "CBADBDCAABCDDBABDCADACCBD"


class CET4Set1ExamTest(unittest.TestCase):
    def test_paper_has_all_25_questions_in_eight_audio_units(self):
        paper = exams.paper_dto(EXAM_ID)
        self.assertIsNotNone(paper)
        self.assertEqual(paper["question_delivery"], "audio_only")
        self.assertEqual([len(unit["questions"]) for unit in paper["units"]],
                         [2, 2, 3, 4, 4, 3, 3, 4])
        questions = [q for unit in paper["units"] for q in unit["questions"]]
        self.assertEqual([q["number"] for q in questions], list(range(1, 26)))
        self.assertTrue(all([o["label"] for o in q["options"]] == list("ABCD")
                            for q in questions))
        exams.assert_no_forbidden(paper)
        self.assertIsNotNone(exams.audio_file(EXAM_ID))

    def test_grade_uses_published_answer_key(self):
        candidate = exams.v2_registry.get(EXAM_ID)
        actual_key = "".join(q["correct_answer"] for q in candidate["questions"])
        self.assertEqual(actual_key, PUBLISHED_KEY)
        answers = [
            {"question_id": f"cet4_202606_set1_q{number:03}", "final_answer": choice}
            for number, choice in enumerate(PUBLISHED_KEY, 1)
        ]
        self.assertEqual(exams.grade_attempt(answers, EXAM_ID)["score"], 25)
        answers[0]["final_answer"] = "A"
        self.assertEqual(exams.grade_attempt(answers, EXAM_ID)["score"], 24)


if __name__ == "__main__":
    unittest.main()
