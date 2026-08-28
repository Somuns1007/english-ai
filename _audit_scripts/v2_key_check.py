# -*- coding: utf-8 -*-
"""V2 audit step 7: cross-validate old DB answers vs official answer key. Read-only."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY = {
    'cet6_202606_set1': list('BCADACBAADCDBDAACBBCDDBAC'.replace('','')) ,  # placeholder
}
# official keys from answer-key page
key1 = ['B','C','A','D','A','C','B','A','A','D','C','D','B','D','A','A','C','B','B','C','D','D','B','A','C']
key2 = ['A','A','B','D','D','C','B','C','A','C','D','D','A','C','A','B','A','C','B','B','D','C','B','D','C']

base = r'D:\kimi-workspace\english-ai\backend\listening\data\exams'
for f, key in [('cet6_202606_set1', key1), ('cet6_202606_set2', key2)]:
    d = json.load(open(base + '\\' + f + '.json', encoding='utf-8'))
    mism = []
    for u in d['units']:
        for q in u['questions']:
            n = q['number']
            if q['correct_answer'] != key[n-1]:
                mism.append((n, q['correct_answer'], key[n-1]))
    print(f, '| mismatches vs official key:', mism if mism else 'NONE (25/25 match)')
