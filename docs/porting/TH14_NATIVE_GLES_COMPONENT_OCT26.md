# TH14 原样 C++ 渲染器的独立 GLES 组件 · 2026-10-26

现在可在独立 EGL 离屏表面运行当前生产 C++ 渲染器，不依赖浏览器交互来定位已有背景差异。该组件复现上次实际浏览器记录的全部 21 幅输出哈希和全部 38 份着色器源码哈希；对原版 D3D9 参考的严格结果仍是 20／21，三面 1199 帧 `(144,373)` 蓝色 119／120 的失败保持不变。

构建直接复制生产 `Renderer.cpp/.hpp`、状态、着色器、透明度和重采样文件，使用仓库现有 Stage 图形流夹具。仅将 SDL 的生命周期替换为无窗口的确定性替身，将 GLES 调用保留为 Wasm 导入；实际绘制、缓冲、纹理、深度、混合、着色器编译和读取均由独立 ANGLE D3D11 执行。`EXT_clip_control` 与留存浏览器配置相同。没有重写固定功能着色器，没有从原版像素生成运行时补丁。

[范围报告](th14-native-gles-component-oct26.json)包含源码、构建、Wasm、工具、纹理、原版缓冲、全部输出、ANGLE DLL 和历史浏览器报告哈希。当前组件 Wasm 为 `1d1c57505ce7bf2a6323102ed66e423c2fa56278cb6cbeceb5cb128374eb5379`。入口为：

```powershell
python tools/th14-build-native-gles-component.py --output artifacts/th14/NEW/build
python tools/th14-native-gles-component.py `
  --build artifacts/th14/NEW/build `
  --reference artifacts/th14/stage-gpu-stream-replay `
  --angle-directory PATH_TO_STANDALONE_ANGLE_DLLS `
  --wasmtime-site PATH_TO_LOCAL_WASMTIME_PYTHON_PACKAGE `
  --output artifacts/th14/NEW/replay `
  --browser-baseline artifacts/th14/current-gpu-baseline-oct25/color/capture/report.json
```

依赖为本地 WASI SDK、Emscripten GLES 头文件、Windows x64 ANGLE DLL 和 Wasmtime Python。本次使用 Wasmtime 50.0.1。工具不会安装依赖、启动 DLL 所属应用、打开浏览器、发送应用输入或打开音频设备。组件保留单次 2 GiB、磁盘至少剩余 100 GiB 的检查。参考图像存在字节差时退出码为 1；复现历史浏览器结果不改变这一失败门槛。

这只覆盖已保留的 Stage 命令流、显式初始状态和原夹具列出的屏幕队列排除范围。历史浏览器记录是读取的对照文件，不能作为当前浏览器验收。没有完成原版实际整帧、全部图形路径、普通游戏、当前发布版浏览器或整作 1:1 验收。生产渲染器未修改，原始纹理、像素、DLL 和 Wasm 不发布。

独立实验曾使用深度钳制及片元近／远面拒绝，结果该帧出现 32 个通道差，未采用。此前 [裁剪次序组件](TH14_BACKGROUND_CLIP_ORDER_OCT26.md)的结论及剩余 WebGL 修复要求保持有效。

进一步的原生视口对照已覆盖全部 21 幅画面：保留同一组件 Wasm、矩阵／顶点／状态／纹理和所有片元着色器，只从提交的顶点着色器移除半像素偏移，再在该离屏组件自己的 D3D11 视口中于裁剪后施加偏移。21／21 幅完整缓冲均与原版参考逐字节一致。八位子像素取整仍保留，屏幕顶点路径不改。独立检查器重新读取所有缓冲、复算差异并验证仅一份顶点着色器改变，见[检查器](../../tools/th14-native-gles-viewport-evidence-check.py)与[范围报告](th14-native-gles-viewport-verified-oct26.json)。

这项控制使用私有离屏进程中的原生 D3D11 视口干预，不是生产 WebGL 修复，也没有访问浏览器或其他应用。它将此前隔离绘制的裁剪次序证据扩展到了同一有限命令流的全部画面。生产 WebGL 仍为 20／21；适用于 WebGL 的实现及其他图形范围继续待验收。

后续[独立 WebGPU 组件](TH14_WEBGPU_STAGE_COMPONENT_OCT26.md)也通过同一 21 组有限命令流，并用全 RGB565 编码采样控制核对位复制到 BGRA8 的转换。它使用 WGSL 镜像而非当前 C++ Renderer，尚待生产接入，未改写本组件或 WebGL 的验收结果。
