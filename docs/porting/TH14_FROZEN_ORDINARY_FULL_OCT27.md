# TH14 首关种子修复后的六面回归与当前候选 · 2026-10-27

已完成绑定 `1d9999a47ea1c8510d4983d47ff22c50a544fad6` 核心的实际 C++ Application 六面回归。现有咲夜 B Hard 录像经普通归一化菜单选择进入一至六面，在残机 1 时自然结束，并保持 60 帧稳定。完整目标、原版普通界面与浏览器尚未验收。

## 冻结版本的全程结果

该次测试使用首关种子恢复后的两份重新编译源及 139 个经核对复用对象，实际 GLES 渲染、字体设备、异步文件服务及静音 PCM sink 均执行。场景仍是已有六面场景，没有改动输入、生命、血量、关卡或录像。

| 项目 | 结果 |
| --- | ---: |
| 实际 Application 帧 | 123,412 |
| 场景断言 | 44 |
| 留存状态日志 | 55,071 行 |
| 自然结束帧 | 123,352 |
| 稳定结束窗口 | 60 帧 |
| 实际关卡入口并激活 | 一至六面 |
| 结束残机 | 1 |
| 最终得分，存储单位 | 154,806,314 |
| 留存完整 BGRA 画面 | 8 幅，9,830,400 字节 |
| 实际静音 PCM sink | 90,553,344 帧 |

每次关卡入口后再运行 240 帧，核对实际战斗时钟重置并前进，曲目依次为 1、3、5、7、9、11。入口截图可能仍显示前一场景的过渡，不能代替各关完整图像验收。初始和最终的 110,306 字节录像文件相同，没有待处理的异步回调或物理音频设备。

在该次回归仍运行时，另预先声明最终得分与残机的只读比较。结束时的 154,806,314 单位与原录像解码头及已有原版暖启动终态相同；残机均为 1。原版参考的实际回调数为 122,811，其首次 Player 后明确清除演示位，不能称为原版普通界面。此处只新增终态所选字段的比较，不宣称两条流程的所有回调、图像或 PCM 相等。

该次代码冻结在 `1d9999a`。[随后模式标志修复](TH14_ATTRACT_RUN_FLAGS_OCT27.md)的 `45b76f0` 仅另有其列明的前缀验证，不继承本次全程通过。KMK 魔理沙 B Normal 的二面失败、30／25 模式覆盖以及其他历史差异保持不变。

## 包含模式标志修复的当前候选

静音入口为 `http://127.0.0.1:8222/?game=th14`，绑定 `45b76f0ea6e35df132437f5f1b201e93d34ea25b`。全部 146 个 C++ 单元重新编译，零对象复用。Wasm 为 2,700,275 字节，SHA-256 `3797f4950b008743e88e2436727089747a63c2887e5d64cb1d91639d93318d69`。

133 条路由、21 项 HTTP／协议检查通过；另实际请求服务中的 Wasm、宿主、着色器及默认静音脚本并核对字节。28 份生成字体／音乐仍使用别名，逻辑大小 414,850,582 字节，未重复复制原版资产。保存的 HTTP 记录证明其观察时刻的服务内容，不是浏览器或玩法验收。

8220 及更早入口保留各自冻结版本。所有测试和预览静音，维持 100 GiB 空闲保护及每例 128 MiB 观察输出限制。

## 复核

[全程检查器](../../tools/th14-frozen-ordinary-full-evidence-oct27.py)与[全程范围报告](th14-frozen-ordinary-full-verified-oct27.json)核对冻结源码、实际构建、全部 25 项动作、44 项断言、六次激活、结束稳定性、输入、画面和终态得分。原始 PCM 只经 sink 累计哈希，没有独立留存，也未与原版整局音频对照。

[通用候选检查器](../../tools/th14-local-candidate-evidence-oct27.py)与[当前候选范围报告](th14-attract-candidate-verified-oct27.json)核对全部源绑定、146 个对象、Wasm、生成资源别名、实际 HTTP 记录和已发布代码的种子／标志调用方。

```powershell
python tools/th14-frozen-ordinary-full-evidence-oct27.py --home artifacts/th14/initial-replay-restore-oct27/sakuyab-full-current --build artifacts/th14/initial-replay-restore-oct27/application-build-gles --backend gles --output docs/porting/th14-frozen-ordinary-full-verified-oct27.json --check
python tools/th14-local-candidate-evidence-oct27.py --home artifacts/th14/attract-run-flags-oct27 --expected-code-commit 45b76f0ea6e35df132437f5f1b201e93d34ea25b --output docs/porting/th14-attract-candidate-verified-oct27.json --check
```

只发布源码与哈希元数据；原版资产、录像、原始报告、像素、PCM 与二进制留在本机。`completeGame=false`、`nativeEquivalent=false`、`browserAcceptance=false`，继续按[剩余清单](TH14_REMAINING_ACCEPTANCE.md)推进。
