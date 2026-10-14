# TH14 加载器的捕获源、调用者与最小接点

2026-10-14，实现前审计。生产 C++ 与先前已绑定证据均未改动。独立工具及受控输入见 [host-boundary 原码证据](th14-staged-loader-host-boundary-verified-oct14.json)。它逐区域核验已有原版快照的318,083,072字节与context，读取真实63个draw注册；不启动原版子进程，也不模拟GPU/线程时间。

## 表面身份与绘制时点分别成立

| 原版字段 | 原版创建入口 | 当前宿主对应角色 |
|---|---|---|
| Supervisor `+1ac` | `447525/44752b` 对 text.anm texture2 调 GetSurfaceLevel | `graphics.texture(core.text,2)` 的中间RT |
| Supervisor `+1b0` | `44753a/447549` 对 text.anm texture3 调 GetSurfaceLevel | `graphics.texture(core.text,3)` 的中间RT |
| Supervisor `+1b4`，即 `4d9114` | `447513` 对 device 调 GetBackBuffer(0,0,0,out) | `GraphicsDevice::screen` 的呈现目标角色 |

快照中三个表面非空、句柄各异；GetBackBuffer方法落在原来加载的d3d9.dll。三段实际原码前缀分别停止在COM调用前，核对输出地址与实参。`GraphicsDevice::select_target(nullptr,...)` 选择screen，`present()`呈现screen；SceneCompositor在draw优先级52切到该目标，53绘制第四个copy，之后还绘制24..29/34/35等层与ASCII，最后74 End。**screen是最终backbuffer角色，不能因此断言任意时刻其像素相同。**

原版延迟消费者 `4690d0` 由 `46ab70` 的首调用进入；主绘制 `4013b0`、flush和EndScene之后才进入该段。当前Application的单一capture bool在 `session.update`之后、`session.draw`之前消费，取的是上一次完成绘制留下的screen；对延迟结束捕获而言，这不是原版同一绘制边界。没有原版/生产framebuffer对照，不能进一步声称像素相同或不同多少。

## 两类capture不能合并成一个postDraw动作

**普通暂停**：`448bf0` 创建text script52后直接在 `448d6a` 调 `47e070` 复制，不调用队列 `44bdd0`。因此“所有Pause都应移到postDraw”是不正确的。原版它属于当前update阶段的即时捕获：

- `*(4db550)+194==0`：取 `4d9114` backbuffer；1倍源RECT为 `[32,16,416,464]`。
- `*(4db550)+194!=0`：该字段是已有对话指针，取 `4d9110` text texture3中间RT；1倍源RECT为 `[128,16,512,464]`，避开最终画面上的对话层。

六项原码前缀使用有/无对话、倍率1/1.5/2，尺寸各异的目标sprite，严格核对源表面/源RECT/目标RECT和四槽保持空。当前 `capture_requested` 的无对话普通Pause来源与update/draw相对顺序可对应；对话分支仍缺选中间RT。它对所有调用者的通用bool也缺捕获类型，不能因为普通Pause使用正确边界就证明结束捕获正确。

**结束类菜单**：全 `.text` 每字节扫描相对call到目标地址，证明 `44bdd0` 唯一直接调用者是 `44be96`；`44be40` 只有 `44a080`、`44b220` 两处直接调用。前者在 `449f20` 的普通结束入口创建script52，且flags `4f58b8 & 0x30` 必须为0；后者是菜单更新内80帧门槛的另一条捕获路径。它们将file/texture与RECT入四槽队列，由postDraw消费者复制**backbuffer**。未发现这两个函数地址作为固定函数指针嵌入PE；这是原码静态调用者证据，不是对所有可能动态执行的形式化证明。

先前 [capture-queue报告](th14-staged-loader-capture-queue-verified-oct14.json) 的recordFields source/target标签写反：队列字2..5是**源**x/y/width/height，字6..9是**目标**x/y/width/height。`469182` 将前者push为D3DX第6参数srcRECT，`46918e` 将后者push为第3参数dstRECT。该报告的原字节入队、退役和wait测试均不变；新证据显式记载勘误，旧文件保持不可变。

## 普通NextStage的wait接点

五项实际 `43726e..437296` 前缀证明：stage1..5只请求Supervisor12、递增stage并更新StageFiles行指针，**不建立capture请求**，原四槽不变。已找到的所有普通队列入口属于结束类菜单；没有证据允许给普通换面另造截图任务。

