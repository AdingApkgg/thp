# Handover — 交接说明（th12 及后续五部）

> **2026-10-04 接手更新：** 本文以下为历史状态，已经落后于当前实现。
> 当前范围、ECL/ANM 分发表纠错与可重跑验收见 [核心接手记录](porting/CORE_STATUS.md)。
> 尤其不要继续使用旧的 TH13 / TH16 / TH17 / TH18 ANM 表推断 ECL 空操作。

本文件是**当前真实状态**的单一入口。每一句结论都可按 §6 的命令重跑验证；
凡是**没有证据**的，这里一律**不写**。

---

## 1. 目标与实际进度

原目标：把 th12 / th13 / th14 / th16 / th17 / th18 六部按「源码重建」路线 1:1 移植到网页端，
并建立 host 平台（启动器 / 协议 / 存档 / Replay / 触控）。

| 组成部分 | 状态 |
| --- | --- |
| **th12 Runtime** | **一部能在浏览器里跑起来并渲染动画的 Runtime**（有证据，见 §2） |
| th13 / th14 / th16 / th17 / th18 | **尚未开始**（0 行代码） |
| host 平台（`host/`） | **空目录**（0 个文件） |
| `shared/eagler-common/` | 参考仓库的**只读逐字副本**，不是本工作区的实现 |

工作区自己的 `docs/ROADMAP.md` 把 host 接入排在 **M6**，前面还有 **M4 玩法层**与 **M5 外壳层**；
**当前阶段是 M3 引擎层**。所以 host 为空**不是遗漏**，而是顺序。

### th12 的引擎层实测数字

来源：`docs/th12/ecl-extended-opcodes.json`（由 8 个闸门把关）。

| 指标 | 值 |
| --- | --- |
| implemented | **131** |
| todo | **16** |
| collision | **7** |
| implemented-collision | **39** |
| unused / noop | 28 / 1 |

**这些数字曾经被低估**：`docs/ROADMAP.md` 早先写「46 个撞车、65 个待抄写」，
与实测相差很远；第 56 轮已改成实测值。

---

## 2. 有证据的部分

* **七关全部跑满 12000 帧的模拟预算**（`tools/th12-stage-probe.mjs 12000`）。
* **浏览器里实跑**：headless Chrome，`error=""`、`traps: 0`、60 FPS
  （`tools/browser-proof.mjs`）。
* **画面确实在变**：帧证明工具检查「单色空白帧」与「连续两帧逐字节相同」两种情况，均未触发
  （`tools/th12-frame-proof.py`）。
* **12/12 核心测试**通过。

> **关键在于这四条各自证明了什么**：
> 它们证明「能跑、能渲染、在动」，**不证明「和原版一样」**。
> **像素不等于正确性**；本工作区没有可用的原版参照运行时，所以「合法但错误」的写入**看不见**。
> 这个 **oracle gap** 是当前最大的方法论风险，见 §5。

---

## 3. 方法论（这是最值钱的部分，六部通用）

### 3.1 证据优先级

1. **首要证据是 Ghidra 反编译的 C 代码**：`reference/th12-decomp/decomp_out/FUN_*.c`；
   调度器是 `FUN_004154d0_004154d0.c`。
2. **反编译器丢寄存器时，用 Capstone 反汇编兜底**：
   `py -3 tools/tmp/xdis.py <start> <stop>`。
3. 需要函数体时：`py -3 tools/th12-case-body.py <opcode...>`——
   它会给出 **case VA、EXE 偏移、与哪些 opcode 共用同一个体、体结束地址**。

### 3.2 已经被踩中三次的**反编译产物陷阱**

* 第 45 轮：一个看起来是**浮点字面量**的东西，其实是**寄存器**；
* 更早：`extraout_ECX`；
* 第 50 轮：**`FUN_0041a970` 的原始值走 `in_EAX`，不是参数**——参数表根本不能当作值的来源。

> **规则**：当一个访问器的**参数表解释不了它的值从哪来**时，
> **先去读调用点的反汇编，再下结论**。

### 3.3 opcode → case 是**两步**，不是一步

