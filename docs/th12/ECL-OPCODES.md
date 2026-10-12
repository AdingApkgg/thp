# th12 ECL 指令集：表已到手，语义待补

## 结论

th12 的 ECL opcode **编号空间**与**参数文法**已经拿到并有机器可验证的对照；
缺的只剩 **opcode 名字**和**每条指令的具体行为**（尤其 256 以上的 th12 专有指令）。

| 项 | 状态 |
| --- | --- |
| 指令封装格式（16 字节头 + 4 字节对齐参数） | ✅ 已验证 |
| opcode 编号全集 | ✅ thtk `th12_fmts`，278 条 |
| 每条指令的参数个数 | ✅ 与实际字节码 100% 吻合（28409 条指令） |
| opcode 名称 | ❌ 无本地来源 |
| opcode 行为语义 | ❌ 需从 `th12.exe` 取 |

## 1. 指令格式（已确证）

从 `stage01.ecl` 的 `BGirl00` 原始字节手工对出：

```
00 00 00 00 | 0b 00 | 2c 00 | 00 00 | ff | 03 | 00 00 00 00 | <28 字节参数>
  time(i32)   id(u16) len(u16) rank(u16) ff  cnt   pad(u32)
```

- `time` @+0：i32，与已过时间的比较量
- `id` @+4：u16，**opcode**
- `len` @+6：u16，整条指令字节数（含 16 字节头，4 字节对齐）
- `rank` @+8：u16，难度位掩码 `1111LHNE`（thtk 注释：高位恒 1）
- `0xff` @+10：常量
- `cnt` @+11：**参数个数**（thtk 认为"无法得知"，实际就在这个字节）
- 参数从 +16 开始，各 4 字节，内联字符串按 4 字节对齐

## 2. opcode 编号全集

`docs/th12/ecl-opcodes.json`（由 `tools/th12-ecl-opcodes.mjs` 从
`reference/thtk/thecl/thecl10.c` 的 `th12_fmts[]` 生成，可 `--check` 校验）。

thtk 解析签名时是**回退链**：`th12 → th11 → alcostg → th10`，取第一个命中。
按同样规则合并后，th12 的**有效**表是 **278 条**：

```
0-1  10-17  21  40  42-45  50-89        <- 核心区（与 th11 同编号）
256-371  400-456  500-535  600-611  700 <- th12 专有区
```

与 th11 逐条对比（同样按回退链合并）：

- **核心区 0–89 没有任何新增编号**，th11 已有的编号 th12 全部保留；
- **没有丢失任何 th11 编号**；
- **核心区只有 1 处签名变化**：`89` 由 th11 的 `SSS` 变成 `fff`；
- **新增 69 条，全部 ≥ 256**。

换句话说：**th11 的 opcode 枚举在 th12 的核心区几乎可以直接用**，
问题不在于核心区，而在于 **256 以上的 th12 专有指令**。

## 3. 参数个数：与真实字节码逐条对照

`tests/cpp/th12-ecl-opcodes.test.mjs` 把 `th12.dat` 里全部 9 个 ECL 文件
（28409 条指令）的参数个数与签名逐条核对。

签名里的 `*` 是"重复"标记：thtk 解码循环（`thecl10.c:1375`）遇到 `*` 就**不再前进**，
所以只有紧跟 `*` 的那个字母会重复零到多次。因此 `m*D` 最少 1 个参数、可变；
`SS` 固定 2 个。

结果：

```
28409 条指令，用到 278 条 opcode 中的 157 条，0 条无法解析，0 条参数个数不符
其中 112 条是 th12 专有（>=256），覆盖 10150 条指令 = 全部指令的 35.7%
```

这是三重交叉验证：我们的指令封装对、thtk 的签名表对、`+11` 字段确实是参数个数。

## 4. 引擎为什么卡住（已定位到具体 opcode）

增加 `cpp/game/Trace.hpp`：一个 `volatile i32 trace_point`，ECL 解释器在每次分派前写入
`2000 + opcode`，`GameBattle::initialize` 每步写入序号。wasm 陷阱会毒化实例、
不能再调导出函数，所以测试先取地址、陷阱后直接读线性内存。

结果：

```
TRAP unreachable trace_point = 2402
  -> ECL opcode 402, thtk signature "S"
```

