#!/usr/bin/env python3
"""Reuse an authorized Cosy voice; no enrollment and no automatic paid retries."""
from pathlib import Path
import argparse, hashlib, io, json, os, urllib.request, urllib.parse, wave

def save(path, value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2));temp.replace(path)

def secure_audio_url(url):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme=='http' and parsed.hostname and parsed.hostname.endswith('.aliyuncs.com'):
        return urllib.parse.urlunsplit(parsed._replace(scheme='https'))
    if parsed.scheme!='https':raise ValueError('Unsupported audio URL scheme')
    return url

def cloud(body):
    key=os.environ.get('DASHSCOPE_API_KEY')
    if not key: raise ValueError('Missing DASHSCOPE_API_KEY in child environment')
    headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}
    if os.environ.get('DASHSCOPE_WORKSPACE_ID'): headers['X-DashScope-WorkSpace']=os.environ['DASHSCOPE_WORKSPACE_ID']
    req=urllib.request.Request('https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer',data=json.dumps(body).encode(),headers=headers)
    with urllib.request.urlopen(req,timeout=120) as response: result=json.load(response)
    url=secure_audio_url(result['output']['audio']['url'])
    with urllib.request.urlopen(url,timeout=90) as response: audio=response.read()
    return audio,result.get('request_id')

def synthesize(voice, segments, output, provider=cloud):
    if voice.get('model')!='cosyvoice-v3.5-plus' or not isinstance(voice.get('voice_id'),str) or not voice['voice_id'].strip(): raise ValueError('Expected authorized Cosy v3.5-plus binding')
    if not isinstance(segments,list) or not 1<=len(segments)<=30:raise ValueError('Expected 1..30 segments')
    ids=set();plans=[]
    for row in segments:
        i=row.get('index');text=row.get('text');direction=row.get('instruction','')
        if type(i)!=int or not 0<=i<=999 or i in ids:raise ValueError('Indices must be unique integers 0..999')
        if not isinstance(text,str) or not text.strip() or len(text)>500:raise ValueError('Expected nonempty text up to500 characters')
        if not isinstance(direction,str) or len(direction)>500:raise ValueError('Invalid instruction')
        ids.add(i);body={'model':voice['model'],'input':{'text':text,'voice':voice['voice_id'],'format':'wav','sample_rate':24000}}
        if direction:body['input']['instruction']=direction
        plans.append((i,body))
    output=Path(output);output.mkdir(parents=True,exist_ok=True);results=[]
    # Check every previous record before initiating any new paid request.
    for i,body in plans:
        record=output/f'voice-{i:02}.json';audio=output/f'voice-{i:02}.wav'
        if record.exists():
            old=json.loads(record.read_text())
            if old.get('state')!='success' or old.get('request')!=body or not audio.exists() or hashlib.sha256(audio.read_bytes()).hexdigest()!=old.get('sha256'):raise ValueError('Prior result differs or is uncertain; inspect before creating an explicit new revision')
        elif audio.exists():raise ValueError('Untracked audio exists; do not overwrite')
    for i,body in plans:
        record=output/f'voice-{i:02}.json';audio=output/f'voice-{i:02}.wav'
        if record.exists():results.append(json.loads(record.read_text()));continue
        entry={'index':i,'state':'submitted','request':body};save(record,entry)
        try:
            data,request_id=provider(body);entry['request_id']=request_id
            provider_sha256=hashlib.sha256(data).hexdigest()
            with wave.open(io.BytesIO(data),'rb') as w:
                rate=w.getframerate();channels=w.getnchannels();width=w.getsampwidth();declared=w.getnframes()
                if w.getcomptype()!='NONE':raise ValueError('Expected PCM WAV')
                pcm=w.readframes(declared)
            if not pcm or len(pcm)%(channels*width):raise ValueError('Incomplete PCM audio')
            frames=len(pcm)//(channels*width);duration=frames/rate
            # Streaming WAV can declare 0xffffffff: measure actual bytes and freeze a valid header.
            normalized=io.BytesIO()
            with wave.open(normalized,'wb') as w:
                w.setnchannels(channels);w.setsampwidth(width);w.setframerate(rate);w.writeframes(pcm)
            data=normalized.getvalue();entry.update(provider_sha256=provider_sha256,streaming_header_normalized=declared!=frames)
            audio.write_bytes(data);entry.update(state='success',file=audio.name,sha256=hashlib.sha256(data).hexdigest(),duration_seconds=duration,sample_rate=rate,channels=channels);save(record,entry);results.append(entry)
        except Exception as error:
            entry.update(state='unknown',error_type=type(error).__name__,note='No automatic retry; provider may have accepted or charged the request');save(record,entry);raise RuntimeError('Voice request did not produce a verified WAV; inspect saved state') from None
    save(output/'manifest.json',{'provider':'dashscope','voice_id':voice['voice_id'],'model':voice['model'],'segments':results,'subjective_listening':'not performed','post_speed_processing':False})
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--voice-file',type=Path,required=True);p.add_argument('--segments',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
    if not os.environ.get('DASHSCOPE_API_KEY'):p.error('DASHSCOPE_API_KEY must be injected in the child environment')
    rows=synthesize(json.loads(args.voice_file.read_text()),json.loads(args.segments.read_text()),args.output_dir)
    print(json.dumps({'segments':len(rows),'duration_seconds':sum(x['duration_seconds'] for x in rows),'manifest':str(args.output_dir/'manifest.json')}))
