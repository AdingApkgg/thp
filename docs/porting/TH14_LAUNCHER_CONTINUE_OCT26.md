# TH14 启动入口、续关流程与观察字段修正 · 2026-10-26

本次补齐本地 WebGPU 候选包的父 Launcher 入口，实际运行生产 C++ Application 的自然 GameOver 与续关，并纠正一处激光观察字段。整作 1:1、普通浏览器及原版普通菜单验收仍未完成。

## 候选启动入口

[准备工具](../../tools/th14-prepare-webgpu-launcher.py)把冻结的共享 Launcher 和现有异步 Runtime 组成不可变路由覆盖层。现有数据、字体、音乐与 Wasm 直接从已校验的位置提供，写入的 103,342 字节仅为元数据；510,696,322 字节既有文件未再次复制，也未把原版游戏文件硬链接。

[HTTP 检查](../../tools/th14-webgpu-launcher-transport-check.mjs)核对 133 条路由、21 项真实回环 HTTP 请求、字节哈希、MIME、隔离响应头、默认静音注入、模块依赖，以及共享 Launcher 的 Host／Release Catalog／Package Descriptor 校验器。字体／音乐资源清单的 28 条依赖也已核对。静音服务沿用本地输出为零的策略，不改混音器；本地 Service Worker 返回无缓存删除的透传版本。

候选 Wasm 仍为 `3786901cbe373d221b14f02bcb3b1fa77901512195a09ba080669753a915018c`，来源和原生 JS WebGPU 范围见[前一批证据](TH14_JS_WEBGPU_OCT26.md)。当前普通 WebGL 预览未替换。没有执行浏览器、DOM、系统输入、IndexedDB 或离线验收；本地静音入口准备和 HTTP 通过不改变 `browserAcceptance=false`。

## 实际 Application 自然结束与续关

新增[声明式输入场景](../../runtimes/th12/th12_web/tests/fixtures/th14-native-application-continue.json)：从冷启动以普通归一化菜单键选择咲夜 B Easy，原地等待自然耗尽残机，进入结束菜单，选择续关，再射击 120 帧。场景的有界等待只查询实际状态，不改血量、残机、分数、关卡、RNG 或结束条件。

实际 C++ Application、图形、字体、音频设备及 141 个冻结核心对象，分别在 WebGPU 和默认 GLES 原生组件宿主执行；两边均无系统窗口／物理音频设备，使用相同声明时钟和静音队列。

| 项目 | 每个后端的结果 |
| --- | ---: |
| 实际总帧数 | 3,637 |
| 场景断言 | 58 |
| 自然 GameOver | 第 3,472 帧，残机为 -1 |
| 续关恢复 | 第 3,517 帧，残机 2、火力 400、续关次数 1 |
| 后续运行 | 保留原关卡与生命周期后继续射击 120 帧 |
| 成对画面 | 4 幅，4,915,200 字节全部一致 |
| 状态日志 | 237 行全部一致 |
| 静音宿主实际 PCM sink | 2,515,968 帧，两个运行的累计哈希一致 |

续关期间音乐选择从结果曲 17 恢复到关卡曲 1。此处验证生产入口确实执行续关流程及音频设备调用；没有把相同后端 PCM 哈希写成与原版音频逐字相同。PCM 原始流未另行保留，独立复核器明确记录这一范围。原指令音乐队列的有限组件证据仍见[续关音乐修复](TH14_MUSIC_CONTINUE_OCT26.md)。原版普通 Application 续关对照、物理通知竞争、设备播放和普通浏览器继续开放。

## 激光对象宽度观察修正

新选用 Royalflare 的 KMK 魔理沙 B Normal 原始录像 `th14_ud0593.rpy`，原作解码器确认选择与六个关卡头。一次独立有界原版观察自然结束于二面、19,496 个回调，不能增加六面覆盖。

旧观察夹具在第 2,991 回调、槽 244 退役激光的 `collisionWidth` 上报告 54／48。保留原始对象显示：激光自身 `+b0` 为 54，其伤害区域指针已指向尺寸为 48 的其他活动区域。生产 `ShotState::th14_beam_length` 已保存正确的自身长度；夹具错误地从区域槽读取这个字段。

修正夹具后，141 个核心对象逐哈希复用，玩法代码未改。前后完整状态、相机、HUD、动画及所有其他采样对象字段逐输出一致；212 个战斗检查点中只有这个观察字改变。新观察 Wasm 为 `b46bea539bc6346c7af8e4d1ac20b90d0c342056044549afeecb0fae1d236880`。

| 原版记录 | 回调 | 严格有限复核 |
| --- | ---: | --- |
| KMK 魔理沙 B Normal，实际一至二面 | 19,496 | 所选 32 字、相机 25 字、HUD 2 字、52 行动画及 212 个战斗检查点通过 |
| 魔理沙 B Easy，一至六面 | 107,233 | 同门槛回归通过，2,630 行动画、1,206 个战斗检查点 |

旧的一个字段失败完整保留。新 Normal 记录和原先另一条 Normal 记录均中途耗尽残机，原因待查。[thprac 的实际实现](https://github.com/touhouworldcup/thprac/blob/9d9d0030f85befd8c2bd8cbc151410788c6fa14c/thprac/src/thprac_th14.cpp#L699)提供了激光栈值的记录／恢复机制，可作为排查参考；目前没有证据把这些早退全部归因于该问题。没有注入修复值、延长存活或改写通关条件。

## 复核

[本次汇总](th14-launcher-continue-verified-oct26.json)重新核对本地部署文件、观察字段原始对象、前后输出、严格完整复核收据，以及实际续关日志和成对画面。两个完整记录均另由默认[严格工具](../../tools/th14-verify-native-campaign.py)独立复算，没有跳过字段门槛。

```powershell
python tools/th14-launcher-continue-evidence-oct26.py --home artifacts/th14/replay-coverage-input-oct26 --launcher artifacts/th14/webgpu-js-host-oct26/launcher-candidate --output docs/porting/th14-launcher-continue-verified-oct26.json --check
```

复核器绑定实际运行时冻结的 `run-tool.py`（SHA-256 `23b40b816b35e861d75abad73f4bf93e2e37394c57268fb661195ce6bab2f5a6`），后续工具版本不继承这次运行。所有原有动作、状态、严格对象和图像门槛不变。后续[实际 Application 六面回放](TH14_FULL_APPLICATION_REPLAY_OCT26.md)由不同的冻结运行另行验证。

当前模式覆盖仍为 30 组自然结束／25 组全部目标入口。相机复制交错、effect149 地址／ABI、剩余完整模式、原版普通流程和浏览器验收继续。原版资源、录像、原始对象、画面、PCM、DLL 与 Wasm 不随源码发布。
