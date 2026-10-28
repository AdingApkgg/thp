# TH14 首批 Sig／ASCII／text 后台解析

2026-10-29。最早的 `sig.anm`、`ascii.anm` 和 `text.anm` 现由独立 CPU worker 实际解压／解析。之前它们在 `Application.initialize` 及 `GameSessionResources.load_core` 中同步完成，早于已有的上传队列。

新的延期路径先保留空资源与稳定所有者，首个 Decode 任务派发三份资源。交付成功后，仍按 Sig、ASCII、text 顺序准备模板，随后才开始原来的 file 1／2／0 上传。工作线程运行期间没有悬挂 Asyncify 栈。后续重复 bootstrap 不再读取；未完成的 bootstrap 不能被 `prepare_core` 同步补读。关闭 browser archive-worker 的消费者保留同步初始化。启动任务仍使用既有代际／挂起检查，并补充已发布任务的所有者检查，没有加入固定帧补偿。

## 有限验证

- 实际生产资源入口在调用者返回时保持三份资源未解析；独立 worker 交付后的全部 ANM 字段、浮点位、纹理及脚本字节与直接解析相同。两次完整有效批次、三份资源分别损坏、失败批次不回退、重复 bootstrap 不再读取及随后有效恢复通过，总计 12 次解析包复制。此组件没有 Application、图形或音频设备。
- 类头文件声明改变后完整重编 146 个浏览器单元。主 Wasm 2,749,413 字节，SHA-256 `40d5504776f8ebf11e275bb3bdc823be3d727a4d363184529f8dfba74ca939bd`；worker 文件与前次剩余核心资源版本逐字相同，worker Wasm 76,918 字节。无关根目录 ResourceCrypt 修改继续排除。
- 从同一冻结源码新编 141 个原生核心单元，分别链接实际 Application／设备／GLES 或 WebGPU。两后端各 2,264 帧、七项断言通过；状态、两份完整 BGRA、339 个活动 VM、RNG、文件和 1,508,352 帧静音 PCM 与此前结果相同。原生宿主关闭 archive-worker，使用声明的时钟／回调；独立 CPU 解析协议和实际浏览器另行验证，不能用该原生结果代替浏览器线程时间测量。
- 139 条路由／27 项 HTTP 以及实际服务的主模块和 worker 字节通过。Chromium 156 静音页面观察到标题及自动演示。
- 测试响应层拒绝 `ascii.anm` 时，同一主 Wasm 的实际 C++ 在首次资源上传前报 `TH14 background bootstrap resource decode failed`。注入只改测试 Endpoint 及对应哈希元数据；故障服务已停止，正常 worker 恢复并整页重载，标题与演示重新出现。
- 恢复后通过菜单进入 Normal 灵梦 A 一面，观察到普通游戏、结束后的成绩姓名、返回标题。该样本包含续关及未逐键控制的菜单输入，可见成绩 111,521；它只证明这些画面和流程已经出现，不是原版分数对照、逐键一致性或移动／暂停验收。

[验证摘要](th14-bootstrap-worker-verified-oct29.json)绑定冻结源码、对象、模块、原生记录、完整图像、组件结果和实际浏览器错误／恢复记录。保留本地测试产物的工作区可以运行：

```powershell
python -X utf8 tools/th14-bootstrap-worker-evidence-oct29.py --check
```

公开内容只有源码、工具、文档和哈希元数据，原作资源、录像、截图及生成模块留在本地。正在另一个静音页面运行的 `2e6d794` 整段咲夜 B Hard 回放属于前次冻结构建，不继承给本次。

SHT 解析、GPU／模板准备及后续换关尚未全部后台化；独立原版线程交付时序、全模式、完整普通流程和全帧图像／音频继续。`completeGame=false`、`nativeEquivalent=false`。
