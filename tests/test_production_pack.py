import unittest,tempfile,json,hashlib,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('pack',Path(__file__).resolve().parents[1]/'skills/studio-character-workflow/scripts/production_pack.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class PackTest(unittest.TestCase):
 def test_actual_evidence_and_stale_asset(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'a.png').write_bytes(b'evidence');f={'path':'a.png','sha256':hashlib.sha256(b'evidence').hexdigest()}
   data={'schema_version':1,'character':{'id':'x','display_name':'Original','naming_basis':'fictional'},'scenes':[{'id':'room','location':'home','time_of_day':'night','style_reference':'approved','actor_placement':{'foot_y':.8},'image':f,'composite_sample':f}],'scene_requirements':[{'scene_id':'room'}],'actions':[{'frames':[{'image':f,'duration_ms':100,'foot_anchor':[.5,.9]}]*3,'continuous_sample':f}]}
   self.assertEqual(m.check(data,p),[])
   (p/'a.png').write_bytes(b'changed');self.assertTrue(any('stale hash' in i for i in m.check(data,p)))
 def test_missing_scenes_do_not_pass(self):
  self.assertIn('scenes required',m.check({'schema_version':1},'.'))
