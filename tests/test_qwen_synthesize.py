import importlib.util,json,tempfile,unittest,io,os
from pathlib import Path
from unittest.mock import patch
SCRIPT=Path(__file__).resolve().parents[1]/'skills/voice-production/scripts/qwen_synthesize.py'
spec=importlib.util.spec_from_file_location('qwen_synthesize',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Tests(unittest.TestCase):
 def run_synthesis(self,out,provider=None,downloader=None):
  return m.synthesize('测试台词','TestVoice','qwen3-tts-instruct-flash-2026-01-26','自然清晰',out,provider or (lambda b:{'request_id':'r1','output':{'audio':{'url':'https://example.org/audio?signature=private'}}}),downloader or (lambda u:b'PCM-test'),lambda p:{'duration_seconds':1.25,'streams':[]})
 def test_success_receipt_and_no_signed_url(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'new';r=self.run_synthesis(p);self.assertEqual(r['state'],'success');self.assertEqual(r['duration_seconds'],1.25);self.assertNotIn('signature',(p/'receipt.json').read_text());self.assertEqual((p/'audio.wav').read_bytes(),b'PCM-test');self.assertEqual((p/'download-private.json').stat().st_mode & 0o777,0o600)
 def test_existing_directory_rejected_before_paid_call(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(FileExistsError):self.run_synthesis(d,provider=lambda b:self.fail('must not call provider'))
 def test_download_failure_preserves_request_id_and_blocks_retry(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'new'
   def fail(u):raise TimeoutError('signed URL secret should not be logged')
   with self.assertRaises(RuntimeError):self.run_synthesis(p,downloader=fail)
   r=json.loads((p/'receipt.json').read_text());self.assertEqual(r['state'],'unknown');self.assertEqual(r['request_id'],'r1');self.assertNotIn('signed URL',str(r));self.assertIn('audio_url',json.loads((p/'download-private.json').read_text()))
   with self.assertRaises(FileExistsError):self.run_synthesis(p)
 def test_provider_error_is_failed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'new'
   with self.assertRaises(RuntimeError):self.run_synthesis(p,provider=lambda b:{'request_id':'bad','code':'InvalidVoice'})
   self.assertEqual(json.loads((p/'receipt.json').read_text())['state'],'failed')
 def test_mock_http_protocol(self):
  captured=[]
  def fake(req,timeout):
   captured.append(req);return io.BytesIO(json.dumps({'request_id':'ok','output':{'audio':{'url':'https://example.org/a'}}}).encode())
  with patch.dict(os.environ,{'DASHSCOPE_API_KEY':'test-key'}),patch.object(m.urllib.request,'urlopen',fake):
   m.cloud({'model':'qwen3-tts-instruct-flash','input':{'voice':'TestVoice','instructions':'自然'}})
  request=captured[0];self.assertEqual(request.full_url,m.ENDPOINT);self.assertEqual(request.get_header('Authorization'),'Bearer test-key');self.assertEqual(json.loads(request.data)['input']['instructions'],'自然')
 def test_aliyun_http_upgrade_preserves_signature(self):
  captured=[]
  def fake(url,timeout):captured.append(url);return io.BytesIO(b'audio')
  with patch.object(m.urllib.request,'urlopen',fake):
   self.assertEqual(m.download('http://bucket.oss-cn-beijing.aliyuncs.com/a.wav?signature=abc'),b'audio')
  self.assertEqual(captured[0],'https://bucket.oss-cn-beijing.aliyuncs.com/a.wav?signature=abc')
  with self.assertRaises(ValueError):m.download('http://example.org/a')
 def test_invalid_model_before_output_creation(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'new'
   with self.assertRaises(ValueError):m.synthesize('text','voice','wrong','instruction',p)
   self.assertFalse(p.exists())

if __name__=='__main__':unittest.main()
