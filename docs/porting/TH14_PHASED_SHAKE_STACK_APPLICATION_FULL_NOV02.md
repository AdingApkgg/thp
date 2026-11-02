# TH14 分阶段震屏核心的完整双后端 Application 回归

游戏核心版本固定为 `2f42560318202a997514d9644adb549db548964a`，本结果不自动适用于后续核心。[检查范围与哈希](th14-phased-shake-stack-application-full-nov02.json)。

GLES 和 WebGPU 均实际完成 122,622 帧、45 项断言：普通菜单进入灵梦 B Normal 完整 Replay，第 122,562 帧自然回到结束菜单，随后稳定 60 帧。两个进程正常退出，没有预算中止；运行耗时分别为 1,230.974 秒与 2,520.330 秒。双后端独立检查在取得两个成功终态后通过。

每个后端八幅完整 BGRA 图像、对应全部捕获 VM、所选日志、文件及录像均与封存 GLES 参考一致。离线混音得到 89,969,664 帧 PCM，SHA-256 为 `39e9d4e4c65b7dea3b259e7a83189c06b7aaf28d76ef71bf9942a5c005453b54`；物理音频设备打开数为零。检查绑定实际 141 个核心对象、各应用构建、Wasm 和实际编译的冻结源码及头文件。

复核需要保留本地私有记录及编译产物：

```powershell
python tools/th14-phased-shake-stack-application-full-evidence-nov02.py --webgpu-home artifacts/th14/phased-shake-stack-applications-nov02/full-webgpu --gles-home artifacts/th14/phased-shake-stack-applications-nov02/full-gles --output docs/porting/th14-phased-shake-stack-application-full-nov02.json --check
```

最初单后端检查器因读取错误的证明字段而失败；修正字段后分别重新验证 GLES 和完整双后端，旧失败记录保留。宿主时钟、熵、文件与异步资源交付仍是声明的平台输入。此项不证明整局原版像素或 PCM、独立线程调度、普通原版 GUI、浏览器表现或全部模式等价。30 个自然结束模式、27 个全部目标关卡入口模式的范围不变；整作 1:1 未完成。