`ecx = opcode - 0x100` → `index = byte[0x419890 + ecx]` → `goto [0x419654 + index*4]`。
**直接读 `[0x419654 + (opcode-0x100)*4]` 是错的**。工具：`tools/th12-ecl-case-map.mjs`。

### 3.4 **三条独立的可达性轴**（缺一条就会写出死代码）

1. **拒绝名单** `kTh12CollidingOpcodes`——`EnemyScriptServices::command` 在进 switch 之前就 `return -2`；
2. **家族路由**——`enemy_movement_command` 等前置链会先吃掉一些 opcode，此时文件里的 `case` 永不执行；
3. **case 标签**本身——没有标签的处理等于没有处理。

> **「写对了」不等于「跑得到」。** 第 42 轮因此丢过一次工；
> 第 53、54 轮在**提交前**各拦下一次；第 54 轮还发现「条件分支被误当成 case 标签」。

### 3.5 写前校验

**先校验每个输入与每个定位器，再写第一个字节**（第 41 轮）。
定位器用**精确构造**（`trimStart().startsWith` 之类），**不要**对整个文件用 `includes()`，
**不要**凭记忆写列号（第 43/44 轮）。

**第 57 轮的教训**：校验要覆盖**所有**相关文件——那一轮我只查了 `EnemyCommands.cpp`，
而真正的冲突在 `EnemyStateCommands.cpp`，**路由闸门替我抓到了**。

### 3.6 闸门与工具（每部作品都要有）

```powershell
cd H:\code\thp
# 8 个闸门，全部 --check，期望 exit 0
node tools/th12-opcode-map.mjs --check
node tools/th12-ecl-opcodes.mjs --check
node tools/th12-ecl-case-map.mjs --check
node tools/th12-replay-format.mjs --check
node tools/th12-dispatch-gate.mjs --check
node tools/th12-bullet-appearances.mjs --check
node tools/th12-handler-routing.mjs --check
node tools/th12-orphan-bodies.mjs --check
```

* `th12-opcode-map.mjs` **不带 `--check`** 时会重新生成
  `docs/th12/ecl-extended-opcodes.json`——**改完代码必须重新生成**，否则闸门会红。
* **构建才是语义的闸门**（第 44 轮）：声明不等于定义，半个契约只有**链接器**能抓住（第 47 轮）。
* **探测器必须先被证伪**：一个什么都没找到的探测器**什么也没证明**。
  例：`tools/th12-frame-proof.py` 用「故意植入空白帧 + 完全相同的帧对」验证过它会报错。

### 3.7 几条会反复咬人的操作纪律

* **绝不要把替换文本塞进 `pwsh -Command`**——PowerShell 先解析整个脚本，
  一个引号错误就**什么都不执行**（已发生 4 次）。**用文件编辑工具。**
* 改了共享文件后，若编辑工具报 `file changed since it was read`，**先重读再改**（那是版本护栏）。
* 报告「已修复 / 已减少」这类结论前，**必须重新构建并重跑全部闸门与测试**。

---

## 4. 立刻可继续的工作（按性价比排序）

### 4.1 th12 引擎层：余下 **7 条碰撞**（每条的现状都已记录在案）

| opcode | 现状 |
| --- | --- |
| 277 (0x115) | 已解码：`&Enemy[0xe0+i(0)*4]` 经 `FUN_00461c50` 取指针，写 `+0x2c` 与标志位 4。**需要那个对象类。** |
| 278 (0x116) | 同一张指针表；写 `+0x40`、`+0x44`（同一个浮点）与标志位 8。**同上。** |
| 281 (0x119) | 已解码：`enemy[i(0)*4 + 0x1e0] = i(1)`。**目标字段未确立**（落在插值器块内）。 |
| 321 (0x141) | **未解码**，715 字节，与 323 共用体——本组最大的一块。 |
| 325 (0x145) | 已解码：写第二个 0x4c 结构（`+0x28c`/`+0x2d8`）的 7 个浮点 + `+0x44` 整数 + `+0x48`=8。**该结构未在端口命名。** |
| 417 (0x1a1) | 已解码：`FUN_004529a0(1,i(0),i(1),i(2),0,0x46)` = `operator_new(0x44)` + `FUN_00452a60`。**需要一个未建模的类。** |
| 419 (0x1a3) | 已解码：对 `DAT_004b43e4+0x6d30` 的对象做致命错误判定（读其 `+0x8c`），失败返回 −1。**需要那个对象。** |

