import importlib.util,unittest,tempfile,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'skills/cartoon-video-studio/scripts/production_state.py'
s=importlib.util.spec_from_file_location('production',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Production(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'line.txt').write_text('hello');(self.root/'out.wav').write_bytes(b'audio')
 def tearDown(self):self.tmp.cleanup()
 def call(self,a,k=None,**kw):return m.operate(self.root,a,k,**kw)
 def start(self):self.call('add','voice',inputs=['line.txt']);return self.call('begin','voice')['run_id']
 def done(self):run=self.start();self.call('finish','voice',run_id=run,outputs=['out.wav']);return run
 def test_changed_input_invalidates_dependents(self):
  self.done();self.call('add','scene',deps=['voice']);run=self.call('begin','scene')['run_id'];self.call('finish','scene',run_id=run,outputs=['out.wav']);self.assertTrue(self.call('status')['scene']['reusable']);(self.root/'line.txt').write_text('changed');self.assertFalse(self.call('status')['scene']['reusable'])
 def test_unknown_remote_prevents_duplicate(self):
  run=self.start();self.call('remote','voice',run_id=run,provider='test',job='job1');self.call('fail','voice',run_id=run,reason='timeout')
  with self.assertRaises(ValueError):self.call('begin','voice')
  self.call('remote','voice',run_id=run,provider='test',job='job1',remote_status='failed');self.assertNotEqual(self.call('begin','voice')['run_id'],run)
 def test_recovered_success_finishes_original_attempt(self):
  run=self.start();self.call('remote','voice',run_id=run,provider='test',job='job1');self.call('fail','voice',run_id=run,reason='network timeout');self.call('remote','voice',run_id=run,provider='test',job='job1',remote_status='succeeded');self.call('finish','voice',run_id=run,outputs=['out.wav']);self.assertTrue(self.call('status')['voice']['reusable'])
 def test_wrong_attempt_and_escape_do_not_finish(self):
  run=self.start()
  with self.assertRaises(ValueError):self.call('finish','voice',run_id='wrong',outputs=['out.wav'])
  with self.assertRaises(ValueError):self.call('finish','voice',run_id=run,outputs=['../outside'])
  self.assertEqual(self.call('status')['voice']['status'],'running')
 def test_dependency_output_change_blocks_completion(self):
  self.done();self.call('add','scene',deps=['voice']);run=self.call('begin','scene')['run_id'];(self.root/'out.wav').write_bytes(b'changed')
  with self.assertRaises(ValueError):self.call('finish','scene',run_id=run,outputs=['out.wav'])
 def test_invalidate_preserves_outputs_and_history(self):
  self.done();self.call('invalidate','voice');self.assertTrue((self.root/'out.wav').exists());self.assertEqual(self.call('status')['voice']['status'],'stale');self.assertGreater(len(json.loads((self.root/'PRODUCTION.json').read_text())['history']),2)
if __name__=='__main__':unittest.main()
