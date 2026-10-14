# TH14 当前本机入口

当前本机预览使用 `tools/th14-serve-workspace-diagnostics.mjs`。它复用冻结的 current 服务与静音脚本，监听 `127.0.0.1:8208`，按固定清单挂载当前诊断。

```powershell
node tools/th14-serve-workspace-diagnostics.mjs --report th14-launcher-preview-prepared-staged-capture-state-oct14.json --descriptor artifacts/th14/stage-angle-shader-diagnostic-oct14/workspace-descriptor.json --descriptor-sha256 26b31b5d2b7159bce273524e1c1e0dfe9ff2779d6444a787b55430fb5b6ce94d --check
```

去掉 `--check` 才启动服务。入口不会停止已有服务。浏览器固定打开 `http://localhost:8208/`，不要混用 `127.0.0.1` 或其他端口，以保留同一来源的授权和存档。

`/app-shell-sw.js` 的 GET/HEAD 先核验发布文件原 SHA，再返回本机专用 worker：install 调用 `skipWaiting()`，activate 调用 `clients.claim()`，无 fetch 拦截。它不删除 cache、IndexedDB 或存档；发布 SW 文件未编辑，适配源不写入发布目录。当前诊断只允许清单中的 54 个 GET 与 2 个 JSON POST，旧诊断写入入口关闭。结果只能独占创建，或以相同哈希重试；[清单接口说明](TH14_WORKSPACE_DIAGNOSTICS_GATEWAY.md)列出路径及范围。

早期只读收据为 `th14-local-workspace-current-server-verified-oct14.json`，仅证明当时的模拟响应与事件接线。后续实际浏览器已显示新诊断入口和静音标记，并在完整刷新后读取新保存的录像 A；范围见 [修复后观察](th14-staged-capture-browser-post-statefix-observed-oct14.json)。音乐和音效默认静音；该适配只用于本机测试，不作为音频等价证明。
