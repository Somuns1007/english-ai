# -*- coding: utf-8 -*-
"""Transcript pollution stats + question structure inspection. Read-only."""
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r'D:\kimi-workspace\english-ai\backend\listening\data\exams'
d = json.load(open(base + r'\cet6_202606_set1.json', encoding='utf-8'))
q = d['units'][0]['questions'][0]
print('question keys:', list(q.keys()))
print('option keys:', list(q['options'][0].keys()))
print('sample option:', json.dumps(q['options'][0], ensure_ascii=False)[:300])
print()

MOJI = re.compile(r'[ω臼﹒￣｀¨明创也由]')
SPLIT = re.compile(r'\b[A-Za-z]{1,3}(?: [a-z]{1,4}){2,}\b')
CJK_IN_EN = re.compile(r'[\u4e00-\u9fff]')

for f in ('cet6_202606_set1', 'cet6_202606_set2'):
    d = json.load(open(base + '\\' + f + '.json', encoding='utf-8'))
    print('=' * 25, f)
    for u in d['units']:
        tr = u.get('transcript') or {}
        text = tr.get('text') if isinstance(tr, dict) else (tr or '')
        if not text:
            print(' ', u.get('unit_id'), 'NO TRANSCRIPT')
            continue
        n_moji = len(MOJI.findall(text))
        n_split = len(SPLIT.findall(text))
        n_cjk = len(CJK_IN_EN.findall(text))
        status = tr.get('review_status') if isinstance(tr, dict) else '?'
        print(' ', u.get('unit_id'), '| len=%d' % len(text),
              '| mojibake=%d splitwords=%d cjk_chars=%d' % (n_moji, n_split, n_cjk),
              '| review=%s' % status)
