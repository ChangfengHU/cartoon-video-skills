from pathlib import Path
import unittest,tempfile,json,hashlib,importlib.util
root=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('register',root/'skills/cartoon-video-studio/scripts/register_character.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class RegistryTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.studio=self.root/'skills/cartoon-video-studio';self.studio.mkdir(parents=True);(self.studio/'characters.json').write_text('{"characters":[]}');self.src=self.root/'new';self.src.mkdir();(self.src/'SKILL.md').write_text('---\nname: cartoon-new\ndescription: test character\n---\n');(self.src/'reference.png').write_bytes(b'test-reference');self.brand={'brand_id':'new','assets':[{'path':'reference.png','sha256':hashlib.sha256(b'test-reference').hexdigest()}]};self.save()
 def save(self):(self.src/'brand.json').write_text(json.dumps(self.brand))
 def tearDown(self):self.tmp.cleanup()
 def test_add_then_preserve_on_collision(self):
  mod.register(self.studio,self.src,'new','新角色','brand.json');before=(self.studio/'characters.json').read_bytes()
  with self.assertRaises(ValueError):mod.register(self.studio,self.src,'other','冲突','brand.json')
  self.assertEqual(before,(self.studio/'characters.json').read_bytes());self.assertTrue((self.root/'skills/cartoon-new/reference.png').exists())
 def test_bad_hash_does_not_register(self):
  self.brand['assets'][0]['sha256']='wrong';self.save()
  with self.assertRaises(ValueError):mod.register(self.studio,self.src,'new','新','brand.json')
  self.assertEqual(json.loads((self.studio/'characters.json').read_text()),{'characters':[]})
 def test_path_escape_rejected(self):
  self.brand['assets'][0]['path']='../outside';self.save()
  with self.assertRaises(ValueError):mod.register(self.studio,self.src,'new','新','brand.json')
if __name__=='__main__':unittest.main()
