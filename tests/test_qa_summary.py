import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('qa',Path(__file__).resolve().parents[1]/'skills/cartoon-video-studio/scripts/qa_summary.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class QA(unittest.TestCase):
 def test_technical_alone_not_quality_pass(self):
  x=m.summarize({'checks':[{'dimension':'technical','status':'pass','evidence':'ffprobe.json','finding':'dimensions match'}]});self.assertTrue(x['needs_review']);self.assertEqual(x['dimensions']['visual'],'pending')
 def test_no_evidence_cannot_pass(self):
  with self.assertRaises(ValueError):m.summarize({'checks':[{'dimension':'audio','status':'pass','finding':'good'}]})
 def test_fail_has_priority(self):
  x=m.summarize({'checks':[{'dimension':'visual','status':'fail','evidence':'frame.png','finding':'cropped text'}]});self.assertEqual(x['dimensions']['visual'],'fail')
