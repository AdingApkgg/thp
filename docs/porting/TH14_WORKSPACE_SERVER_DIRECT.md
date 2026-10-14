# 单服务直接诊断

ROOT 最终只启动 `127.0.0.1:8208`，不再依赖 8254 服务：

```powershell
node tools/th14-serve-workspace-direct.mjs --report th14-launcher-preview-prepared-staged-loader-oct14.json
```

将报告名替换为最终冻结预览报告。主页面右上角的可见诊断链接、静音脚本、Launcher 文件校验与路径 allowlist 均复用旧版。诊断 GET 直接读取已绑定文件；只允许原 8 个 `portable-000.pixels` 至 `portable-007.pixels` 及 `report.json` POST 到固定 `artifacts/th14/deferred-capture-success-dirty-oct14/webgl-capture`。像素长度必须与原版 cases 相同，报告 `frames=8`；首次独占创建，已存在文件只接受相同 SHA256。

只读短检查使用 `--check`，不会启动服务、发送网络或写入实际 POST 文件。旧 gateway、links、quiet 源码与收据保留不变。
