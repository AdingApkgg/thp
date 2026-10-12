# 2026-10-03 · 工作区与工具链落地记录

本轮范围：阶段 0。目标是把「模板 → 构建 → 数据」这条链路跑通，为 th12 移植做准备。

## 已完成并有证据

| 项 | 操作 | 证据 |
| --- | --- | --- |
| 参考仓库 | 克隆 eagler-touhou / eagler-common / th06@eagler / th11@eagler / th12-decomp | `reference/` 下 5 个只读仓库 |
| th12 Runtime 模板 | 由 `th11@eagler` 的 `th11_web` + `portable` 分叉为 `runtimes/th12` | 562 个文件 |
| Emscripten | emsdk 6.0.10（`emcc --version` = `6.0.10-git`）+ emsdk 自带 node 24.19.0 / python 3.13.3 | `tools/emsdk` |
| cmake / ninja | pip 安装 cmake 4.4.3、ninja 1.13.2 | Python 3.13 |
| wasi-sdk | wasi-sdk 34.0（`clang version 23.1.0-rc3`，target `wasm32-unknown-wasip1`） | `tools/wasi-sdk-34.0-x86_64-windows` |
| 原版对照器依赖 | `@alexaltea/unicorn-js` | `tools/unicorn/node_modules` |
| 数据工具 | thtk v12，SHA-256 与官方发布一致（`f6acc00f…65154`），含 `thdat`/`thecl`/`thanm`/`thmsg` | `tools/thtk` |
| **WASM 构建贯通** | th12 模板（当前仍是 th11 代码）用 SDL3 + WebGL2 成功产出 WASM | `artifacts/sdl3/th11-harness.wasm`，1 425 376 字节，`sha256=8a800d88a6b3fda430e406a6a56d65da5186a66676e5cbb811c23d487aa269ea` |

构建可复现：`tools/build-runtime.ps1 -Runtime th12` 连跑两次得到同一个 SHA-256。

## 工具链的两个坑（已固化到构建包装脚本）

1. `python` 必须在 PATH 上且 >= 3.10 —— 本机默认 `python` 是 3.7.9，emsdk 会直接拒绝。
2. clang 在默认 `%TEMP%` 下会报 `unable to make temporary file: permission denied`（编译 compiler-rt 时必现）；
   把 `TEMP/TMP/TMPDIR` 指到工作区内目录后正常。

emsdk 安装器本身还会在解包 `emscripten/test/test_other.py` 时偶发 `WinError 5`；
本轮用 Python 手动解包 + 补写 `upstream/.emsdk_version` 绕过，`emsdk activate latest` 随后成功。

## th12 目标基线

```
th12.exe  (H:\Games\th\12\th12.exe)
  sha256  d8d644d2e64957a3031b1a1399d0502e1ddaa5252d2c4e492770ad6717827628
  size    737280
  版本串  "Undefined Fantastic Object. ver 1.00b"
```

原版 EXE 里保留了 ZUN 自己的源码路径字符串（例如 `.\src\game\effect.cpp`、`.\src\game\laser.cpp`），
可作为「函数 → 源文件」的归类线索，已记入 `target.json` 的 `evidence`。

## 数据基线

`th12.dat` 用 thdat 版本 12 解出 183 个条目（清单见 `docs/th12/th12.dat.entries.txt`）：

| 类型 | 数量 |
| --- | --- |
| msg | 55 |
| wav | 49 |
| anm | 45 |
| ecl | 9 |
| std | 7 |
| sht | 6 |
| rpy | 4 |

th18 的 `th18.dat` **不被 thtk v12 支持**（自动探测失败，v12 最高到 th17）；th17 需显式指定版本 17。
阶段 3 需要自行实现 th18 的容器解析。

## 下一步

1. 把 `runtimes/th12` 从 th11 模板改为真正的 th12（先做命名与目标基线切换，再逐模块替换逻辑）。
2. 建立 th12 原版 oracle：PE 导入表 → Unicorn 打桩 → 关键函数行为采样。
3. th12 资源层（PBG3 / ANM / ECL / STD）解码并与 thtk 输出对照。

## 补充：原版 oracle 与 WASI 夹具已跑通

- WASI 核心夹具构建成功：`runtimes/th12/th12_web/artifacts/cpp/game-core-test.wasm`
  （`scripts/cpp/build.mjs` 已改为指向本工作区的 `tools/wasi-sdk-34.0-x86_64-windows`）。
- 原版 oracle 打通：`scripts/native/th12-probe.mjs` 用 Unicorn 加载 `th12.exe` 并解析 PE：

  | 项 | 值 |
  | --- | --- |
  | 基址 | `0x400000` |
  | 节区 | `.text`(0x1000, 617472) / `.rdata`(0x98000, 86016) / `.data`(0xad000) / `.rsrc`(0xd7000) |
  | 导入 | 184 个函数，来自 `dinput8` / `dsound` / `d3d9` / `d3dx9_40` / `winmm` / `kernel32` 等 |

  这说明 th12 的原版机器码可以在本项目自带的 x86 解释器里加载；
  下一步是给导入打桩并定位与 th11 对应的 CRT / 控制器入口。

### 模板自带的 oracle 缺口

th11 模板的 `tests/cpp/*.test.mjs` 依赖两个**未随仓库分发**的本机参考物：

- `th12_web/reference/native/unicorn-bounded.wasm`（带指令预算钩子的定制 Unicorn 构建）
- `reference/native/d3dx9_37.dll`

且 `tests/cpp/helpers.mjs` 里 `malloc`/`free`/`memcpy` 的打桩地址（如 `0x460192`）
和 `Controller` 初始化入口（`0x48abf0`）都是 **th11 的地址**。
这些都需要在 th12 上重做：`scripts/native/machine.mjs` 已改为使用 npm 的
`@alexaltea/unicorn-js`，因此可以不依赖那个定制构建先跑起来。

