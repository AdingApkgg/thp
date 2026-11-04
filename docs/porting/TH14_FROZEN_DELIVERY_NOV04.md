# TH14 冻结构建的可重复打包

2026-11-04，修复 `tools/th14-package-webgpu-candidate.py` 的一个发布流程问题：工具此前要求发布工作副本的 HEAD 等于浏览器构建记录的 `basePublishedCommit`。源码或证据继续发布后，旧浏览器构建即使完整保留且哈希正确，也会被拒绝打包。

现在先校验该字段是一个存在的完整 Git commit，再从该提交读取八个配套平台文件，保留小份来源副本和哈希。打包不再依赖可移动的 HEAD，也不把当前工作区网页文件混入已冻结构建。Wasm、loader、源码与生成资源仍逐项校验。此修复不修改游戏 C++ 或计算结果。

本次实际验证使用的平台基底为 `4ff66fd7b2e302c6878bb535d6d75554f09e8da8`，发布工作副本已推进至 `a2ed896be3ff984c4423a0afe4d4aeb53924d37b`。浏览器构建包含基底之上的冻结源码覆盖，不能只用基底提交代表游戏核心。其全部 146 个编译单元为新编译，核心源码和头文件与当前原生对照构建逐项相同；四个本次生产修改文件另与公开核心 `51fcb47992be0af65777d2ea87e9e409be6cc641` 的 Git blob 校验一致。

交付包的 Wasm SHA-256 为 `4a782422a0d52e4c72f33b67896fc434523e16dcfc8b974f4e11fb2e3e0c1506`。28 个已生成字体／FLAC 文件以硬链接复用，引用 414,850,582 字节，没有新增同量资源副本；原版资产不复制、不链接、不公开。Launcher 复用已有冻结文件，只新增 104,768 字节路由元数据。

本地 HTTP 检查逐项校验 139 条路由和三个纯 Launcher 合约，通过 27 项请求检查，包含 Wasm 的 MIME、隔离头、默认静音脚本、模块依赖、资源清单、HEAD、404、405 和本地 Service Worker 直通策略。该进程没有启动浏览器、创建 DOM、操作窗口或输出物理音频。第一次在沙箱内连接 loopback 被拒绝，使用已授权的本地传输检查权限重跑通过；不将第一次失败当作通过。

可复核索引为 [th14-frozen-delivery-nov04.json](th14-frozen-delivery-nov04.json)。验证器重新读取本地封存构建、包、Git blob、生成资源、路由和传输检查记录：

```powershell
python -X utf8 tools/th14-frozen-delivery-evidence-nov04.py --output docs/porting/th14-frozen-delivery-nov04.json --check
```

该命令复核已留存的 HTTP 结果，不自行重发请求。新传输检查使用 `tools/th14-webgpu-launcher-transport-check.mjs`；其 `--report` 和 `--output` 参数见索引中的本地路径。构建和资源仍只保存在本地，索引不包含它们的原始内容。

这里验证的是来源一致且可传输的交付包。未改变默认预览，也未进行浏览器 UI、GPU 显示、浏览器存档刷新、离线启动或原版整局图像／PCM 验收；`browserAcceptance`、`persistenceAccepted`、`completeGame` 和 `nativeEquivalent` 均为 false。当前 1:1 剩余项继续按 [剩余验收清单](TH14_REMAINING_ACCEPTANCE.md) 推进。
