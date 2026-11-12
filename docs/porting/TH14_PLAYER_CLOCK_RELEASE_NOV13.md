# TH14 Player 时钟修正：生产发布

源码 [b8e36ef2](https://github.com/AdingApkgg/thp/commit/b8e36ef27d96238352f5edaf9b368ca23394ceb3)已部署至 [TH14 测试站](https://wth.saop.cc/)。修正 Player 激活前的 transition 时钟，以及 TH14 `Timer.tick()` 的空速率指针语义；[原版对照与范围](TH14_PLAYER_INITIALIZATION_NOV13.md)保持整作未完成。

- generation：`d417e12111318aef5b8cc92eb5c9f479fdb9b93e861fe06a826590abb8d66821`
- Wasm：`5a1badbd123a966e78a22efbd8e64e3c0dbf553f50afcd39a2d81e6305a749fe`，3,129,436 字节。
- loader：`6d6513fb060514872894c2b1c80db99ce1c130a1bd42b35cd98408499dbf3a7a`。

369 个浏览器构建输入的 Git blob 与上述公开源码逐项相同。SDK141／浏览器146正常单元全量重编，实际 Application 另用141个新游戏对象和4个新宿主对象。六种自机初始化3,024字、960次时钟比较、加载13组2,093帧均通过，六对其他作品优化对象相同。正式构建完成后，再使用该浏览器构建的游戏对象运行协作者的349组ANM：3,571帧、121,414个所选字一致，无缺失或错误默认操作码路由；57个资源的操作码扫描完成。诊断模块单独链接，不冒充正式浏览器 UI 验收。

Arch 生产包验证通过，服务正常。新代原点39个Runtime文件和公网39个完整解压响应体均与同代清单一致，包含HTML、loader、Wasm和字体；COOP／COEP／no-transform保留，没有分段请求或完整性绕过。此次公网检查首次全部通过，无缓存清除或失败项重跑。重启时第一轮本机curl连接被拒绝，既有重试随后取得正确清单；该瞬时记录保留。

18首现有Vorbis原样保留，仅上传5个运行文件约3.48MB，没有传送原作资产、重新提取或重新编码音乐。网站运行逻辑仍是`2eeb8db4`；fork文档提交`bd9badc9`只更新TH14核心构建指针，Arch检出也已前进到该文档提交。两个既有vendor LICENSE工作区改动保留。回滚目录为`/home/i/Code/th14-release/hosted-before-b8e36ef2`。

新实际静音普通菜单开局在540个宿主更新后到达灵梦B Normal首个Player／Present，线程、GPU、文件和时钟资源回收。它仍只是一帧玩法窗口，使用旧FLAC测试输入；未配对原版普通开局、验收新Vorbis最终PCM或浏览器UI。旧24次加载RNG、剩余弹状态、相机／完整画面、全部机体难度与完整录像、普通完整流程和存档均继续开放。

[发布收据与绑定](th14-player-clock-release-nov13.json)。所有原始资源、VM、画面、存档和二进制保留本地。
