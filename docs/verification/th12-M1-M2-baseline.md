# th12 M1/M2 · 原版对照与资源层证据

本轮范围：把 th12 从「模板骨架」推进到「已有三个模块被原版证据证明等价」。

所有测试都可在本机复跑，命令见每节末尾。

## 1. 原版 oracle 可用

`th12_web/scripts/native/th12-probe.mjs` 用 Unicorn 加载 `th12.exe` 并解析 PE：

| 项 | 值 |
| --- | --- |
| 目标 | `th12.exe` 1.00b，737 280 字节，`sha256=d8d644d2e64957a3031b1a1399d0502e1ddaa5252d2c4e492770ad6717827628` |
| 基址 | `0x400000` |
| 节区 | `.text` `0x1000`/617472、`.rdata` `0x98000`/86016、`.data` `0xad000`/27136、`.rsrc` `0xd7000`/5632 |
| 导入 | 184 个，`dinput8` / `dsound` / `d3d9` / `d3dx9_40` / `winmm` / `kernel32` 等 |

新增 `th12_web/tests/cpp/th12-oracle.mjs`：带 SHA-256 校验、CRT 打桩
（`_malloc 0x46d04a`、`_free 0x46c941`、`_memcpy 0x47a330`）和导入处理器。

## 2. RNG 与原版逐字节一致

`th12_web/tests/cpp/th12-rng.test.mjs` 把可移植 C++ `Rng` 与 `th12.exe` 机器码
（`next16 0x4643d0`、`next32 0x464440`）做差分：

- 8 个种子 × 2 种模式 × 512 轮 = **8 192 次比较**，返回值和 8 字节状态全部相同。
- 另一条断言证明 `next32` 恰好等于两轮 `next16`，且 th12 没有 th11 那个四字变体。

结论：th11 模板的 RNG 算法对 th12 可直接复用，只是函数地址不同。

## 3. PBG3 归档读取器与 thtk 完全一致

`th12_web/tests/cpp/th12-archive.test.mjs`：

- `ResourceCrypt` 的密钥表按版本参数化，th12 用 `archive_crypt_th12`（取自 thtk 源码）。
- 读取用户本机 `th12.dat`（`sha256=dca82df072ba51c4b74c3d41ea1cbdcb91f709ce7cfea23599ee52caa34f2d72`）：
  - 条目表 **180 条**，顺序、名字、解压后大小、压缩后大小全部与 `thdat -l 12` 相同。
  - 180 个条目逐条解码，**每一个的 SHA-256 都与 `thdat -x 12` 的产物相同**。

报告：`runtimes/th12/th12_web/artifacts/cpp/verification/th12-archive.json`
（含 `entriesSha256=de153adea6affa327b964ef39dbe1884aa28e34fd5815a60c43b1d0500ae2ea0`）。

## 4. ANM 精灵档案与 thanm 完全一致

`th12_web/tests/cpp/th12-anm.test.mjs`，对 th12.dat 内全部 `.anm`：

| 指标 | 数量 |
| --- | --- |
| 档案 | 47（全部 ANM 版本 7） |
| 纹理 | 357 |
| 精灵 | 2287 |
| 脚本 | 1532 |
| 指令 | 28 336 |

每个纹理的 `名称/格式/宽/高/优先级`、每个精灵的 `source id/x/y/w/h`、
每个脚本的 `source id` 与**逐条指令的 `time`/`param_mask`/`opcode`** 都与 `thanm -l` 相同。
同时脚本字节流的边界解析必须完全走通，否则报错。

过程中修掉一个真实缺陷：模板的 `pixel_size` 缺少 `7 = GRAY8`，
导致 `stage01.anm` 这类含亮度贴图的档案整档打不开。现已按 thtk 的格式枚举补齐，
并给 `AnmResource` 加了 `last_error` 诊断码。

报告：`runtimes/th12/th12_web/artifacts/cpp/verification/th12-anm.json`。

## 5. ECL 敌机脚本与 thecl 完全一致

