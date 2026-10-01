#!/usr/bin/env python3
"""Fetch character assets dynamically from Fleet Cartoon Assets MCP into local workspace."""

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

DEFAULT_ENDPOINT = "https://fleet.vyibc.com/api/hub/plugin-bootstrap/mcp/vyibc-cartoon-assets"
DEFAULT_BOOTSTRAP_TOKEN = "eyJleHAiOjE3OTM0MDk5MzcsInBsdWdpbiI6ImNhcnRvb24tdmlkZW8tc3R1ZGlvIiwibm9uY2UiOiJkMTI3MDIzZi1lNTBhLTQ5ODYtYjQ4ZC00M2RkOWFiNDdlN2IifQ.RGLZagCvRvJcJBagVmM6QrbJ8ZHWRmVjY0SLQTD98gc"

def resolve_token():
    if os.environ.get("CARTOON_ASSETS_TOKEN"):
        return os.environ["CARTOON_ASSETS_TOKEN"]
    creds_path = Path.home() / ".config/vyibc-cartoon-assets/credentials.json"
    if creds_path.is_file():
        try:
            data = json.loads(creds_path.read_text())
            if data.get("token"):
                return data["token"]
        except Exception:
            pass
    return DEFAULT_BOOTSTRAP_TOKEN

def call_mcp(endpoint, token, method, params=None):
    req_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(req_data).encode("utf-8"),
        headers={
            "user-agent": "curl/8.5.0",
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
            "authorization": f"Bearer {token}"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
        for event in raw.split("\n\n"):
            for line in event.splitlines():
                if line.startswith("data:"):
                    return json.loads(line[5:].lstrip())
        return json.loads(raw)

def get_character_assets(character_id, endpoint=DEFAULT_ENDPOINT, token=None):
    token = token or resolve_token()
    res = call_mcp(endpoint, token, "tools/call", {
        "name": "character_assets",
        "arguments": {"character_id": character_id}
    })
    text = res.get("result", {}).get("content", [{}])[0].get("text", "")
    if not text:
        raise RuntimeError(f"Empty character_assets response: {res}")
    return json.loads(text)

def get_asset_detail(asset_id, endpoint=DEFAULT_ENDPOINT, token=None):
    token = token or resolve_token()
    res = call_mcp(endpoint, token, "tools/call", {
        "name": "asset_get",
        "arguments": {"id": asset_id}
    })
    text = res.get("result", {}).get("content", [{}])[0].get("text", "")
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None

def download_file(url, target_path, expected_sha256=None):
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"user-agent": "curl/8.5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(target_path, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
    if expected_sha256:
        actual_sha256 = hashlib.sha256(target_path.read_bytes()).hexdigest()
        if actual_sha256 != expected_sha256:
            raise ValueError(f"Hash mismatch for {target_path}: expected {expected_sha256}, got {actual_sha256}")
    return target_path

def sync_character_assets(character_id="xuman-campus-v1", dest_dir="assets", categories=None, dry_run=False):
    dest_path = Path(dest_dir).resolve()
    assets_data = get_character_assets(character_id)
    all_categories = assets_data.get("assets", {})
    selected_categories = categories or list(all_categories.keys())
    
    downloaded = []
    manifest = {
        "character_id": character_id,
        "assets": []
    }
    
    for cat in selected_categories:
        items = all_categories.get(cat, [])
        for item in items:
            asset_id = item.get("id")
            title = item.get("title", asset_id)
            kind = item.get("kind", "file")
            if kind not in ("image", "audio"):
                continue
            
            detail = get_asset_detail(asset_id)
            if not detail:
                continue
            
            dl_info = detail.get("download", {})
            dl_url = dl_info.get("url")
            expected_hash = dl_info.get("sha256")
            
            # fallback to direct cdn url if present in detail
            if not dl_url:
                for entry in detail.get("generation_inputs", []):
                    if entry.get("url"):
                        dl_url = entry["url"]
                        break
            
            if not dl_url:
                continue
            
            ext = ".png" if kind == "image" else ".wav"
            safe_name = f"{cat}_{asset_id[:8]}{ext}"
            file_dest = dest_path / safe_name
            
            record = {
                "id": asset_id,
                "category": cat,
                "title": title,
                "local_path": str(file_dest.relative_to(dest_path)),
                "sha256": expected_hash,
                "source_url": dl_url
            }
            manifest["assets"].append(record)
            
            if dry_run:
                print(f"[DRY-RUN] Would fetch: {title} ({cat}) -> {safe_name}")
            else:
                print(f"Fetching {title} -> {safe_name}...")
                try:
                    download_file(dl_url, file_dest, expected_sha256=expected_hash)
                    downloaded.append(record)
                except Exception as err:
                    print(f"Warning: Failed to fetch {asset_id} ({title}): {err}", file=sys.stderr)
    
    if not dry_run:
        manifest_file = dest_path / "assets_manifest.json"
        manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        print(f"Asset sync complete. {len(downloaded)} assets saved to {dest_path}.")
    
    return manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--character-id", default="xuman-campus-v1", help="Character ID in Fleet media library")
    parser.add_argument("--dest-dir", default="assets", help="Target assets directory")
    parser.add_argument("--categories", nargs="*", help="Filter categories to download")
    parser.add_argument("--dry-run", action="store_true", help="Print asset details without downloading")
    args = parser.parse_args()
    
    sync_character_assets(
        character_id=args.character_id,
        dest_dir=args.dest_dir,
        categories=args.categories,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()
