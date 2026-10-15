import json, re, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'plugins/cartoon-video-studio'

class AudioRelations(unittest.TestCase):
 def test_shared_connection_preserves_existing_services(self):
  servers=json.loads((PACKAGE/'.mcp.json').read_text())['mcpServers']
  previous={'vyibc-cartoon-assets','vyibc-image','vyibc-douyin','vyibc-youtube','vyibc-voice','vyibc-behavior','vyibc-xiaohongshu','vyibc-vault'}
  self.assertEqual(set(servers),previous|{'auto-parse-audio'})
  self.assertEqual(servers['auto-parse-audio'],{'url':'https://auto-parse-audio.2513120790.workers.dev/mcp','bearer_token_env_var':'MCP_AUTO_PARSE_AUDIO_TOKEN'})
  self.assertEqual(len({server['url'] for server in servers.values()}),len(servers))
 def test_audio_contract_and_references_survive_mirror(self):
  contract='skills/studio-music/references/audio-mcp.md'
  self.assertEqual((ROOT/contract).read_bytes(),(PACKAGE/contract).read_bytes())
  for name in ['studio-music','studio-materials','cartoon-video-studio','studio-quality','cartoon-11nodes']:
   relative=f'skills/{name}/SKILL.md'
   self.assertEqual((ROOT/relative).read_bytes(),(PACKAGE/relative).read_bytes())
   links=re.findall(r'\]\(([^)]+audio-mcp\.md)\)',(PACKAGE/relative).read_text())
   self.assertTrue(links,name)
   for link in links:self.assertEqual((PACKAGE/relative).parent.joinpath(link).resolve(),(PACKAGE/contract).resolve())

if __name__=='__main__':unittest.main()
