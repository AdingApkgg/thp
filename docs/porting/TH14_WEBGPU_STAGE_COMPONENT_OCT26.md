# TH14 WebGPU 阶段图形组件 · 2026-10-26

独立 WebGPU 组件执行保留的 21 组 Stage 图形命令流，包含一至七面各 0／599／1199 更新边界、1,005 次直接绘制。全部 25,804,800 字节与既有原版 D3D9 离屏参考一致，没有像素容差。该组件使用 WGSL 表达所列固定功能子集，并未执行生产 C++ Renderer；当前生产 WebGL 的 20／21 结果及浏览器未验收状态保持不变。

组件使用裁剪后的浮点视口 `x + 0.5 / y + 0.5`，保留矩阵计算、八位子像素取整、雾、颜色运算、混合、D16 深度和实际设备测得的 Alpha 转换边界。此前独立 D3D11 视口控制已表明这个次序可消除原有差异；现在在 WebGPU API 中完成同一有限命令流的控制，而不是修改某个失败帧的颜色。

RGB565 转换也需要匹配原设备的采样路径：五位通道按 `(v << 3) | (v >> 2)`，六位按 `(v << 2) | (v >> 4)` 展开为 BGRA8。直接除以 31／63 存入浮点纹理，或将归一化值四舍五入到八位，都不是本组件中已验证的转换。独立采样器实验遍历全部 65,536 个 RGB565 编码，最近采样比较原生 GLES RGB565 与 BGRA8；固定四分之一 texel 的线性采样另比较 GLES 与 WebGPU，三组共 786,432 个浮点字均一致。该结论绑定报告所列 NVIDIA 设备、驱动和 ANGLE／wgpu-native 实现，不能扩大为所有采样坐标和设备。

本次使用 [wgpu-py](https://github.com/pygfx/wgpu-py) 0.32.0 的独立 Windows D3D12 设备。阶段组件没有请求可选 WebGPU 特性，也未打开窗口、浏览器或音频设备。[独立检查器](../../tools/th14-webgpu-stage-evidence-oct26.py)重读每幅完整缓冲及所有采样字，绑定工具、WGSL、生产数学源码、命令、纹理、参考和实际加载库哈希；见[范围报告](th14-webgpu-stage-verified-oct26.json)。

```powershell
python tools/th14-webgpu-stage-component-oct26.py `
  --wgpu-site PATH_TO_LOCAL_WGPU_PY_PACKAGE `
  --reference artifacts/th14/stage-gpu-stream-replay `
  --output artifacts/th14/NEW_WEBGPU/replay --frames 21
python tools/th14-webgpu-rgb565-sampler-oct26.py `
  --wgpu-site PATH_TO_LOCAL_WGPU_PY_PACKAGE `
  --angle-directory PATH_TO_ANGLE_DLLS `
  --output artifacts/th14/NEW_WEBGPU/sampler
python tools/th14-webgpu-stage-evidence-oct26.py `
  --home artifacts/th14/NEW_WEBGPU
```

依赖为本地 wgpu-py／NumPy，采样器控制另用已有独立 ANGLE DLL。工具不安装依赖，输出拒绝覆盖已有目录，保留单次 2 GiB 和至少剩余 100 GiB 的存储检查。原始游戏纹理、像素、浮点缓冲和库文件不随源码发布。

下一步仍需接入真正的生产渲染路径，核对同步读取、暂停捕获、所有 Surface／深度目标和普通 Application 流程，再执行真实浏览器验收。原版参考保留其受控初始状态和屏幕队列排除范围，不是原作整局帧缓冲。`productionWebgpuBackendImplemented=false`、`productionWebglFix=false`、`browserAcceptance=false`、`completeGame=false`、`nativeEquivalent=false`。
