#!/usr/bin/env python3
import sys
import os
import json
import random
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from common import init_node_context, write_manifest

DASHSCOPE_KEY = os.environ.get("DASHSCOPE_API_KEY") or "sk-a1f311c28fdc4584a550b99d7ba8e963"

EXPANDED_TOPIC_POOL = [
    {
        "title": "打工人的精简断舍离：扔掉三件旧衣服，反向网购八个收纳箱",
        "pain_point": "周末雄心勃勃搞断舍离，结果旧物舍不得扔，反手网购更多收纳箱置物架把客厅堆成迷宫",
        "hook": "扔掉三件旧衣服，反向网购八个收纳箱，打工人的断舍离到底有多离谱？",
        "tags": ["周末断舍离", "反向消费", "收纳黑洞", "打工人自嘲", "下班小人"]
    },
    {
        "title": "老板说‘再改一版’时，我CPU彻底烧了",
        "pain_point": "连续通宵修改8版方案，需求方突然要求用回第1版还加新功能",
        "hook": "我电脑里存了终版、打死不改版、再改自杀版，结果你告诉我用原版？！",
        "tags": ["改需求", "设计崩溃", "甲方日常", "情绪稳定打工人", "下班小人"]
    },
    {
        "title": "周五下午4点59分，突然收到全员开会通知",
        "pain_point": "包都收拾好了，工牌都摘了，手机突然狂震被拉进紧急群",
        "hook": "下班不积极，思想有问题；但在走前一秒被截胡，才是终极破防！",
        "tags": ["下班倒计时", "紧急开会", "周五破防", "打工人嘴替", "下班小人"]
    },
    {
        "title": "假装在认真看代码，其实脑子在放空",
        "pain_point": "下午三点半的大脑宕机时刻，双手机械敲键盘，眼神无比空洞",
        "hook": "眼神无比专注，屏幕代码狂滚，实际上我已经在想要点哪家奶茶了。",
        "tags": ["摸鱼哲学", "下午三点", "打工人放空", "人间清醒", "下班小人"]
    },
    {
        "title": "用AI工具十分钟干完活，我犯了职场最致命错误",
        "pain_point": "手快把周报秒发大群，被领导抓包派了三个救火项目",
        "hook": "本想用科技革命提前下班，结果把自己卷成了卷王之王！",
        "tags": ["AI摸鱼", "反向自卷", "职场翻车", "戏精打工人", "下班小人"]
    },
    {
        "title": "带薪拉屎20分钟，腿麻到扶着墙走出隔间",
        "pain_point": "在厕所刷短视频太沉浸，双腿失去知觉仿佛不是自己的",
        "hook": "每一个颤颤巍巍走出洗手间的打工人，都在用生命捍卫带薪尊严！",
        "tags": ["带薪摸鱼", "卫生间避难所", "打工人自愈", "生活细节", "下班小人"]
    },
    {
        "title": "周一早会夺命催进度，文档只有两行字",
        "pain_point": "早会汇报还没准备好，领导突然点名要成果",
        "hook": "只要我不抬头，领导的眼神就扫不到我！",
        "tags": ["职场日常", "周一早会", "打工人自嘲", "下班小人"]
    },
    {
        "title": "报销流程审批两星期，发票快褪色了还没到账",
        "pain_point": "垫付巨款出差，财务审批卡在某位领导那里不动",
        "hook": "工资还没发，垫资两万八，每天查审批系统比看股票还勤！",
        "tags": ["财务报销", "职场催办", "打工人辛酸", "真实写照", "下班小人"]
    },
    {
        "title": "面试造火箭，入职拧螺丝还被螺丝滑丝了",
        "pain_point": "面试聊分布式高并发微服务，入职天天手动改Excel表格",
        "hook": "面试时我是架构大师，入职后我是复制粘贴首席执行官！",
        "tags": ["职场现实", "大材小用", "自嘲幽默", "打工心酸", "下班小人"]
    },
    {
        "title": "跨部门拉齐赋能闭环，听完两小时我只记住了‘拉齐’",
        "pain_point": "通篇互联网大厂黑话，开完会没人知道下一步具体干啥",
        "hook": "只要黑话足够多，就没人发现我们其实根本没方案！",
        "tags": ["大厂黑话", "无效会议", "职场讽刺", "下班小人"]
    },
    {
        "title": "假装加班到八点，只为了领那份二十块的夜宵补助",
        "pain_point": "工作早就做完了，硬熬到饭点打卡就为了蹭盒饭",
        "hook": "不是加班有多香，而是二十块的免费黄焖鸡更有性价比！",
        "tags": ["加班文化", "羊毛党", "打工人日常", "生活喜剧", "下班小人"]
    }
]