**具体机制**：`EclInterpreter.cpp` 用 th11 的 `Op` 枚举解释 th12 的 opcode，
402 不在枚举里 → 落到 `default:` → `services.command(*this)`。
而 th11 的 `services.command` 按 th10 承袭下来的 402 号指令处理它
——**号码撞车，执行了完全不同的指令**，随后栈失衡，
在 `DivideInt`（56）上以除零触发 `__builtin_trap()`。

所以这不是"未知指令被忽略"，而是**已知指令被张冠李戴**，比想象中更危险：
它不会报错，只会静默算错。这也说明为什么不能靠"宽容跳过"来绕过这张表。

### 4.1 已修：撞车改为显式拒绝（不再陷阱）

`EnemyScript.cpp` 现在在任何分派之前先查一张 `kTh12CollidingOpcodes` 表：
签名与 th11 同号指令**不一致**的 opcode 一律返回 `-2`（unavailable），
并记录 `{instruction, thread_id, time, opcode}`。

效果（同一份测试、同一个入口）：

```
修复前: TRAP unreachable trace_point = 2402   （opcode 402）
修复后: begin returned 0 | error: "stage battle initialization failed: stage main: ECL opcode 402"
```

这是**用显式失败替代静默算错**，不是功能完成。当前拒绝 46 个 opcode、
共 3206 条指令；剩余 65 个待抄写的 opcode 覆盖 6925 条指令。
拒绝表由测试与工作图（下节）对账，不能自行漂移。

## 5. 扩展指令工作图（新增）

`docs/th12/ecl-extended-opcodes.json` + `tools/th12-opcode-map.mjs` 把四路信息并成一张表：

| 来源 | 提供 |
| --- | --- |
| `FUN_004154d0` 的 173 个 `case` 体 | th12 实际存在的 opcode 与其体形状（`noop`/`shared`/`inline`/`fallthrough`） |
| `docs/th12/ecl-opcodes.json` | th12 签名 + 与 th11 同号指令的差异 |
| `cpp/game/Enemy*.cpp` | 引擎当前能处理哪些号码 |
| `artifacts/.../th12-ecl-opcodes.json` | th12.dat 真正执行了哪些 opcode、各多少次 |

当前分布（222 个扩展 id）：

| verdict | 数量 | 含义 |
| --- | --- | --- |
| `collision` | 46 | th12.dat 在用，签名与 th11 同号指令不同 → **已改为拒绝** |
| `todo` | 65 | th12.dat 在用，行为尚未抄写 |
| `unused` | 110 | th12.dat 未用到 |
| `noop-in-original` | 1 | `case 0x1a4: break;` —— 原件里就是空操作，已照实现 |

`noop` 这一类是本轮的一个白捡结论：**0x1a4（420）在原件里是空操作**，
而 th11 会把它路由进激光处理器。照原件实现后它不再有副作用。

### 5.1 已确证的结构体布局与 th11 模板一致

读 th12 反编译时逐字段核对，th11 模板的四个结构**与 th12 逐字节相同**：

| th11 模板 | th12 原件用法 | 结论 |
| --- | --- | --- |
| `EclInstruction`（16 字节，`references`@+8，参数@+16） | `FUN_00468e20` 读 `+8` 位掩码、`+0x10+i*4` 参数 | 一致 |
| `EclStack`（`top`@+0x1000，`frame_base`@+0x1004） | 上下文 `+0x1008`/`+0x100c` | 一致 |
| `EclContext`（`instruction`@+4，`owner`@+0x1014，size 0x1024） | `*(int*)(ctx+4)=instruction`，`ctx+0x1014` | 一致 |
| `EclOwner`（`active`@+4，`program`@+0x102c） | `*(int*)(owner+4)` 即当前上下文 | 一致 |

也就是说：**核心区（0..89）与运行时结构可以直接复用，问题被隔离在扩展区（≥256）的语义上。**
这让剩下的工作从"重做一个引擎"缩小为"重做一张分派表 + 若干处理器"。

敌人侧进一步确证：th12 的 `EnemyState` 与 th11 模板是**两段线性偏移**关系
（中段 `Δ=0x118`，尾段 `Δ=0x138`，五个字段对上，其中 `emitters[8]` 步长 0x214 完全相同），
所以 th11 的敌人处理器也可复用，只需按字段重映射偏移。
见 [`docs/th12/ENEMY-LAYOUT.md`](ENEMY-LAYOUT.md)。

