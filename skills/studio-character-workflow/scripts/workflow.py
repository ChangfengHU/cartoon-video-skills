#!/usr/bin/env python3
"""Offline project evidence validation and existing production-ledger initialization."""
import argparse, hashlib, importlib.util, json
from pathlib import Path

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def check(data,root):
 root=Path(root).resolve();issues=[]
 def need(ok,msg):
  if not ok:issues.append(msg)
 def file(item,label):
  if not isinstance(item,dict) or not isinstance(item.get('path'),str):need(False,label+': file required');return None
  p=(root/item['path']).resolve()
  if not p.is_relative_to(root) or not p.is_file():need(False,label+': missing/outside project');return None
  if digest(p)!=item.get('sha256'):need(False,label+': stale SHA256');return None
  return p
 need(data.get('schema_version')==1,'schema_version must be 1')
 policy=file(data.get('voice_policy'),'voice_policy');excluded=set()
 if policy:
  v=json.loads(policy.read_text());ids=v.get('excluded_voice_ids');need(isinstance(ids,list) and all(isinstance(x,str) and x.strip() for x in ids),'invalid excluded_voice_ids')
  if isinstance(ids,list):excluded={str(x).strip().casefold() for x in ids}
 references=data.get('references',[]);need(isinstance(references,list),'references must be a list');refs={}
 for r in references if isinstance(references,list) else []:
  rid=r.get('id');need(bool(rid) and rid not in refs,'duplicate/missing reference id');refs[rid]=r
  file(r.get('image'),str(rid)+' image');need(bool(r.get('platform')) and bool(r.get('source_url')),str(rid)+': source required')
  need(bool(r.get('preview_asset_id')),str(rid)+': private preview not registered')
  if r.get('used_for_generation'):
   need(r.get('usage_status')=='recorded_at_generation',str(rid)+': usage only retrospectively recorded or unknown')
   file(r.get('request_receipt'),str(rid)+' generation receipt')
 chars=data.get('characters',[]);need(isinstance(chars,list) and bool(chars),'characters required');seen=set()
 for c in chars if isinstance(chars,list) else []:
  cid=c.get('id');need(bool(cid) and cid not in seen,'duplicate/missing character id');seen.add(cid)
  profile=file(c.get('profile'),str(cid)+' profile')
  if profile:
   p=json.loads(profile.read_text());need(p.get('id')==cid,str(cid)+': profile identity mismatch')
   for k in ['positioning','personality','suitable_scenes','identity_locks']:need(bool(p.get(k)),str(cid)+': profile missing '+k)
  linked=c.get('reference_ids',[]);need(isinstance(linked,list) and all(x in refs for x in linked),str(cid)+': unknown reference')
  assets=c.get('assets',[]);need(bool(assets),str(cid)+': no actual assets')
  for a in assets:file(a,str(cid)+' asset')
  voice=c.get('voice',{});vid=voice.get('voice_id','');need(bool(vid) and vid.strip().casefold() not in excluded,str(cid)+': excluded/missing voice')
  for k in ['provider','model','selection_reason']:need(bool(voice.get(k)),str(cid)+': voice missing '+k)
  file(voice.get('preview'),str(cid)+' voice preview');file(c.get('visual_review'),str(cid)+' visual review')
 video=data.get('example_video')
 if video is not None:
  target=file(video.get('file'),'video');report=file(video.get('release_report'),'video release report')
  if target and report:
   spec=importlib.util.spec_from_file_location('studio_release',Path(__file__).resolve().parents[2]/'cartoon-video-studio/scripts/release_check.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
   rd=json.loads(report.read_text());need(rd.get('target',{}).get('sha256')==digest(target),'release report targets a different video')
   result=m.evaluate(rd,report.parent)
   # Existing checker returns issues, not an artistic score.
   for issue in result['issues']:issues.append('release: '+str(issue))
 delivery=data.get('delivery',{});file(delivery.get('receipt'),'delivery receipt')
 evidence=delivery.get('browser_evidence',[]);need(bool(evidence),'browser evidence required')
 for e in evidence:file(e,'browser evidence')
 return issues

def init(root,brief):
 root=Path(root).resolve();brief=Path(brief).resolve()
 if not brief.is_relative_to(root) or not brief.is_file():raise ValueError('Brief must be an existing project file')
 data=json.loads(brief.read_text());names=[('reference-research',[]),('character-design',['reference-research']),('voice-casting',['character-design'])]
 if data.get('example_video',True):names += [('scene-production',['voice-casting']),('final-review',['scene-production'])]
 else:names += [('final-review',['character-design','voice-casting'])]
 names += [('asset-delivery',['final-review'])]
 script=Path(__file__).resolve().parents[2]/'cartoon-video-studio/scripts/production_state.py'
 spec=importlib.util.spec_from_file_location('studio_production',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 # A single existing ledger transaction makes initialization atomic and idempotent.
 with m.ledger(root) as (_,state):
  for name,deps in names:
   extras=data.get('stage_inputs',{}).get(name,[])
   if not isinstance(extras,list) or not all(isinstance(x,str) and (root/x).resolve().is_relative_to(root) for x in extras):raise ValueError('Stage inputs must stay inside project')
   global_inputs=[data['voice_policy_path']] if data.get('voice_policy_path') else []
   if not all(isinstance(x,str) and (root/x).resolve().is_relative_to(root) for x in global_inputs):raise ValueError('Policy must stay inside project')
   expected={'status':'pending','deps':deps,'input_paths':list(dict.fromkeys([str(brief.relative_to(root))]+global_inputs+extras)),'outputs':[]}
   if name in state['tasks']:
    old=state['tasks'][name]
    if old['deps']!=deps or old['input_paths']!=expected['input_paths']:raise ValueError('Existing plan differs; preserve it and reconcile explicitly')
   else:state['tasks'][name]=expected
 return [name for name,_ in names]

if __name__=='__main__':
 p=argparse.ArgumentParser();subs=p.add_subparsers(dest='command',required=True);i=subs.add_parser('init');i.add_argument('--project',required=True);i.add_argument('--brief',required=True);c=subs.add_parser('check');c.add_argument('report');args=p.parse_args()
 try:
  if args.command=='init':print(json.dumps({'tasks':init(args.project,args.brief),'executed':False}));raise SystemExit(0)
  path=Path(args.report);issues=check(json.loads(path.read_text()),path.parent);print(json.dumps({'evidence_complete':not issues,'artistic_approval':'not_inferred','issues':issues},ensure_ascii=False,indent=2));raise SystemExit(2 if issues else 0)
 except (ValueError,KeyError,TypeError,OSError) as e:print(json.dumps({'error':str(e)},ensure_ascii=False));raise SystemExit(1)
