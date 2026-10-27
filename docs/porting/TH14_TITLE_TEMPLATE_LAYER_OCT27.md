# TH14 标题工厂保留模板图层 · 2026-10-27

标题 `file=0` 的创建路径现在保留模板图层。原版根脚本 0 为 layer 0，移植版先前强制指定 22；子动画继续按自身脚本设置可见图层。改动限于 TH14 的此创建路径。

实际原版第 420 次 Present 前读取的 30 个活动 VM 已包含这个 layer 0。另以[原指令前缀控制](../../tools/th14-native-title-template-layer-oct27.py)执行 `458d70`：声明分配与模板复制两个服务，使用脚本 0／86／91 和模板图层 0／7／22／35 共 12 例，在真实 `46fe50` ANM 更新入口前停止。所有输入图层均保留；该组件未执行 ANM 更新或注册发布，不称为完整原版工厂验收。

实际 C++ Application 重编 TitleMenu 一个核心对象、核对复用 140 个核心及五个平台对象后，空闲计数 231 的完整 1,228,800 字节仍与实际原版标题相同，启动输入和两组 RNG 相同。严格 303 字 VM 比较由 62 项差异降为 61 项，仍因句柄池槽及其链接不同而失败。按唯一文件／脚本配对、显式映射句柄仅作诊断时，30 对象的 9,090 个规范字已无其余差异；该映射不作为严格通过。

受此创建路径影响，另重跑实际 Application 至首个演示后的 240 拍：2,265 帧、七项断言，131 行状态、两幅图像、文件和 1,508,352 帧静音 PCM 与前一线段修复相同。未继承旧版完整演示或完整游戏回归。

[范围复核工具](../../tools/th14-title-template-layer-evidence-oct27.py)与[摘要](th14-title-template-layer-verified-oct27.json)绑定原版只读采样、声明服务的原指令前缀、实际对象和输出，保留严格失败。

```powershell
python tools/th14-title-template-layer-evidence-oct27.py --check
```

最新静音 8228 候选已绑定本项源码 `736103c`，包含标题 FPS、首次空闲计数、屏幕线段裁剪和模板图层四项修复。重编 TitleMenu 一个单元，核对复用 145 个对象；133 路由／21 HTTP 及实际服务 Wasm、宿主、着色器和静音脚本逐字节核对通过，见[候选摘要](th14-title-template-candidate-verified-oct27.json)。28 份生成资源继续别名复用，普通浏览器界面与持久化尚未验收。前一静音 8226 仍冻结 `d53076b` 的线段修复及全量编译结果。模式覆盖仍为 30／25，其余[剩余验收](TH14_REMAINING_ACCEPTANCE.md)继续；仅发布源码和元数据，不发布原版资产、原始内存／像素或二进制。所有测试静音，`completeGame=false`、`nativeEquivalent=false`、`browserAcceptance=false`。

```powershell
python tools/th14-local-candidate-evidence-oct27.py --home artifacts/th14/native-frame-readback-oct27/title-layer-delivery --expected-code-commit 736103cbc00c2067dbd72d9fd14ebbeef2694245 --output docs/porting/th14-title-template-candidate-verified-oct27.json --reuse-build artifacts/th14/native-frame-readback-oct27/line-browser-candidate --check
```
