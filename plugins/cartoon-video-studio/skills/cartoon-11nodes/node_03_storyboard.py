#!/usr/bin/env python3
import sys
import os
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from common import init_node_context, find_upstream_artifact, write_manifest

DASHSCOPE_KEY = os.environ.get("DASHSCOPE_API_KEY") or "sk-a1f311c28fdc4584a550b99d7ba8e963"

AVAILABLE_POSES = [
    "pose_0.png",   # 轻松思考/摸鱼
    "pose_1.png",   # 得意自嗨/偷乐
    "pose_2.png",   # 疑惑抓头/懵逼
    "pose_3.png",   # 欢呼庆祝/胜利
    "pose_4.png",   # 震惊瞪眼/破防
    "pose_5.png",   # 抱头崩溃/绝望
    "pose_6.png",   # 偷看斜眼/暗中观察
    "pose_7.png",   # 慌张手抖/手足无措
    "pose_8.png",   # 神气指点/嘴硬
    "pose_9.png",   # 无奈耸肩/认命
    "pose_10.png",  # 累瘫桌上/生无可恋
    "pose_11.png",  # 敬礼乖巧/认错
    "pose_12.png",  # 叹气丧气/低头
    "pose_13.png",  # 连滚带爬逃跑
    "pose_14.png",  # 佛系打坐/看化
    "pose_15.png",  # 握拳宣誓/立Flag (fist_pump)
    "pose_16.png",  # 抱大箱子/负重前行 (carrying)
    "pose_17.png",  # 蹲地拆箱/狂拆快递 (unpacking)
    "pose_18.png",  # 仰面瘫坐/彻底躺平 (kicking_back)
    "pose_19.png",  # 端碗吃面/安慰自己 (eating)
    "pose_20.png",  # 贼眉鼠眼/暗自得意 (scheming)
    "pose_21.png"   # 呆滞注视/石化无语 (staring)
]

def detect_scene_prop_and_pose(dialogue, scene_id):
    d = dialogue.lower()
    prop = None
    suggested_pose = None
    if any(k in d for k in ["镜子", "照镜", "深呼吸", "看自己"]):
        prop = "prop_mirror.png"
        suggested_pose = "pose_6.png"  # 暗中侧目看镜子
    elif any(k in d for k in ["旧衣服", "睡衣", "t恤", "大衣柜", "穿穿", "面料"]):
        prop = "prop_hanger.png"
        suggested_pose = "pose_9.png"  # 无奈耸肩看着旧衣服
    elif any(k in d for k in ["数据线", "电线", "充电线", "插头", "电子传家宝"]):
        prop = "prop_cables.png"
        suggested_pose = "pose_2.png"  # 疑惑抓头
    elif any(k in d for k in ["收纳箱", "纸箱", "快递", "洞洞板", "大箱子", "城墙", "堆满", "满屋子"]):
        prop = "prop_storage_box.png"
        if scene_id in [10, 11]:
            suggested_pose = "pose_17.png"  # 拆箱/箱子堆
        elif scene_id == 12:
            suggested_pose = "pose_18.png"  # 躺在箱子堆里
        else:
            suggested_pose = "pose_16.png"  # 抱箱子
    elif any(k in d for k in ["吃", "泡面", "点外卖", "午饭", "喝水"]):
        prop = "prop_coffee_mug.png"
        suggested_pose = "pose_19.png"  # 吃面

    return prop, suggested_pose

