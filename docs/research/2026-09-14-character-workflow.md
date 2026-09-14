# 阿栗制作流程通用化：独立开源对比

日期：2026-09-14。独立研究agent执行；只读考察指定插件与 `women-studio-20260914`，未查看其他旧工程、未安装候选、未运行候选、未改技能。原始GitHub API结果见 `upstream-evidence.json`，下载结果含一次404见 `source-fetch.json`。`evidence/` 仅保存研究源码及其许可证，不属于插件集成代码。

## 本地观察与要补的缺口

- 插件 `scripts/production_state.py` 已提供文件SHA256、依赖run_id、下游失效、原子账本写入和fcntl锁、原远程job登记及结果未知时禁止重复begin。无需另建工作流引擎。它并不承担上传、云端重试或审批。其fcntl依赖意味着现实现面向POSIX，不能直接宣称Windows原生支持。
- `references/asset-management.md` 已区分作品、具体文件、创作档案、项目使用四层，并有版本冻结、派生与反馈。角色参考宜补结构化的“发现来源→实际看过的本地帧→生成调用确实输入→输出SHA→角色锁/缺陷”链，继续引用资产ID，不另造素材数据库。
- 阿栗 `characters/ali/profile.json` 已写明用户点赞参考、取2秒帧并输入生图、原创借鉴部位、服装版本与缺陷；approval仍为candidate。该来源叙述不是每次生成调用都有可机械核对的引用锁。
- `QA.md` 与 `film/qa-v2/receipt.json` 已记录最终MP4的SHA、完整解码、12场景及35–37秒连续采样；明确渲染143失败、二维剪纸跑步限制与尚未用户认可。需把这种实际证据组织成通用检查点和明确的候选基准，不能把v2自动晋升为用户认可基准。

## 最多三个候选

### 1. DVC：借鉴依赖与产物锁，不引入CLI或第二份真相库

