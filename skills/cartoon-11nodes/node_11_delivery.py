#!/usr/bin/env python3
import sys
import os
import json
import shutil
import hashlib
import hmac
import datetime
import urllib.request
import subprocess
from pathlib import Path
from common import init_node_context, find_upstream_artifact, write_manifest

ACCOUNT_ID = "059feb047348e153b65f5efde638acf4"
ACCESS_KEY = "e8630d9a2fdd202be8a85f6cbe2b6f3c"
SECRET_KEY = "3f1efc20c99a95680f15d044b3677623f15413b2a8309757f59de655a1cad58c"
BUCKET = "my-images"

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, region_name, service_name):
    k_date = sign(("AWS4" + key).encode("utf-8"), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, "aws4_request")
    return k_signing

def upload_to_r2(local_file, key_path, content_type="video/mp4"):
    content = local_file.read_bytes()
    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    endpoint = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"
    content_hash = hashlib.sha256(content).hexdigest()

    canonical_uri = f"/{BUCKET}/{key_path}"
    host = f"{ACCOUNT_ID}.r2.cloudflarestorage.com"

    canonical_headers = f"host:{host}\nx-amz-content-sha256:{content_hash}\nx-amz-date:{amz_date}\n"
    signed_headers = "host;x-amz-content-sha256;x-amz-date"
    canonical_request = f"PUT\n{canonical_uri}\n\n{canonical_headers}\n{signed_headers}\n{content_hash}"

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/auto/s3/aws4_request"
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

    signing_key = get_signature_key(SECRET_KEY, date_stamp, "auto", "s3")
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    auth_header = f"{algorithm} Credential={ACCESS_KEY}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(
                f"{endpoint}{canonical_uri}",
                data=content,
                headers={
                    "Authorization": auth_header,
                    "x-amz-date": amz_date,
                    "x-amz-content-sha256": content_hash,
                    "Content-Type": content_type
                },
                method="PUT"
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status in (200, 204):
                    return f"https://cdn.vyibc.com/{key_path}"
        except Exception as e:
            if attempt == 3:
                raise e
    return f"https://cdn.vyibc.com/{key_path}"

def main():
    print("=== [Node 11: R2 Delivery Publisher] Started ===")
    wiki_path, node_run_id, node_workspace, outputs_dir = init_node_context(sys.argv)

    raw_video = find_upstream_artifact(wiki_path, node_workspace, "raw-render.mp4")
    if not raw_video or not Path(raw_video).exists():
        raise ValueError("Missing raw-render.mp4 for R2 delivery")

    raw_path = Path(raw_video)
    final_mp4 = outputs_dir / "cartoon-video.mp4"
    shutil.copy2(raw_path, final_mp4)

    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    r2_key = f"uploads/{today}/workflow-runs/{node_run_id}/cartoon-video.mp4"

    print(f"Uploading to Cloudflare R2: {r2_key}...")
    cdn_url = upload_to_r2(final_mp4, r2_key, "video/mp4")
    print(f"Public CDN URL: {cdn_url}")

    url_file = outputs_dir / "cdn-playback-url.txt"
    url_file.write_text(cdn_url + "\n", encoding="utf-8")

    cert = {
        "status": "delivered",
        "video_file": "cartoon-video.mp4",
        "cdn_playback_url": cdn_url,
        "filesize_bytes": final_mp4.stat().st_size,
        "sha256": hashlib.sha256(final_mp4.read_bytes()).hexdigest(),
        "delivered_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "node_run_id": node_run_id
    }
    cert_file = outputs_dir / "delivery-certificate.json"
    cert_file.write_text(json.dumps(cert, ensure_ascii=False, indent=2), encoding="utf-8")

    items = [
        {
            "output": "cartoon-video.mp4",
            "path": "cartoon-video.mp4",
            "kind": "file",
            "type": "video/mp4",
            "title": "成片 MP4 视频文件"
        },
        {
            "output": "cdn-playback-url.txt",
            "path": "cdn-playback-url.txt",
            "kind": "file",
            "type": "text/plain",
            "title": "全球 CDN 播放地址"
        },
        {
            "output": "delivery-certificate.json",
            "path": "delivery-certificate.json",
            "kind": "file",
            "type": "application/json",
            "title": "R2 交付与存证证书"
        }
    ]
    write_manifest(outputs_dir, items)
    print("=== [Node 11: R2 Delivery Publisher] Succeeded ===")

if __name__ == "__main__":
    main()