**已修好的先例**：第 55 轮把 300（0x12c）转写并移出名单；第 57 轮把 320（0x140）转写并移出名单——
后者尤其值得读：**端口早就握着 TH12 的 0x140 体，只是挂在 TH11 的 0x12c 号码上**。
**余下的碰撞多属「需要端口先有某个子系统」，不是「还没抄」——所以顺序是先补子系统。**

### 4.2 余下 **16 条 `todo`**

**准确的 16 条**（`docs/th12/ecl-extended-opcodes.json` 的 `entries` 里 `verdict==="todo"`，
按 `usedInTh12Dat` 排序；字段是 `id` / `usedInTh12Dat` / `decompiled`，**不要猜字段名**）：

| 使用次数 | opcode | `decompiled` |
| --- | --- | --- |
| 98 | 602 (0x25a) | inline |
| 83 | 525 (0x20d) | inline |
| 70 | 600 (0x258) | absent |
| 55 | 312 (0x138) | **fallthrough → 313** |
| 43 | 279 (0x117) | inline |
| 41 | 601 (0x259) | inline |
| 30 | 611 (0x263) | inline |
| 24 | 700 (0x2bc) | absent |
| 22 | 523 (0x20b) | inline |
| 21 | 520 (0x208) | inline |
| 20 | 603 (0x25b) | inline |
| 8 | 510 (0x1fe) | inline |
| 8 | 610 (0x262) | inline |
| 3 | 452 (0x1c4) | inline |
| 3 | 453 (0x1c5) | inline |
| 3 | 608 (0x260) | inline |

> **257（0x101）不在这张表里**——它早已被管理器闸门处理（第 51 轮证明，见
> `docs/th12/DELIVERY.md` §52）。本文件早先的版本把 257 写成了待办，**那是错的**，此处更正。

**这批 `todo` 与碰撞是同一类**：它们**不是「小 setter 还没抄」，而是需要端口先有某个子系统**。
以使用最多的 602（0x25a）为例，它的体在调度器里（`case 0x25a:`，`FUN_004154d0` 第 2124 行起）：

* `_memset(&local_2a8, 0, 0x1e8)`；
* `uVar26 = FUN_0041a900(0)`——**整数自变量 0 当作索引**；
* 从 `(iVar10 * 0x214 + param_1) + 300` 起**整块复制 108 个浮点**到栈上；
* 读 `param_1 + iVar10*0xc + 0x152c / 0x1594 / 0x1530 / 0x1534`，
  并加上 `param_1 + 0x34 / 0x38 / 0x3c`（**`param_1` 的坐标**）。

即：**按索引访问的 `0x214` 步长槽位数组 + `0xc` 步长表**，再合成一个 0x1e8 的局部结构。
**在端口把这两个数组与那个局部结构的语义确立之前，转写它只会得到外表合理、含义错误的一堆写入。**

`decompiled` 字段的取值含义也要注意：`inline` = 体在调度器里；`fallthrough` = 它会**落到下一个
opcode 的体**（312 → 313）；`absent` = 反编译输出里**没有**（600、700——需要先读反汇编补上）。

### 4.3 其余已知缺口

* **444**：TH12 在哪里设置**碰撞回调**——候选是 444（0x1bc），尚未确证；
  445 曾是一个 TH11 残留体位，已改为有记录的空操作。
* **`+0x26b8` 的 `+2` vs `+3`**：`FUN_00412990` 写 `(manager[0x74] & 1) + 3`，
  端口写 `(total_created & 1) + 2`。**差异未解释，故意保留不动。**
* **th12 存档偏移**仍是 th11 形状；`ReplayStageState::read` 的偏移未逐条核对。
* **`.sht` 读取器**没有 thtk 对应物。
* **opcode 名称**未恢复（目前只有编号）。
* **th12 的 56 条 `sound_definitions` 表**（基址 `0x4ae5aa`，步长 0x14）与
  `bullet_cancel_scripts` 未恢复。
