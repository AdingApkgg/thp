# TH14 effect149 的栈输入来源 · 2026-10-26

新增实际原版公共命中调用链的组件证据：`451760 → 453a90 → 452050`。在 960 组声明的地址、Shot Z、奖励计数、种子和年龄输入中，聚焦命中读取的栈字最后均由 `453aae push edi` 写入，内容是调用者持有的目标坐标指针。工厂接收的 Z 等于 `float32(shotZ + reinterpret_float32(targetPositionAddress))`。

这比此前直接执行 `452050`、声明未写栈 Z 的实验多覆盖了真实奖励函数。公共包装函数先把 EDX 目标指针存入 EDI；奖励函数保存 EDI 的栈槽，随后被聚焦命中的局部向量 Z 复用。按包装函数入口 ESP 计算，该槽为 `ESP - 56`；聚焦回调入口为 `ESP - 40`，其读取位置为自己的入口 `ESP - 16`。15 个跳过奖励消费者的控制组保留原声明栈字，验证了这条写入链的作用。主实验执行原奖励函数，控制组的服务跳过不会进入生产代码。

进一步对照已有 Hard／Lunatic 原始记录：11 个隐藏根 Z 字均可关联到保留过的 `Enemy + 0x1234` 位置地址。其中三个使用同一回调的 VM／战斗对象快照；八个使用较早检查点，其中两个地址的观测明显更早。后八个关联不能证明命中时的对象身份，必须保留地址复用的不确定性，也不等于实时观测到了那条栈写指令。

[原版组件工具](../../tools/th14-focused-hit-stack-producer-native-oct26.py)和[独立检查器](../../tools/th14-focused-hit-stack-producer-evidence-oct26.py)绑定实际 EXE、指令、输入组合、完整组件记录以及原始快照的关联。[范围报告](th14-focused-hit-stack-producer-verified-oct26.json)重算工厂 Z 的浮点加法、最后写入者和控制结果。主实验不修改原指令；ANM 中断、特效分配、声音是声明的返回边界，道具池为空闲分配失败环境，没有执行实际特效工厂或完整渲染。

```powershell
python tools/th14-focused-hit-stack-producer-native-oct26.py `
  --output artifacts/th14/NEW_STACK_PRODUCER/native
python tools/th14-focused-hit-stack-producer-evidence-oct26.py `
  --native artifacts/th14/NEW_STACK_PRODUCER/native
```

需要本机原版 EXE、Unicorn；检查器另读取已有私有完整记录。原始内存和组件输出不发布。实验不启动原版进程，也没有向移植引擎提供原版指针或 Z 字。

生产地址／ABI 模型与实际调用点仍待实现和核对，Hard 六个、Lunatic 五个原始字差继续失败。本轮没有使用固定 Z、从快照灌入地址，或归一化／豁免该字段。此前[完整有限生命周期](TH14_EFFECT149_RETIREMENT_OCT26.md)仍只证明其声明输入下的后续家族行为；当前证据也不证明任意调用路径、整局图像、音频、普通浏览器或整作 1:1。
