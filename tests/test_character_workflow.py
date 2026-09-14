import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'skills/studio-character-workflow/scripts/workflow.py'
s=importlib.util.spec_from_file_location('workflow',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class WorkflowTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
  def save(n,v):
   p=self.root/n;p.write_text(json.dumps(v));return {'path':n,'sha256':m.digest(p)}
  self.save=save;generic=save('evidence.json',{'actual':'test fixture, not real QA'})
  self.data={'schema_version':1,'voice_policy':save('policy.json',{'excluded_voice_ids':['excluded-voice']}),'references':[{'id':'ref','source_url':'https://example.com/post','platform':'user','used_for_generation':True,'usage_status':'recorded_at_generation','request_receipt':generic,'image':generic,'preview_asset_id':'private-id'}],'characters':[{'id':'role','profile':save('profile.json',{'id':'role','positioning':'test','personality':['calm'],'suitable_scenes':['test'],'identity_locks':['hair']}),'reference_ids':['ref'],'assets':[generic],'voice':{'provider':'provider','model':'model','voice_id':'permitted','preview':generic,'selection_reason':'fixture'},'visual_review':generic}],'example_video':None,'delivery':{'receipt':generic,'browser_evidence':[generic]}}
 def tearDown(self):self.t.cleanup()
 def test_complete_is_not_artistic_approval(self):self.assertEqual(m.check(self.data,self.root),[])
 def test_policy_cannot_be_bypassed_with_case(self):
  self.data['characters'][0]['voice']['voice_id']=' EXCLUDED-VOICE ';self.assertTrue(any('excluded' in s for s in m.check(self.data,self.root)))
 def test_retrospective_inputs_stay_pending(self):
  self.data['references'][0]['usage_status']='retrospective';self.assertTrue(any('retrospectively' in s for s in m.check(self.data,self.root)))
 def test_changed_evidence_invalidates(self):
  (self.root/'evidence.json').write_text('changed');self.assertTrue(any('stale' in s for s in m.check(self.data,self.root)))
 def test_outside_reference_refused(self):
  self.data['references'][0]['image']={'path':'../secret','sha256':'x'};self.assertTrue(any('outside' in s for s in m.check(self.data,self.root)))
 def test_atomic_idempotent_plan(self):
  brief=self.root/'brief.json';brief.write_text('{"example_video":false}');m.init(self.root,brief);before=(self.root/'PRODUCTION.json').read_bytes();m.init(self.root,brief);self.assertEqual(before,(self.root/'PRODUCTION.json').read_bytes());brief.write_text('{"example_video":true}')
  with self.assertRaises(ValueError):m.init(self.root,brief)
  self.assertEqual(before,(self.root/'PRODUCTION.json').read_bytes())
if __name__=='__main__':unittest.main()
