import importlib.util
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('release_check',Path(__file__).parents[1]/'skills/cartoon-video-studio/scripts/release_check.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ReleaseCheck(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  for name in ['audio.wav','reference.wav','review.txt']:(self.root/name).write_bytes(name.encode())
  def asset(name):return {'path':name,'sha256':m.digest(self.root/name)}
  self.report={'profile':'audio','target':{**asset('audio.wav'),'duration_seconds':10},'reference':{**asset('reference.wav'),'required':True,'source':'test fixture','selection_basis':'test only'},'checks':[]}
  for dim in m.PROFILES['audio']:
   self.report['checks'].append({'dimension':dim,'status':'pass','target_sha256':self.report['target']['sha256'],'reference_sha256':self.report['reference']['sha256'],'finding':'fixture observation','reviewer':'test fixture','method':'direct_review','evidence':[asset('review.txt')],'ranges':[[0,10]],'coverage':'whole'})
 def run_report(self):return m.evaluate(self.report,self.root)
 def test_complete_is_not_quality_approval(self):
  r=self.run_report();self.assertEqual(r['status'],'evidence_complete');self.assertNotIn('approved',r)
 def test_pending_performance_blocks(self):
  next(c for c in self.report['checks'] if c['dimension']=='performance')['status']='pending';self.assertTrue(self.run_report()['issues'])
 def test_asr_cannot_clear_performance(self):
  next(c for c in self.report['checks'] if c['dimension']=='performance')['method']='automated';self.assertTrue(self.run_report()['issues'])
 def test_changed_audio_invalidates(self):
  (self.root/'audio.wav').write_bytes(b'new revision');self.assertTrue(self.run_report()['issues'])
 def test_stale_target(self):
  self.report['checks'][0]['target_sha256']='old';self.assertTrue(self.run_report()['issues'])
 def test_missing_evidence(self):
  (self.root/'review.txt').unlink();self.assertTrue(self.run_report()['issues'])
 def test_whole_claim_with_gap(self):
  self.report['checks'][0]['ranges']=[[0,3],[5,10]];self.assertTrue(self.run_report()['issues'])
 def test_sampled_is_reportable(self):
  self.report['checks'][0].update(ranges=[[0,3]],coverage='sampled');self.assertFalse(self.run_report()['issues'])
 def test_cannot_exempt_reference(self):
  next(c for c in self.report['checks'] if c['dimension']=='reference').update(status='not_applicable',reason='skip');self.assertTrue(self.run_report()['issues'])
 def test_missing_video_dimensions(self):
  self.report['profile']='video';self.assertTrue(self.run_report()['issues'])
 def test_bad_range(self):
  self.report['checks'][0]['ranges']=[[0,float('nan')]];self.assertTrue(self.run_report()['issues'])
 def test_model_assistance_not_direct_review(self):
  next(c for c in self.report['checks'] if c['dimension']=='performance')['method']='model_assisted';self.assertTrue(self.run_report()['issues'])
if __name__=='__main__':unittest.main()
