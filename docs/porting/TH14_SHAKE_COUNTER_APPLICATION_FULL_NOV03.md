# TH14 震屏计数修复核心的完整双后端 Application 回归

本项固定绑定游戏核心 `22c4f853fc1cb81b8a0c0891b88023f2f5dc065e`。[检查范围与哈希](th14-shake-counter-application-full-nov03.json)。

GLES 和 WebGPU 均实际完成 122,622 帧、45 项断言：从普通菜单进入灵梦 B Normal Replay，第 122,562 帧回到结束菜单，继续稳定 60 帧。两份进程正常退出且没有触发预算限制；实际耗时分别为 1,377.733 秒和 2,827.189 秒。双后端独立检查在两份成功终态后通过。

每后端八幅完整 BGRA 图像及全部捕获 VM、所选日志、文件和录像与封存 GLES 参考一致。离线混音 89,969,664 帧 PCM 的 SHA-256 为 `39e9d4e4c65b7dea3b259e7a83189c06b7aaf28d76ef71bf9942a5c005453b54`；物理音频设备打开数为零。检查绑定 141 个核心对象、应用对象和实际编译的冻结源码／头文件。

WebGPU 的首次沙箱内尝试在设备初始化时以 `0xC0000005` 退出，记录保留。相同 D3D12 最小设备探针在默认沙箱失败、在允许访问 GPU 后成功；本报告使用后者条件下同一构建实际完成的重试，不把失败尝试算作通过。

复核需要本机私有记录和编译产物：

```powershell
python tools/th14-shake-counter-application-full-evidence-nov03.py --webgpu-home artifacts/th14/shake-counter-applications-nov03/full-webgpu-retry --gles-home artifacts/th14/shake-counter-applications-nov03/full-gles --output docs/porting/th14-shake-counter-application-full-nov03.json --check
```

宿主时间、熵、文件与异步资源交付仍为声明的平台输入。本项不证明整局原版像素／PCM、独立线程调度、普通原版 GUI、浏览器表现、源录像 EOF 或所有模式等价；整作 1:1 未完成。
