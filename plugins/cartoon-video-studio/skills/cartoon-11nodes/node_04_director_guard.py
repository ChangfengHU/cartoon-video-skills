#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from common import init_node_context, find_upstream_artifact, write_manifest

def main():
    print("=== [Node 04: Director Guard] Started ===")
    wiki_path, node_run_id, node_workspace, outputs_dir = init_node_context(sys.argv)

    storyboard = find_upstream_artifact(wiki_path, node_workspace, "storyboard.json")
    if not storyboard:
        raise ValueError("Missing storyboard.json for director guard")

    scenes = storyboard.get("scenes", [])
    if len(scenes) < 10:
        raise ValueError(f"Too few scenes: {len(scenes)}, required >= 10")

    for s in scenes:
        txt = s.get("dialogue", "").strip()
        if not txt:
            raise ValueError(f"Empty dialogue in scene {s.get('scene_id')}")

    total_chars = sum(len(s.get("dialogue", "").strip()) for s in scenes)
    if total_chars < 180:
        raise ValueError(f"Total dialogue characters too low: {total_chars} (min 180 characters required for 80s target)")

    receipt = {
        "status": "passed",
        "scene_count": len(scenes),
        "total_estimated_seconds": storyboard.get("total_estimated_seconds", 96.0),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "node_run_id": node_run_id
    }

    guard_file = outputs_dir / "director-guard-passed.json"
    guard_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")

    items = [
        {
            "output": "director-guard-passed.json",
            "path": "director-guard-passed.json",
            "kind": "file",
            "type": "application/json",
            "title": "导演静态门禁通过证书"
        }
    ]
    write_manifest(outputs_dir, items)
    print("=== [Node 04: Director Guard] Succeeded ===")

if __name__ == "__main__":
    main()
