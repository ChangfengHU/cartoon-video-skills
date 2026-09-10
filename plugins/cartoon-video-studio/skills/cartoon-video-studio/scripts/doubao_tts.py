#!/usr/bin/env python3
"""Generate a Doubao Speech V3 sample without persisting the API key."""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path


ENDPOINT = "https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--resource-id", default="seed-tts-2.0")
    parser.add_argument("--sample-rate", type=int, default=24000)
    parser.add_argument("--speech-rate", type=int, default=5)
    args = parser.parse_args()

    if args.output.exists():
        print("Output already exists; choose another path.", file=sys.stderr)
        return 2
    api_key = os.environ.get("DOUBAO_API_KEY", "").strip()
    if not api_key and sys.stdin.isatty():
        api_key = getpass.getpass("Doubao Speech API key: ").strip()
    if not api_key:
        print("API key is empty.", file=sys.stderr)
        return 2

    additions = {
        "post_process": {"pitch": 0},
        "disable_markdown_filter": False,
        "enable_latex_tn": False,
    }
    payload = {
        "user": {"uid": "behavior-video-mvp-sample"},
        "req_params": {
            "text": args.text,
            "speaker": args.voice,
            "sample_rate": args.sample_rate,
            "audio_params": {
                "format": "mp3",
                "sample_rate": args.sample_rate,
                "speech_rate": args.speech_rate,
                "loudness_rate": 0,
                "bit_rate": 128000,
            },
            "additions": json.dumps(additions, ensure_ascii=False),
        },
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
            "X-Api-Resource-Id": args.resource_id,
            "X-Api-Request-Id": str(uuid.uuid4()),
        },
    )

    chunks: list[bytes] = []
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                event = json.loads(line[5:].strip())
                code = event.get("code", 0)
                if code not in (0, 20000000):
                    raise RuntimeError(
                        f"Doubao error {code}: {event.get('message', '')}"
                    )
                if event.get("data"):
                    chunks.append(base64.b64decode(event["data"]))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}: {detail.replace(api_key, '[REDACTED]')[:1000]}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc).replace(api_key, '[REDACTED]'), file=sys.stderr)
        return 1

    if not chunks:
        print("Doubao returned no audio data.", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(b"".join(chunks))
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
