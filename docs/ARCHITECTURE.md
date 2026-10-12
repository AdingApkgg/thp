# 架构

本工作区沿用 eagler-touhou 的两层边界：**Host** 拥有产品界面与生命周期，**Runtime** 拥有游戏模拟与渲染。
两者只通过 `eagler-touhou/1` 协议通信，同一个 Host 可以挂任意数量的 Runtime。

```
浏览器
 ├── Host（host/）           启动器 · 游戏包 · 存档/Replay · 触控 UI · 联机大厅
 │      │  postMessage: eagler-touhou/1
 │      └── Runtime iframe（同源）
 │             └── WASM（runtimes/th12/…）游戏模拟 · WebGL2 · 音频 · IDBFS
 └── 共享运行时基础（shared/eagler-common/）联机 · 回滚 · 输入 · 帧调度
```

## 1. Host / Runtime 边界

| | Host 拥有 | Runtime 拥有 |
| --- | --- | --- |
| 产品 | 作品目录、包安装、语言包、更新、首用须知 | — |
| 生命周期 | `configure` / `launch`、`first-frame` / `exit` / `error` 事件 | 游戏状态机、固定 60Hz 逻辑 |
| 输入 | 浏览器键盘镜像、触控布局、灵敏度 | 把输入落到原版输入模型 |
| 存储 | 只经协议 `list/read/write/remove/sync` | `/savesth12` 挂载、原版存档与 Replay 格式 |
| 表现 | 缩放、放大镜、画布位置 | 全部游戏渲染（WebGL2） |

协议细节以 `reference/eagler-touhou/docs/ADAPTING_A_GAME.md` 为准，不在本仓库另立一份。

## 2. 为什么以 th11 portable 为 th12 的模板

`reference/th11-eagler` 是完整的 TH11 1.00a 可移植 C++/SDL3 实现（`th11_web/` + `portable/`）：

- 引擎分层与 th12 同源：`AnmManager`、`EclInterpreter`、`BulletManager`、`EnemyManager`、
  `LaserManager`、`PlayerFrame`、`Stage`、`Dialogue`、`ScoreFile`、`ReplayRecorder` 等。
- 渲染已经是 WebGL2：`AnmRenderer` → `ZunGraphics` → `GraphicsDevice` → `portable/sdl/Renderer.cpp`。
- 已经有启动器、`sdl-runtime` 宿主、IDBFS 存档、触控、包发布与 `verify-release` 验收链。
- 已经有**原版对照工作台**：`scripts/native/`（Unicorn x86 跑原版 EXE）+ `scripts/cpp/`（WASI 核心）+ `tests/cpp/*.test.mjs`。

因此 th12 Runtime 不是从 Ghidra 文本从零整理，而是**分叉模板 + 逐模块替换 + 用原版做差分验证**。

## 3. 移植工作台（每部作品都要有）

| 组件 | 作用 | 位置 |
| --- | --- | --- |
| 目标基线 | 原版 EXE 的 SHA-256 / PE 字段 / 版本字符串 | `th12_web/target.json` |
| 原版 oracle | Unicorn 加载 `th12.exe`，按机器码执行并逐指令/逐内存对照 | `th12_web/scripts/native/` |
| 核心测试夹具 | 同一份 C++ 用 wasi-sdk 编译成 `wasm32-wasip1`，供 Node 直接断言 | `th12_web/scripts/cpp/` + `tests/cpp/` |
| 数据工具 | thtk（`thdat` / `thecl` / `thanm` / `thmsg`）解包 `th12.dat` | `tools/thtk/` |
| 浏览器验收 | 实际 WebGL2 启动、回放、存档、触控 | `th12_web/tests/browser/` |

**验收规则**：任何「已实现」的声明都必须有证据（模块测试、原版前缀等价、浏览器实跑），
并且证据要记录源码/核心哈希。固定样本通过不等于覆盖所有输入。

## 4. 数据链路

Runtime 在浏览器里直接读原版数据包（与 th06/th11 Runtime 一致）：

```
th12.dat / thbgm.dat  →  PBG3 解包  →  ANM / ECL / STD / MSG / 音乐
                                      ↑ 由 Runtime 内 C++ 实现，构建期用 thtk 交叉校验
```

用户自己导入原版数据（Import 模式）或由部署方提供（Hosted 模式），前端不上传任何原版数据。

## 5. 与参考仓库的差异

- 本工作区把六部作品的目标统一在一份 `docs/ROADMAP.md` 下，每部一个 Runtime 目录。
- th13–th18 没有模板，先在 th12 上把「模板 → 原版差分 → 验收」这条流水线跑通，再复制到其余五部。
- 本工作区不修改 `reference/` 下的任何内容；所有改动都发生在 `host/`、`runtimes/`、`shared/`、`tools/`。