真实仓库访问 `iterative/dvc` 经GitHub API重定向为 [treeverse/dvc](https://github.com/treeverse/dvc)。固定研究commit `56e59829512ff134aa269099a2099587b810b4dd`，提交日期2026-08-06，仓库pushed_at为2026-09-14，未归档；这只是维护证据，不代表所有功能已验证。

许可证已读：[Apache-2.0](https://github.com/treeverse/dvc/blob/56e59829512ff134aa269099a2099587b810b4dd/LICENSE)。源码已读：[Stage](https://github.com/treeverse/dvc/blob/56e59829512ff134aa269099a2099587b810b4dd/dvc/stage/__init__.py) 的changed_stage/changed_deps/changed_outs分别检查定义、依赖、输出，reproduce决定是否重跑；[Lockfile](https://github.com/treeverse/dvc/blob/56e59829512ff134aa269099a2099587b810b4dd/dvc/dvcfile.py)持久化stage记录。不是只依据README推断。

[pyproject](https://github.com/treeverse/dvc/blob/56e59829512ff134aa269099a2099587b810b4dd/pyproject.toml)要求Python>=3.9，并依赖dvc-data、dvc-objects、fsspec、networkx等；[官方安装文档](https://doc.dvc.org/install)列出macOS、Windows、Linux。研究到的本地锁和依赖检查不要求服务凭据；远程存储需要对应服务的访问配置与可能费用，未做远程运行验证。

**差异与决定：** 本地账本已实现所需大部分机制，DVC的缓存/数据实验体系明显更重。只借鉴“定义、输入、输出均参与失效”的语义：将参考清单、角色锁、剧本、真实音频时长、渲染参数和质量规则文件显式加入任务inputs，避免仅素材变动才失效。DVC不提供用户审美认可、参考版权判断或防重复收费的通用保证。

### 2. LangGraph SQLite checkpoint：借鉴恢复谱系，不引入运行框架

真实仓库 [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)，固定commit `e539ac122f4126f6dd850581c1494948cf620e31`，2026-09-09提交，2026-09-13推送，未归档。已读[MIT许可证](https://github.com/langchain-ai/langgraph/blob/e539ac122f4126f6dd850581c1494948cf620e31/LICENSE)。

[SqliteSaver源码](https://github.com/langchain-ai/langgraph/blob/e539ac122f4126f6dd850581c1494948cf620e31/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py)实际建立WAL数据库，以thread_id/checkpoint_ns/checkpoint_id定位检查点，保留parent_checkpoint_id，另存task_id/idx区分的writes，提供get_tuple/put/put_writes。它是持久化能力，不是外部生成API的exactly-once承诺。

[依赖文件](https://github.com/langchain-ai/langgraph/blob/e539ac122f4126f6dd850581c1494948cf620e31/libs/checkpoint-sqlite/pyproject.toml)中checkpoint-sqlite版本3.1.1，Python>=3.10，依赖langgraph-checkpoint>=4.1.0,<5.0.0、aiosqlite>=0.20、sqlite-vec>=0.1.6。本地SQLite无需云服务密钥；平台可用性还取决于Python/SQLite与sqlite-vec原生包，未验证此机器安装。LangSmith或模型调用不是本地检查点必需条件，相关服务费用未启用。

**差异与决定：** 本地已有run_id、历史与remote_job，继续以PRODUCTION.json为权威。借鉴父子尝试关系和按任务定位恢复结果；恢复报告应首先展示原job和已有产物，再按实际结果更新，不能把失联当失败自动重复收费生成。若以后实测多进程账本规模成为问题，再评估SQLite迁移；当前不增加框架与数据库。

### 3. Playwright快照比较：借鉴基准/实际/差异证据，保留真实成片听审

真实仓库 [microsoft/playwright](https://github.com/microsoft/playwright)，固定commit `d1ead3ecca23182f2d06d761c28e3d4edafb6595`，2026-09-11提交/推送，未归档；[Apache-2.0许可证](https://github.com/microsoft/playwright/blob/d1ead3ecca23182f2d06d761c28e3d4edafb6595/LICENSE)已读。

已读[toMatchSnapshot源码](https://github.com/microsoft/playwright/blob/d1ead3ecca23182f2d06d761c28e3d4edafb6595/packages/playwright/src/matchers/toMatchSnapshot.ts)：区分expectedPath/actualPath/diffPath，将实际与差异作为附件，显式updateSnapshots模式可写基准，maxDiffPixels/maxDiffPixelRatio参与比较。[官方视觉比较文档](https://github.com/microsoft/playwright/blob/main/docs/src/test-snapshots-js.md)提醒基准与实际应使用同环境；该页是滚动文档，固定实现以commit为准。

[package.json](https://github.com/microsoft/playwright/blob/d1ead3ecca23182f2d06d761c28e3d4edafb6595/packages/playwright/package.json)是1.64.0-next，Node>=20，依赖同版playwright-core。它是开发分支快照，不能当稳定发布版安装建议。[当前安装文档](https://playwright.dev/docs/intro)列出Node 22/24/26与受支持Windows、macOS、Linux版本，以及浏览器二进制安装步骤。源码engine下限与官方测试支持范围须分开。本地浏览器/图片比较不要求云凭据；被测认证页面另需授权会话。本次没有运行浏览器或截图测试。

**差异与决定：** HyperFrames已有capture/check与实际MP4采样，不重复搭浏览器测试栈。借鉴基准manifest与对照附件：记录影片SHA、采样时间、画幅、工具版本、审批依据和比较结论。新角色按表演/字幕/混音/节奏维度对照，不能用跨画风像素相似度作审美评分。不存在认可基准时应报告“待认可候选”，不能自动创建一个看似通过的认可基准。

## 融合建议与验证边界

1. 继续使用现有素材服务、production_state.py、HyperFrames、配音和质检入口；新增轻量项目证据契约或校验器，不改变云端接口。
2. 将参考发现、实际看图、调用输入、文件指纹和角色版本连接起来；未知值明确unknown，不根据prompt文字推断实际输入过参考。
3. 配套任务输入列表与恢复说明；SHA变化只使相应下游失效。原远程job结果未知时保留该事实，不自动重发；产物存在仍要完整解码与身份确认。
4. 基准区分candidate/approved及审批来源，技术通过、模型视听审查、用户审美认可分开。真实成片覆盖与连续动作采样属于证据，不能由计数自动推出优秀。
5. 集成后最小验证应覆盖参考缺失/篡改、基准尚未认可、输入变化使下游失效、已有远程job禁止重复开始；采用现有测试框架，避免搭新套件。

当前实际验证仅包括公开API/原始源码下载与阅读、本地指定文件检查；没有运行三个候选、没有对其性能/恢复稳定性/画质作实测结论。未核验所有传递依赖许可证或全部平台原生兼容性。本报告仅借鉴设计思想；若后续复制源码或安装依赖，应固定具体版本、保留本次已收集许可证及上游必要署名，并在实际集成环境运行相应验证。
