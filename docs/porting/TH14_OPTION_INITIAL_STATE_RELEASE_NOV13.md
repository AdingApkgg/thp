# TH14 Player 初值修正上线与流式解码验证 · 2026-11-13

核心源码 [59a8cc4c](https://github.com/AdingApkgg/thp/commit/59a8cc4cc5ae404d8439019b35f4915f75c03c5d) 已部署至 [TH14 测试站](https://wth.saop.cc/)。正式浏览器 Wasm 为 `e367ee01f323d9ced76959574a3a530762ee0fee91b692adb41151eb291359e3`，3,129,571 字节，generation 为 `988ce3cedb28d0cd7519dbfaadb2341bf05ca140e94a87377ed0e3bf62dbdeb8`。这是早期测试版本，整作 1:1 仍未完成。

本次将已验证的 33 个 Player 移动历史点及八个僚机初始 Y 修正交付到线上。浏览器仅重编 PlayerFrame，逐项核验复用其余 145 个对象；369 个构建源码 blob 与公开源码提交一致。此前当前源码的 35,000 回调游戏状态／RNG／弹数／HUD／游标和 123 个弹槽采样通过，[完整范围与采集脚本失败说明](TH14_OPTION_INITIAL_STATE_NOV13.md)保持。三面相机缓存仍有严格差异；[72 个实际线程的复制／构造联合对照](TH14_CAMERA_COPY_CONSTRUCTOR_NOV13.md)相同，但不能据此把缓存固定成 screen 或计作物理调度通过。

Arch 原点的 39 个完整 HTTP 响应逐个与同代清单匹配。Windows 经 Cloudflare 的首轮完整响应中 37 个匹配，font6 与 Wasm 两次接收被连接重置；初次失败报告保留。对这两个相同不可变 URL 各重新完整请求一次后均匹配，最终 39 个文件通过，包括 HTML、loader、Wasm 和字体。没有 Range、清除缓存、放宽哈希或关闭完整性校验；COOP／COEP 和 no-transform 保持。服务重启后的首次本机连接拒绝由已声明重试恢复，原日志保留。

只上传四个运行文件约 3.15 MB，loader 字节未变，未重新编码或传输音乐／游戏归档。18 首既有 Vorbis 保留，并另在 Arch 用当前生产解码函数完成全部 99,457,880 个立体声帧与独立 FFmpeg 对照、54 个寻址窗口和 18 个循环边界；[解码证据及其边界](TH14_VORBIS_STREAM_NOV13.md)不代替浏览器播放或最终混音验收。小型音频探针和格式元数据是额外测试输入，不属于上线运行文件。

网站 fork 的 `9e3f5f17` 只修改 TH14 接入文档和核心指针，Arch 检出已同步；网站运行逻辑仍为 `2eeb8db4`。两个既有 vendor LICENSE 本地改动逐项哈希相同。上一代保留在 `/home/i/Code/th14-release/hosted-before-59a8cc4c`。未借此次发布声称完整机体／难度、普通完整流程和存档、整帧、最终 PCM 或浏览器 UI 已通过。

[发布收据与源／工具／HTTP 绑定](th14-option-initial-state-release-nov13.json)。原作资产、原始相机、格式字节、音频和生成 Wasm 不进入公开 Git。
