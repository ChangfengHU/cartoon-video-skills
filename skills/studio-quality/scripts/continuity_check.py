#!/usr/bin/env python3
"""Check continuity evidence, never invent visual approval. Standard library only."""
import argparse, hashlib, json, math
from pathlib import Path

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def inputs_digest(items):
 return hashlib.sha256(json.dumps(items,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def plan_digest(seq):
 return inputs_digest({k:seq.get(k) for k in ['id','range','intent','contact','end_state','states','hold_reason','inputs']})

def evaluate(data, root, stage='preflight'):
 root=Path(root).resolve();issues=[]
 def issue(where,msg):issues.append({'where':where,'finding':msg})
 def asset(x,where):
  if not isinstance(x,dict) or not isinstance(x.get('path'),str):issue(where,'missing file');return None
  p=(root/x['path']).resolve()
  if not p.is_relative_to(root) or not p.is_file():issue(where,'missing/outside project file');return None
  if digest(p)!=x.get('sha256'):issue(where,'stale file hash');return None
  return p
 def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
 ref=data.get('reference',{});asset(ref,'reference')
 if not ref.get('selection_basis') or not ref.get('preserve'):issue('reference','selection basis and preserve scope required')
 if not ref.get('feedback_scope'):issue('reference','feedback scope required; do not infer blanket approval')
 seqs=data.get('sequences',[])
 if not isinstance(seqs,list) or not seqs:issue('sequences','no action sequences');seqs=[]
 ids=set()
 for seq in seqs:
  name=seq.get('id','?')
  if name in ids:issue(name,'duplicate sequence id')
  ids.add(name);span=seq.get('range',[])
  if not isinstance(span,list) or len(span)!=2 or not all(finite(t) for t in span) or not 0<=span[0]<span[1]:issue(name,'invalid range');continue
  if not seq.get('intent') or not seq.get('contact') or not seq.get('end_state'):issue(name,'intent/contact/end state missing')
  states=seq.get('states',[])
  if not states:issue(name,'at least one explicit state required')
  if len(states)<2 and not seq.get('hold_reason'):issue(name,'single-state hold requires narrative reason')
  previous=span[0]
  for state in states:
   t=state.get('at')
   if not finite(t) or not previous<=t<span[1]:issue(name,'state times not ordered within range')
   else:previous=t
   if not state.get('pose') or not state.get('gaze'):issue(name,'state pose/gaze missing')
  inputs=seq.get('inputs',[])
  if not inputs:issue(name,'no frozen action inputs')
  for a in inputs:asset(a,name+' input')
  pre=seq.get('preflight',{});clip=pre.get('clip',{});asset(clip,name+' clip')
  if pre.get('inputs_digest')!=inputs_digest(inputs):issue(name,'preflight no longer matches inputs')
  if pre.get('plan_digest')!=plan_digest(seq):issue(name,'preflight no longer matches action plan/timing')
  review=pre.get('review',{})
  if review.get('status')!='pass':issue(name,'preflight '+str(review.get('status','pending')))
  if review.get('method')!='direct_review' or not review.get('finding'):issue(name,'requires actual visual observation, not automatic/model score')
  for e in review.get('evidence',[]):asset(e,name+' review')
  if not review.get('evidence'):issue(name,'review evidence absent')
  sample_path=asset(pre.get('sample',{}),name+' sample')
  if sample_path:
   try:
    sample=json.loads(sample_path.read_text())
    if sample.get('source_sha256')!=clip.get('sha256'):issue(name,'sample belongs to another clip')
    files=sample.get('files',[])
    if sample.get('frame_count',0)<2:issue(name,'continuous sample has fewer than 2 frames')
    if sample.get('frame_count')!=len(files) or len({x.get('path') for x in files})!=len(files):issue(name,'sample frame count/paths inconsistent')
    for e in sample.get('files',[]):asset(e,name+' sampled frame')
    if not sample.get('files'):issue(name,'sample contains no actual frames')
   except (ValueError,TypeError):issue(name,'invalid sampling manifest')
 if stage=='final':
  target=data.get('target',{});asset(target,'target');samples=data.get('final_samples',[])
  if not samples:issue('final','missing final MP4 samples')
  for s in samples:
   sp=asset(s,'final sample')
   if sp:
    try:
     m=json.loads(sp.read_text())
     if m.get('source_sha256')!=target.get('sha256'):issue('final','sample from old MP4')
     files=m.get('files',[])
     if len(files)<2 or m.get('frame_count')!=len(files) or len({x.get('path') for x in files})!=len(files):issue('final','continuous sample frame count/paths inconsistent')
     for f in m.get('files',[]):asset(f,'final frame')
     if not m.get('files'):issue('final','empty final sample')
    except (ValueError,TypeError):issue('final','invalid sample manifest')
 return {'stage':stage,'status':'candidate' if issues else 'evidence_complete','issues':issues,'note':'Checks files and recorded observations only; not aesthetic quality, whole-film approval or permission to publish.'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('--stage',choices=['preflight','final'],default='preflight');p.add_argument('--out',type=Path);a=p.parse_args()
 try:r=evaluate(json.loads(a.manifest.read_text()),a.manifest.parent,a.stage)
 except (ValueError,TypeError,OSError) as e:p.exit(1,str(e)+'\n')
 s=json.dumps(r,ensure_ascii=False,indent=2);print(s)
 if a.out:a.out.write_text(s+'\n')
 raise SystemExit(2 if r['issues'] else 0)