def detect_scene_environment(dialogue, scene_id):
    d = dialogue.lower()
    if any(k in d for k in ["床", "早晨", "醒来", "卧室", "被窝", "爬起来"]):
        return "bg_bedroom_messy.png", "乱糟糟的早晨卧室，被子散乱，窗外晨光照入"
    elif any(k in d for k in ["衣柜", "衣服", "睡衣", "校服", "面料"]):
        return "bg_wardrobe_open.png", "敞开的双门大衣柜，挂满十年前旧衣物与高中校服"
    elif any(k in d for k in ["数据线", "电线", "充电器", "抽屉", "接口", "电子"]):
        return "bg_desk_cables.png", "书桌电脑前抽屉大开，缠绕着杂乱废弃的数据线与插头"
    elif any(k in d for k in ["网购", "手机", "搜", "下单", "凑单", "买它", "神器", "洞洞板"]):
        return "bg_night_laptop.png", "深夜书桌台灯暖光下，笔记本电脑屏幕显示疯抢收纳神器购物车"
    elif any(k in d for k in ["阳台", "厨房", "油刷", "空气炸锅", "零食", "收纳盒"]):
        return "bg_balcony_snacks.png", "阳台多层收纳置物架，塞满未拆封零食与杂物"
    elif any(k in d for k in ["快递堆", "城墙", "堡垒", "纸箱城", "下脚", "满屋"]):
        return "bg_cardboard_fortress.png", "客厅堆满直通天花板的纸箱城墙，形成纸箱堡垒"
    elif any(k in d for k in ["门口", "走廊", "电梯", "扔", "垃圾桶"]):
        return "bg_hallway_boxes.png", "公寓楼走廊通道，门前堆放着等待处理的大号纸箱与快递"
    elif any(k in d for k in ["空荡荡", "空虚", "干净", "冷静", "反思"]):
        return "bg_empty_room.png", "空无一物的极简房间，阳光穿透窗户在地板留下回音"
    elif any(k in d for k in ["悟", "禅", "最高境界", "不在乎", "执念", "躺平"]):
        return "bg_zen_office_chair.png", "纸箱围拢的中央办公转椅，头顶微光，万物皆空禅意境界"
    else:
        if scene_id in [1, 2]:
            return "bg_livingroom_boxes.png", "凌乱客厅，旧沙发与拆开的纸箱"
        elif scene_id in [8, 9]:
            return "bg_hallway_boxes.png", "走廊门口快递纸箱堆"
        elif scene_id in [10, 11]:
            return "bg_cardboard_fortress.png", "纸箱堡垒客厅"
        elif scene_id == 12:
            return "bg_zen_office_chair.png", "纸箱堆里的转椅禅意空间"
        else:
            return "bg_livingroom_boxes.png", "客厅沙发与杂物堆"

def detect_scene_camera_motion(dialogue, emotion, scene_id):
    if emotion in ["shocked", "panicked", "desperate", "frustrated"]:
        return "shake"
    elif emotion in ["smug", "proud", "realized", "focused"]:
        return "push_in"
    elif any(k in dialogue for k in ["城墙", "堡垒", "满屋", "乱糟糟", "到处", "快递堆"]):
        return "wide_pan"
    else:
        return "push_in"

AVAILABLE_SFX = [
    "typing",
    "notification",
    "error",
    "impact-bass-1",
    "impact-bass-2",
    "chime",
    "pop",
    "whoosh",
    "whoosh-short",
    "glitch-1",
    "sparkle",
    "ping"
]

