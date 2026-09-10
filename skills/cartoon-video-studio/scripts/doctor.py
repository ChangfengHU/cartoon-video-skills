#!/usr/bin/env python3
import shutil,subprocess,json,os
checks={}
for tool,args in [('node',['--version']),('ffmpeg',['-version']),('python3',['--version']),('hyperframes',['--version'])]:
 path=shutil.which(tool)
 if not path:checks[tool]={'available':False};continue
 try:
  r=subprocess.run([path]+args,capture_output=True,text=True,timeout=12);checks[tool]={'available':r.returncode==0,'version':r.stdout.splitlines()[0] if r.stdout else ''}
 except subprocess.TimeoutExpired:checks[tool]={'available':False,'reason':'timeout'}
browser=os.environ.get('HYPERFRAMES_BROWSER_PATH');checks['chromium']={'available':bool(browser and os.path.isfile(browser) and os.access(browser,os.X_OK)) or bool(shutil.which('chromium') or shutil.which('google-chrome')),'launch_verified':False}
checks['authorization']={k:bool(os.environ.get(k)) for k in ['DOUBAO_API_KEY','CARTOON_ASSETS_TOKEN','VYIBC_IMAGE_TOKEN','VYIBC_DOUYIN_TOKEN','VYIBC_YOUTUBE_TOKEN']}
print(json.dumps(checks,ensure_ascii=False,indent=2))
