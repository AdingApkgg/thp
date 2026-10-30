# TH14 裁剪与浏览器调度控制 · 2026-10-30

本组裁剪负控制没有引入 Renderer、着色器或浏览器时钟改动。随后独立完成的 [WebGPU 实例批次合入](TH14_WEBGPU_INSTANCING_OCT30.md)另有版本和验收绑定。默认 GLES 的 21 幅 Stage 参考仍为 20 幅完整一致，三面 1199 帧 `(144,373)` 的蓝通道 119／120 失败保留。WebGPU 的有限 Stage 21／21 结果不作为整作通过。

## CPU 裁剪的完整缓冲负控制

使用原先隔离的跨近裁剪面四边形，重新计算四个顶点。CPU 的 16 个 binary32 字与已有原版 D3D9 vs2／D3D11 dot4 控制逐字相同。因此本例不能再把差异归因于 CPU 矩阵点积；此结论只覆盖这四个输入。

六种插值精度与 1／2／6 个裁剪平面，分别接三种投影路径：原生小数视口、1024×512 整数视口，以及后者加 1／256 屏幕取整。共 54 例，每例检查全部 307,200 像素的覆盖和 UV 浮点字，完整缓冲通过数为零。对同一种 CPU 裁剪结果，三种投影路径的 18 对完整哈希全部相同。整数二次幂视口未解决裁剪误差，不能接入生产作为修复。

即使保留原生小数视口，最少仍有 17,723 个共同覆盖 U 字及 8,420 个 V 字不同；两项最小值可能来自不同用例。部分用例覆盖完全相同，仍不能称插值相同。另三个硬件控制也失败：关闭深度裁剪、将顶点 Z 改为 W／2，以及未偏移几何上的负半像素属性求值；它们均未改参考或生产代码。

微软说明关闭 [DepthClipEnable](https://learn.microsoft.com/en-us/windows/win32/api/d3d11/ns-d3d11-d3d11_rasterizer_desc) 仍保留 W 裁剪。这只是控制的 API 含义，不能从它推断当前 GPU 内部插值公式。下一步不能重复普通 CPU 裁剪加视口代数变换，也不能用目标像素颜色、容差或原版输出值补游戏运行时。

[复核工具](../../tools/th14-clip-projection-controls-oct30.py)重新核对输入变换、54 例报告、成对哈希与三个硬件控制，见[哈希元数据](th14-clip-projection-controls-oct30.json)。它不重新执行 GPU；原始输入、纹理、像素和着色器均留在私有目录。

## 独立于游戏的 RAF 低频

两个 Chrome 156 本机页面各采样 15 秒，同时记录 RAF、16ms 主线程定时器、独立 worker 定时器和长任务。第一份不创建画布；第二份持续更新 Canvas2D。两者均不加载游戏、Wasm、音频或请求 WebGL／WebGPU。Canvas2D 可能使用浏览器内部 GPU 加速，因此第二份不能称为完全无 GPU 工作。

| 页面 | RAF 总数 | 后半段 RAF 间隔中位数 | 主线程定时器 | worker 定时器 | 观测到的长任务 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 无画布 | 878 | 约 1005.5ms | 61.90Hz | 61.70Hz | 0 |
| 连续 Canvas2D | 24 | 约 1005.5ms | 62.41Hz | 62.14Hz | 0 |

第一份最初约五秒有接近 180Hz 的 RAF，随后降到约 1Hz；整段平均 58.51Hz 会掩盖这个停顿，不能拿平均数验收稳定 60 帧。两个页面的 DOM 可见性／焦点记录均为 visible／true；这不是操作系统遮挡状态的测量。结果证明低频可以独立于游戏复现，尚不证明唯一浏览器策略、OS 原因，或解释游戏本身的全部帧开销。

Chromium 的[窗口遮挡说明](https://blog.chromium.org/2021/12/chrome-windows-performance-improvements-native-window-occlusion.html)和[帧调度说明](https://www.chromium.org/developers/how-tos/trace-event-profiling-tool/anatomy-of-jank/)仅作为后续查证背景；本轮没有改浏览器设置、关闭保护或用替代时钟强行推进游戏。实际 8243 静音入口仍显示 C++／WebGPU 演示，未观察到控制台警告／错误；这些不代替完整浏览器验收。

[复核工具](../../tools/th14-browser-scheduling-control-oct30.py)读取两个完整调度记录并保留分段统计，见[范围元数据](th14-browser-scheduling-controls-oct30.json)。采样网页、原始时间序列和截图不公开。

## 当前继续工作

57a 核心的串行 WebGPU Application（Wasm `69839139b1e1ac9363335cb71485c09116510a2ec0b6f9cee2082a78c5383d8f`）已正常结束。完整灵梦 B Normal 实际 122,622 帧、45 项断言，全部动作／所选日志、八幅完整图像、文件和 89,969,664 帧静音 PCM 哈希与 GLES 一致。实际墙钟 4,184.91 秒；预先声明的上限为 150,000 帧、6,000 秒、至少 100GiB 空闲和单例 128MiB，旧 3,600 秒失败保留。

该冻结基线在生产改动前通过[严格检查器](../../tools/th14-reimub-webgpu-application-evidence-oct30.py)，证明保留旧版本绑定。新实例批次另跑完整流程，不自动继承旧 Renderer 整局结果。[内置浏览器跨宿主控制及普通录制](TH14_BROWSER_CROSSHOST_OCT30.md)进一步观察到 180Hz RAF、标题／演示 60fps，以及一份新短录像的普通保存／刷新／下载全部字节一致；这些均不验收全场景帧率。原版普通 GUI、整局原版画面／PCM、独立 worker、全模式继续开放，30／25 清单不变，`completeGame=false`、`nativeEquivalent=false`。
