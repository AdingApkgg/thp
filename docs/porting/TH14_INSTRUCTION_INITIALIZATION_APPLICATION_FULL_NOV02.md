# TH14 指令初始化核心的完整 Application 回归

2026-11-02。源码核心 `50d212bab4114ecb05472b2ad805873f11840cd2` 的 GLES 和 WebGPU 各实际完成 122,622 帧、45 项断言；在第 122,562 帧自然结束后保持 60 帧稳定。两进程均正常退出，独立双后端检查通过。GLES 用时 1,234.593 秒，WebGPU 用时 2,694.439 秒。

复核绑定重新编译的 141 个游戏对象，以及各自平台构建、实际终态和完整日志。八幅完整 BGRA 缓冲、全部所捕获 VM 状态、动作／场景断言、录像和文件均与封存 GLES 参考一致；每后端离线音频输出 89,969,664 帧，累计 SHA256 为 `39e9d4e4c65b7dea3b259e7a83189c06b7aaf28d76ef71bf9942a5c005453b54`。物理音频设备开启数为零；离线音频内容并非全零。

这是声明平台时钟和外部输入下的实际 C++ Application 回归。它没有验收原版普通 GUI、原版整局像素／PCM、独立线程调度或浏览器；不能继承给随后修改的核心。模式仍为 30 组自然记录／27 组全部关卡入口，整作 1:1 未完成。

[版本绑定证明](th14-instruction-initialization-application-full-nov02.json)只包含源码路径和哈希元数据，原版资源、Replay、原始内存、图像、PCM 与 Wasm 均保留本机。

```powershell
python tools/th14-instruction-initialization-application-full-evidence-nov02.py --webgpu-home artifacts/th14/instruction-initialization-applications-nov02/full-webgpu --gles-home artifacts/th14/instruction-initialization-applications-nov02/full-gles --output docs/porting/th14-instruction-initialization-application-full-nov02.json --check
```

该命令在本次发布的源码状态下复核；后续游戏源码变化时，应使用此冻结版本核验，不把旧证据当作新核心验收。
