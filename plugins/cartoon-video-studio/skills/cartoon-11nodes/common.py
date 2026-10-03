import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

def init_node_context(argv):
    """
    Parses argv: <wiki_path> <node_run_id> [pipeline_id]
    Returns (wiki_path, node_run_id, node_workspace, outputs_dir)
    """
    if len(argv) < 3:
        print(f"Error: expected at least 2 args: <wiki_path> <node_run_id>, got {argv}")
        sys.exit(1)

    wiki_path = Path(argv[1]).expanduser().resolve()
    node_run_id = argv[2]
    node_workspace = wiki_path / "raw" / "node-runs" / node_run_id
    outputs_dir = node_workspace / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    return wiki_path, node_run_id, node_workspace, outputs_dir

def find_upstream_artifact(wiki_path, node_workspace, filename):
    """
    Finds artifact by checking:
    1. input.json parts
    2. Directly looking in upstream node runs in raw/node-runs/
    """
    input_json = node_workspace / "input.json"
    if input_json.exists():
        try:
            doc = json.loads(input_json.read_text(encoding="utf-8"))
            parts = doc.get("a2a", {}).get("message", {}).get("parts", [])
            for p in parts:
                fn = p.get("filename")
                if fn == filename:
                    # check data inline or source_path
                    data = p.get("data") or p.get("content", {}).get("value")
                    if data:
                        if isinstance(data, dict) and "source_path" in data:
                            sp = wiki_path / data["source_path"]
                            if sp.exists():
                                if filename.endswith(".json"):
                                    return json.loads(sp.read_text(encoding="utf-8"))
                                return sp
                        if isinstance(data, dict):
                            return data
                        if isinstance(data, str) and filename.endswith(".json"):
                            try:
                                return json.loads(data)
                            except:
                                pass
        except Exception as e:
            print(f"Warning parsing input.json: {e}")

    # Fallback: scan previous node-runs
    node_runs_dir = wiki_path / "raw" / "node-runs"
    if node_runs_dir.exists():
        is_11node = node_workspace.name.startswith("node-run-node-")
        def run_priority(p):
            if not p.is_dir():
                return (-1, 0)
            same_family = 1 if (is_11node and p.name.startswith("node-run-node-")) else 0
            return (same_family, p.stat().st_mtime)

        runs = sorted(node_runs_dir.iterdir(), key=run_priority, reverse=True)
        for r in runs:
            if not r.is_dir() or r.name == node_workspace.name:
                continue
            cand = r / "outputs" / filename
            if cand.exists():
                if filename.endswith(".json"):
                    try:
                        return json.loads(cand.read_text(encoding="utf-8"))
                    except:
                        pass
                return cand

    return None

def write_manifest(outputs_dir, items):
    manifest = {
        "version": 1,
        "items": items
    }
    (outputs_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifest written with {len(items)} items to {outputs_dir / 'manifest.json'}")
