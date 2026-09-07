#!/usr/bin/env python3
"""Explicit opt-in real production test: one reusable v1 SFX copied to v2.

Writes only the selected SFX provenance revision, integration-test feedback and
one project snapshot. No personal voice, generation or public media upload.
"""
import argparse, importlib.util, json, subprocess, tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('asset_mcp',root/'skills/cartoon-xiaban/scripts/asset_mcp.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
p = argparse.ArgumentParser(description=__doc__); p.add_argument('--allow-write',action='store_true'); args=p.parse_args()
if not args.allow_write: raise SystemExit('Pass --allow-write only for an authorized integration test')
client=module.Client(); page=client.call('asset_search',{'kind':'sfx','query':'ding'})
source=next(a for a in page['assets'] if a.get('seed_id')=='round03-sfx-ding')
directory=Path(tempfile.mkdtemp(prefix='cartoon-assets-live-')).resolve()
module.safe_new(directory/'source-card.json',module.encode(source))
client.download(source['id'],directory/'ding.wav')
card={k:v for k,v in source.items() if k not in {'id','created_at','object'}}
card.update(supersedes=source['id'],import_note='MCP v2 integration migration; original rights, author and review status preserved. No new artistic approval.')
module.safe_new(directory/'card.json',module.encode(card))
cmd=['python3',str(root/'skills/cartoon-xiaban/scripts/asset_mcp.py'),'upload','--card',str(directory/'card.json'),'--file',str(directory/'ding.wav')]
a=json.loads(subprocess.check_output(cmd)); b=json.loads(subprocess.check_output(cmd))
assert a['id']==b['id'] and b['deduplicated'] is True
feedback={'asset_id':a['id'],'project':'mcp-integration-20260907','outcome':'used','reason':'Technical upload/download/hash and cross-session acceptance only; not listening approval or use in a new film.','reviewer':'integration-test','observed_at':'2026-09-07T18:30:00Z'}
f=client.call('asset_feedback',{'feedback':feedback})
selection={'project':'mcp-integration-20260907','story_intent':'Technical provenance-preserving restoration test, not a new episode','platform':'private-test','selected':[{'asset_id':a['id'],'reason':'Check original notification sound survives authenticated transport','project_review':{'status':'verified_for_project','allowed_platforms':['private-test'],'checked_at':'2026-09-07','evidence':'Existing user-authorized original-algorithm SFX; no external distribution in this test'}}]}
module.safe_new(directory/'selection.json',module.encode(selection))
frozen=json.loads(subprocess.check_output(['python3',str(root/'skills/cartoon-xiaban/scripts/asset_mcp.py'),'freeze','--selection',str(directory/'selection.json'),'--output',str(directory/'frozen')]))
other=module.Client(); restored=other.call('project_get',{'id':frozen['project_id']}); assert restored['selection']['project']==selection['project']
result={'asset_id':a['id'],'source_id':source['id'],'sha256':source['object']['sha256'],'duplicate_retry':True,'feedback_id':f['id'],'project_id':frozen['project_id'],'verified_files':frozen['verified_files'],'directory':str(directory),'new_client_restore':True}
module.safe_new(directory/'receipt.json',module.encode(result)); print(json.dumps(result,ensure_ascii=False,indent=2))
