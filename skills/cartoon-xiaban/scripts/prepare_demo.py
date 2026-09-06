#!/usr/bin/env python3
"""Prepare the fixed six-scene demo using explicit, caller-owned runtime assets."""
import argparse
import json
import math
from pathlib import Path
import shutil
from prepare_project import validate

ROOT = Path(__file__).resolve().parents[1]
SFX = ('notification', 'whoosh-short', 'pop', 'key-press', 'click-soft')

def prepare(output, timing_path, voice, font, gsap, sfx_dir=None):
    validate(ROOT)
    paths = [timing_path, voice, font, gsap]
    if not all(p.is_file() for p in paths):
        raise ValueError('Every input asset must be an existing file.')
    timing = json.loads(timing_path.read_text())
    lines = json.loads((ROOT/'assets/examples/script.json').read_text())['lines']
    records = timing.get('records', [])
    if len(records) != len(lines):
        raise ValueError('The reference implementation needs the ten fixed demo lines.')
    duration = timing.get('duration', 0)
    if not isinstance(duration, (float, int)) or not math.isfinite(duration) or not 0 < duration <= 60:
        raise ValueError('Invalid duration; do not accelerate speech to fit.')
    cleaned = []
    for i, (r, line) in enumerate(zip(records, lines)):
        if r['text'] != line['text']:
            raise ValueError(f'Demo text differs at line {i}; new stories need new storyboards.')
        nums = [r[k] for k in ('start', 'end', 'duration')]
        if not all(isinstance(n, (float, int)) and math.isfinite(n) for n in nums):
            raise ValueError('Non-finite timing')
        if r['start'] < 0 or r['end'] <= r['start'] or r['end'] > duration or (i and r['start'] < records[i-1]['end']):
            raise ValueError('Overlapping or out-of-bounds line windows')
        cleaned.append({k:r[k] for k in ('id','text','start','end','duration','pauseAfter') if k in r})
    sound_meta = {}
    if sfx_dir:
        manifest = json.loads((sfx_dir/'manifest.json').read_text())
        for name in SFX:
            m = manifest[name]
            f = m['file']
            if Path(f).name != f or not (sfx_dir/f).is_file():
                raise ValueError(f'Unsafe or missing SFX: {name}')
            sound_meta[name] = m
    output.mkdir(parents=True, exist_ok=False)
    for name in ('assets/audio','assets/images','assets/fonts','assets/sfx','compositions','renders','evidence'):
        (output/name).mkdir(parents=True, exist_ok=True)
    for source, relative in (
        (voice,'assets/audio/voice.wav'),(font,'assets/fonts/Chinese.ttf'),(gsap,'assets/gsap.min.js'),
        (ROOT/'assets/identity/acting-sheet-v2.png','assets/images/acting-sheet-v2.png')):
        shutil.copy2(source, output/relative)
    public_timing = {'duration':duration,'records':cleaned,'captions':timing.get('captions',[]),
        'captionTiming':timing.get('captionTiming','caller supplied; alignment not independently verified'),
        'voiceIdentity':'caller-supplied authorized narration; no identity data bundled'}
    (output/'assets/audio/timing.json').write_text(json.dumps(public_timing, ensure_ascii=False, indent=2)+'\n')
    if sfx_dir:
        for m in sound_meta.values():
            shutil.copy2(sfx_dir/m['file'], output/'assets/sfx'/m['file'])
        (output/'assets/sfx/manifest.json').write_text(json.dumps(sound_meta,ensure_ascii=False,indent=2)+'\n')
    package = {'name':'cartoon-xiaban-demo','private':True,'type':'module','scripts':{
        'check':'npx --yes hyperframes@0.8.30 check',
        'render':'npx --yes hyperframes@0.8.30 render',
        'preview':'npx --yes hyperframes@0.8.30 preview --background'}}
    (output/'package.json').write_text(json.dumps(package,indent=2)+'\n')
    return {'prepared':str(output),'duration':duration,'sfx':list(sound_meta),'audio_synthesized':False}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ('output','timing','voice','font','gsap'):
        p.add_argument('--'+flag, type=Path, required=True)
    p.add_argument('--sfx-dir',type=Path)
    a = p.parse_args()
    print(json.dumps(prepare(a.output,a.timing,a.voice,a.font,a.gsap,a.sfx_dir),ensure_ascii=False))
