#!/usr/bin/env python3
"""Generate client entrypoints from one reviewed contract; never execute a production."""
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'plugins/cartoon-video-studio'
COMMANDS={
 'studio':('工作室菜单：选择已有角色或创建新角色','[帮助或制作要求]','menu',None),
 'studio-xiabanxiaoren':('下班小人：生活观察、消费与职场喜剧','[主题；留空主动研究选题]','character','下班小人'),
 'studio-hongyi':('红衣女生：女性独白、生活喜剧与反转故事','[主题；留空主动研究选题]','character','红衣女生'),
 'studio-ali':('阿栗：都市生活、机灵吐槽与自嘲喜剧','[主题；留空主动研究选题]','character','阿栗'),
 'studio-new':('新角色：真实参考、设计、选声并制作视频','[抖音喜欢/小红书/参考图/主题；可只设计角色]','new',None),
 'studio-help':('查看指令与角色介绍、预设提示词和使用示例','[指令名]','help',None),
 'studio-revise':('修改已有作品并对照旧版检查','[工程或视频] [修改要求]','revise',None),
 'studio-check':('检查实际成片，不默认修改','[视频或工程]','check',None),
 'studio-publish':('准备文案封面并发布指定作品','[作品] [平台/账号]','publish',None),
}

def catalog():
 return [dict(name=n,description=d,argument_hint=h,mode=m,character_name=c,
              codex='$'+n,slash='/'+n,legacy='/prompts:'+n,
              defaults=('help' if m in ('menu','help') else 'research_topic' if m in ('character','new') else 'resolve_explicit_project'))
         for n,(d,h,m,c) in COMMANDS.items()]

def body(name):
 d,h,mode,char=COMMANDS[name]
 header=f'执行工作室入口 `{name}`。'
 if char: header+=f'固定使用角色「{char}」；从真实档案加载身份、性格、表演参考和认可范围，不重设计或替换。'
 if mode=='new': header+='创建原创角色并制作完整视频；明确只设计角色时才省略视频。'
 if mode in ('menu','help'): header+='空参数仅显示下列帮助，不调用生成、入库或发布。'
 routes='按所选分支加载 cartoon-video-studio、studio-character-workflow 或 studio-quality；从已安装Skill目录找真实文件。缺少依赖报告具体缺项，不能以命令模板冒充完整技能。'
 return header+'\n\n'+routes+'\n\n'

def outputs():
 rules=(ROOT/'skills/studio/references/commands.md').read_text()
 helptext='# 指令帮助\n\n'+ '\n'.join(f'- `/{n}`：{d}。参数：{h}。' for n,(d,h,m,c) in COMMANDS.items())+'\n\nClaude项目/Pi使用 /名称；Codex当前支持 $名称，旧CLI/IDE可选 /prompts:名称。菜单是否加载以当前客户端实际状态为准。\n\n例：`/studio-ali` 主动选题制作；`/studio-hongyi 主题：网购凑单`；`/studio-new 从小红书找参考`；`/studio-new 抖音喜欢，只设计角色`。\n'
 result={ROOT/'skills/studio/references/help.md':helptext}
 for name,(desc,hint,mode,char) in COMMANDS.items():
  for client in ('pi','claude','codex-legacy'):
   result[PACKAGE/'command-support'/client/f'{name}.md']=f'---\ndescription: {desc}\nargument-hint: "{hint}"\n---\n\n'+body(name)+'本次用户补充要求：\n\n$ARGUMENTS\n\n'+('帮助请求只展示用法、预设和默认行为；不得执行选题、生成、入库或发布。\n' if mode=='help' else rules)+'\n'+helptext
  # Native Codex entrypoints are thin skill adapters; roles remain private data.
  ref='references/' if name=='studio' else '../studio/references/'
  result[ROOT/'skills'/name/'SKILL.md']=f'---\nname: {name}\ndescription: {desc}；用户调用本命令时使用，引用示例或请求帮助时只解释。\n---\n\n'+body(name)+f'先读 [共用规则]({ref}commands.md)，帮助见 [命令目录]({ref}help.md)。\n\n本次要求来自调用后的用户文字，空参按规则执行；角色身份与当前音色策略以授权档案为准。\n'
 result[PACKAGE/'command-support/catalog.json']=json.dumps({'schema_version':2,'commands':catalog(),'runtime_tested':[]},ensure_ascii=False,indent=2)+'\n'
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
 for path,content in outputs().items():
  if a.check:
   if not path.is_file() or path.read_text()!=content:raise SystemExit(f'Stale generated file: {path}')
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
 # Remove only the obsolete, unshipped generated entry, never arbitrary files.
 for client in ('pi','claude','codex-legacy'):
  old=PACKAGE/'command-support'/client/'studio-character.md'
  if old.exists():
   if a.check:raise SystemExit(f'Obsolete entry: {old}')
   old.unlink()
 print('Command adapters verified' if a.check else 'Command adapters generated')
