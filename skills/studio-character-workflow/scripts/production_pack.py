#!/usr/bin/env python3
"""Validate real scene/action evidence; no artistic approval is inferred."""
import json,hashlib,sys
from pathlib import Path

def check(data,root):
 root=Path(root).resolve(); issues=[]
 def need(value,label):
  if not value:issues.append(label)
 def file(item,label):
  if not isinstance(item,dict):need(False,label+': file required');return
  p=(root/str(item.get('path',''))).resolve()
  if not p.is_relative_to(root) or not p.is_file():need(False,label+': missing/outside project');return
  need(hashlib.sha256(p.read_bytes()).hexdigest()==item.get('sha256'),label+': stale hash')
 need(data.get('schema_version')==1,'schema_version must be 1')
 c=data.get('character',{});need(c.get('id') and c.get('display_name') and c.get('naming_basis'),'character identity/name/basis required')
 scenes=data.get('scenes',[]);need(isinstance(scenes,list) and scenes,'scenes required');ids=set()
 for s in scenes if isinstance(scenes,list) else []:
  sid=s.get('id');need(sid and sid not in ids,'scene id missing/duplicate');ids.add(sid)
  for k in ['location','time_of_day','style_reference','actor_placement']:need(s.get(k),str(sid)+': missing '+k)
  file(s.get('image'),str(sid)+' image');file(s.get('composite_sample'),str(sid)+' composite')
 for req in data.get('scene_requirements',[]):need(req.get('scene_id') in ids,'unresolved scene requirement')
 for a in data.get('actions',[]):
  frames=a.get('frames',[]);need(len(frames)>=3,'continuous action needs actual intermediate poses')
  for f in frames:
   file(f.get('image'),'action frame');need(isinstance(f.get('duration_ms'),(float,int)) and f['duration_ms']>0,'invalid frame duration');need(isinstance(f.get('foot_anchor'),list) and len(f['foot_anchor'])==2,'foot anchor required')
  file(a.get('continuous_sample'),'continuous action sample')
 return issues
if __name__=='__main__':
 try:
  if len(sys.argv)!=3 or sys.argv[1]!='check':raise ValueError('usage: production_pack.py check FILE')
  p=Path(sys.argv[2]);issues=check(json.loads(p.read_text()),p.parent);print(json.dumps({'issues':issues,'evidence_complete':not issues,'artistic_approval':'not_inferred'},ensure_ascii=False));sys.exit(2 if issues else 0)
 except (ValueError,TypeError,KeyError,OSError) as e:print(json.dumps({'error':str(e)}));sys.exit(1)