`FUN_00468e20(ctx_unused, EclContext*, index)` 就是 `EclContext::argument/float_argument`
的原件（ECX 未用，EDX 是上下文，index 在栈上）。

## 6. 还缺什么

### 6.2 opcode 行为

名称拿到也只是标签，行为仍须从 `th12.exe` 取。可行路径：

1. **从 `FUN_004154d0` 读**。这个函数 16758 字节、173 个 `case`，
   在指令 +4 处取 `short` 后做 `switch`，范围正是 `0x100..0x263`
   ——即 th12 专有区。它就是 th12 的扩展指令解释器。
   很多 `case` 体只有一行 `goto switchD_00415546_caseD_XXX;`，工作图已把
   `fallthrough`/`shared` 两类解析出来，读的时候只需看被共享的标签体。
   `FUN_0041a900(i)` 就是 `argument(i)`（绑定了当前上下文），
   `FUN_00468e20` 是取值原语。
2. **差分实验确认**。用本仓已有的 Unicorn oracle 骨架
   （`tests/cpp/th12-oracle.mjs`），构造只含单条 opcode 的合成 ECL 脚本，
   在 `FUN_004154d0` 的入口设断点、观察写入 ECL 上下文字段的偏移，
   从而给每条指令定性。这条路不依赖 Ghidra 伪代码的可读性。
3. **对照 th13**：th13 的 `th13_fmts` 有 267 条，与 th12 重叠度高，
   可用编号对齐交叉印证。

### 6.3 已知的深水区

抄写 `todo` 里的若干条会牵出大函数，不是一行的活：

- `case 0x101`/`caseD_100`（opcode 257/280）会构造一个 0x50 字节的参数块，
  再调 `FUN_00412990(name, params)`——**敌人构造器**。
  也就是说 th12 的"生成敌人"不是核心区的 `Spawn`（15），而是扩展区一族指令。
- `case 0x118` 的共享体 `switchD_00415546_caseD_100` 同样落进这条路径。
- opcode 402 = `manager->flags |= argument(0); if(flags & 0x20) 16× FUN_00461d80();`，
  而 `FUN_00461d80` 遍历敌人清掉一个标志位——语义要等 `FUN_00461920`
  （敌人查找）与 `manager+0x16b8` 的含义确定后才能命名。

因此"112 个 opcode"不该按行数估工：其中一部分要先补出敌人构造/查找这一层。

## 7. 复现命令

```powershell
cd H:\code\thp
node tools\th12-ecl-opcodes.mjs            # 重新生成签名表
node tools\th12-ecl-opcodes.mjs --check    # 校验签名表是否过期
node tools\th12-opcode-map.mjs             # 重新生成扩展指令工作图
node tools\th12-opcode-map.mjs --check     # 校验工作图是否过期
node tools\th12-ecl-case-map.mjs           # 重新生成「opcode -> case 体」映射
node tools\th12-ecl-case-map.mjs --check   # 校验映射是否过期
cd runtimes\th12
node --test --test-concurrency=1 th12_web/tests/cpp/th12-ecl-opcodes.test.mjs
node --test --test-concurrency=1 th12_web/tests/cpp/th12-ecl-coverage.test.mjs
node --test --test-concurrency=1 th12_web/tests/cpp/th12-engine-boot.test.mjs
# 启动测试会打印当前停在哪条 opcode，并写入
# runtimes/th12/th12_web/artifacts/cpp/verification/th12-engine-refusal.json
```

## 8. 分发表：每个 opcode 到底跳到哪段代码（新增）

`FUN_004154d0` 不是普通 switch，是**两级表**：

```
0x41551e  movzx eax, word [edi+4]        ; eax = opcode
0x415522  movsx ecx, ax
0x415525  add   ecx, 0xffffff00          ; ecx = opcode - 0x100
0x415533  cmp   ecx, 0x163               ; 范围 0x100..0x263
0x415539  ja    0x41962b                 ; 越界 -> 尾段
0x41553f  movzx ecx, byte [ecx+0x419890] ; 一级：字节索引表
0x415546  jmp   dword [ecx*4+0x419654]   ; 二级：跳转表
```

所以 **opcode → case 体地址是可计算的**，不需要猜标签。
`tools/th12-ecl-case-map.mjs` 就做这件事，并把结果写进
`docs/th12/ecl-case-bodies.json`。实测：

