# TH14 测试站交付 · 2026-11-13

[测试站](https://wth.saop.cc/)当前游戏源码为 [`84b8741a`](https://github.com/AdingApkgg/thp/commit/84b8741af5b7ca617cc4046fe697d3cbfebbf4ad)，网站源码为 [`2eeb8db4`](https://github.com/AdingApkgg/eagler-touhou/commit/2eeb8db4b6f2ef337656d4d979c60abfaca579be)。Runtime generation 为 `f91cdcec13bf2a6579f7da7288cb08665f6d74eac2cd8f205dcea0907c70b815`，Wasm SHA256 为 `f4026156b7449c8186fb0c6b4c77a46024451eb79b9078fac39faa3c77e3dd5a`。整作继续处于施工和测试状态。

本次部署包含 TH14 无纹理绘制解绑修复，以及 Goan114 的缓存页面／worker 隔离头修复。缓存导入的 HTML 和 JavaScript 响应补回 COEP、COOP、CORP，原版 ANM、界面、纹理、短输入和浏览器调度修复也已在前一核心整合中接回。协作者 `19170e47` 的延迟颜色清屏／alpha 优化仍是独立候选，未作为当前生产核心合入。

标准自托管封面准备器登记了现有 `th14-card.jpg`，可使用仓库卡图或同名 JPEG 覆盖文件。三项合成／实际 CLI 回归通过，实际卡图输出 3,225 字节与已有源文件相同。新增 JPEG 校验会拒绝损坏图像和冒用扩展名的 PNG；没有新增原作资产到 Git。

当前默认字体 `.bin` 已进入既有 HTTP 压缩管线，路径限定在 TH14 不可变 generation 的已知字体文件。真实 HTTP 测试核验 gzip 解压结果和未压缩正文相同，其他二进制路径保持原规则。原点 30,524,029 字节的 font4 经 gzip 传输为 2,947,524 字节，解压 SHA256 与 Runtime 清单相同，`no-transform` 保留。

原点同代 39 个运行文件逐项相等；公网同代 39 个完整响应体也全部相等，包含 HTML、加载器和 Wasm，并核对 COOP、COEP、`no-transform`。Windows 首轮 30 项成功、Arch 补验至 33 项；开启压缩后只补验失败字体至 38 项。最后一个字体命中旧的未压缩 CDN 缓存，仅通过 Alice 的现有 CF CLI 清除这一 URL，随后取得 `MISS`、Brotli 编码及完整正确正文。所有失败记录保留，成功正文按同代复用，无分段下载、完整性放宽或原始大文件留存。

18 首音乐现为真实 Ogg Vorbis，使用质量 5 和固定流序号。从部署清单已核验的无损 FLAC 在 Arch 上转换，原文件不改，输入合计 295,272,965 字节，输出合计 46,560,471 字节。FFprobe 的全部 18 个流采样帧数与原布局一致，循环元数据保留；此项是流长度与格式验证，没有测得 C++ 解码器逐样本数量或最终混音相等。原点所有曲目确认 Ogg 容器，公网首首曲目的完整响应体与新清单相同。公网还完整核验了新站点清单和 37,098 字节的缓存 worker 脚本。

游戏构建的 369 个源码 blob 与公开提交相同，正式浏览器重编一个 Renderer 并核验复用其余 145 个对象。三个其他作品的渲染对象逐字节不变。先前针对该源码的静音 SDK Application 开局在 542 个宿主帧后到达首个 Player，资源回收；该检查使用之前的 FLAC 输入，不能当作本次浏览器 Ogg 播放验收。加载 ASCII16 的 65 次初始化、1,560 条调用边界另与实际原版 VM 执行一致，仍未闭合初始化频率和物理时间线。

站点包验证 1,057 个文件，可信 HTTPS、隔离头、哈希检查和回滚保留。实际浏览器 UI、完整机体／难度和录像、普通完整流程与存档、加载 RNG／弹状态／相机、整帧和最终 PCM 仍待验收。`completeGame=false`。[交付收据](th14-release-nov13.json)。
