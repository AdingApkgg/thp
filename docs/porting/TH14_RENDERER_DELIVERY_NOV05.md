# TH14 当前浏览器构建的后端身份与交付 · 2026-11-05

修复浏览器交付工具始终把构建标成 WebGPU 的问题。用未修改的旧打包器处理当前 GLES 构建，实际复现：Wasm 没有 `th14_webgpu_*` 导出，但 Runtime 的版本和 execution kind 仍为 WebGPU。新工具同时校验构建宏、导出、归档 worker 和回调模式，再把实际后端写入 Runtime 与 Launcher 元数据；后端声明和编译宏不符时直接拒绝。旧工具和基线包保留。

当前近裁剪修正的两个浏览器构建已分别打包，玩法、渲染数学和 Wasm 本身均未改动：

| 本地包 | Wasm SHA-256 | 冻结路由 | 实际 HTTP 检查 |
| --- | --- | --- | --- |
| GLES／WebGL 2 | `0a9750bfe24129ec6005b197fe599b49c2adb62652e175c85e8c0b479f616794` | 134 | 27 |
| WebGPU | `340aad1aeac70cda36f084a3bf567cc2f31924feb10e9e09feafd875d0d0049b` | 139 | 27 |

两者均由各自完整重编的 146 单元构建交付，四个正式渲染文件与构建输入逐项一致。GLES 包不要求五个无关 WebGPU 模块，这五条请求实际返回 404；WebGPU 包继续交付所需模块。每个包的三个纯 Launcher 合约、字面模块依赖、资源清单、Wasm MIME、隔离头、默认静音注入、HEAD、404、405 和本机 Service Worker 直通检查均通过。两个故意互换后端声明的控制在读取 Wasm 或资产之前被拒绝。

每个包的 28 个已生成字体／FLAC 资源，共引用 414,850,582 字节，以硬链接复用同一批不可变文件，未复制两套大型资源。Launcher 的路由元数据载荷分别为 103,650／104,793 字节，不含检查报告自身；索引同时单独计算包含报告的实际目录总字节，未把旧 `physicalBytesWritten` 提示字段当作目录总占用。原版资产没有复制或链接到新包，路由引用已有私有 Launcher 的 DATA。所有游戏资产、生成资源、录像／存档和二进制均留在本地，不在公开证据索引中提供原始内容。

新的 GLES 默认静音入口已启动于 `http://localhost:8208/?game=th14`。另行对运行中的固定入口回读五条实际响应，确认 Wasm 与冻结包一致、Runtime HTML 包含静音注入。公开证据复核的是这次留存响应，**不表示该服务器在未来仍运行**。没有自动打开、导航或操作浏览器；只读窗口枚举未发现可验收的 Chrome 窗口。因此没有把 HTTP 和模块检查当作浏览器画面、输入、GPU、IndexedDB 刷新或离线执行验收。

GLES 使用普通 SDL 回调，没有后台 archive worker 集成，也没有借用 WebGPU 的帧／worker 串行化结果。这里不声称两个后端已具有相同的独立线程调度。

源码工具：

- [按后端打包](../../tools/th14-package-renderer-candidate-nov05.py)
- [生成冻结 Launcher 路由](../../tools/th14-prepare-renderer-launcher-nov05.py)
- [默认静音本机服务器](../../tools/th14-serve-renderer-candidate-nov05.mjs)
- [真实 HTTP 交付检查](../../tools/th14-renderer-launcher-transport-check-nov05.mjs)
- [交付证据复核](../../tools/th14-renderer-delivery-evidence-nov05.py)与[计数／路径／哈希索引](th14-renderer-delivery-nov05.json)

首轮沙箱硬链接和 loopback 访问失败、缺少新后端字段的旧构建报告拒绝均保留；后续使用正常权限及受编译宏／导出约束的旧 WebGPU 报告识别，未把失败改写成成功。原版整局画面／PCM、Normal 历史独立调度差异、完整模式、普通 GUI、当前浏览器实际运行与持久化继续，整作 1:1 未完成。

发布前的 Git 行尾检查拒绝了打包器中的多余回车。实际运行文件已按原始哈希冻结，公开文件仅按 Python 通用换行规则规范化行尾；检查器逐字节核对这项转换，并确认 Python AST 相同。包报告继续绑定实际运行的文件，不把格式修正后的哈希冒充为此前执行版本。数据和二进制未改动。