| 项 | 值 |
| --- | --- |
| opcode 范围 | 0x100..0x263（356 条） |
| 不同 case 体 | 143 个 |
| 落到尾段 `0x41962b` 的 | **193 条** |
| 有真实指令体的 | 142 个表项 / 163 条 opcode |

**尾段 `0x41962b` 是什么**：`xor eax,eax`（返回成功）＋ SEH 收尾 ＋ `ret`，
没有任何副作用。也就是说**这 193 条 opcode 在原始引擎里就是空操作**，
不是「还没实现」。这一点对移植很关键：凡是映射到 `0x41962b` 的 opcode，
直接当成空操作通过即可，不需要从 th12-decomp 反编译。

不过要说清收益边界：把空操作集合与 `docs/th12/ecl-extended-opcodes.json`
的判定交叉比对后，**`todo`(65) 与 `collision`(46) 里一条空操作都没有**——
空操作只出现在 `unused`(110) 中（58 条）。所以这个结论省掉的是
「以后碰到这些编号别再当报错」，而不是把 111 条待实现指令变少。

## 9. 第一条拦路指令：402 / 0x192

`stage01.ecl` 的 main 开场就是 `40, 402, 280, 15, 83, 257, 420, 11`，
所以浏览器实跑停在 402。它的 case 体已经定位并读出（`0x417934`）：

```
0x417934  xor  ecx,ecx
0x417936  mov  eax,ebx
0x417938  call 0x41a900             ; eax = argument(0)
0x41793d  or   [ebx+0x16b8],eax     ; state->flags |= argument(0)
0x417943  test byte [ebx+0x16b8],0x20
0x41794a  je   0x41962b             ; 没置上 0x20 就结束
0x417950  lea  esi,[ebx+0xe0]
0x417956  mov  edi,0x10
0x417960  mov  eax,esi
0x417962  call 0x461d80             ; 16 次
0x417967  add  esi,4
0x41796a  sub  edi,1
0x41796d  jne  0x417960
0x41796f  jmp  0x41962b
```

三个可直接核对的结果：

1. `[ebx+0x16b8]` 就是 `EnemyState::flags`。这与 §5 里独立推出来的
   th11 `0x1580` → th12 `0x16b8`（Δ = 0x138）**互相印证**。
2. `argument(0)` 走的是 `0x41a900`，与已确证的 `argument` 绑定一致。
3. 后面是**对 `state+0xe0` 处 16 个 4 字节元素逐个调用 `0x461d80`**。
   相邻 case `0x417974`（403）是它的镜像：`flags &= ~argument(0)`，
   然后若 `!(flags & 0x20)` 就对着同一数组调 `0x461d40`（18 个字节开外）。
   即 402/403 是「成对开启/关闭 `state+0xe0` 的 16 个槽位」。

所以 402 要落地，还差两件事的先证：`state+0xe0` 那 16 个槽位是什么，
以及 `0x461d80` / `0x461d40` 做什么。在这两件确定之前，
**只实现 `flags |= argument(0)` 是不诚实的**——那样阶段会带着 16 个未初始化的槽位继续跑。

### 9.1 已落地（含实跑证据）

上面这两个问题现在都有答案：

1. **`0x461d80` / `0x461d40`**：按 id 查对象（`0x461920`）后，清 / 置该对象
   `+0x47c` 的第 1 位，并沿 `+0x14` 的子链表递归。
2. **`0x461920(id, manager)` 对 `id == 0` 直接返回 null**（函数头
   `test ecx,ecx; jne; xor eax,eax; ret 4`）。
3. **实跑测到 16 个槽位在这次调用时全是 0**：
   `opcode=402 flags=00005020 update=1 slots: 00000000 ×16`。

因此「16 次调用什么也不做」是**精确**的，不是近似。实现取不做事，
并在槽位非 0 时显式拒绝（那时原版会真的去调 `0x461d80`）。

还要注意 `EnemyScript.cpp` 会**先**试 `enemy_emitter_command`，
而那里 th11 的 `0x192/0x193` 用 `i(0)` 当发射器下标、
`u32(index)>=8` 就 `__builtin_trap()`——402 的参数正是 `0x20`。
所以必须同时把 `0x192/0x193` 从 emitter 的 case 列表里摘掉，
否则新 case 永远跑不到，页面直接 trap。详见 `DELIVERY.md` §7。
