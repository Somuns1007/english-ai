# -*- coding: utf-8 -*-
"""V2 audit step 5: extract set1 clean options + answer key; compare set3 transcript vs set1/2. Read-only."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

base = r'D:\kimi-workspace\english-ai\_incoming_source'

# ---------- 1) Set-1 clean options from separate paper ----------
r = PdfReader(base + r'\2026年6月英语六级真题第1套.pdf')
r.decrypt('')
full = '\n'.join((p.extract_text() or '') for p in r.pages)
# locate listening question blocks Q1..Q25
qpat = re.compile(r'(\d{1,2})\.\s+A\)', re.M)
hits = [(m.group(1), m.start()) for m in qpat.finditer(full)]
print('set1 paper: question-start hits:', [h[0] for h in hits][:40])

# ---------- 2) answer key page (p23 of combined) ----------
r3 = PdfReader(base + r'\2026年6月英语六级真题3套全.pdf')
key_text = r3.pages[22].extract_text() or ''
print('\n--- answer key page ---')
print(re.sub(r'\n{2,}', '\n', key_text)[:1500])

# ---------- 3) transcripts from analysis PDFs ----------
def grab(fname):
    rr = PdfReader(base + '\\' + fname)
    return '\n'.join((p.extract_text() or '') for p in rr.pages)

trans = {}
for s in ['第1套', '第2套', '第3套']:
    trans[s] = grab(f'2026年6月英语六级解析{s}.pdf')

# locate listening transcript start in each
for s, t in trans.items():
    m = re.search(r'(News Report (One|1)|Section A|Conversation One)', t)
    print(f'\n解析{s}: len={len(t)}, transcript anchor ->', m.group(0) if m else None)

# compare set3 vs set1/2 by long English n-gram overlap
def english_words(t):
    return re.findall(r"[A-Za-z][a-z]{3,}", t.lower())

def jaccard(a, b):
    sa, sb = set(a), set(b)
    return len(sa & sb) / max(len(sa | sb), 1)

w = {s: english_words(t) for s, t in trans.items()}
print('\nword-set jaccard:')
print(' set3 vs set1:', round(jaccard(w['第3套'], w['第1套']), 3))
print(' set3 vs set2:', round(jaccard(w['第3套'], w['第2套']), 3))
print(' set1 vs set2:', round(jaccard(w['第1套'], w['第2套']), 3))
