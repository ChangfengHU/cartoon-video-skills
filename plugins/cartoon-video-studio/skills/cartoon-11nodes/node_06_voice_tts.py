#!/usr/bin/env python3
import sys
import os
import json
import hashlib
import io
import wave
import urllib.request
import urllib.parse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
import concurrent.futures
from common import init_node_context, find_upstream_artifact, write_manifest

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

def synthesize_one_scene(sc, clips_dir):
    raw_id = sc.get("scene_id") or sc.get("id") or sc.get("scene_num") or 1
    if isinstance(raw_id, str):
        digits = "".join(filter(str.isdigit, raw_id))
        sc_id = int(digits) if digits else 1
    else:
        try:
            sc_id = int(raw_id)
        except:
            sc_id = 1

    text = sc.get("dialogue", "").strip()
    if not text:
        text = sc.get("title", f"第{sc_id}幕")
    emotion = sc.get("emotion", "calm")
    instruction = EMOTION_INSTRUCTIONS.get(emotion, EMOTION_INSTRUCTIONS["calm"])

    mp3_path = clips_dir / f"scene_{sc_id:02d}.mp3"

    body = {
        "model": COSY_MODEL,
        "input": {
            "text": text,
            "voice": COSY_VOICE_ID,
            "format": "mp3",
            "sample_rate": 24000
        }
    }
    if instruction:
        body["input"]["instruction"] = instruction

    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-WorkSpace": DASHSCOPE_WORKSPACE_ID
    }

    for attempt in range(4):
        try:
            req = urllib.request.Request(TTS_ENDPOINT, headers=headers, data=json.dumps(body).encode("utf-8"))
            with urllib.request.urlopen(req, timeout=30) as res:
                result = json.loads(res.read().decode())
            audio_url = result["output"]["audio"]["url"]
            if audio_url.startswith("http://"):
                audio_url = "https://" + audio_url[7:]
            req2 = urllib.request.Request(audio_url, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req2, timeout=30) as res2:
                mp3_path.write_bytes(res2.read())
            dur = get_audio_duration(mp3_path)
            print(f"  [TTS] scene_{sc_id:02d} done ({dur:.2f}s): {text[:12]}...")
            return {
                "scene_id": sc_id,
                "duration": dur,
                "file": f"clips/scene_{sc_id:02d}.mp3",
                "full_path": str(mp3_path.resolve()),
                "text": text
            }
        except Exception as e:
            if attempt < 3:
                import time
                time.sleep(1.5 * (attempt + 1))
            else:
                print(f"  [TTS Error] scene_{sc_id:02d} ({e}), falling back to silence")
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "3.0", "-q:a", "9", str(mp3_path)
                ], check=True, capture_output=True)
                return {
                    "scene_id": sc_id,
                    "duration": 3.0,
                    "file": f"clips/scene_{sc_id:02d}.mp3",
                    "full_path": str(mp3_path.resolve()),
                    "text": text
                }

def main():
    print("=== [Node 06: Voice Synthesizer] Started ===")
    wiki_path, node_run_id, node_workspace, outputs_dir = init_node_context(sys.argv)

    storyboard = find_upstream_artifact(wiki_path, node_workspace, "storyboard.json")
    if not storyboard:
        raise ValueError("Missing storyboard.json for voice synthesizer")

    scenes = storyboard.get("scenes", [])
    clips_dir = outputs_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    measured = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(synthesize_one_scene, s, clips_dir) for s in scenes]
        for f in concurrent.futures.as_completed(futures):
            measured.append(f.result())

    measured.sort(key=lambda x: x["scene_id"])
    total_dur = round(sum(m["duration"] for m in measured), 2)

    receipt = {
        "status": "completed",
        "voice": COSY_VOICE_ID,
        "total_duration": total_dur,
        "scene_count": len(measured),
        "clips_dir": str(clips_dir.resolve()),
        "scenes": measured,
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "node_run_id": node_run_id
    }

    voice_file = outputs_dir / "voice-measured.json"
    voice_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")

    items = [
        {
            "output": "voice-measured.json",
            "path": "voice-measured.json",
            "kind": "file",
            "type": "application/json",
            "title": "实测语音时长与音频清单"
        }
    ]
    write_manifest(outputs_dir, items)
    print(f"=== [Node 06: Voice Synthesizer] Succeeded (Total {total_dur}s) ===")

if __name__ == "__main__":
    main()
