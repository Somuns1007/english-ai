# -*- coding: utf-8 -*-
"""V2.0a machine precheck step 1: ASR both exam audios with the project's
faster-whisper (tiny.en). Output raw ASR json to review_pack/machine_precheck/.
ASR is an INDEPENDENT machine cross-check against the audio (final evidence);
it does NOT create teacher_verified anything."""
import sys, io, json, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = r'D:\kimi-workspace\english-ai'
OUT = ROOT + r'\backend\listening\data\v2_pilot\review_pack\machine_precheck'
os.makedirs(OUT, exist_ok=True)

from faster_whisper import WhisperModel
model = WhisperModel('tiny.en', device='cpu', compute_type='int8')

AUDIOS = {
    'cet6_202606_set1': ROOT + r'\backend\listening\data\audio\cet6_202606_set1.mp3',
    'cet6_202606_set2': ROOT + r'\backend\listening\data\audio\cet6_202606_set2.m4a',
}

for exam_id, path in AUDIOS.items():
    t0 = time.time()
    segments, info = model.transcribe(path, language='en', vad_filter=True)
    segs = [{'start': round(s.start, 2), 'end': round(s.end, 2), 'text': s.text.strip()} for s in segments]
    rec = {
        'exam_id': exam_id,
        'audio': path,
        'model': 'faster-whisper tiny.en cpu int8',
        'language_prob': round(info.language_probability, 3),
        'duration_s': round(info.duration, 1),
        'segments': segs,
    }
    out = OUT + f'\\{exam_id}.asr.json'
    json.dump(rec, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(exam_id, '| segs:', len(segs), '| duration:', rec['duration_s'], 's | took', round(time.time() - t0, 1), 's')
    print('  first 300 chars:', ' '.join(s['text'] for s in segs)[:300])
