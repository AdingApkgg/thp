# TH14 WebGPU 矩形 stencil 清除 · 2026-10-26

可选 JavaScript WebGPU 后端及原生 Python GPU 宿主现在支持矩形 stencil 清除。原先该路径明确报错；新实现通过矩形裁剪和 stencil 替换写入，只清除请求的颜色、深度或 stencil 分量。生产 C++ 玩法、音频和 Renderer 的 Wasm 不变。

## 实现

部分清除沿用现有全屏三角形与每个矩形的 scissor，在 `Depth24Stencil8` 附件上使用双面 `always`／`replace`，写入 stencil 的低 8 位。清除管线缓存现在区分全部三个清除标志，避免复用仅有颜色／深度的管线。没有请求深度时不写深度，没有请求颜色时不写颜色；普通清除保持 stencil 不变。

完整清除也按实际 D3D9 行为取 stencil 低 8 位。没有 stencil 存储、D16 和普通 D24 不接受 stencil 清除。JavaScript 实现位于 [Th14WebGpuHost.mjs](../../runtimes/th12/portable/sdl/Th14WebGpuHost.mjs)，原生对应路径位于 [GPU 宿主](../../tools/th14-native-webgpu-context.py)。

## 实际设备比较

[D3D9 HAL 控制](../../tools/th14-stencil-clear-hal-control.py)使用独立、未显示的设备窗口句柄和 D24S8 附件，没有启动原游戏。96 个用例覆盖四种 stencil／颜色／深度标志组合、八种 stencil 值及三种矩形集合，含重叠和边界条带。stencil 内容通过真实固定功能相等测试绘制读回，深度通过 less 测试绘制读回；颜色、两个 stencil 探针与深度探针均另由纯 CPU 字节期望核对。

[C++ 测试入口](../../runtimes/th12/th12_web/tests/cpp/th14-stencil-clear-fixture.cpp)实际调用生产 Renderer 的 Clear，经 Emscripten／Asyncify 与 JavaScript WebGPU 宿主执行。观察探针直接查询真实 GPU 附件，使用原生 Deno 设备 API。另一路使用实际 Python GPU 宿主，单独验证其实现，不把这一路写成 C++ 验收。

| 范围 | 留存结果 |
| --- | --- |
| D3D9 HAL | 96／96 用例符合独立 CPU 期望 |
| 实际 C++ → Asyncify → JS WebGPU | 96 用例，384 份缓冲，4,718,592 字节全部与 HAL 一致 |
| 原生 Python WebGPU 宿主 | 同一批 384 份缓冲全部一致，另拒绝三种无 stencil 存储输入 |
| C++ 测试 Wasm | 前后逐字相同，SHA-256 `36fe2971f671143e22b7b93fd1307bd12dfbbab373439c1c7fc0a568d9c939f7` |
| 当前 Stage 回归 | 21／21 幅完整原版缓冲，25,804,800 字节一致 |
| 当前 D3DX 捕获回归 | 8／8 份缓冲，5,242,880 字节一致 |
| 既有矩形颜色清除、CPU 版本更新及复制 | 回归通过 |

初始负向运行仍保留“Partial stencil clear is not implemented”的实际拒绝。该次测试工具没有在启动时另存源码，现按已记录的 SHA-256 精确恢复当时版本，并明确标记为恢复版本。第一轮正向执行虽然所有缓冲一致，测试工具却在关闭宿主后查询健康状态而退出；修正收尾顺序后另行运行并正常退出，只有后者列为通过。

[独立复核报告](th14-stencil-clear-verified-oct26.json)重新生成全部 CPU 期望，逐字读取 HAL、JavaScript 和 Python 留存缓冲，检查前后构建、实际源码、Wasm／loader 哈希及当前 21／8 回归。源码发布仅含工具、夹具和元数据，不含原始像素、DLL、Wasm 或游戏资源。

```powershell
python tools/th14-stencil-clear-evidence-oct26.py --output docs/porting/th14-stencil-clear-verified-oct26.json --check
```

这是有限的矩形清除修复。普通浏览器、系统呈现、IndexedDB、原版完整游戏画面和整作 1:1 没有据此完成。本次图形修复当时没有替换浏览器候选；随后新增的独立候选见下节，默认 WebGL 预览保持此前版本；旧的整局／Asyncify／菜单证据仍绑定各自实际执行版本，不继承到新宿主。打包格式光栅目标的拒绝及默认 WebGL 的历史单像素差继续保留。

## 后续当前宿主候选包

以已发布源码 `1776db96c0655bf0c941a715c5aa30f4c4c00285` 重新链接真实 SDL3 浏览器候选，146 个 C++ 对象按完整输入、编译标志和文件哈希复用，未重编 C++ 单元。完整 Wasm 仍为 `3786901cbe373d221b14f02bcb3b1fa77901512195a09ba080669753a915018c`；当前 stencil 宿主单独绑定到新包，不能把 Wasm 不变当作宿主未变或浏览器通过。

[候选复核](th14-stencil-candidate-verified-oct26.json)检查实际对象、源码、Wasm／loader、新宿主及包内文件。414,850,582 字节生成字体／FLAC 通过 28 个不可变别名复用，原游戏文件没有链接。父 Launcher 只写 103,342 字节元数据，引用 510,696,486 字节既有文件；133 条路由和 21 项实际 HTTP／协议检查通过。

新本地[静音候选入口](http://127.0.0.1:8214/?game=th14)已启动，直接 HTTP 请求核对当前宿主字节。8212 端口已被其他服务占用，未停止该服务；原默认预览也未替换。没有打开或驱动浏览器，呈现、系统输入、IndexedDB、物理音频及整作 1:1 均未据此验收。
