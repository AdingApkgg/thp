# TH14 换面加载：冻结后的最小核心改动

2026-10-14，只读实施清单。当前正式SDL/浏览器检查点尚在冻结；未修改核心C++。新增 [差异映射](th14-staged-loader-current-gap-map-verified-oct14.json) 重算全部90793对raw32，并保留已独立核验的所有object差异；捕获语义和源码接点详见 [宿主边界审计](TH14_STAGED_LOADER_HOST_BOUNDARY.md)。

## 当前差异与边界

| incoming stage | 第一inactive callback | 原版calls仍未清零的区间 | 原版owner缺席的区间 | 新owner首次可见 |
|---|---:|---|---|---:|
| 2 | 9729 | 9729..9733，5条 | 9729..9743，15条 | 9744 |
| 3 | 21908 | 21908..21912，5条 | 21908..21920，13条 | 21921 |
| 4 | 35004 | 35004..35008，5条 | 35004..35013，10条 | 35014 |
| 5 | 52777 | 52777..52781，5条 | 52777..52791，15条 | 52792 |
| 6 | 69201 | 69201..69205，5条 | 69201..69219，19条 | 69220 |

25条calls差中，当前生产已经为0，原版保留上关计数；72条nextId差中，当前生产已经为1，原版global owner为空所以读取0。生产即刻restore/reset和过早发布owner分别解释这两组差异。**表中的回调索引和长度只用于诊断，不能成为等待常量。** 原版Stage/纹理/ECL载入耗时与宿主不同；修正逻辑顺序后也不能承诺录制线程时序完全相同。其他8条active damage-area与181570条visual RNG差仍独立保留。

## 最小状态机

| 状态/事件 | 原版地址 | 核心动作/离开条件 |
|---|---|---|
| Request | `43726e` request12，`446a99`清initial flag | 保存incoming编号/header，只解析header；旧owner真实退役，保持Player/RNG/旧背景。此请求不造capture。 |
| WaitCapture | `435acf/435af9` | 检查现存**首槽**signed file index；负值直接离开。0也busy，不能检查“所有槽空”。busy且Supervisor `4d9684 & 0x180`才走abort；负值绕过这处abort检查。 |
| WaitMinimum | `435b04..435b0f` | 正常request12令initial flag为0，因此建立真实单调now+60ms deadline。原版Sleep60本身不轮询中断；不要据此编造逐帧abort或5次callback。 |
| EnterWork | `435b11/435b2a/435b3a` | **Supervisor+1bc，即SceneCompositor.copy0** pending interrupt2并实际更新一次；它在seed初始化前。它不是ASCII17加载指示器。 |
| InitializeHeader | `435f32→456050` | 回放restore双seed与28个globals，清玩法calls；普通录制在此采集seed/创建下关header/清calls。ANM RNG calls不由此清零。 |
| PrepareHud | `435f3d→42eb30` | 首先载入logo ANM slot6、当前角色MSG，准备模板/图形并刷新HUD stage字段。 |
| PrepareScene | `435f4b→40d8a0` | STD/背景与incoming Stage完成；旧背景保持稳定owner。 |
| PublishEnemy | `435f66→4228a0`，`4228de/4228e4` | 发布真实空enemy owner与nextId1；此刻ECL尚未解析。 |
| PrepareTimeline | `4228fa→422340` | 解析ECL/includes及ANM、完成真实准备/绑定。 |
| Ready/Activate | `436a40→455ed0/456170` | 原HUD result120及transition30、位置/输入/shot池恢复、root ECL激活。不要把“GPU准备完”当作立即激活。 |

原版 `42eb30` 开头 `42eb3d→47d090` 从stage row `+2c`载入logo slot6；之后读取/复用GUI `+198` MSG。当前“先整包解析，再统一准备”需要拆开，不能在新Enemy owner发布前就完成timeline ANM模板执行。ASCII17的begin与finish/interrupt1仍是独立加载指示事件；不能拿它替代copy0的interrupt2。

## 具体文件与API拆点

