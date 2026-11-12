# TH14 上游协作修复与 Oracle 整合 · 2026-11-12

本次接回 Goan114 直接追加在网站 [PR233](https://github.com/Ritosa2333/eagler-touhou/pull/233) 分支的四个提交，而非从网站主线寻找这些补丁：

- [6bab4fce](https://github.com/AdingApkgg/eagler-touhou/commit/6bab4fcee6a0b77ec6eeb32845b3aa7c7ae8ab69)：ANM VM、界面、曲线激光与浏览器节奏。
- [5f2b79d3](https://github.com/AdingApkgg/eagler-touhou/commit/5f2b79d3ec8cc3adcca2ab1c720d9babe9a8f3e3)：按实际显示档上传纹理。
- [4202ff78](https://github.com/AdingApkgg/eagler-touhou/commit/4202ff7827d9c357c32b13324a80af8a931052a3)：实际 Ogg Vorbis、FLAC 回退与短按键保留。
- [9255fa4e](https://github.com/AdingApkgg/eagler-touhou/commit/9255fa4e745262a681dfc350f5732256befd9bca)：WebGL 提交刷新和双 fence 背压。

作者提供的补丁以 `5eb4ac87` 为基线，完整补丁 SHA256 为 `545842d97a9f58c62eddf89c8cea56b5ca84192d1937f42b2a8c540db843feb1`，覆盖 49 个路径。本地以已发布 `022a6aaa` 为基础接入，保留后来修正的 world-strip 原点。第一轮检查因该文件的换行空白不匹配而失败；忽略空白后可应用，未丢弃后续逻辑。

具体修复包括速度使能位 `0x800000`、旋转／缩放脏位、单值插值的 SSE 舍入、缺失的 ANM 411／418／419、按分辨率选择 ASCII、高分辨率纹理上传、曲线激光宽度及中间原点、暂停截图比例、续关禁用项恢复、原版菜单音效、短输入边沿与浏览器提交节奏。

先原样构建协作者的完整候选，146 个正常权限生产单元全部重编，再独立运行他提供的三套 Oracle。ANM 349 组、3,571 帧，每帧 34 字，共 121,414 字零差异；界面 69 项和纹理 12 组零差异。原版 EXE 与 DAT 哈希均核验。Oracle 使用声明的 cookie、D3D 和几何边界，纹理结果是分配／上传请求与直接复制判断，未测 GPU 滤波像素；界面使用受控菜单与几何。原版游戏进程及实际 GPU 没有启动，不能把这批结果当作整局通过。

整合保留原版配置的三种显示尺寸，移除协作补丁在浏览器中无条件固定 1280×960 的策略。在启动 worker 之前设置 ASCII 显示档，避免旧配置选择低分辨率时仍加载高清档。六个显示断言改为执行原版 `46ae40` 获取尺寸，而非沿用浏览器固定尺寸的字面期望。调整后的 349／69／12 三套对照再次全部通过；完整候选 Wasm 为 `a3a7770f72ed9bb89f6902f306e981435fbdd34ca16cda3c063cbbe9e44a1b70`。

共享代码还有六处非 TH14 对象变化：shader key 的编码表达式以及通用键盘／RAF 分派。将新增表达式与路径限定在 TH14，其他作品恢复原分支。TH12／TH13／TH16 共 48 对对象逐字节相等，比较时只规范化诊断文件路径；42 对已通过的未变结果复用，仅重编六个受影响候选。最终 TH14 只重编两个单元，另 144 个对象逐项核验，整个 Wasm 和 loader 与上述通过 Oracle 的候选逐字节相同，无需重复执行同一组件测试。

原样复核时的隔离环境失败均保留：首次缺少 `target.json`，随后 SDK 子进程选用了过旧的 Python，纹理录制依赖也未复制。这些发生在比较之前，不是游戏差异；补齐元数据／依赖并指定 Python 后通过。没有为通过比较而注入参考状态或放宽差异条件。

本次 Oracle 覆盖不接受浏览器双更新／跳绘制的物理时间线、真实输入延迟、最终 PCM、整帧、完整机体／难度或主线加载 RNG／弹状态。尤其不能将此前 Native 单派发组件的结论直接用于新的浏览器调度器。原 24 次加载 RNG 和其他严格反例仍保持开放，`completeGame=false`。所有测试均静音；原作资源、完整原始观测、存档及二进制不随 Git 发布。

[源码与证据绑定](th14-upstream-helper-integration-nov12.json)。源码已接回工作树；运行包交付另记收据，不能根据本文推定新包已经部署。

Native 对照用的 141 个 SDK 游戏提供者也已重新编译，功能宏与实际浏览器保持一致；旧 SDK／宿主对象已明确失效，不混用旧布局。新的宿主侧提供者及实际 Application 仍需独立验收。
