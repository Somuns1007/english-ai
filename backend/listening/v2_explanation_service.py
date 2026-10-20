"""Post-submission explanation data for V2 listening exams."""
import json
from pathlib import Path

from .v2_exam_service import DATA_DIR, V2_DIR, v2_registry


def explanations_for(attempt: dict, answers: list[dict]) -> list[dict] | None:
    exam_id = attempt['exam_id']
    candidate = v2_registry.get(exam_id)
    if not candidate or exam_id not in {'cet4_202606_set2_v2', 'cet6_202606_set2_v2'}:
        return None
    if exam_id == 'cet4_202606_set2_v2':
        source = json.loads((V2_DIR / 'cet4_202606_set2.explanations.json').read_text(encoding='utf-8'))
        by_number = {q['number']: q for q in source['questions']}
    else:
        source = json.loads((DATA_DIR / 'exams/cet6_202606_set2.json').read_text(encoding='utf-8'))
        by_number = {q['number']: q for u in source['units'] for q in u['questions']}
    own_answers = {a['question_id']: a['final_answer'] for a in answers}
    output = []
    for question in sorted(candidate['questions'], key=lambda q: q['number']):
        number = question['number']
        explanation = by_number[number]
        if explanation['correct_answer'] != question['correct_answer']:
            raise ValueError(f'V2 explanation answer mismatch: {exam_id} #{number}')
        output.append({
            'number': number,
            'question_id': question['question_id'],
            'your_answer': own_answers.get(question['question_id']),
            'correct_answer': question['correct_answer'],
            'source_explanation': explanation['source_explanation'],
            'distractor_analysis': explanation['distractor_analysis'],
        })
    if len(output) != 25:
        raise ValueError(f'Expected 25 V2 explanations for {exam_id}')
    return output
