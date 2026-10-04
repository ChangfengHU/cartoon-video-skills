#!/usr/bin/env python3
import sys
import os
import json
import math
import subprocess
import concurrent.futures
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
from common import init_node_context, find_upstream_artifact, write_manifest

SKILL_DIR = Path("/home/claude/agent-brain-plugins/youtube-wiki/skills/cartoon-hyperframes-animator")
POSES_DIR = SKILL_DIR / "assets" / "poses"
AUDIO_DIR = SKILL_DIR / "assets" / "audio"
BGM_FILE = AUDIO_DIR / "bgm-comedy.mp3"
SFX_DIR = AUDIO_DIR / "sfx"

FONT_SYS_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_SYS_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

BG_COLOR = "#F8F1E3"       # Warm comic paper
INK_COLOR = "#292620"      # Hand-drawn ink line
MUTED_TAG = "#8A8070"      # Warm gray for act/time tag
FLOOR_COLOR = "#D1C4AF"    # Hand-drawn floor line
SHADOW_COLOR = "#E2D7C3"   # Soft shoe shadow
ALERT_RED = "#D84315"
ACCENT_ORANGE = "#E0834B"

font_tag = ImageFont.truetype(FONT_SYS_REG, 34)
font_head = ImageFont.truetype(FONT_SYS_BOLD, 62)
font_stamp = ImageFont.truetype(FONT_SYS_BOLD, 42)
font_sub = ImageFont.truetype(FONT_SYS_BOLD, 50)
font_fx = ImageFont.truetype(FONT_SYS_BOLD, 56)

