# TH14 私有加载原型，2026-10-14

本轮仅在 `artifacts/th14/staged-loader-prototype-oct14/` 编译私有源码副本。生产 265 个文件、140 个链接用共享对象前后 SHA 相同；没有合入 `GameSession` / `GameBattle`，没有生产回放、浏览器或 ASAN 通过声明。最终验证见 `th14-staged-loader-private-events-prototype-verified-oct14.json`。

## 可分段合入的内容

1. `owner-lifecycle.patch` 仅增加 TH14 的 `EnemyManager::retire()`、`initialize_empty(EclProgram&)` 和只读 owner/timeline 访问器，不改对象布局。`reset()` 的旧行为和其他 title 的 wrapper 保留。退役用真实 `destroy()` 清空链表、脚本线程和 shot target，再取消 `commands.manager`、`environment.th14_enemy_list` 的发布并将可观察 nextId 置零。空 owner 初始化绑定稳定的 pending timeline，恢复发布并保留 ID0。
2. `loader-state.patch` 增加独立状态接口：`WaitCapture -> WaitMinimum -> Hud -> Scene -> Timeline -> Ready`，另有失败和中止状态。它仍在 `th11::prototype` 命名空间，尚需正式接口命名和调用者合入。`StageActions` 分别提供真实工作事件；同次 pump 可完成多个已就绪阶段，不设置每阶段帧数。
3. `fixture-v4.cpp` 是验证夹具，不是生产代码。它用真实 `SceneCompositor::stage_start()`、原版 ASCII/text ANM 和真实 `ReplayStageState::restore()` 实施一次 copy0 label2 → replay 初始化；用真实 `EclProgram::load()` 解析原版 stage2/includes；HUD/STD/GPU 的完成仍由明确声明的测试事件提供。

原版边界对应：`422821` 退役全局 owner，`4228de/4228e4` 在 ECL `422340` 调用前发布 owner/nextId1；`435acf` 检查首个 copy slot 的有符号 index，等待时 `flags&0x180` 中止，负数越过这一检查；`435b0d` 在非初次加载请求 Sleep60；`435b3a` 执行 detached copy0 的 label2，然后 `435f32` 进入 replay 初始化。原始原码执行报告与原 EXE 均绑定于最终报告，未重写已发布证据。

## 已跑验证

- 48 个原版 worker-entry 受控分支，与私有 phase/初始化边界逐例比较；原报告的另外 48 个 recheck 分支继续作为独立证据保留，没有伪造 Sleep 返回连接它们。
- 首 slot 为0时等待；变负后才开始60,000,000ns deadline；deadline 前一纳秒不初始化，达到 deadline 初始化一次。等待时中止、负 slot 跳过该中止检查、时钟回退、deadline 溢出、重复 request 和 HUD/Scene/Timeline 失败均保留真实断言。
- 独立一次用实际 WASI `CLOCK_MONOTONIC` 及宿主定时器，实测 elapsed >=60ms，不将此时长伪称原版线程时间。
- 真实敌人 spawn/destroy/retire 清除链、target、发布指针和 counter。使用一个未来时间的受控 ECL 子程序、空真实 ANM manager、明确零碰撞/零伤害 world；未证明原版 live enemy 退役全过程。
- pending `StageResources` 的 timeline 在发布和 `unique_ptr` 所有权移动后地址相同；ECL 解析发生在空 owner 发布之后。
- 原版 ANM 的真实 copy0 初始化在等待边界前无变化，边界执行一次，后续 pump 不重复；未比较 Native copy0 VM/GPU 输出。
- Title12、13、16 的私有 owner 对象编译通过。没有完整其他 title 回归声明。

前两种夹具错误及一次缺少碰撞/动画依赖的失败都留档：WASM memory grow 后错误使用旧 ArrayBuffer；合成子程序遗漏 ECLH 前缀；有效 ECL 但缺少 EnemyFrame 依赖。失败日志、旧 fixture/WASM 的 SHA 在最终报告中保留，没有改输入掩盖差异。

## 正式整合的最小接点

`GameSession.cpp` 的 TH14 `NextStage` 路径先保存稳定的请求/header 所有权，移除该处立即 seed/calls 初始化。初次 start、其他 title 保持旧 wrapper。`GameBattle::next_stage()` 发起退役和 pending 分配；旧 transition120/30、player/HUD/old scene 回调继续执行。只有 enemy manager 的实际 owner 存在时才调它的 update，trace 的 owner/nextId 从发布指针读取，不能只改显示字段。

`GameResources::load_stage()` / `GameSessionResources::load_stage()` 需要分为 HUD logo/MSG、scene STD/background、timeline ECL/includes/ANM 三段。先 HUD，再 scene，再绑定 pending timeline 的空 owner，最后 ECL 工作与 GPU readiness。`StageResources` 必须由 `unique_ptr` 固定地址；不得给 manager 绑定栈上或可搬动的 `EclProgram`。这个拆分尚未实现，当前 prototype 的 HUD/scene gates 不应直接合入假完成状态。

当前 port 没有对应原版 ANM copy 队列的四个 index。首 slot 必须由真实 capture 请求登记及该 copy 的完成/失败退役来驱动；普通 NextStage 本身不创建这一请求。不得用 `flush()`、一般 boot upload 空队列或所有 slot 空代替原版首 slot 条件。DeferredEnd 的 post-draw copy 尚未整合，普通 pause 的 before-draw copy 不迁移。相关源表面和矩形由 host-boundary 报告明确区分。

WASI/SDL 调用者将真实单调时间传给 pump；它们将解析任务和图形准备的实际完成传给 `StageActions`。SDL 若 worker 解析，GPU 操作仍由主线程接收完成事件；WASI 当前同步 parse wrapper 需要先拆开再表达完成，不能随机生成原版 worker 时间。所有宿主延迟会改变 loading callbacks 的数量，此原型证明事件顺序与最低等待合同，不保证固定原版录像的 25 RNG/72 nextId 差异立即逐帧消失。

正式合入后仍须跑完整生产回放、普通输入存档、SDL 构建/浏览器和合适的 sanitizer 验证。8 个 active damage-area、181570 个 visual RNG 差异及普通 Native ending 的缺证均未由此原型处理。
