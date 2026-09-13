import tempfile,unittest
from pathlib import Path
from install import install
class InstallTests(unittest.TestCase):
 def test_idempotence_preservation_and_uninstall(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(install(d),'installed');self.assertEqual(install(d),'unchanged');p=Path(d)/'voice-production/SKILL.md';original=p.read_bytes();p.write_text('user edit')
   with self.assertRaises(ValueError):install(d)
   self.assertEqual(p.read_text(),'user edit');p.write_bytes(original);self.assertEqual(install(d,True),'removed');self.assertEqual(install(d,True),'absent')
if __name__=='__main__':unittest.main()
