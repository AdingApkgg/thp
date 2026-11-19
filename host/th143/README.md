# TH143 自托管发布包

入口：https://wth.saop.cc/th143/ 。源码与独立构建说明见 ../../runtimes/th143/README.md。

runtime-manifest.json 记录验收生产包882个文件的大小与SHA256。资源独立自托管；Git不包含原版资源、Wasm二进制、私有存档或开发测试页面。部署时先在新目录核对全部文件，将完整th143目录原子移动到站点；已有目录应保留备份。现有其他游戏和服务配置保持。正式部署结果在docs/porting/th143-production-release-nov20.json记录。
