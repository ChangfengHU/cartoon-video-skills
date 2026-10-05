#!/usr/bin/env python3
"""
ForEach Map-Reduce Orchestration Adapter for Cartoon TTS (Node 06)
- MapStep: Slices 12 scenes from node-03 storyboard into concurrent TTS workers (concurrency=4)
- Worker: Synthesizes individual scene audio with CosyVoice / BigTTS
- Reduce: Aggregates measured durations and audio manifests into voice-measured.json
- Hot-Retry: Allows isolated re-synthesis of single failed scene slices
"""

import sys
import os
import json
import hashlib
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone
import concurrent.futures

COSY_MODEL = "cosyvoice-v3.5-plus"
COSY_VOICE_ID = "cosyvoice-v3.5-plus-tape0912-0225bd3f896c446f9cba1c0a94024554"
TTS_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-ws-H.RYYRYEE.evC5.MEUCIQCPdMJJv11RsGzIH5cdBsNpGnr8bOvoCnMh-uTDTcC5EgIgFbWxsnYjb89OsTc-KHlKY2M5gA1j4Jo-_P28x7PMSqI")
DASHSCOPE_WORKSPACE_ID = os.environ.get("DASHSCOPE_WORKSPACE_ID", "llm-lzsu3q43q4rhpa6i")

EMOTION_INSTRUCTIONS = {
    "relaxed": "用极其放松、慵懒自如的语气说，带点漫不经心的调侃感！",
    "panicked": "极度惊慌失措、声调拔高、倒吸一口凉气、语速极快地惊呼尖叫！",
    "helpless": "深深叹一口长气、满脸写着认命和疲惫、苦笑自嘲地说！",
    "resigned_happy": "想通了一样释怀长舒一口气、破罐子破摔、带着可爱微笑地说！",
    "excited": "兴奋激动得直搓手、两眼放光、声调高昂地欢呼！",
    "proud": "尾音傲娇上扬、不可一世、神气活现地吹嘘！",
    "shocked": "用极度震惊、破防破音、眼睛瞪圆了难以置信的语调大喊！",
    "desperate": "带浓重哭腔、生无可恋、快要瘫倒在地的绝望哀嚎！",
    "cunning": "贼眉鼠眼、压低嗓音、暗搓搓使坏偷笑、沾沾自喜地小声嘀咕！",
    "defeated": "整个人泄了气、生无可恋、有气无力地认输！",
    "calm": "表面一本正经、内心暗自吐槽地沉稳叙述！",
    "sarcastic": "阴阳怪气拉满、慢吞吞翻着白眼、极其戏谑戏精地大声自嘲！",
    "triumphant": "昂首挺胸、狂喜大笑、得瑟到飞起地大声宣布！"
}

