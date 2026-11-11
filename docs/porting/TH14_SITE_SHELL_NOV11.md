# TH14 网站运行壳

2026-11-11 的网站接入使用 `b5580f47e7a6c7ddda0c1980e6600e2d4e0f6ecf` 的游戏 Wasm，SHA-256 为 `32e62384f7c9b3443905068c9e6a7121b1b499309bc107c745d5749cf70f96f7`。

`shell.mjs` 的错误读取器先从 Wasm 堆复制字节，再传给 `TextDecoder`。浏览器不接受共享内存视图作为该接口的输入；复制避免错误报告及退出保存失败时再次抛出 `ArrayBufferView must not be shared`，保留 C++ 返回的原始错误字符串。

`node tools/th14-core-error-shared-test-nov11.mjs` 对实际运行壳中的读取函数验证普通内存、共享内存、空错误和日文错误，共四例。测试不打开音频设备，不运行游戏或回放。

网站的录制音乐和原作数据独立于 Runtime generation。TS Arch 上的静态发布包已通过文件清单、哈希、依赖闭包及启动器协议校验；浏览器经 SSH 转发连接 Arch，完成 Normal 第一关的手动开始、移动、射击、暂停和返回标题检查。公网入口为 https://wth.saop.cc/ ，由 Cloudflare Tunnel 连接同一 Arch 服务。上述接入检查不代表原版 1:1 已完成。

正常退出的终止帧以 `ok=0, phase=finished(4)` 返回网页壳。TH14 对该组合调用既有 `stop()`，按异步帧队列完成停止、原生分数保存、IDB 同步及 SDL 音频断开，最后通知启动器 `exit`；其余失败帧仍报告原始错误。此分支不改变其他作品的失败处理。

`node tools/th14-shell-exit-test-nov11.mjs` 执行实际运行壳的帧回调、停止及存档函数，并使用实际 `Th14AsyncRuntime` 队列。十二例覆盖终止帧、重复终止通知、各非终止 phase 的错误、旧作错误分支、原生存档失败、IDB 失败、音频断开失败，以及宿主共享音频上下文的归还。该组件检查不启动游戏或音频设备，不代替实际菜单退出与存档往返验收。
