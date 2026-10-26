# TH14 相机逐分量写入与 Scene 复制 · 2026-10-26

原版实际指令现在复现出咲夜 B Easy 四面留存的混合 right 向量：X 已归一化，Y/Z 仍为原始值。这个值既不是绘制前的旧向量，也不是完整计算后的最终向量。只在整次绘制前后交付 Scene 的夹具不足以表达它；当前整局相机失败继续保留。

[组件工具](../../tools/th14-camera-store-interleaving-oct26.py)执行未修改的原版 `446400`、固定 x86 D3DX DLL，以及 `40d435..40d447` 的实际 Scene 复制指令。两个完整 CPU 上下文共享内存，分别承担主线程计算和工作线程的 `rep movsd`。设备 SetTransform 是声明的接收端；没有启动 Windows 游戏进程、窗口或音频设备。

## 真实写入顺序

| 完成的存储次数 | 指令 | right 的状态 |
| --- | --- | --- |
| 0 | 尚未写入 | 上一次保留值 |
| 1 | 原作 `446590`，8 字节 | 原始 X/Y，旧 Z |
| 2 | 原作 `44659d`，4 字节 | 原始 X/Y/Z |
| 3 | D3DX `101bcaa0`，4 字节 | 已归一化 X，原始 Y/Z |
| 4 | D3DX `101bcaa4`，4 字节 | 已归一化 X/Y，原始 Z |
| 5 | D3DX `101bcaa9`，4 字节 | 已归一化 X/Y/Z |

DLL 地址采用固定映像基址；Windows 实际装载地址需要通过模块 RVA 对齐。此次模型将原始 8 字节写指令视为一次事务，没有证明真实硬件在单条指令内部不会发生撕裂。

工作线程实际按地址递增复制 75 个双字、共 300 字节；right 位于第 13 至 15 个复制字。每个字可以读到不同的主线程存储阶段。因此对五个留存关卡输入，逐一执行全部 56 种单调阶段组合，共 280 次实际计算／复制和 21,000 次实际双字读取。每次都核对源／目的指针、剩余 ECX、完整复制缓冲、三个 right 字，以及主线程最终计算值。

全部实际复制结果与按真实写入构造的独立阶段模型相同；所有交错顺序均不改变主线程最终 right。二至六面的留存复制结果均在有限输出集合内。

四面第 48,006 回调的留存值只对应 `[3,3,3]`、`[3,3,4]` 两种所列阶段组合：三个字均在 X 归一化后读取，Y 在自身归一化前读取，Z 可以在 Y 写回前后读取。旧值、完整原始值、完整归一化值三个控制均与该留存值不同。这个实验确认部分写回足以生成它，但不能从缺少的历史时间信息中确定两种具体顺序之一，也不声称覆盖所有硬件交错。

## 复核与下一步

[范围、计数和哈希](th14-camera-store-interleaving-oct26.json)绑定未修改的原版 EXE、固定 D3DX、完整原版记录、复制事件、工具和全部私有组件输出。实际相机字只作为组件输入和结果比较，不传给游戏引擎。

```powershell
$env:PYTHONPATH='H:/code/thp/tools/tmp/th14-analysis-python;H:/code/thp/tools'
python tools/th14-camera-store-interleaving-oct26.py --home artifacts/th14/camera-interleaving-oct26/instruction-pair-final --summary docs/porting/th14-camera-store-interleaving-oct26.json --check
```

新增[逐字观察器准备工具](../../tools/th14-prepare-scene-copy-word-observer-oct26.py)，从当前未改动的版本化观察器生成独立冻结诊断版本。在实际 Scene 复制窗口中配置三个工作线程目标字硬件断点，并通过 TF 逐步执行原始复制指令；记录每步完整调试寄存器、复制计数、主线程 PC／寄存器及实际 DLL 装载身份。原始相机值属于诊断数据，不作为引擎输入。生成工具本身不启动游戏，不修改既有观察器；诊断版本明确标记前缀范围，离开复制窗口后清除所设 TF。

