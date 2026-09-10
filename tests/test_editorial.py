import copy, hashlib, importlib.util, tempfile, unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'skills/cartoon-video-studio/scripts/editorial_check.py'
s=importlib.util.spec_from_file_location('editorial',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class Editorial(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.data={'schema_version':1,'topic':'城市夜间公交','style':{'name':'实地解释','reason':'路线变化适合地图展示'},'sources':[{'id':'notice','locator':'notice.txt','scope':'本次公告，未调查全市乘客'}],'findings':[{'id':'route','claim':'末班延后','kind':'fact','source_ids':['notice'],'decision':'include','reason':'影响夜归观众'},{'id':'color','claim':'站牌颜色改变','kind':'observation','source_ids':['notice'],'decision':'omit','reason':'与本片出行问题关系较弱'}],'beats':[{'id':'explain','finding_ids':['route'],'message':'何时仍能坐车','visual':'公告时间与路线图','audio':'解释变化与适用日期','evidence_role':'evidence'}]}
 def tearDown(self): self.tmp.cleanup()
 def check(self,stage='plan'): return m.validate(self.data,self.root,stage)
 def final(self):
  (self.root/'film.mp4').write_bytes(b'test artifact');(self.root/'observation.txt').write_text('test observation')
  h=hashlib.sha256(b'test artifact').hexdigest();self.data['artifact']={'path':'film.mp4','sha256':h,'duration':10}
  self.data['reviews']=[{'beat_id':'explain','dimension':d,'status':'pass','range':[0,10],'artifact_sha256':h,'note':'test observation','evidence':'observation.txt'} for d in ['editorial','visual','audio']]
 def test_other_topic_and_justified_omission(self): self.assertFalse(self.check()['errors'])
 def test_selected_finding_cannot_silently_disappear(self):
  self.data['findings'][1]['decision']='include';self.assertIn('color:not_in_beats',self.check()['errors'])
 def test_missing_source_and_empty_explanation(self):
  self.data['findings'][0]['source_ids']=['invented'];self.data['beats'][0]['message']='';self.assertGreaterEqual(len(self.check()['errors']),2)
 def test_fiction_does_not_require_web_sources(self):
  self.data['sources']=[]
  for f in self.data['findings']:f.update(kind='hypothetical',source_ids=[])
  self.assertFalse(self.check()['errors'])
 def test_final_missing_listening_stays_pending(self):
  self.final();self.data['reviews'].pop();self.assertIn('explain:audio',self.check('final')['pending'])
 def test_technical_artifact_cannot_approve_quality(self):
  self.final();r=self.check('final');self.assertEqual(r['record_status'],'reported_pass');self.assertFalse(r['quality_approved'])
 def test_render_change_invalidates_review(self):
  self.final();(self.root/'film.mp4').write_bytes(b'new');r=self.check('final');self.assertIn('artifact_hash_mismatch',r['errors']);self.assertIn('review:stale:explain',r['errors'])
 def test_range_and_missing_evidence(self):
  self.final();self.data['reviews'][0].update(range=[9,11],evidence='../outside');self.assertGreaterEqual(len(self.check('final')['errors']),2)
 def test_duplicate_review_cannot_hide_failure(self):
  self.final();r=copy.deepcopy(self.data['reviews'][0]);r['status']='fail';self.data['reviews'].append(r);self.assertTrue(self.check('final')['errors'])
 def test_malformed_inputs(self):
  for key,value in [('sources',None),('beats',[None]),('style',None),('findings',None)]:
   d=copy.deepcopy(self.data);d[key]=value;self.assertTrue(m.validate(d,self.root)['errors'])
class EditorialV2(Editorial):
 def setUp(self):
  super().setUp();self.data['schema_version']=2
  self.data['intent']={'audience':'夜班乘客','assumed_knowledge':'知道旧末班时间','promise':'理解哪些晚班现在可以坐公交'}
  self.data['findings'][0]['contribution']={'role':'focus','known':'旧时间','adds':'公告新增覆盖时段'}
  self.data['beats'][0]['loss_if_removed']='不知道新增班次适用范围'
 def test_missing_promise(self):
  self.data['intent'].pop('promise');self.assertIn('intent_required',self.check()['errors'])
 def test_context_cannot_be_only_focus(self):
  self.data['findings'][0]['contribution']['role']='context';self.assertIn('focus_required',self.check()['errors'])
 def test_comparison_needs_evidence(self):
  self.data['findings'][0]['comparison']={'baseline':'旧公告','source_ids':[]}
  self.assertIn('route:comparison_evidence_required',self.check()['errors'])
 def test_no_comparison_required(self):self.assertFalse(self.check()['errors'])
 def test_removal_review(self):
  self.data['beats'][0].pop('loss_if_removed');self.assertIn('explain:removal_review_required',self.check()['errors'])
if __name__=='__main__': unittest.main()