def generate_topic_via_qwen(instruction=""):
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DASHSCOPE_KEY}"
    }

    if instruction and len(instruction) > 3 and "自动" not in instruction:
        user_prompt = f"请根据命题《{instruction}》，策划一个下班小人（职场自嘲圆头人）幽默短剧选题。必须有强戏剧冲突、黄金前3秒开场梗、扎心反转与自愈金句。"
    else:
        user_prompt = "请策划一个当下最能引发年轻打工人强烈共鸣的爆笑职场反转选题（例如改需求崩溃、摸鱼翻车、假装加班、开会黑话、AI反噬等）。必须有戏剧冲突与反转金句。"

    prompt = f"""{user_prompt}
请严格输出JSON：
{{
  "title": "选题标题（12-20字，吸睛爆梗）",
  "pain_point": "核心痛点（描述具体职场尴尬或冲突）",
  "hook": "开场黄金3秒吸睛金句",
  "tags": ["职场自嘲", "下班小人", "热梗"]
}}
"""

    payload = {
        "model": "qwen-turbo",
        "messages": [
            {"role": "system", "content": "你是千万级职场搞笑短视频的爆款编导，擅长捕捉打工人最真实的破防与自嘲瞬间。严格输出合法JSON。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "response_format": {"type": "json_object"}
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            content = res["choices"][0]["message"]["content"]
            data = json.loads(content)
            if data.get("title") and data.get("pain_point"):
                return data
    except Exception as e:
        print(f"Qwen dynamic topic generation warning: {e}, falling back to curated pool.")
    return None

def main():
    print("=== [Node 01: Topic Curator] Started ===")
    wiki_path, node_run_id, node_workspace, outputs_dir = init_node_context(sys.argv)

    instruction = ""
    input_json = node_workspace / "input.json"
    if input_json.exists():
        try:
            doc = json.loads(input_json.read_text(encoding="utf-8"))
            manual = doc.get("manual_inputs", {})
            instruction = manual.get("instruction", "")
            if not instruction:
                parts = doc.get("a2a", {}).get("message", {}).get("parts", [])
                for p in parts:
                    txt = p.get("text") or p.get("content", {}).get("value") or ""
                    if txt and len(txt) > 2:
                        instruction = txt
                        break
        except Exception as e:
            print(f"Error parsing input.json: {e}")

    # Try dynamic Qwen generation first
    choice = generate_topic_via_qwen(instruction)

    if not choice:
        if instruction and "自动" not in instruction and len(instruction) > 5 and not instruction.startswith("#"):
            choice = {
                "title": instruction[:30],
                "pain_point": instruction,
                "hook": f"今天聊聊：{instruction[:20]}...",
                "tags": ["打工人日常", "职场自嘲", "下班小人"]
            }
        else:
            choice = random.choice(EXPANDED_TOPIC_POOL)
            print(f"Selected topic from expanded curated pool: {choice['title']}")

    topic_data = {
        "topic_title": choice["title"],
        "core_pain_point": choice["pain_point"],
        "hook": choice["hook"],
        "audience_emotion": "共鸣自嘲 + 释怀解压",
        "tags": choice.get("tags", ["职场自嘲", "下班小人"]),
        "curated_at": datetime.now(timezone.utc).isoformat(),
        "node_run_id": node_run_id
    }

    topic_file = outputs_dir / "topic.json"
    topic_file.write_text(json.dumps(topic_data, ensure_ascii=False, indent=2), encoding="utf-8")

    history_data = {
        "recent_topics": [choice["title"]],
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    history_file = outputs_dir / "topic-history.json"
    history_file.write_text(json.dumps(history_data, ensure_ascii=False, indent=2), encoding="utf-8")

    items = [
        {
            "output": "topic.json",
            "path": "topic.json",
            "kind": "file",
            "type": "application/json",
            "title": "爆款选题方案与痛点策划"
        },
        {
            "output": "topic-history.json",
            "path": "topic-history.json",
            "kind": "file",
            "type": "application/json",
            "title": "历史选题记录"
        }
    ]
    write_manifest(outputs_dir, items)
    print(f"=== [Node 01: Topic Curator] Succeeded with topic: '{choice['title']}' ===")

if __name__ == "__main__":
    main()
