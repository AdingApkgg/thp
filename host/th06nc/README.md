# TH06nc 生产静态传输适配

`static-content-policy.mjs`来自既有Eagler Touhou静态内容策略，按其launcher的GPL-3.0-or-later许可保留源码及LICENSE。本次只为TH06nc路径增加DDS／脚本压缩和no-transform，其他既有路径108项对照保持一致。

`th14-multiplayer-capability.patch`用于既有正式校验器的独立副本，登记站点已经发布的TH14多人Runtime。完整原始语义／文件校验继续执行，四项无效元数据控制均被拒绝。此补丁不修改旧站游戏文件或运行包。

当前服务的兼容校验副本和交接脚本位于Arch生产目录`th06nc-nov20`内，服务drop-in依赖该目录；维护时需保留。原始服务unit文件及旧发布包均已留存。范围与交付结果见`docs/porting/TH06NC_BROWSER_RELEASE_NOV20.md`。
