# -*- coding: utf-8 -*-
"""V2 audit step 3: decrypt set1 paper, test extraction; probe analysis PDFs. Read-only."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

base = r'D:\kimi-workspace\english-ai\_incoming_source'

# 1) encrypted set-1 question paper
f = base + r'\2026年6月英语六级真题第1套.pdf'
r = PdfReader(f)
if r.is_encrypted:
    res = r.decrypt('')
    print('set1 paper encrypted, decrypt("") ->', res)
print('pages:', len(r.pages))
for i in [1, 2]:
    t = r.pages[i].extract_text() or ''
    print(f'--- p{i+1} ---')
    print(re.sub(r'\n{2,}', '\n', t)[:500])
    print()

# 2) analysis PDFs (contain transcripts): probe page 1-2 text quality
for name in ['2026年6月英语六级解析第1套.pdf', '2026年6月英语六级解析第2套.pdf', '2026年6月英语六级解析第3套.pdf']:
    try:
        rr = PdfReader(base + '\\' + name)
        if rr.is_encrypted:
            print(name, 'encrypted, decrypt ->', rr.decrypt(''))
        t = rr.pages[0].extract_text() or ''
        t2 = rr.pages[min(5, len(rr.pages)-1)].extract_text() or ''
        print('=' * 15, name, '| pages:', len(rr.pages))
        print('  p1:', repr(re.sub(r'\s+', ' ', t)[:150]))
        print('  p6:', repr(re.sub(r'\s+', ' ', t2)[:150]))
    except Exception as e:
        print(name, 'ERROR:', e)
