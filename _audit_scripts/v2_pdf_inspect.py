# -*- coding: utf-8 -*-
"""V2 data audit step 1: inspect new PDF text extraction quality. Read-only."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

base = r'D:\kimi-workspace\english-ai\_incoming_source'
files = [
    '2026年6月英语六级真题3套全.pdf',
    '2026年6月英语六级真题第1套.pdf',
    '2026年6月英语六级解析第1套.pdf',
    '2026年6月英语六级解析第2套.pdf',
    '2026年6月英语六级解析第3套.pdf',
]
for f in files:
    r = PdfReader(base + '\\' + f)
    print('=' * 20, f, '| pages:', len(r.pages))
    # sample pages: first 3 + a middle page
    for i in [0, 1, 2, len(r.pages) // 2]:
        t = r.pages[i].extract_text() or ''
        ascii_ratio = sum(1 for c in t if ord(c) < 128) / max(len(t), 1)
        print(f'  p{i+1}: chars={len(t)} ascii={ascii_ratio:.0%}')
        snippet = re.sub(r'\s+', ' ', t)[:160]
        print('    ', repr(snippet))
