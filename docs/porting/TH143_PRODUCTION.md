# TH143 生产入口

[启动弾幕アマノジャク](https://wth.saop.cc/?game=th143)

V154 已接入标准 Launcher 首页、资源安装、不可变运行器、统一存档和输入、音频与生命周期接口。原生核心保持已验收的 SHA-256：`d4d5407fb0b7b06cf0052efbe845f9abf303838d39e71a21bc5cc57ae3ee7cbd`。

源码与构建入口见 [TH143 运行器说明](https://github.com/AdingApkgg/thp/tree/main/host/th143)。游戏资源与编译产物通过生产资源包发布，个人存档独立保存在浏览器。

2026-11-20 的生产浏览器完成完整资源包安装与校验、标题画面、音频和约60 FPS呈现检查。标准候选还验证了更新重启、保存退出和成绩导出入口。生产整站4458文件通过校验，181个程序/元数据文件通过公网字节身份检查；TH14的普通/多人程序、数据、存档名称和共享字体保持原有身份。整作行为验收仍以 `TH143_GOAL.md` 的范围和证据为准。

本次发布回执：`archive/th143-production-20261120/receipt.json`。工作区原始证据：`artifacts/th143/production-v154-nov20/`。
