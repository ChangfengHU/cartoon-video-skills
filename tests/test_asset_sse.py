import importlib.util,unittest,json
from pathlib import Path
s=importlib.util.spec_from_file_location('assetclient',Path(__file__).resolve().parents[1]/'skills/cartoon-xiaban/scripts/asset_mcp.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class SSE(unittest.TestCase):
 def test_unicode_separator_inside_json_is_not_sse_newline(self):
  client=object.__new__(m.Client) if hasattr(m,'Client') else None
  self.assertIsNotNone(client)
  value={'jsonrpc':'2.0','id':1,'result':{'text':'中文\u2028仍在同一数据行'}}
  client.http=lambda *args: (('event: message\r\ndata: '+json.dumps(value,ensure_ascii=False)+'\r\n\r\n').encode(),{'Content-Type':'text/event-stream'})
  self.assertEqual(client.rpc({'id':1,'method':'tools/list'}),value)
