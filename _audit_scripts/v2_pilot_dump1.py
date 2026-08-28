# -*- coding: utf-8 -*-
"""V2.0 Pilot: dump raw text of set1 paper listening pages + set1/set2 analysis-book
Conversation One regions, for manual candidate construction. Read-only, no DB writes."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

base = r'D:\kimi-workspace\english-ai\_incoming_source'

print('################ SET1 真题卷 p1-2 (listening Section A) ################')
r = PdfReader(base + r'\2026年6月英语六级真题第1套.pdf')
r.decrypt('')
for i in [0, 1]:
    t = r.pages[i].extract_text() or ''
    print(f'===== p{i+1} =====')
    print(t)
