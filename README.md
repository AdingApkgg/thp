# thp — 东方原作 Web 移植工作区

TH14 启动顺序修正（2026-10-23）：按原版记录，将 ascii/text 的模板准备和启动上传改为 ascii → text。9 组延迟加载与自然标题到 Demo 的 1921 帧基线对照通过；原码检查已跑过 text 两个真实渲染目标。sig 完整启动流程、原版绘制与整作 1:1 仍未完成，静音预览保留旧模块。[修正范围](docs/porting/TH14_STARTUP_RESOURCE_ORDER_OCT23.md)、[验证摘要](docs/porting/th14-startup-resource-order-verified-oct23.json)。

TH14 当前修正（2026-10-23）：标题开始／回放请求在当帧动画完成后切换；结局按原回调顺序执行，快进重跑动画、淡入淡出及输入计数，完成后下一入口进入成绩页。两次普通按键自然通关、真实进度保存／读取及 30 份完整回放回归通过；回放与旧移植基线的 92,343,392 个所选状态字零差异。整作 1:1 仍未完成，只推进 TH14，预览静音。[修正范围](docs/porting/TH14_TITLE_ENDING_SCHEDULER_FIX_OCT21.md)、[新版完整回归](docs/porting/th14-title-ending-full-matrix-oct23.json)、[当前本机入口](docs/porting/TH14_LOCAL_WORKSPACE_CURRENT_SERVER.md)。

TH14 当前修正（2026-10-21）：补齐 Replay 自然 GameOver 菜单，修正暂停动画顺序、同帧恢复／续关及音效停住与恢复。三条长回放相对旧移植基线的 89,235 次回调前缀零差；原版菜单、普通恢复、自然续关和同帧再次失败组合均有独立验证，视觉 RNG 差异保留。整作 1:1 继续施工，只标 TH14。[本轮范围](docs/porting/TH14_REPLAY_END_SOUND_FIX_OCT21.md)、[证据摘要](docs/porting/th14-pause-replay-evidence-oct21.json)、[当前静音入口](docs/porting/TH14_LOCAL_WORKSPACE_CURRENT_SERVER.md)。

以下早期记录保留各自版本的范围，不自动继承为当前模块通过。

TH14 最新核验（2026-10-15）：原码已完成二面资源回调并请求 CRT 线程退出，随后记录到两个二面 Player 入口及主循环返回。`enemy.anm`／`st02enm.anm` 的 12,673 个选定字与当前核心零差，三个 ECL 包含文件的 44,040 字节独立核对零差。此次补充证据，生产游戏代码及 SDL 未改；实际并发、当前 C++ 整帧、GPU／音频及整作 1:1 继续核验。[范围与收据](docs/porting/TH14_STAGE2_CALLBACK_RETURN_OCT15.md)。

TH14 最新修正（2026-10-15）：后续关卡逐块上传，并只排入实际 ECL ANIM 列表，二面对照队列由 35 块改为 19 块，去掉 16 个重复块。43 项队列／纹理检查通过，背景模板等 531 个选定字与当前核心零差；新版 `78d3d19b…` 已在本机静音预览显示 Normal Demo。后续完整换关、原版异步时序与整作 1:1 仍待验证。[修正范围与证据](docs/porting/TH14_STAGE_TIMELINE_ANM_FIX_OCT15.md)。

TH14 最新修正（2026-10-15）：屏幕相机使用原版 FOV 和视口起点，四相机的 52 个参数字及 128 个矩阵字与本轮原码记录一致。新 SDL `3083772c…` 已在本机静音预览显示标题和 Normal Demo。[修正与验证范围](docs/porting/TH14_SCREEN_CAMERA_FIX_OCT15.md)、[当前进度](docs/porting/CORE_STATUS.md)。整作 1:1 继续施工，其他作品不占坑。

