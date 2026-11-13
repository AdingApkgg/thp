# TH14 激光回退保护生产交付 · 2026-11-14

Arch 测试站 [wth.saop.cc](https://wth.saop.cc/?game=th14) 已启用核心 85a60542、前端 c7468a29，Runtime generation 为 `fd54b8473646f6cbd1b10017594fb003dc69c7013f13c5383c5bc8b56c77b341`。Wasm SHA256 为 `afed096d2403cb387c4d2094198198e5e0c5ec6f6714a7ec0fdb3958dc89ae40`。

39 个公网运行文件的完整字节数和 SHA256 与清单一致，COOP／COEP 及 no-transform 响应头通过。部署采用目录原子交换；服务未请求重启，进程 443019 保持，旧 generation 47743edb、18 首 Vorbis 与回滚目录保留。构建使用 COW 复制，未再次解包游戏数据。

相同完整运行版本已在独立静音浏览器预览中完成魔理沙 A Normal 开局、射击／激光显示、暂停和返回标题；OGG 流式模式音乐、音效均为 0，观察约 60 FPS。[浏览器证据](TH14_BEAM_BROWSER_PREVIEW_NOV14.md)。公开站点页签已打开，但浏览器工具两次超时，未完成公网画面操作验收，不以 HTTP 文件校验代替该检查。

网站 fork 的可选补丁同步于 [6c65ed26](https://github.com/AdingApkgg/eagler-touhou/commit/6c65ed26931296cc3de852156e3787ff493677da)。普通模式启用同样的保护，显式 thprac 激光记录／播放／恢复保留原语义。4,032 个有效输入、48 个边缘、30 个异常值和 21 个记录／回放检查通过；整份补丁用声明基线的 Linux Git 原始文件实际检查并应用。可选完整运行包仍未重编，不以普通版浏览器结果代替其验收。

[机器摘要](th14-beam-release-nov14.json)。此前魔理沙 A／B Normal 完整流程及存档读回证据仍按[长度保护候选](TH14_BEAM_LENGTH_GUARD_NOV14.md)的范围使用。魔理沙 A Hard 和魔理沙 B Lunatic 等剩余玩法、完整图形／音频与普通流程缺口继续追踪；本次不标记整作完成。
