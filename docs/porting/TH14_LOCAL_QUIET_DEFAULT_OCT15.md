# TH14 本机默认静音（2026-10-15）

此前固定 workspace 服务会注入静音脚本，三个普通服务则直接发送原 HTML。Launcher 在按键或点击时恢复父页面共享的 AudioContext，因此普通入口仍可能播放声音。新增的 v2 入口在每个 HTML 响应的首个应用脚本之前注入同一个已验证静音适配，覆盖外层与游戏 iframe；实时扬声器输出为零，离线混音继续生成采样。生产混音器、系统音量和存档不修改。

后续本机普通预览使用以下入口；默认同一 `http://localhost:8208/`、静音，显式添加 `--sound` 才有声。已有 8208 服务仍运行时，无需另外启动服务。

```powershell
node tools/th14-serve-launcher-v2.mjs
node tools/th14-serve-v2.mjs
node tools/th14-serve-package-v2.mjs --package-root runtimes/th14/th14_web/artifacts/local-package/49e81af8b1d62833-c459f56f7a8e
```

默认 Launcher 使用 `th14-launcher-preview-prepared-screen-camera-oct15.json`。直接运行与本地包仍使用各自原构建，不能将历史包当成最新核心。包入口只读取原清单和资源，先校验原字节，再叠加响应；原包的 `serve.mjs`、清单和站点文件保持原样。Launcher 的本机 worker 仍为无 fetch 拦截的 passthrough，`--sound` 也不恢复发布 worker，不删除 cache、IndexedDB 或存档。历史脚本留作原测试记录。

四个新文件通过语法及独立只读复核；实际 handler 检查覆盖 Launcher 六个 HTML 响应、直接运行一个、本地包两个，确认静音在首脚本前、HEAD 长度正确、显式有声返回原 HTML，并验证损坏哈希被拒绝。未为这些 v2 服务新开监听、浏览器或音频设备；当前固定 8208 已实际显示内外静音标记。[检查收据](th14-local-quiet-default-observed-oct15.json)。这证明本机响应策略，不证明原版音频等价。

权限提示来自沙箱的目录或网络边界。工作区内的修改与离线检查使用普通权限；已有服务和授权优先复用。此修正没有调整安全设置或审批模式，也不承诺所有后续操作都能省略平台审批。
