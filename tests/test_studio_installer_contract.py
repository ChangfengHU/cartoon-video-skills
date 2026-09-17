import re
import unittest
from pathlib import Path


INSTALLER = Path(__file__).resolve().parents[1] / "release" / "install-cartoon-video-studio.sh"


class InstallerContractTests(unittest.TestCase):
    def test_dsh_can_inspect_declared_plugin_and_mcp_contract(self):
        script = INSTALLER.read_text()
        marketplace = re.search(r"codex\s+plugin\s+marketplace\s+add\s+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", script)
        selector = re.search(r"codex\s+plugin\s+add\s+([A-Za-z0-9_.-]+)@([A-Za-z0-9_.-]+)", script)
        bridge = re.search(r'BRIDGE_BASE="\$\{VYIBC_PLUGIN_BRIDGE_BASE:-([^}"\s]+)\}"', script)
        declared = re.search(r"servers\s*=\s*\[([^\]]+)\]", script)
        servers = re.findall(r"['\"]([A-Za-z0-9_.-]+)['\"]", declared.group(1) if declared else "")

        self.assertEqual(marketplace.group(1), "ChangfengHU/cartoon-video-skills")
        self.assertEqual(selector.groups(), ("cartoon-video-studio", "personal"))
        self.assertEqual(bridge.group(1), "https://fleet.vyibc.com/api/hub/plugin-bootstrap/mcp")
        self.assertEqual(
            servers,
            [
                "vyibc-cartoon-assets", "vyibc-image", "vyibc-douyin", "vyibc-youtube",
                "vyibc-voice", "vyibc-behavior", "vyibc-xiaohongshu", "vyibc-vault",
            ],
        )

