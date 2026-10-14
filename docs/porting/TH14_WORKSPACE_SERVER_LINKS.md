# 同源可见诊断导航

新 wrapper 保留冻结 gateway 和 quiet 脚本，只在主页面右上角增加“本机诊断：延迟拷贝像素比对”链接。ROOT 从已允许的 `http://127.0.0.1:8208/` 页面点击即可在同一标签页打开 `/checks/deferred-copy-success/`。

```powershell
node tools/th14-serve-workspace-links.mjs --report th14-launcher-preview-prepared-staged-loader-oct14.json --check
```

ROOT 替换自己的旧 8208 服务时使用新 wrapper，并把报告名替换为最终冻结预览报告：

```powershell
node tools/th14-serve-workspace-links.mjs --report th14-launcher-preview-prepared-staged-loader-oct14.json
```

当前仅完成无服务器、无网络的短检查；真实网页点击导航由 ROOT 验证。原工具、quiet JS、已发布/冻结收据、C++、WASM、原版像素与 POST 目的均未修改。
