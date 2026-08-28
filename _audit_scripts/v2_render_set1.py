# -*- coding: utf-8 -*-
"""Render set1 paper listening pages to PNG for vision verification."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pypdfium2 as pdfium

out = r'D:\kimi-workspace\english-ai\_audit_scripts\pages'
os.makedirs(out, exist_ok=True)
pdf = pdfium.PdfDocument(r'D:\kimi-workspace\english-ai\_incoming_source\2026年6月英语六级真题第1套.pdf')
print('pages:', len(pdf))
for i in [0, 1, 2]:
    img = pdf[i].render(scale=2.0).to_pil()
    p = out + rf'\set1_p{i+1}.png'
    img.save(p)
    print(p, img.size)
