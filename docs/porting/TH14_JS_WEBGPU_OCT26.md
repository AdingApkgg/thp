# TH14 JavaScript WebGPU 主机及浏览器候选包 · 2026-10-26

实际 C++ Renderer 现有浏览器端 WebGPU 主机和 Emscripten Asyncify 桥接。C++ 继续拥有状态、批处理、布局、矩阵、顶点及打包纹理解码；JavaScript 只管理 GPU 对象、提交、映射读回和画布呈现。初始化与读回等待 Promise，帧回调、加载回调和输入修改共用执行队列，避免在 C++ 栈暂停时再次启动异步调用。实际 SDK 的 `EM_BOOL` 为 `bool`，回调声明和间接调用保留其真实类型。

| 对象 | 当前证据 |
| --- | --- |
| 实际 C++ → Emscripten／Asyncify → JavaScript WebGPU | 原生 Deno 2.9.8 WebGPU 接口执行；21／21 个 Stage 完整参考缓冲一致，共 25,804,800 字节 |
| 捕获／复制 | 8／8 个原版 D3DX 完整缓冲一致，共 5,242,880 字节；部分清屏、CPU 版本失效及复制控制的完整缓冲也一致 |
| 暂停的异步 C++ 栈 | 真实 GPU 读回被暂缓交付，期间 Wasm 内存增长 65,536 字节；2,048 个栈保护字、16 字节 GPU 像素、两个加载回调、三个帧回调及一个排队的实际类型 `th11_key(17,1)` 调用均通过；重复绑定不叠加包装 |
| 当前生产 Application 回归 | 声明同一元数据时钟的 WebGPU／GLES 成对原生 WASI 流程共 2,008 帧、239 项断言、18 幅画面、PCM 与文件一致；新进程读回文件不变，实际文件通过原版 codec 检查 |
| 浏览器目标构建 | 使用真实 SDL3 端口构建 146 个 C++ 编译单元，Wasm 为 2,699,895 字节；最终 JS 修正复用源文件、头文件及编译选项均一致的 146 个已验证对象重新链接 |

候选 Wasm 为 `3786901cbe373d221b14f02bcb3b1fa77901512195a09ba080669753a915018c`。浏览器主机实现、队列、异步 shell、真实 SDL3 构建和本地管理式运行目录已准备；未执行普通 Chrome 验收，现有默认 WebGL 预览仍保持原版本。候选没有强制关卡、无敌或完成游戏的诊断控制导出。

本地字体／FLAC 共 414,850,582 字节通过哈希验证后的生成缓存建立不可变别名，避免再次复制。原版归档和原版音乐容器没有建立硬链接。游戏资源、生成资源、图片、原始缓冲、DLL、Wasm、对象文件、录像与存档不随源码发布。

画布呈现另有两个合成格式控制。原生 OffscreenCanvas 的 BGRA8 与 RGBA8 GPU 原字节均正确；标准 PNG 解码后，BGRA8 导出出现红蓝通道互换，RGBA8 导出控制正确。检查器保留该失败，生产呈现着色器未据此添加通道交换。这个控制使用额外 `COPY_SRC` 权限检查 GPU 字节，不能当作 Chrome 或系统合成器画面验收。

[独立复核报告](th14-js-webgpu-verified-oct26.json)及[检查器](../../tools/th14-js-webgpu-evidence-oct26.py)重读完整 Stage／D3DX／矩形缓冲、异步结果、PNG 数据、Application 场景断言和实际文件，核对源码、冻结构建、对象复用、候选 ABI 与资源别名。原生 JS 组件没有浏览器、DOM、真实 SDL 窗口、物理输入或音频设备。Application 的归一化输入／虚拟平台流程和浏览器候选编译分别判断；它们不是原版普通菜单或 IndexedDB 证明。

```powershell
python tools/th14-build-webgpu-async-component.py `
  --lifetime-shim-build PATH_TO_RETAINED_NATIVE_COMPONENT_BUILD `
  --output artifacts/th14/NEW/stage-build
deno run --unstable-webgpu --allow-read --allow-write=artifacts/th14/NEW/stage `
  tools/th14-webgpu-js-component.mjs --build artifacts/th14/NEW/stage-build `
  --reference PATH_TO_RETAINED_STAGE_REFERENCE --output artifacts/th14/NEW/stage
python tools/th14-build-webgpu-release.py `
  --base-commit faee616ae3be0ee38c66c0d7fd69a2f3da2300e0 `
  --output artifacts/th14/NEW/browser-build
python tools/th14-package-webgpu-candidate.py `
  --build artifacts/th14/NEW/browser-build --output artifacts/th14/NEW/browser-runtime
```

Native Deno 控制使用 `DENO_WEBGPU_BACKEND=dx12`，设备不请求可选特性。Deno 二进制来自官方 v2.9.8 发布并核对官方 SHA256；它仅用于原生 GPU API 单元验证，没有启动 Deno 的桌面浏览器或窗口。参考 [Deno GPU API](https://docs.deno.com/api/web/gpu/)、[实际后端选择源码](https://github.com/denoland/deno/blob/v2.9.8/ext/webgpu/lib.rs)及 [Emscripten Asyncify 文档](https://emscripten.org/docs/porting/asyncify.html)。SDK 组件明确使用无真实窗口的 SDL 生命周期边界；浏览器候选使用真实 SDL3，后者的运行验收仍独立开放。

所有输出写入新私有目录并保留至少 100 GiB 空间。浏览器策略检查此前因无法可靠识别当前 URL 终止；本轮没有重试该失败、发送应用输入或请求手动 Ctrl+L，也没有通过其他浏览器、CDP 或 DOM 替代物绕过。普通 Chrome 的启动／呈现／输入／音频／刷新及持久化、完整模式和历史相机／effect149 字差继续验收。一般打包目标光栅混合、部分 stencil 与加权捕获也保留其范围。`browserAcceptance=false`、`completeGame=false`、`nativeEquivalent=false`。

后续[父 Launcher 与实际 Application 续关流程](TH14_LAUNCHER_CONTINUE_OCT26.md)补齐独立静音候选入口，并在两个原生后端完成自然 GameOver／续关／恢复射击的有限集成。原版普通菜单与浏览器范围继续开放。

后续新增[矩形 stencil 清除修复](TH14_STENCIL_CLEAR_OCT26.md)，以独立 HAL、实际 C++／Asyncify／JS 与原生 Python 设备控制另行验证，当前 21／8 图像回归通过。本文较早运行及浏览器候选保留原版本范围，不自动继承到新宿主。

当前 stencil 宿主随后装入[新本地候选包](TH14_STENCIL_CLEAR_OCT26.md)，146 个 C++ 对象输入相同并复用，完整 Wasm 字节不变，独立包与 Launcher HTTP 检查通过。普通浏览器与系统呈现范围仍未验收。
