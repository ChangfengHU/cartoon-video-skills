"""Explicit-directory install; refuse to replace modified files. No credential access."""
import argparse,shutil
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1]
def files(root):return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
def install(target,uninstall=False):
 target=Path(target).resolve()/SOURCE.name
 if target==SOURCE:raise ValueError('target is source')
 if target.exists():
  if files(target)!=files(SOURCE):raise ValueError('existing skill differs; preserved')
  if uninstall:shutil.rmtree(target);return 'removed'
  return 'unchanged'
 if uninstall:return 'absent'
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(SOURCE,target,ignore=shutil.ignore_patterns('__pycache__'));return 'installed'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--target-dir',required=True);p.add_argument('--uninstall',action='store_true');a=p.parse_args();print(install(a.target_dir,a.uninstall))
