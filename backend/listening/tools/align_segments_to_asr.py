import json, re, difflib, sys
words=json.load(open(sys.argv[1])); cand=json.load(open(sys.argv[2],encoding='utf-8'))
norm=lambda w: re.sub(r"[^a-z0-9']","",w.lower().replace('’',"'"))
aw=[(s,e,norm(t)) for s,e,t,p in words if norm(t)]
res={}
for u in cand['units']:
    b=u.get('learning_audio_bounds')
    lo,hi=(b['start_ms']/1000,b['end_ms']/1000) if b else (globals().get('NEXT',0),1e9)
    win=[w for w in aw if lo-5<=w[0]<=hi+5]
    toks=[]; owner=[]
    for i,s in enumerate(u['transcript']['segments']):
        t=re.sub(r"\[\d+(?:-\d+)?\]","",s['text']); t=re.sub(r"^[WM]:\s*","",t)
        for w in re.split(r'[\s—–-]+',t):
            n=norm(w)
            if n: toks.append(n); owner.append(i)
    sm=difflib.SequenceMatcher(None,toks,[w[2] for w in win],autojunk=False)
    match={}
    for a,b2,n in sm.get_matching_blocks():
        for k in range(n): match[a+k]=b2+k
    segs=[]
    for i,s in enumerate(u['transcript']['segments']):
        idx=[k for k,o in enumerate(owner) if o==i]
        m=[match[k] for k in idx if k in match and all((k+d) in match and match[k+d]==match[k]+d for d in (-1,1) if 0<=k+d<len(toks) and owner[k+d]==i)] or [match[k] for k in idx if k in match]
        cov=len(m)/len(idx)
        segs.append((s['segment_id'][-6:], round(win[m[0]][0],2) if m else None, round(win[m[-1]][1],2) if m else None, round(cov,2)))
    res[u['unit_id']]=segs
    globals()['NEXT']=segs[-1][2] or 0
    print(u['unit_id'][-2:], 'min覆盖率', min(x[3] for x in segs), segs[:3])
json.dump(res,open(sys.argv[3],'w'))
