#!/usr/bin/env python3
"""Register a complete character bundle without overwriting existing identities."""
from pathlib import Path
import argparse,json,re,hashlib,shutil,tempfile,os

def register(studio,source,identity,name,brand_file):
 studio=Path(studio).resolve();source=Path(source).resolve();skills=studio.parent;catalog=studio/'characters.json';data=json.loads(catalog.read_text());rows=data['characters']
 if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',identity):raise ValueError('Invalid character id')
 content=(source/'SKILL.md').read_text();match=re.search(r'^name:\s*([a-z0-9-]+)\s*$',content,re.M)
 if not match:raise ValueError('Missing valid skill name')
 skill=match[1];dest=skills/skill
 if any(r['id']==identity or r['skill']==skill for r in rows) or dest.exists():raise ValueError('Character id or skill already exists')
 brandpath=(source/brand_file).resolve()
 if not brandpath.is_relative_to(source) or not brandpath.is_file():raise ValueError('Brand file must be inside source')
 brand=json.loads(brandpath.read_text());bid=brand.get('brand_id')
 if not bid:raise ValueError('Independent brand_id required')
 for r in rows:
  other=json.loads((skills/r['skill']/r['brandFile']).read_text())
  if other.get('brand_id')==bid:raise ValueError('brand_id already exists')
 for f in source.rglob('*'):
  if f.is_symlink():raise ValueError('Symlinks are not accepted in character bundles')
 assets=brand.get('assets',[])
 if not assets:raise ValueError('At least one frozen reference asset required')
 for a in assets:
  file=(source/a['path']).resolve()
  if not file.is_relative_to(source) or not file.is_file():raise ValueError('Asset outside source or missing')
  if hashlib.sha256(file.read_bytes()).hexdigest()!=a['sha256']:raise ValueError('Asset hash mismatch')
 rows.append({'id':identity,'name':name,'skill':skill,'brandFile':brand_file,'approval':brand.get('approval','candidate; no user approval recorded')})
 stage=Path(tempfile.mkdtemp(prefix='.register-',dir=skills));moved=False
 try:
  shutil.copytree(source,stage/'bundle');(stage/'catalog.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');os.replace(stage/'bundle',dest);moved=True;os.replace(stage/'catalog.json',catalog)
 except BaseException:
  if moved:shutil.rmtree(dest)
  raise
 finally:shutil.rmtree(stage)
 return skill
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--id',required=True);p.add_argument('--name',required=True);p.add_argument('--brand-file',default='brand.json');a=p.parse_args()
 print(register(Path(__file__).resolve().parents[1],a.source,a.id,a.name,a.brand_file))
