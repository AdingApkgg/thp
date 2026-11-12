# TH14 录像保存／重开及原版解码 · 2026-11-13

使用已修复新开局 D8 标志的真实 GameSession::record_stage_entry、GameSession::save_replay、ReplayRecorder、Replay::open/select/tick 执行 60 组受控录制。选择为六自机×五 difficulty 参数×两 practice 参数；部分合成参数并非实际菜单可选组合，不能据此声称全部游戏模式完成。普通 difficulty<4 构造两阶段记录，其他用一阶段；输入刻意覆盖按下／释放、33 帧跨 FPS 采样边界，以及末尾终止标记。

逐项检查重复保存字节一致、终止保存不改变活动录制的帧数／终止状态、选择字段、初次 D8=1／换关 D8=0、非零坐标，以及重开后每帧 held／pressed／released 和末尾六字节终止标记。这里没有加载 SHT／ANM 或运行普通战斗，输入直接进入录制器；不是整局录像或图形／声音验收。

随后由原版实际 4028e0 两次解密、465840 LZSS 解压全部 60 份保存文件。CRT 分配／复制／释放为明确声明的服务，原版指令未修改；每份文件使用原版零初始化字典起点，不接受真实进程热字典生命周期。解码后的所有字节与当前读取器保留的解码结果相同，并另按文件布局检查阶段数、初次／换关标志、非零坐标及每帧输入边沿。合成普通两阶段记录共 24 份，合成单阶段共 36 份。

阶段标志源码修复已在 Root，GameSession.cpp SHA256 为 0e0fb1e1d4174acbf13652f6118351f8732272f444882e57b690dcd63bce8be9。141 个提供者逐项核验并复用（其中 GameSession 是前轮正常权限新编对象），本轮仅编译访问放宽的诊断夹具。TH12／TH13／TH16 源码编译对象的前轮逐字节一致结果仍适用，本轮未更改引擎。尚未构建新浏览器包，线上仍是 59a8cc4c；不得把该源码修复记成已部署。

坐标清零候选经后续原版激活写入复核被拒绝，当前复制实际 Player 坐标的实现保留，见 [位置生命周期](TH14_REPLAY_ENTRY_POSITION_LIFECYCLE_NOV13.md)。当前结果不证明浏览器下载、操作系统写盘、实际普通游戏跨关／暂停／续关／通关、原版完整录像加载器或录像逐帧玩法等价。主线加载 RNG、僚机加载帧龄与相机物理交接等缺口继续；completeGame=false。

[公开计数和哈希绑定](th14-replay-save-reopen-nov13.json)。工具：tools/th14-replay-save-reopen-nov13.cpp、tools/th14-build-replay-save-reopen-nov13.py、tools/th14-check-replay-save-reopen-nov13.mjs、tools/th14-replay-save-reopen-native-codec-nov13.py。完整受控文件和解码字节仅保留本地 artifacts/th14/replay-save-reopen-nov13/files，不加入 Git；没有复制游戏资源、启动原版窗口、GPU 或音频设备。
