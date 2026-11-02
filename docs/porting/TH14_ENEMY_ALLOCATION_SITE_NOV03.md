# TH14 敌人工厂的分配调用边界

使用本机原版 EXE 的实际 x86 指令，先执行 CRT 堆初始化至导入表中的 `KERNEL32!GetProcessHeap`，再从敌人工厂 `421ef0` 执行到 CRT 分配入口，直至 `KERNEL32!HeapAlloc`。操作系统调用返回的堆句柄和分配地址是声明的合成输入；导入表名称和原指令编码均从 EXE 核对。额外的零堆句柄控制会使原版初始化报告失败。

四个不同的合成分配返回地址都验证了相同的行为：工厂请求 `0x530c` 字节，`HeapAlloc` 接收同样的字节数和标志 `0`；在声明的 OS 调用边界返回后，原版工厂将该地址原样作为 `422ab0` 构造函数的 `this`，并保留构造参数。[复算摘要](th14-enemy-allocation-site-nov03.json)绑定原版 EXE 与工具哈希。

该实验执行了原版 CRT 初始化、工厂和分配包装指令，但没有执行 Windows 堆分配器或构造函数内部，也没有证明真实地址、堆布局、跨进程对象生命周期或完整分配顺序。合成地址不进入游戏引擎；既有 `worldZ` 字差和整作 1:1 仍未解决。

```powershell
python tools/th14-enemy-allocation-site-nov03.py --check
```
