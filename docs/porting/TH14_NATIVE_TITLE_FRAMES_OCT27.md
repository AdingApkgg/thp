# TH14 实际原版标题整帧与空闲计数修复 · 2026-10-27

修正两处生产调用：标题界面不再额外绘制 FPS；首次标题激活不再提前增加空闲计数。两份实际原版 D3D9 后缓冲各 1,228,800 字节，分别在空闲计数 51 和 231 时与实际 C++ Application 的 GLES 输出完全一致；完整菜单的 231 帧在 WebGPU 下也完全一致。比较包含所有 BGRA 通道，容差为零。

这是有限标题帧验收。实际动画句柄／图层比较仍失败，进入演示后的两后端画面也保留一个像素、两个字节的差异。整作、原版普通游戏流程、完整音频和浏览器验收继续进行。

## 原版采样与声明的诊断介入

[原版观察器](../../tools/th14-native-device-observer-oct27.py)创建独立、隐藏、音量为零的原作进程，使用完整原版 DAT 和隔离工作输入。硬件断点观察实际 CreateDevice：640×480，格式 21（A8R8G8B8），返回后缓冲数量为 1。随后在声明的第 240 或 420 次 Present 入口停止同一渲染线程。

实际像素回读明确包含诊断介入：分配私有代码／数据页，将代码页改为只读可执行，两次重定向被观察渲染线程的上下文，调用 GetBackBuffer、GetDesc、CreateOffscreenPlainSurface、GetRenderTargetData 和 LockRect；复制全部四通道后 UnlockRect、Release 两个临时引用，结束该独立进程，不恢复游戏。原有指令、游戏字段、RNG 和输入未写入。不能将这种采样称为未插桩原作、窗口截图或普通用户界面验收。

[回读程序生成器](../../tools/th14-native-frame-readback-program-oct27.py)按实际 SDK 接口生成调用。18 组 ABI 控制包含五处负 HRESULT 的提前停止；实际捕获的五个主要 HRESULT 全为零，清理返回为 `[0,0,1]`，独立进程均已退出。第 420 次采样另在诊断调用前读取普通／叠加活动注册链和全部 VM 字节；420 个 Present 上的归一化输入掩码均为零，这不是物理输入事件记录。早期第 240 次采样未记录该掩码序列。

## 首差与生产修复

最初空闲计数 51 的画面有 203 像素、630 字节不同，全部位于额外的 FPS 标签。实际原指令 `42e5c3..42e5d7` 在 Supervisor 模式 4 和 15 跳过该标签；16 组[原指令守卫](../../tools/th14-native-fps-guard-oct27.py)通过。这里只证实标题对应模式 4，未补称其他 C++ 场景的模式 15 映射已完成。

去掉标题标签后，空闲计数 231 的完整菜单仍有 27,980 像素、47,122 字节不同。GLES／WebGPU 的输出相同；相同外部启动 tick 和进程 cookie 下，两组 RNG 的种子与调用次数也相同。按唯一文件／脚本配对，30 个动画的年龄都少一拍，四个颜色／透明度值不同。

原版 `459944..45995c` 只在 Title 状态已为 1 时增加空闲计数；首次状态 0 的回调随后初始化并执行第一次主菜单更新。C++ 已将 TitleMenu 构造为 Main，原先因此提前计数。现在首次 session 帧保留空闲计数，继续正常菜单与动画更新。36 组[原指令控制](../../tools/th14-native-title-idle-guard-oct27.py)覆盖状态、空闲计数和输入，无逐帧覆盖、额外动画 tick、种子注入或像素补丁。

| 原版 Present／空闲计数 | C++ 后端／Application 帧 | 完整比较 |
| --- | --- | --- |
| 240／51 | GLES／235 | 1,228,800 字节全部相同 |
| 420／231 | GLES／415 | 1,228,800 字节全部相同 |
| 420／231 | WebGPU／415 | 1,228,800 字节全部相同 |

帧配对依据是原版空闲计数及启动输入，未按画面挑选偏移。原版与 C++ 的加载回调数量不同，不声称物理时间和工作线程调度相同。

## 保留的失败与复核

[只读标题夹具](../../runtimes/th12/th12_web/tests/cpp/th14-native-title-fixture.cpp)调用生产 Application，额外导出启动输入、空闲计数、RNG 和活动动画。`-fno-access-control` 仅用于读取私有计数；不修改游戏状态。使用[构建工具](../../tools/th14-build-native-application.py)的 `--title-observer` 选项可构建两个后端。[进程输入宿主](../../tools/th14-native-application-process-host-oct27.py)只将声明的初始 tick 加到游戏时钟导入，不移动 SDL／WASI 相对时间；cookie 为外部输入。

[严格图像比较器](../../tools/th14-native-title-image-compare-oct27.py)在写出失败报告后以非零退出码结束。修复前后原始失败均保留。[严格 303 字 VM 比较](../../tools/th14-native-title-live-compare-oct27.py)修复后仍失败：30 对象中存在句柄池槽差异及根脚本的 layer 0／22 差异，共 62 项严格差异。另行按唯一文件／脚本配对并显式映射链接句柄，仅作诊断；在此诊断下颜色、年龄、插值、矩阵和链关系相同，剩一个 layer 字不同。该映射不作为严格 VM 验收。

受标题计数修改影响，两后端分别重跑至首次演示进入后的 240 拍：2,265 个 Application 帧、7 项断言、131 行状态、1,508,352 帧静音 PCM sink 和文件相同，标题画面也相同。但演示图像 `(32,166)` 的 R／A 分别为 GLES `155/243`、WebGPU `117/233`，严格图像比较失败。尚未取得这次实际绘制的独立原版裁决，未将失败归因给本次修改，也未继承旧冻结版本的完整演示回归。

[范围复核工具](../../tools/th14-native-title-evidence-oct27.py)重新读取实际后缓冲、夹具输出、RNG、编译对象和失败报告；[摘要](th14-native-title-verified-oct27.json)只发布哈希与元数据。原版资产、原始内存、图像、录像、诊断二进制和编译产物均不发布。

```powershell
python tools/th14-native-title-evidence-oct27.py --check
```

模式覆盖仍为 30／25；[剩余验收清单](TH14_REMAINING_ACCEPTANCE.md)继续保留普通流程、模式覆盖、历史相机／effect149、Stage 像素、完整音频及浏览器持久化／输入。测试与预览静音，保持 100 GiB 空闲下限及每例 128 MiB 新观察输出限制。`completeGame=false`、`nativeEquivalent=false`、`browserAcceptance=false`。

源码 `4a843e6` 已构建为静音 8224 候选，包含上述两处标题修复。146 个单元中只重编修改过的 GameSession／Application，144 个对象按完整头文件清单、编译参数、源码哈希及旧对象哈希核对后复用；出现头文件修改、输入清单变化或源码包含其他 `.cpp` 时拒绝此复用路径。28 份生成字体／音乐资源继续别名复用，未复制原版资产。133 条路由／21 项 HTTP 检查通过，实际服务的 Wasm、宿主、着色器和默认静音脚本逐字节核对。[候选摘要](th14-native-title-candidate-verified-oct27.json)保留编译／复用数及冻结来源，浏览器界面与持久化尚未验收。

```powershell
python tools/th14-local-candidate-evidence-oct27.py --home artifacts/th14/native-frame-readback-oct27 --expected-code-commit 4a843e67c262cf6a7968fd71291a80b062e5bbb8 --output docs/porting/th14-native-title-candidate-verified-oct27.json --reuse-build artifacts/th14/attract-run-flags-oct27/browser-candidate --check
```
