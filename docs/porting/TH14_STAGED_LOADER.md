# TH14 换面加载的最小状态与验证边界

2026-10-14：这是实现前设计；当前生产没有新增 loader、时钟或 owner 生命周期。不能用固定五/六次回调、复制原版计数，或编造线程完成时间消除加载差异。

当前关键差异已有[受控原码对照](th14-staged-loader-owner-boundary-observed-oct14.json)：原版完整 `4226c0` 在声明的空敌列表/已解绑回调前提下执行退役，`422821` 清 `4db544`；可观察 owner/nextId 为缺席/0，玩法 RNG 仍为 seed49408、calls66446。生产实际 `EnemyManager::reset(empty)` 保持 `commands.manager`、敌列表发布指针和 nextId1。因此 reset 不能兼任退役。这是两个不同 API 的生命周期差异，不是完整游戏对照。原码执行仅控制一个自有 ECL块的 CRT free；没有模拟 game callback、时间或实际原版进程。

下一轮独立的[构造发布前缀证据](th14-staged-loader-owner-publication-boundary-observed-oct14.json)执行原版构造前缀：`4228de` 发布 owner，`4228e4` 保留 nextId1，然后才在 `4228fa` 调 `422340` 载入 ECL。前一份已发布退役报告、工具和私有fixture/native/WASM均保持原字节。**owner 存在、ECL完成、GPU完成是三个状态**；不能把 owner 创建推迟到所有 ECL/GPU工作完成。

## 状态及事件

| 状态 | 进入动作 | 离开条件 |
|---|---|---|
| 退役 | 保存 next stage/header；清旧敌与目标引用，解除 owner 发布；冻结 controller clock。玩家与全局 RNG 保留。 | 延迟屏幕复制队列首槽已空；这与旧 ANM引用及资源上传完成无关。 |
| 等待 | 在上述确认时刻记录单调时钟 deadline=now+60,000,000ns。 | now达到deadline；不是回调次数达到某值。 |
| Replay 初始化 | 原版 `456050` 语义一次性生效：回放双 seed/玩法 calls0/28个全局字；普通录制在此采集 seed、创建下一关 header并清 calls。 | 初始化成功；然后执行 HUD/Stage加载任务。 |
| 新敌 owner | HUD/Stage对应的实际工作完成后，先发布空 owner、nextId1，再执行 ECL及其 ANM加载任务。 | CPU解析、必要GPU准备与资源绑定完成。 |
| 结算与交叠 | 保留 HUD result timer120阈值；新资源已就绪才能启动 incoming Stage objects。 | 原有 transition timer30阈值。 |
| 激活 | `455ed0`对应的位置/输入恢复、玩家 shot pool reset、根 ECL等激活动作。 | 回到正常关卡执行。 |

原版链的字节/IAT及完整连续采样见[加载证据](th14-loading-lifecycle-verified-oct14.json)：请求12先把 `4d9658` 清零；worker在 ANMmanager `+20`等待结束后执行条件 `Sleep(60)`，之后 `435f32→456050`，再 `435f66→4228a0`。那份录像的五个等待回调是采样结果；owner出现又分别晚15/13/10/15/19个回调，均不能成为生产常数。

[96项原码分支测试](th14-staged-loader-wait-predicate-verified-oct14.json)进一步证实 `[*(4f56cc)+20]` 必须按有符号32位解释：**严格小于0才离开wait；0也继续等待**。等待期间 `4d9684 & 0x180` 转到abort，否则先请求Sleep1；负值后只有 `4d9658==0` 请求Sleep60。测试在所有Sleep/abort调用前停止，未执行或模拟Sleep；worker入口和recheck是各自声明状态的独立分支，不生成线程时间。该份历史报告只证明分支；字段含义由下一份证据独立补齐。

[真实 writer 与消费者证据](th14-staged-loader-capture-queue-verified-oct14.json)现在证明 `+20` 是四槽延迟屏幕复制队列**首槽的 ANM 文件索引**，不是引用计数、任务数或通用 GPU fence。构造 `47a958/47a95f/47a966/47a96d` 将 `20/48/70/98` 设为 -1。完整 `44bdd0` 扫描负索引空槽，再于 `44bdf5` 发布 file slot；后九字是 texture slot 与目标/源矩形。完整四槽消费者 `4690d0` 用该 file/texture索引取目标纹理，把 Supervisor `+1b4` 屏幕表面通过 `D3DXLoadSurfaceFromSurface` 复制进去；`4691d1` 将索引置回 -1。目标纹理不存在或取表面失败同样退役。18项入队、5项空目标消费、2项独立错误分支及真实消费前后 wait前缀均执行原码，零 host/game call shim。worker**只检查首槽**；首槽为空、后三槽仍有请求也会继续，不能加强成全队列为空。