NextStage应读取**现存首槽**的signed file index，负值就越过1ms轮询。请求12在 `446a99` 清 `4d9658`，所以正常换面随后请求60ms。首槽未退役才等待现有捕获消费者事件；不能等待所有槽、上传队列、旧ANM引用或GPU硬件fence。这条队列消费是复制请求处理返回，空目标与错误也退役，未证明物理显卡工作已结束。

已有快照只记录首次Player边界四槽空，90793连续回调采样没有四槽/worker时间戳。因此这里没有新称“普通完整换面全过程copy队列已观察”。普通NextStage不主动入队由具体原码请求/调用者证明；旧动态时间差仍保留。

最小事件是 `capture_first_slot_free`，由共享请求状态得出，而非 `renderer.flush()`返回值。即时Pause无需占用延迟队列；延迟结束请求在实际postDraw复制返回或空目标/错误处理后退役。没有请求时自然为空，不额外等待一帧。headless无图形目标必须走明确空目标处理，并记录实际请求/退役，不能模拟NativeGPU返回或加固定帧数。

## Worker顺序要求的最小拆分

这条换面worker的顺序是：

1. 首capture槽空，再条件Sleep60。
2. `435b3a→46fe50` 对加载ANM做实际更新；它在Replay重置seed之前，不能将这些ANM模板/更新随意挪到新seed之后。
3. `435f32→456050` 初始化下一关Replay/live header、双seed与玩法calls0。新工具实际执行该调用和完整原函数，再停在下一次HUD调用前；seed写入地址/顺序与既有独立单元一致。
4. `435f3d→42eb30` HUD stage refresh；`435f4b→40d8a0` 载入/构造新Stage。
5. `435f66→4228a0` 新EnemyManager构造，`4228de`先发布owner，`4228e4`保留nextId1，然后 `4228fa→422340` 才解析ECL与其ANM。
6. 之后仍按原controller/HUD120/transition30规则激活；owner存在、Stage构造、ECL/GPU准备、激活不是同一事件。

当前 `GameResources::load_stage` 将STD/背景/logo/enemy、ECL/includes ANM、MSG/boss ECL混成一调用；`GameSessionResources::load_stage` 再一并prepare/swap。`GameBattle::next_stage` 完成这些工作后才 `enter_stage_transition`，后者才reset enemy、建立incoming Stage。它无法表示“旧enemy已退役→等待→Replay初始化→新Stage→新空enemy owner→ECL”。仅往目前整块调用前面加60ms，还会继续把owner与资源解析顺序放错。

最小可落地闭环按两个生产改动边界组织，不能把所有既有capturing/渲染重写塞入加载器：

- 核心增加独立 `NextStageLoad` 状态：请求时一次性保存header/关卡、退役并解除旧enemy发布，保留Player/RNG与旧背景；记录无capture时首槽为空。用update前供给的单调ns启动60ms deadline。不得立即restore/清calls，或将Session转成会跳过Player/HUD的整局loading phase。loader是battle内子状态，controller动作/clock按原flag冻结，已有其他回调按自身启用条件继续。
- 拆 `load_stage_scene` 与 `load_stage_timeline`，沿用稳定pending `unique_ptr<StageResources>` 与既有真实GPU队列。deadline后先Replay/live初始化、HUD刷新、STD/背景准备与incoming Stage构造；再 `EnemyManager::initialize_empty()`发布nextId1，随后真实ECL/ANM解析/准备并绑定。`retire()`须解除 `commands.manager`/环境列表发布，PlayerMotion的enemy-owner判据取逻辑owner状态。WASI同步解析/空图形准备可当次返回；SDL按实际任务完成发事件，不能批量早建owner或用模板未完状态执行ECL。

共享C++值对象可以保留；无需先改成整个EnemyManager的unique_ptr。需要将当前 `reset(EclProgram&)` 拆出退役、空owner初始化与ECL绑定；旧Stage继续注册/更新直至新Stage构造接管，不因提前设置transitioning而误停旧背景。HUD result timer不能在任何资源完成事件重置。已有SDL上传分支对于有battle的换面应泵真实任务后继续正常update/draw，不能double-update ANM并return整个frame。

capture类型/对话源与postDraw结束消费可作为独立小改动：`ImmediatePause`保留update时即时处理并按对话选择screen/text texture3；`DeferredEnd`交给draw后队列，向loader发布首槽实际状态。普通换面不需要新capture，不能让尚未移植的截图器成为人工延迟来源。

以上还需独立核实具体callback启用flags与普通录制header采集顺序；旧报告已提供原456050两分支的初始化指令。最小闭环完成后再运行真实普通输入、四份不可变回放、原版counter/nextId不掩码比较与ASAN。它不承诺复刻OS线程调度，或把这份录像的五个loading回调固化为生产规则。
