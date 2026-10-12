# 路线图

> **2026-10-04：** 用户已明确范围：其提供的 `06、06nc、07–20` 目录中，排除三个参考站点已转作品。
> [最新范围与核心状态](porting/CORE_STATUS.md)及[发行清单快照](porting/reference-coverage.json)
> 优先于下文历史进度；当前仅 TH06nc、TH12、TH13、TH14、TH16、TH17、TH18、TH19 八项，构建成功不等于完整移植。

目标：th12 / th13 / th14 / th16 / th17 / th18 六部原作在网页端 1:1 可玩，架构对齐 touhou.vip。

这是长周期工程。下面按「先跑通一条流水线，再复制到六部」组织，每一阶段都以可验证证据收尾。

## 阶段 0 · 工作区与工具链

- [x] 侦察参考实现，确认六作无现成可移植重建
- [x] 工作区骨架、只读参考仓库、thtk v12 数据工具（SHA-256 校验通过）
- [x] emsdk 6.0.10 可用（`emcc --version` = `6.0.10-git`）
- [x] wasi-sdk 34.0 + `@alexaltea/unicorn-js`（原版 oracle 依赖）
- [x] Node / Python 版本固定，构建包装脚本 `tools/build-runtime.ps1`
- [x] **模板 WASM 构建贯通**：`runtimes/th12` 产出 SDL3/WebGL2 WASM，两次构建 SHA-256 一致

证据见 [`docs/verification/2026-10-03-toolchain-bringup.md`](verification/2026-10-03-toolchain-bringup.md)。

## 阶段 1 · th12 流水线贯通（第一部作品）

按 `docs/th12/PORT_PLAN.md` 执行。里程碑：

1. **M1 基线** ✅：`th12.exe` 哈希/PE 字段入库；`th12.dat` 可解包；Runtime 骨架能构建出 WASM；原版 oracle 可执行。
2. **M2 资源层** ✅：PBG3 / ANM / ECL / STD / MSG 全部与本机原版工具差分对照通过。
3. **M3 引擎层** ⏳：ANM 渲染、输入、计时器、RNG ✅、存档，与 th11 模板对齐。
   th12 的运行时结构（`EclInstruction`/`EclStack`/`EclContext`/`EclOwner`）已逐字段
   确证与 th11 模板一致，核心区 0..89 可直接复用；瓶颈集中在扩展区（≥256）：
   112 个 opcode 在用。**当前实测**（`docs/th12/ecl-extended-opcodes.json`，8 个闸门把关）：
   **implemented 131、todo 16、collision 8、implemented-collision 38、unused 28、noop 1**。
   ——「46 个撞车 / 65 个待抄写」是本文件早先的估计，已被逐条核对取代；
   每条碰撞都附有原版反汇编与「为何仍然拒绝」的理由（见 DELIVERY §52–§57）。
   见 [`docs/th12/ECL-OPCODES.md`](th12/ECL-OPCODES.md) 与
   [`docs/th12/ecl-extended-opcodes.json`](th12/ecl-extended-opcodes.json)。
   —— 引擎已能在真实 `th12.dat` 上加载核心资源与全部 7 关关卡资源集；
   启动战斗阻塞于 th12 专有 ECL 指令（≥256，占指令总数 35.7%）的行为尚未实现，
   编号表与参数文法已到手（见 `docs/th12/ecl-opcodes.json` 与 `docs/th12/ECL-OPCODES.md`）。
   —— **浏览器侧已能实跑**：WASM 运行时在 headless Chrome 里通过资源/字体/音频初始化，
   并成功创建标题画面 ANM（`title.anm` 233 脚本），当前唯一阻塞是 BGM 布局表。
   见 [`docs/th12/DELIVERY.md`](th12/DELIVERY.md)。
4. **M4 玩法层**：自机三装备、UFO 系统、敌人/弹幕/激光、六面 + Extra 的 ECL 全关覆盖。
5. **M5 外壳层**：标题/菜单/暂停/结算/结局/录像，浏览器实跑验收。
6. **M6 发布**：`eagler-touhou/1` 接入 Host，游戏包与离线运行。

M1/M2 的逐项证据见 [`docs/verification/th12-M1-M2-baseline.md`](verification/th12-M1-M2-baseline.md)。
资源层目前的对照规模：归档 180 条目、ANM 47 档案 / 28 336 指令、
ECL 9 文件 / 854 子程序 / 28 409 指令、STD 7 文件 / 233 指令、MSG 55 文件 / 121 entry、
RNG 8 192 次比较。
M3 起的施工清单见 [`docs/th12/RESOURCE-GAP.md`](th12/RESOURCE-GAP.md)。

## 阶段 2 · th13 / th14 / th16（引擎同代）

th13（神霊廟）与 th12 差异最小，先做；th14（輝針城）/ th16（天空璋）沿用同一引擎与工作台。
每部重复 M1–M6，共享 `shared/eagler-common` 与 `portable/`。

## 阶段 3 · th17 / th18（较新引擎）

th17（鬼形獣）与 th18（虹龍洞）引擎改动更大（新的资源容器与绘制路径），
数据工具也需要扩展（thtk v12 不支持 th18 的 `th18.dat`，需自行实现 PBG3 变体）。

## 阶段 4 · 跨作品基础设施

联机（预测回滚）、thprac 练习菜单、thcrap 多语言、高刷新率、触控布局编辑、离线 PWA。

## 风险与已知阻塞

| 风险 | 说明 |
| --- | --- |
| 工作量 | 单部作品是数千函数级的重建；六部合计以年计 |
| 无公开重建 | th13/14/16/17/18 完全没有参考源码，只能靠原版机器码逆推 |
| 数据工具缺口 | thtk v12 最高支持 th17；th18 需自研解包 |
| 性能 | 高弹幕量 + 高刷新率对 WASM 渲染与逻辑预算的要求 |
| 素材许可 | 原版数据不入库、不上传，仅本机参与构建与对照 |

---

## 附：当前状态（第 60 轮末）

* **th12**：一部能在浏览器里跑并渲染的 Runtime（131 implemented / 16 todo / 7 collision / 39 implemented-collision）；
  7 关跑满 12000 帧；8 闸门 exit 0；12/12 测试；浏览器 `error=""` / 61 FPS / 0 traps；帧证明 exit 0。
* **M3 仍在进行**：M4 玩法层、M5 外壳层、M6 host 接入**均未完成**。
* **th13 / th14 / th16 / th17 / th18：零行代码**。
* **host 平台（`host/`）：空目录**。
* 接手请先读 [`docs/HANDOVER.md`](HANDOVER.md)。
