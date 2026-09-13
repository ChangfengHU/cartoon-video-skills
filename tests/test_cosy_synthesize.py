import importlib.util,io,json,tempfile,unittest,wave
from pathlib import Path
s=importlib.util.spec_from_file_location('cosy',Path(__file__).resolve().parents[1]/'skills/voice-production/scripts/cosy_synthesize.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class CosyTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=Path(self.temp.name);self.voice={'model':'cosyvoice-v3.5-plus','voice_id':'test-authorized'};self.rows=[{'index':0,'text':'下班了。','instruction':'轻松收尾'}];self.calls=[]
 def provider(self,body):
  self.calls.append(body);b=io.BytesIO()
  with wave.open(b,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\0'*48000)
  return b.getvalue(),'request-test'
 def test_instruction_duration_and_idempotence(self):
  r=m.synthesize(self.voice,self.rows,self.p,self.provider);self.assertEqual(r[0]['duration_seconds'],1);self.assertEqual(self.calls[0]['input']['instruction'],'轻松收尾');m.synthesize(self.voice,self.rows,self.p,self.provider);self.assertEqual(len(self.calls),1)
 def test_unknown_never_retried(self):
  def fail(body):self.calls.append(body);raise TimeoutError('private')
  with self.assertRaises(RuntimeError):m.synthesize(self.voice,self.rows,self.p,fail)
  with self.assertRaises(ValueError):m.synthesize(self.voice,self.rows,self.p,self.provider)
  self.assertEqual(len(self.calls),1);self.assertNotIn('private',(self.p/'voice-00.json').read_text())
 def test_changed_source_and_duplicates_rejected(self):
  m.synthesize(self.voice,self.rows,self.p,self.provider)
  with self.assertRaises(ValueError):m.synthesize(self.voice,[{**self.rows[0],'text':'改词'}],self.p,self.provider)
  with self.assertRaises(ValueError):m.synthesize(self.voice,self.rows*2,self.p,self.provider)
  self.assertEqual(len(self.calls),1)
if __name__=='__main__':unittest.main()
