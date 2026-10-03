#!/usr/bin/env python3
import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from common import init_node_context, find_upstream_artifact, write_manifest

POSES_DIR = Path("/home/claude/agent-brain-plugins/youtube-wiki/skills/cartoon-hyperframes-animator/assets/poses")

def sha256_file(p):
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()

def main():
    print("=== [Node 05: Visual Assets] Started ===")
    wiki_path, node_run_id, node_workspace, outputs_dir = init_node_context(sys.argv)

    storyboard = find_upstream_artifact(wiki_path, node_workspace, "storyboard.json")
    if not storyboard:
        raise ValueError("Missing storyboard.json for visual assets")

    scenes = storyboard.get("scenes", [])
    verified_assets = []

    for s in scenes:
        pose_name = s.get("pose", "pose_0.png")
        p = POSES_DIR / pose_name
        if not p.exists():
            # fallback
            p = POSES_DIR / "pose_0.png"
        digest = sha256_file(p)
        verified_assets.append({
            "scene_id": s.get("scene_id"),
            "pose_name": pose_name,
            "path": str(p),
            "sha256": digest
        })

    receipt = {
        "status": "ready",
        "asset_count": len(verified_assets),
        "assets": verified_assets,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "node_run_id": node_run_id
    }

    manifest_file = outputs_dir / "visual-manifest.json"
    manifest_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")

    items = [
        {
            "output": "visual-manifest.json",
            "path": "visual-manifest.json",
            "kind": "file",
            "type": "application/json",
            "title": "视觉资产清单与哈希验真"
        }
    ]
    write_manifest(outputs_dir, items)
    print("=== [Node 05: Visual Assets] Succeeded ===")

if __name__ == "__main__":
    main()
