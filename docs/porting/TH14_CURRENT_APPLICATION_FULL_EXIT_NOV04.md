# TH14 当前 Application 的六面回放、退出与保存

2026-11-04，[启动配置回退修复 ae284631](https://github.com/AdingApkgg/thp/commit/ae284631c2ebaf4006eb8b17662bc5caeeb6da5c)的实际 C++ Application 完成灵梦 B Normal 完整回放及普通菜单退出，共 122,780 帧、53 项断言。此前玩法核心仍为 `51fcb479`。这次运行使用当前 Application 对象，没有把前一版本的完整运行当作本版本已通过。

从冷启动主菜单进入 Replay 列表，选择完整原始录像，实际经过一至六面；122,562 帧时自然到达 Replay 结束菜单，得分单位 91,452,576、残机 8，再稳定 60 帧。随后经 Replay 列表、主菜单和 Quit 到达 finished，调用生产保存 ABI，完成文件写入。整份录像 110,022 字节保持不变；原版格式成绩文件和 92 字节用户配置写出成功，异步回调队列为空。

参考运行是同一玩法核心、修复前 Application 的独立完整运行。当前版本与参考逐项比较结果为：

| 比较范围 | 结果 |
| --- | --- |
| 16 份完整载荷：动作、状态日志、断言、文件操作、保存清单、回调、音频等 | 全部相同 |
| 10 幅完整 BGRA 图像，合计 12,288,000 字节，保留 alpha，零容差 | 全部相同 |
| 10 份完整注册链快照，共 959 行 VM，各 303 字段及登记顺序 | 全部相同 |
| 虚拟静音音频 sink，90,086,400 帧 PCM 的增量摘要 | 相同 |
| 主机物理音频设备数 | 0 |

PCM 在产生时逐块计算摘要，没有额外保存数百 MB 原始 PCM。摘要为 `83c5d5007095faa9884f57f702579cd6ea29cd50f8ba140e6c30abf0bec07512`。这里的图像、VM 和音频参考均是封存的 C++ Application，**不是原版整局逐帧画面或音频参考**；没有做句柄映射、字段排除或像素容差。

另用此前实际浏览器导出的非默认成绩文件进行当前 C++ Application 的新进程读回：文件含已记录的灵梦 A Normal 成绩，21,656 字节、SHA-256 为 `ed92a752b5fc74288a87d74588a94b5292fbc2a69ef1b5394590693012dce50d`。配合非默认 BGM／SE 音量 37／53 的配置，冷启动、主菜单 Quit、生产保存后，成绩和配置全部字节保持不变。这个新检查没有运行浏览器或 IndexedDB，不替代本轮浏览器刷新验收。

运行在独立原生测试宿主中执行真实 Application、GLES 渲染及音频混合；宿主提供声明的初始时钟、进程 cookie、逐帧时钟、异步交付和私有文件。控制仅为归一化菜单输入及退出后的正常保存调用，未改关卡、RNG、生命、敌人或录像输入。141 个玩法核心对象与同核心参考逐哈希相同；配置回退只重编一个 Application 单元，其他设备对象也绑定到封存构建。测试静音，保留至少 100 GiB 空间，不复制字体和音乐资源。

独立结果与来源绑定：[th14-current-application-full-exit-nov04.json](th14-current-application-full-exit-nov04.json)。验证器先保留比较结果，再因任何不相同退出失败：

```powershell
python -X utf8 tools/th14-full-application-exit-evidence-nov04.py --output docs/porting/th14-current-application-full-exit-nov04.json --check
```

这个有限完整流程通过，不关闭普通原版 GUI、物理输入、独立加载调度、全部模式、浏览器 UI／持久化或原版整局像素／PCM。自然结束也不等于原文件声明输入全部用尽。`completeGame=false`、`nativeEquivalent=false`、`browserAcceptance=false`，整作 1:1 继续。
