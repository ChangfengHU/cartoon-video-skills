# 运行环境

包内含13个skills：工作室入口、两个角色、10个共享HyperFrames/media-use skills。共享skills是Apache-2.0上游快照，版权与来源见插件THIRD-PARTY.md。

本地需要Node22+、FFmpeg、Python3、可启动Chromium、HyperFrames CLI。参考成片使用hyperframes0.8.33。CLI二进制不捆绑，使用项目依赖锁：npm install --save-exact hyperframes@0.8.33 gsap@3.14.2。新项目可依HyperFrames升级规范验证后升级，不能把指导文件版本冒称安装版本。

运行scripts/doctor.py只读检查工具与指定HYPERFRAMES_BROWSER_PATH，不安装系统包、不修改浏览器登录。Snap ARM运行库需要项目内适配，该主机问题不是所有用户都要执行的通用安装步骤。

豆包：scripts/doubao_tts.py调用授权HTTP服务；DOUBAO_API_KEY只从环境/隐藏交互读取。角色明确voice与resource_id，生成后实测时长。没有情绪API或声线克隆功能，不把标点表演意图称为模型情绪控制。1.2倍是当前红衣角色偏好，不强加所有角色。

MCP：素材库CARTOON_ASSETS_TOKEN；生图、抖音、转写使用各自授权VYIBC_IMAGE_TOKEN / VYIBC_DOUYIN_TOKEN / VYIBC_YOUTUBE_TOKEN环境变量。没有任何内嵌token，安装不授予机主账号。优先对现有同端点连接复用，避免重复注册。工具权限以服务实际授权为准。
