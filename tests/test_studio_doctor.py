import importlib.util
from pathlib import Path
import unittest

PATH=Path(__file__).parents[1]/'skills/cartoon-video-studio/scripts/doctor.py'
SPEC=importlib.util.spec_from_file_location('studio_doctor',PATH)
DOCTOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(DOCTOR)

class StudioDoctorTest(unittest.TestCase):
 def test_version_parser(self):
  self.assertEqual(DOCTOR.major('v22.18.0'),22)
  self.assertEqual(DOCTOR.major('Node.js 24.1.0'),24)
  self.assertIsNone(DOCTOR.major('unknown'))
 def test_missing_executable_is_structured(self):
  result=DOCTOR.executable('cartoon-video-studio-test-not-a-command',['--version'])
  self.assertEqual(result,{'status':'missing','path':None})

if __name__=='__main__':unittest.main()
