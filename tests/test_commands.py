import importlib.util, tempfile, unittest, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
build=load('command_build',ROOT/'scripts/build-commands.py')
installer=load('command_install',ROOT/'plugins/cartoon-video-studio/command-support/install.py')
class Commands(unittest.TestCase):
 def test_conflict_preflight_and_idempotence(self):
  with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
   p=Path(tmp)/'prompts';installer.install('pi',p);self.assertFalse(p.exists())
   p.mkdir();(p/'studio-new.md').write_text('user custom command')
   with self.assertRaises(FileExistsError):installer.install('pi',p,True)
   self.assertEqual(len(list(p.iterdir())),1)
   (p/'studio-new.md').unlink();installer.install('pi',p,True)
   before={f.name:f.read_bytes() for f in p.iterdir()};installer.install('pi',p,True)
   self.assertEqual(before,{f.name:f.read_bytes() for f in p.iterdir()})
 def test_symlink_rejected(self):
  with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
   p=Path(tmp);outside=p/'untouched';outside.write_text('owned');dest=p/'prompts';dest.mkdir();(dest/'studio.md').symlink_to(outside)
   with self.assertRaises(FileExistsError):installer.install('pi',dest,True)
   self.assertEqual(outside.read_text(),'owned')
 def test_all_adapters_and_native_links(self):
  for p,expected in build.outputs().items():
   self.assertEqual(p.read_text(),expected)
  rows=build.catalog();self.assertEqual(len({r['name'] for r in rows}),len(rows))
  for row in rows:
   native=ROOT/'skills'/row['name']/'SKILL.md';self.assertTrue(native.exists())
   for client in ('pi','claude','codex-legacy'):
    self.assertTrue((build.PACKAGE/'command-support'/client/(row['name']+'.md')).exists())
 def test_help_does_not_embed_production_contract(self):
  helptext=(build.PACKAGE/'command-support/pi/studio-help.md').read_text()
  self.assertNotIn('## 主题缺省',helptext)
  self.assertEqual(next(r for r in build.catalog() if r['name']=='studio-help')['defaults'],'help')
if __name__=='__main__':unittest.main()
