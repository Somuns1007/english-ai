# -*- coding: utf-8 -*-
"""V2.0 Pilot: build the new exam payload preview from candidate JSONs and assert
forbidden fields are absent. Writes payload preview files. No DB/existing-data changes."""
import sys, io, json, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r'D:\kimi-workspace\english-ai\backend\listening\data\v2_pilot'
OUT = BASE + r'\payload_preview'

FORBIDDEN_QUESTION = [
    'question_text', 'question_text_zh', 'correct_answer', 'source_explanation',
    'distractor_analysis', 'teacher_annotation', 'ai_annotation', 'evidence_text',
    'evidence_start_ms', 'evidence_end_ms', 'evidence_marker',
    'timing_status', 'review_status', 'provenance',
]
FORBIDDEN_OPTION = ['text_zh']
FORBIDDEN_UNIT = ['transcript', 'timing_status', 'timing_note']
ALLOWED_QUESTION = ['id', 'number', 'section', 'options']
ALLOWED_OPTION = ['label', 'text_en']
ALLOWED_UNIT = ['unit_id', 'section', 'type', 'title', 'audio_path']

def build_payload(cand: dict) -> dict:
    unit = cand['unit']
    p_unit = {k: unit[k] for k in ALLOWED_UNIT if k in unit}
    p_unit['exam_id'] = cand['exam_id']
    p_questions = []
    for q in cand['questions']:
        pq = {
            'id': f"{cand['exam_id']}_q{q['number']}",
            'number': q['number'],
            'section': q.get('section') or unit['section'],
            'options': [
                {'label': o['label'], 'text_en': o['text_en']}
                for o in q['options']
            ],
        }
        p_questions.append(pq)
    return {'unit': p_unit, 'questions': p_questions}

def assert_clean(obj, path=''):
    """Recursively assert no forbidden keys/values leak."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in FORBIDDEN_QUESTION + FORBIDDEN_OPTION + FORBIDDEN_UNIT, f'FORBIDDEN KEY {k} at {path}'
            assert_clean(v, f'{path}.{k}')
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            assert_clean(v, f'{path}[{i}]')

import os
os.makedirs(OUT, exist_ok=True)
for name in ['cet6_202606_set1_conv1', 'cet6_202606_set2_conv1']:
    cand = json.load(open(BASE + f'\\{name}.candidate.json', encoding='utf-8'))
    payload = build_payload(cand)
    assert_clean(payload)
    out = OUT + f'\\{name}.exam_payload.json'
    json.dump(payload, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('OK written:', out)
    # sanity: all options have non-empty text_en
    for q in payload['questions']:
        assert len(q['options']) == 4 and all(o['text_en'].strip() for o in q['options'])
    print('  questions:', [q['number'] for q in payload['questions']],
          '| all 4x options text_en non-empty: True')

print('\nassert_clean passed: no forbidden field in payload.')
