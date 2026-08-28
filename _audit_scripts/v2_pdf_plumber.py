# -*- coding: utf-8 -*-
"""V2 data audit step 2: try pdfplumber on 3-set PDF + decrypt set1 paper. Read-only."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pdfplumber

base = r'D:\kimi-workspace\english-ai\_incoming_source'

# 1) pdfplumber on the 3-set combined paper
f = base + r'\2026年6月英语六级真题3套全.pdf'
with pdfplumber.open(f) as pdf:
    print('pages:', len(pdf.pages))
    for i in [1, 2]:
        t = pdf.pages[i].extract_text() or ''
        print(f'--- p{i+1} (pdfplumber) ---')
        print(re.sub(r'\n{2,}', '\n', t)[:600])
        print()