本机普通预览固定使用 `http://localhost:8208/`，音乐与音效静音；按[当前入口说明](docs/porting/TH14_LOCAL_WORKSPACE_CURRENT_SERVER.md)启动，已有服务运行时直接复用。旧命令、包及结果按对应日期保留。

下方 2026-10-14 的加载、整局及像素记录保留修改前版本范围，不自动作为本次相机修正的整局通过。

<!-- th14-staged-loader-current:start -->
## TH14 当前阶段 · 实际加载与四槽捕获（2026-10-14）

当前只推进 TH14，整作 1:1 未完成。加载生命周期已合入生产：267 个游戏核心文件、141 个 WASI 对象重新绑定并实跑，未继承私有 v2/v3 的整局通过结果。[本轮汇总检查点](docs/porting/th14-staged-loader-current-checkpoint-oct14.json)。

普通换关使用真实单调时间的 60ms 最小等待，按 HUD、Scene、新 Enemy owner、ECL 的顺序完成真实资源工作；SDL 队列执行实际上传。原 HUD result 的 120 与随后 transition 的 30 保留，60ms 等待与 HUD 更新重叠，不能再串行叠加一轮 120。内置四槽 capture 队列直接提供首槽状态，0 也表示 busy；DeferredEnd 在 postDraw 消费。完整 session 重置和直接换关替换先取消延迟 capture，普通 ANM clear 仍保留队列。复制成功才更新目标纹理 revision，ANM material cache 的 invalidate 继续保留。

| 新生产回放 | 物理回调 | 独立 Native 所选玩法字差 | 视觉 RNG 字差 |
| --- | ---: | ---: | ---: |
| 灵梦 A Lunatic | 90,793 | 10（非活跃加载期） | 181,570 |
| 灵梦 B Lunatic | 98,074 | 尚无对应完整 Native 基线 | 尚无对应完整 Native 基线 |
| 灵梦 A Extra | 39,458 | 0 | 78,916 |
| 咲夜 A Normal | 96,016 | 10（非活跃加载期） | 192,016 |

四份不可变输入均在当前无窗口生产核心结束，并重新通过不恢复错误的 ASAN／UBSan；测试明确注入 60Hz 单调时钟，在成功 draw 后执行无目标 capture 退役，不作为 Native 线程时间或实际 GPU 上传证明。Lunatic 新完整对象采集和另一份生产回放的 raw32 字节完全相同；65 项对象差异仍失败，包括 57 项非活跃加载期 enemyNextId 和 8 项活跃伤害区域 Z 原始字差。三处详细窗口位于四、五、六面，各 71 个活跃回调；其余所选玩法字段相同，但所有视觉字差与完整失败数组保留。Native 的 90,793 次采集预算不等于普通原版结局／完整终止。[本轮 raw32 与完整对象复算](docs/porting/th14-staged-loader-production-raw-evidence-verified-oct14.json)。

当前普通按键 Normal 重新执行 95,220 帧进入 e05，经过 3,737 帧结局／staff 和实际成绩、录像保存请求返回 Main。22,379 编码字节／149,076 解码字节与原版成绩 loader／writer 的完整编解码边界相同。此证明覆盖无窗口生产流程及编解码，未覆盖普通原版整局菜单／结局、Native 文件系统或浏览器 IndexedDB 持久化。[当前普通流程与成绩边界](docs/porting/th14-natural-storage-normal-sakuyaa-staged-loader-oct14-observed-oct14.json)。

延迟复制的独立浏览器候选实测 8 个完整缓冲，共 5,242,880 字节，与实际 original32 D3D9 HAL／D3DX 输出及修改前 WebGL 输出均零差；另有 null resource、null texture 与明确标注的 false-return adapter 三组退役控制。输入是声明的合成后缓冲，使用真实 text52 的 512×512 RGB565 目标与矩形／格式控制；不是完整游戏帧、全部格式、实际 GL 错误／HRESULT 映射或音频等价证明。当前 helper 与已测候选逐字节一致。[独立复制像素及成功 dirty 证据](docs/porting/th14-deferred-capture-success-dirty-verified-oct14.json)。

