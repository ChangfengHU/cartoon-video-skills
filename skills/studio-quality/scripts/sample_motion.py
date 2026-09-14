#!/usr/bin/env python3
"""Extract bounded continuous frames from actual MP4; never evaluate aesthetics."""
import argparse,hashlib,json,math,subprocess as sp
from pathlib import Path

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def sample(video,root,out,start,end,fps=6,width=360):
 root=Path(root).resolve();video=Path(video).resolve();out=Path(out).resolve()
 if not video.is_relative_to(root) or not out.is_relative_to(root):raise ValueError('video and output must be within project')
 if not all(isinstance(t,(int,float)) and math.isfinite(t) for t in [start,end,fps]) or not 0<=start<end or not 0<fps<=60 or not 64<=width<=1920:raise ValueError('invalid range/fps/width')
 if out.exists() and any(out.iterdir()):raise ValueError('output must be empty; preserve earlier samples')
 probe=json.loads(sp.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(video)]));duration=float(probe['format']['duration'])
 if end>duration+0.001:raise ValueError('range extends beyond source')
 out.mkdir(parents=True,exist_ok=True)
 cmd=['ffmpeg','-v','error','-threads','2','-i',str(video),'-vf',f'trim=start={start}:end={end},setpts=PTS-STARTPTS,fps={fps},scale={width}:-2','-threads','1',str(out/'frame-%04d.png')]
 sp.run(cmd,check=True)
 frames=sorted(out.glob('frame-*.png'))
 if len(frames)<2:raise ValueError('not enough frames for continuous evidence; widen range or increase sampling fps')
 result={'source':str(video.relative_to(root)),'source_sha256':sha(video),'range':[start,end],'sampling_fps':fps,'frame_count':len(frames),'time_note':'trim precedes fps; nominal sample times have source frame quantization, not word alignment','files':[{'path':str(f.relative_to(root)),'sha256':sha(f)} for f in frames],'review_status':'pending','command':cmd}
 (out/'sample.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('video',type=Path);p.add_argument('--project',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--start',required=True,type=float);p.add_argument('--end',required=True,type=float);p.add_argument('--fps',type=float,default=6);p.add_argument('--width',type=int,default=360);a=p.parse_args()
 try:r=sample(a.video,a.project,a.out,a.start,a.end,a.fps,a.width)
 except (ValueError,OSError,sp.CalledProcessError) as e:p.exit(1,str(e)+'\n')
 print(json.dumps({'frames':r['frame_count'],'source_sha256':r['source_sha256'],'review_status':'pending'}))
