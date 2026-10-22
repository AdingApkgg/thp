# TH14 当前本机入口 · 2026-10-23

当前固定静音入口为 `http://localhost:8208/?game=th14`，使用标题／结局调度修正后的模块 `0e1ba6d1531edb51cfcf3f45aa0e01c4221788716369154470c95834d114a4bd`（1,902,898 字节）。启动命令：

```powershell
node tools/th14-serve-workspace-diagnostics.mjs --report th14-launcher-site-title-ending-scheduler-oct21.json --descriptor artifacts/th14/save-conflict-observe-oct16/descriptor.json --descriptor-sha256 3fbb87653355b16e2586a2ca833386f688da72378e069a5840f351e48c4cd085
```

不重复启动已占用端口。当前进程、HTTP 完整模块和适配检查记录位于本机 `artifacts/th14/title-ending-preview-oct23/`。当前站点只读检查通过；通用诊断 `--check` 因既有 save-conflict 描述符没有独立诊断 WASM 条目而失败，记录保留，不能把它称作通过。HTTP 实测验证的是游戏模块及静音／本机透传 worker。无缓存或存档清除。旧五份录像仍在，普通管理导出新增录像的完整 114,005 字节 SHA 与原导入相同。

当前模块已实际完成普通开局、暂停、返回标题、五面回放自然结束菜单与返回录像列表，警告／错误为空；[独立浏览器记录](th14-title-ending-browser-observed-oct23.json)不宣称浏览器完整结局或原版像素／音频等价。源码、自然通关和新版完整回放范围见[标题／结局修正](TH14_TITLE_ENDING_SCHEDULER_FIX_OCT21.md)、[新版回归](th14-title-ending-full-matrix-oct23.json)。整作 1:1 未完成。

## 历史入口 · 2026-10-21

当前静音预览固定使用 `http://localhost:8208/?game=th14`，启动命令更新为：

```powershell
node tools/th14-serve-workspace-diagnostics.mjs --report th14-launcher-site-replay-resume-final-oct21.json --descriptor artifacts/th14/save-conflict-observe-oct16/descriptor.json --descriptor-sha256 3fbb87653355b16e2586a2ca833386f688da72378e069a5840f351e48c4cd085
```

命令不负责停止已有服务；不要重复启动同端口服务或改用其他来源。当前进程身份收据为 `artifacts/th14/replay-resume-final-preview-oct21/server-start.json`，切换前已核对原进程可执行文件、完整参数和创建时间。HTTP 完整模块已核对 SHA-256 `02669f7731b7e774e59974b798e7b129fe3470187e10bc0e6e11e72eb2900b6e`，运行时 40 文件、站点 127 文件。146 对象来自冻结全新构建及经过哈希核验的增量构建；最后的标题隔离改动单独编译，证明最终对象与已测模块逐字节相同，没有借旧源哈希冒充当前源码。

实际预览保持“本机测试静音”和 `0ms SP`；四份旧录像保留，已通过普通管理窗口增加本轮测试录像，列表共五份，没有清存档或缓存。当前模块已通过普通菜单实际观察自然 GameOver、续关、普通暂停、恢复、返回标题，以及魔理沙 B Lunatic 从五面自然进入强制结束菜单、Escape 不能取消、确认返回录像列表，警告／错误为空；[浏览器收据](th14-pause-replay-browser-observed-oct21.json)限定实际范围，不继承旧模块结果。新导入文件再次完整刷新后的持久化和最终浏览器重新播放尚未在该收据中验收。源码与范围见[暂停／结束菜单修正](TH14_REPLAY_END_SOUND_FIX_OCT21.md)、[当前站点清单](th14-launcher-site-replay-resume-final-oct21.json)。整作 1:1 仍未达成。

## 历史入口和诊断范围 · 2026-10-15

以下命令、模块与“当前”描述均指当时冻结记录，不是今天的默认包，不能继承为今天的检查结果。

当前本机预览使用 `tools/th14-serve-workspace-diagnostics.mjs`。它复用冻结的 current 服务与静音脚本，监听 `127.0.0.1:8208`，按固定清单挂载当前诊断。

```powershell
node tools/th14-serve-workspace-diagnostics.mjs --report th14-launcher-preview-prepared-screen-camera-oct15.json --descriptor artifacts/th14/triangle-weights-raw-oct15/workspace-descriptor.json --descriptor-sha256 7a3b1f431080dac76372cea8ca8621ce44fddbc63fc3cd129027615071ae3836
```

上述命令启动服务，入口不会停止已有服务。浏览器固定打开 `http://localhost:8208/`，不要混用 `127.0.0.1` 或其他端口，以保留同一来源的授权和存档。此独立 JS 诊断没有 WASM，旧通用 `--check` 内置的 WASM 必须存在检查会失败；此前坐标传递清单的这项失败和独立只读 9 GET／5 POST 检查均保留原范围，不继承为当前清单验收。当前新清单已通过实际浏览器读取和捕获。

`/app-shell-sw.js` 的 GET/HEAD 先核验发布文件原 SHA，再返回本机专用 worker：install 调用 `skipWaiting()`，activate 调用 `clients.claim()`，无 fetch 拦截。它不删除 cache、IndexedDB 或存档；发布 SW 文件未编辑，适配源不写入发布目录。当前透视属性基诊断只允许清单中的 8 个 GET 与 5 个 POST，其中报告限 2 MiB，两臂各有固定 5,616 字节顶点缓冲和 4,915,200 字节像素缓冲；旧诊断写入入口关闭。网关原全局大小限制未修改，结果只能独占创建，或以相同哈希重试；[清单接口说明](TH14_WORKSPACE_DIAGNOSTICS_GATEWAY.md)列出路径及范围。

早期只读收据为 `th14-local-workspace-current-server-verified-oct14.json`，仅证明当时的模拟响应与事件接线。后续实际浏览器已显示新诊断入口和静音标记，并在完整刷新后读取新保存的录像 A；范围见 [修复后观察](th14-staged-capture-browser-post-statefix-observed-oct14.json)。音乐和音效默认静音；该适配只用于本机测试，不作为音频等价证明。

此前摘要页的 UV 模式已实际运行，范围见[历史摘要页观察](th14-stage-transform-feedback-summary-browser-observed-oct14.json)。当前 `/checks/render-gap-pass-through/` 已实际完成两次绘制：A 完整复现旧浏览器顶点和像素；B 使用测得的 Native authored VS2 坐标与当前 GPU 坐标桥接，输出的全部顶点与像素仍与 A 相同，327 个 UV 字差保留，覆盖差为零。页面只显示短摘要，完整数据保存在私有产物目录。此坐标并非原固定管线 clip 的直接捕获，整作 1:1 未完成。

当前默认运行包为屏幕相机参数修正后的 `3083772c…`。新增标签页已实际显示标题和 Normal Demo，内外静音标记可见；旧游戏页保持原状态。该浏览器观察不继承旧版完整录像或图像通过结果，详见[相机修正](TH14_SCREEN_CAMERA_FIX_OCT15.md)。服务需要本机回环套接字权限；编译和矩阵比较均在普通工作区权限中完成。

当前 `/checks/triangle-weights-raw/` 已实际完成控制与属性基两次绘制，保存两个完整 4,915,200 字节像素缓冲及两个顶点缓冲，捕获警告／错误为空，静音标记可见。独立对照仍有 328 个权重字差，覆盖差为零；原值不作归一化、四舍五入或夹取。[实际权重范围](th14-triangle-weights-receipt-oct15.json)。原生侧同为两个独立隐藏绘制，不启动原版游戏、Present 或音频；正常清理成功，超时清理未实际触发。
