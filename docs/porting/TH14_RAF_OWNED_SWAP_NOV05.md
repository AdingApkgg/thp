# TH14 自有 RAF 与 SDL 交换间隔时钟

2026-11-05，修复此前实际 GLES 浏览器启动持续出现的 `emscripten_set_main_loop_timing` 错误。原有四条错误记录继续保留，新候选两次实际启动及正常退出没有 warning/error。此结论只覆盖以下有限流程，不代表完整浏览器或整作 1:1 完成。

Renderer 在创建 GL 上下文后调用 `SDL_GL_SetSwapInterval(1)`。本机 SDL 3.4.2 的 `Emscripten_ShouldSetSwapInterval` 会把初始化请求延迟到首次 `PumpEvents`，再由 `Emscripten_GLES_SetSwapInterval` 调用 `emscripten_set_main_loop_timing(EM_TIMING_RAF, interval)`。但 TH14 GLES 已使用 Asyncify 安全的自有 RAF 调度器，不创建 Emscripten main loop，因此这项延迟设置会报告主循环不存在。SDL 初始待处理间隔为 -1，没有请求时无需设置。

正式修复只在 Emscripten TH14 路径跳过这项不适用的交换间隔请求。其他标题和原生编译分支仍保留原调用；WebGPU 初始化原有提前返回路径不变。自有 RAF、异步队列、SDL 换帧挂起和混音逻辑均不改变。没有截获或过滤控制台错误文本。

`tools/th14-build-raf-owned-swap-nov05.py` 从已验收的 `4a8e02cc…` 冻结输入重编译一个 Renderer 对象，逐项核验并复用另外 145 个对象，其中全部 141 个玩法对象未变。编译、链接选项及导出列表不变。新 Wasm SHA-256 为 `7396f28c66e97e961b94352fca493ee54ad1b67ae757b1715b811826db410325`。TH11、TH12、TH13、TH16 GLES 与 TH14 WebGPU 五个共享分支编译检查通过。

新候选在独立本机端口 8210 静音验收，8208 原有数据和旧失败保留。135 条路由哈希、三个 Launcher 契约、28 项实际 HTTP 检查通过；另外直接回读 Wasm、shell 和异步调度模块三份文件并核对新版本哈希。字体音乐复用已有生成资源硬链接，没有再复制 414,850,582 字节资源。

实际浏览器首轮通过标题、普通 Normal／灵梦 A 开局、射击、暂停、恢复和向左移动、再次暂停、普通确认返回标题及 Quit。两张暂停截图可见自机位置变化、分数由 3,920 推进至 3,970，没有读取隐藏引擎帧计数。随后整页刷新、重新选择 TH14、创建新 Runtime，再次到达标题并正常 Quit。最终控制台 warning/error 为空。截图、DOM、SDK 源码和构建文件的本地路径及哈希由 `tools/th14-raf-owned-swap-evidence-nov05.py` 核验，[公开证据索引](th14-raf-owned-swap-nov05.json)不上传原始文件。

本次没有把旧 Wasm 下的全部录像持久化证据自动转为新版本验收，也没有关闭此前偶发的录像管理窗口失败。独立原版时序、全模式、全部存档／录像分支、离线、整局原版像素和 PCM 仍需继续，整作 1:1 未完成。
