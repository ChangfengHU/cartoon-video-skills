#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from common import init_node_context, find_upstream_artifact, write_manifest

DEFAULT_SFX_ROTATION = [
    "typing", "notification", "whoosh-short", "impact-bass-1",
    "error", "glitch-1", "chime", "whoosh",
    "impact-bass-2", "ping", "pop", "sparkle"
]

def main():
    print("=== [Node 07: Audio Foley] Started ===")
    wiki_path, node_run_id, node_workspace, outputs_dir = init_node_context(sys.argv)

    voice_data = find_upstream_artifact(wiki_path, node_workspace, "voice-measured.json")
    storyboard = find_upstream_artifact(wiki_path, node_workspace, "storyboard.json")

    if not voice_data:
        raise ValueError("Missing voice-measured.json for audio foley")

    scenes_voice = voice_data.get("scenes", [])
    sb_scenes = {s["scene_id"]: s for s in (storyboard.get("scenes", []) if storyboard else [])}
    clips_dir = voice_data.get("clips_dir", "")

    records = []
    current_time = 0.0

    for idx, v in enumerate(scenes_voice):
        sc_id = v["scene_id"]
        sb = sb_scenes.get(sc_id, {})
        dur = v["duration"]
        voice_path = v.get("full_path") or (str(Path(clips_dir) / Path(v["file"]).name) if clips_dir else v["file"])

        sfx_cue = sb.get("sfx_cue")
        if not sfx_cue:
            sfx_cue = DEFAULT_SFX_ROTATION[idx % len(DEFAULT_SFX_ROTATION)]

        rec = {
            "scene_id": sc_id,
            "start_time": round(current_time, 3),
            "end_time": round(current_time + dur, 3),
            "duration": dur,
            "voice_file": voice_path,
            "text": v.get("text", ""),
            "sfx_cue": sfx_cue,
            "bgm_cut": sb.get("bgm_cut", False)
        }
        records.append(rec)
        current_time += dur

    timeline = {
        "status": "completed",
        "total_duration": round(current_time, 3),
        "scene_count": len(records),
        "clips_dir": clips_dir,
        "records": records,
        "bgm_track": "bgm-comedy.mp3",
        "foley_version": "2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "node_run_id": node_run_id
    }

    timeline_file = outputs_dir / "audio-timeline.json"
    timeline_file.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")

    items = [
        {
            "output": "audio-timeline.json",
            "path": "audio-timeline.json",
            "kind": "file",
            "type": "application/json",
            "title": "音频总账本与毫秒卡点时间轴"
        }
    ]
    write_manifest(outputs_dir, items)
    print(f"=== [Node 07: Audio Foley] Succeeded (Total {round(current_time, 2)}s, {len(records)} scenes) ===")

if __name__ == "__main__":
    main()
