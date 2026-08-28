# -*- coding: utf-8 -*-
"""CET Core Correction audit: per-question stem/options/transcript quality. Read-only."""
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# suspicious OCR patterns: mojibake chars, split words, known W-misreads
MOJI = re.compile(r'[ω臼﹒￣｀¨]')
SPLIT_WORD = re.compile(r'\b[A-Za-z]{1,3}(?: [a-z]{1,4}){2,}\b')  # 'spea kers mainl y'
WMIS = re.compile(r'\b(Wbat|Wby|Wben|Wbere|Wbo|Hbw|Hbw|Wbat|W hy|W hat)\b')

def scan(text):
    hits = []
    if not text:
        return ['<EMPTY>']
    for m in MOJI.findall(text):
        hits.append('mojibake:' + m)
    for m in WMIS.findall(text):
        hits.append('W-misread:' + m)
    for m in SPLIT_WORD.findall(text):
        hits.append('split:' + m)
    return hits

base = r'D:\kimi-workspace\english-ai\backend\listening\data\exams'
for f in ('cet6_202606_set1', 'cet6_202606_set2'):
    d = json.load(open(base + '\\' + f + '.json', encoding='utf-8'))
    print('=' * 25, f)
    print('top-level keys:', list(d.keys()))
    units = d.get('units') or []
    nq = 0
    stem_suspect = []
    opts_en_missing = 0
    opts_en_present = 0
    for u in units:
        for q in u.get('questions', []):
            nq += 1
            stem = q.get('question_text') or q.get('stem') or ''
            hits = scan(stem)
            if hits:
                stem_suspect.append((q.get('question_id'), hits, stem[:90]))
            opts = q.get('options', [])
            ens = [(o.get('text_en') or '').strip() for o in opts]
            if all(ens):
                opts_en_present += 1
            else:
                opts_en_missing += 1
    print('questions:', nq, '| options text_en complete:', opts_en_present,
          '| missing:', opts_en_missing)
    print('--- suspect stems ---')
    for qid, hits, stem in stem_suspect:
        print(' ', qid, hits)
        print('    ', repr(stem))
