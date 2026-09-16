#!/usr/bin/env python3
"""Read-only local runtime diagnosis for Cartoon Video Studio."""
from __future__ import annotations
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
SCHEMA='cartoon-video-studio-doctor/v1'
def run(argv,timeout=20):
 try:r=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
 except (OSError,subprocess.TimeoutExpired) as exc:return False,str(exc)
 output=(r.stdout or r.stderr).strip();return r.returncode==0,(output.splitlines()[0] if output else '')
def major(value):
 m=re.search(r'v?(\d+)(?:\.\d+){0,2}',value);return int(m.group(1)) if m else None
def executable(name,argv):
 path=shutil.which(name)
 if not path:return {'status':'missing','path':None}
 ok,version=run([path,*argv]);return {'status':'ready' if ok else 'failed','path':path,'version':version}
def hyperframes(runtime):
 candidates=[runtime/'node_modules/.bin/hyperframes'];found=shutil.which('hyperframes')
 if found:candidates.append(Path(found))
 for path in candidates:
  if path.is_file() and os.access(path,os.X_OK):
   ok,version=run([str(path),'--version']);return {'status':'ready' if ok else 'failed','path':str(path),'version':version}
 return {'status':'missing','path':None}
def browser(hf):
 requested=os.environ.get('HYPERFRAMES_BROWSER_PATH','')
 if requested and Path(requested).is_file() and os.access(requested,os.X_OK):
  ok,version=run([requested,'--version']);return {'status':'ready' if ok else 'failed','path':requested,'version':version,'source':'environment','launch_verified':ok}
 if hf.get('status')=='ready':
  ok,path=run([hf['path'],'browser','path'])
  if ok and Path(path).is_file() and os.access(path,os.X_OK):
   launched,version=run([path,'--headless=new','--no-sandbox','--disable-gpu','--version']);return {'status':'ready' if launched else 'failed','path':path,'version':version,'source':'hyperframes','launch_verified':launched}
 for name in ('chromium','chromium-browser','google-chrome'):
  path=shutil.which(name)
  if path:
   ok,version=run([path,'--headless=new','--no-sandbox','--disable-gpu','--version']);return {'status':'ready' if ok else 'failed','path':path,'version':version,'source':'system','launch_verified':ok}
 return {'status':'missing','path':None,'launch_verified':False}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--runtime-dir',type=Path,default=Path(os.environ.get('VYIBC_STUDIO_RUNTIME_DIR',Path.home()/'.local/share/vyibc/cartoon-video-studio/runtime')));parser.add_argument('--json',action='store_true');args=parser.parse_args()
 checks={name:executable(name,argv) for name,argv in [('node',['--version']),('npm',['--version']),('python3',['--version']),('ffmpeg',['-version']),('ffprobe',['-version'])]}
 if checks['node']['status']=='ready' and (major(checks['node'].get('version','')) or 0)<22:checks['node'].update(status='failed',reason='Node.js 22 or newer is required')
 checks['hyperframes']=hyperframes(args.runtime_dir);checks['chromium']=browser(checks['hyperframes'])
 fc=shutil.which('fc-match');font_ok,font_name=run([fc,'Noto Sans CJK SC','--format=%{family}']) if fc else (False,'')
 checks['chinese_font']={'status':'ready' if font_ok and font_name else 'missing','family':font_name or None}
 required=('node','npm','python3','ffmpeg','ffprobe','hyperframes','chromium','chinese_font');blockers=[name for name in required if checks[name]['status']!='ready']
 print(json.dumps({'schema':SCHEMA,'ok':not blockers,'blocking':blockers,'checks':checks,'notes':['This verifies local tooling only. Remote MCP account readiness and finished-video quality require their own checks.']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
