#!/usr/bin/env python3
"""Mechanically mirror the canonical public Skill into the distributable Plugin."""
import hashlib
from pathlib import Path
import shutil
root = Path(__file__).resolve().parents[1]
source = root/'skills/cartoon-xiaban'
dest = root/'plugins/cartoon-video-studio/skills/cartoon-xiaban'
for p in sorted(source.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc':
        output = dest/p.relative_to(source)
        output.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,output)
        assert hashlib.sha256(p.read_bytes()).digest() == hashlib.sha256(output.read_bytes()).digest()
print('Plugin Skill mirror verified.')
