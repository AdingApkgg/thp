# thp — 东方原作 Web 移植工作区

把东方 Project 原作 **TH06nc / TH12 / TH13 / TH14 / TH16 / TH17 / TH18 / TH19** 按「源码重建」路线移植到网页端，目标为完整 1:1 还原；目前仍在施工，尚未完成整作验收。

架构、协议和验收方法对齐 [touhou.vip](https://touhou.vip/)（[eagler-touhou](https://github.com/YomotsuHisami/eagler-touhou)）及其关联仓库。

## 为什么是「源码重建」而不是模拟器

touhou.vip 的每一部作品都是一个独立的 **可移植 C++ 重建 Runtime**，用 Emscripten 编译成 WASM，
通过 `eagler-touhou/1` 协议挂在共用的启动器上。它目前覆盖 th06–th11，因为这些作品有公开的重建仓库。

目标六作没有现成重建，所以本工作区从最近的一代模板（**th11 portable**，同为 ZUN 现代引擎 + SDL3/WebGL2）
分叉出 `runtimes/th12`，再逐模块按原版机器码重建。

## 目录

| 路径 | 内容 |
| --- | --- |
| `host/` | 启动器 / 联机大厅 / 游戏包与离线运行（来自 eagler-touhou） |
| `runtimes/th12/` | th12 Runtime（由 th11 portable 分叉，逐步替换为 th12 逻辑） |
| `runtimes/th13…th18/` | 其余五部，按同一模板推进 |
| `shared/eagler-common/` | 跨作品的联机 / 回滚 / 输入等共享运行时基础设施 |
| `tools/` | emsdk、thtk 数据工具、构建脚本 |
| `reference/` | 只读参考仓库（eagler-touhou、eagler-common、th06、th11、th12-decomp 等） |
| `docs/` | 架构、路线图、每部作品的移植计划与验收记录 |
| `artifacts/` | 构建产物（不提交） |

## 当前状态

当前仅推进 TH14，其他作品后置，进度表只标 TH14。最新核心修正六面符卡伤害除数、ECL 阶段计时读取及随全局倍率推进的关卡时钟。独立暖启动的六个分关共95,266次原版回调，30玩法字段和捕获对象窗口差0；视觉RNG差异保留。完整玩家录像在当前生产核心连续播放96,016帧后正常结束，无GameOver或未支持弹幕。连续活动帧对照保留五个关卡首帧pressed差异，750个加载回调单独保留；原版六面采样未达到请求预算，仍不是不间断原版整局通过或1:1。当前收据见[六面检查点](docs/porting/th14-zps-normal-six-stage-current-checkpoint-oct13.json)，详细范围见[发布说明](docs/GITHUB_RELEASE.md)、[核心记录](docs/porting/CORE_STATUS.md)和[方法调整](docs/porting/TH14_METHOD.md)。

## 素材与许可

本工作区**不包含**任何原版可执行文件、游戏数据、音乐、存档或录像。
运行需要你自己合法持有的游戏文件（如 `H:\Games\th\12\th12.exe` 与 `th12.dat`），
这些文件只在本机参与构建与对照，不会被打进站点资源包，也不会提交到仓库。

各 Runtime 的许可见对应目录；参考仓库的许可见其 `LICENSE`。

## 交接

想快速接手请先读 [`docs/HANDOVER.md`](docs/HANDOVER.md)：
它用一节讲清**现在到底有什么、没有什么**、六部通用的方法论（含已经踩中三次的反编译陷阱）、
**立刻可继续的工作清单**（含余下 7 条碰撞逐条的现状）、最大的风险（没有原版 oracle）、
以及**照抄即可**的重建与验证命令。逐轮决策现场见 `docs/th12/DELIVERY.md`。