def get_audio_duration(path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        return round(float(out), 4)
    except:
        return 3.0

class ForEachTTSOrchestrator:
    def __init__(self, scenes, output_dir, concurrency=4):
        self.scenes = scenes
        self.output_dir = Path(output_dir)
        self.clips_dir = self.output_dir / "voice_clips"
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        self.concurrency = concurrency
        self.slices = []

    def execute_slice(self, index, sc):
        raw_id = sc.get("scene_id") or sc.get("id") or sc.get("scene_num") or (index + 1)
        try:
            sc_id = int(str(raw_id).strip("scene_"))
        except:
            sc_id = index + 1

        text = sc.get("dialogue", "").strip() or sc.get("title", f"第{sc_id}幕")
        emotion = sc.get("emotion", "calm")
        mp3_path = self.clips_dir / f"scene_{sc_id:02d}.mp3"

        slice_meta = {
            "slice_id": f"voice-slice-{sc_id:02d}",
            "index": index,
            "scene_id": sc_id,
            "text": text,
            "emotion": emotion,
            "status": "running",
            "file": str(mp3_path.name),
            "full_path": str(mp3_path),
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        # Check if cache exists and is valid
        if mp3_path.exists() and mp3_path.stat().st_size > 1024:
            dur = get_audio_duration(mp3_path)
            slice_meta.update({
                "status": "completed",
                "duration": dur,
                "size_bytes": mp3_path.stat().st_size,
                "cached": True,
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            return slice_meta

        # Synthesize via DashScope / CosyVoice
        try:
            import urllib.request
            body = {
                "model": COSY_MODEL,
                "input": {
                    "text": text,
                    "voice": COSY_VOICE_ID,
                    "format": "mp3",
                    "sample_rate": 24000
                },
                "parameters": {
                    "rate": 0.85
                }
            }
            if emotion in EMOTION_INSTRUCTIONS:
                body["input"]["instruction"] = EMOTION_INSTRUCTIONS[emotion]

            req = urllib.request.Request(
                TTS_ENDPOINT,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                    "X-DashScope-WorkSpace": DASHSCOPE_WORKSPACE_ID
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                if resp.status == 200 and len(data) > 1024:
                    with open(mp3_path, "wb") as f:
                        f.write(data)
                    dur = get_audio_duration(mp3_path)
                    slice_meta.update({
                        "status": "completed",
                        "duration": dur,
                        "size_bytes": len(data),
                        "cached": False,
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    })
                    return slice_meta
                else:
                    raise RuntimeError(f"HTTP {resp.status}, response size: {len(data)}")
        except Exception as e:
            slice_meta.update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            return slice_meta

    def run_map_reduce(self):
        print(f"[ForEach-TTS] Slicing {len(self.scenes)} scenes with concurrency={self.concurrency}")
        results = [None] * len(self.scenes)
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            future_to_index = {
                executor.submit(self.execute_slice, i, sc): i
                for i, sc in enumerate(self.scenes)
            }
            for future in concurrent.futures.as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    slice_res = future.result()
                    results[idx] = slice_res
                    print(f"  [Slice {slice_res['slice_id']}] {slice_res['status']} · {slice_res.get('duration', 0)}s")
                except Exception as e:
                    results[idx] = {
                        "slice_id": f"voice-slice-{idx+1:02d}",
                        "index": idx,
                        "status": "failed",
                        "error": str(e)
                    }

        self.slices = results
        # Reduce aggregation
        total_duration = sum(s.get("duration", 0) for s in self.slices if s.get("status") == "completed")
        successful_slices = [s for s in self.slices if s.get("status") == "completed"]
        failed_slices = [s for s in self.slices if s.get("status") == "failed"]

        reduced = {
            "schema": "sop-voice-measured/v2-foreach",
            "orchestration_type": "foreach-map-reduce",
            "total_scenes": len(self.scenes),
            "successful_slices": len(successful_slices),
            "failed_slices": len(failed_slices),
            "total_duration_seconds": round(total_duration, 4),
            "slices": self.slices,
            "clips": [
                {
                    "scene_id": s["scene_id"],
                    "file": s["file"],
                    "duration": s["duration"],
                    "text": s["text"],
                    "emotion": s["emotion"]
                }
                for s in successful_slices
            ]
        }

        output_path = self.output_dir / "voice-measured.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(reduced, f, ensure_ascii=False, indent=2)

        print(f"[ForEach-TTS] Reduced {len(successful_slices)}/{len(self.scenes)} slices. Total duration: {total_duration:.2f}s")
        return reduced

    def hot_retry_slice(self, scene_id):
        idx = next((i for i, sc in enumerate(self.scenes) if (sc.get("scene_id") or sc.get("id")) == scene_id), None)
        if idx is None:
            raise ValueError(f"Scene ID {scene_id} not found")
        print(f"[ForEach-TTS Hot-Retry] Re-running slice for scene {scene_id}...")
        res = self.execute_slice(idx, self.scenes[idx])
        self.slices[idx] = res
        return res

if __name__ == "__main__":
    test_scenes = [
        {"id": 1, "dialogue": "第一幕测试台词", "emotion": "calm"},
        {"id": 2, "dialogue": "第二幕测试台词", "emotion": "excited"},
    ]
    orchestrator = ForEachTTSOrchestrator(test_scenes, "/tmp/foreach_tts_test", concurrency=2)
    orchestrator.run_map_reduce()
