# TH14 当前本机入口

仅本机预览使用 `tools/th14-serve-workspace-current.mjs`。它复用冻结的 direct 服务、诊断链接和静音脚本，监听 `127.0.0.1:8208`。

```powershell
node tools/th14-serve-workspace-current.mjs --report th14-launcher-preview-prepared-staged-loader-oct14.json --check
```

去掉 `--check` 才启动服务。入口不会停止已有服务；本轮仅执行只读模拟，没有启动或切换当前进程。

`/app-shell-sw.js` 的 GET/HEAD 先核验发布文件原 SHA，再返回本机专用 worker：install 调用 `skipWaiting()`，activate 调用 `clients.claim()`，无 fetch 拦截。它不删除 cache、IndexedDB 或存档；发布 SW 文件未编辑，适配源不写入发布目录。其他路由及固定 9 个 POST 仍由原 direct handler 处理。

只读收据为 `th14-local-workspace-current-server-verified-oct14.json`。模拟只证明响应与事件接线，未证明真实浏览器已完成 worker 接管。
