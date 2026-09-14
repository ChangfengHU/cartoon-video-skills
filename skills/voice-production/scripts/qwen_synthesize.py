#!/usr/bin/env python3
"""One Qwen preset TTS request. Environment credentials; no enrollment or paid retries."""
import argparse, hashlib, json, os, subprocess, urllib.request, urllib.parse
from pathlib import Path

ENDPOINT='https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation'

def save(path, value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2));tmp.replace(path)

def save_private(path, value):
    # Create with owner-only mode from the first byte; never route signed URLs to stdout.
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f,ensure_ascii=False,indent=2)

def cloud(body):
    key=os.environ.get('DASHSCOPE_API_KEY')
    if not key:raise ValueError('Missing DASHSCOPE_API_KEY in child environment')
    headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}
    if os.environ.get('DASHSCOPE_WORKSPACE_ID'):headers['X-DashScope-WorkSpace']=os.environ['DASHSCOPE_WORKSPACE_ID']
    request=urllib.request.Request(ENDPOINT,data=json.dumps(body).encode(),headers=headers)
    with urllib.request.urlopen(request,timeout=120) as response:result=json.load(response)
    # Preserve successful provider response before trying a potentially failing download.
    return result

def download(url):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme=='http' and parsed.hostname and parsed.hostname.endswith('.aliyuncs.com'):
        url=urllib.parse.urlunsplit(parsed._replace(scheme='https'))
        parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='https' or not parsed.hostname:raise ValueError('Expected HTTPS provider audio URL')
    with urllib.request.urlopen(url,timeout=90) as response:return response.read()

def probe(path):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,sample_rate,channels','-of','json',str(path)]))
    duration=float(data['format']['duration'])
    if not 0<duration<3600:raise ValueError('Invalid audio duration')
    return {'duration_seconds':duration,'streams':data.get('streams',[])}

def synthesize(text, voice, model, instructions, output, provider=cloud, downloader=download, prober=probe):
    if not isinstance(text,str) or not text.strip() or len(text)>500:raise ValueError('Expected text of 1..500 characters')
    if not isinstance(voice,str) or not voice.strip() or len(voice)>150:raise ValueError('Expected explicit voice ID')
    if not isinstance(model,str) or not model.startswith('qwen3-tts-instruct-flash'):raise ValueError('Expected Qwen3 TTS Instruct Flash model; verify voice compatibility')
    if not isinstance(instructions,str) or not instructions.strip() or len(instructions)>1000:raise ValueError('Expected instructions of 1..1000 characters')
    body={'model':model,'input':{'text':text,'voice':voice,'language_type':'Chinese','instructions':instructions,'optimize_instructions':True}}
    output=Path(output)
    # A fresh output directory is mandatory, even if prior state is failed/unknown.
    output.mkdir(parents=True,exist_ok=False)
    record=output/'receipt.json';entry={'state':'submitted','request':body};save(record,entry)
    try:
        result=provider(body)
        entry.update(request_id=result.get('request_id'),usage=result.get('usage'))
        audio_result=result.get('output',{}).get('audio',{})
        url=audio_result.get('url')
        if not url:
            entry.update(state='failed',provider_code=result.get('code'),note='Provider returned no audio URL; no automatic retry')
            save(record,entry);raise ValueError('Provider returned no audio URL')
        # Persist the accepted job URL before downloading so a failed download need not pay again.
        save_private(output/'download-private.json',{'request_id':result.get('request_id'),'audio_url':url})
        entry.update(state='audio_ready');save(record,entry)
        audio=downloader(url)
        if not audio:raise ValueError('Empty audio')
        target=output/'audio.wav';target.write_bytes(audio)
        entry.update(raw_sha256=hashlib.sha256(audio).hexdigest(),bytes=len(audio),file=target.name)
        measurements=prober(target)
        entry.update(state='success',**measurements,listening_status='not_performed',post_speed_processing=False)
        save(record,entry)
        return entry
    except Exception as error:
        if entry.get('state')!='failed':entry.update(state='unknown',error_type=type(error).__name__,note='No automatic retry; provider may have accepted or charged the request')
        save(record,entry)
        raise RuntimeError('No verified output; inspect receipt before creating a new explicit revision') from None

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--text-file',type=Path,required=True);p.add_argument('--voice',required=True);p.add_argument('--model',required=True);p.add_argument('--instructions-file',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
    if not os.environ.get('DASHSCOPE_API_KEY'):p.error('DASHSCOPE_API_KEY must be injected in child environment')
    row=synthesize(args.text_file.read_text().strip(),args.voice,args.model,args.instructions_file.read_text().strip(),args.output_dir)
    print(json.dumps({'state':row['state'],'duration_seconds':row['duration_seconds'],'receipt':str(args.output_dir/'receipt.json')}))
