# -*- coding: utf-8 -*-
"""V2 batch: parse set1 paper text layer -> all 25 questions' English options.
Two-column layout means text order interleaves (A,C / B,D); we reassemble by label.
Output raw parse for manual review. Read-only."""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

r = PdfReader(r'D:\kimi-workspace\english-ai\_incoming_source\2026年6月英语六级真题第1套.pdf')
r.decrypt('')
text = '\n'.join((p.extract_text() or '') for p in r.pages[:3])  # listening on p1-3

# cut listening region: from 'Questions 1 to 4' to 'Part' III / reading start
start = text.find('Questions 1 to 4')
end = text.find('Part 111')
if end < 0:
    end = text.find('Reading Comprehension')
region = text[start:end]

# split into per-question blocks: 'N. ' begins a question; options A) B) C) D)
# find all question starts
qs = [(int(m.group(1)), m.start()) for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\.\s+A\)', region)]
print('question starts found:', [n for n, _ in qs])

questions = {}
for idx, (n, pos) in enumerate(qs):
    stop = qs[idx + 1][1] if idx + 1 < len(qs) else len(region)
    block = region[pos:stop]
    # options: split by label markers
    parts = re.split(r'([ABCD8])[\)）]', block)
    # parts[0] = 'N. ' ; then alternating label, text
    opts = {}
    i = 1
    while i + 1 < len(parts):
        lab = parts[i].replace('8', 'B')  # OCR: 8) misread for B)
        txt = parts[i + 1]
        # stop at next question-number line or 'Questions' marker
        txt = re.split(r'\n\s*(?:\d{1,2}\.\s|Question)', txt)[0]
        txt = re.sub(r'\s+', ' ', txt).strip()
        if lab in 'ABCD' and txt:
            opts[lab] = txt
        i += 2
    questions[n] = opts

for n in sorted(questions):
    o = questions[n]
    ok = all(k in o for k in 'ABCD')
    print(f'\nQ{n} [{"OK" if ok else "INCOMPLETE"}]')
    for lab in 'ABCD':
        print(f'  {lab}) {o.get(lab, "<MISSING>")}')

json.dump({str(k): v for k, v in questions.items()},
          open(r'D:\kimi-workspace\english-ai\_audit_scripts\set1_options_raw.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