th12 使用 th10–th17 共用的 `SCPT` 容器：36 字节头 + ANIM/ECLI 引用块 +
u32 子程序偏移表 + 名字表 + 每个子程序一个 `ECLH` 块（16 字节指令）。
模板里 `EclInstruction` 的字段顺序正好等于 thtk 的 `th10_instr_t`
（`time/opcode/length/param_mask/rank/param_count/zero`，共 16 字节），无需改动。

`th12_web/tests/cpp/th12-ecl.test.mjs` 对 th12.dat 内全部 9 个 ECL：

| 指标 | 数量 |
| --- | --- |
| 文件 | 9（`default` + `stage01`–`stage06` + `stage07` + `stage07boss`，含 Extra 面） |
| 子程序 | 854 |
| 指令 | 28 409 |

每个文件的子程序个数、名字与顺序、ANIM/ECLI 引用列表、
以及**每条指令的 `time` 与 opcode 序列**都与 `thecl -d 12 -r` 相同。

报告：`runtimes/th12/th12_web/artifacts/cpp/verification/th12-ecl.json`。

## 6. STD 背景脚本与 thstd 完全一致

`th12_web/tests/cpp/th12-std.test.mjs` 对 th12.dat 内全部 7 个 STD：

| 指标 | 数量 |
| --- | --- |
| 文件 | 7（`stage01`–`stage07`） |
| 对象（ENTRY） | 25 |
| 四边形（QUAD） | 48 |
| 面（FACE） | 414 |
| 指令 | 233 |

逐项对照 `thstd -d 12`：ANM 名、每个对象的 `Unknown/Position/Depth/Width/Height`、
每个 QUAD 的 `Type/Script_index/Position/Width/Height`、
每个对象归属的 FACE 列表（`unknown1` 与坐标）、以及每条背景指令的 `time`/opcode。

附带确认了一个容易踩的坑：STD 指令流以一个 `time=-1, opcode=-1, length=-1` 哨兵结尾，
而 `thstd` 不打印它 —— 比较时必须把它排除，否则永远差 1。

报告：`runtimes/th12/th12_web/artifacts/cpp/verification/th12-std.json`。

## 7. MSG 对话目录与 thmsg 完全一致

`th12_web/tests/cpp/th12-msg.test.mjs` 对 th12.dat 内全部 55 个 MSG 文件
（共 121 个 entry）核对目录表：entry 数、每个 entry 的流偏移（必须落在文件内且严格递增）、
以及每个 entry 的第二个 u32（thmsg 打印成 `entry N (FLAGS)`）。

为了在不加载 ANM 的前提下测到**真正的游戏代码**，把 `Dialogue::begin` 里的
「entry → 流偏移」解析抽成了 `Dialogue::locate`，`begin` 与测试共用同一份实现。

补充记录：thtk v12 的 thmsg 在 th12 上会报 `value_list_from_data: N bytes left over`
——那是 thtk 自带的 opcode 格式表对 th12 还不完整（不影响目录解析，但说明
**th12 的 opcode 语义不能靠 thtk v12 认定**，必须回到原版二进制）。

报告：`runtimes/th12/th12_web/artifacts/cpp/verification/th12-msg.json`。

## 复跑命令

```powershell
# 资源层 / RNG（需要本机装有 th12.dat；thtk 走 tools/thtk）
cd H:\code\thp\runtimes\th12
& H:\code\thp\tools\emsdk\node\24.19.0_64bit\node.exe --test --test-concurrency=1 `
  th12_web/tests/cpp/th12-rng.test.mjs `
  th12_web/tests/cpp/th12-archive.test.mjs `
  th12_web/tests/cpp/th12-anm.test.mjs `
  th12_web/tests/cpp/th12-ecl.test.mjs `
  th12_web/tests/cpp/th12-std.test.mjs `
  th12_web/tests/cpp/th12-msg.test.mjs
```

夹具需先用 `node th12_web/scripts/cpp/build.mjs` 重新生成；
本记录对应的 `game-core-test.wasm` 为 579 452 字节，`sha256=cd50c23b89ce57732729122b2cf783682696e39ecdc7579de83f0aa2ca27aaa7`。
