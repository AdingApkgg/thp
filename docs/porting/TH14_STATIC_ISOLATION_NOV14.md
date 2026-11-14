# TH14 静态预览跨源隔离 · 2026-11-14

上游静态服务器缺少生产使用的隔离开关，设置 `EAGLER_TOUHOU_CROSS_ORIGIN_ISOLATION=1` 后仍未发送隔离响应头，阻碍 TH14 的共享内存线程启动。候选将生产已有的显式开关接回 `launcher/scripts/serve-static.mjs`：启用时统一发送 COOP `same-origin`、COEP `require-corp` 与 CORP `same-origin`；不启用时保持原响应。

实际 HTTP 服务的 12 例检查覆盖开关关闭／开启时的普通 GET、运行文件 HEAD、304、404、302 及 308；原始上游在开启用例中被拒绝。私有预览的 32 个完整运行响应另通过大小、SHA256、隔离头和 `no-transform` 校验，运行 generation 为 `3f01b5a3…`。

所有检查使用回环地址，预览通过现有 SSH 转发访问；生产服务未变。新静态预览组装强制使用写时复制，复用原有游戏数据、18 首 OGG 和字体。测试工具：`tools/th14-check-static-isolation-nov14.mjs`；[机器摘要](th14-static-isolation-nov14.json)。