消费者来自渲染循环 `46ab70→4690d0`；调用链在 draw queue `4013b0` 与 ANM flush之后。它表示捕获请求已处理/退役，不证明 GPU硬件完成。当前SDL `Application.cpp` 在 session.update后、session.draw前处理 `PauseMenu::capture_requested`，只有一个 bool，尚未把此四槽状态发布给核心；这个事件接点与实际解析/上传完成必须分开。

## 最小接口

核心的 `request_next_stage(stage, header, now_ns)` 只建立 pending job并启动退役，不能立即 restore、换资源或建立 nextId1。`pump_next_stage(now_ns, progress)` 每次正常 update调用，接收首捕获槽退役、CPU任务完成、GPU准备完成和错误事件；核心只推进合法状态。无待捕获首槽时可直接进入60ms等待，不能为加载另造一个捕获请求。pending资源使用稳定 `unique_ptr<StageResources>`，旧背景由 outgoing/previous owner继续持有。

`EnemyManager` 可保持当前值对象，新增逻辑 `retire()` 与 `initialize(EclProgram&)`：前者解除 `commands.manager`、`th14_enemy_list`并使 owner缺席；后者在新构造边界重新发布及保留ID0。`PlayerMotion::enemy_manager`必须取 owner存在状态，不能恒真或根据观察窗口掩码。ECL执行仍受 stage-active/回调启用状态限制。

SDL在 update前用 `SDL_GetTicksNS()`供给纳秒。WASI实际宿主用 `CLOCK_MONOTONIC`；确定性单元可明确注入受控单调时间并标作测试，不能称为原版线程时间。post-render `sample_spell_clock`及当前 fixture的 frame/60负责另一种时间语义，不可默认为真实 loader时钟。

CPU工作完成来自实际解析返回；GPU准备完成来自上传队列与资源准备返回。原版先建立 owner再解析 ECL，当前单体 `GameResources::load_stage`需要按 STD/Stage、ECL、其 ANM等实际依赖拆任务，不能让当前 `stage_ready()==boot_uploads.empty()`同时代表全部边界。捕获首槽只在实际渲染复制操作返回、空目标或明确失败处理时退役；SDL/WebGL不能把它等同上传队列为空，也不需凭空增加GPU硬件 fence。无渲染的 WASI应明确采用无捕获目标的真实空目标消费路径，并保留事件记录；不能按回调数虚构完成。没有捕获请求则首槽本来就空。60ms等待仍独立生效。

## 回调与接点

加载是 `GameBattle`内的子状态，Session继续 stage update。overlay ANM8、Replay12、仍注册的 Stage13、score17、Player18和普通 ANM29按自身启用条件继续；controller11被调用但走加载分支，不推进控制 clock及其控制动作。HUD结算保持原timer规则。Enemy21在 owner缺席时不执行；Bomb20、laser22、bullet23、item24、spell26、dialogue27与HUD28应保持原版注册/启用规则，不应因“加载”一律暂停或一律强开。尚未独立证明的 callback flags需要单独核实。

具体拆点是 `GameSession.cpp`的 NextStage块、`GameBattle::next_stage/enter_stage_transition/stage_control`、`GameSessionResources::load_stage/prepare_stage`及SDL上传分支。当前 Session loading直接退出 update；`Application.cpp`上传分支直接更新两遍ANM并 return。这两处不能承接已有 battle的换面：应泵一次真实GPU任务后继续正常 update/draw，不重复ANM。初次无 battle加载可继续使用现有路径。

120/30规则不能在CPU/GPU完成时重置或加等待帧。如果资源未准备好，只保持未激活；不能为了重放旧录像时序强行创建资源。原版 `+20` 已映射到捕获队列首槽，`renderer.flush()`只是复制前的操作，不能自行将请求退役；当前宿主需提供捕获处理结果与单调时钟，不能靠 `boot_uploads.empty()`代替。

## 后续验证

已通过的受控原码语义是退役时全局RNG存活、新 owner发布先于ECL加载、首捕获槽写入/消费/wait，以及既有 `456050` seed/计数写入顺序。下一步应核实回调启用规则、普通录制的初始化顺序与clock deadline状态测试，再实施生命周期拆分。之后重跑四份独立输入、ASAN、普通录制/回放与存档codec，完整保留重复clock和所有加载回调。

受控单元不证明线程调度、实际heap/显卡完成、普通原版结局或整作1:1；旧连续原版基线也没有 worker事件时间戳。实现后仍可能存在合理的宿主调度差异，必须报告，不能据此修改或删除原版观测。
