# TH14 实际 C++ Renderer 的 WebGPU 接入 · 2026-10-26

本页记录此前 C++／原生 GPU 接入的冻结证据；后续[JavaScript 主机、Asyncify 与浏览器候选包](TH14_JS_WEBGPU_OCT26.md)另行核对。

实际 `Renderer` 新增显式选择的 `TH14_WEBGPU_BACKEND` 分支。生产的状态、批处理、实例记录、矩阵组合、布局读取及纹理解码仍由 C++ 执行；平台只接收语义管线、派生矩阵、展开纹理和顶点字节。与先前 Python／WGSL 镜像组件相比，本次运行实际 C++ 渲染入口及 Application。默认 GLES／WebGL 分支保持原行为。

| 验证对象 | 严格有限范围结果 |
| --- | --- |
| 保留的原版 D3D9 Stage 绘制参考 | 21／21 完整缓冲一致，共 25,804,800 字节，Stage 3 原先的一个蓝通道差异也消失 |
| 原版 D3DX POINT 捕获参考 | 8／8 完整缓冲一致，共 5,242,880 字节，包含 RGB565、ARGB8、偏移及缩放控制 |
| 实际 Application 与默认 GLES 成对运行 | 保存／回放 1,286 帧、新进程读回 722 帧，共 239 项状态断言、18 幅画面、静音 PCM 和实际保存文件逐字节一致 |

另检查部分矩形清屏、CPU 修改后的版本失效、GPU 复制及读回，保存完整控制缓冲供独立复算。分数和录像实际文件再经原版 x86 codec 解密／解压；原版分数加载器读取全部 149,076 字节，原版写回的完整分数文件一致。新进程读回后三个文件未改变。

后端使用裁剪后的浮点视口、原语投影安全判断和实际设备测得的 RGBA8 alpha 阈值。RGB565 通过 5／6 位复制扩展到 8 位；捕获着色器先计算原格式的量化值，再扩展为采样字节。渲染目标的半像素边缘使用额外一行／列，采样时复制逻辑尺寸，避免纹理 UV 被填充尺寸改变。相同目标内的绘制、更新、捕获、复制、读回和提交保持调用顺序。

测试平台是独立的 WASI／wgpu-native D3D12 组件，无浏览器、DOM、真实 SDL 窗口、物理输入或音频设备。未请求可选 WebGPU 特性。Application 链接 141 个已冻结游戏对象；新编译 Application、设备及 Renderer 的绑定与复用对象来源分别保留，未声称工作区全部游戏源码重新编译。

成对 Application 测试声明 `--metadata-epoch 1792965600`，WASI 实时时钟从该 UTC 秒值随虚拟帧时钟推进。`std::time` 写出的录像时间及菜单时间文本因此可直接逐字节比较；没有屏蔽时间区域或修改输出像素。未控制元数据时钟的探索记录另行保留，其两幅录像列表图像随实际保存时间变化，不当作渲染通过证据。

[独立检查器](../../tools/th14-cpp-webgpu-evidence-oct26.py)复算[范围报告](th14-cpp-webgpu-verified-oct26.json)中的源文件／构建／工具绑定、全部参考缓冲、矩形控制、场景断言、18 幅成对缓冲及实际文件。检查器只处理本次所列有限场景。原版资源、图像、录像、存档、DLL、对象文件和 Wasm 不随源码发布。

```powershell
python tools/th14-build-native-gles-component.py --backend webgpu `
  --output artifacts/th14/NEW/stage-build
python tools/th14-native-webgpu-component.py `
  --build artifacts/th14/NEW/stage-build --reference PATH_TO_RETAINED_STAGE_REFERENCE `
  --wgpu-site PATH_TO_LOCAL_WGPU_PACKAGE --wasmtime-site PATH_TO_LOCAL_WASMTIME_PACKAGE `
  --output artifacts/th14/NEW/stage
python tools/th14-build-native-gles-component.py --backend webgpu `
  --fixture runtimes/th12/th12_web/tests/cpp/th14-webgpu-surface-fixture.cpp `
  --output artifacts/th14/NEW/surface-build
python tools/th14-native-webgpu-surfaces.py `
  --build artifacts/th14/NEW/surface-build --reference PATH_TO_RETAINED_D3DX_REFERENCE `
  --wgpu-site PATH_TO_LOCAL_WGPU_PACKAGE --wasmtime-site PATH_TO_LOCAL_WASMTIME_PACKAGE `
  --output artifacts/th14/NEW/surfaces
```

Application 使用 [既有流程](TH14_NATIVE_APPLICATION_OCT26.md)的构建／运行命令，加 `--backend webgpu`、本地 `--wgpu-site` 及上述 `--metadata-epoch`；对照构建使用 `--backend gles` 和同一个元数据时钟。所有输出使用新的私有目录，至少保留 100 GiB 空间。工具不下载游戏或安装运行库。

尚未实现浏览器 WebGPU 主机、异步初始化／读回与画布呈现；不启用发布入口的新后端。默认 WebGL 仍保留既有 20／21 和一个蓝通道差异，重构后的完整缓冲与保留浏览器记录一致。打包格式目标上的一般光栅混合及部分 stencil 清除明确拒绝；加权捕获着色器、其余格式、深度和管线组合仍需单独原版控制。Stage 参考保留原有屏幕队列排除，成对 Application 画面也不是原版普通菜单画面对照。完整模式、相机交错、effect149 地址／ABI、音频、普通原版界面和浏览器持久化验收仍待完成。`browserAcceptance=false`、`completeGame=false`、`nativeEquivalent=false`。

后续新增[矩形 stencil 清除修复](TH14_STENCIL_CLEAR_OCT26.md)，以独立 HAL、实际 C++／Asyncify／JS 与原生 Python 设备控制另行验证，当前 21／8 图像回归通过。本文较早运行及浏览器候选保留原版本范围，不自动继承到新宿主。

2026-10-27 新增[Bgrx8 清除／绘制目标](TH14_BGRX_RASTER_OCT27.md)，两条实际 C++ 宿主路径在 1,344 个设备用例中分别比较全部 4,032 份实际 D3DX 规范化缓冲一致；原始 X 字节也保留。当前 21／8／96 图形回归通过，16 位打包光栅与原有混合格式复制继续开放。本文较早完整 Application 和浏览器构建仍保留实际版本范围。
