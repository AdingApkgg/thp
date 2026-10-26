# TH14 实际 Application 六面回放 · 2026-10-26

真实生产 C++ Application 现在以普通归一化菜单输入，从冷标题进入一份完整咲夜 B Hard 录像，运行一至六面，最后停在存活的回放结束菜单。WebGPU 和 GLES 两个原生组件后端均完成。本次补齐长流程集成范围；整作 1:1、原版普通界面与浏览器验收仍未完成。

[输入场景](../../runtimes/th12/th12_web/tests/fixtures/th14-native-application-full-replay.json)使用同一完整原始录像，SHA-256 为 `866bf6bac02e1c2b9067dacce6705dc71a512eeb2755106474be492a2d23dcdc`。它经原版 codec 验证为咲夜 B Hard，含六个关卡头。此前原版有限记录共 122,811 回调、结束于六面且残机 1；当前 Application 的菜单帧与回调口径不同，本次没有声称两条记录的每帧状态、图像或 PCM 全部相同。

## 完成的实际流程

实际 Application、图形、字体、音频设备与 141 个冻结核心对象分别通过原生 WebGPU 和 GLES 执行。声明的平台时钟、文件服务及异步队列相同；使用真实 GPU 和静音 PCM sink，未创建系统窗口或物理音频设备。

25 个输入动作从冷标题选择 Replay、录像与一面。六面等待只读取实际状态；每次入口标记后再运行 240 帧，检查战斗时钟确实重置并前进、模式不变及音乐切换。没有强制切关、改残机、改 RNG 或延长存活。两个后端均自然进入结束菜单，残机 1，再保持 60 帧稳定。

| 项目 | 每个后端的结果 |
| --- | ---: |
| 实际运行帧数 | 123,412 |
| 场景断言 | 44 |
| 完整相同的状态日志 | 55,071 行 |
| 相同的动作终态 | 25 项 |
| 实际进入并激活的关卡 | 一至六面 |
| 自然回放结束 | 第 123,352 帧，残机 1 |
| 结束菜单稳定性 | 60 帧 |
| 成对 BGRA 图像 | 8 幅，9,830,400 字节，零差异 |
| 实际静音 PCM sink | 90,553,344 帧，累计哈希相同 |

| 关卡 | 入口帧 | 激活确认帧 | 确认时战斗帧 | 曲目索引 |
| --- | ---: | ---: | ---: | ---: |
| 1 | 通过菜单选择 | 722 | 166 | 1 |
| 2 | 12,302 | 12,542 | 90 | 3 |
| 3 | 30,453 | 30,693 | 90 | 5 |
| 4 | 48,709 | 48,949 | 90 | 7 |
| 5 | 70,904 | 71,144 | 90 | 9 |
| 6 | 94,009 | 94,249 | 90 | 11 |

八幅画面包括一面激活、二至六面入口边界、自然结束及稳定结束。入口截图可能仍显示前一场景的过渡内容；后续 240 帧的实际状态检查确认关卡激活，不能把入口截图写成六个已加载场景的完整视觉验收。

PCM 累计 SHA-256 为 `0aa75b6806bae366b72d4667ab5ae79a446522b13c63c2c87ad32a241362f5fe`。原始 PCM 未独立保留，也没有与原版完整 Application 音频逐字比较。初始和最终存档均只有同一份录像，文件内容保持不变；没有待执行异步回调。

## 版本与复核

实际运行的工具在启动时冻结，SHA-256 为 `bed3b9c452b2fc5fb8fec0988d94ea84bcd8eab6c52817ebc73471b5bcf08edf`。新增显式预算参数后默认 12,000 帧／900 秒不变；本例事先声明最多 240,000 帧／7,200 秒、至少 100 GiB 余量及 2 GiB 输出上限，不自动接续其他用例。场景声明的最大帧数为 211,982，实际结束早于上限。

- WebGPU Wasm：`1aad63f3cc94bf5b2b598da62be0ad3742525e33f3f4af524316b03369e5ece3`。
- GLES Wasm：`860d6adde435fce5f205c5940911c44c9c9e05da4ad4f2b08a22e5358ba32b8f`。
- [WebGPU 完整流程复核](th14-full-application-webgpu-verified-oct26.json)、[GLES 完整流程复核](th14-full-application-gles-verified-oct26.json)分别检查冻结来源、动作、实际关卡重置、结束、输入文件、日志及捕获哈希。
- [跨后端逐字比较](th14-full-application-pair-verified-oct26.json)检查两个终态成功报告、全部日志、动作、留存图像和 PCM sink 元数据。比较器本身不代替各自的完整流程复核。

```powershell
python tools/th14-application-full-replay-evidence-oct26.py --home artifacts/th14/application-full-replay-oct26 --backend webgpu --build artifacts/th14/webgpu-js-host-oct26/application-native-webgpu-final-build --output docs/porting/th14-full-application-webgpu-verified-oct26.json --check
python tools/th14-application-full-replay-evidence-oct26.py --home artifacts/th14/application-full-replay-oct26 --backend gles --build artifacts/th14/webgpu-js-host-oct26/application-native-gles-final-build --output docs/porting/th14-full-application-gles-verified-oct26.json --check
python tools/th14-application-render-pair-check.py --home artifacts/th14/application-full-replay-oct26 --output docs/porting/th14-full-application-pair-verified-oct26.json --check
```

此前[自然续关证据](TH14_LAUNCHER_CONTINUE_OCT26.md)现在显式绑定当时实际冻结的运行工具，不要求后来的未执行版本具有相同哈希；原有全部玩法、状态和图像门槛不变。较新的工具版本不会继承旧运行的通过结论。

本次没有执行浏览器、DOM、系统输入或原版普通菜单。原版普通窗口启动尝试超时，复查没有目标窗口，未发送输入；未将启动失败列为流程通过。发布默认 WebGL 的旧单像素失败、30／25 模式覆盖、相机交错与 effect149 地址／ABI 仍见[剩余清单](TH14_REMAINING_ACCEPTANCE.md)。源码发布不包含录像、原版资源、原始日志、图像、PCM、DLL、EXE 或 Wasm。
