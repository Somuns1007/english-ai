# -*- coding: utf-8 -*-
"""V2.0 Pilot: dump Conversation One regions from analysis books (stems/transcript/zh)."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

base = r'D:\kimi-workspace\english-ai\_incoming_source'

for s in ['第1套', '第2套']:
    rr = PdfReader(base + f'\\2026年6月英语六级解析{s}.pdf')
    full = '\n'.join((p.extract_text() or '') for p in rr.pages)
    print('#' * 25, s)
    # locate Conversation One region
    m = re.search(r'Conversation\s+One', full)
    if not m:
        print('Conversation One NOT FOUND; anchors:')
        for pat in ['听力原文', 'Section A', 'Q1', 'What']:
            print(' ', pat, [mm.start() for mm in re.finditer(pat, full)][:5])
        continue
    seg = full[m.start():m.start() + 4200]
    print(re.sub(r'\n{3,}', '\n\n', seg))