def generate_storyboard_via_llm(title, scenes):
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DASHSCOPE_KEY}"
    }

    dialogue_list = [f"{s.get('scene_id', i+1)}. {s.get('dialogue', '')} ({s.get('acting_note', '')})" for i, s in enumerate(scenes)]
    dialogues_text = "\n".join(dialogue_list)

    prompt = f"""你是一名顶级喜剧分镜导演。请为短剧《{title}》的12幕台词设计视觉卡片（Hero Card）、角色动作姿态（pose）与喜剧音效（sfx_cue）。

台词列表：
{dialogues_text}

必须输出严格合法的JSON格式：
{{
  "scenes": [
    {{
      "scene_id": 1,
      "pose": "pose_8.png",
      "emotion": "relaxed",
      "camera": "push_in",
      "sfx_cue": "typing",
      "hero_card": {{
        "kind": "code",
        "title": "VS Code - main.py",
        "tag": "CODE",
        "lines": [
          "// 这段代码能跑，但别问我怎么跑的",
          "for i in range(17):",
          "    console.log('1'); // 优化中",
          "return 'done in 5m'"
        ]
      }}
    }}
  ]
}}

硬性要求：
1. pose 只能在 pose_0.png 到 pose_14.png 中挑选！绝不可出现单调重复！12个场景必须多样化覆盖思考、得意、抓头、震惊、崩溃、手抖、神气、逃跑、打坐等不同情绪！
2. sfx_cue 必须紧扣动作笑点，从 typing, notification, error, impact-bass-1, chime, pop, whoosh, glitch-1, sparkle 中挑选！
3. hero_card 必须紧扣台词关键词（代码/设计稿/微信弹窗/外卖/报错终端/会议/奖状等）。
"""

    payload = {
        "model": "qwen-turbo",
        "messages": [
            {"role": "system", "content": "你是一名爆笑卡通分镜导演，擅长将口语笑点转化为视觉爆梗UI与丰富角色肢体语言。严格输出JSON。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
        "response_format": {"type": "json_object"}
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=25) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            content = res["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception as e:
        print(f"Warning: LLM storyboard generation failed ({e}), using smart fallback.")
        return None

def build_fallback_hero_card(scene_id, dialogue):
    d = dialogue.lower()
    if any(k in d for k in ["奶茶", "外卖", "点哪家", "喝", "咖啡"]):
        return {
            "kind": "browser", "title": "美团外卖 - 下午茶专区", "tag": "TEA",
            "lines": ["波霸奶茶 (大杯/微糖/去冰)", "正在结算中...", "预计送达: 15:40", "备注: 偷偷放前台别让领导看到"]
        }
    elif any(k in d for k in ["ui", "设计", "色值", "figma", "稿", "切图"]):
        return {
            "kind": "code", "title": "Figma - 终极设计方案", "tag": "FIGMA",
            "lines": ["当前图层: 第27版_最终_真的不改了", "呼吸感参数: 99.8%", "自愈色值: #FF4400 (破防红)", "状态: 待客户第28次挑刺"]
        }
    elif any(k in d for k in ["git", "commit", "push", "分支", "合并"]):
        return {
            "kind": "terminal", "title": "Terminal - git commit", "tag": "GIT",
            "lines": ["$ git commit -m 'fix: urgent bugs'", "error: empty ident name not allowed", "fatal: Please tell me who you are.", "Status: Identity crisis confirmed"]
        }
    elif any(k in d for k in ["typeerror", "undefined", "报错", "崩", "bug", "宕机"]):
        return {
            "kind": "error", "title": "Chrome DevTools - Console", "tag": "ALERT",
            "lines": ["Uncaught TypeError: undefined is not a function", "  at Work.execute (main.js:404)", "  at Brain.think (zero_percent.js:1)", "Status: Critical breakdown"]
        }
    elif any(k in d for k in ["微信", "弹窗", "叮", "群", "老板", "领导", "通知"]):
        return {
            "kind": "chat", "title": "钉钉工作群 (领导在线)", "tag": "CHAT",
            "lines": ["领导: 这段逻辑到底是谁写的？", "我: 是...是我的咖啡因写的！", "同事: 哈哈哈哈哈哈", "领导: 马上来会议室一趟"]
        }
    elif any(k in d for k in ["ai", "唤醒", "智能", "模型", "算法"]):
        return {
            "kind": "code", "title": "AI 助手 - 任务执行控制台", "tag": "AI",
            "lines": ["已生成代码行数: 9999+", "自研深度神经网络: 运行中", "核心指令: 假装很忙并自动提交", "CPU使用率: 100% (烧干了)"]
        }
    elif any(k in d for k in ["ppt", "汇报", "开会", "早会", "大纲"]):
        return {
            "kind": "ppt", "title": "工作汇报 - 本周成果.pptx", "tag": "PPT",
            "lines": ["第一页: 大道至简 (纯白背景)", "第二页: 核心进展 (敬请期待)", "第三页: 未来展望 (下周再说)", "汇报状态: 领导眉头紧锁"]
        }
    elif any(k in d for k in ["奖", "优秀", "工匠", "卷", "自愈", "自嘲", "神"]):
        return {
            "kind": "award", "title": "打工人摸鱼段位证书", "tag": "AWARD",
            "lines": ["授予：职场自嘲嘴替小人", "称号：稳如泰山摸鱼大师", "成就：需求会崩，姿势永远不倒", "认证机构：全国打工人自愈协会"]
        }
    else:
        # Default rotating cards
        kind_rot = ["code", "browser", "chat", "terminal", "ppt"]
        k = kind_rot[scene_id % len(kind_rot)]
        return {
            "kind": k, "title": f"工作台 - 任务第 {scene_id} 幕", "tag": "TASK",
            "lines": [f"进度节点 {scene_id}/12 正在推进", "表面专注度: 100%", "内心慌乱度: 85%", "状态: 稳住能赢"]
        }

def get_fallback_pose_and_sfx(scene_id, dialogue):
    d = dialogue.lower()
    # Dynamic comedic arc per scene
    if scene_id == 1:
        return "pose_0.png", "typing", "relaxed"
    elif scene_id == 2:
        return "pose_8.png", "whoosh-short", "proud"
    elif scene_id == 3:
        return "pose_1.png", "chime", "smug"
    elif scene_id == 4:
        return "pose_4.png", "notification", "shocked"
    elif scene_id == 5:
        return "pose_7.png", "impact-bass-1", "panicked"
    elif scene_id == 6:
        return "pose_2.png", "error", "confused"
    elif scene_id == 7:
        return "pose_5.png", "glitch-1", "desperate"
    elif scene_id == 8:
        return "pose_13.png", "whoosh", "escaping"
    elif scene_id == 9:
        return "pose_12.png", "pop", "depressed"
    elif scene_id == 10:
        return "pose_10.png", "impact-bass-2", "exhausted"
    elif scene_id == 11:
        return "pose_6.png", "ping", "observing"
    else: # 12
        return "pose_14.png", "sparkle", "zen"

def main():
    print("=== [Node 03: Storyboard Director] Started ===")
    wiki_path, node_run_id, node_workspace, outputs_dir = init_node_context(sys.argv)

    script_data = find_upstream_artifact(wiki_path, node_workspace, "script.json")
    if not script_data:
        script_data = {
            "title": "职场自嘲",
            "scenes": [{"scene_id": i, "dialogue": f"第{i}幕职场自嘲台词测试。"} for i in range(1, 13)]
        }

    title = script_data.get("title", "职场自嘲")
    scenes_raw = script_data.get("scenes", [])

    # Try LLM generation first
    llm_result = generate_storyboard_via_llm(title, scenes_raw)
    llm_scenes_map = {}
    if llm_result and "scenes" in llm_result:
        for ls in llm_result["scenes"]:
            llm_scenes_map[ls.get("scene_id")] = ls

    storyboard_scenes = []
    used_poses = []

    for i, s in enumerate(scenes_raw, 1):
        dialogue = s.get("dialogue", "")
        acting = s.get("acting_note", "")
        ls = llm_scenes_map.get(i)

        prop, suggested_pose = detect_scene_prop_and_pose(dialogue, i)

        fallback_pose, fallback_sfx, fallback_emotion = get_fallback_pose_and_sfx(i, dialogue)
        fallback_hero = build_fallback_hero_card(i, dialogue)

        if ls and ls.get("hero_card"):
            raw_pose = ls.get("pose")
            emotion = ls.get("emotion", fallback_emotion)
            camera = ls.get("camera", "push_in")
            sfx_cue = ls.get("sfx_cue", fallback_sfx)
            if sfx_cue not in AVAILABLE_SFX:
                sfx_cue = fallback_sfx
            hero_card = ls.get("hero_card", fallback_hero)
        else:
            hero_card = fallback_hero
            raw_pose = fallback_pose
            emotion = fallback_emotion
            camera = "shake" if emotion in ["shocked", "panicked", "desperate"] else "push_in"
            sfx_cue = fallback_sfx

        # STRICT ZERO-REPETITION POSE SELECTION:
        # Every scene cut MUST have a distinct character expression/pose
        chosen_pose = None
        if suggested_pose and suggested_pose in AVAILABLE_POSES and suggested_pose not in used_poses:
            chosen_pose = suggested_pose
        elif raw_pose and raw_pose in AVAILABLE_POSES and raw_pose not in used_poses:
            chosen_pose = raw_pose
        elif fallback_pose in AVAILABLE_POSES and fallback_pose not in used_poses:
            chosen_pose = fallback_pose
        else:
            unused_pool = [p for p in AVAILABLE_POSES if p not in used_poses]
            if unused_pool:
                chosen_pose = unused_pool[0]
            else:
                chosen_pose = AVAILABLE_POSES[i % len(AVAILABLE_POSES)]

        used_poses.append(chosen_pose)

        act_tag = s.get("act_tag") or f"场景 · {i}"
        headline = s.get("headline") or f"断舍离第 {i} 幕"
        stamp_text = s.get("stamp_text") or (f"[打脸 ✕ {i}]" if i % 2 == 0 else "[立誓极简]")
        stamp_angle = float(s.get("stamp_angle", -3.0 if i % 2 == 0 else 2.5))
        bgm_cut = bool(s.get("bgm_cut", emotion in ["shocked", "panicked", "desperate"]))

        comic_card = {
            "act_tag": act_tag,
            "headline": headline,
            "stamp_text": stamp_text,
            "stamp_angle": stamp_angle
        }

        env_bg, env_desc = detect_scene_environment(dialogue, i)
        cam_motion = detect_scene_camera_motion(dialogue, emotion, i)
        visual_prompt = f"Warm paper comic style [{act_tag}]: {env_desc}. Character performing {chosen_pose} with emotion {emotion}. Story prop: {prop or 'none'}."

        sc = {
            "scene_id": i,
            "title": f"第{i}幕",
            "dialogue": dialogue,
            "acting_note": acting,
            "estimated_duration": 8.0,
            "environment_bg": env_bg,
            "environment_desc": env_desc,
            "visual_prompt": visual_prompt,
            "pose": chosen_pose,
            "prop": prop,
            "emotion": emotion,
            "camera": cam_motion,
            "sfx_cue": sfx_cue,
            "bgm_cut": bgm_cut,
            "act_tag": act_tag,
            "headline": headline,
            "stamp_text": stamp_text,
            "stamp_angle": stamp_angle,
            "hero_card": comic_card
        }
        storyboard_scenes.append(sc)

    # Validate distinct poses count
    unique_poses_count = len(set(used_poses))
    print(f"Storyboard generated with {unique_poses_count} unique character poses across {len(storyboard_scenes)} scenes.")
    print("Pose sequence:", [s["pose"] for s in storyboard_scenes])
    print("SFX sequence:", [s["sfx_cue"] for s in storyboard_scenes])

    storyboard_data = {
        "title": title,
        "total_scenes": len(storyboard_scenes),
        "total_estimated_seconds": len(storyboard_scenes) * 8.0,
        "unique_poses_count": unique_poses_count,
        "scenes": storyboard_scenes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "node_run_id": node_run_id
    }

    storyboard_file = outputs_dir / "storyboard.json"
    storyboard_file.write_text(json.dumps(storyboard_data, ensure_ascii=False, indent=2), encoding="utf-8")

    items = [
        {
            "output": "storyboard.json",
            "path": "storyboard.json",
            "kind": "file",
            "type": "application/json",
            "title": "镜头分镜脚本"
        }
    ]
    write_manifest(outputs_dir, items)
    print("=== [Node 03: Storyboard Director] Succeeded ===")

if __name__ == "__main__":
    main()
