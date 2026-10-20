import sys, time, json
from faster_whisper import WhisperModel
t=time.time()
m=WhisperModel(sys.argv[2], device='cpu', compute_type='int8')
segs,info=m.transcribe(sys.argv[1], word_timestamps=True, language='en', beam_size=5)
out=[]
for s in segs:
    for w in s.words: out.append((round(w.start,2),round(w.end,2),w.word.strip(),round(w.probability,2)))
print('time',round(time.time()-t,1),'s words',len(out))
json.dump(out,open(sys.argv[3],'w'))
for w in out[:60]: print(w)