最终正式 SDL 为 1,890,810 字节，SHA-256 `64b46da7c4aa1af2426d024c176e8c77b9ecae5a3da13a1eeea6c648ee82ca54`，146 源码／149 头文件绑定。本机预览固定 `8208`，HTML 使用独立静音适配；发布包音频逻辑不变。最终 64b46 模块的完整浏览器流程和持久化仍待验证，旧版短录像保存／播放证据保持历史版本，不能继承为本轮通过。[本机固定预览说明](docs/porting/TH14_WORKSPACE_SERVER.md)。全部自机／难度、普通原版完整流程、图像／音频、浏览器持久化与剩余加载差异继续验收；`completeGame=false`、`nativeEquivalent=false` 保持。
<!-- th14-staged-loader-current:end -->

<!-- th14-staged-capture-browser-scope -->
后续在同一核心上修正了启动器更新通知早于 state 初始化的问题，并重建启动器包。固定浏览器地址使用 `http://localhost:8208/`，音乐和音效默认静音；127.0.0.1 和其他端口属于不同存储来源，后续不混用。当前地址通过普通游戏菜单保存了新录像 A，完整刷新后仍可见；选择一面后完成 6 项资源上传并观察到自动返回列表。日志报告该录像 1,240 字节，未导出其字节或测量播放帧数，不能推断完整存储、全部模式或整作 1:1。历史初始化错误完整保留，新启动窗口无新增错误。[修复及回归](docs/porting/th14-launcher-state-initialization-verified-oct14.json)、[本次浏览器观察](docs/porting/th14-staged-capture-browser-post-statefix-observed-oct14.json)、[当前本机预览入口](docs/porting/TH14_LOCAL_WORKSPACE_CURRENT_SERVER.md)。

<!-- th14-local-quiet-diagnostics-oct14 -->
本机诊断沿用 `http://localhost:8208/` 并默认静音，固定清单入口只开放当前实验的有限读写路径，保留现有存档。实际 Color21／UV23 观察取得每模式 70 份 shader 转译字符串；44 个输出哈希与此前物理采样相同，颜色仍有 880 个通道差异，7 组原版完整 UV 缓冲仍有 5,292 个字差、覆盖差异 0。转译字符串不是最终 DXBC／硬件指令，不能据此认定运算融合或像素舍入原因。[实际 shader 观察](docs/porting/th14-stage-angle-shaders-observed-oct14.json)。

实际音频混音器在私有无声接口中完成 15 组原版整数命令对照，整块／分块与队列／直接命令共 245,760 个比较字一致，未调用播放输出。12 组独立声像／音量规范控制中有 4 组浮点字差，最大绝对误差约 `2.98e-8`，失败结果保留；此处没有原版 DirectSound PCM 对照。[无声内存采样](docs/porting/th14-audio-offline-pcm-observed-oct14.json)。整作 `completeGame=false`、`nativeEquivalent=false` 继续保持。


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

## 历史状态 · 本轮前的矩阵组合与暂停检查点

当前仅推进TH14，进度表只标TH14。已合入原版矩阵组合／半像素修正和对话暂停截图来源修正；实际21个颜色缓冲差由3,887通道降至880，23个UV样本中20个完整hash一致，失败完整保留。游戏核心265文件未变，四份完整输入、ASAN及普通流程证据仅在该核心范围复用；新版浏览器旧录像自动播放已重验。加载生命周期、全部模式、图像／音频与整作1:1继续施工。详见[当前检查点](docs/porting/th14-clip-pause-current-checkpoint-oct14.json)、[发布说明](docs/GITHUB_RELEASE.md)和[加载实施清单](docs/porting/TH14_STAGED_LOADER_MINIMUM_IMPLEMENTATION.md)。

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