首次数据断点观察在 13,578 回调捕获第一个复制字后遇到未预期的断点状态，主动结束所创建进程并保留失败。该次没有留存失败点完整 DR6／DR7，不能推断具体原因。[Intel 手册 19.3.1.2](https://cdrdv2-public.intel.com/835755/253669-sdm-vol-3b.pdf)说明快速字符串操作的数据断点可能延迟至一组迭代完成，因而不能预设每个数据断点都给出独立字的时刻。

后续诊断缩小为预先声明的 15,000 回调／600 秒、100 GiB 磁盘余量及 2 GiB 输出上限，只验证二面的一次复制。TF 版本在断言前保留每步原始上下文；若迭代合并，仍直接失败，不把一次分组报告拆成臆测的字事件。其完成与复核结果单独记录；准备、组件通过和正在观察均不等于实际逐字记录通过。调试断点会改变线程调度，新运行不会改写旧失败；停止后的主线程 PC 也不等于复制瞬间的同步采样。

该诊断已正常结束并通过[独立观察复核](th14-scene-copy-word-prefix-oct26.json)：78 个原始调试事件核对了三条设置指令和全部 75 次实际复制迭代，目标 right 的三个字分别有完整 DR6／DR7、指针、计数和主线程停止上下文。没有未结束的复制观察器；到达预先声明的 15,000 回调后仅结束本工具创建的进程。它是诊断前缀，没有自然结束／普通菜单／六面通过结论。

## 新前缀的交付修正

同一份新记录在旧夹具中仍出现 1,286 个 right.x 字差：Scene 在整次复制开始时即交付，当时最近标记仍是控制器发布。新增三个目标字事件各自已有当前回调的原指令 `4465a6` 归一化完成标记。夹具现仅在显式提供并验证这种观察证据时，按该边界与时间在绘制后交付 Scene；不读取源／目的相机数值来决定引擎输入。

[同 Wasm 前后复核](th14-scene-copy-handoff-verified-oct26.json)确认 15,000 回调的全部 25 个相机字一致，原来的 1,286 个差异消失。所选 32 字、HUD、384 行动画及登记顺序、228 个战斗检查点和初始 2,023 次分配输出逐字不变。141 个核心对象和生产 Wasm 均未修改；变动属于观察夹具的宿主交付。

默认[严格复核工具](../../tools/th14-verify-native-campaign.py)增加显式观察凭据选项，仅接受另行复核的 15,000 回调 TF 前缀。没有改变状态、相机、动画或对象字段门槛：故意改坏一个相机字仍被拒绝。经典硬件断点路径的魔理沙 B Easy 完整 107,233 回调、2,630 行动画和 1,206 个战斗检查点也由当前复核工具回归通过。

```powershell
node tools/th14-compare-native-campaign.mjs --native artifacts/th14/retail-sakuyab-easy-copy-word-step-prefix-hardware-oct26 --assets artifacts/th14/native-campaign-assets/57d84a5cbe82-e98fc11baae2 --build artifacts/th14/replay-coverage-input-oct26/beam-owned-field-observer-final/observer-build.json --output artifacts/th14/camera-interleaving-oct26/new-word-handoff-model --selection 2,1,0,1 --prefix 15000 --scheduler-phases observed --scene-copy-observation docs/porting/th14-scene-copy-word-prefix-oct26.json
python tools/th14-scene-copy-handoff-evidence-oct26.py --home artifacts/th14/camera-interleaving-oct26 --output docs/porting/th14-scene-copy-handoff-verified-oct26.json --check
```

旧六面 Easy 记录的部分归一化值以及其他历史相机失败仍缺足够交付边界，不能继承新前缀结果；其全部字段门槛和失败计数继续保留。

完整模式中的相机字差、原版普通界面、整局图像／PCM、浏览器和整作 1:1 均未据此完成。原始相机、寄存器、录像、资源和二进制不随源码发布。
