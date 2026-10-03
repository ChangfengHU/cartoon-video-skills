#!/usr/bin/env python3
import sys
import os
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from common import init_node_context, find_upstream_artifact, write_manifest

DASHSCOPE_KEY = os.environ.get("DASHSCOPE_API_KEY") or "sk-a1f311c28fdc4584a550b99d7ba8e963"

def call_qwen(prompt):
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DASHSCOPE_KEY}"
    }
    payload = {
        "model": "qwen-turbo",
        "messages": [
            {"role": "system", "content": "你是一名顶级生活喜剧短视频编剧。你必须输出严格合法的JSON格式，不包含任何Markdown标记。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        content = res["choices"][0]["message"]["content"]
        return json.loads(content)

def main():
    print("=== [Node 02: Script Writer] Started ===")
    wiki_path, node_run_id, node_workspace, outputs_dir = init_node_context(sys.argv)

    topic_data = find_upstream_artifact(wiki_path, node_workspace, "topic.json")
    if not topic_data:
        topic_data = {
            "topic_title": "打工人的精简断舍离：扔掉三件旧衣服，反向网购八个收纳箱",
            "core_pain_point": "周末雄心勃勃搞断舍离，结果旧物舍不得扔，反手网购更多收纳箱置物架把客厅堆成迷宫",
            "hook": "扔掉三件旧衣服，反向网购八个收纳箱，打工人的断舍离到底有多离谱？"
        }

    title = topic_data.get("topic_title", "生活自嘲喜剧")
    pain = topic_data.get("core_pain_point", "断舍离反向消费")
    hook = topic_data.get("hook", "扔掉三件旧衣服，反向网购八个收纳箱！")

    prompt = f"""请针对短视频主题编写12幕爆笑生活喜剧短剧本，并严格按照【条漫四层排版】输出视觉卡片要素。
主题：《{title}》
核心痛点：{pain}
开场金句：{hook}

剧情结构（四段反转递进）：
第1-3幕（立Flag）：周末大早下定决心彻底断舍离，立誓过上日系极简生活；
第4-6幕（现实反噬）：旧衣服觉得还能当睡衣，旧数据线觉得万一能用，扔了半天只扔三个塑料袋；
第7-9幕（恶性升级）：觉得房子乱是因为没收纳，打开手机搜整理神器，疯狂凑单买亚克力箱和洞洞板；
第10-12幕（终极反转躺平）：周日晚上快递堆成城墙连门都打不开，主角在箱子堆里安详顿悟自嘲。

严格要求：
1. 必须总共恰好12幕。
2. 每幕 dialogue 必须精炼口语化、纯正自嘲嘴替，字数严格在 14 到 22 字之间！绝不要书面语！
3. 每幕需输出条漫视觉要素：
   - act_tag: 左上角时空阶段标签（如 "周六 · 09:30", "衣柜前 · 10:15", "网购中 · 14:00", "周日 · 快递进门", "顿悟 · 20:00"）
   - headline: 顶部场景大标题，极具冲击力（如 "今天，必须断舍离", "这衣服，还能当睡衣", "反向消费，买它！", "房子满了，我也空了"）
   - stamp_text: 倾斜吐槽印章文字（如 "[立誓极简]", "[舍不得 ✕ 99]", "[买到就是赚到]", "[快递攻城]"）
   - stamp_angle: 倾斜角度，-4.0 到 4.0 之间的浮点数
   - emotion: 情绪标签（relaxed / proud / puzzled / defeated / shocked / desperate / triumphant）
   - sfx_cue: 音效（typing, notification, pop, whoosh, chime, error, impact-bass-1）
   - bgm_cut: 布尔值，关键反转打脸点（如第4、7、10幕）设为 true 触发音乐急停留白！

输出纯JSON格式：
{{
  "title": "{title}",
  "scenes": [
    {{
      "scene_id": 1,
      "dialogue": "台词内容(14-22字)",
      "act_tag": "周六 · 09:30",
      "headline": "今天，必须断舍离",
      "stamp_text": "[立誓极简]",
      "stamp_angle": -3.5,
      "emotion": "proud",
      "sfx_cue": "whoosh",
      "bgm_cut": false
    }}
  ]
}}
"""
    try:
        data = call_qwen(prompt)
        scenes = data.get("scenes", [])
        if len(scenes) < 10:
            raise ValueError("Too few scenes")
    except Exception as e:
        print(f"Fallback script generation due to: {e}")
        scenes = [
            {
                "scene_id": 1,
                "dialogue": "周六早晨九点半，我看着乱糟糟的客厅下定决心！",
                "act_tag": "周六 · 09:30",
                "headline": "今天，必须断舍离",
                "stamp_text": "[立誓极简]",
                "stamp_angle": -3.0,
                "emotion": "proud",
                "sfx_cue": "chime",
                "bgm_cut": False
            },
            {
                "scene_id": 2,
                "dialogue": "今天不把屋子精简成日式极简风，绝不出这个家门！",
                "act_tag": "周六 · 09:45",
                "headline": "向极简生活宣誓",
                "stamp_text": "[豪言壮语]",
                "stamp_angle": 2.5,
                "emotion": "triumphant",
                "sfx_cue": "whoosh",
                "bgm_cut": False
            },
            {
                "scene_id": 3,
                "dialogue": "拿出黑色大垃圾袋，气势磅礴地走向堆成山的大衣柜。",
                "act_tag": "衣柜前 · 10:15",
                "headline": "第一战场：大衣柜",
                "stamp_text": "[准备动刀]",
                "stamp_angle": -2.0,
                "emotion": "relaxed",
                "sfx_cue": "pop",
                "bgm_cut": False
            },
            {
                "scene_id": 4,
                "dialogue": "拿起一件大二买的破T恤，突然觉得还能当睡衣穿穿。",
                "act_tag": "衣柜前 · 10:30",
                "headline": "等等，万一还能穿呢？",
                "stamp_text": "[舍不得 ✕ 1]",
                "stamp_angle": 3.2,
                "emotion": "puzzled",
                "sfx_cue": "error",
                "bgm_cut": True
            },
            {
                "scene_id": 5,
                "dialogue": "又翻出五根不知名旧数据线，心想哪天肯定用得上吧？",
                "act_tag": "抽屉前 · 11:00",
                "headline": "绝版电子传家宝",
                "stamp_text": "[未雨绸缪]",
                "stamp_angle": -3.5,
                "emotion": "puzzled",
                "sfx_cue": "notification",
                "bgm_cut": False
            },
            {
                "scene_id": 6,
                "dialogue": "折腾了整整两小时，垃圾袋里就扔了三个外卖塑料袋！",
                "act_tag": "战果核算 · 12:00",
                "headline": "两小时的伟大成果",
                "stamp_text": "[精简了个寂寞]",
                "stamp_angle": 4.0,
                "emotion": "defeated",
                "sfx_cue": "impact-bass-1",
                "bgm_cut": False
            },
            {
                "scene_id": 7,
                "dialogue": "我悟了，乱不是因为东西多，纯粹是因为我缺收纳！",
                "act_tag": "顿悟时刻 · 13:00",
                "headline": "问题不在我，在收纳！",
                "stamp_text": "[逻辑闭环]",
                "stamp_angle": -2.8,
                "emotion": "proud",
                "sfx_cue": "chime",
                "bgm_cut": True
            },
            {
                "scene_id": 8,
                "dialogue": "打开橙色软件搜收纳神器，大数据精准得让我害怕。",
                "act_tag": "网购战场 · 14:00",
                "headline": "大数据：听说你要收纳？",
                "stamp_text": "[精准推送]",
                "stamp_angle": 2.2,
                "emotion": "shocked",
                "sfx_cue": "notification",
                "bgm_cut": False
            },
            {
                "scene_id": 9,
                "dialogue": "八个亚克力抽屉，两套免打孔洞洞板，顺手凑个满减！",
                "act_tag": "清空购物车 · 15:30",
                "headline": "为了省两百，怒花八百",
                "stamp_text": "[凑单大胜利]",
                "stamp_angle": -4.0,
                "emotion": "triumphant",
                "sfx_cue": "whoosh-short",
                "bgm_cut": False
            },
            {
                "scene_id": 10,
                "dialogue": "周日下午门铃狂响，十几个巨大纸箱直接堵死了防盗门！",
                "act_tag": "周日 · 快递进门",
                "headline": "反向断舍离现场",
                "stamp_text": "[快递围城]",
                "stamp_angle": 3.8,
                "emotion": "shocked",
                "sfx_cue": "impact-bass-2",
                "bgm_cut": True
            },
            {
                "scene_id": 11,
                "dialogue": "我坐在快递筑成的城墙顶上，突然感觉房子彻底空了。",
                "act_tag": "客厅废墟 · 18:00",
                "headline": "坐拥江山，无处下脚",
                "stamp_text": "[钱包极简了]",
                "stamp_angle": -3.2,
                "emotion": "desperate",
                "sfx_cue": "error",
                "bgm_cut": False
            },
            {
                "scene_id": 12,
                "dialogue": "真正的极简，就是连‘断舍离’三个字都别想起来！",
                "act_tag": "人生哲理 · 20:00",
                "headline": "今日悟道：放下执念",
                "stamp_text": "[终极躺平]",
                "stamp_angle": 0.0,
                "emotion": "relaxed",
                "sfx_cue": "pop",
                "bgm_cut": False
            }
        ]

    script_data = {
        "title": title,
        "scenes": scenes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    script_file = outputs_dir / "script.json"
    script_file.write_text(json.dumps(script_data, ensure_ascii=False, indent=2), encoding="utf-8")

    items = [
        {
            "output": "script.json",
            "path": "script.json",
            "kind": "file",
            "type": "application/json",
            "title": "爆笑剧本台词方案"
        }
    ]
    write_manifest(outputs_dir, items)
    print("=== [Node 02: Script Writer] Succeeded ===")

if __name__ == "__main__":
    main()