def draw_comic_header(draw, img, sc):
    act_tag = sc.get("act_tag") or sc.get("hero_card", {}).get("act_tag", f"第 {sc.get('scene_id', 1)} 幕")
    headline = sc.get("headline") or sc.get("hero_card", {}).get("headline", "断舍离进行时")
    stamp_text = sc.get("stamp_text") or sc.get("hero_card", {}).get("stamp_text", "[立誓极简]")
    stamp_angle = float(sc.get("stamp_angle") or sc.get("hero_card", {}).get("stamp_angle", -3.0))

    # 1. Top left time/context tag
    draw.text((105, 140), act_tag, font=font_tag, fill=MUTED_TAG)

    # 2. Main Scene Headline (Big bold)
    draw.text((105, 210), headline, font=font_head, fill=INK_COLOR)

    # 3. Angled Comic Stamp Badge
    bbox = font_stamp.getbbox(stamp_text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    bw, bh = tw + 70, th + 44

    stamp_img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(stamp_img)
    sdraw.rounded_rectangle([2, 2, bw - 2, bh - 2], radius=14, fill="#FFF9ED", outline=INK_COLOR, width=4)
    stamp_col = ALERT_RED if any(w in stamp_text for w in ["打脸", "寂寞", "围城", "废墟", "空了", "崩"]) else INK_COLOR
    sdraw.text(((bw - tw) // 2, (bh - th) // 2 - 4), stamp_text, font=font_stamp, fill=stamp_col)

    stamp_rot = stamp_img.rotate(stamp_angle, expand=True, resample=Image.BICUBIC)
    stamp_x = 320
    stamp_y = 330
    img.paste(stamp_rot, (stamp_x, stamp_y), stamp_rot)

def draw_floor_and_grounding(draw, floor_y=1380):
    # Soft shoe shadow
    draw.ellipse([540 - 240, floor_y - 18, 540 + 240, floor_y + 18], fill=SHADOW_COLOR)
    # Hand-drawn sketch floor line
    draw.line([(80, floor_y), (1000, floor_y)], fill=FLOOR_COLOR, width=4)
    draw.line([(140, floor_y + 12), (360, floor_y + 12)], fill=FLOOR_COLOR, width=2)
    draw.line([(720, floor_y + 12), (920, floor_y + 12)], fill=FLOOR_COLOR, width=2)

def draw_comic_effects(draw, emotion, char_x, char_y, target_w):
    if emotion in ["shocked", "panicked"]:
        # Blue sweat drop near right temple
        sx, sy = char_x + target_w - 70, char_y + 90
        draw.ellipse([sx, sy, sx + 28, sy + 38], fill="#42A5F5", outline=INK_COLOR, width=2)
        draw.text((char_x + target_w - 30, char_y + 40), "!!", font=font_fx, fill=ALERT_RED)
    elif emotion in ["desperate", "defeated"]:
        for offset in [-30, -10, 10, 30]:
            draw.line([(char_x + target_w // 2 + offset, char_y - 20), (char_x + target_w // 2 + offset, char_y + 30)], fill="#8A8070", width=3)
    elif emotion in ["triumphant", "proud"]:
        draw.text((char_x + 30, char_y + 40), "✦", font=font_fx, fill="#F57F17")
        draw.text((char_x + target_w - 40, char_y + 60), "✧", font=font_fx, fill="#F57F17")

def draw_subtitle_card(draw, text, y_center=1600, max_w=920):
    raw_lines = text.split('\n')
    lines = []
    for rl in raw_lines:
        current = ""
        for ch in rl:
            test = current + ch
            bbox = font_sub.getbbox(test)
            w = bbox[2] - bbox[0]
            if w > max_w and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)

    line_h = 64
    total_h = len(lines) * line_h
    start_y = y_center - total_h // 2

    for i, line in enumerate(lines):
        bb = font_sub.getbbox(line)
        lw = bb[2] - bb[0]
        lx = (1080 - lw) // 2
        ly = start_y + i * line_h
        draw.text((lx, ly), line, font=font_sub, fill=INK_COLOR)

def render_scene_frame(sc, beat_type="a", out_path=None):
    img = Image.new("RGB", (1080, 1920), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # 1. Comic 4-Tier Header (Act Tag + Headline + Angled Stamp)
    draw_comic_header(draw, img, sc)

    # 2. Floor line & grounding
    floor_y = 1380
    draw_floor_and_grounding(draw, floor_y)

    # 3. Character Pose
    pose_name = sc.get("pose", "pose_0.png")
    if beat_type == "b":
        alt_poses = {
            "pose_0.png": "pose_2.png",   # 轻松摸鱼 -> 抓头疑惑
            "pose_1.png": "pose_4.png",   # 得意暗爽 -> 震惊破防
            "pose_2.png": "pose_7.png",   # 抓头疑惑 -> 手抖慌张
            "pose_3.png": "pose_10.png",  # 欢呼庆祝 -> 累瘫桌上
            "pose_4.png": "pose_5.png",   # 震惊瞪眼 -> 抱头崩溃
            "pose_5.png": "pose_13.png",  # 抱头崩溃 -> 连滚带爬逃跑
            "pose_6.png": "pose_7.png",   # 偷看斜眼 -> 慌张手抖
            "pose_7.png": "pose_12.png",  # 慌张手抖 -> 叹气丧气
            "pose_8.png": "pose_4.png",   # 神气指点 -> 瞬间打脸破防
            "pose_9.png": "pose_14.png",  # 无奈耸肩 -> 佛系打坐
            "pose_10.png": "pose_14.png", # 累瘫桌上 -> 佛系打坐
            "pose_11.png": "pose_13.png", # 敬礼认错 -> 溜之大吉
            "pose_12.png": "pose_10.png", # 叹气丧气 -> 累瘫桌上
            "pose_13.png": "pose_5.png",  # 逃跑撞墙 -> 抱头崩溃
            "pose_14.png": "pose_1.png"   # 佛系看化 -> 狡黠偷笑
        }
        pose_name = alt_poses.get(pose_name, "pose_2.png")

    pose_path = POSES_DIR / pose_name
    if not pose_path.exists():
        pose_path = POSES_DIR / "pose_0.png"

    try:
        p_img = Image.open(pose_path).convert("RGBA")
        pw, ph = p_img.size
        target_h = 750
        scale = target_h / ph
        target_w = int(pw * scale)
        p_resized = p_img.resize((target_w, target_h), Image.LANCZOS)

        prop_name = sc.get("prop")
        char_x = (1080 - target_w) // 2
        char_y = floor_y - target_h + 10

        # Dynamic layout: avoid character and prop overlap
        if prop_name:
            if "mirror" in prop_name:
                char_x = max(440, (1080 - target_w) // 2 + 180)
            elif "storage_box" in prop_name:
                if sc.get("scene_id") in [10, 11]:
                    char_x = (1080 - target_w) // 2
                else:
                    char_x = min(280, (1080 - target_w) // 2 - 130)
            elif any(k in prop_name for k in ["hanger", "cables", "coffee_mug"]):
                char_x = min(320, (1080 - target_w) // 2 - 120)

        img.paste(p_resized, (char_x, char_y), p_resized)

        # 3.5 Story Prop Rendering (Mirror, Storage Box, Hanger, Cables)
        prop_name = sc.get("prop")
        if prop_name:
            prop_path = POSES_DIR / prop_name
            if prop_path.exists():
                pr_img = Image.open(prop_path).convert("RGBA")
                pr_w, pr_h = pr_img.size
                if "mirror" in prop_name:
                    target_ph = 680
                    scale_p = target_ph / pr_h
                    target_pw = int(pr_w * scale_p)
                    pr_resized = pr_img.resize((target_pw, target_ph), Image.LANCZOS)
                    img.paste(pr_resized, (110, floor_y - target_ph + 25), pr_resized)
                elif "storage_box" in prop_name:
                    target_ph = 300
                    scale_p = target_ph / pr_h
                    target_pw = int(pr_w * scale_p)
                    pr_resized = pr_img.resize((target_pw, target_ph), Image.LANCZOS)
                    img.paste(pr_resized, (700, floor_y - target_ph + 15), pr_resized)
                    if sc.get("scene_id") in [10, 11]:
                        img.paste(pr_resized, (130, floor_y - target_ph + 15), pr_resized)
                elif "hanger" in prop_name:
                    target_ph = 360
                    scale_p = target_ph / pr_h
                    target_pw = int(pr_w * scale_p)
                    pr_resized = pr_img.resize((target_pw, target_ph), Image.LANCZOS)
                    img.paste(pr_resized, (690, floor_y - target_ph - 120), pr_resized)
                elif "cables" in prop_name:
                    target_ph = 220
                    scale_p = target_ph / pr_h
                    target_pw = int(pr_w * scale_p)
                    pr_resized = pr_img.resize((target_pw, target_ph), Image.LANCZOS)
                    img.paste(pr_resized, (680, floor_y - target_ph + 20), pr_resized)

        # 4. Comic FX overlay on Beat B
        if beat_type == "b":
            draw_comic_effects(draw, sc.get("emotion", "relaxed"), char_x, char_y, target_w)
    except Exception as e:
        print(f"Error drawing pose: {e}")

    # 5. Subtitle Card
    dialogue = sc.get("dialogue", "")
    draw_subtitle_card(draw, dialogue)

    if out_path:
        img.save(out_path, quality=95)
    return img

def render_single_scene_av(rec, sb, clips_dir, frames_dir, segs_dir):
    """
    Renders video for scene (beat a + beat b), attaches its EXACT matching voiceover and SFX,
    and returns path to scene_XX_av.mp4.
    """
    sc_id = rec["scene_id"]
    dur = float(rec["duration"])
    dur_a = round(dur * 0.48, 3)
    dur_b = round(dur - dur_a, 3)

    f_a = frames_dir / f"frame_{sc_id:02d}_a.jpg"
    f_b = frames_dir / f"frame_{sc_id:02d}_b.jpg"

    render_scene_frame(sb, "a", f_a)
    render_scene_frame(sb, "b", f_b)

    seg_a = segs_dir / f"seg_{sc_id:02d}_a.mp4"
    seg_b = segs_dir / f"seg_{sc_id:02d}_b.mp4"

    motion = sb.get("camera", "push_in")
    m_a = "push" if motion == "push_in" else ("shake" if motion == "shake" else "static")
    m_b = "punch" if motion in ["shake", "punch"] else "push"

    # Render beat a
    vf_a = f"zoompan=z='min(zoom+0.0008,1.06)':d={max(1, int(dur_a*30))}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30" if m_a == "push" else "null"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(f_a),
        "-vf", vf_a, "-t", f"{dur_a:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-r", "30",
        str(seg_a)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Render beat b
    if m_b == "shake":
        vf_b = f"zoompan=z='1.04':d={max(1, int(dur_b*30))}:x='iw/2-(iw/zoom/2)+sin(in*3)*6':y='ih/2-(ih/zoom/2)+cos(in*3)*6':s=1080x1920:fps=30"
    elif m_b == "punch":
        vf_b = f"zoompan=z='if(lte(in,6),1.0+in*0.015,1.09)':d={max(1, int(dur_b*30))}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
    else:
        vf_b = f"zoompan=z='min(zoom+0.0006,1.05)':d={max(1, int(dur_b*30))}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"

    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(f_b),
        "-vf", vf_b, "-t", f"{dur_b:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-r", "30",
        str(seg_b)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Concat video for this scene
    scene_concat_txt = segs_dir / f"concat_{sc_id:02d}.txt"
    scene_concat_txt.write_text(f"file '{seg_a}'\nfile '{seg_b}'\n", encoding="utf-8")
    scene_video = segs_dir / f"scene_{sc_id:02d}_video.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(scene_concat_txt),
        "-c", "copy", str(scene_video)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Resolve exact voice clip
    voice_path = Path(rec.get("voice_file", ""))
    if not voice_path.exists():
        voice_path = clips_dir / f"scene_{sc_id:02d}.mp3"
    if not voice_path.exists():
        voice_path = clips_dir / f"scene_{sc_id}.mp3"

    scene_audio = segs_dir / f"scene_{sc_id:02d}_audio.mp4"
    sfx_cue = sb.get("sfx_cue", rec.get("sfx_cue", "pop"))
    sfx_file = f"{sfx_cue}.mp3" if not str(sfx_cue).endswith(".mp3") else str(sfx_cue)
    sfx_path = SFX_DIR / sfx_file
    if not sfx_path.exists():
        sfx_path = SFX_DIR / "pop.mp3"

    # Mix voice + SFX with strict 48000Hz stereo format and limiter to avoid clipping
    if sfx_path and sfx_path.exists():
        delay_ms = int(dur_a * 1000)
        filter_complex = (
            f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.0[v];"
            f"[1:a]adelay={delay_ms}|{delay_ms},aformat=sample_rates=48000:channel_layouts=stereo,volume=0.35[sfx];"
            f"[v][sfx]amix=inputs=2:weights=1 1:normalize=0:duration=first,alimiter=limit=0.95[a]"
        )
        subprocess.run([
            "ffmpeg", "-y", "-i", str(voice_path), "-i", str(sfx_path),
            "-filter_complex", filter_complex, "-map", "[a]",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            str(scene_audio)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(voice_path),
            "-af", "aformat=sample_rates=48000:channel_layouts=stereo",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            str(scene_audio)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Mux scene video and audio into scene_XX_av.mp4 with clean stream copy
    scene_av = segs_dir / f"scene_{sc_id:02d}_av.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(scene_video), "-i", str(scene_audio),
        "-c:v", "copy", "-c:a", "copy", "-shortest",
        str(scene_av)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return scene_av

def main():
    print("=== [Node 09: HyperFrames Animator 2.0] Started ===")
    wiki_path, node_run_id, node_workspace, outputs_dir = init_node_context(sys.argv)

    storyboard = find_upstream_artifact(wiki_path, node_workspace, "storyboard.json")
    timeline = find_upstream_artifact(wiki_path, node_workspace, "audio-timeline.json")

    if not storyboard or not timeline:
        raise ValueError("Missing storyboard.json or audio-timeline.json for animator")

    records = timeline.get("records", [])
    sb_scenes = {s["scene_id"]: s for s in storyboard.get("scenes", [])}

    frames_dir = outputs_dir / "frames"
    segs_dir = outputs_dir / "segments"
    frames_dir.mkdir(parents=True, exist_ok=True)
    segs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Resolve exact clips directory from current run
    clips_dir = None
    if timeline.get("clips_dir") and Path(timeline["clips_dir"]).exists():
        clips_dir = Path(timeline["clips_dir"])

    if not clips_dir:
        voice_measured = find_upstream_artifact(wiki_path, node_workspace, "voice-measured.json")
        if voice_measured and voice_measured.get("clips_dir") and Path(voice_measured["clips_dir"]).exists():
            clips_dir = Path(voice_measured["clips_dir"])
        elif voice_measured and voice_measured.get("node_run_id"):
            cand = wiki_path / "raw" / "node-runs" / voice_measured["node_run_id"] / "outputs" / "clips"
            if cand.exists():
                clips_dir = cand

    if not clips_dir:
        # scan node-runs sorted by mtime descending (most recent first!)
        node_runs_dir = wiki_path / "raw" / "node-runs"
        if node_runs_dir.exists():
            sorted_runs = sorted(node_runs_dir.iterdir(), key=lambda p: p.stat().st_mtime if p.is_dir() else 0, reverse=True)
            for r in sorted_runs:
                if (r / "outputs" / "clips").exists() and (r / "outputs" / "clips" / "scene_01.mp3").exists():
                    clips_dir = r / "outputs" / "clips"
                    break

    if not clips_dir:
        clips_dir = outputs_dir / "clips"

    print(f"Using verified voice clips directory: {clips_dir}")

    # 2. Render each scene's audio & video synchronously (Per-Scene Zero Drift)
    print("Rendering per-scene audio-visual synchronized segments...")
    av_segments = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(render_single_scene_av, rec, sb_scenes.get(rec["scene_id"], {}), clips_dir, frames_dir, segs_dir): rec["scene_id"]
            for rec in records
        }
        results = {}
        for f in concurrent.futures.as_completed(futures):
            sc_id = futures[f]
            results[sc_id] = f.result()

    for rec in records:
        av_segments.append(results[rec["scene_id"]])

    # 3. Concatenate all AV segments
    concat_av_txt = outputs_dir / "concat_av.txt"
    concat_av_txt.write_text("".join([f"file '{p}'\n" for p in av_segments]), encoding="utf-8")

    video_with_voice = outputs_dir / "video_with_voice.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_av_txt),
        "-c", "copy", str(video_with_voice)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("All scene AV segments concatenated with 100% synchronization.")

    # 4. Mix Ducked BGM with EBU R128 Loudness Normalization
    print("Mixing background music and mastering audio with EBU R128...")
    final_output = outputs_dir / "raw-render.mp4"
    total_dur = timeline.get("total_duration", 96.0)

    if BGM_FILE.exists():
        filter_complex = (
            f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.0[voice];"
            f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{total_dur},aformat=sample_rates=48000:channel_layouts=stereo,volume=0.10[bgm];"
            f"[voice][bgm]amix=inputs=2:weights=1 1:normalize=0:duration=first:dropout_transition=2,"
            f"alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=9[a]"
        )
        cmd_mix = [
            "ffmpeg", "-y", "-i", str(video_with_voice), "-i", str(BGM_FILE),
            "-filter_complex", filter_complex,
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            str(final_output)
        ]
    else:
        cmd_mix = [
            "ffmpeg", "-y", "-i", str(video_with_voice),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            str(final_output)
        ]

    subprocess.run(cmd_mix, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Final render completed: {final_output}")

    items = [
        {
            "output": "raw-render.mp4",
            "path": "raw-render.mp4",
            "kind": "file",
            "type": "video/mp4",
            "title": "HyperFrames 2.0 高清动画成片"
        }
    ]
    write_manifest(outputs_dir, items)
    print("=== [Node 09: HyperFrames Animator 2.0] Succeeded ===")

if __name__ == "__main__":
    main()
