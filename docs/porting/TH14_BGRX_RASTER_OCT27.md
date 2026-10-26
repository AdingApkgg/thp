# TH14 WebGPU Bgrx8 渲染目标 · 2026-10-27

生产 C++ WebGPU 分支现在接受 Bgrx8 清除和绘制目标。它原先虽能上传和读回这种格式，却在目标绑定时统一拒绝。新实现保留源 alpha 供混合使用，将 X8 清除的 GPU alpha 设为 1，并在绘制时屏蔽 alpha 存储写入，使后续目标 alpha 混合保持正确。

修改位于 [WebGpuRenderer.hpp](../../runtimes/th12/portable/sdl/WebGpuRenderer.hpp)。玩法及音频未改；16 位打包光栅目标和此前不支持的混合格式复制没有据此启用。

## 设备参考与 X 字节

首次控制假设 X8 的原始高字节总为 255，实际设备立即否定了它。当前固定 D3D9 HAL 的 X8 原始高字节在这些用例中均为 0。将这些字节自行忽略或改为 255，不能证明格式语义。

[新设备控制](../../tools/th14-bgrx-raster-hal-control-oct27.py)保留全部原始读回，并实际调用安装的 D3DX 将目标转换为 ARGB8。X8 的实际转换结果 alpha 为 255，RGB 与原始读回一致；A8 控制的全部字节转换前后相同。移植输出与这些真实转换缓冲逐字比较，四个通道全部保留。原始 X8 高字节也另行核对和归档；不声称重现无用途存储位的所有硬件取值。

1,344 个用例由 A8／X8 两种目标、四种清除 alpha、八类混合、七种颜色写掩码和三种源 alpha 组合而成。每例包含完整／重叠矩形清除、第一次绘制，以及依赖已存目标 alpha 的第二次区域混合。X8 的 672 次后续混合还由独立字节期望核对，验证目标 alpha 的实际含义。

| 路径 | 完整结果 |
| --- | --- |
| D3D9 HAL 与实际 D3DX 转换 | 1,344 例，原始与规范化缓冲均保留 |
| 生产 C++ → Emscripten／Asyncify → JS WebGPU | 4,032 份、4,128,768 字节全部与参考一致 |
| 生产 C++ → WASI／原生 GPU 宿主 | 同一批 4,032 份缓冲全部一致 |
| 当前 Stage 回归 | 21／21 幅，25,804,800 字节一致 |
| 当前 D3DX 捕获回归 | 8／8 份，5,242,880 字节一致 |
| 当前 stencil 清除回归 | 96 例，384 份、4,718,592 字节一致 |

两条 C++ 路径分别使用[同一夹具](../../runtimes/th12/th12_web/tests/cpp/th14-bgrx-raster-fixture.cpp)，运行工具见 [JS 路径](../../tools/th14-webgpu-bgrx-raster-control-oct27.mjs)和[原生路径](../../tools/th14-native-webgpu-bgrx-control-oct27.py)。原生模块保留了一些未执行的 GLES 回退导入；它们绑定到一旦调用即失败的陷阱，实际调用数为零。没有以空函数代替绘制。

初始 C++ 拒绝、原始 X 字节假设失败，以及原生工具最初拒绝未执行导入的诊断均保留。通过结论只对应实际完成的两条完整运行；工具源码在启动时冻结。

## 独立复核与存储

[独立检查器](../../tools/th14-bgrx-raster-evidence-oct27.py)读取全部原始、实际 D3DX 转换、JS 与原生缓冲，重新检查清除、无混合写掩码和目标 alpha 链的字节期望，并核对全部当前图形回归。像素不写入公共元数据；[范围报告](th14-bgrx-raster-verified-oct27.json)绑定私有逐文件清单、完整数据集合摘要、源码、构建及工具版本。

```powershell
python tools/th14-bgrx-raster-evidence-oct27.py --home artifacts/th14/bgrx-raster-oct27 --output docs/porting/th14-bgrx-raster-verified-oct27.json --check
```

磁盘接近既定余量时，对 24 份已结束采集的自生成原始缓冲执行 NTFS 透明压缩：833,675,368 字节内容存入 181,379,072 字节，全部路径和内容哈希保持不变，没有删除证据。发布构建工具新增逐编译单元、链接前及链接后的容量检查，继续使用 100 GiB 余量与 2 GiB 输出约束。

本次 C++ 图形变化尚未进入新的完整浏览器候选；此前 8214 入口仍绑定其实际构建版本。现有整局、异步与 UI 证据不继承给新 C++。普通浏览器、IndexedDB、原版普通流程、完整格式光栅、历史单像素及相机／effect149 差异和整作 1:1 继续待验收。原版资源、录像、原始像素、DLL 和 Wasm 不随源码发布。
