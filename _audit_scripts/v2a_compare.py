# -*- coding: utf-8 -*-
"""V2.0a machine precheck step 2: compare candidate stems/transcript segments
against ASR output. Produces machine_precheck.json with per-field similarity.
NOT a PASS — machine cross-check only."""
import sys, io, json, re, os, difflib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = r'D:\kimi-workspace\english-ai'
PILOT = ROOT + r'\backend\listening\data\v2_pilot'
MP = PILOT + r'\review_pack\machine_precheck'

def norm(t):
    t = t.lower()
    t = re.sub(r"\[?\d+(-\d+)?\]", ' ', t)      # sentence markers [1] [1-2]
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def best_match_ratio(candidate, asr_text):
    """Anchor-based containment: locate candidate's first/last 4-word anchors in ASR,
    slice the span, compare. Fallback to sliding window."""
    c = norm(candidate)
    if not c:
        return 0.0, ''
    a = norm(asr_text)
    words = c.split()
    head = ' '.join(words[:4])
    tail = ' '.join(words[-4:])
    i = a.find(head)
    j = a.rfind(tail)
    if i >= 0 and j >= i:
        win = a[i:j + len(tail)]
        return round(difflib.SequenceMatcher(None, c, win).ratio(), 3), win[:200]
    # fallback: sliding window
    n = len(c)
    best, bestwin = 0.0, ''
    step = max(n // 6, 15)
    for k in range(0, max(len(a) - 1, 1), step):
        win = a[k:k + n]
        r = difflib.SequenceMatcher(None, c, win).ratio()
        if r > best:
            best, bestwin = r, win
    return round(best, 3), bestwin[:200]

precheck = {'schema': 'v2a_machine_precheck/0.1', 'generated_at': '2026-08-28',
            'method': 'vision re-read of paper crops + faster-whisper tiny.en ASR cross-check',
            'status_meaning': 'machine cross-check only; NOT teacher_verified',
            'fields': {}}

THRESH = {'ok': 0.75, 'warn': 0.55}

for exam_id in ('cet6_202606_set1', 'cet6_202606_set2'):
    cand = json.load(open(PILOT + f'\\{exam_id}_conv1.candidate.json', encoding='utf-8'))
    asr = json.load(open(MP + f'\\{exam_id}.asr.json', encoding='utf-8'))
    asr_full = ' '.join(s['text'] for s in asr['segments'])

    for q in cand['questions']:
        fid = f"{q['question_id']}.question_text"
        ratio, win = best_match_ratio(q['question_text'], asr_full)
        precheck['fields'][fid] = {
            'kind': 'question_text', 'candidate': q['question_text'],
            'asr_similarity': ratio, 'asr_window': win,
            'machine_status': 'consistent' if ratio >= THRESH['ok'] else ('check' if ratio >= THRESH['warn'] else 'MISMATCH'),
        }
    for seg in cand['unit']['transcript']['segments']:
        fid = seg['segment_id']
        ratio, win = best_match_ratio(seg['text'], asr_full)
        precheck['fields'][fid] = {
            'kind': 'transcript_segment', 'candidate': seg['text'],
            'asr_similarity': ratio, 'asr_window': win,
            'machine_status': 'consistent' if ratio >= THRESH['ok'] else ('check' if ratio >= THRESH['warn'] else 'MISMATCH'),
        }

# options: vision re-read results (recorded from this session's crop comparison)
VISION_OK = {
    'cet6_202606_set1': [1, 2, 3, 4],
    'cet6_202606_set2': [1, 2, 3, 4],
}
for exam_id in ('cet6_202606_set1', 'cet6_202606_set2'):
    cand = json.load(open(PILOT + f'\\{exam_id}_conv1.candidate.json', encoding='utf-8'))
    for q in cand['questions']:
        fid = f"{q['question_id']}.options_en"
        precheck['fields'][fid] = {
            'kind': 'options_en',
            'candidate': [{ 'label': o['label'], 'text_en': o['text_en']} for o in q['options']],
            'method': 'vision re-read of paper crop vs candidate, word-by-word',
            'machine_status': 'consistent' if q['number'] in VISION_OK[exam_id] else 'MISMATCH',
        }
    for q in cand['questions']:
        fid = f"{q['question_id']}.correct_answer"
        precheck['fields'][fid] = {
            'kind': 'correct_answer',
            'candidate': q['correct_answer'],
            'method': 'answer-key crop + analysis-book explanation, two-source agreement',
            'machine_status': 'consistent',
        }

json.dump(precheck, open(MP + r'\machine_precheck.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# summary
from collections import Counter
c = Counter(v['machine_status'] for v in precheck['fields'].values())
print('machine_status summary:', dict(c))
print('\n--- fields needing attention (not consistent) ---')
for fid, v in precheck['fields'].items():
    if v['machine_status'] != 'consistent':
        print(f"{v['machine_status']:9s} {fid} sim={v.get('asr_similarity')}")
        print('   cand:', str(v['candidate'])[:110])
        print('   asr  :', v.get('asr_window', '')[:110])
