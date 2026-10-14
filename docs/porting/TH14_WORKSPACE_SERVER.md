# TH14 固定工作区预览

新服务保持 `http://127.0.0.1:8208/`，读取指定冻结 Launcher 报告，启动前校验全部 127 文件，每次文件请求再次核对 SHA256。仅服务报告列出的文件与该站点的 `files.json`。

先只读检查，不启动服务、不发送网络请求或写入诊断 POST：

```powershell
node tools/th14-serve-workspace.mjs --report th14-launcher-preview-prepared-staged-loader-oct14.json --check
```

ROOT 停止自己的旧 8208 服务后，仅替换一次：

```powershell
node tools/th14-serve-workspace.mjs --report th14-launcher-preview-prepared-staged-loader-oct14.json
```

普通 Launcher 为 `/`；当前诊断为 `/checks/deferred-copy-success/`，固定转发到现有 `127.0.0.1:8254` 服务。诊断 HTML 增加请求路径前缀；CPP、WASM 与原版像素内容保持原字节。剥除前缀后的 POST 仍为原 `/capture/portable-000.pixels` 至 `portable-007.pixels` 和 `/capture/report.json`，由已有 8254 服务按原不可变规则写入。

服务仅在送出的 HTML 注入 `/__workspace/quiet-audio.js`（包括父页面与 runtime iframe），显示“本机测试静音”。脚本在实际 `AudioContext.destination` 前使用原生 `GainNode`，`gain=0`，混音器与 AudioContext 保持运行；非最终输出连接、AudioParam、索引参数、返回值和 disconnect 保留，OfflineAudioContext 渲染保留。参照 [MDN connect](https://developer.mozilla.org/en-US/docs/Web/API/AudioNode/connect)、[disconnect](https://developer.mozilla.org/en-US/docs/Web/API/AudioNode/disconnect) 和 [GainNode](https://developer.mozilla.org/en-US/docs/Web/API/GainNode)。这仅为本机测试适配，不是 Native 音频等价证明；发布包、C++、Launcher 音乐偏好与存档不修改。

允许路径与本地来源集中声明在工具顶部 `CHECKS`；后续 fixture 需 ROOT 显式新增并审查映射。CLI 不接受其他端口、上游地址或文件系统目录。未知诊断路径、query 代理选择器、目录穿越与编码斜杠拒绝；不会将用户 URL 拼成任意上游地址。所有正常响应保留 COOP/COEP/CORP 与 `no-store`。

`--check` 的请求/响应为声明的内存依赖。真实 8254 HTTP、浏览器像素和用户操作另行验证，不能由此标为通过。
