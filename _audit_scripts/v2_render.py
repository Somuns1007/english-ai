# -*- coding: utf-8 -*-
"""V2 audit step 8: render set-2 listening pages of combined paper to PNG for vision transcription."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pypdfium2 as pdfium

base = r'D:\kimi-workspace\english-ai'
pdf = pdfium.PdfDocument(base + r'\_incoming_source\2026年6月英语六级真题3套全.pdf')
outdir = base + r'\_audit_scripts\pages'
import os
os.makedirs(outdir, exist_ok=True)
# pages 9-11 (0-indexed 8-10): set-2 listening questions
for i in [8, 9, 10]:
    page = pdf[i]
    img = page.render(scale=2.0).to_pil()  # ~144dpi*2
    out = outdir + rf'\set2_p{i+1}.png'
    img.save(out)
    print(out, img.size)
