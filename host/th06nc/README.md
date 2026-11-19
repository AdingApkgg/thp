# TH06nc 标准 Launcher 接入

当前接入通过首页产品目录、Package Store、共享输入桥和用户文件协议完成，构建步骤见 [LAUNCHER.md](LAUNCHER.md)。站点源码补丁以 `4ad1867ed6e825bb2f91b71ad73536ec106c608c` 为基线；游戏资源不进入 Git。

`site-integration.patch` 包含标准产品声明、TH143 既有声明、离线发布配置恢复和静态传输策略。生产构建使用正式打包器、完整构建校验器和公网部署校验器。

`static-content-policy.mjs`、`th14-multiplayer-capability.patch` 和交接脚本是先前独立页面发布的历史文件。其策略源自 Eagler Touhou，按 GPL-3.0-or-later 保留源码及 LICENSE。后续部署应使用上述标准接入流程，不能以独立页面替代首页注册。
