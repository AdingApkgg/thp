# th12 资源盘点与 M3/M4 缺口

本页把 `th12.dat` 的实际内容、已经过验证的读取器、以及下一步要补的引擎/玩法缺口放在一起，
作为 M3 起的施工清单。

## th12.dat 内容（180 条目，thtk `-l 12`）

| 扩展名 | 数量 | 读取器 | 对照证据 |
| --- | ---: | --- | --- |
| `.msg` | 55 | `Dialogue::locate` | `th12-msg`：121 entry，目录表全同 |
| `.wav` | 49 | 直接按裸 WAV 送 SDL3 音频 | 未对照（音频通道不参与逻辑） |
| `.anm` | 47 | `AnmResource` | `th12-anm`：357 纹理 / 2287 精灵 / 1532 脚本 / 28336 指令 |
| `.ecl` | 9 | `EclResource` | `th12-ecl`：854 子程序 / 28409 指令 |
| `.std` | 7 | `StageResource` | `th12-std`：25 对象 / 48 QUAD / 414 FACE / 233 指令 |
| `.sht` | 6 | `ShtResource` | 无 thtk 对照工具（thtk 没有 `thsht`）；改由引擎启动用例覆盖：6 个档案全部可解，每组 2/4/6/8/10 发弹幕 |
| `.rpy` | 4 | 仅作样例，实际录像走 `Replay` 自研格式 | — |
| `.fmt` / `.txt` / `.ver` / 无扩展名 | 各 1 | 元数据 | 未对照 |

归档容器本身（PBG3）已由 `th12-archive` 证明与 thtk 逐字节一致（180/180，SHA-256 相同）。
随机数发生器由 `th12-rng` 证明与 `th12.exe` 机器码一致（8192 次比较含状态）。

## 已确认可跨作品复用的事实

- **ANM v7 = th11/th12/th12.5，v8 = th13+**。th12 的 ANM 读取器在 th13 上要按 v8 差异调整。
- **归档密钥**：th12/12.5/12.8 一张表，th13 一张，th14 及以后（含 th18）共用一张。
- **ECL 指令结构** `{u32 time; u16 id,size,param_mask; u8 rank_mask,param_count; u32 zero}`（16 字节）
  与模板的 `EclInstruction` 一致，th13+ 不必改。
- **MSG 容器**（头 `u32 entry_count` + `entry_count × {u32 offset; u32 flags}`，文本
  XOR key=0x77 / step=7 / step+=0x10）th11 与 th12 相同。

## M3/M4 的真正缺口

### 1. th12 专有的玩法系统在模板里完全不存在

th12-eagler（th11 模板）里没有 UFO。th12 新增：

- **UFO 系统**：击破敌机掉落三色 UFO 碎片，集齐后召唤 UFO，UFO 吸收道具后变成
  红/蓝/绿三色并给出对应奖励。
- **「母舰」与灵界系统**：`mother.cpp` 级别的对象。
- **自机三装备 × 三种子机行为**：th12 是灵梦/魔理沙/早苗各 2 种装备，共 6 个 `.sht`。

模板的 `ShotManager` / `ItemManager` / `GameEconomy` 需要按 th12 重写而不是微调。

### 2. opcode 语义必须回原版二进制，不能靠 thtk

thtk v12 在 th12 的 `.msg` 上会报 `value_list_from_data: N bytes left over`，
说明它自带的格式表对 th12 的 opcode 集合不完整。
`.ecl` 的 opcode 同理：`thecl -d 12 -r` 能给出**指令框架**（time/opcode/参数个数），
但**每条 opcode 的行为**必须从 `th12.exe` 取。

方法是复用 th11 模板已经跑通的**差分 oracle**：在 Unicorn 里把 th12 的 ECL 上下文
放到真实机器码上执行一条指令，把产生的游戏状态与可移植实现逐字段比较。

### 3. 原版模块划分（用于定位函数）

`th12.exe` 里内嵌了 118 条 `.\src\game\*.cpp:LINE <消息>` 字面量，覆盖 44 个源文件，
包括 th12 专有的 `ufo.cpp`、`mother.cpp`、`eclview.cpp`、`sptcmd.cpp`、`sptlib.cpp`、
`sprtlib.cpp`、`sprtanim.cpp`、`spttest.cpp`、`setest.cpp`、`smollscore.cpp`。

这些字面量给出了**原版的模块划分**（哪些逻辑属于哪个翻译单元），但有一个重要限制：
**它们没有任何代码引用**——对 `.text` 的完整 4 字节扫描、以及
`reference/th12-decomp/decomp_out` 的交叉引用都没有命中。
因此这套字面量只能当**模块清单**用，不能当**函数定位**用。
脚本保留在 `tools/th12-source-map.mjs`，其 `literals` 输出记录了每个字面量的地址。

函数定位仍走 `reference/th12-decomp`：`decomp_out` 的 1941 个
`<符号>_<地址>.c` 给出函数边界，配合 oracle 的差分实验逐个确认职责。

## 下一步

1. **实现 th12 专有 ECL 指令（256 以上）** —— 表已经拿到
   （[`ecl-opcodes.json`](ecl-opcodes.json)，278 条，参数个数已与真实字节码逐条对齐），
   缺的是**行为**。引擎已经能加载 `th12.dat` 全部 7 关资源，但在执行
   `stage01.ecl` 的 `main` 时于 **opcode 402** 处因号码撞车而张冠李戴、栈失衡后陷阱。
   详见 [`ECL-OPCODES.md`](ECL-OPCODES.md)，其中给出了 `FUN_004154d0`
   （th12 扩展指令解释器）这条恢复路径。
2. 浏览器竖切片：SDL3 外壳已经存在，需要把 `GameResources` 的资源清单
   与启动参数从 th11 换成 th12（已完成的部分见下表）。
3. 触控 / 存档 / Replay 的 th12 布局核对（`scores.characters[6]` 已按 3 角色 × 2 装备改，
   但存档文件的偏移仍沿用 th11 的，需要与原版 `th12_*.sav` 对照）。

## 本轮已修掉的 th11→th12 结构性差异

| 位置 | th11 假设 | th12 事实 |
| --- | --- | --- |
| `GameResources::open_archive` | 条目名必须唯一 | `th12.dat` 真的有重复条目 `se_cardget.wav`；按原版线性查找取第一个 |
| `GameResources::load_stage` 对话名 | `st%02u_%02u%c`（i/3, a/b/c） | `stNN_00a/00b/01a/01b/02a/02b`（i/2, a/b） |
| `CoreResources::players` | 2 个（`pl00`/`pl01`） | 3 个（`pl00`/`pl01`/`pl02`） |
| `.sht` 名单 | `pl00a/b/c`、`pl01a/b/c` | `pl00a/b`、`pl01a/b`、`pl02a/b` |
| 装备索引 | `character*3+subtype`（2×3） | `character*2+subtype`（3×2） |
| 选择范围校验 | `character<=1 && subtype<=2` | `character<=2 && subtype<=1` |
| `ShotSpec` 回调字段 | 必须为 0 | 是小枚举；早苗 B 的 `extra_callback=1` |
| `ShtResource::group_index` | 有隠藏第三种「weapon mode」层 | 所有 6 套都是 每威力层 2 种（未聚焦/聚焦） |
