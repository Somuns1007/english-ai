# -*- coding: utf-8 -*-
"""V2 audit step 6: verify set3 listening = duplicate; locate transcript sections. Read-only."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

base = r'D:\kimi-workspace\english-ai\_incoming_source'

def grab(fname):
    rr = PdfReader(base + '\\' + fname)
    return '\n'.join((p.extract_text() or '') for p in rr.pages)

t3 = grab('2026年6月英语六级解析第3套.pdf')
# what does 解析3套 cover? list section anchors
for pat in ['Listening', 'News Report', 'Conversation', 'Passage', 'Recording', '听力']:
    idxs = [m.start() for m in re.finditer(pat, t3)]
    print(f'解析3套 "{pat}": {len(idxs)} hits', idxs[:5])

print('\n--- 解析3套 Section A context ---')
i = t3.find('Section A')
print(re.sub(r'\n{2,}', '\n', t3[i-200:i+600]))

# compare: extract transcript-ish sentences from 解析2套 Passage Two sample
t2 = grab('2026年6月英语六级解析第2套.pdf')
i2 = t2.find('Passage Two')
print('\n--- 解析2套 Passage Two sample ---')
print(re.sub(r'\n{2,}', '\n', t2[i2:i2+400]))