* **16 个非 oracle 测试文件**仍硬编码 th11.dat 路径，应改为读 `target.json`。
* 完整测试套件目前是 `tests 140 / pass 12 / fail 122 / skipped 6`——
  109 个缺 `unicorn-bounded.wasm`，12 个是上面那条路径问题，1 个缺分析用汇编。
  **这是已知且已记录的，不是回归。**

### 4.4 host 平台（M6）与后续五部

* host 的**协议边界**以 `reference/eagler-touhou/docs/ADAPTING_A_GAME.md` 为准
  （**不要另立一份**）；`docs/ARCHITECTURE.md` 已有 Host/Runtime 职责划分表。
* 顺序：th12 的 **M4 玩法层 → M5 外壳层 → M6 host 接入**；
  再按同一模板推进 th13（与 th12 差异最小）→ th14 → th16 → th17 → th18。
* 数据层结论已落在 `docs/FORMATS.md`：**th14 之后所有作品共用同一张密钥表**，
  th18 的归档没有额外密钥障碍，障碍只在 thtk v12 二进制太老。

---

## 5. 已知的最大风险：**没有 oracle**

* 端口可以**自洽地跑**，也可以**渲染**，但**没有任何东西能证明它和原版一致**。
* 后果：**「合法但错误」的写入完全不可见**——例如某个字段写对了位置、写错了含义。
* 已经**实际发生过**的：第 50 轮我在一个**对端口毫无影响**的差异上下错过结论；
  第 34 轮一个残留的 TH11 体位把第 4 关从 12000 帧压到 301 帧——
  **是"帧数变化"暴露了它，不是正确性检查**。
* 缓解方向（未实施）：`th11-eagler` 模板自带 **Unicorn 跑原版 EXE** 的对照工作台
  （`scripts/native/`），可以按同一路径为 th12 建起来。

> **在 oracle 建成之前，任何「1:1」的断言都应当被读作「按反汇编逐条转写」，
> 而不是「与原版行为等价」。**

---

## 6. 如何重建与验证（照抄即可）

```powershell
# 核心构建（wasi-sdk → wasm32-wasip1，供 Node 直接断言）
cd H:\code\thp\runtimes\th12\th12_web
node scripts\cpp\build.mjs

# 重新生成 opcode 判决表（改完代码必须做）
cd H:\code\thp
node tools\th12-opcode-map.mjs

# 七关模拟
node tools\th12-stage-probe.mjs 12000

# 8 个闸门
foreach($g in @('th12-opcode-map','th12-ecl-opcodes','th12-ecl-case-map','th12-replay-format','th12-dispatch-gate','th12-bullet-appearances','th12-handler-routing','th12-orphan-bodies')){ node tools\$g.mjs --check }

# 核心测试
cd H:\code\thp\runtimes\th12
node --test --test-concurrency=1 "th12_web/tests/cpp/th12-*.test.mjs"

# 浏览器实跑 + 帧证明（需要先起 dev server：scripts/serve-th12.mjs，默认 127.0.0.1:8113）
cd H:\code\thp
node tools\browser-proof.mjs --url "http://127.0.0.1:8113/?autostart=1" --out artifacts/th12 --shots 3 --interval 40000 --wait 95000 --prefix rNN --port 95NN
py -3 tools\th12-frame-proof.py artifacts\th12\browser-proof.json
```

**注意**：`artifacts/`、`tools/emsdk/`、`tools/wasi-sdk-*/`、`reference/`、`node_modules/`
都在 `.gitignore` 里；原版 `th12.exe` / `th12.dat` / `thbgm.dat` / 存档 / 录像
**不入库、不上传**，只在本机参与构建与对照。

---

## 7. 逐轮决策记录

每一轮的**发现、证据、以及被闸门抓到的错误**都按顺序记在
[`docs/th12/DELIVERY.md`](th12/DELIVERY.md)（§1 … §57）。
**读它比读本文件更接近现场**；本文件只负责「现在在哪、下一步做什么」。
