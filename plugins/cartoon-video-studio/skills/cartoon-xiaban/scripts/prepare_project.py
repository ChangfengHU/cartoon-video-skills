#!/usr/bin/env python3
"""Validate this brand pack or copy a frozen, credential-free snapshot to a new project."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


REFERENCES = (
    "references/visual-identity.md",
    "references/story-and-motion.md",
    "references/voice-and-music.md",
    "references/voice-routing.md",
    "references/local-runtime.md",
    "references/comedy-writing.md",
    "references/acting-recipe.md",
    "references/music-research.md",
    "references/episode-direction.md",
    "references/quality-regression.md",
    "references/asset-library.md",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Unsafe asset path: {relative}")
    path = (root / rel).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"Asset is not a file within the pack: {relative}")
    return path


def validate(root: Path) -> tuple[dict, list[str]]:
    profile = json.loads((root / "assets/brand.json").read_text(encoding="utf-8"))
    if profile.get("schema_version") != 1:
        raise ValueError("Unsupported schema_version")
    if not re.fullmatch(r"[a-z0-9-]{1,63}", profile.get("brand_id", "")):
        raise ValueError("Invalid brand_id")
    if not re.fullmatch(r"\d+\.\d+\.\d+", profile.get("version", "")):
        raise ValueError("Version must be major.minor.patch")
    for section in ("identity", "visual", "voice", "music"):
        if not isinstance(profile.get(section), dict) or not profile[section].get("status"):
            raise ValueError(f"Missing status for {section}")
    assets = profile.get("assets", [])
    if not assets:
        raise ValueError("At least one actual identity asset is required")
    names: set[str] = set()
    ids: set[str] = set()
    for asset in assets:
        name = asset["path"]
        if name in names or asset["id"] in ids:
            raise ValueError("Duplicate asset path or id")
        if not name.startswith("assets/") or name == "assets/brand.json":
            raise ValueError("Assets must be media under assets/")
        names.add(name)
        ids.add(asset["id"])
        if digest(inside(root, name)) != asset["sha256"]:
            raise ValueError(f"Asset checksum mismatch: {name}")
    for name in (profile["identity"]["canonical_reference"], profile["identity"]["origin_reference"]):
        if name not in names:
            raise ValueError(f"Identity reference not in asset ledger: {name}")
    voice = profile["voice"]
    if voice["status"] == "user_approved":
        if not voice.get("selected_voice_id") or voice.get("approved_sample") not in names:
            raise ValueError("Approved voice requires an ID and a checksummed sample")
    music = profile["music"]
    if music["status"] == "user_approved" and music.get("selected_track") not in names:
        raise ValueError("Approved music requires a checksummed track")
    files = ["SKILL.md", "assets/brand.json", "scripts/asset_library.py", "scripts/plan_music.py", *REFERENCES, *sorted(names)]
    for name in files:
        inside(root, name)
    # Credential values never belong in profile snapshots. IDs are allowed, auth values are not.
    def inspect_keys(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() in {"api_key", "apikey", "authorization", "access_token", "cookie", "password", "secret"}:
                    raise ValueError(f"Credential field forbidden in brand profile: {key}")
                inspect_keys(item)
        elif isinstance(value, list):
            for item in value:
                inspect_keys(item)
    inspect_keys(profile)
    return profile, files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="A new, non-existing project directory")
    parser.add_argument("--topic", default="", help="Topic for this work only; does not change the brand")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--target-seconds", type=int, default=None, help="Story target, not time stretching")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        profile, files = validate(root)
        target_seconds = args.target_seconds or profile["output_defaults"].get("target_seconds", 90)
        if args.target_seconds is not None and not 10 <= args.target_seconds <= 600:
            raise ValueError("target-seconds must be between 10 and 600")
        states = {part: profile[part]["status"] for part in ("identity", "visual", "voice", "music")}
        if args.check_only:
            print(json.dumps({"valid": True, "brand_id": profile["brand_id"], "version": profile["version"], "assets": len(profile["assets"]), "states": states}, ensure_ascii=False, indent=2))
            return 0
        if not args.output:
            parser.error("--output is required unless --check-only is used")
        if args.output.exists() or args.output.is_symlink():
            raise ValueError("Output already exists; choose a new directory. Nothing was overwritten.")
        output = args.output.expanduser().absolute()
        if output.exists() or output.is_symlink():
            raise ValueError("Resolved output already exists. Nothing was overwritten.")
        # Exclusive mkdir catches races; there is intentionally no overwrite or recursive-delete mode.
        output.mkdir(parents=True, exist_ok=False)
        snapshot = output / "brand"
        ledger = []
        for name in files:
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(inside(root, name), target)
            ledger.append({"path": f"brand/{name}", "sha256": digest(target)})
        lock = {
            "schema_version": 1,
            "brand_id": profile["brand_id"],
            "brand_version": profile["version"],
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "topic": args.topic,
            "target_seconds": target_seconds,
            "output_defaults": {**profile["output_defaults"], "target_seconds": target_seconds},
            "states": states,
            "selected_voice_id": profile["voice"].get("selected_voice_id"),
            "selected_music": profile["music"].get("selected_track"),
            "files": ledger,
            "note": "Asset/configuration snapshot only; not a guarantee of bit-identical generative output. Pending choices remain pending.",
        }
        (output / "BRAND_LOCK.json").write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        brief = f"""# 品牌视频任务

主题：{args.topic or '由本次用户请求决定'}

目标时长：{target_seconds}秒，以实测语音和动作停顿落地，不慢放凑时长。

品牌：{profile['display_name']}（{profile['brand_id']} v{profile['version']}）

先读取 `brand/assets/brand.json`，查看其中参考图，再按 `brand/references/` 的规则制作。本目录是独立作品，别直接修改安装的品牌默认。

- 形象：{states['identity']}
- 画风：{states['visual']}
- 声音：{states['voice']}；选中音色：{profile['voice'].get('selected_voice_id') or '尚未选定'}
- 音乐：{states['music']}；默认：{profile['music']['default_mode']}

音色/音乐尚未定稿时，先生成试听或明确可用性问题；不把空字段当成已选资产。用户本次可以指定试用候选，交付时注明是否尚待认可。

视频按用户指定引擎执行，其余默认参考品牌档案。实际时长按音频确定；本步骤只准备素材与快照，不代表视频已经生成。
"""
        (output / "BRAND_BRIEF.md").write_text(brief, encoding="utf-8")
        print(json.dumps({"prepared": str(output), "files_copied": len(files), "states": states}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Brand preparation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
