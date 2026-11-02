# TH14 原版初始化时间覆盖检查

早期时间检查只核对报告中已经列出的 Initialize 项，不能发现某项被漏掉。现在另加完整覆盖检查：根据保留的原版事件流、原版报告和实际采样阶段，要求每个应出现的 Initialize 项恰好出现一次，再逐项核对事件位置和时间。此检查只约束 Initialize，不替代其他加载阶段或整局验收。

当前核心的 16 份自然回归全部通过。五种独立负控制分别修改时间、修改来源、漏掉事件、重复事件和篡改事件流，均被拒绝。新的组合入口先运行覆盖检查，再运行既有原始状态／相机／HUD／VM／战斗严格检查；正向样本两道均通过，未经原版证明的较早时间假设在进入严格检查前被拒绝。

```powershell
python tools/th14-verify-native-campaign-with-timing-nov03.py --native <原版记录目录> --model <移植记录目录> --timing-output <本地产物目录/timing.json> --build <observer-build.json> --output <本地产物目录/strict.json>
```

已有结果与验证范围见[证据元数据](th14-initialize-time-coverage-nov03.json)。此次没有修改游戏玩法，也没有启动原版或音频设备；其他线程时序、浏览器及整作 1:1 仍未完成。
