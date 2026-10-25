# TH14 完整录像对照工具复用 · 2026-10-25

将此前本机组合夹具迁为仓库内的 [C++ 观察夹具](../../runtimes/th12/th12_web/tests/cpp/th14-native-campaign-fixture.cpp)，与参数化的 [构建工具](../../tools/th14-build-campaign-observer.py)、[对照工具](../../tools/th14-compare-native-campaign.mjs) 配套使用。自机、难度、输入归档、已验证对象、原版观察和输出目录均显式传入，减少逐模式复制脚本。生产游戏代码未因这次迁移修改。

构建工具验证已有核心的源码、头文件及对象 SHA256，再重链接观察夹具，不重复编译同一组 141 个核心对象。存在无关 ResourceCrypt 工作区改动时，只有显式允许后才排除该工作区源文件，继续使用原先校验过的对象，排除情况写入报告。夹具现仅引用仓库内头文件，不依赖旧的私有绝对包含路径。

示例均从仓库根目录执行，原作、输入归档和原版观察需要事先准备，不能从公开源码取得：

```powershell
python tools/th14-build-campaign-observer.py --reuse-build artifacts/th14/stage-item-retirement-oct25/observer-curve-cursor-build.json --output artifacts/th14/example-campaign-build --allow-unrelated-resourcecrypt-edit
node tools/th14-compare-native-campaign.mjs --native artifacts/th14/retail-reimub-hard-full-bounded-hardware-oct25 --assets artifacts/th14/native-campaign-assets/57d84a5cbe82-c5db55756f58 --build artifacts/th14/example-campaign-build/observer-build.json --output artifacts/th14/example-hard-comparison --selection 0,1,2,1
```

输出目录必须为新的 TH14 产物目录。`--prefix` 只验证相应前缀，不能代替自然结束的完整录像；默认要求实际 HUD 初始化写完时刻，选择 `--hud-ready boundary` 时仅具有主线程观察边界的较弱范围。发布序列窗口通过 `--publication-cutoff` 声明，完整对照时必须与原版报告一致。动画创建环形缓冲每批最多读取 4,096 项，越界直接失败。

当前工具针对完整标准关卡录像的显式时序观察，不代表普通原版菜单冷启动或全部模式已通过。原版观察器的首次选择校验原先写死为灵梦 B Hard，现已改为检查命令中声明的自机和难度；原 Lunatic 尝试在零回调时退出，失败记录保留，未计通过。

迁移核验复用同一原版记录与核心对象：

- 完整灵梦 B Hard 的 107,662 次所选状态回调、镜头、HUD、七个动画检查点及 1,496 个所选对象检查点继续一致。
- 迁移前后共 1,508 份状态、动画、对象和发布输出逐字节一致。新模块与旧观察模块的文件哈希不同，分别记录，不冒充同一二进制。
- 灵梦 B Lunatic 一至三面共 38,530 次回调在新工具中通过，包含 521 个所选对象检查点。原版完整采集自然结束 104,544 次回调，但四面未观察到主线程加载完成位清除；完整对照因此拒绝继续，未计整段通过。

针对这个采集缺口，观察器在 HUD 初始化写完后，将该 worker 的硬件执行断点移至 `43605a`，直接观察原版 `436053` 的 `and [ebx+80],~4` 执行之后。读取七个原指令字节 `83a380000000fb` 并确认完成位已清除；只提供完成时刻，不把计分、随机数或其他现场数值交给移植核心。新采集已捕获一至四面该事件，前 40,000 次回调及 485 个所选对象检查点通过；其完整回放仍在进行。原缺口记录和失败对照保留，未由猜测时刻补成通过。

新增完成位观察之前的迁移核验工具 SHA 与之后的新分支核验分别记录。旧工具源码在本机按 SHA 保留；此前完整 Hard 的 1,508 份输出相同比较不冒充新分支的完整 Lunatic 验证。

模块及范围绑定见 [迁移核验](th14-campaign-tooling-verified-oct25.json)。已有记录和仍缺的自机／难度组合见 [30 组模式清单](TH14_MODE_ACCEPTANCE_OCT25.md)，由 [清单生成工具](../../tools/th14-mode-acceptance-inventory.py) 读取实际保留文件生成。该清单区分自然结束、实际关卡范围与已报告的所选状态对照，不将记录存在自动判为模式等价。

测试保持静音并遵守 [存储限制](TH14_STORAGE_POLICY_OCT25.md)。原版观察、存档、录像、资源和二进制留在本机。实际 GPU／音频、当前包浏览器流程和整作 1:1 仍未完成。
