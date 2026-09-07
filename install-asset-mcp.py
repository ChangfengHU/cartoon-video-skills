#!/usr/bin/env python3
"""Add only the scoped asset MCP to Codex. Does not configure private credentials."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--skill-dir',type=Path,default=Path.home()/'.codex/skills/cartoon-xiaban')
p.add_argument('--codex',default='codex')
a = p.parse_args()
client = (a.skill_dir/'scripts/asset_mcp.py').resolve(strict=True)
directory = Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
config = directory/'config.toml'
existing = subprocess.run([a.codex,'mcp','get','vyibc-cartoon-assets','--json'],capture_output=True,text=True)
if existing.returncode == 0:
    data = json.loads(existing.stdout)
    transport = data.get('transport',{})
    if transport.get('args') == [str(client),'stdio']:
        print('Existing scoped asset MCP matches; left unchanged.')
    else:
        raise SystemExit('A differently configured vyibc-cartoon-assets already exists; preserve it and resolve explicitly.')
else:
    if config.exists():
        if config.is_symlink(): raise SystemExit('Refuse to modify symlink config')
        backup = directory/'backups'/('asset-mcp-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.toml')
        backup.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(config,backup); backup.chmod(0o600)
    subprocess.run([a.codex,'mcp','add','vyibc-cartoon-assets','--','python3',str(client),'stdio'],check=True)
print('Private authorization: python3 '+str(client)+' configure')
print('Start a new Codex task to load the new MCP. Existing sessions are not modified.')
