# -*- coding: utf-8 -*-
"""V2.0a: build the teacher review pack from the two pilot candidate JSONs.

- adds stable question_id / option_id / segment_id
- splits transcripts into per-turn segments
- computes sha256 content hashes (canonicalized), revision=1
- renders evidence: full pages, per-question crops, answer-key blocks
- writes review_pack.json with empty verdict slots bound to hash+revision
- writes REVIEW_GUIDE.md

Idempotent: re-running regenerates pack from candidate JSONs. If a candidate field
changes after a PASS was recorded, its hash changes and the validator will invalidate it.
"""
import sys, io, json, re, os, hashlib, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pypdfium2 as pdfium

ROOT = r'D:\kimi-workspace\english-ai'
PILOT = ROOT + r'\backend\listening\data\v2_pilot'
SRC = ROOT + r'\_incoming_source'
PACK = PILOT + r'\review_pack'
EV = PACK + r'\evidence'
os.makedirs(EV, exist_ok=True)

def canon_text(t: str) -> str:
    t = unicodedata.normalize('NFC', t or '')
    return re.sub(r'\s+', ' ', t).strip()

def h_text(t: str) -> str:
    return hashlib.sha256(canon_text(t).encode('utf-8')).hexdigest()

def h_json(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()

# ---------------------------------------------------------------- candidates
SETS = {
    'set1': {
        'candidate': PILOT + r'\cet6_202606_set1_conv1.candidate.json',
        'exam_id': 'cet6_202606_set1',
        'paper_pdf': SRC + r'\2026年6月英语六级真题第1套.pdf',
        'paper_page0': 0,                       # 0-indexed page of options
        'analysis_pdf': SRC + r'\2026年6月英语六级解析第1套.pdf',
        'audio': ROOT + r'\backend\listening\data\audio\cet6_202606_set1.mp3',
        # crop ranges in PDF points (top_from, top_to) on the paper page
        'crops': {1: (348, 441), 2: (441, 517), 3: (517, 555), 4: (555, 593)},
        'key_block': (143, 207),                # answer-key listening block, 3-in-1 p23
    },
    'set2': {
        'candidate': PILOT + r'\cet6_202606_set2_conv1.candidate.json',
        'exam_id': 'cet6_202606_set2',
        'paper_pdf': SRC + r'\2026年6月英语六级真题3套全.pdf',
        'paper_page0': 8,
        'analysis_pdf': SRC + r'\2026年6月英语六级解析第2套.pdf',
        'audio': ROOT + r'\backend\listening\data\audio\cet6_202606_set2.m4a',
        'crops': {1: (358, 390), 2: (390, 449), 3: (449, 507), 4: (507, 552)},
        'key_block': (355, 418),
    },
}
KEY_PDF = SRC + r'\2026年6月英语六级真题3套全.pdf'
KEY_PAGE0 = 22

# ---------------------------------------------------------------- id + hash + segments
def augment(cfg):
    cand = json.load(open(cfg['candidate'], encoding='utf-8'))
    exam_id = cfg['exam_id']
    unit = cand['unit']
    unit_id = unit['unit_id']

    # transcript segments (per turn)
    turns = [t.strip() for t in unit['transcript']['cleaned_text'].split('\n') if t.strip()]
    segments = []
    for i, turn in enumerate(turns, 1):
        speaker = turn[:2].rstrip(':')
        seg_id = f'{unit_id}_seg{i:03d}'
        segments.append({
            'segment_id': seg_id,
            'speaker': speaker,
            'text': turn,
            'revision': 1,
            'content_hash': h_text(turn),
        })
    unit['transcript']['segments'] = segments
    unit['transcript']['revision'] = 1
    unit['transcript']['content_hash'] = h_text(unit['transcript']['cleaned_text'])

    for q in cand['questions']:
        qid = f"{exam_id}_q{q['number']:03d}"
        q['question_id'] = qid
        q['revision'] = 1
        for o in q['options']:
            o['option_id'] = f"{qid}_{o['label']}"
            o['revision'] = 1
            o['content_hash'] = h_json({'label': o['label'], 'text_en': o['text_en'], 'text_zh': o['text_zh']})
        q['field_hashes'] = {
            'options': h_json([{k: o[k] for k in ('label', 'text_en', 'text_zh')} for o in q['options']]),
            'question_text': h_text(q['question_text']),
            'question_text_zh': h_text(q['question_text_zh']),
            'correct_answer': h_text(q['correct_answer']),
        }
    cand['_meta']['pack_revision'] = 1
    json.dump(cand, open(cfg['candidate'], 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    return cand

# ---------------------------------------------------------------- evidence renders
def render_crops(pdf_path, page0, ranges, prefix, scale=2.0):
    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[page0]
    img = page.render(scale=scale).to_pil()
    pw, ph = page.get_size()
    sx = img.width / pw
    full_path = EV + f'\{prefix}_full.png'
    img.save(full_path)
    outs = {'full': full_path}
    for tag, (t0, t1) in ranges.items():
        crop = img.crop((0, int(t0 * sx), img.width, min(int(t1 * sx), img.height)))
        p = EV + f'\{prefix}_{tag}.png'
        crop.save(p)
        outs[str(tag)] = p
    return outs

# ---------------------------------------------------------------- build
pack = {
    'schema': 'v2a_teacher_review_pack/0.1',
    'generated_at': '2026-08-27',
    'rules': {
        'verdict_values': ['PASS', 'NEEDS_REVIEW'],
        'pass_binding': ['item_id', 'field_id|segment_id', 'revision', 'content_hash', 'reviewer', 'reviewed_at'],
        'invalidation': 'candidate 任何修改会改变 content_hash,校验器将自动判定对应 PASS 失效并回到 review_ready。',
        'unit_verified_rule': 'Unit 只有在全部必验字段 PASS 后才可汇总为 teacher_verified。',
        'final_evidence': {
            'options_en': '原始真题页面(裁切图)',
            'question_text': '原始音频',
            'transcript': '原始音频(逐句逐话轮)',
            'correct_answer': '答案速查表 + 解析册 双向交叉',
            'note': '解析册与自动转录仅为 review helper,不得替代最终证据。',
        },
    },
    'units': [],
    'verdicts': {},
}

for key, cfg in SETS.items():
    cand = augment(cfg)
    exam_id = cfg['exam_id']
    unit = cand['unit']

    # evidence renders
    crops = render_crops(cfg['paper_pdf'], cfg['paper_page0'], cfg['crops'], f'{key}_paper')
    keycrop = render_crops(KEY_PDF, KEY_PAGE0, {'key': cfg['key_block']}, f'{key}_answerkey')

    u = {
        'unit_id': unit['unit_id'],
        'exam_id': exam_id,
        'title': unit['title'],
        'audio': {'path': cfg['audio'], 'note': 'Conversation One 为音频开头第一段', 'sha256': hashlib.sha256(open(cfg['audio'], 'rb').read()).hexdigest()},
        'evidence': {
            'paper_full': crops['full'],
            'question_crops': {f"q{n:03d}": crops[str(n)] for n in (1, 2, 3, 4)},
            'answer_key_block': keycrop['key'],
        },
        'mandatory_fields': [],
    }

    # transcript segments (100% sentence-level vs audio)
    for seg in unit['transcript']['segments']:
        fid = seg['segment_id']
        u['mandatory_fields'].append({'field_id': fid, 'kind': 'transcript_segment', 'evidence': 'audio', 'content': seg['text'], 'revision': 1, 'content_hash': seg['content_hash']})
        pack['verdicts'][fid] = {'verdict': None, 'reviewer': None, 'reviewed_at': None, 'revision': 1, 'content_hash': seg['content_hash'], 'note': None}

    for q in cand['questions']:
        qid = q['question_id']
        for kind, content, ev, hh in [
            ('options_en', [{k: o[k] for k in ('label', 'text_en')} for o in q['options']], 'paper_page', q['field_hashes']['options']),
            ('question_text', q['question_text'], 'audio', q['field_hashes']['question_text']),
            ('correct_answer', q['correct_answer'], 'answer_key+analysis_cross', q['field_hashes']['correct_answer']),
        ]:
            fid = f'{qid}.{kind}'
            u['mandatory_fields'].append({'field_id': fid, 'kind': kind, 'evidence': ev, 'content': content, 'revision': 1, 'content_hash': hh})
            pack['verdicts'][fid] = {'verdict': None, 'reviewer': None, 'reviewed_at': None, 'revision': 1, 'content_hash': hh, 'note': None}
        # optional helper fields (not required for unit verified)
        for kind, hh in [('options_zh', None), ('question_text_zh', q['field_hashes']['question_text_zh'])]:
            fid = f'{qid}.{kind}'
            pack['verdicts'][fid] = {'verdict': None, 'reviewer': None, 'reviewed_at': None, 'revision': 1, 'content_hash': hh, 'note': '辅助字段(复盘用),非必验'}

    # payload field
    pfid = f'{exam_id}_u1.exam_payload'
    u['mandatory_fields'].append({'field_id': pfid, 'kind': 'exam_payload', 'evidence': 'payload_whitelist_check', 'content': '见 payload_preview 目录;校验器重新生成并断言白名单', 'revision': 1, 'content_hash': None})
    pack['verdicts'][pfid] = {'verdict': None, 'reviewer': None, 'reviewed_at': None, 'revision': 1, 'content_hash': None, 'note': '需 100% 确认无禁用字段'}

    pack['units'].append(u)

json.dump(pack, open(PACK + r'\review_pack.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
n_mand = sum(len(u['mandatory_fields']) for u in pack['units'])
print('review pack written:', PACK + r'\review_pack.json')
print('mandatory fields total:', n_mand, '| verdict slots:', len(pack['verdicts']))
