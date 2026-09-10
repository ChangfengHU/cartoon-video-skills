#!/usr/bin/env python3
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1];dest=root/'plugins/cartoon-video-studio/skills'
for source in sorted((root/'skills').iterdir()):
 if source.is_dir() and (source/'SKILL.md').is_file():
  output=dest/source.name
  if output.exists():shutil.rmtree(output)
  shutil.copytree(source,output,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
print('Canonical skills mirrored.')