`GameSession.cpp` NextStage块现在立刻执行 `recording_seed/calls0` 或 `replay_entry.restore`，再调用battle->next_stage。改为存 `pending_entry`/incoming编号，并调用 `GameBattle::request_next_stage`；restore/录制采集在InitializeHeader事件做一次。header解析、RNG初始化、输入流/位置激活分开，不能先切下一关输入并假设这等同456050；既有455ed0/456170证据用于激活边界。

`EnemyManager.cpp` 最小可保留值对象，增加 `retire()` 和 `initialize_empty(EclProgram&)`。retire必须实际销毁entries/清目标引用，解除 `commands.manager` 与 `environment.th14_enemy_list` 发布，使总创建号为0；不能只把观察getter改成0。initialize_empty先reset字段/保留ID0、发布manager与list、total_created1，再允许load_ecl填充那个稳定EclProgram。`owner_present()`可直接由实际发布指针判定；不需要另造与发布脱节的bool。`GameBattle.cpp` 当前movement.enemy_manager恒真要取实际owner；Enemy21只在owner与其callback启用条件满足时执行，Player18继续按自身规则运行。

`GameResources.cpp` 将TH14 `load_stage`拆成三个有实际工作的phase，例如 `load_stage_hud(number,StageResources&)`（logo/MSG）、`load_stage_scene(...)`（STD/背景）、`load_stage_timeline(...)`（ECL/includes ANM）。现shared enemy ANM和其他title兼容包装需明确归属，不能新增未证明的ANM重准备。各函数只返回真实工作成功/失败；不能每phase固定占N帧。原非TH14整包wrapper可保留原行为，不改变其他作品时序。

`GameSessionResources.cpp/.hpp` 保存稳定pending `unique_ptr<StageResources>`，分开scene与timeline prepare/readiness，旧资源至outgoing背景结束才释放。不要在timeline parse/GPU准备之前就丢失pending对象地址；新enemy program指向pending.timeline，发布后再填充。`StageResourceEffects`最少区分HUD/scene与timeline工作的实际完成，不再让一个 `stage_ready()==boot_uploads.empty()`承载全部生命周期。

`GameBattle.cpp/.hpp` 增加独立 `NextStageLoad` 子状态与 `pump_next_stage(now_ns,capture_first_slot_free)`，不要立刻设置会冻结旧Stage更新的transitioning。请求只做一次退役；controller的动作/clock走loading分支，旧Stage/background及Player/HUD按原启用规则继续。incoming Stage建立后才接现有outgoing/incoming结构；不要重置HUD result timer。当前 `enter_stage_transition` 大块至少拆出旧owner退役、HUD/Stage建立、空新owner发布、timeline绑定；其reset/Stage/HUD先后需要按上表安排。

`Application.cpp` update前用 `SDL_GetTicksNS()`供给clock；普通NextStage首capture槽自然空，不新增截图任务。现有battle的上传分支泵真实job后继续通常update/draw，不能double-update ANM然后return整帧。初次无battle的boot路径另保留。WASI由宿主 `CLOCK_MONOTONIC`供给真实时间；受控单元可显式注入单调时间，但必须标为测试clock，不能称为原版线程时间。

ImmediatePause当前已独立修复对话时取text texture3，继续在draw前；DeferredEnd的四槽postDraw消费仍是后续独立边界。loader接受现存首槽状态，不可以 `renderer.flush`、普通Pause capture bool或上传队列来代替。

## 冻结后实施与验证顺序

先实施owner实际退役/发布与可测试loader状态、clock deadline/abort/错误收尾；再按HUD/scene/timeline实际工作拆资源并接已有SDL队列。两步都不得改原版状态、输入或屏蔽inactive callbacks。单元验证最少覆盖首槽0/负数、busy时0x180 abort、initial flag1不请求60ms、deadline前/后只初始化一次、scene pending时owner缺席、ECL pending时owner已经nextId1、失败时不会继续activate，以及Player/HUD/旧Stage不被整体停更。

之后才重新跑四份不可变回放、普通录制/回放/score codec与ASAN，按实际callback完整输出calls/nextId与所有失败。若有宿主调度差异，需要用真实clock/任务事件记录解释，不修改report getter或复刻表中窗口来消除差异。当前未实施核心修正，未证明整作1:1。
