# TH14 六自机 Extra 普通流程 · 2026-11-14

按[当前目标](../../GOAL.md)的可观察行为标准，验证六种自机使用真实 Normal 通关所得存档，从标题选择 Extra，自然通关、署名、返回标题并保存成绩，再由六个新 Application 进程读取。范围与具体结果见[机器记录](th14-ordinary-extra-loadouts-nov14.json)。

## 方法与边界

输入存档来自[六自机 Normal 普通流程](TH14_ORDINARY_NORMAL_LOADOUTS_NOV14.md)，没有构造解锁记录。只供给已有完整输入的物理按键和普通菜单操作；启动时钟是声明的外部测试条件，不写游戏中的 RNG、位置、库存、分数或完成标志，也不调用完成关卡的快捷接口。稳定玩法可使用固定逻辑步长加速；菜单与加载使用实际时钟。这是功能验收方法，不是生产性能结论。

实际运行 C++ Application、Wasm 与工作线程，使用录制图形接口且无可听音频输出；没有据此宣称全程真实 GPU、原版 Win32 界面或浏览器整局验收。测试构建校验 145 个提供对象和源文件绑定；规范 fixture 重编译的 Wasm 与执行版本相同。

## 检查内容

- 六自机各自自然走完 Extra，结果的最终分数与所用完整输入档案一致，成绩关卡为 8、续关数为 0。
- 每份存档的 Extra 通关／无续关计数由 0 增至 1，已有 Normal 排名和解锁、其他机体成绩保持。
- 六个新进程从实际写出的文件读取 Extra 通关计数，标题中的原有 Extra 解锁仍有效；成绩文件保持。
- 六份文件的 48 条记录类型、长度与校验和通过；原版解密／解压指令读取的 894,456 字节与独立解码一致。原版指令未修改，分配／复制／释放为声明的外部接口。
- 所测工作线程、文件、定时器和图形录制对象均正常退出。

## Extra 终点的测试修正

初版测试在灵梦 A 的结束状态 21 提前停止，错误标作 Game Over。实际 `PauseMenu::begin_end` 对完成的 Extra 使用此状态，再进入成绩署名和简化结束菜单；它不经过 Normal 的 ending／staff／标题 Results 页面。第二版测试通过正常菜单按键走完署名和返回标题，没有修改游戏逻辑。原始失败报告保留在 `artifacts/th14/ordinary-extra-nov14/reimua-extra-full-v1/report.json`，不将其改写成通过。

## 复核入口

构建：`tools/th14-build-ordinary-extra-nov14.py --out artifacts/th14/<新目录>`；运行：`tools/th14-run-ordinary-extra-flow-nov14.mjs <机体-extra> full`；新进程读回：`tools/th14-read-ordinary-extra-flow-nov14.mjs <机体-extra>`，通过 `TH14_FLOW_SOURCE_SAVE` 指定实际存档目录。输入、素材与原始存档留在本地，不随源码公开。

`tools/th14-qualify-extra-scores-nov14.py` 核验保存语义，`tools/th14-extra-score-native-codec-nov14.py` 逐份运行原版解密／解压指令，`tools/th14-qualify-ordinary-extra-nov14.py` 汇总绑定和有限验收证据。

本记录只补齐声明开局条件下的六自机 Extra 普通通关与存档链路。任意开局、其余普通难度和分支、全程 GPU／浏览器、最终音画仍按项目目标继续补齐；整作目标保持进行中，本次无需部署新的游戏运行模块。
