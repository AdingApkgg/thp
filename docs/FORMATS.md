# 东方原作数据格式对照表（th12–th18）

本文件是移植六作时共享的格式参考。所有结论都有出处，不靠猜。

## 1. 归档容器（PBG3 / THA1）

- 头部 16 字节用固定密钥解密：`th_decrypt(header, sizeof(header), 0x1b, 0x37, sizeof(header), sizeof(header))`。
- 目录表位于文件末尾倒数 `zsize` 字节处，用固定密钥解密：`{0x3e, 0x9b, 0x80, zsize}`，随后 LZSS 解压。
- 头部三个 32 位字段是 **存储值减去固定偏移**：`size-123456789`、`zsize-987654321`、`entry_count-135792468`。
- 每个条目的密钥由 **文件名所有字节之和 & 7** 选择，表按引擎代次切换：

| 作品 | 版本号 | 密钥表 |
| --- | --- | --- |
| th09.5 / th10 / th10.3 / th11 | 95 / 10 / 103 / 11 | `th95` |
| **th12 / th12.5 / th12.8** | 12 / 125 / 128 | `th12` |
| **th13** | 13 | `th13` |
| **th14 / th14.3 / th15 / th16 / th16.5 / th17 / th18 / th18.5 / th19 / th20** | 14+ | `th14` |

四张表已落在 [`ResourceCrypt.cpp`](../runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp)，
数值与 thtk 的 `thdat95.c` 一致（thtk 源码为准，因为已发布的 thtk v12 二进制不支持 th18）。

> 关键结论：**th14 之后所有作品共用同一张密钥表**，所以 th18 的归档没有额外密钥障碍，
> 障碍只在 thtk v12 二进制太老。运行时自己实现 PBG3 读取器即可覆盖全部六作。

## 2. 精灵档案（ANM）

档案头结构（TH11 起，64 字节）：

| 偏移 | 类型 | 含义 |
| --- | --- | --- |
| 0 | u32 | 版本 |
| 4 / 6 | u16 | 精灵数 / 脚本数 |
| 10 / 12 / 14 | u16 | 宽 / 高 / 格式 |
| 16 | u32 | 名称偏移 |
| 20 / 22 | u16 | x / y |
| 24 | u32 | 显存优先级 |
| 28 | u32 | THTX 偏移 |
| 32 | u16 | hasdata |
| 34 | u16 | lowresscale（v8 起有意义） |
| 36 | u32 | nextoffset（下一个 entry 的相对偏移，0 表示结束） |

指令结构（8 字节头 + 4 字节对齐参数）：

```c
struct AnmInstruction { u16 type; u16 length; i16 time; u16 param_mask; };
```

**版本分界**（来自 thtk `anm_types.h` 注释）：

- `7`：**th11、th12、th12.5**
- `8`：**th13 及以后**

也就是说 th11 模板里的 ANM 读取器对 **th12 可以直接用**（已实测，见下），
而 th13+ 需要在同一结构上处理 v8 的差异（`lowresscale` 生效、RT 纹理槽等）。

### THTX 像素格式

| 值 | 格式 | 字节/像素 |
| --- | --- | --- |
| 1 | BGRA8888 | 4 |
| 3 | RGB565 | 2 |
| 5 | ARGB4444 | 2 |
| 7 | GRAY8（亮度） | 1 |

th11 模板原本缺少 `7`，th12 的背景 ANM 大量使用它（如 `stage01.anm` 的 `stage01f.png`
是 512×256 的 GRAY8）。已补齐，见 [`AnmResource.cpp`](../runtimes/th12/th12_web/cpp/game/AnmResource.cpp)。

## 3. 游戏随机数

th12 与 th11 是同一族 xorshift/rotl2，只是地址不同：

```c
u16 next16(){ u16 m = (seed ^ 0x9630) + 0x9aad; seed = (m >> 14) | (m << 2); ++calls; return seed; }
```

| 作品 | next16 | next32 |
| --- | --- | --- |
| th12 | `0x004643d0` | `0x00464440` |
| th11（模板） | `0x458bc0` | `0x458c30` |

注意 th11 有第三个「一次消耗 4 个 word」的变体（`0x458d70`），**th12 没有**：
在 th12 反编译语料里只有两处出现该常量序列。

## 4. th12 原版可执行文件地址索引

来源：[`reference/th12-decomp`](../reference/th12-decomp) 的 Ghidra 反编译语料，
每个函数一个文件，文件名即 `<符号>_<地址>.c`，共 1941 个函数。

| 符号 | 地址 | 用途 |
| --- | --- | --- |
| `_malloc` | `0x0046d04a` | oracle 堆打桩 |
| `_free` | `0x0046c941` | oracle 堆打桩 |
| `_memcpy` | `0x0047a330` | oracle 打桩 |
| `FUN_004643d0` | `0x004643d0` | RNG next16 |
| `FUN_00464440` | `0x00464440` | RNG next32 |

`th12.exe` 的 PE：基址 `0x400000`，节区 `.text`/`.rdata`/`.data`/`.rsrc`，
184 个导入，来自 `dinput8` / `dsound` / `d3d9` / `d3dx9_40` / `winmm` / `kernel32`。

导出符号名可用以下命令重建：

```powershell
Get-ChildItem reference\th12-decomp\decomp_out -File |
  ForEach-Object { if ($_.BaseName -match '^(.*)_([0-9a-fA-F]{8})$') {
    [pscustomobject]@{ name = $Matches[1]; addr = '0x' + $Matches[2].ToLower() } } }
```
