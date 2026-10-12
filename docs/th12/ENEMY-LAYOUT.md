# th12 敌人状态结构：与 th11 的两段线性偏移

## 结论

th12 的敌人状态结构与 th11 模板**不是同一套偏移，但同源**：

> **在 `emitters` 之前插入了 0x118 字节，在 `visual_size` 与 `flags` 之间又插入了 0x20 字节。**
> 也就是两段线性映射：`Δ=0x118`（中段）与 `Δ=0x138`（尾段）。

这条结论不是猜的：有 **五个** 字段在两个独立来源上对上，其中三个偏移是 th12 反编译里
直接读到的常量，两个由数组步长反推。前两个偏移完全对不上时，我们原本的结论是
"th11 处理器不可复用"；现在修正为"可复用，但要按字段重映射偏移"。

## 证据表

| th11 模板字段 | th11 偏移 | th12 观察到 | Δ | 来源 |
| --- | --- | --- | --- | --- |
| `emitter_offset[8]`（`Vec3`，步长 0xc） | 0x1414 | 0x152c | **0x118** | `case 0x1f5`(501) 读 `param_1+i*0xc+0x152c/0x1530/0x1534` |
| `emitter_origin[8]`（`Vec3`，步长 0xc） | 0x1474 | 0x158c | **0x118** | 同上，`+0x158c/0x1590/0x1594` |
| `visual_size`（`Vec2`） | 0x14d4 | 0x15ec | **0x118** | `case 0x106`(262) 写 `+0x15ec`、`+0x15f0` |
| `flags`（`u32`） | 0x1580 | 0x16b8 | **0x138** | `case 0x192`(402) `\|=`、`case 0x106`(262) 读 `&0x2000000` |
| `script_owner`（`Enemy*`） | 0x1614 | 0x174c | **0x138** | `*(int*)(param_1+0x174c)` 再 `+4` 取当前 `EclContext*` |
| `emitters[8]`（步长） | 0x214 | 0x214 | 0 | `case 0x1f8`/`0x1fd` 的 `param_1 + arg*0x214` |

`script_owner` 那一行是**语义**上的对上，不只是数字对上：th11 里
`Enemy{ EclOwner script; EnemyState state; }`，`script` 在 `Enemy` 偏移 0，
所以 `script_owner + 4` 正好是 `EclOwner::active`，即当前 `EclContext*`。
th12 的 `FUN_004154d0` 写的是 `*(int*)(*(int*)(param_1+0x174c) + 4)` ——
**同一个表达式形状**。这同时说明 `param_1` 按 `EnemyState` 的偏移寻址
（否则 `+0x174c` 落不到 `script_owner` 上）。

两处旁证：

- `emitter_offset` 与 `emitter_origin` 的间距在两个版本里都是 **0x60**（8×`Vec3` 步长 0xc）——
  说明这一段结构没有被改动，只是整体平移。
- th11 `emitters[8]` 的步长 `(0x1414-0x374)/8` = **0x214**，
  与 th12 `case 0x1f8`(504)/`case 0x1fd`(509) 里 `param_1 + argument(0)*0x214 + …`
  的步长**完全相同**。

于是 th12 的 `emitters` 基址可反推为 `0x152c - 8*0x214` = **0x48c**
（注意这是推算值，不是直接观测值）。th12 实际用到的槽内偏移：
`+0x04/0x08/0x0c`（x,y,z，见 501）、`+0x10/0x14`（504 写两个 float）、
`+0x24…+0x38`（509 写两 float + 四 int）。

## 这对移植意味着什么

1. **th11 的 `EnemyCommands`/`EnemyStateCommands`/… 处理器可以复用**，
   前提是把 `EnemyState` 的字段偏移按上表重映射。
   实现方式二选一：
   - 给 th12 单独一份 `EnemyState` 结构体（两段 `RESERVED[0x118]`/`RESERVED[0x20]` 占位），
     同一套处理器代码通过字段名访问——**推荐**，因为能继续用 `static_assert` 把偏移钉死；
   - 或者保留 th11 结构，只在访问处 +Δ——更容易出错，排除。
2. **扩展区 opcode 的号码仍然是 th12 自己的**，偏移映射解决的是"处理器怎么访问字段"，
   不解决"哪个号码用哪个处理器"。号码映射仍须逐条从 `FUN_004154d0` 取。
3. `param_1 + 0xe0 + i*4`（指针数组）与 `param_1 + 0x1620 + i*4`（int 数组）
   尚不能对到 th11 字段上，属于 th12 新增或位于未确定区间的成员，待补。

## 未确定

- **`param_1` 的身份仍未证实。** 五个字段全部落在 `EnemyState` 的偏移上，
  且 `script_owner` 的语义形状完全一致，所以可以按 `EnemyState*` 使用；
  但它是"独立的 `EnemyState`"还是"`Enemy`，且 th12 把 `EnemyState` 放在了偏移 0"，
  两者在观测上等价，尚未区分。
  `FUN_004154d0` 在 `.text` 里**没有直接调用点**
  （扫描 `E8 rel32` 指向 0x4154d0 的结果为 0），说明它是虚函数，
  通过 `EclServices::command` 的虚表间接调用——与模板的
  `EnemyScriptServices::command` 结构一致。
  `0x174c` 在整个反编译语料里**只被读、没有被写**，
  所以写入方在那个 Ghidra 语料之外（或用了不同的取址表达式）。
- `param_1 + 0x34/0x38/0x3c`（501 当作基准位置的 `Vec3`）在 th11 里对不到 `0x174` 的
  `absolute_position`；它更可能是管理器/发射器侧的量，不是敌人的位置。
- 完整的 th12 `EnemyState` 大小（≥ 0x1774）与 `BulletEmitter` 槽内布局尚未逐字段核对。

## 复现

```powershell
cd H:\code\thp
# 逐个 case 体（含 goto 共享标签的解析）见：
node tools\th12-opcode-map.mjs
# 调用点扫描（PE 节表在 e_lfanew+0x18+OptionalHeaderSize，本文件为 0x208）：
node tools\tmp\callsite.mjs 0x4154d0
```

反编译语料位于 `reference/th12-decomp/decomp_out/`（不随仓库分发）。
