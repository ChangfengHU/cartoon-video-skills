from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1];pkg=root/'plugins/cartoon-video-studio';skills=root/'skills';names=[]
for source in skills.iterdir():
 if not source.is_dir() or not (source/'SKILL.md').exists():continue
 names.append(source.name)
 for f in source.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:
   other=pkg/'skills'/f.relative_to(skills);assert other.is_file() and f.read_bytes()==other.read_bytes(),str(f)
registry=json.loads((skills/'cartoon-video-studio/characters.json').read_text());ids=set();brands=set()
for c in registry['characters']:
 assert c['id'] not in ids;ids.add(c['id']);brand=json.loads((skills/c['skill']/c['brandFile']).read_text());assert brand['brand_id'] not in brands;brands.add(brand['brand_id'])
 for a in brand.get('assets',[]):
  if isinstance(a,dict) and 'path' in a and 'sha256' in a:assert hashlib.sha256((skills/c['skill']/a['path']).read_bytes()).hexdigest()==a['sha256']
lock=json.loads((pkg/'upstream-skills.lock.json').read_text())
for n,digest in lock['files'].items():assert hashlib.sha256((pkg/'skills'/n).read_bytes()).hexdigest()==digest
m=json.loads((pkg/'.mcp.json').read_text());assert set(m['mcpServers'])=={'vyibc-cartoon-assets','vyibc-image','vyibc-douyin','vyibc-youtube','vyibc-voice'}
for n,c in m['mcpServers'].items():assert c['url'].startswith('https://') and c.get('bearer_token_env_var') and 'headers' not in c
print(json.dumps({'skills':len(names),'characters':len(ids),'mcp':len(m['mcpServers']),'mirrors':'identical','upstream_files':len(lock['files'])}))

for c in registry['characters']:
 profile=json.loads((skills/c['skill']/c['profileFile']).read_text())
 assert profile['id']==c['id'] and profile['profile_version']>=1
 for k in ['introduction','personality','speaking_style','suitable_scenes','casting_roles','editorial_status']:assert profile.get(k),k
cl=json.loads((pkg/'character-design.lock.json').read_text())
for name,digest in cl['files'].items():assert hashlib.sha256((pkg/'skills/vyibc-character-design'/name).read_bytes()).hexdigest()==digest
print('Character profiles and imported designer bytes verified')
