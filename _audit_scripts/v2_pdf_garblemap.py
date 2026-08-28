# -*- coding: utf-8 -*-
"""V2 audit step 4: full-page garble map of 3-set paper; locate set boundaries & listening sections."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

base = r'D:\kimi-workspace\english-ai\_incoming_source'
f = base + r'\2026年6月英语六级真题3套全.pdf'
r = PdfReader(f)

# common garble chars seen: 也 由 皿 ∞ 阳 加 甲 司 四 础 理 迦 诅 民 钞 司 成 仰 仍 ...
GARBLE = re.compile(r'[也由皿∞阳加甲司四础理迦诅民钞成仍仍伊川]')

for i, p in enumerate(r.pages):
    t = p.extract_text() or ''
    g = len(GARBLE.findall(t))
    ratio = g / max(len(t), 1)
    # find set markers and section markers
    marks = []
    for pat in [r'第\s*[123]\s*套', r'S.?e.?tion\s+[ABC]', r'Part\s*[IVX]+', r'听力']:
        for m in re.findall(pat, t):
            marks.append(m)
    head = re.sub(r'\s+', ' ', t)[:70]
    print(f'p{i+1:02d} chars={len(t):4d} garble={g:3d} ({ratio:.1%}) marks={marks[:6]}')
    print('     ', repr(head))
