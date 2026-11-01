# TH14 当前插值修复核心的完整双后端 Application

当前生产玩法核心为 `54cbc0cd05b5db6d8257ffa14dc1dcaf407a8754`，核心 Wasm 为 `1de2cbb429832670d52fde4b398137a66b59a54212426599d13aba957f56eeef`。本轮实际重新运行 GLES 和实例 WebGPU，分别完成 122,622 帧／45 项断言，一至六面自然结束于第 122,562 帧，再运行 60 帧稳定结束菜单。实际墙钟为 GLES 1393.382 秒、WebGPU 2609.929 秒，不据此声称浏览器稳定帧率。

两份成功终态产生后，独立检查器重新核对修复证明、冻结源码、141 个核心对象、各平台对象、构建及运行器。每后端八幅完整 1,228,800 字节 BGRA、所有对应活动 VM、所选日志、25 项动作、45 项断言、存档／Replay 和 89,969,664 帧离线混音 PCM 均与封存 GLES 参考一致。PCM 哈希为 `39e9d4e4c65b7dea3b259e7a83189c06b7aaf28d76ef71bf9942a5c005453b54`；这是离线 sink 的混音输出，不能解读为全零采样。物理音频设备打开数为零。

本次结果绑定当前核心，没有自动继承 ebba 或其他旧核心的完整运行。此前 GLES 单后端证明仍保留其单独范围。整段 Application 与封存模型参考的相同不证明整局原版像素或原版操作系统混音；声明的时钟／熵／资源交付条件仍保留。原版普通 GUI、其他完整模式、独立加载调度及浏览器 UI／帧率／存储／导出继续开放，模式清单仍为 30／27，整作未完成。

[实际双后端证明](th14-interpolator-application-full-nov02.json)仅公开源码及哈希元数据，不含原版资源、Replay、原始内存、图像、PCM 或 Wasm。

```powershell
python tools/th14-interpolator-application-full-evidence-nov02.py --gles-home artifacts/th14/rgb-acceleration-stack-nov02/full-gles --webgpu-home artifacts/th14/rgb-acceleration-stack-nov02/full-webgpu --output docs/porting/th14-interpolator-application-full-nov02.json --check
```
