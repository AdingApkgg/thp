# TH14 损坏配置的启动回退

2026-11-04，修复普通冷启动时读取无效 `th14.cfg` 导致整个 Application 初始化失败的问题。TH14 的启动调用点现在恢复默认配置并继续启动；有效配置保留全部 92 字节。修复不改变 `GameConfig::open` 或文件导入 ABI 的严格校验，也不改变其他标题的无效配置处理分支。

生产源码已发布：[ae284631](https://github.com/AdingApkgg/thp/commit/ae284631c2ebaf4006eb8b17662bc5caeeb6da5c)。此前玩法核心仍为 `51fcb479`；本次只修改 Application 的启动处理。

原版 `4454b8..445549` 检查六个选项、签名和长度；拒绝路径 `44552d` 经过错误日志，调用 `4376e0` 重置后在 `445549` 与正常启动合流。新组件实际执行这些原指令及重置函数的写入，1,568 组输入中 21 组有效、1,547 组拒绝，输出全部相符。控制器 20 字节为声明输入，CRT 清零和日志调用为受控边界；未把这个组件称为原版文件系统或普通 GUI 验收。

旧二进制的负例保留：92 字节的错误签名配置使 `Application::initialize` 以 `Invalid /save/th14.cfg` 失败。修复后的实际 Application 在相同输入下到达主菜单，经正常菜单 Quit 进入 finished，再调用生产 `th11_save_scores`，写出原版格式成绩和默认配置。初始化、菜单、保存、渲染和虚拟音频均使用实际生产实现，宿主只提供声明的文件、时钟、异步交付和归一化输入。

共 13 个实际用例、5,772 帧通过：缺失文件、错误签名、91／93 字节、空文件、六个选项分别越界、有效的非默认音量和保留字节，以及新进程重新加载。无效配置恢复默认值；有效配置及重新加载后的所有保存文件逐字节不变。初始私有输入不被改写，保存目录没有遗留 `.tmp` 文件。全部用例物理音频设备数为零。

本修复只改变 `cpp/sdl/Application.cpp` 的冷启动调用点。141 个玩法核心对象未改、逐哈希复用；原生 Application 重编一个适配单元，另四个设备对象复用。TH12／TH13／TH14／TH16 的该源文件语法检查通过。浏览器重编一个 Application 单元，复用 145 个对象；与上一构建比较，全部 C++ 输入只有该文件变化。新 Wasm 为 `ea291b20a2efe340fd5925331906dc8f768df4e39f2208a3bdfeb4db553f1d2e`。新包通过 139 条路由和 27 项真实 HTTP 请求检查，生成字体／音乐仍以硬链接复用，默认预览未改变。

独立复核索引：[th14-config-startup-fallback-nov04.json](th14-config-startup-fallback-nov04.json)。索引只包含结果、来源路径和哈希，不包含配置原始缓冲、原版内存、游戏资产或运行二进制。

```powershell
python -X utf8 tools/th14-config-startup-evidence-nov04.py --output docs/porting/th14-config-startup-fallback-nov04.json --check
```

这是冷启动回退、普通归一化菜单退出及原生文件读回的有限验收。没有启动或操作浏览器窗口，未证明 IndexedDB 刷新、原版普通 GUI、整局像素／PCM或独立加载调度。此前的一面浏览器观察及正在另行进行的完整回放均保持各自源码版本范围，不自动继承为这个新 Application 的完整验收。`browserAcceptance=false`、`completeGame=false`、`nativeEquivalent=false`，整作 1:1 继续。
