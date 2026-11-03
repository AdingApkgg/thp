# TH14 背景对象核心的完整 Application 场景复核

这份历史复核明确绑定已发布源码 02eccdb19b81d10e5a1a1b9fe2eeb70880ee15eb、核心 dfb49af20c890c4f6c909e992af5828b21ecf1101cf1d04e57ee24fa842a9b1a，不代表后续逐字相机核心已完成同样的全长运行。[机器收据](th14-stage-object-full-application-nov04.json)。

GLES 与 WebGPU 两个实际静音 Application 都各运行 122,622 宿主帧、45 项断言，返回菜单后稳定运行 60 帧，进程均正常结束。各八幅图像、捕获动画、所选状态和保存文件检查，以及 89,969,664 帧离线 PCM 与封存 Application 参考一致。两后端物理音频设备打开数均零。

GLES 原计划文件里的 runner 哈希继承了旧值，现已公开披露纠正：实际启动时冻结的 runner 与该次原始运行报告相符，也逐字等于上述公开提交的 runner。原计划保留，单独纠正收据绑定原计划、实际报告和实际 runner；没有改变游戏输入、时钟或运行结果。WebGPU 启动前已修正计划绑定。验收器会检查这项纠正。

复核命令：python -X utf8 tools/th14-stage-object-application-full-evidence-nov04.py --backend both --output artifacts/th14/NEW_NONEXISTENT_RECEIPT.json。需要本机封存的私有证据目录；公开仓库只发布源码与哈希收据，不附原作资源。

比较对象是封存 Application 参考，不是原版整局画面／PCM。这不是原始录像 EOF、普通原版 GUI、独立线程调度或浏览器验收，整作 1:1 未完成。
