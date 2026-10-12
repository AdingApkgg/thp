# th12 浏览器交付链（当前状态）

本文记录「th12 在浏览器里真正跑起来」这条链路的**实测进度**与复现命令。
结论以 headless Chrome 的实跑输出为准，不以「代码看起来对了」为准。

## 1. 现在能跑到哪一步

`scripts/serve-th12.mjs` + `sdl-runtime/th12.html` 把 th12 的 WASM 运行时送到浏览器。
用 headless Chrome 实测，页面依次通过：

| 阶段 | 结果 |
| --- | --- |
| 加载 Emscripten 运行时 `th11-harness.wasm` | ✅ |
| 载入 `th12.dat`（31 MB，183 条目） | ✅ |
| 载入烘焙字体（6 个 `.bin`，16.2 MB） | ✅ |
| `_th11_initialize()`：资源核心（ANM/ECL/SHT/MSG/STD） | ✅ |
| 音频初始化：载入 49 个 SE 采样 | ✅（见 §2） |
| 标题画面 ANM 创建（`title.anm`，233 脚本） | ✅（见 §2） |
| 音乐布局查询 + 18 首 OGG | ✅ |
| 标题画面**渲染**（60 FPS，画面有内容） | ✅ |
| 吸引演示：标题闲置 1800 帧后读 `demo3.rpy` 并解密解压 | ✅（本轮修复，见 §3） |
| 舞台图形：背景 / logo / 敌人 ANM（含 GRAY8 格式） | ✅（本轮修复，见 §4） |
| 舞台开场 ECL：`402`/`403`（标志/可见性对） | ✅（见 §7） |
| 舞台开场 ECL：`280`（`mSSSSS`，相对坐标生成敌人） | ✅（本轮，见 §8） |
| **第一关真正跑起来**（开场序列 `40,402,280,15,83,257,420,11` 全部通过） | ✅（本轮） |
| 舞台持续运行 + 渲染动画 | ✅ 实跑 91 秒、60 FPS、0 次 trap |

也就是说：**第一关现在能在浏览器里跑起来了**——标题 → 吸引演示 → 第 1 关舞台
持续渲染并动画。浏览器实测 91 秒无错误无 trap，画面每帧约 12 万像素在变；
引擎侧 12 项测试全过，其中「开局并存活 120 帧」从 skip 变成了真跑。
（注意口径：这 12 项来自 9 个 `th12-*` 文件；仓库里 133 个测试文件按正式
glob 跑是 140 项 / 12 过 / 122 失败，原因见 §10——不要把这 12 项当成全套。）

## 1.1 实跑时间线（本轮实测）

`tools/browser-proof.mjs` 用 CDP 驱动 headless Chrome，每秒采样一次 DOM 状态：

```
ms=1      error=""  health=""        welcomeHidden=false
ms=5849   error=""  health="60 FPS"  welcomeHidden=true   <- 标题画面已在跑
...
ms=91059  error=""  health="60 FPS"  welcomeHidden=true   <- 95 秒全程无错误
errors: []      traps: 0
```

闲置阈值 1800 帧（约 30 秒）一到，标题装载 `demo3.rpy` 进入吸引演示；
**这次它一路跑通并画出舞台**——同一次运行的截图序列（每 15 秒一张）：

```
cyc.png 11279, cyc-1.png 11182          <- 标题（约 11 KB）
cyc-2.png 376213, cyc-3.png 367004,
cyc-4.png 360353, cyc-5.png 363581      <- 舞台：约 36 万字节，相邻帧 12.2 万像素在变
```

复现命令见 §5、§8.2。

## 2. 修掉的两处会让启动直接失败的偏差

### 2.1 SE 采样表不是 th11 的

th11 的 `sound_samples[46]` 里有 `se_hint00.wav`，**th12 根本没有这个文件**；
启动时 `resources.read()` 直接返回失败：`Missing sound: se_hint00.wav`。

th12 自己的采样表可硬证据恢复：`th12.exe` 的 `.data` **0x4aea50** 处是
**49 个连续指针**，指向 `.rdata` 里的 `se_*.wav` 字符串，且顺序与 `th12.dat`
的归档顺序**逐条一致**。已据此替换 `SoundEffects.cpp` 的 `sound_samples[49]`。

`sound_definitions[56]`（音量/元数据）**仍是 th11 的**，只把 `sample` 字段按
**文件名**重映射到 th12 的表上。th12 丢弃了 7 个 th11 采样
（`se_hint00/se_water/se_warpl/se_warpr/se_msl/se_cat01/se_alert`），
用到它们的 4 条定义暂时落到 index 0，代码里已用注释标为占位而非证据。

### 2.2 ANM `Sprite(-1)` 哨兵

`title.anm` 的脚本 79 / 83 第一条有效指令就是 `Sprite`，参数 **-1**：

```
op 68 len 12 time 0 args 22     ; 层/优先级
op 3  len 12 time 0 args -1     ; Sprite(-1)
op 108 ...
```

`bind_sprite()` 拒绝负数下标 → 脚本中止 → `create()` 返回 nullptr →
标题创建失败（原报错只给脚本号 83，已补成 `...(ANM opcode 3)`）。
`AnmRenderer` 本来就把 `sprite == nullptr` 当作「不画」（`return -2`），
所以把负数解释为「不绑定精灵」既安全又与渲染器一致。

## 3. 吸引演示：Replay 容器是 th11 的形状，但**密钥不同**

标题闲置 1800 帧后 `GameSession` 会装载 `demoN.rpy`（在 `th12.dat` 里，共
`demo0..demo3` 四个）。th11 的 `Replay::open` 逐项拒绝了 th12 的文件。三处偏差
全部从 `th12.exe` 自己的重放装载函数里读出来，不是猜的：

th12.exe `.text` 0x43c3c2 起就是装载函数。它按
`lea edi,[eax+0x24]` 取正文，`cmp dword [eax],0x72323174` 查魔数，
`cmp word [eax+4],4` 查版本，`mov edi,[eax+0x1c]` 取压缩长度。

### 3.1 魔数：`t12r`，不是 `t11r`

```
0x43c3cd  81 38 74 31 32 72   cmp dword ptr [eax], 0x72323174
```
`0x72323174` 小端就是 ASCII `t12r`。版本字仍然是 4（与 th11 相同），
所以**只有魔数变了**。

### 3.2 两趟异或密钥：th11 的用不了

```
0x43c428  push 0x800          0x43c42d  push 0xe1          0x43c434  mov al,0x5e
0x43c442  push 0x40           0x43c444  push 0x3a          0x43c448  mov al,0x7d
```

| | 第一趟 | 第二趟 |
| --- | --- | --- |
| th12 | key `0x5e` step `0xe1` block `0x800` | key `0x7d` step `0x3a` block `0x40` |
| th11（原来写死的） | key `0xaa` step `0xe1` block `0x800` | key `0x3d` step `0x7a` block `0x40` |

用错密钥时 LZSS 不会报错，只会提前撞上终止符：实测四个 demo 都只解出约 54%
（如 `wrote 17864 of 33323`）。换成 th12 的密钥后四个 demo **全部精确解压**
（`wrote == unpacked`，终止符正确）。

### 3.3 舞台记录头是 `0xA0`，th11 是 `0x90`

```
0x43c49c  lea edx,[eax+0xa0]         ; 输入正文 = 记录 + 0xA0
0x43c4cc  lea eax,[eax+ecx+0xa0]     ; 下一条记录 = 记录 + payload + 0xA0
```
`frames`@+4 与 `payload`@+8 的相对位置不变，所以证据是自洽的：四个 demo 都满足
`payload == frames*6 + (1+(frames-2)/30)`，而按 0xA0 走正好落在缓冲区末尾。

原先硬编码的 `0x90` 让舞台遍历比缓冲区少 16 字节，报
`unexpected replay data after stages`。现在 `Replay.hpp` 定义
`kReplayFileHeader=0x70` / `kReplayStageHeader=0xA0`，六处引用全部改成常量。

### 3.4 回归闸门

`tools/th12-replay-format.mjs --check` 把上面每条都钉死在二进制上：它先校验
`th12.exe` 里那 8 个 push/mov 立即数的字节，再从这些立即数推出密钥与头长度，
用它解密 `th12.dat` 里的四个 demo（必须**精确**解压、舞台遍历必须落到缓冲区末尾），
最后检查 `Replay.cpp` / `Replay.hpp` 里的常量与二进制一致。改错密钥时闸门会失败
（已做反向验证）。

## 4. 舞台图形：ANM 的 GRAY8（格式 7）

装第一关图形时报 `Unable to prepare ANM texture: background/stage01/stage01f.png`。
原来 `TextureImage` 把 `format>=6` 一律拒绝，而 th12 的舞台背景真的用了
**THTX 格式 7 = GRAY8（亮度，1 字节/像素）**——`thtk` 的 ANM 枚举就是
`1=BGRA8888, 3=RGB565, 5=ARGB4444, 7=GRAY8`，`AnmTexture::rgba()` 早就在处理 7，
只有送进显存的这条路没处理。实测元数据是
`format=7 kind=0 512x256 pixel_format=7 pixel=512x256 pixel_bytes=131072`
（512×256×1 = 131072，正好是一字节一像素）。

修法：格式 7 展开成 BGRA8888（R=G=B=亮度，A=255，与 `AnmTexture::rgba` 的解释一致），
并把「输入布局」与「显存布局」分开，避免再出现「输入 1 字节、输出按 1 字节算」这类错配。

顺带修了一处可诊断性缺陷：`GameSessionResources::load_stage` 会把
`effects->prepare()` 的具体错误覆盖成一句泛化的 `stage graphics preparation`，
现在经 `last_error()` 透传，报错会带上真正的纹理名与原因。

## 5. 复现命令

```powershell
cd H:\code\thp\runtimes\th12\th12_web

# 1) 字体（只在本机烘焙，不入库）
npm install koffi --prefix H:\code\thp\runtimes\th12   # 一次即可
node scripts\prepare-fonts.mjs

# 2) WASM 运行时
node scripts\build-sdl.mjs

# 3) 起服务（只监听 127.0.0.1，端口 TH12_PORT ?? 8113）
node scripts\serve-th12.mjs

# 4) 无头浏览器实跑（CDP 驱动，能拿到时间线 + 截图）
cd H:\code\thp
node tools\browser-proof.mjs --url "http://127.0.0.1:8113/?autostart=1" `
  --out artifacts/th12 --shots 2 --interval 15000 --wait 100000 --prefix demo
# 报告写到 artifacts/th12/browser-proof.json，帧写到 artifacts/th12/demo*.png

# 5) 回归闸门
node tools\th12-replay-format.mjs --check
node tools\th12-sound-table.mjs --check
node tools\th12-music-table.mjs --check
```

注意：headless 下**不要**加 `--disable-gpu`，否则 `getContext('webgl2')` 在远程调试
模式下返回 null（即使带了 `--enable-unsafe-swiftshader`）。可用组合是
`--headless=new --no-sandbox --enable-unsafe-swiftshader`。

`?autostart=1` 是 `th12.html` 里的一个小开关：模块 shell 挂好事件后自动点「启动游戏」，
让整条链可以在无头环境里被驱动。

## 6. 下一步（按收益排序）

1. **剩下的 TH12 专有 ECL 指令**：65 条 `todo`（6925 条指令）+
   43 条 `collision`（被显式拒绝），见 `docs/th12/ecl-extended-opcodes.json`。
   开场序列已经全部打通（§7/§8），所以现在不再是「进不去」，
   而是**打得更久/走到别的关卡时**才会撞上。优先级建议按 `usedInTh12Dat`
   从高到低：509(870)、504(673)、256(548)、501(325)、502(312)、500(307)、258(301)。
   语义都要从 `FUN_004154d0` 转写，`docs/th12/ecl-case-bodies.json` 给出每个
   opcode 的 case 体地址，`reference/th12-decomp/decomp_out/FUN_004154d0_004154d0.c`
   是同一函数**已经反编译好的 C 代码**——优先读它，比读汇编快得多。
2. **一个已知的位常量分歧**：`EnemyManager.cpp:115` 用 `e.flags&0x400000` 决定
   是否走 3D 投影生成，而 `FUN_004154d0` 的 `switchD_00415546_caseD_100`
   用的是 `flags & 0x2000000`。两者在开局时都不置位，所以不影响当前路径，
   但必须用证据定谁对（很可能 th11 常量没跟着 th12 重编号）。
2. `sound_definitions` 的 56 条音量/元数据表仍是 th11 的，需要用
   th12.exe 里对应的 `.data` 表替换（按 56×8 / 56×12 两种布局扫描均未命中，
   说明 th12 的记录形状或条数与 th11 不同，需要先定形状再扫）。
3. th12 存档 / 触控布局校验（Replay 的 0xA0 头已确证，但
   `ReplayStageState::read` 的字段偏移仍是 th11 的，尚未与 th12 对照）。
4. fork/适配 host，把 th12–th18 注册进运行时目录。
5. th13 / th14 / th16 / th17 / th18 流水线。

## 7. 本轮：402/403 拿下，以及一个被 th11 处理器吞掉的 trap

### 7.1 402/403 是 th11 的 0x142/0x143 换了编号

th11 里「改 `flags` 并批量切换可见性」的那对指令在 th11 是 `0x142/0x143`；
th12 把同一对指令放到了 **402/403**（`0x192/0x193`），并把作用范围从
`animations` 扩到 **`state+0xe0` 开始的 16 个 dword**：

```
0x417934  call 0x41a900        ; argument(0) —— 已确证的 argument 绑定
0x41793d  or   [ebx+0x16b8],eax ; state->flags |= arg0
0x417943  test byte [ebx+0x16b8],0x20
0x41794a  je   0x41962b         ; 没置上 0x20 就直接结束
0x417950  lea  esi,[ebx+0xe0]
0x417956  mov  edi,0x10         ; 16 次
0x417960  mov  eax,esi
0x417962  call 0x461d80         ; 去激活
```

`0x461d80`/`0x461d40` 是「按 id 查对象，然后清/置该对象 `+0x47c` 的第 1 位」，
查找函数 `0x461920` 开头就是：

```
0x461920  mov ecx,[esp+4]   ; id
0x461924  test ecx,ecx
0x461926  jne 0x46192d
0x461928  xor eax,eax       ; id == 0 直接返回 null
0x46192a  ret 4
```

所以「16 个槽位全是 0」时，原版这 16 次调用**什么也不做**。实跑把这一点测了出来：

```
[th12 402/403] opcode=402 flags=00005020 update=1 slots:
  00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
  00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
```

`flags=0x5020` 说明 `argument(0)=0x20` 确实或了进去、`update=1` 分支确实走了。
因此实现取「不做事」，并且**在槽位非 0 时明确拒绝**——
那种情况下原版会去调 `0x461d80`，而我们没有复现它，宁可报错也不静默。

### 7.2 真正的 trap：th11 的 emitter 处理器抢先吃掉了 402

光加 case 不够：`EnemyScript.cpp:34` 会**先**试
`enemy_movement_command || enemy_emitter_command`，而
`EnemyEmitterCommands.cpp` 的 case 列表里有 `0x192/0x193`（th11 的
「设置发射器 sprite/color」）。它用 `i(0)` 当发射器下标：

```
EnemyEmitterCommands.cpp:14
  const i32 index=i(0); if(u32(index)>=8)__builtin_trap();
```

402 的参数是 `0x20`，于是 `32>=8` → **`__builtin_trap()`**。
现象是页面在 **ms=33087** 抛出 `RuntimeError: unreachable`，
而 `#error` 是空的、FPS 定格——因为 trap 不在被捕获的那条路径上。

把 `0x192/0x193` 从 emitter 的 case 列表里摘掉后，流程才落到
`enemy_state_command` 的新 case 上。

**这条给后续所有 opcode 提了个醒**：`enemy_state_command` 不是 402 唯一的入口，
`i(0)` 被两个处理器用不同含义解释时，先跑的那个可能直接 trap。

### 7.3 副产品：wasm trap 现在可以符号化

`build-sdl.mjs` 原来用 `-g0`，wasm 里没有 name section，`RuntimeError: unreachable`
只能看到 `wasm-function[568]`。加上 `--profiling-funcs` 后
（`-O2` 下保留函数名，无性能代价）就能直接读出来：

```
[568] th11::EnemyScriptServices::command(th11::EclContext&)
[525] th11::EclContext::update(float, th11::EclServices&)
[555] th11::enemy_frame(...)
[558] th11::EnemyManager::spawn(char const*, th11::EnemySpawn const&)
```

配合 `tools/tmp/wnames.mjs` 可以随时把任意 trap 栈翻成 C++ 函数名。
本轮 402 的定位就是靠它把范围从「整条启动链」缩到 `command()` 一行。

### 7.4 记住的两条命令

```powershell
# 浏览器侧的证据（会写 artifacts/th12/browser-proof.json）
node tools\browser-proof.mjs --url "http://127.0.0.1:8113/?autostart=1" `
  --out artifacts/th12 --shots 1 --interval 40000 --wait 60000 --prefix run --port 9466
# 引擎侧的证据（会写 artifacts/cpp/verification/th12-engine-refusal.json）
cd runtimes\th12 ; node --test --test-concurrency=1 th12_web/tests/cpp/th12-engine-boot.test.mjs
```

**注意**：`th12-engine-boot.test.mjs` 读的是**预编译**的
`artifacts/cpp/game-core-test.wasm`。改了 C++ 之后必须
`node scripts/cpp/build.mjs` 重建，否则测试会拿着旧二进制报一个过时的 frontier
（本轮就出现过：网页已经跑到 280，测试还在报 402）。


## 8. 本轮：280 拿下，第一关跑起来了

### 8.1 280 是 0x100 的共用 case 体

`12` 的 `0x118`（280）和 `0x100` 在 `FUN_004154d0` 里**共用同一个 case 体**
（`reference/th12-decomp/decomp_out/FUN_004154d0_004154d0.c`，
`switchD_00415546_caseD_100`，反编译文件里 `case 0x100: case 0x118:` 一起
`goto` 过去）。所以 280 不是新指令，就是**相对坐标生成敌人**。

它调用 `FUN_00412990(name, params)`，而后者已经被反编译出来
（`decomp_out/FUN_00412990_00412990.c`）：

```c
pvVar3 = operator_new(0x27b8);
iVar4 = FUN_00413230(param_1);        /* 按名字查敌人定义并构造 */
*(undefined4 *)(iVar4 + 0x10a8) = *param_2;      /* x */
*(undefined4 *)(iVar4 + 0x10ac) = param_2[1];    /* y */
*(undefined4 *)(iVar4 + 0x10b0) = param_2[2];    /* z */
...
    把敌人挂进管理器链表（iVar2 = DAT_004b43dc）
```

参数块 `local_a0` 的填法与槽位对应关系，和移植里已有的
`EnemyManager::command`（`mSSSSS` 布局：arg0 = 字符串字节数、名字在
`instruction+20`、整数参数从 `20+string_bytes` 开始）**逐条吻合**：

| 反编译 | 移植 |
| --- | --- |
| `local_a0 = f(1) + [ebx+0x34]` | `value.position.x = floating(1) + e.current.position.x` |
| `local_9c = f(2) + [ebx+0x38]` | `value.position.y = floating(2) + e.current.position.y` |
| `local_8c = i(3)` → `param_2[5]` | `value.health = integer(3)` |
| `local_94 = i(4)` → `param_2[3]` | `value.score = integer(4)` |
| `local_90 = i(5)` → `param_2[4]` | `value.drop = integer(5)` |
| `param_2[8..]` ← `[ebx+0x23c]` 12 个 dword | `memcpy(value.integers, e.integers, 48)` |

所以移植里这套逻辑**早就写对了**，缺的只是**路由**：
`EnemyScript.cpp` 只把 `0x100..0x10f` 送进 `commands.manager`，而 `0x118` 不在这个区间，
于是掉进 `enemy_state_command` 被当成未转写指令拒绝。

改动就三处：
1. `EnemyManager.cpp` 的 `relative` 里加上 `op==0x118`；
2. `EnemyScript.cpp:40` 的路由条件加上 `op==0x118`；
3. 把 280 从 `kTh12CollidingOpcodes` 拿掉。

### 8.2 证据

**引擎侧**（`node --test ... th12-engine-boot.test.mjs`）：
`game_session_begin` 从「返回 0 并给出命名拒绝」变成**返回 1 直接开局**，
「开局并存活 120 帧」那条从 skip 变真跑：

```
✔ TH12 engine starts a stage battle and survives 120 frames
ℹ tests 12 / pass 12 / fail 0 / skipped 0
```

产物 `th12-engine-refusal.json` 同步变成 `"battleStarts": true, "frontier": null`。

**浏览器侧**（`tools/browser-proof.mjs`，95 秒）：

```
frames: cyc.png 11279, cyc-1.png 11182, cyc-2.png 376213,
        cyc-3.png 367004, cyc-4.png 360353, cyc-5.png 363581
errors: []      traps: 0      health: 60 FPS
```

前两帧是标题（约 11 KB），后四帧是舞台：**每帧约 36 万字节、11.6 万种颜色、
24.1 万非黑像素**，相邻帧约 **12.2 万像素在变**。对比上一轮最好的一帧
（450 种颜色、6.6 万非黑像素），这已经不是同一个量级——
第一关的背景与角色真的在画、在动。

### 8.3 顺带修掉一个会说假话的测试

`th12-engine-boot.test.mjs` 原来断言「开局必须被拒绝」，现在开局成功了，
它反而失败。已改成断言**不变量**而不是结论：
要么开局成功，要么给出**带 opcode 的命名拒绝**（绝不能是 trap）——
并把这个二选一的结果写进产物。这样无论将来 frontier 前进还是后退，
这条测试都仍然在守它真正该守的东西。
## 9. 本轮：先量后写——真正的拦路虎是 400/406，不是用得最多的那几条

上一轮结束时只知道「第一关能跑」。要决定接着转写哪些指令，靠
`usedInTh12Dat` 排序是在猜：用得多的指令未必先撞上。于是写了
`tools/th12-stage-probe.mjs`，用原生引擎把**七个关卡逐个真跑**，记录每关
撑到第几帧、被哪条指令拒绝。每关用**独立的 wasm 实例**——引擎有全局状态，
共用一个实例会把上一关的残留算到下一关头上（第一版就是这么误报 stage 3 的）。

`node tools/th12-stage-probe.mjs 3000`：

| 关卡 | 结果 | 拦路指令 |
| --- | --- | --- |
| 1 | 跑满 3000 帧 | — |
| 2 | 跑满 3000 帧 | — |
| 3 | 第 121 帧 | **ECL opcode 400**（`0x190`） |
| 4 | 第 101 帧 | **ECL opcode 406**（`0x196`） |
| 5 | 第 121 帧 | **ECL opcode 400** |
| 6 | 第 121 帧 | **ECL opcode 406** |
| 7 | 跑满 3000 帧 | — |

七关**全部都能开局**，卡的是中段/关底。下一步应该做 400 和 406，
而不是按用量排在前面的 509(870)、504(673)、256(548)。

### 9.1 400/401 是什么（已解出）

case 体地址：400 → `0x4178d8`，401 → `0x417906`（来自
`docs/th12/ecl-case-bodies.json`）。两个体结构相同，都是

```asm
mov  eax,[esi+4]          ; esi = EclContext，[+4] = instruction
xor  ecx,ecx              ; 参数下标 0
call 0x468ec0             ; 从 instruction 取 float 参数
fstp dword [ebx+0xd0]     ; 400 写 +0xd0，401 写 +0xd8
mov  eax,[ebx+0x174c]
mov  eax,[eax+4]          ; 再来一次「取 instruction」
mov  ecx,1                ; 参数下标 1
call 0x468ec0
fstp dword [ebx+0xd4]     ; 400 写 +0xd4，401 写 +0xdc
jmp  0x41962b             ; 共用收尾
```

签名对得上：th12 的 400 是 `ff`（两个 float），th11 同号是 `S`——所以它在
`kTh12CollidingOpcodes` 里，被显式拒绝而不是让 th11 的处理器吞掉。

**偏移是什么**：th11/th12 在 `0x1414` 以下是同一套布局。移植里
`Movement` 是 `0x34`（`current.position` 正好在 `0x34`，与
`FUN_004154d0` 里的 `[ebx+0x34]` 一致），于是

```
previous 0x00  current 0x34  absolute 0x68  relative 0x9c
hitbox 0xd0   collision_box 0xd8   animations 0xe0
```

所以 **400 设置 `hitbox`，401 设置 `collision_box`**（每个两个 float，
和 `ff` 签名一致）。移植里这两个字段就叫 `e.hitbox` / `e.collision_box`。

**一个还没定死的点**：第一个 float 来自当前上下文（`[esi+4]`），第二个来自
`[ebx+0x174c]` 的 `+4`。按 Δ=0x138 的映射 `0x174c` 是 `script_owner`，
但移植里 `script_owner` 是 `Enemy*`，而这里需要的是「能取 `.instruction` 的东西」
（即 `EclContext*`）。要么 th12 的 `script_owner` 类型就是上下文，
要么 Δ 映射在这个字段上不成立。**写 400/401 之前必须先把这一点用证据定死**，
否则第二个坐标会读错来源。这就是下一轮的第一件事。

### 9.2 406 是什么（已解出，只差偏移映射）

`FUN_004154d0` 里 0x196 是内联体（`decompiled: "inline"`）：

```c
case 0x196:
    _memset((void *)((int)param_1 + 0x1624), 0, 0x4c);
    break;
```

旁边 0x197 是 `[param_1 + 参数*4 + 0x1620] = ...`，说明 `0x1620` 起是一个
4 字节元素数组，406 清掉从第 1 个元素起的 19 个 dword。`0x1620` 落在
`0x1414` 的 Δ=0x118 段落里（对应 th11 的 `0x1508`），需要先把这一段
映射到移植的结构体字段才能落笔。同样留作下一轮。

## 10. 一个必须先纠正的数字：测试并不是「12 项全过」

前面几轮报的「12 项测试」是**我挑选的 9 个 `th12-*` 文件**。仓库里
`th12_web/tests/cpp/*.test.mjs` 一共有 **133 个文件**，而
`reference/th11-eagler` 的 `docs/BUILD.md` 写的正式跑法是**整个 glob**：

```
node --test --test-concurrency=1 'th12_web/tests/cpp/*.test.mjs'
```

照这个跑，实际结果是 **140 项 / 12 过 / 122 失败 / 6 跳过**。所以要说清楚：
**这个 fork 目前只有 12 项能真正跑起来**，前面那个「全过」是有前提的。

失败原因只有三个，全部量过：

| 数量 | 原因 |
| --- | --- |
| 109 | `th12_web/reference/native/unicorn-bounded.wasm` 不存在 |
| 12 | 写死了 `../[th11] 东方地灵殿 (汉化版+日文版)/th11.dat` 这个 th11 时代的路径 |
| 1 | `artifacts/cpp/analysis/jp/functions/004526f0.asm` 不存在 |

109 项占 133 个文件里 **107 个文件**——它们都调 `helpers.mjs` 的 `oracle()`：

```js
const m=await NativeMachine.create(bytes,{wasmBinary:readFileSync(
    resolve(root,'reference/native/unicorn-bounded.wasm'))});
m.replace(0x460192,'malloc',()=>m.allocate(m.u32(m.reg('ESP')+4)));
m.replace(0x45fc3b,'free',()=>0);
m.call(0x48abf0);
```

两个问题叠加：(a) 那个 wasm 二进制根本不在仓库里（`@alexaltea/unicorn-js`
只提供 `unicorn_x86.js`，不是同一个东西）；(b) `oracle()` 里的
`0x460192`/`0x45fc3b`/`0x46d630`/`0x48abf0` 是 **th11.exe 的地址**。
所以这套 x86 差分对照**在当前 fork 里既跑不了、也不是为 th12 准备的**。

这反而说明了一件重要的事：**对 th12 而言，可用的对照不是 Unicorn 模拟器，
而是 `reference/th12-decomp/decomp_out/` 里已经反编译好的 C 代码**——
本轮解 280、400、406 用的正是它。也就是说，「先建对照、再写实现」这条纪律
在这个 fork 里的载体已经从「跑原版机器码」换成了「读反编译源码」。
这是一个方法上的更替，应当明确写下来，而不是继续假设 Unicorn 那套还在。

**结论**：`th12-*` 这 9 个文件是目前**唯一**能跑、也确实是 th12 语义的测试；
其余 124 个要么需要那个缺失的 wasm，要么带着 th11 的路径与地址。
把它们当成「122 个回归」会看错方向，当成「可以无视」也会丢掉真实信号——
下一步应当是把其中**不依赖 oracle 的 16 个文件**（`game-session`、
`stage-integration`、`restart-session`、`session-replays` 等）的数据档路径
改成读 `target.json`，让它们先跑起来，再逐个判断失败是 th11/th12 编号差异
还是真 bug。
## 11. 本轮：400/401 拿下，406 变成四关唯一的门

### 11.1 上一轮那个「还没定死的点」其实一句话就能定死

上一轮我说：400/401 的第二个 float 来自 `[ebx+0x174c]+4`，按 Δ=0x138 是
`script_owner`，但代码需要的是能取 `.instruction` 的东西，所以得先定死。

**答案在派发器序言里**（`th12.exe 0x4154d0`，37 字节）：

```asm
mov ebx, ecx            ; ecx (thiscall) = EnemyState*   → ebx = e
mov esi, [ebx + 0x174c] ; esi = e.script_owner (Enemy*)
mov eax, [esi + 4]      ; eax = script_owner->script.active (EclContext*)
mov edi, [eax + 4]      ; edi = ctx->instruction
movzx eax, word [edi+4] ; 取 opcode
...
mov [esp+0x34], ebx     ; 存 e
mov [esp+0x18], edi     ; 存 instruction
```

`esi` 就是 `script_owner`，`[esi+4]` 就是 `script_owner->script.active`。
而移植的 `EclOwner` 是 `{void* original_virtual_table; EclContext* active; ...}`
——**`active` 本来就是 `EclContext*`**。

把两条寄存器语义代回 400 的 case 体：

```asm
mov eax,[esi+4]        ; = script_owner->script.active   ← 同一个上下文
xor ecx,ecx ; call 0x468ec0 ; fstp [ebx+0xd0]
mov eax,[ebx+0x174c] ; mov eax,[eax+4]   ; 又是 script_owner->script.active
mov ecx,1 ; call 0x468ec0 ; fstp [ebx+0xd4]
```

**两次读的是同一个上下文**，也就是移植里传进来的 `c`。所谓「两个来源不同」
是我的误读——`[esi+4]` 和 `[[ebx+0x174c]+4]` 是同一个表达式。

顺带确认了参数取值惯例：`FUN_0041a9b0(i, raw)` 读
`ctx->instruction->references`（指令 `+8`）的第 `i` 位，置位才去
`FUN_00468fe0` 解引用——和移植里 `floating(i)` 的
`instruction->references & (1u<<i) ? resolve : raw` 完全一致。

### 11.2 这段转写移植里早就有了，只是编号是 th11 的

`EnemyStateCommands.cpp` 里本来就有：

```cpp
case 0x140:e.hitbox.x=f(0);e.hitbox.y=f(1);break;
case 0x141:e.collision_box.x=f(0);e.collision_box.y=f(1);break;
```

**th12 把这段搬到了 0x190/0x191**，并把 0x140/0x141 让给了另一族
（作用在 `ebx+0x68` / `ebx+0x9c` 那两个 Vec2，即 absolute/relative 位置）。
签名也印证：400/401 在 th12 是 `ff`，而 th11 的 0x190/0x191 分别是 `S` 和
放弹指令。

`0xd0`/`0xd8` 是 hitbox/collision_box 的原因：`Movement` 是 `0x34`，
四个 Movement 加两个 Vec2 正好让 hitbox 落在 `0xd0`、`animations` 落在 `0xe0`
——和 `static_assert(offsetof(EnemyState,emitters)==0x374)`、
`offsetof(health)==0x14f0` 一路对得上。

### 11.3 顺手拆掉两颗地雷

1. **`enemy_emitter_command` 的 `case 0x190:`**：th11 的「发射器重置」，
   里面是 `const i32 index=i(0);if(u32(index)>=8)__builtin_trap();`。
   th12 的 0x190 是 hitbox 设置，`i(0)` 是坐标——**和上一轮 402/403 被吞掉
   是同一个坑**。已从外层 case 表和内层 switch 里删除。
2. **`else if(op==0x191) enemy_fire_command(...)`**：这是 th11 的放弹路由。
   th12 的 0x191 是 collision_box 设置，这条路由在 401 不再被拒绝之后
   会**抢先吞掉正确的 case 体**。已删除。th12 真正的放弹指令编号尚未确定，
   所以 `enemy_fire_command` 现在是「没有路由」而不是「错误路由」——
   错误路由比没有更糟，因为它会静默跑错处理器而不是按名字拒绝。

### 11.4 证据

`node tools/th12-stage-probe.mjs 3000`（每关独立实例）：

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 7 | 跑满 3000 帧 | 跑满 3000 帧 |
| 3 | 121 帧 → 400 | 121 帧 → **406** |
| 4 | 101 帧 → 406 | 101 帧 → 406 |
| 5 | 121 帧 → 400 | 121 帧 → **406** |
| 6 | 121 帧 → 406 | 121 帧 → 406 |

400 从两关的拦路虎消失，**406 现在是 3/4/5/6 四关唯一的门**。

其余验证：`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、60 FPS，
舞台帧 365903 / 401027 字节（上一轮最大 376213），比上一轮更大。
`docs/th12/ecl-extended-opcodes.json`：`collision` 43→41，`implemented-collision` 3→5。

### 11.5 406 已经查清，但需要改结构体布局，留作下一轮

把 case 0x196 前后的整族一起读出来（`FUN_004154d0` L1243-1267）：

```c
case 0x196: _memset((void *)((int)param_1 + 0x1624),0,0x4c); break;
case 0x197: uVar26 = FUN_0041a900(0); uVar24 = FUN_0041a900(1);
            *(int *)((int)param_1 + (int)uVar26 * 4 + 0x1620) = (int)uVar24; break;
case 0x198: *(float *)((int)param_1 + 0x1670) = f(0);
            *(float **)((int)param_1 + 0x1674) = f(1); break;
case 0x19a: *(int *)((int)param_1 + 0x1620) = FUN_0041a900(0); break;
```

结构一目了然：`0x1620` 起是 **20 个 dword**（0x1620..0x166c），紧跟
**两个 float**（0x1670/0x1674）；406 清的正是 `0x1624` 起 19 个 dword。
这正好就是 **`EnemyDrop`**：`{i32 primary; i32 counts[19]; Vec2 spread;}`
——`primary` 在 0x1620、`counts[0..18]` 在 0x1624..0x166c、`spread` 在 0x1670。
旁证：th11 的 `drops` 在 0x1508，th11↔th12 在这一段正好差 0x20，而
`counts` 从 12 个涨到 19 个恰好多 0x1c（加对齐就是 0x20）。

**代价**：移植的 `EnemyDrop::counts` 是 `[12]`（th11），改成 `[19]` 会让
`drops` 之后的所有字段整体后移，`static_assert` 里的 `flags==0x1580`、
`script_owner==0x1614`、`sizeof(EnemyState)==0x163c`、`sizeof(Enemy)==0x2678`
都要跟着改。这是**一次结构体布局变更**，必须单独一轮做，并且要重新验证
全部 12 项测试、探针和浏览器——不能顺手塞进这一轮。下一轮第一件事就是它。
## 12. 本轮：406 拿下，顺带抓到一个「静默跑错处理器」的指令

### 12.1 布局变更不是猜的，是构造函数里量出来的

上一轮我是从「th11 的 drops 在 0x1508、这一段差 0x20」推出来的。这一轮直接从
th12 的敌人构造函数 `FUN_00413230`（`unaff_EDI` 就是 `this`，偏移以 dword 计）
里读到了硬证据：

```c
_memset(unaff_EDI + 0x410, 0, 0x1774);   /* byte 0x1040 起 0x1774 字节 = EnemyState */
_memset(unaff_EDI + 0x998, 0, 0x58);     /* byte 0x2660 起 0x58 字节   = 掉落表 */
...
unaff_EDI[0x9ac] = 0x42000000;           /* byte 0x26b0 = 0x1670 = 32.0f */
unaff_EDI[0x9ad] = 0x42000000;           /* byte 0x26b4 = 0x1674 = 32.0f */
unaff_EDI[0x444..0x447] = 0x41c00000;    /* byte 0x1110 = 0xd0..0xdc = 24.0f */
```

三件事同时被钉死：

1. **th12 的 `offsetof(Enemy,state)` 是 `0x1040`**（不是 th11 的 `0x103c`），
   所以 byte `0x2660` 就是 `EnemyState + 0x1620`。
2. 掉落表正好 **`0x58` 字节** = `primary(4) + counts[19](0x4c) + spread(8)`
   ——和 406 清 `0x4c` 字节、408 写 `0x1670/0x1674` 严丝合缝。
3. `spread` 两个 float 的初值都是 **32.0f**，和移植里
   `EnemyState::initialize` 的 `drops.spread={32,32}` 一致；
   而 `0xd0..0xdc` 默认 `24.0f`，正好印证上一轮 400/401 把
   `0xd0`/`0xd8` 认成 hitbox/collision_box。

### 12.2 结构体改了什么，以及没改什么

`EnemyDrop::counts` 从 `[12]` 改成 `[19]`，`sizeof` 从 `0x3c` 变 `0x58`。
`drops` 之后的字段整体后移 `0x1c`，四个 `static_assert` 同步更新为
`flags==0x159c`、`script_owner==0x1630`、`sizeof(EnemyState)==0x1658`、
`sizeof(Enemy)==0x2694`。编译器没有报错，说明预算的偏移是对的。

现在把话说清楚：**这四个值不再是「th12 的偏移」，而是移植自己的布局**。
`drops` 之前的字段（`emitters==0x374`、`emitter_offset==0x1414`、
`health==0x14f0`）仍然同时是 th11 和 th12 的，因为 `0x1414` 以下两者一致。
而 th12 真正的 `flags==0x16b8`、`script_owner==0x174c`、
`offsetof(Enemy,state)==0x1040` **没有对上**——因为移植保留了 th11 的
`EclOwner` 尺寸。这一处是已知未对齐，已写进注释，不再假装相等。

### 12.3 掉落族是重编号，而且 th12 去掉了 boss 类型重映射

移植在 th11 编号下本来就有这一族：

```cpp
case 0x146: for(auto& count:e.drops.counts)count=0;break;
case 0x147: {i32 type=drop_type(i(0),e.flags),count=i(1); ...}
case 0x148: {e.drops.spread=(f(0),f(1));}
case 0x14a: e.drops.primary=drop_type(i(0),e.flags);
```

th12 把它们整体上移 `0x50`（和 0x140/0x141→400/401、0x142/0x143→402/403
同一个位移），落在 **406/407/408/410**（`0x196/0x197/0x198/0x19a`）。
但 body 里 **没有 `drop_type`**：`FUN_004154d0` 的这四条直接调
`FUN_0041a900`，不再走 `flags&0x80000` 的 boss 映射。这个差异照实转写，
没有跟着 th11 保留。

唯一的主动偏离：0x197 在原版里**没有边界检查**，越界就是写坏紧邻的
`spread` 两个 float。移植加了 `if(u32(index)>=20)return -2;`——对原版会
「静默写坏内存」的输入，改成一个**带名字的拒绝**。这条偏离写在代码注释里。

### 12.4 顺手抓到：407 一直是在静默跑错处理器

`kTh12CollidingOpcodes` 里有 406 和 408，**却没有 407**。于是今天之前，
th12 的 407（存掉落表）会一路走到 `enemy_emitter_command`——它外层
case 表里有 `0x197`——然后执行 th11 的 `b.aim=i16(i(1))` 并 `return true`。
既不是拒绝，也不报错，就是**安静地改错字段**。

这比上一轮那种 trap 更危险，因为它不会留下任何痕迹。已一并修掉：
发射器的外层 case 表和内层 body 都不再声明 `0x196/0x197/0x198`。

### 12.5 证据

`node tools/th12-stage-probe.mjs 3000`（每关独立实例）：

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 7 | 跑满 3000 帧 | **跑满 3000 帧（未回归）** |
| 3 | 121 帧 → 406 | 121 帧 → **305** |
| 4 | 101 帧 → 406 | 101 帧 → **414** |
| 5 | 121 帧 → 406 | 121 帧 → **305** |
| 6 | 121 帧 → 406 | 121 帧 → **305** |

406 从四关全部消失，**新拦路虎是 305（3/5/6 三关）和 414（第 4 关）**，
两条都在 `kTh12CollidingOpcodes` 里。

其余：`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、61 FPS，
舞台帧 369545 / 398792 字节；opcode map `collision` 41→38、
`implemented-collision` 5→8。

### 12.6 下一轮

**305（`0x131`）优先**：一改能同时推三关。注意 305 在 `0x100..0x14x` 区间，
这一段的位移规律已经反复验证是 `+0x50`（0x140/0x141→400/401、
0x142/0x143→402/403、0x146..0x14a→406..410），所以 305 对应的 th12 指令
很可能就在 **`0x181`（385）** 附近——但要先用 `docs/th12/ecl-case-bodies.json`
和反编译确认，不要直接套。然后 414（`0x19e`），最后重跑探针。
## 13. 本轮：破了 +0x50 位移，414/421 落地；305 成了四关唯一的门
### 13.1 一个系统性发现：th12 把一整个指令家族上移了 0x50

把 th12 反编译里的 case 体和移植的 th11 处理器逐条对读，**连续十二条**都对上了
同一种关系：`th12 = th11 + 0x50`。

| th11 | th12 | 语义 | 证据 |
| --- | --- | --- | --- |
| 0x140 | 0x190 | 设 hitbox | body `f(0)/f(1) → +0xd0/+0xd4` |
| 0x141 | 0x191 | 设 collision box | body `→ +0xd8/+0xdc` |
| 0x142 | 0x192 | flags \|= arg | body `+0x16b8 \|= arg` |
| 0x143 | 0x193 | flags &= ~arg | body `+0x16b8 &= ~arg` |
| 0x146 | 0x196 | 清掉落表 | `memset(+0x1624,0,0x4c)` |
| 0x147 | 0x197 | 写掉落表 | `((i32*)(+0x1620))[arg0]=arg1` |
| 0x148 | 0x198 | 设 spread | `+0x1670/+0x1674 = f(0)/f(1)` |
| 0x14a | 0x19a | 设 primary | `+0x1620 = arg0` |
| **0x14e** | **0x19e** | **登记 interrupt** | 见 13.2 |
| **0x155** | **0x1a5** | **设 timeout 脚本** | `+0x2718+slot*0x10` |
| 0x131? | 0x181? | 未验证 | 见 13.4 |

0x14e/0x19e 这一对是这一轮最干净的证据。移植的 th11 版本是：

```cpp
case 0x14e:{const i32 time=i(2),health=i(1),slot=i(0);
  if(slot<0||slot>=8)return -2;
  auto& interrupt=e.interrupts[slot];interrupt.health=health;
  if(health>=0){interrupt.time=time;
    interrupt.health_script=interrupt.timeout_script=
      reinterpret_cast<const char*>(c.instruction)+32;}break;}
```

th12 的 0x19e：

```c
FUN_0041a900(2); uVar26 = FUN_0041a900(1); uVar24 = FUN_0041a900(0);
iVar10 = *(int *)((int)param_1 + 0x174c);              /* script_owner */
*(int *)((int)uVar24 * 0x10 + 0x270c + iVar10) = (int)uVar26;
if (-1 < (int)uVar26) FUN_0041a680(local_314 + 8,iVar10);
```

形状完全一致：读三个 int 参数、slot=arg0、把 arg1 落到 slot 的首个 dword、
**当 arg1 >= 0** 时才用 `指令 + 0x20` 去装脚本名（`local_314` 是 ECL 指令指针，
`+8` 是它的 `references`，而移植里写成 `instruction+32`——同一个位置）。
三条相邻指令 0x196/0x197/0x198 上一轮已经用同样的方式确认过，所以这不是巧合。

`0x155` 同理：th12 的 0x1a5 写 `+0x2718 + slot*0x10`，正好是 slot 的
`timeout_script` 字段，移植的 0x155 写的也是这个字段。

### 13.2 一个必须说清楚的陷阱：34 条「已有处理器」里有大量假的

我先跑了一个看起来很美的统计：`kTh12CollidingOpcodes` 里 39 条被拒的指令，
**有 34 条在自己的编号上已经有 `case` 了**。看起来只要把它们从拒绝名单里放出来
就能白捡一大片进度。

**但这是假象，我没有那么做。** 因为位移的存在意味着移植里同时存在
`X` 和 `X+0x50` 两套处理器：

| X | X+0x50 | 性质 |
| --- | --- | --- |
| 0x142/0x143 | 0x192/0x193 | th12 用后者，前者是**残留的 th11 处理器** |
| 0x144/0x145 | 0x194/0x195 | 同上 |
| 0x156..0x171 | 0x1a6..0x1c1 | 同上，一整片 |

也就是说「有 case」既不等于「是 th12 的处理器」，也不等于「语义对」。
一个具体的反例：th12 的 0x194 是 `flags |= 0x10000`，移植的 0x194 是
`flags |= 0x2000`——**结构一样、常量不同**。这种差异如果被「放进拒绝名单」
的操作盖过去，就会变成静默的保真度错误，正是上一轮抓到的那一类。

所以这一轮只放行了两条我**逐字节对读过 body** 的：414 和 421。

### 13.3 两条放行的结果：四关合流到一个门

`node tools/th12-stage-probe.mjs 3000`：

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 7 | 跑满 3000 帧 | 跑满 3000 帧 |
| 3 | 121 帧 → 305 | 121 帧 → 305 |
| 4 | 101 帧 → **414** | 101 帧 → **305** |
| 5 | 121 帧 → 305 | 121 帧 → 305 |
| 6 | 121 帧 → 305 | 121 帧 → 305 |

第 4 关从 414 推进到 305，**七个关卡里的四个（3/4/5/6）现在卡在同一条指令 305 上**。
opcode map：`collision` 38→36，`implemented-collision` 8→10。

其余：`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、61 FPS，
舞台帧 365369 / 404616 字节。

### 13.4 305 为什么不能靠重编号解决

th12 的 0x131 和移植的 0x131 **不是同一条指令**，它们的形状差得远：

* 移植的 0x131/0x132 是**位置曲线**：读 `i(0)` 为时长、`f(1)..f(6)` 为目标点、
  起止切线，共 7 个参数，作用在两个两个的 `Vec3Interpolator` 上。
* th12 的 0x131/0x133/0x149/0x14b 共用一段**角度插值**：只读 `i(0)`、`i(1)`、
  `f(2)`、`f(3)` 四个参数，作用在 `param_1+0x68`/`+0x9c` 这两个 Movement 上，
  并且带 -999999.0 的「保持当前值」哨兵、`arg1==7` 的特例，以及
  `flags & 0x40000` 时 ±90° 的分支——那个分支还会去读**上一条指令的 opcode**
  （`*(short*)(local_314+1)`）来决定是否补偿。

已确认的字段线索（留给下一轮，不要再猜）：

* `param_1+0x324` 与 `param_1+0x360` 是**一对 absolute/relative**，两者相差
  `0x3c`，正好是 `Vec2Interpolator` 的步长；`piVar9[0xd]`/`[0xe]` 就是这对结构
  `+0x34`/`+0x38` 的两个 dword。
* `FUN_00402520` 和 `FUN_00454b80` 都写 `+0x324 = 0x3f800000`（**1.0f**），
  所以这两个字段里至少有一个是浮点且默认 1.0。
* 但它**没有**落在移植现有布局的任何一个 `Vec2Interpolator` 基址上
  （移植是 0x20c/0x284/0x2fc，步长 0x3c 的成对结构），说明 th12 这一段插值器
  的基址与移植不同。**下一步要先用构造函数把这个区段量出来，再转写。**

### 13.5 下一轮

1. **305（`0x131`）是唯一值得先做的目标**：一条指令解锁四关。
   先量 th12 插值器区段的真实基址，再照抄角度插值。
2. 把 13.2 那 34 条候选做成**可核对清单**：每条拿
   `docs/th12/ecl-case-bodies.json` 的 case 体去对移植的实现，相同的才放行。
   0x194/0x195 的常量差异说明**不能批量放行**。
## 14. 本轮：量出 th12 的插值器区段，305 落地，五关再进一步

### 14.1 用反编译自己的 memset 定死了插值器区段

上一轮我说 `param_1+0x324`/`+0x360` 是一对 `Vec2Interpolator`，但**它落在移植
布局的哪个基址上不确定**。这一轮从两条互不相干的证据把它量死了。

**证据一：字段偏移完全对上。** 移植的

```cpp
template<class T,u32 N> struct Interpolator {
    T start[N],end[N],initial_tangent[N],final_tangent[N];
    Timer timer; i32 duration; InterpolationMode mode;
};
```

对 `N=2` 就是 `start@0x00, end@0x08, initial_tangent@0x10, final_tangent@0x18,
timer@0x20, duration@0x34, mode@0x38`。而 th12 的 0x131 写的是：

```c
piVar9[0xd] = arg0;      piVar9[4] = DAT_004ce8dc;  piVar9[5] = DAT_004ce8e0;
*piVar9 = local_2ec;     piVar9[6] = DAT_004ce8dc;  piVar9[7] = DAT_004ce8e0;
piVar9[2] = local_310;   piVar9[1] = local_2e8;     piVar9[3] = local_30c;
```

`[0xd]`=duration、`[4..7]`=两对切线、`[0]`=start.angle、`[1]`=start.speed、
`[2]`=end.angle、`[3]`=end.speed——**逐字段对上**。而 `piVar9[0xe]`=mode 那边
`arg1 == 7` 的特例，正好是移植枚举里的 `InterpolationMode::Velocity = 7`。

**证据二：发射器基址。** 派发器自己写着

```c
_memset((void *)((int)param_1 + iVar10 * 0x214 + 0x48c),0,0x214);
```

步长 0x214 是发射器步长，基址 **0x48c**——正是移植的 `emitters==0x374` **加
0x118**。于是整段都对齐了：

| 字段 | 移植（th11） | th12 | 差异 |
| --- | --- | --- | --- |
| absolute_position | 0x174 | — | |
| absolute_angle | 0x20c | **0x324** | +0x118 |
| relative_angle | 0x248 | **0x360** | +0x118 |
| emitters | 0x374 | **0x48c** | +0x118 ✓ 独立验证 |

所以 305 里的 `param_1+0x324` 就是 **`absolute_angle`**、`+0x360` 就是
**`relative_angle`**，不再是猜测。

### 14.2 305 的真身：th12 的 0x131/0x133/0x149/0x14b

它是「速度+角度插值」，和移植里 th11 的 `0x11d/0x11f` 是同一段逻辑，八处结构
逐条吻合：只读 `i(0)` 时长、`i(1)` 模式、`f(2)` 目标角度、`f(3)` 目标速度；
`-999999.0` 是「保持当前值」哨兵；`mode==7` 单独一支；参考角跨 π 时补 `2π`；
写 `start=(angle,speed)`、`end=(target angle,target speed)`；清 Movement 插值标志。

**一个值得记下来的解码**：th12 的镜像分支在反编译里长这样——

```c
local_31c = angle - 1.5707963705062866;
angle = FUN_004646e0(local_31c);
local_31c = 1.5707963705062866 - angle;
angle = FUN_004646e0(local_31c);
```

看起来像 cos/sin 复合，其实 `FUN_004646e0` 就是 `normalize_angle`：
`normalize(π/2 − normalize(angle − π/2))` 在不跨界时就是 **`π − angle`**，
也就是移植里现成的 `mirror()`。所以这一支不需要新写函数。

**三处常量不同，按 th12 转写**：镜像开关读 `e.flags & 0x40000`（th11 的孪生读
`0x8000`）；清标志用 `m.flags &= ~3`（th11 用 `~1`）。

### 14.3 顺带删掉一个「没有 th12 归宿」的残留处理器

移植原来的 `case 0x131:case 0x132:` 是**位置曲线**（`Vec3Interpolator`、
起止切线、7 个参数）。按本轮证据，th12 的 0x131 是角度插值，两者不是一条指令；
而 th11 的位置曲线按 `+0x50` 规律应该落到 th12 的 0x181，移植里没有这个 case。
所以这个 body 对 th12 而言**没有归宿**，直接删掉而不是留着——留着只会让它
继续静默处理 th12 的 0x131。删掉后第 1/2/7 关仍然跑满 3000 帧，证明它确实没被
那三关需要。

### 14.4 结果：五关全部推进，507 成为新的共同拦路虎

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 7 | 跑满 3000 帧 | **跑满 3000 帧（未回归）** |
| 3 | 121 帧 → 305 | **123 帧 → 507** |
| 4 | 101 帧 → 305 | **133 帧 → 507** |
| 5 | 121 帧 → 305 | **123 帧 → 507** |
| 6 | 121 帧 → 305 | **193 帧 → 507** |

四关全部越过 305，第 6 关多跑了 72 帧。opcode map：`collision` 36→34、
`implemented-collision` 10→12。

其余：`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、59 FPS，
舞台帧 368951 / 391898 字节。

### 14.5 下一轮

**507（`0x1fb`）**：th12.dat 里用了 239 次，现在卡住四关。反编译里
`case 0x1fb:` 的头部是 `uVar26 = FUN_0041a900(0); uVar24 = FUN_0041a900(1);`，
和它相邻的 0x1f5..0x1ff 是一整片尚未转写的家族，可以一次性对读。
注意这一片不在 0x140..0x1c1 的 `+0x50` 位移区内，**不要套用那个规律**。
## 15. 本轮：修正上一轮的一个错误结论；发射器家族落地，507 拿下

### 15.1 先纠正我自己：上一轮「414/421 已经有处理器」是错的

上一轮我跑了一个枚举脚本，输出里写着：

```
0x14e (334) and 0x19e (414)   EnemyStateCommands.cpp
```

我据此认定「414 的处理器已经存在，而且 body 对得上」，就把 414/421 从拒绝名单里
放了出来。**这个结论是错的**，错在两点：

1. **脚本打印的是较小那条的文件名。** 那行 `EnemyStateCommands.cpp` 属于 334，
   414 的归属根本没打印出来。我读错了输出，没有复核。
2. **414 当时唯一的处理器是激光组** (`EnemyLaserCommands.cpp` 的
   `case 0x19e:case 0x19f:...:`)，而它的 body 第一句是：

   ```cpp
   auto* b=lasers.find(i(0));if(!b)return 0;
   ```

   敌人中断引用不到活着的激光时，它**返回成功什么都不做**。也就是说上一轮
   把 414 放出来之后，第 4 关越过 414 是**假进展**——中断根本没有登记。

这一轮把它改对了：`0x19e`/`0x1a5` 从激光组的 case 表和
`EnemyScript.cpp` 的激光路由区间
(`op>=0x19c&&op<=0x1a5` → 排除这两条) 里摘掉，然后在
`EnemyStateCommands.cpp` 里**照 th11 的孪生体（`0x14e`/`0x155`）写入真正的
实现**——这两段 body 是上一轮已经逐条对读过反编译的，语义没问题，问题只在
它们挂在了错误的编号上、又被激光组抢走。

复跑探针：结果仍是 522，但这次 414/421 **是真的执行了登记逻辑**，而不是
静默返回成功。

### 15.2 发射器家族的编号和字段全部对上了

th12 的发射器指令在 **0x1f6..0x1fc**，不是 th11 的 0x194..0x19b。判定依据是
两边发射器结构体都是 0x214 字节（th11 `0x374 + 8*0x214 = 0x1414 = emitter_offset`；
th12 派发器用基址 `0x48c`、同样 0x214 步长），所以**字段偏移可以一一对搬**：

| 字段 | 偏移 | th12 写入它的 case |
| --- | --- | --- |
| sprite / color | +0x00 / +0x02 | **0x1f6** |
| angle / spread | +0x10 / +0x14 | 0x1f8 |
| speed / slow_speed | +0x18 / +0x1c | **0x1f9** |
| count / layers | +0x1f8 / +0x1fa | 0x1f6? 否——见下 |
| aim | +0x1fc | **0x1fb** |
| flags | +0x200 | |
| fire_sound / transform_sound | +0x204 / +0x208 | **0x1fc** |

`emitter_offset` 也印证了上一轮量出的 Δ=0x118：th12 的 0x1f7 写
`param_1 + i*0xc + 0x152c`，而 0x152c = th11 的 0x1414 + 0x118。

本轮落地了五条**逐字段核对过**的：0x1f6（sprite/color）、0x1f7
（`emitter_offset`）、0x1f9（speed/slow_speed）、0x1fb（**aim，就是 507**）、
0x1fc（fire/transform sound）。其中 **507 就是卡住四关的那条**：
`*(short*)(param_1 + i*0x214 + 0x688) = arg1`，0x688-0x48c = 0x1fc = `aim`。

### 15.3 顺带找到 th12 真正的放弹指令：501，不是 0x191

th12 的 `case 0x1f5:` 开头是：

```c
if (*(float *)(param_1 + iVar10 * 0xc + 0x1594) <= 0.9) {
  fVar15 = *(float *)(param_1 + 0x34) + *(float *)(param_1 + iVar10 * 0xc + 0x152c);
  fVar2  = *(float *)(param_1 + iVar10 * 0xc + 0x1530) + *(float *)(param_1 + 0x38);
```

`+0x1594` 是 `emitter_origin[i].z`（0x158c + 8），`+0x152c`/`+0x1530` 是
`emitter_offset[i].x/.y`，`+0x34`/`+0x38` 是 `current.position.x/.y`。这和移植里
现成的 `enemy_fire_command` **一字不差**：

```cpp
if(origin.z<=.9){const auto& p=e.current.position;
  emitter.position={offset.x+p.x, offset.y+p.y, offset.z+p.z};}
```

所以 **th12 的放弹编号是 501（`0x1f5`）**，而那个函数至今在断言
`opcode!=0x191`、并且因为两轮前删掉了 0x191 路由而没有调用者。
本轮没有动它——需要先把 0x1f5 的完整 body 读完（不止开头六行）再接线，
不能只凭前缀断言就改守卫。

### 15.4 结果

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 7 | 跑满 3000 帧 | 跑满 3000 帧 |
| 3 | 123 帧 → 507 | 123 帧 → **522** |
| 4 | 133 帧 → 507 | 133 帧 → **522** |
| 5 | 123 帧 → 507 | 123 帧 → **522** |
| 6 | 193 帧 → 507 | 193 帧 → **522** |

507 从四关消失，新的共同拦路虎是 **522（`0x20a`）**。帧数没变是因为 507 与 522
出现在同一帧的指令流里，清掉前者只是让执行继续走到了后者。

其余：`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、60 FPS，
舞台帧 355885 / 419816 字节。

**重新数了一遍**（上一轮那个脚本有打印 bug）：拒绝名单 34 条里 31 条在自己编号
上有 case，但绝大多数是 **th11 编号的残留**（比如 404/405/409/422..427/435..439
全是发射器文件里 th11 编号的那一套）。所以结论不变：**「有 case」不能作为放行
依据**。

### 15.5 下一轮

1. **522（`0x20a`）**：反编译开头是 `uVar26 = FUN_0041a900(0); if (DAT_004b0ca8 == 0) { uVar12 = 1;`，
   带全局状态分支，先读完整个 body 再转写。
2. **把 501 接上**：读完 `case 0x1f5` 全文，然后改 `enemy_fire_command` 的
   守卫（`0x191`→`0x1f5`）并在 `command()` 里路由。这是 325 次使用量的大件。
## 16. 本轮：接上 501（真正的放弹），发射器家族连下四城，五关大幅推进

### 16.1 501 就是 th12 的放弹指令，body 与移植函数逐行相同

上一轮只是从开头六行猜到 th12 的放弹编号是 501。这一轮读完了 `case 0x1f5` 全文
（反编译 1659-1687 行），结论坐实——它就是移植里 `enemy_fire_command` 的**逐行**
对应：

| th12 | 移植 |
| --- | --- |
| `if (origin.z <= 0.9)` | `if(origin.z<=.9)` |
| `current.position.x/y/z + emitter_offset[i].x/y/z` | `offset.x+p.x, offset.y+p.y, offset.z+p.z` |
| else 分支 `origin + offset`，**z 强制 0** | `{origin.x+offset.x, origin.y+offset.y, 0}` |
| `DAT_004b43c8+0x60 = *(param_1+0x16c8)`；开火；再置 0 | `exclusion_squared=e.exclusion_distance`；fire；置 0 |

`param_1+0x16c8` 是 th11 `0x1590` 加上那段 0x138 位移，即
**`exclusion_distance`**（顺带纠正：我早先把 0x16c8 猜成中断表，那是错的）。

**一处有意的保真改动**：th12 的 case 以无条件的 `break;` 结束，开火调用的返回值
被丢弃；移植原来的 `return ok?0:-2` 会在开火失败时中止脚本，而原作会照常继续。
已按原作改成 `return 0`。

于是守卫从 `opcode!=0x191` 改成 `opcode!=0x1f5`，并在 `command()` 里把 0x1f5 接回
（上一轮删掉 0x191 路由是对的，这一轮只是在**正确的编号**上接回来）。

### 16.2 521 / 522 是 th11 的 0x1b3 / 0x1b4 整体 +0x56

th12 的 `0x20a`（**522**，上一轮的共同拦路虎）读 arg0 当发射器下标，然后按全局
`DAT_004b0ca8` 选参数下标：0→1、1→2、2→3、其余→4，写入 `+0x684`；第二组
5/6/7/8 写入 `+0x686`。减掉发射器基址 0x48c 就是 `count`(+0x1f8) 与
`layers`(+0x1fa)。这和移植里现成的 `case 0x1b4`
（`arg=难度?1:2:3:4; b.count=i16(i(arg)); b.layers=i16(i(arg+4))`）**完全一致**。

孪生的 `0x209`（**521**）同理：写 `+0x4a4`/`+0x4a8` = `speed`/`slow_speed`，
参数下标同样 1..4 / 5..8 —— 就是移植的 `case 0x1b3`。

两条都按 th12 编号新增（th11 的 0x1b3/0x1b4 仍在外面那句话里，但对 th12 数据
不可达，因为两条都在拒绝名单里）。

### 16.3 504（0x1f8）：一个走出数组的写入

`case 0x1f8` 先写 `emitter+0x10`（`angle`），第二笔却是
`((i*3 + 0x54c) * 4)`，即 `i*0xc + 0x1530` —— 步长是 0xc 而不是发射器的 0x214，
所以它写的是 **`emitter_offset[i].y`**，不是 th11 那条的 `spread`(+0x14)。
反汇编在这里没有歧义（乘法因子是 3 再乘 4，不是 0x214），所以照实转写，并在代码
注释里标明这条不是 th11 的 0x194。

### 16.4 509（0x1fd）：与移植旧有的 0x199 逐字段相同

`case 0x1fd` 取 emitter[arg0]、按 arg1*0x18 步进到变换项，写六个字段。减掉基址
0x48c 后偏移分别是 0x38/0x34/0x2c/0x30/0x28/0x24，也就是
`transforms[slot]` 的 +0x14/+0x10/+0x08/+0x0c/+0x04/+0x00 —— 正好是移植
`BulletTransform{float a,b; i32 c,d; u32 opcode; i32 concurrent;}` 的
`concurrent/opcode/c/d/b/a`。写法和移植现成的 `case 0x199` **一字不差**。

### 16.5 结果：清掉 509 之后局面豁然打开

| 关卡 | 第 14 轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 7 | 跑满 3000 帧 | 跑满 3000 帧 |
| 3 | 123 帧 → 522 | **153 帧 → 435** |
| 4 | 133 帧 → 522 | 133 帧 → **435** |
| 5 | 123 帧 → 522 | **461 帧 → 454** |
| 6 | 193 帧 → 522 | **621 帧 → 454** |

第 5 关帧数翻了近四倍，第 6 关翻了三倍。原因是这一批发射器指令（521/522 选
弹幕数量层数、504/509 设角度与变换）本来就是弹幕生成的前置条件，前面一直被挡住，
现在才真正开始放弹。

本轮新增：0x1f8(504)、0x1fd(509)、0x209(521)、0x20a(522)，加上接通 0x1f5(501)。

其余：`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、60 FPS。

### 16.6 工具上的一处短板

`th12-opcode-map.mjs` 的判定只在**拒绝名单**内区分
`collision`/`implemented-collision`，非拒绝的 `todo` 项即使实现了也仍然显示
`todo`。所以本轮这四条在 map 上**看不出来**——进度只能靠关卡探针佐证。
下一轮给 map 增加一个独立的 `hasHandler` 字段（只作信息展示，不改判定，
因为「有 case」本来就不能当放行依据）。

### 16.7 下一轮

1. **435（`0x1b3`，在拒绝名单里）与 454（`0x1c6`）**：现在分别卡住第 3/4 关和第
   5/6 关。435 是拒绝项，要先对读 th12 的 `case 0x1b3` body 再决定放行还是另派。
2. **剩余发射器家族**：`0x1fa`(506)、`0x1fe`、`0x1ff`(511)、`0x200..0x208`，
   其中 `0x1ff` 看起来是「复制发射器」，对应移植的 `0x19b`。
## 17. 本轮：435 拿下、454 转为「有名字的缺口」，四关全部突破 700 帧

### 17.1 506 / 511

- **506（`0x1fa`）**：共享尾 `LAB_004180d4` 把 `i16(arg1)` 写进 `emitter+0x684`
  （`count`,+0x1f8）、`i16(arg[2])` 写进 `+0x686`（`layers`,+0x1fa）。就是移植
  早先那条 `0x196` 的写法。
- **511（`0x1ff`）**：从 `emitter[arg1]` 向 `emitter[arg0]` 拷 **0x85 个 dword**
  （0x214 字节），再经 `LAB_004174d7`（`a=b; a[1]=b[1]; a[2]=b[2]`）拷
  `emitter_offset`(0x152c) 与 `emitter_origin`(0x158c) 各三个 float。

  **读这条时发现移植里的一个缺陷**：移植的 `case 0x19b`（th11 的复制发射器）
  **只拷了发射器本体，漏了 offset 与 origin**，所以 th11 的复制会悄悄保留旧偏移。
  311 目前不参与（0x19b 在拒绝名单里，对 th12 不可达），但这个 bug 是真实存在的，
  本轮把它**写进注释保持可见**，而不是顺手改掉——因为 0x19b 是 th11 的编号。

### 17.2 435（`0x1b3`）：先看清共享标签属于谁，再动手

上一轮它卡住第 3/4 关，我一度以为要逆向一大片共享代码。这一轮把
`switchD_00417ba4_caseD_1` / `_caseD_3` 的归属查清了——**它们属于 case 0x1b0 和
case 0x1b1**，0x1b3 只是向后跳进去复用：

```c
case 0x1b0: if (rank > 0x1ff) *ref = arg2; else *ref = arg0;
case 0x1b1: rank>599→arg4; >199→arg3; >-201→arg2; >-401→arg1; else→arg0;
case 0x1b2: *ref = ((arg2-arg1)*(rank+1024))>>11 + arg1;
case 0x1b3: 按难度选 arg1/arg2/arg3/arg4
```

关键在 `caseD_3`（0x1b1 的 `rank>599` 分支）末尾那个 `break`——0x1b3 跳进去执行完
`*ref = arg4` 就 **break 出整个 switch**，**不会**继续往下走到 0x1b1 的 rank 阶梯。
所以 0x1b3 确实只是一个干净的难度选择。`FUN_0041a910` 就是 ECL 整数引用解析器
（用 `instruction->[8]` bit0 判定引用、`instruction->[0x10]` 作数据段下标），
对应移植现成的 `c.integer_reference(0, g)`。

本轮落地 0x1b0 / 0x1b1 / 0x1b3，并把 435 从拒绝名单里放出来。
`0x1b2` 暂不转写：它的 `((x>>0x1f & 0x7ff) + x) >> 0xb` 是有符号除 2048 的
特定取整，要逐位搬对再上，不能凭感觉。

### 17.3 454（`0x1c6`）：从「硬停」改成「有名字的缺口」

435 清掉之后，**四关全部收敛到同一条指令 454**。读完 `case 0x1c6` 全文与它的
调用链：

```c
case 0x1c6: FUN_00421740(); break;

FUN_00421740:  if (DAT_004cee40 != 8 && (DAT_004b0ce0 & 0x20) == 0)
                   FUN_004615a0(NULL, *(void**)(DAT_004b43e4 + 0x6ce4), &local_4, 0, 0);
```

`FUN_004615a0` **有 117 个调用者**：它递增计数、经 `FUN_004621c0` 从一个池里取对象、
写 id(+0x20)、标志(+0x480) 与坐标(+0x430/+0x434/+0x438)——是**引擎侧的视觉特效实例**。
而移植里**根本没有特效系统**：`cpp/game` 下不存在任何 Effect / Particle 类型，
`FUN_00421740` 在全 exe 里也只有这一个调用者。

于是把它从「硬停」改成**有名字的 no-op**：敌人脚本继续跑，唯一丢失的是引擎侧
视觉。这不是「静默成功」——它带着完整证据被记录在案（本节），是第 3/4/5/6 关此前
唯一的共同拦路虎。这个取舍写进了代码注释，也写在这里。

### 17.4 结果：四关一起突破 700 帧

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 7 | 跑满 3000 帧 | 跑满 3000 帧 |
| 3 | 153 帧 → 435 | **941 帧 → 416** |
| 4 | 133 帧 → 435 | **731 帧 → 403** |
| 5 | 461 帧 → 454 | **721 帧 → 524** |
| 6 | 621 帧 → 454 | **940 帧 → 416** |

四关全部越过 700 帧（上一轮最深才 621），而且**各自停在不同指令上**——说明共同
拦路虎已经消失，四条舞台线开始各自展开内容。

opcode map：`collision` 34→33、`implemented-collision` 12→13。

其余：`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、59 FPS。

### 17.5 下一轮

新的三个拦路虎，按「好办程度」排：

1. **524（`0x20c`）**：`*(float*)(param_1 + i*0x214 + 0x4ac) = f(1)`，
   `0x4ac-0x48c = 0x20` = 发射器的 **`radius`**，一行就能转写。
2. **403（`0x193`）**：它早就实现过（flags/可见性族），却仍被拒——说明是**返回 -2**
   而不是没有 case，要查是哪个分支把它挡住的。**这是本轮最值得先查的一条**，
   因为「已实现却仍报错」往往意味着守卫条件写错了。
3. **416（`0x1a0`）**：在拒绝名单里，body 涉及位置计算，需要完整对读后再放行。
## 18. 本轮：403 的真因、524 一行、以及一个「实现了其实没生效」的潜伏 bug

### 18.1 403（`0x193`）为什么「已实现却仍被拒」

上一轮我留了个问题：403 早就实现过，却仍然报错。答案在 `EnemyStateCommands.cpp`
里的一句话：

```cpp
// 如果任何槽位非零就大声拒绝
for(u32 id:slots)if(id)return -2;
```

当初的依据是「第 1 关跑 402 时十六个槽全是 0」。**这个观测是对的，但结论只对第 1
关成立**：第 4 关一旦给某个动画槽赋值，这个守卫就立刻开火，把整关打死。

读 th12 的 body 才知道正确处理是什么：

```c
case 0x192: flags |= arg0;  if (flags & 0x20) { loop 16x FUN_00461d80(); }
case 0x193: flags &= ~arg0; if (!(flags & 0x20)) { loop 16x FUN_00461d40(); }
```

`FUN_00461d80` 把管理器对象（`FUN_00461920` 按 id 查到）`+0x47c` 的 **bit 1 清掉**，
`FUN_00461d40` 置上，并顺带处理 `[0x11f]` 与 `[5]` 链表。**bit 1 of +0x47c 正是移植
里 th11 `0x142/0x143` 通过 `w.animation_visibility` 驱动的那个可见性位**，而且代码
里已经算好的 `visible` **本来就是正确的实参**：0x192 清位→传 `false`，0x193 置位→
传 `true`。循环次数在反编译里就是字面的 `0x10`。

于是把「拒绝」换成真正的回调路径。**这次修正的意义**：`return -2` 是「大声失败」，
比静默好；但当它把整关拦住时，就该去补上真正的语义，而不是让它一直拦着。

### 18.2 524（`0x20c`）

`*(float*)(param_1 + i*0x214 + 0x4ac) = f(1)`，`0x4ac - 0x48c = 0x20` = 发射器的
**`radius`**。一行。

### 18.3 潜伏 bug：上一轮的 506/511 其实没生效

改完 524 后探针**仍然报 524**，这不合理。查下去发现发射器文件的外层闸门是：

```
...case 0x1f9:case 0x1fb:case 0x1fd:case 0x1fc:case 0x209:case 0x20a:break;
```

**`0x1fa`、`0x1ff`、`0x20c` 都不在里面。**外层闸门先于内层 switch 执行，
`default:return false;`，所以这三条永远走不到内层的实现。也就是说：

> **上一轮我在文档里写的「506 / 511 已落地」是错的——它们当时一行都没生效。**

根因是我用 `.Replace()` 做字符串替换，`Replace` 在**找不到目标时不报错**，
链条里任何一环静默失配就悄悄丢掉了。这类 bug 只能靠「实现」与「可达」分开核对
才能发现。

修法不是再手写一遍名单，而是**让脚本从内层 switch 自动重建外层闸门**：
解析内层所有 `case`，并上特殊分支的 `if(op==0x…)`，排序后生成闸门。重建后
内层 27 条全部在闸门里，脚本也直接打印出「旧闸门缺了哪几条」——
`missing from old gate: 0x1fa 0x1ff 0x20c`，把这次事故量化了。

### 18.4 结果

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 7 | 跑满 3000 帧 | 跑满 3000 帧 |
| 3 | 941 帧 → 416 | 941 帧 → 416 |
| 4 | 731 帧 → 403 | **732 帧 → 448** |
| 5 | 721 帧 → 524 | **726 帧 → 448** |
| 6 | 940 帧 → 416 | 940 帧 → 416 |

其余：`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、60 FPS，
舞台帧 368503 / 422793 字节。

### 18.5 下一轮

1. **先补一道工具闸**：本轮这类「内层有 case、外层没放行」的错，应该由
   `tools/th12-dispatch-gate.mjs --check` 自动查——对每个命令文件比对内层 case 集合
   与外层闸门集合，缺一条就非零退出。**这条比再多写两个 opcode 更值钱**，
   因为它防的是「以为做了、其实没做」。
2. **416（`0x1a0`）**：卡住第 3/6 关，在拒绝名单里，需完整对读位置计算后放行。
3. **448（`0x1c0`）**：卡住第 4/5 关，在拒绝名单里，且落在激光路由区间
   `0x1be..0x1c0` 内。
## 19. 本轮：补上防「以为做了其实没做」的闸门，外加 436

### 19.1 新增闸门 `tools/th12-dispatch-gate.mjs`

上一轮那个 bug（内层写了 case、外层闸门没放行，于是实现一行都没生效，而文档却
写了「已落地」）值得一个专门的工具。本轮补上，它查**两类**同一性质的错：

1. **闸门漏放行**：发射器文件用
   `switch(op){case …:break;default:return false;}` 作外层闸门，真正的实现挂在紧随
   其后的内层 `switch(op)` 上。工具按**结构**识别闸门（只含 case 标签、`break;` 和
   `default:return false;`），与紧随的实现 switch 比对标签集合，缺一条就报。
   闸门与实现之间用 `if(op==0x…)` 接的特殊分支（发射器里 0x19b / 0x1ff 那种
   双下标复制）也算「已放行」。
2. **路由漏覆盖**：`EnemyScript.cpp::command()` 用 opcode 条件把激光族和动画族
   分派到各自文件。**没被条件覆盖的 case 和没被闸门放行的 case 一样是死的**，
   只是错误位置高了一层。工具把这两条条件解析出来，在 opcode 全域上求值，再和
   文件里的 `case` 集合比对。求值时**不认识的项（如 `commands.animations` 这类
   指针守卫）按「不覆盖」处理**——把它当成覆盖一切正好会掩盖这个工具要抓的漂移。

**两处都做了反证**（这比「跑通」更有说服力）：

- 把 `case 0x1fa` 从闸门里摘掉 → `UNREACHABLE … missing from gate: 0x1fa`，
  **exit=1**；还原后 exit=0。
- 把激光路由的 `0x1be..0x1c0` 改成 `0x1be..0x1bf` →
  `UNREACHABLE EnemyLaserCommands.cpp: 1 of 19 cases are not routed`，
  指出 `0x1c0`，**exit=1**；还原后 exit=0。

当前状态：闸门 1 对、激光 19/19 可路由、动画文件 0/0（该文件没有 `switch(op)`，
所以这条检查目前是空的——`0/0` 会被打印出来，不会假装通过）。

### 19.2 436（`0x1b4`）：0x1b3 的浮点孪生

`case 0x1b4` 用同样的难度选择器（0→arg1、1→arg2、2→arg3、其余→arg4），但取的是
**浮点实参**，且写入路径是：

```c
fVar23 = FUN_00468ec0(<难度选中的下标>);      // 浮点实参
pfVar11 = FUN_004690b0(0, ctx);              // 浮点引用取址
goto LAB_00419629;                           // *pfVar11 = (float)pfVar18;
```

`FUN_004690b0` 就是**浮点引用取址器**（先测掩码位，再取 `ctx+0x10+下标*4`），与整数
版 `FUN_0041a910` 同形；`LAB_00419629` 就是 `*pfVar11 = (float)pfVar18;`。
移植里 `float_reference` 与 `integer_reference` 并列存在，所以直接对应：

```cpp
case 0x1b4:{float* ref=c.float_reference(0,g);if(!ref)return -2;
    *ref=float(f(难度选中的下标));break;}
```

436 从拒绝名单释放。opcode map：`collision` 33→32、`implemented-collision` 13→14。

### 19.3 两个拦路虎的现状（下一轮的活）

- **416（`0x1a0`）**，卡第 3/6 关。body 很短：
  ```c
  uVar12 = *(undefined4 *)(param_1 + 0x34);   // current.position.x
  uVar26 = FUN_0041a900(0);
  FUN_00453e20(ecx, (int)(uVar26 >> 0x20), uVar12);
  ```
  参数是「一个浮点的位模式」+「当前 x 坐标」，但 `FUN_00453e20` 还没识别，**先不猜**。
- **448（`0x1c0`）**，卡第 4/5 关，在激光路由区间内：
  ```c
  switch (difficulty) { 0→i(0); 1→i(1); 2→i(2); else→i(3); }
  pfVar11 = ctx; pfVar18 = *pfVar11 - (float)value;
  goto LAB_00419629;                          // *pfVar11 = (float)pfVar18;
  ```
  即「按难度取一个整数实参、转 float，再从 `ctx` 指的那格浮点里减掉」。**卡点在
  `pfVar11 = ctx` 究竟指哪一格**——这需要先把 `FUN_0041a900` 在「引用型实参」下的
  返回值语义定清楚，而它同时也是 0x192/0x1b3 等一堆指令的取值来源，值得单独查一次。

### 19.4 结果与证据

关卡探针与上一轮相同（436 不在 416/448 之前被触达）：
第 3/6 关 → 416（941 / 940 帧），第 4/5 关 → 448（732 / 726 帧），
第 1/2/7 关跑满 3000 帧。

`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、60 FPS，
舞台帧 369713 / 400482 字节；本轮的闸门（含两处反证）exit=0。
## 20. 本轮：查清 `FUN_0041a900` 的语义，据此拿下 448，并让子弹系统的失败自己报出死因

### 20.1 `FUN_0041a900` / `FUN_00468e20` 到底返回什么

上一轮把「引用型实参下返回什么」列为最高优先级，因为它同时决定 448 和一批指令。
答案在 `FUN_00468e20`：

```c
iVar1 = ctx->instruction;                       // param_2 + 4
if ((1 << (index & 0x1f) & *(u16 *)(iVar1 + 8)) == 0) {
    param_3 = *(int *)(iVar1 + 0x10 + index * 4);          // 位为 0：普通值
} else {                                                    // 位为 1：引用
    iVar1 = *(int *)(iVar1 + 0x10 + index * 4);
    if (iVar1 >= 0) return CONCAT44(param_2, *(u32 *)(ctx->[0x100c] + iVar1 + 8 + ctx));
    if (iVar1 != -1) return (**(code **)(**(int **)(ctx + 0x1014) + 4))(iVar1);
    ...                                                     // -1：从栈上取，'f' 走 x87
}
```

**`instruction+8` 是指令的「哪些实参是引用」位掩码**：位为 0 → 该实参就是一个普通
值；位为 1 → 该实参是引用，其值作为下标进入数据段，函数返回**解析后的地址**
（高位 dword 放 `param_2`，即上下文指针）。这和移植里 `integer_argument` /
`integer_reference` 的分工完全一致——**移植的访问器契约是对的**。

### 20.2 448（`0x1c0`）：结论落在 `EclContext` 的第一个成员上

有了上面的语义，448 只剩一个问题：`pfVar11 = ctx` 指向哪一格。

```c
case 0x1c0:
  switch (difficulty) { 0→i(0); 1→i(1); 2→i(2); else→i(3); }
  pfVar11 = *(float **)(*(int *)(param_1 + 0x174c) + 4);   // = 活动 EclContext
  pfVar18 = *pfVar11 - (float)value;
  goto LAB_00419629;                                        // *pfVar11 = (float)pfVar18;
```

而移植里 `EclContext` 的第一个成员就是 **`float time`**（`EclContext.hpp:27`，并且有
`static_assert(offsetof(EclContext,owner)==0x1014)` 把布局钉住）。所以这就是
**`ctx->time -= value`**——一次脚本计时器调整。落地：

```cpp
case 0x1c0:c.time-=float(i(难度选中下标));break;
```

两处容易看错的地方记下来：**难度选择的实参下标是 0/1/2/3（从 0 起）**，与
0x1b3 / 0x1b4 的 1 起不同；实参是**整数**再转 float，不是浮点实参。

### 20.3 新闸门第一次真正发挥作用

删掉激光路由里的 `0x1c0` 之后，闸门立刻报：

```
UNREACHABLE EnemyLaserCommands.cpp: 1 of 19 cases are not routed by command()
  missing from routing: 0x1c0
```

也就是说**激光文件里有一个 `case 0x1c0`**——th11 的「激光消除循环」。th12 的 0x1c0
是上面那条计时器减法，编号撞了。这正是两轮前 414 那类陷阱的重演，只不过这次是
**工具先发现的，不是我事后回想的**。删掉该 case 后闸门回到 18/18 全绿。

### 20.4 结果：448 让第 5 关从 726 帧跳到 2340 帧

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 7 | 跑满 3000 帧 | 跑满 3000 帧 |
| 3 | 941 帧 → 416 | 941 帧 → 416 |
| 4 | 732 帧 → 448 | 732 帧 → **子弹系统失败** |
| 5 | 726 帧 → 448 | **2340 帧 → 513** |
| 6 | 940 帧 → 416 | 940 帧 → 416 |

第 5 关一举越过 2000 帧，第 4 关则换了失败方式——不再是「未实现的 opcode」，
而是**跑进了子弹系统**。

### 20.5 让子弹系统的失败报出死因

第 4 关的报文原本只有 `battle update failed: -1002`，而 `-1002` 只表示
`bullets.update()` 返回 false，它内部 12 处 `return -2;` 全被压成同一个
`last_error=6`——**这正是「失败必须说出原因」的反面**。于是：

1. 给 `BulletManager.cpp` 里 12 处 `return -2;` 各自编号（61..72），
   并让 `update()` 不再无条件覆盖（`if(last_error<60)last_error=6;`）。
2. `GameBattle.cpp` 改成 `last_error=-1000-bullets.last_error;`，把内部编号带出来。

再跑一次，第 4 关报 **`-1062` → `last_error=62` → `BulletManager.cpp:49`**：

```cpp
if(!appearance(b,e.sprite,e.color,false)){last_error=1;return -2;}
```

`appearance()` 在四种情况下返回 false，最短路径是
`u32(type)>=bullet_appearances.size()`——即**这一发子弹的类型下标超出了移植的
子弹外观表**（`BulletManager.cpp:24`，其次是 `color>=8` 且 `effect_mode==1`）。
**下一轮的活因此有了明确的名字：对照 th12 的子弹外观表长度，补上移植缺的表项。**

opcode map：`collision` 32→31、`implemented-collision` 14→15。
`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、60 FPS；
舞台帧 364265 / 395984 字节；5 个闸门 exit 0。
## 21. 本轮：把子弹外观表换成 th12 自己的（不是 th11 的），第 4 关翻倍

### 21.1 找到了 th12 真正的子弹外观表

上一轮的报错把「子弹外观表」点成了明确目标。在反编译里搜 `* 0xd0` 找到了它：
**`DAT_004af280`，步长 `0xd0`**——而 `0xd0` 正是移植里 `sizeof(BulletAppearance)`，
字段偏移也和移植的结构体逐一对上：

| 偏移 | 字段 | 依据 |
| --- | --- | --- |
| +0x00 | `script` | `*(int *)(&DAT_004af280 + sprite*0xd0) == 0x26` |
| +0x04 | `sprites[48]` | `*(short **)(&DAT_004af280 + type*0xd0)` |
| +0xc4 | `hitbox` | `&DAT_004af344 + type*0xd0` |
| +0xc8 | `group` | `&DAT_004af348 + type*0xd0` |
| +0xcc | `effect_mode` | `&DAT_004af34c + type*0xd0` |

**十八个反编译函数**都写成 `&DAT_004af280 + sprite * 0xd0`，所以这不是猜的。
表在 `.data` 里是静态的，直接从 `th12.exe` 读出来即可。

### 21.2 移植的表根本不是 th12 的

读出来的第一件事就说明问题——两边**脚本列完全不同**：

```
th11（移植现有 29 项）: 0,34,35,36,37,38,39,40,41,42,43,44,63,64,65,66,67,72,95,68,...
th12（exe 实测 31 项）: 35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,69,70,71,...
```

移植的表是**按 th11 的 ANM 布局手工重算出来的**：脚本列对不上，项数也只有 29，
少了 th12 的两项（索引 29 = 脚本 216、索引 30 = 脚本 233）。**第 4 关之所以报
`appearance()` 失败，就是因为这一发子弹的类型下标超过了 29 项的数组。**

### 21.3 新增生成器 `tools/th12-bullet-appearances.mjs`

不再手抄：生成器从 `th12.exe` 直接读表并生成 `BulletAppearance.cpp`，
支持 `--check`。它还带**反悔保护**——如果脚本列出现离谱值、或 `hitbox`/`effect_mode`
越界，就直接拒绝写文件（基底或步长错了的话，这三列会是噪声而不是 th12 那样的小整数）。
生成结果：31 项、脚本列 `35..51,69..75,98,99,161,75,163,215,216,233`。

### 21.4 结果：第 4 关 732 → 1502 帧

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 7 | 跑满 3000 帧 | 跑满 3000 帧 |
| 3 | 941 帧 → 416 | 941 帧 → 416 |
| 4 | 732 帧 → 外观表拒绝 | **1502 帧 → 内存越界崩溃** |
| 5 | 2340 帧 → 513 | 2340 帧 → 513 |
| 6 | 940 帧 → 416 | 940 帧 → 416 |

换了正确的表之后，第 4 关**帧数翻了一倍多**，并且换了死法：不再是「这张表里没有
这一项」，而是跑进子弹生命周期后**内存越界**。

### 21.5 顺手修掉的三处

1. **探针现在按关卡隔离崩溃**。以前一次 wasm trap 会终结整轮探针，把后面所有关卡
   的结果一起吞掉——这轮就真的发生过（第 4 关崩溃时，第 5/6/7 关全没报出来）。
   现在每关自己 catch，记成该关的结局 `crashed`，其余关卡照常跑完。这是这一轮
   能同时看到「第 4 关 1502 帧」和「第 5 关 2340 帧」的原因。
2. **补上三处未检查的 `bullet_appearances[...]` 下标**（`BulletManager.cpp` 的
   `sprite_callback`、`LaserInfinite.cpp`、`LaserLine.cpp`）。越界下标现在返回 -1，
   不再可能变成越界访问。
3. **th12 新增的 `effect_mode == 5`**（类型 29/30）以前会从 switch 里掉出去，
   把上一条子弹留在同一槽位里的 `cancel_effect` 当成本次的值用；现在显式拒绝。

### 21.6 下一轮

1. **第 4 关的内存越界**是现在的第一拦路虎。已确认 `AnmVm.cpp:16` 对精灵下标有边界
   检查、`BulletManager` 的 `draw_group` 也有，所以需要**拿到崩溃点本身**——
   当前 wasm 是 release 构建、没有 name section（已实测 `named functions: 0`），
   函数下标映射不出名字。**下一轮第一步应该是让构建保留调试信息或断言**，
   否则只能靠猜。
2. **`EnemyCallbacks.cpp` 里还有 th11 的脚本号**：它按
   `bullet_appearances[b.sprite].script == 0x22 / 0x40 / 0xbf` 分派，而 th12 的脚本列
   是 `35..51,69..75,98,99,161,75,163,215,...`，**一个都对不上**，于是这些回调静默
   不做任何事。这是和 414/0x1c0 同一类的编号撞车，应照着 th12 的真实脚本号改写。
## 22. 本轮：把「wasm 崩溃定位」从愿望变成能力，并修回两个死掉的通知回调

### 22.1 崩溃定位：拿到了名字，但还差最后一步

上一轮说下一轮第一步是「让构建保留调试信息」。查下来发现**构建脚本里早就有这个开关**
（`TH12_CORE_DEBUG=1`），只是探针一直用 stripped 产物跑：

```js
const debug=process.env.TH12_CORE_DEBUG==='1';
const flags=[..., debug?'-g':'-g0', ..., (debug?['-Wl,--no-gc-sections']:['-Wl,--strip-all'])];
```

本轮在 debug 分支上补了 `-Wl,--keep-section=name`，并给探针加了 `crashFrames`
（记录 `函数下标:偏移` 对）。实测结果：

- debug 产物带上了 **DWARF**：`.debug_abbrev / .debug_info / .debug_str / .debug_line /
  .debug_loc / .debug_ranges`（**没有 `name` section**——所以 `wasm-function[N]` 本身
  仍无名）。
- 但 **`llvm-objdump -d` 能从 DWARF 里还原出真实 C++ 函数名**，例如
  `0007437a <bm_appearance>:`。**名字是拿得到的**，只是要通过 objdump 而不是 V8 的栈。

**卡在哪**：V8 给的是 `wasm-function[127]:0x16a18` 这样的**下标 + 模块级偏移**，
objdump 打印的是**函数起始地址**，两者同一空间；但 wasm 里有 **1640 个已定义函数、
0 个导入函数**，而 objdump 只列出**有名字的 618 个**。用「618 个起始地址」去夹逼偏移，
落点会飘到很远的另一个具名函数上——本轮实测就是这样（十个栈帧全被映射到
`timer_advance`，显然不对）。

**下一轮的第一步已经写明了**：对 **stripped** 产物跑 `llvm-objdump -d`，让 objdump 把
全部 1640 个函数按顺序列成 `wasm-function[N]`，然后**直接用下标对下标**映射，
不再做地址夹逼。这一步不需要 DWARF，因此也不会再受「只有具名函数」的干扰。

### 22.2 修回两个「按 th11 脚本号分派」的死回调

`EnemyCallbacks.cpp` 里三个回调按**th11 的脚本号**判断该对哪些子弹生效。而 th12 的
外观表脚本列是 `35..51,69..75,98,99,161,75,163,215,216,233`——**`0x22`(34)、`0x40`(64)、
`0xbf`(191) 一个都不在里面**，所以这些回调一直是**静默的空转**。全文搜
`0xd0) == 0x` 只找到两个 th12 的比较点，正好对上两个回调：

| 回调 | th11 脚本号 | **th12 实测** | 依据（函数体逐条对上） |
| --- | --- | --- | --- |
| `attract` | `0x22` (34) | **`0x26` (38)** | `FUN_0041ae20`：先按 `integers[0]==1` 移动玩家，再对每发命中子弹 `b.speed = -e.floats[3]`、经 `FUN_0041c580` 重设速度、在 `e.floats[0]² * 0.25` 内取消——**与移植的 `attract` 逐条一致** |
| `spawn_from_bullets` | `0x40` (64) | **`0x47` (71)** | `FUN_0041aff0`：对每发命中子弹在**其位置**生成 `"MBossCard2_at2"` |

第三个回调 `bullet_emitter` 用的 `0xbf`(191) **在 th12 里找不到对应的比较点**
（全文只有那两处），所以本轮**不动它**，留作待查——不拿没有证据的值去替换。

**诚实说明**：这两处修好之后，探针的帧数与上一轮**完全相同**（第 4 关仍是 1502 帧崩溃）。
因为这两个回调在崩溃之前没有被触发。所以它们是**证据充分的潜在正确性修复**，
而不是本轮可见的推进——不应记成「第 4 关变好了」。

### 22.3 当前关卡状态（与上一轮相同）

| 关卡 | 帧数 | 结局 |
| --- | --- | --- |
| 1, 2, 7 | 3000 | 跑满预算 |
| 3 | 941 | ECL opcode 416 |
| 4 | 1502 | **内存越界崩溃**（待定位） |
| 5 | 2340 | ECL opcode 513 |
| 6 | 940 | ECL opcode 416 |

`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、60 FPS；
**6 个闸门** exit 0（新增的 `th12-bullet-appearances.mjs --check` 也在其中）。
## 23. 本轮：解开崩溃定位、修掉第 4 关的越界，并拿到「4.0f」这个铁证

### 23.1 上一轮为什么定位失败，以及正确的做法

上一轮把十个栈帧全映射到 `timer_advance`，是错的。原因这一轮查清了：
**objdump 给每个函数都输出一行头，但函数没有 DWARF 名字时头是 `<>:`**，
而我上一轮的抓取正则要求 `<(.+)>`（至少一个字符），**把这些空名头全丢了**，
只剩下 618 个具名函数。用「618 个起始地址」去夹逼偏移，自然乱飘。

正确的做法是**完全不做地址夹逼**：

1. objdump 按 **code section 顺序**输出函数头（实测 1641 行 = 1640 个已定义函数
   + 1 个 `<CODE>` 伪头）；
2. wasm 的 **export section 直接给出「名字 → 函数下标」**；
3. 用导出的名字对上它在头列表里的位置，就得到**下标→位置**的偏移；
   实测 **375 个导出**一致同意同一个偏移——这个投票非常稳。
4. 然后 `位置 = 下标 - 偏移`，直接索引头列表。

另外确认了**偏移量就是地址**：把 9 个故障地址拿去和**全部 1641 个函数**的地址区间
比对，**每一个都干净地落在某个函数区间内**（上一轮只拿具名函数比对才会失败）。

新增工具 `tools/th12-wasm-trap-map.mjs` 把这个流程固化下来，
并且**在函数没有名字时如实报「unnamed」**，不会编一个名字出来。

### 23.2 崩溃点：`EclStack::local` 没有边界检查

故障指令（直接从反汇编读出）是：

```
16a15: 41 08        i32.const 8
16a17: 6a           i32.add
16a18: 28 00 00     i32.load  0:p2align=0     <-- 这里越界
```

即 `load(base + index + 8)`。而移植里 `EclStack::data` 正好在 **EclContext+8**
（前面是 `float time` 与 `const EclInstruction* instruction`），于是指向的就是：

```cpp
template<class T>T local(i32 offset)const noexcept{T v;std::memcpy(&v,data+frame_base+offset,sizeof v);return v;}
```

**完全没有边界检查**。原版之所以安全，是因为它的 ECL 上下文**嵌在一块更大的分配里**，
读到邻近内存不会出事；而移植里 `data` 是真正的 4096 字节数组，越过它就是越界访问，
在 wasm 里直接 trap 掉整个会话。

### 23.3 修法：夹紧，但**必须可测量**，不能静默

单纯夹紧会变成「静默读到错数据」——那正是这个项目一直在防的反面。所以：

- `ecl_stack_clamp(position, size)` 把位置夹进数组，**同时计数**，
  并记下**到过的最大位置**；
- 通过 `ecl_stack_clamps` / `ecl_stack_clamp_first_offset` 两个导出暴露出来，
  探针每关打印；
- `local<T>` 与 `integer_reference` / `float_reference` 两条直接对 `data` 取址的
  裸路径都走这个函数。

这样偏差是**可数、可报、可追**的，而不是悄悄发生。

### 23.4 结果：第 4 关不再崩溃，而且铁证到手

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 7 | 跑满 3000 帧 | 跑满 3000 帧 |
| 3 | 941 帧 → 416 | 941 帧 → 416 |
| 4 | 1502 帧 → **崩溃** | **1502 帧 → ECL opcode 301** |
| 5 | 2340 帧 → 513 | 2340 帧 → 513 |
| 6 | 940 帧 → 416 | 940 帧 → 416 |

第 4 关从「wasm 崩溃」变成「干净的 opcode 拒绝」，而且计数器直接给出了答案：

```
[1 clamped stack access(es), max position 1082130432]
```

**`1082130432` = `0x40800000` = 4.0f 的位模式。** 也就是说，那一次
`stack.local<i32>(value)` 收到的**不是栈偏移量，而是一个浮点数的二进制位**——
这在原来的 ECL 里同样会被当成下标去读邻近内存（所以原版不崩），
但它**暴露了移植的一处类型混淆**：某个 opcode 把「浮点引用」按「整数引用」的
路径解析了。**这不是栈太小的容量问题**，所以「把栈改大」是错的解法，本轮没有那样做。

下一轮的第一个目标因此非常清晰：**找出是哪个指令把浮点当整数引用解析**，
把它引到 `float_reference` / `resolve_float` 上，然后那一次夹紧应当归零。

### 23.5 证据

`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、59 FPS；
**6 个闸门** exit 0；新工具 `th12-wasm-trap-map.mjs` 的标定有 375 个导出背书。
## 24. 本轮：拆掉 0x1b4 的「影子处理器」，第 4 关跑满全程

### 24.1 上一轮的夹紧记录，如何变成定位

上一轮只给出了夹紧位置 `0x40800000`（= 4.0f 的位模式），但不知道是**哪条指令**。
本轮让**每一条访问路径**（整数与浮点都算）在进入时记下当前指令，夹紧时一并记下
**opcode 与参数下标**，并通过 `ecl_clamp_opcode` / `ecl_clamp_argument` 导出。结果：

```
[1 clamped stack access(es), max position 1082130432, opcode 0x1b4, argument 0]
```

（顺带修掉一个记录缺陷：此前只记整数路径，所以在浮点路径上夹紧会报出**过期**的 opcode。）

### 24.2 0x1b4 有两个处理器，th11 那个把 th12 的挡住了

`EnemyEmitterCommands.cpp` 的内层 switch 里留着一对 th11 的：

```cpp
case 0x1b3:{...b.speed=f(arg);b.slow_speed=f(arg+4);break;}
case 0x1b4:{...b.count=i16(i(arg));b.layers=i16(i(arg+4));break;}
```

它们旁边的注释写着：「TH11 自己的 0x1b3/0x1b4 留在外层 switch，但对 TH12 数据**不可达**，
因为两者都在 `kTh12CollidingOpcodes` 里」。**这个判断在第 19 轮就过期了**：
那一轮释放 th12 自己的 `0x1b3/0x1b4` 时，**已经把 435/436 从该表里删除**。
于是「影子」变成活的：发射器先认领 `0x1b4`，`EnemyStateCommands.cpp` 里
**th12 真正的 0x1b4（float twin）**永远轮不到。

而 th11 的 0x1b4 是「按难度选 count/layers」，用**整数路径**读实参；
当 th12 数据在该位置给的是**浮点实参**时，浮点的位模式就会被当作栈偏移 ——
这正是 `0x40800000` = 4.0f 的来源，也是第 4 关越界的直接原因。

**这是「按 th11 号码分派」这一类 bug 的第三个实例**（前两个是 `EnemyCallbacks` 的
`0x22/0x40`，以及第 18 轮的 `0x1c0`）。共同点：th11 的实现留在原地，
而 th12 的号码语义变了。

### 24.3 修法与验证：一个可证伪的预测

- 从**内层 switch 和外层 gate** 里都删掉 th11 的 `0x1b3/0x1b4`，让它们落到 th12 真正的处理器；
- 把那段过期注释换成完整的来龙去脉记录。

**预测**：若诊断正确，夹紧计数应归零，且第 4 关应越过 1502 帧。实测：

- 夹紧计数 **0**（不再打印夹紧提示）；
- **第 4 关跑满 3000 帧**。

预测完全命中。所以这不是「改改试试」，而是一次**被验证的因果修复**。

### 24.4 关卡状态：7 关中 4 关跑满

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2 | 3000 | 3000 |
| 3 | 941 → 416 | 941 → 416 |
| 4 | 1502 → opcode 301 拒绝 | **3000（跑满）** |
| 5 | 2340 → 513 | 2340 → 513 |
| 6 | 940 → 416 | 940 → 416 |
| 7 | 3000 | 3000 |

### 24.5 闸门按预期变红，并已重生成

`th12-opcode-map.mjs --check` 本轮**正确地**报了 `ecl-extended-opcodes.json is stale`：
因为 435/436 的 `engineHandles` 从 `[EnemyEmitterCommands.cpp, EnemyStateCommands.cpp]`
变成了 `[EnemyStateCommands.cpp]` —— 这正是本次修改的语义。重生成后 `--check` 通过。
这说明闸门确实在盯「谁处理了这个 opcode」，而不是摆设。

### 24.6 证据

`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、59 FPS；**6 个闸门** exit 0。

### 24.7 下一步

仍卡住的两处都不是「号码错位」而是**功能未实现**：
- `416`（`0x1a0`，卡第 3/6 关）需要识别 `FUN_00453e20`；
- `513`（`0x201`，卡第 5 关）。
## 25. 本轮：把「两个处理器抢同一个 opcode」变成可检测

### 25.1 为什么需要它

第 22–23 轮的根因是**同一类**：th11 的实现留在**另一个文件**的 switch 里，
而 th12 改了同一个号码的含义。**C++ 编译器对这件事完全无能为力** ——
两张 `switch` 在不同函数、不同编译单元，重复的 `case` 标签不是错误，
运行时**谁先跑谁赢**。

而 `EnemyScript::command()` 的结构让这件事格外隐蔽：

```cpp
if(enemy_movement_command(...)||enemy_emitter_command(...))return 0;   // 先跑
...
else if(路由链 A) ...                                                  // 后跑
else if(路由链 B) ...
```

「先跑的两个」的 gate 一旦认领某个号码，**后面整条链都看不到它**。
`0x1b4` 就是这么死的：发射器先认领，`EnemyStateCommands.cpp` 里 th12 真正的
处理器永远轮不到 —— 代价是一次 wasm 越界崩溃和两轮排查。

三个实例都是**偶然撞见**的（`EnemyCallbacks` 的 `0x22/0x40`、第 18 轮的 `0x1c0`、
第 23 轮的 `0x1b4`）。偶然撞见三次，就该主动搜。

### 25.2 工具：`tools/th12-handler-routing.mjs`

- 从 `EnemyScript.cpp` 里把那条路由链的**原文表达式**逐条取出，
  **原文找不到就报错**（不许拿旧副本继续算）；
- 提取 `enemy_movement_command` / `enemy_emitter_command` 的**外层 gate**，
  以及各路由分支所属文件的 `case` 标签集合；
- 在 `0x100..0x2ff` 上求值：**「先跑的处理器的 gate 认领了它」且
  「路由本该去的处理器也有它的 case」= 影子**；
- `kTh12CollidingOpcodes` 里的号码按「故意拒绝」排除（那些是有据可查的拒绝，不是意外）。

### 25.3 结果，以及「故意证伪」

- 现状：movement gate **28** 个、emitter gate **25** 个，其中**影子 0 个**。
- **证伪 1（把原 bug 放回去）**：往 emitter gate 塞回 th11 的 `case 0x1b4` → 工具报

  ```
  0x1b4: enemy_emitter_command runs first, EnemyStateCommands.cpp also handles it and never runs
  FAIL: 1 opcode(s) are shadowed by a pre-chain handler
  ```

  exit 1 —— **它抓得住那个花了两轮才找到的 bug**。
- **证伪 2（换一个号码）**：塞 `0x199` → **不报影子**（`EnemyStateCommands.cpp` 没有这个
  case），说明判定不是针对 `0x1b4` 的特例硬编码；随后把文件**原样还原**
  （`git diff` 确认与提交状态逐字节一致）。

所以本工具的两半都**先被证伪过**才留下 —— 和 `th12-dispatch-gate.mjs` 一样的标准。

### 25.4 结论，以及本工具的边界

**第 22–23 轮的修复没有遗漏同类影子** —— 这是本轮能说的唯一「好消息」，
而且它是有证据的，不是感觉。

边界要说清楚：本工具只覆盖**「先跑的两个 vs 路由链」**这一种影子。
`EnemyCallbacks` 那种「按数据里的脚本号分派」是**另一类**（第 22 轮已修两处，
第三个 `0xbf` 因在 th12 里找不到对应比较点而保留），不在此工具射程内。

### 25.5 证据

`th12-*` 12 项全过；浏览器 95 秒 `error=""`、`traps: 0`、60 FPS；
**7 个闸门** exit 0（新增的 `th12-handler-routing.mjs --check` 已加入每轮闸门清单）。

### 25.6 下一步

仍卡住的两处都不是号码错位，而是**功能未实现**：`416`（`0x1a0`，卡第 3/6 关）
需要识别 `FUN_00453e20`；`513`（`0x201`，卡第 5 关）。
## 26. 本轮：把 416（0x1a0）从「拒绝」变成音效 —— 第 3 关跑满、第 6 关越过

### 26.1 416 到底是什么：证据链

推进到第 24 轮后，卡住的只剩两处，而 416 卡着第 3、6 关，且 `usedInTh12Dat: 328`
（th12 数据里最常见的指令之一）。它的函数体一直把 `FUN_00453e20` 当黑盒，本轮读穿了：

1. `FUN_00453e20` 读 `*(short*)(&DAT_004ae5aa + id*0x14)` —— 一张 **0x14 步长**的 16 位表。
   `0x4ae5aa + 56*0x14 ≈ 0x4aea0a`，**正好紧挨着已知的 49 指针音效表 `0x4aea50`**
   —— 即这是那张约 56 项的「音效定义表」（正是待办清单里的那条）。
2. 它把值写进 `DAT_004cf508`：`0x4cf538 - 0x4cf508 = 0x30 = 12*4` → **12 个槽**；
   每槽一个计数 `DAT_004cf538`；每槽最多 128 个值 `DAT_004cf568`（`0x80*4 = 0x200` 步长）。
3. **决定性的一步**：该族的消费者 `FUN_00453fa0` 在第 252–257 行做的是

   ```c
   (**(code **)(*piVar3 + 0x24))(piVar3,&fStack_4);
   (**(code **)(*(int *)(&DAT_004d0e70)[iVar4*6] + 0x48))(...);
   ```

   —— **COM 虚表调用**（+0x24 / +0x48），外侧包着 `LeaveCriticalSection`，
   入口由 `DAT_004ceacc` 把关。这是 **DirectSound 缓冲区控制**（Stop / Play 一类）。

所以 **416 = 播放音效 `i(0)`**：音效 id 由 `FUN_0041a900(0)` 的低 dword 传来
（即第一个 ECL 参数），与端口里已有的 0x150 是同一类路径。**这是被证明的，不是猜的。**

### 26.2 真正的问题：一个音效调用不该让整关停下

端口的原则是「不认识的指令宁可拒绝」。但对**音效**指令，拒绝的代价是
**整关停在第 941 帧** —— 为了一个音频调用牺牲整个关卡，这个交换是不对的。
所以本轮把它实现掉，而不是继续拒绝。

### 26.3 改动

- **路由**：把 `0x1a0` 移出激光区间（加 `op!=0x1a0`），加入 `EnemyManager` 分支（与 0x150 同处）；
- **实现**：`if(op==0x1a0)return world.sound(c.integer_argument(0,g),e.current.position.x)?0:-2;`
- **从 `kTh12CollidingOpcodes` 删掉 416**（不再是碰撞指令）；
- 删掉 `EnemyLaserCommands.cpp` 里 th11 的 `case 0x1a0` 及其 `b->speed=f(1)` 分支
  —— 又一个「th11 号码残留」，不删就会与新处理器抢号码；
- `th12-handler-routing.mjs` 里的**原文表达式**同步更新。该工具正是为此设计：
  **本轮它确实因为原文不符而报错**，我据此修正 —— 工具起作用了。

### 26.4 结果

| 关卡 | 上一轮 | 本轮 |
| --- | --- | --- |
| 1, 2, 4, 7 | 3000 | 3000 |
| 3 | 941 → 416 | **3000（跑满）** |
| 5 | 2340 → 513 | 2340 → 513 |
| 6 | 940 → 416 | **1010 → 308（越过 416）** |

**7 关中 5 关跑满**（1 / 2 / 3 / 4 / 7）。

### 26.5 记录与闸门

- `ecl-extended-opcodes.json` 重新生成：`collision` **31→30**、`implemented-collision`
  **15→16**，**恰好一条移动**，就是 416；其 `engineHandles` 由
  `EnemyLaserCommands.cpp` 变为 `EnemyManager.cpp`，并标记 `implementedNotRefused`。
- **7 个闸门** exit 0。

### 26.6 诚实的偏差说明

端口**不模拟**那 12 通道的值队列与逐帧缓冲区更新（那是宿主没有暴露的混音细节），
只把 id 交给宿主的音效层播放。这条偏差写在代码注释里，不藏着。

### 26.7 下一步

只剩 `513`（`0x201`，卡第 5 关）与本轮新暴露的 `308`（卡第 6 关）。
## 27. 本轮：把两个剩余阻塞指令的原始 case body 挖出来（并修掉一个我自己踩的坑）

### 27.1 先修一个我自己踩的坑：opcode → case 不是一张表

第 26 轮我为了找 case body，按
`[0x419654 + (opcode-0x100)*4]` 直接读跳转表 —— **这是错的**，
而且错得很隐蔽：它读出来的是**字节表的字节被当成指针**，会**落到另一个 opcode 的 case 上**。
实测：这样算出的「308」其实是 **opcode 411 的 body**。

正确的两段式（`tools/th12-ecl-case-map.mjs` 的注释里早就写着）：

```
ecx   = opcode - 0x100
index = byte[0x419890 + ecx]      ; 字节表
goto  [0x419654 + index*4]        ; 跳转表按「字节表的输出」索引
```

**教训与第 16 轮的 `.Replace()`、第 23 轮的「影子」同类**：一个看似合理的机械步骤，
如果没有对照就会安静地给出错误答案，而且答案看起来「像那么回事」。

### 27.2 新工具：`tools/th12-case-body.py`

把手写了两遍的流程固化成工具：读 `docs/th12/ecl-case-bodies.json` 里**已有的反向表**
（每个 case 地址列出哪些 opcode 到达它，且由 `th12-ecl-case-map.mjs --check` 守着），
输出 case VA、exe 偏移、**共享该 body 的 opcode 列表**，并用 Capstone 反汇编到
共享尾声 `jmp 0x41962b` 为止。

```
$ py -3 tools/th12-case-body.py 308 513
=== opcode 308 (0x134) ===
  case VA 0x416d06  exe offset 0x16106  shared with opcodes [308, 310]
=== opcode 513 (0x201) ===
  case VA 0x4190aa  exe offset 0x184aa  shared with opcodes [513]
```

### 27.3 opcode 308（0x134）：往 `EnemyState+0x68` / `+0x9c` 写四个浮点

反汇编读到的事实：

- `mov edx,0x134` / `cmp ax,dx` / `je` → **同一 body 被 308 与 310 共享**，
  这一比较就是**结构体选择开关**：308 用 `ebx+0x68`，310 用 `ebx+0x9c`；
- `ebx` 由 `[ebx+0x174c]`（script_owner）可确认是 **EnemyState**；
- 依次 `call 0x468ec0` 取**四个浮点实参**（0..3）；
- 若 `byte[edi+0x30]&1` 未置位，先把 `[edi..edi+8]` 复制到 `[edi+0xc..edi+0x14]`
  （**把当前位置存成「上一帧位置」**）；
- 再把 arg1→`+0x18`、arg2→`+0x20`、arg3→`+0x24`（各自带一个与
  `qword[0x4a4440]` 常量的比较，**小于阈值就跳过不写** —— 「保留原值」的哨兵语义）；
- 置位 `[edi+0x30] |= 1`，然后 `call 0x464eb0`、`call 0x413700`。

**已知**：这是一个双实例的插值/平滑结构写入（位置 + 上一帧 + 三个参数 + 标志位）。
**未知**：`0x464eb0` / `0x413700` 的确切职责、以及 `+0x18/+0x20/+0x24` 三个字段的语义。
**没有实现** —— 端口里没有这两个结构体的对应布局可对，硬塞就是猜。

### 27.4 opcode 513（0x201）：以 `f(0)` 为半径消弹

反汇编 + `FUN_0040caa0` 的完整函数体给出确定语义：

```
call 0x41a950            ; f(0) -> 半径
push 0; push 0; ... ; call 0x40caa0(位置=&EnemyState+0x34, 0, 0, 半径)
push 1; push 0; ... ; call 0x4286f0(半径, 0, 1)
```

`FUN_0040caa0` 内部（已读全文）：

- 遍历 **2000 个子弹槽**（`DAT_004b43c8+100`，步长 0x9f8），只要子弹状态 ∉ {0,3}；
- `dx*dx + dy*dy <= (bullet[+0x4dc]*0.5 + 半径)^2` 即命中；
- 命中后 `FUN_0040c8b0()` —— **这就是消弹**（同一个函数在 `FUN_0041ae20` 里也是消弹）；
- 再 `FUN_0040d560(bullet+0x4bc,2.0,2.0)`，返回 0 且 param_4≠0 时
  `FUN_004273f0(..., 9, bullet+0x4bc, -1.5707964, 0.6)`（**在子弹处生成 9 号特效**）；
- 最后 `FUN_00414f40(..., 位置, 半径, param_4)`。

`FUN_004286f0`：把 `ESI[0..2]` 写进 `DAT_004b44f4+0x470/0x474/0x478`，
再遍历一个链表对各对象调用 `vtable+0x1c` 并累加返回值 —— **在给定位置触发一批效果**。

**已知**：513 = 「以敌人为中心、半径 `f(0)` 消弹，并在每发被消子弹处出分数/特效」。
**没实现的原因（诚实说明）**：命中判定里的 `bullet[+0x4dc]`（每发子弹的半径项）
在端口 `BulletState` 里我**还没有对照出对应字段**。拿一个没验证的字段去算半径
就是猜——这正是本项目一直在防的事，所以本轮**只把证据落地，不写实现**。

### 27.5 下一步（非常具体）

1. 在端口核出 `bullet[+0x4dc]` 的对应字段（对照 `BulletState` 布局），然后实现 513 的消弹部分；
2. 核出 `EnemyState+0x68` / `+0x9c` 两个结构体在端口里的对应（第 27.3 节），再实现 308；
3. 两者都会把「已实现的 case 数」往前推一格，而不是靠猜。

### 27.6 证据

`th12-*` 12 项全过；**7 个闸门** exit 0；本轮**没有改动任何 Runtime 源码**
（`git diff --name-only runtimes/` 为空），所以第 25 轮的浏览器实测（59 FPS、0 trap）依然适用。
## 28. 本轮：513 落地，**第 5 关跑满 → 7 关中 6 关跑满**

### 28.1 关键一步：`bullet[+0x4dc]` 就是端口里的 `hitbox.x`

上一轮卡在「`bullet[+0x4dc]` 对不上端口字段，所以不写实现」。本轮把它对上了，
方法是找一个**可验证的位移**而不是猜名字：

端口的 `BulletState` 断言 `offsetof(position)==0x43c`，而 th12 的子弹位置在 `+0x4bc`
—— 两者相差 **0x80**。于是拿四个**独立锚点**验证这个位移：

| 字段 | 端口偏移 | th12 偏移 | 差 |
| --- | --- | --- | --- |
| position | 0x43c | 0x4bc | 0x80 |
| velocity | 0x448 | 0x4c8 | 0x80 |
| speed | 0x454 | 0x4d4 | 0x80 |
| angle | 0x458 | 0x4d8 | 0x80 |

四个全部恰好 0x80，所以 `+0x4dc` → 端口 **0x45c = `hitbox`（Vec2）的第一个分量**。
（`sizeof` 总和不等 0x910+0x80 只是说明结构体后段另有差异，与我们要的区间无关。）

### 28.2 更大的发现：`cancel_circle` 本来就是 `FUN_0040caa0`

对完偏移后我去看 `BulletManager::cancel_circle`（第 99 行），结果它**逐字段**就是
th12 的 `FUN_0040caa0`：

| th12 反汇编/反编译 | 端口 `cancel_circle` |
| --- | --- |
| `state != 0 && state != 3` | `if(!b.state\|\|b.state==3\|...)continue;` |
| `(bullet[+0x4dc]*0.5 + param_3)` | `float r=b.hitbox.x*.5+radius` |
| `dx*dx+dy*dy <= r*r` | `if(!(distance > r*r))` |
| `FUN_0040c8b0()`（消弹） | `cancel(b)` |
| `FUN_0040d560(bullet+0x4bc,2.0,2.0)` | `outside(b.position,2,2,0)` + `cancel_reward` |
| `FUN_00414f40(...,位置,半径,...)` | `world.cancel_enemies(center,radius,reward)` |
| 开场 `(flags&1)&&0x5f<timer<100 → param_3/3` | `context.protected_spell() → radius/3` |

**这是双向验证**：我从反汇编独立推出的公式（第 27 轮），与几轮之前就写好的端口代码
**完全一致**；同时反过来说明那段端口代码确实对应 `FUN_0040caa0`，不是别的函数。

### 28.3 所以 513 是一次调用，不是新代码

th12 的 513 体是 `FUN_0040caa0(位置, 半径=f(0), 0, 0)`：`param_4=0`（不出 9 号特效）、
`param_5=0`（不加子弹过滤）→ 端口的 `reward=true`、`skip_delayed=false`。
按 `EnemyLaserCommands.cpp:19` 已有的写法补上取消上下文：

```cpp
case 0x201:
    if(!w.bullets)return -2;
    return w.bullets->cancel_circle(e.current.position,f(0),true,false,
             w.cancellation?*w.cancellation:BulletCancelContext{})?0:-2;
```

**构建期抓到一个错**：第一次编译报
`member access into incomplete type 'BulletManager'` —— 类型不完整，补
`#include "BulletManager.hpp"` 即好。（不是名字写错，编译器替我分清了。）

**未建模并写在注释里**：`FUN_004286f0`（把敌人位置写进某个管理器，再对一个效果链表
批量调用 `vtable+0x1c` 并累加）**没有实现**。

### 28.4 结果

| 关卡 | 第 26 轮 | 本轮 |
| --- | --- | --- |
| 1,2,3,4,7 | 3000 | 3000 |
| **5** | 2340 → 513 | **3000（跑满）** |
| 6 | 1010 → 308 | 1010 → 308 |

**7 关中 6 关跑满**，只剩第 6 关被 308 卡住。

### 28.5 308 的对账（已推进一大步，但仍未实现）

- `EnemyState` 的前四个成员是 `Movement previous,current,absolute,relative`，而
  `Movement` 断言 `sizeof==0x34` → `previous@0x00, current@0x34, absolute@0x68,
  relative@0x9c` —— **恰好就是 308 / 310 选择的两个偏移**（308→`+0x68`，310→`+0x9c`）；
- `Movement` 的 `speed@0x18, angle@0x1c, radius@0x20, radial_velocity@0x24` 与
  body 写入的 `+0x18/+0x20/+0x24`（跳过 +0x1c）**逐一对上**；
- **但 `+0x0c` 对不上**：body 在 `flags&1` 未置位时把 `[+0x00..+0x08]` 复制到
  `[+0x0c..+0x14]`，端口这个位置叫 `velocity`，而那语义上应是「首帧把当前位置对齐到目标」。
  字段语义存疑——**所以本轮不写 308**，不拿没核实的字段去改敌人运动。

### 28.6 证据

- 关卡探针（各 3000 帧）：**1/2/3/4/5/7 跑满**，6 停在 1010 → 308；
- `th12-*` 12/12；`build-sdl.mjs` exit 0（sha256 `92bb6e74…`，1554480 字节）；
- 浏览器实测：`error=""`、`61 FPS`、`traps: 0`；
- **7 个闸门** exit 0。

### 28.7 下一步

只需解决 `+0x0c` 的字段语义（找一个已知会写该字段的 th12 opcode 做对照），308 即可落地，
7 关全满。
## 29. 本轮：修判决规则、308/310 落地（含三个 callee 全部对上）

### 29.1 先修判决规则：`todo` 一直在骗人

上一轮末尾发现：判决表的 `verdict` 只在「原作是 no-op」或「碰撞指令」两种情况下脱离 `todo`，
**其余一律 `todo`**。也就是说 **`todo` 的真实含义是「被 th12.dat 用到且不是碰撞指令」，
而不是「未实现」**。工具其实早就算出 `engineHandles`，只是没用它做判决。

本轮加一档 `implemented`（`handled.has(id)` → `implemented`，其余 `used>0` → `todo`）：

| 轮次 | implemented | todo | unused |
| --- | --- | --- | --- |
| 修规则前 | — | 65 | 110 |
| 修规则后 | 116 | **28** | 31 |
| 308/310 落地后 | **118** | **26** | 31 |

现在 **`todo` = 「th12.dat 用到、但引擎里没有对应 case」**，这才是真正可执行的待办清单，
而且它和第 24 轮的「处理器路由」闸门方向一致（那边管「有没有抢号码」）。

### 29.2 308 / 310 落地：三个 callee 全部指回端口已有函数

`EnemyState` 前四个成员是 `Movement previous,current,absolute,relative`，`sizeof(Movement)==0x34`
→ `absolute@0x68`、`relative@0x9c` —— **正好就是 body 开头 `cmp ax,0x134` 选择的那两个偏移**
（0x134 用 absolute，0x136 用 relative）。字段也逐个对上：

| 反汇编 | 端口 ->
| --- | --- |
| `FUN_00408910(edi,arg0)` 写 `edi+0x1c` | `Movement::angle` |
| `fstp [edi+0x18]` = arg1 | `Movement::speed` |
| `fstp [edi+0x20]` = arg2 | `Movement::radius` |
| `fstp [edi+0x24]` = arg3 | `Movement::radial_velocity` |
| `flags |= 1` | 切到极坐标模式 |
| `FUN_00464eb0`（读 `EBX+0x30` 的 bit0） | `Movement::update_velocity` |
| `FUN_00413700` | `EnemyState::combine_movement` |

三个 callee 都读了原文，**都是端口里已经存在的函数**：

- `FUN_004646e0` = **`normalize_angle`**：±π 折返 + **同样的 32 次循环上限**，与端口实现逐句相同；
  `FUN_00408910` 是它连用两次（幂等，所以端口写一次即可）；
- `FUN_00464eb0`：`if(flags&1){radius+=radial_velocity;angle+=speed;}` —— 就是 `update_velocity`；
- `FUN_00413700`：
  `*(ESI+0x40) = (*(ESI+0x9c)+*(ESI+0x68)) - *(ESI+0x34)` —— 即
  `current.velocity = relative.position + absolute.position - current.position`，
  正是端口已有的 `combine_movement()`（`ESI+0x40` = `current` 的 `velocity` 字段）。

阈值常量 `[0x4a4440]` 读出来是 double **−999999**（防御性下限，正常值一律写入）。

### 29.3 「看起来不合理」的那条拷贝，其实是轨道中心

body 里 `if(!(flags&1)) [edi+0x0c..] = [edi+0x00..]` 一度像是 `velocity = position` 这种无意义写法。
把 `Movement.cpp` 两种模式读在一起就通了：

- `flags&1 == 0`（速度模式）：`update()` 做 `position += velocity`，`velocity` 是**速度**；
- `flags&1 == 1`（极坐标模式）：`refresh_position()` 做 `position = velocity + polar(angle,radius)`，
  **`velocity` 变成轨道中心**；`update_velocity()` 做 `radius+=radial_velocity; angle+=speed`。

所以「把当前位置复制进 velocity」= **以后就以敌人现在的位置为圆心转**，而
**已经处于极坐标模式时跳过**这条拷贝，等于「重新设参数但保持圆心」—— 完全自洽。

### 29.4 结果

stage 6 从 `1010 → 308` 前进到 `1010 → 309`（309 是同帧的下一条指令，属 308/309/310 家族）。
7 关中 6 关仍跑满，但 308/310 已从阻塞名单消失。

### 29.5 309 / 311：已挖出，但本轮不写

309 与 311 共享 body，它同时选三组结构：`absolute`/`relative`（0x68/0x9c）、
`absolute_angle`/`relative_angle`（**0x324/0x360**）、`absolute_radius`/`relative_radius`（**0x39c/0x3d8**）
—— 正是已知的 **+0x118 插值器族**。但它有 **5 个实参**、会拼一个多浮点实参块、
还会两次调用 `0x468e20`，比 308 复杂一档。**没有实现对**——需要先像 29.2 那样把
`Vec2Interpolator` 的字段逐个对上，否则又是猜。

### 29.6 又抓到我自己工具的一个 bug

`tools/th12-case-body.py` 原本「遇到第一条 `jmp 0x41962b` 就停」。309 的 body 里
有一条 `jg 0x416f5d` **继续往后**，于是反汇编被**截断**了 —— 又一次「安静的错答案」。
已改成**停在下一个 case 地址**：308 现在正确结束在 `0x416e03`，**正好是 309 的 case 地址**。

### 29.7 证据

- 判决表：`todo` 65 → **26**；308/310/513 = `implemented`，309 = `todo`；
- 关卡探针（各 3000 帧）：1/2/3/4/5/7 跑满，6 停在 1010 → **309**；
- `th12-*` 12/12；`build-sdl.mjs` exit 0（sha256 `bcc65de1…`）；浏览器 `error=""`、**60 FPS**、`traps: 0`；
- **7 个闸门** exit 0。

### 29.8 下一步

把 309/311 的 `Vec2Interpolator` 字段对上（对照 `+0x118` 族的 four 个插值器），
然后实现 —— 那将是第 7 关也跑满的临门一脚。
## 30. 本轮：512 落地；并回头**验证**上一轮已落地的 513 是对的

### 30.1 512（0x200，49 次使用）落地

512 的 body 与 513 **是同一个调用**，只差一个标志：

```
f(0) -> 半径
push 0; push 1; ... call 0x40caa0   ; 512: param_5=0, param_4=1
f(0) -> 半径
push 0; push 0; ... call 0x40caa0   ; 513: param_5=0, param_4=0
```

所以本轮把 `case 0x200:` 与 `case 0x201:` 合并到同一条已验证的 `cancel_circle` 路径上。
判决表：`implemented` 118 → **119**，`todo` 26 → **25**。

### 30.2 顺手把 513 的那个「reward 到底该不该是 true」验证掉了

上一轮 513 我写的是 `reward=true`，但当时没读 `FUN_00414f40`，心里其实没底。本轮读了：

- `FUN_00414f40` 的**第 5 个参数只用来 gate `FUN_004273f0(...,9,...,-pi/2,0.6)`**（出特效）；
- 而它上面的**扣血/结算（`-99999` 那一整段）是**无条件执行**的**。

也就是说 `FUN_0040caa0` 的 `param_4` **始终是「特效开关」，不是「是否结算」**——
它既用于每发子弹的 9 号特效，也作为 `FUN_00414f40` 的第 5 参数传下去，两处一致。
**所以 513 的 `reward=true` 是对的**，无需修改。

**512 与 513 的唯一差别**就是：512（`param_4=1`）要为**每发被消子弹**额外生成 9 号特效。
端口的 `cancel_circle` 没有「每发回调」这个钩子，所以这一条**明确记为偏差**；
**消弹与结算是逐字段精确的**。另外那个 `FUN_004286f0` 批量效果调用两处都没建模。

### 30.3 309/311：又一次**确认不写**（并说明还差什么）

309/311 的结构本轮全部对上了：

| 反汇编 | 端口 |
| --- | --- |
| `ebx+0x68` / `ebx+0x9c` | `EnemyState::absolute` / `relative`（Movement） |
| `ebx+0x324` / `ebx+0x360` | `absolute_angle` / `relative_angle`（步长 0x3c） |
| `ebx+0x39c` / `ebx+0x3d8` | `absolute_radius` / `relative_radius` |

th12 的插值器偏移 = 端口偏移 **+0x118**（`absolute_angle` 0x20c→0x324 恰好吻合），
且 `0x360-0x324 = 0x3c` 正是 `Vec2Interpolator` 的大小。端口的
`Interpolator<float,2>` 布局为 `start/end/initial_tangent/final_tangent`（0x00/0x08/0x10/0x18）
+ `Timer`（0x20）→ 于是 `[eax+0x34]` = **duration**、`[eax+0x38]` = **mode**
（mode 来自 `FUN_00468e20` 这个**取引用式取参**函数，它读 `+0x100c`，与端口 EclStack 布局一致）。
`FUN_0041c350` 是插值器复位（写 `+0x20/+0x24/+0x28/+0x2c/+0x30`）。

**但仍有两处没落实，所以不写**：
1. `FUN_00468e20(0)` 的返回值存进 `[esp+0x18]` 后，我在两条路径里都没看到它被真正使用；
2. 用作两个切线的全局量 `0x4ce8dc`/`0x4ce8e0` 位于 `.data` 的**零填充尾部**（文件里读不到，
   装载后为 0.0），但不能排除运行期被写入。

拿一个没核实的切线/模式去初始化插值器，会得到**看起来在动但语义不对**的敌人运动——
这正是本项目一直防的事，所以 309/311 继续留给下一轮。

### 30.4 `todo` 现在是一张真正的路线图

25 条，按使用次数排：

| opcode | 使用次数 | 备注 |
| --- | --- | --- |
| 257 (0x101) | **135** | 最高频，`shared`，`sharedBodyCalls=3` |
| 602 (0x25a) | 98 | |
| 525 (0x20d) | 83 | |
| 529 (0x211) | 70 | |
| 600 (0x258) | 70 | `decompiled=absent` |
| 512 (0x200) | 49 | **本轮已落地** |
| 279 (0x117) | 43 | |

**309 只有 3 次使用**，却因为是第 6 关第 1010 帧的下一条指令而卡在那里。
这些高频指令在 1–5/7 关的 3000 帧内都没被触及——说明**探针的 3000 帧预算看不到它们**，
后续要按「使用次数 × 可达性」而不是只看探针来排优先级。

### 30.5 证据

- 判决表：`implemented` **119**、`todo` **25**；
- 关卡探针（各 3000 帧）：1/2/3/4/5/7 跑满，6 停在 1010 → 309（512 不在其前 1010 帧内，故未变）；
- `th12-*` 12/12；`build-sdl.mjs` exit 0（sha256 `486bda39…`）；浏览器 `error=""`、**59 FPS**、`traps: 0`；
- **7 个闸门** exit 0。

### 30.6 下一步

309/311 补上那两处（`FUN_00468e20(0)` 的用途、`0x4ce8dc/0x4ce8e0` 是否运行期写入）后即可实现；
之后按 30.4 的表推进高频指令。
## 31. 本轮：309/311 落地 —— **7 关全部跑满 3000 帧（首次）**

### 31.1 方法上的升级：别再只看反汇编，直接读反编译出来的 C

第 26–29 轮我一直用 Capstone 反汇编去逐条读 case body，309 因此连着两轮「差两处没落实」。
本轮换了来源：**调度器本身有反编译好的 C**（`FUN_004154d0_004154d0.c`），
里面就是 `case 0x135: case 0x137:` 的完整 C 体。两处悬案**当场全解**：

1. **`FUN_00468e20(...,0)`/`(...,1)` 就是 duration / mode**：
   C 里写得很清楚 `piVar9[0xd] = FUN_00468e20(...,0);`、`piVar9[0xe] = FUN_00468e20(...,1);`
   —— `0xd*4 = 0x34`（duration）、`0xe*4 = 0x38`（mode），与我上一轮的推断一致。
2. **两个切线全局量是常量 0**：`DAT_004ce8dc`/`DAT_004ce8e0` 在**整棵反编译树里只被读**
   （三处，全是赋给插值器的 `+0x10/+0x14/+0x18/+0x1c`），而且它们位于 `.data` 的**零填充尾部**
   —— 所以两个切线都是 `{0,0}`。
3. `FUN_0041c350` 就是端口的 **`Timer::set(0, rate)`**：
   它把 `previous=-1`、`current=0`、`fractional=0`，并装上默认速率指针 —— 逐句一致。

**更重要的收获**：这份 C 同时**独立验证了第 28 轮的 308 实现**——
`puVar13[6]/[8]/[9]`（=+0x18/+0x20/+0x24）、`flags&1` 的拷贝、`|= 1`、`FUN_00464eb0`、`FUN_00413700`
与我的实现逐条对应。**并抓到我一个错**：角度写入在原作里**也受 `-999999` 保护**，我写成了无条件；
且比较是严格的 `>`（`if (-999999.0 < v)`），我用的是 `>=`。本轮已改。

### 31.2 309/311 的字段映射（全部落在端口已有构造上）

| C 里的量 | 端口 |
| --- | --- |
| `local_314 = 0x68/0x9c` | `EnemyState::absolute` / `relative` |
| `local_2f0 = 0x324/0x360` | `absolute_angle` / `relative_angle` |
| `pfVar11 = 0x39c/0x3d8` | `absolute_radius` / `relative_radius` |
| `f(2)/f(3)/f(4)`，各自在 `<= -999999`（含 NaN）时回退到 Movement 的 speed/radius/radial_velocity | 同 |
| `FUN_00468e20(...,0/1)` | duration / mode |
| `piVar9[4..7]` = 常量 0 | 两个切线 = 0 |
| `FUN_0041c350` | `Timer::set(0, rate)` |
| duration `< 1` 时只把两个 duration 置 0（连 `flags|=1` 与两个调用都跳过） | 同 |

### 31.3 构建期又抓到一次错

`Interpolator<T,N>` 用的是 **C 数组** `T start[N]`，所以 `angle.start={...}` 报
`array type 'float[2]' is not assignable` —— 改成分量赋值。**编译器又一次替我挡住了错**。

### 31.4 结果：7 关全部跑满，并且边界一次推进 4 倍

| 关卡 | 第 29 轮（3000 帧） | 本轮（3000 帧） | 本轮（**12000 帧**） |
| --- | --- | --- | --- |
| 1,2,3,4,7 | 跑满 | 跑满 | **12000 跑满** |
| 5 | 跑满 | 跑满 | 4320 → **418** |
| 6 | 1010 → 309 | **跑满** | **12000 跑满** |

**首次 7 关全部跑满 3000 帧。** 把预算加到 12000 帧后，**6 关仍然跑满**，
只剩第 5 关停在 4320 → opcode **418**（此前探针只能看到 2340，边界一次推进约 4 倍）。

### 31.5 证据

- 判决表：`implemented` **121**、`todo` **23**；
- 关卡探针 3000 帧：**7/7 跑满**；12000 帧：**6/7 跑满**，5 关 4320 → 418；
- `th12-*` 12/12；`build-sdl.mjs` exit 0（sha256 `0f63cfc3…`）；浏览器 `error=""`、**61 FPS**、`traps: 0`；
- **7 个闸门** exit 0。

### 31.6 下一步

第 5 关的 **418**（在碰撞名单里，属拒绝类）与 `todo` 剩 23 条；
按「使用次数 × 可达性」推进，探针预算此后用 12000 帧。
## 32. 本轮：418 落地 —— 第 5 关从 4320 推进到 412；并补上对话关闭这个端口缺口

### 32.1 418（0x1a2）是什么

从调度器 C（`FUN_004154d0`，`case 0x1a2`）读出来是**一串「清屏」**，并且**掉进 0x1a9**：

| 反编译 | 实际做的事 |
| --- | --- |
| `FUN_0041fbe0` | **拆掉并释放对话对象**（`_free`，由 `DAT_004b43e4+0x6d30` 是否非空保护） |
| `FUN_0040cf60(…,0)` | **清子弹**：遍历 2000 个弹槽，把**在屏内**的子弹打上标志位 8（取消位），并累加一个计数；带「符卡保护窗口」闸门 |
| `FUN_00428750` | **取消激光**：遍历 `DAT_004b44f4+0x18`，对每个对象调 `vtable+0x14` |
| `FUN_00414c60`（经 0x1a9 掉入） | **清除关卡敌机**：遍历 `DAT_004b43dc+0x68`（与 `FUN_00414f40` 同一张表） |

### 32.2 端口其实**已经**有这套组合

`GameBattle::start_dialogue`（`GameBattle.cpp:429`）里就写着：

```cpp
if(!bullets.cancel_all(false,cancellation)||!lasers.cancel_all(false,false)||!enemies.erase_stage_enemies())return false;
```

——**子弹 / 激光 / 敌机三清**，而且 `erase_stage_enemies` 的名字与 `FUN_00414c60` 的语义正好对上。
所以 418 直接复用这三步，加上第一步的对话拆除，就是逐段精确的。

### 32.3 顺带补上一个真实端口缺口

端口的 `DialogueControl` 接口**只有** `start_dialogue` 和 `dialogue_waiting`——
**没有「关闭」**，而 th12 的 0x1a2 要拆对话对象。本轮补上：

* `Dialogue.hpp`：`virtual bool dialogue_close(){return false;}`；
* `GameBattle`：`dialogue_close(){if(dialogue)dialogue->clear();return true;}`。

### 32.4 为什么 418 一直躺在碰撞名单里

th11 的 `0x1a2` 是「设置激光角度」（端口旧代码正把 `0x19f/0x1a1/0x1a2/0x1a3` 并成一组这么写）。
th12 的 0x1a2 与它毫无关系，所以它被算作碰撞并拒绝。本轮：
* 从 `kTh12CollidingOpcodes` 移除 `418`；
* 把 `case 0x1a2:` 从激光那组**拆出来**，单独实现。

构建期又抓到一次错：`DialogueControl`/`EnemyManager` 在 `EnemyLaserCommands.cpp` 里是**不完整类型**，
补 `#include` 后通过。

### 32.5 结果

| 关卡 | 上一轮（12000 帧） | 本轮（12000 帧） |
| --- | --- | --- |
| 1,2,3,4,6,7 | 跑满 | 跑满 |
| 5 | 4320 → 418 | 4320 → **412**（再下一层） |

判决表：`collision` 30 → **29**，`implemented-collision` 16 → **17**。

### 32.6 下一轮的目标（语义本轮已经读出来了）

**412（0x19c）**——它其实很干净：

```c
iVar17 = (int)FUN_0041a900(0);          // 取整数参数 0
FUN_004124e0(0);
if (iVar17 < 0) {                        // 参数 < 0：注销
    if (flags & 0x400000) manager[0x1c + e[0x16c4]*4] = 0;
    flags &= ~0x400000;
} else {                                 // 参数 >= 0：注册
    flags |= 0x400000;
    manager[0x1c + iVar17*4] = e[0x174c];    // 存 script_owner
    e[0x16c4] = iVar17;                      // 记住槽位
}
```

即「**把这只敌机登记/注销到管理器的投影数组**」。顺带说明一件事：
**这佐证了端口 `EnemyManager.cpp:115` 用 `e.flags&0x400000` 作为 3D 投影闸门是对的**——
DELIVERY §6 里那条「端口用 `0x400000`、反编译另一处用 `0x2000000`」的悬案，
至少 `0x400000` 的含义现在从使用点上得到了独立确认（两者是不同的标志，不是同一处写错）。

### 32.7 证据

- 关卡探针 12000 帧：1/2/3/4/6/7 **跑满**，5 关 4320 → **412**；
- `th12-*` 12/12；`build-sdl.mjs` exit 0（sha256 `917411cd…`）；浏览器 `error=""`、**60 FPS**、`traps: 0`；
- **7 个闸门** exit 0。
## 33. 本轮：412 落地；425 落地后**被闸门否决、已回滚**（本轮最重要的收获）

### 33.1 412（0x19c）落地

调度器 C 里的 `case 0x19c` 很干净：

```c
iVar17 = (int)FUN_0041a900(0);      // 参数 0 = 槽位
FUN_004124e0(0);                    // 清 manager+0x3c 的第 0 位
if (iVar17 < 0) {                   // 注销
    if (flags & 0x400000) manager[0x1c + e[0x16c4]*4] = 0;
    flags &= ~0x400000;
} else {                            // 注册
    flags |= 0x400000;
    manager[0x1c + iVar17*4] = e[0x174c];   // script_owner
    e[0x16c4] = iVar17;
}
```

端口的对应关系全部落实：

* **`FUN_004124e0(0)` → `w.manager_flags &= ~1u`**：端口**早就**把这个字段建模成
  `w.manager_flags`（`case 0x1ba` 正是用参数写这一位，`case 0x14c` 清这一位）。
* **`flags & 0x400000` 也已全程建模**：`EnemyManager.cpp:17` 从敌机生成参数的
  `world_coordinates` 第 22 位设它；投影、碰撞、动画、状态四条路径都按它分支。
  端口是**逐敌机读这一位**，而不是去遍历原作那个 8 槽数组，
  所以在这里置位/清位与「数组里有没有它」**产生的可观察效果完全等价**。
* 数组槽位与 `e[0x16c4]` 记下来的索引在端口没有消费者，**如实记录为未建模**。

**又抓到一处 th11 数字残留**：端口原来把 `0x19c` 和 `0x1ac/0x1af/0x1b1` 并成一组，
当作 **th11 的激光生成**——th12 的 0x19c 与此毫无关系。本轮把它从那一组拆出来单独实现。

**还有一次「自己抓自己」**：我第一版 412 的注释写着 `manager+0x3c` 第 0 位「在端口没有消费者」——
这是我**没查就下的结论**。随后在端口里找到 `w.manager_flags`（`case 0x1ba` 操作的正是这一位），
于是补上了 `w.manager_flags&=~1u;` 并改正注释。**这是读端口发现的，不是测试发现的。**

### 33.2 425（0x1a9）：落地 → 闸门否决 → **回滚**

调度器 C 里 `case 0x1a9:` 只有一句 `FUN_00414c60()`，也就是「清除关卡敌机」，
端口已有 `EnemyManager::erase_stage_enemies`（0x159/0x173 用的同一句）。
于是本轮也把它实现了、并从碰撞名单里移除。**探针看起来「前进了」**：

> （未回滚时）stage 5: 4320 → 412 → 425 → **413**

**但这个「前进」是假的。** `th12-handler-routing.mjs` 立刻报错：

```
0x1a9: enemy_emitter_command runs first, EnemyStateCommands.cpp also handles it and never runs
FAIL: 1 opcode(s) are shadowed by a pre-chain handler
```

也就是说：端口的 `enemy_emitter_command` 是**前置闸门**（在调度链之前），
它**已经声明了 0x1a9**，而 th11 的语义是「设发射器数量/层数」。
我一旦把 425 从碰撞名单里放出来，**它就被那个错误的 th11 处理器接走了**——
探针只会告诉你「不再拒绝」，**不会告诉你「被谁处理了」**。

**所以本轮把它回滚了**：425 重新回到碰撞名单，`EnemyStateCommands.cpp` 里那个 case 删除。
这是本项目第一次**依据闸门证据回滚已完成的改动**——正是这套纪律存在的意义。

**留给下一轮的明确问题**：
th12 调度器说 0x1a9 = `FUN_00414c60`（清敌机），而端口的**前置**发射器路由声明了 0x1a9——
**两者不可能同时生效**。要判定，必须去读 **th12 自己那份发射器路由条件**
（端口的这份很可能是 th11 残留，就像本轮拆掉的 0x19c 一样）。在此之前 425 保持拒绝。

### 33.3 状态

| 关卡 | 本轮（12000 帧） |
| --- | --- |
| 1,2,3,4,6,7 | 跑满 |
| 5 | 4320 → **425**（412 已修好，链条推进到 425 为止） |

判决表：`collision` 30 → **28**，`implemented-collision` 16 → **18**。

### 33.4 证据

- 关卡探针 12000 帧：1/2/3/4/6/7 跑满，5 关 4320 → 425；
- `th12-*` 12/12；`build-sdl.mjs` exit 0（sha256 `b427c16c…`）；浏览器 `error=""`、**60 FPS**、`traps: 0`；
- **7 个闸门** exit 0（含回滚后重跑，以及重新生成的判决表）。
## 34. 本轮：查清 0x1a9 的真身（th12 根本没有独立的发射器命令函数），425 真正落地

### 34.1 第 32 轮留下的问题，用一次 grep 就定案了

问题：th12 调度器说 0x1a9 = `FUN_00414c60`（清关卡敌机），而端口的**前置**发射器闸门也声明了 0x1a9
——两者不可能同时生效。本轮直接在整棵反编译树里搜：

```
搜 `case 0x1a6:` → 只有 FUN_004154d0_004154d0.c
搜 `case 0x1a9:` → 只有 FUN_004154d0_004154d0.c
```

**th12 没有独立的发射器命令函数**：所有 opcode 的 body 都在**同一个调度器 switch** 里。
所以端口那个「前置发射器闸门」是 **th11 的架构**，
它对 0x1a9 的声明是一处 **th11 残留**——和第 32 轮拆掉的 0x19c 完全同一类。

### 34.2 425 这次是真的落地了（并且被两个闸门接力纠正）

正确做法不是「把 425 从碰撞名单里放出来」（第 32 轮的做法，已被否决），
而是**把这处 th11 残留从路由里拿掉**：

1. `EnemyEmitterCommands.cpp` **外层声明表**移除 `0x1a9`；
2. 同一个文件的**内层 switch** 也必须移除 `case 0x1a9:`
   ——**这一步我一开始漏了**，`th12-dispatch-gate.mjs` 立刻报：

   > `UNREACHABLE EnemyEmitterCommands.cpp: 1 of 23 inner cases are not released`
   > `missing from gate: 0x1a9`
   > 「一个没有任何东西释放或路由到它的 case，无论写得多对都等于没写。」

   （同组的 `0x1aa` 靠 `op==0x1aa` 自辨，所以拆开后它仍然正确。）
3. `EnemyStateCommands.cpp` 里重新加回 0x1a9 的实现（现在**可达**）；
4. 从碰撞名单移除 425。

结果：

| 闸门 | 结果 |
| --- | --- |
| `th12-handler-routing.mjs` | 发射器闸门 25 → **24**，遮蔽 **0**（第 32 轮是 1） |
| `th12-dispatch-gate.mjs` | 从失败（内层 case 无人释放）到 **exit 0** |

探针：stage 5 4320 → **413**。**与第 32 轮不同，这次的「前进」是合法的**
——路由闸门确认没有任何前置处理器抢走 0x1a9。

### 34.3 由此得到的**全局结论**（本轮最有价值的产出）

端口的前置闸门一共声明 **52 个** opcode（移动 28 + 发射器 24）。
既然 th12 只有单一调度器 switch、**没有前置分发**，那么：

* 这 52 个 opcode 走的都是**th11 派生的 body**；
* 当 th11 与 th12 恰好一致时，前置闸门**碰巧是对的**；
* 一旦不一致，就会出现**静默的语义错误**——这正是贯穿本项目的
  「th11 数字残留」bug 类的**总根源**（0x19c、0x1a9、0x192/0x193、0x196/0x197/0x198 …）。

**所以下一阶段最高价值的工作，是拿 th12 调度器的 body 逐个审计这 52 条**，
而不是继续一条条等探针撞上来。

### 34.4 下一条：413（0x19d）已经读出来了

```c
case 0x19d:
    goto switchD_00415546_caseD_19d;
...
switchD_00415546_caseD_19d:
    FUN_004067e0(0);
    goto switchD_00417c29_caseD_5;
```

是**两段复合**：先 `FUN_004067e0(0)`，再跳进**另一个调度器**
（`switchD_00417c29_caseD_5`，即 `0x417c29` 那一张表）的共享体。
端口现在的 0x19d 是 th11 的「无限激光」——又一处残留。
下一轮需要同时识别 `FUN_004067e0` 与那张二级表的分支。

### 34.5 证据

- 关卡探针 12000 帧：1/2/3/4/6/7 跑满，5 关 4320 → **413**；
- `th12-*` 12/12；`build-sdl.mjs` exit 0（sha256 `b7d04529…`）；浏览器 `error=""`、**59 FPS**、`traps: 0`；
- **7 个闸门** exit 0（判决表：`collision` 28 → **27**，`implemented-collision` 18 → **19**）。
## 35. 本轮：做前置残留审计工具 —— 它立刻揪出一个 241 次使用的**错实现**

### 35.1 新工具：`tools/th12-preechain-audit.mjs`

第 33 轮得出的结论是「前置闸门声明的 opcode 走的都是 th11 派生的 body，要逐个审计」。
本轮把它变成工具：读取移动/发射器两个闸门的声明表（用与路由闸门**同一份**括号匹配提取，
避免两个工具各自漂移），再对每个 opcode 附上 th12 调度器里的 case 地址、
共享该 body 的 opcode 数、判决表里的 verdict、以及链上是否有处理器，
**按 th12.dat 的实际使用次数排序**。

结果：

```
pre-chain claims: 52 opcodes (movement 28, emitter 24)
30 of 52 are used by th12.dat, total weight 4270 uses.
```

最重的几条全是发射器家族（0x1fd 870、0x1f8 673、0x1f6 312、0x1fb 239、0x1f9 233），
而这些**恰好是端口已经按 th12 重新推导过**的那批（`EnemyEmitterCommands.cpp` 注释里写着
「TH12 的发射器家族在 0x1f6..0x1fc，不是 TH11 的 0x194..0x19b」）。
真正危险的是**从没被重新推导过**的那些。

### 35.2 立刻命中：**0x130（241 次使用）是错的**

调度器里 `case 0x130:` 与 `0x132/0x148/0x14a` **共享同一段 body**：

```c
m = (op==0x130||op==0x148) ? e+0x68 : e+0x9c;      // absolute : relative
a0 = f(0); a1 = f(1);
if (a0 > -999999) {
    if ((e.flags & 0x40000) && (op==0x130||op==0x132))
        a0 = normalize(1.5707964 - normalize(a0 - 1.5707964));   // 瞄准翻转
    FUN_00408910(m, a0);                            // 角度写到 m+0x1c
}
m.flags &= ~3u;                                     // 清两个模式位
if (a1 > -999999) m.speed = a1;                     // +0x18
```

**而端口里 0x130 是 th11 的 `e.flags=(e.flags&~0x8000u)|((i(0)&1)<<15)`——一个标志位开关。**
本轮按调度器实现，并把 0x132/0x148/0x14a 一起补上：

* `implemented` 121 → **124**，`todo` 23 → **22**，`unused` 31 → **29**。

### 35.3 重要的方法论提醒：**修对了反而让探针「倒退」**

修好 0x130 之后：

| 关卡 | 修改前 | 修改后 |
| --- | --- | --- |
| 4 | **12000 帧跑满** | **1502 → 301（0x12d）** |

**旧的 12000 帧是错误行为换来的。** 探针只是**代理指标**：
「跑得更久」不等于「更接近原作」。反过来说，这次也**证明了 0x130 确实被执行到**
（否则执行路径不会改变）。

### 35.4 审计的第二个发现：**路由闸门有个探测盲区**

`th12-handler-routing.mjs` 的 `caseSet()` **只匹配 `case` 标签**，
而 `EnemyManager.cpp` 用的是 `if(op==0x159)` 风格 —— 于是该分支的 case 集合**永远是空集**。
也就是说：**管理器分支上如果真的存在遮蔽，这个闸门看不见。**

审计工具报出的两个「同时被前置声明又被链上处理器处理」的候选正是 0x118 与 0x149，
而闸门对此**毫无反应**。今天它们安全只是因为**两个都在碰撞名单里**（被拒绝，轮不到谁抢）——
**这是运气，不是检测**。

这正是本项目反复吃到的那个教训的又一例：
**「找不到东西的探测器不能证明任何事」**。下一轮要修 `caseSet`，让它也认 `op==0x…`。

### 35.5 下一轮

1. 修 `caseSet` 的盲区（并给闸门补一个能自证的用例）；
2. **301（0x12d，220 次使用）**：th12 case 地址 `0x4166d6`，与 0x12f 共享 body，
   判决表里是 `collision`（即被拒绝）——这是 0x130 修好后第 4 关的新阻塞点；
3. 继续按审计表推进：0x131（216 次）等。

### 35.6 证据

- 关卡探针 12000 帧：1/2/3/5(4320→413)/6/7，4 关 **1502 → 301**（见上，非退化而是修正）；
- `th12-*` 12/12；`build-sdl.mjs` exit 0（sha256 `bab6a24f…`）；浏览器 `error=""`、**61 FPS**、`traps: 0`；
- **7 个闸门** exit 0；判决表：`implemented` **124**、`todo` **22**、`unused` **29**。
## 36. 本轮：修好闸门盲区（它立刻推翻了我上一轮的说法），清掉两处**真实**遮蔽，并实现 413

### 36.1 闸门盲区修好之后，它马上**否证了我自己**

上轮我写「0x118/0x149 安全，因为都在碰撞名单里」——**这是错的**。
修好 `caseSet()`（现在也认 `op==0x…` 这种写法）后，闸门第一次给出：

```
of those, shadowing a routing branch: 2
  0x118: enemy_movement_command runs first, EnemyManager.cpp also handles it and never runs
  0x149: ... 同上
of those, shadowed but refused by kTh12CollidingOpcodes: 0      <-- 关键
FAIL: 2 opcode(s) are shadowed by a pre-chain handler
```

**`refused: 0`** —— 它们**根本不在**碰撞名单里。上轮我把判决表的 `implemented-collision`
层级误当成了 `kTh12CollidingOpcodes` 的成员。也就是说：**这两处遮蔽一直是活的**
（movement 处理器赢，manager 的代码永不执行）。

这正是本项目反复吃到的那个教训的最教科书案例：
**探测器根本不会响，那么它之前的沉默就不能证明任何事。**

### 36.2 两处遮蔽都用证据解决了（方向相反）

| opcode | th12 调度器 | 链上路由 | 结论 |
| --- | --- | --- | --- |
| **0x118** | `goto switchD_00415546_caseD_100`（0x100 家族） | 路由到 manager，且 `EnemyManager.cpp:115` 已把 0x118 放进 relative 列表 | **movement 闸门的声明是残留** → 从 `EnemyCommands.cpp` 移除 |
| **0x149** | 与 0x131/0x14b 共享**插值器** body | —— | movement 闸门里 `case 0x131:case 0x149:` 本来就是**对的** → **manager 的 `drop_items` 才是残留** → 移除 |

两点独立证据、方向相反，都说明「前置闸门是 th11 架构」这个结论要**逐条查**，不能整批处理。
另外给工具补了一条 manager 路由表达式的 needle——以前只有激光表达式有，
所以 `EnemyScript.cpp` 改了 manager 条件时工具会**静默用旧规则**。

结果：`movement gate: 31 → 30`，`shadowing: 0`，闸门 exit 0。

### 36.3 探针：一关变好，两关换了路径

| 关卡 | 上轮 | 本轮 |
| --- | --- | --- |
| 5 | 4320 → 413 | **12000 跑满**（实质改善） |
| 1 | 12000 | 2970 → 413 →（修 413 后）**2970 → 411** |
| 7 | 12000 | 1300 → 455 |

1/7 关是「换路」而不是「退化」——它们现在走进了本来就在的拒绝点。
探针是代理指标这一条，本轮再次成立。

### 36.4 413（0x19d）实现：**反编译器丢掉的指针，用反汇编找回来**

上轮我记成「`FUN_004067e0(0)` 然后跳进第二个调度器」——**后半句是错的**，
那个 `switchD_00417c29_caseD_5` 其实是**函数尾声**。反汇编一眼看清：

```
0x418963  push 0
0x418965  lea  eax, [ebx + 0x26c]      <-- 指针在这里
0x41896b  call 0x4067e0
0x418970  jmp  0x41962b                <-- 共享尾声（break）
```

而 `FUN_004067e0` **就是 `Timer::set`**（`in_EAX` 指到 owner+0x20 时：
`[0]`previous、`[1]`current、`[2]`fractional、`[3]`rate 指针、`[4]`flags；
先测 flags 的 bit0，再写默认 rate 指针，然后 previous=n-1、current=n、fractional=n）
——与端口 `Timer.hpp` 的 `Timer::set` **逐行对应**。

th12 的 `+0x26c` 在插值器家族位移 0x118 下映射到端口 **0x154**，
而 `EnemyState.hpp:61` 自己就写着 `static_assert(offsetof(EnemyState,lifetime)==0x154)` ——
**推断与文件里的断言独立吻合**。于是 413 = `e.lifetime.set(0,&g.environment.rate)`，
从 th11 的无限激光组（0x1ad/0x1b0/0x1b2）里拆出来，并从碰撞名单移除
（判决表 `collision` 27 → **26**，`implemented-collision` 19 → **20**）。

### 36.5 诚实交待：**浏览器现在会报错，而上一轮不会**

修好 0x118 之后，第 1 关脚本走的是**正确分支**，于是撞上碰撞名单里的拒绝点：

* 先撞 **413** —— 本轮已实现，现在前进到 **411**；
* 浏览器证据：`error="… -1001 ECL opcode 411"`，`traps: 0`，61 FPS。

**这不是新引入的缺陷，而是被掩盖的缺陷露出来了**：以前第 1 关走错分支，根本走不到这些点。
我不打算把 0x118 回滚去换一个绿灯——那样等于用错误行为买好看的数字。

### 36.6 下一轮的队列（碰撞名单成了主队列）

1. **411（0x19b，57 次使用）**：th12 case `0x417a4c`，第 1 关的新阻塞点；
2. **301（0x12d，220 次使用）**：`0x4166d6`，与 0x12f 共享，第 4 关；
3. **455（0x1c7）**：第 7 关。

这些**都是碰撞名单里的条目、而 th12.dat 确实在用**——把「有冲突就拒绝」换成
「按 th12 实现」，是接下来最直接的一条线。

### 36.7 证据

- 探针 12000 帧：1 关 2970→411、2/3/5/6 跑满、4 关 1502→301、7 关 1300→455；
- `th12-*` 12/12（本轮结束时重跑）；**7 个闸门** exit 0；
- `build-sdl.mjs` exit 0（sha256 `e06e18be…`）；浏览器 `traps: 0`、61 FPS、`error` 见 36.5。
## 37. 本轮：实现 301（0x12d）—— 第 4 关跑满 12000 帧，7 关里 6 关完整

### 37.1 301 的真身：**建立「位置」插值器**（而不是 th11 的角/半径/椭圆）

th12 里 `case 0x12d:` 与 `0x12f` **共享** body（exe 里 VA `0x4166d6`，body 结束 `0x416831`）：

```c
m = (op==0x12d) ? e+0x68 : e+0x9c            // absolute : relative Movement
p = (op==0x12d) ? e+0x28c : e+0x2d8          // absolute_position : relative_position
duration=i(0); mode=i(1); x=f(2); y=f(3);
if (duration < 1) { p.duration = 0; break; }        // 其它什么都不碰
p.duration=duration; p.mode=mode;
p.initial_tangent = p.final_tangent = DAT_004ce8d0/d4/d8;
p.start = m.position;                                // *p=m[0]; p[1]=m[1]; p[2]=m[2]
p.end   = ( x>-999999 ? x : m.position.x,
            y>-999999 ? y : m.position.y,
            0 );
m.flags &= ~3;
```

两个可直接落地的要点：

* **切线常量是 0**。`DAT_004ce8d0/d4/d8` 的地址在 `0x4ce8d0` 附近，
  而 `.data` 的 raw 只覆盖到 `0x4ada00` —— **落在零填充的虚拟尾部**，
  所以三个值都读作 `0.0`，就是普通线性插值。这是前面几轮 PE 事实的直接复用。
* 端口里**已经有同形状的正确实现**：`case 0x119`（`EnemyCommands.cpp:35`）就是
  `endpoints(p,m.position,{keep(x,…x),keep(y,…y),0});setup(p,duration,mode,rate);m.flags&=~1u;`。
  所以这次不是新发明，而是**把 301 改成和它的兄弟一样**。

端口的旧 body 是 th11 的「用 8 个参数建立角/半径/椭圆三个插值器」——**又是 th11 残留**。
补丁同时把 301 从碰撞名单移除（脚本先断言它**确实在**名单里，否则直接报错不猜）。

### 37.2 结果

| 关卡 | 上轮 | 本轮 |
| --- | --- | --- |
| **4** | 1502 → 301 | **12000 跑满** |
| 1 | 2970 → 411 | 2970 → 411 |
| 7 | 1300 → 455 | 1300 → 455 |
| 2/3/5/6 | 跑满 | 跑满 |

**7 关里有 6 关现在跑满 12000 帧。** 判决表：`collision` 26 → **25**，
`implemented-collision` 20 → **21**；7 个闸门 exit 0。

### 37.3 411（0x19b）读完了，但**没有实现**——原因写清楚

第 1 关（也就是浏览器那条路）的阻塞点是 411。它的 body 已经完整读出：

```c
case 0x19b:
  v = FUN_0041a900(0);                     // = i(0)
  e[0x1608] = v;  e[0x160c] = v;
  if (e.flags & 0x400000) {                // 同一个「投影/世界坐标」标志
      FUN_004126f0(0,0,0.0f); FUN_004126f0(1,0,0.0f);
      FUN_004126f0(2,0,0.0f); FUN_004126f0(3,0,0.0f);
  }
  e[0x1610] = e[0x1608];
  if (e.flags & 0x400000) e.flags |= 0x20000000;
  e[0x1614] = e[0x1608] * 7;
```

而 `FUN_004126f0(index, a, b)` 的真身（26 字节）：

```c
*(u32 *)(DAT_004b43e4 + 0x6cf8 + index*8) = b;
*(u32 *)(DAT_004b43e4 + 0x6cfc + index*8) = a;
```

即**玩家/游戏结构里一张 4 槽 × 8 字节的表**（`DAT_004b43e4` 就是 418 拆对话时用的同一个基址），
被 `flags & 0x400000` 保护着整体清零。

**但这里有两个我还不该猜的东西：**

1. `+0x1608/+0x160c/+0x1610/+0x1614` 映射到端口**哪个偏移**？
   按插值器家族位移 0x118 是 **0x14ec..0x14f8**，按尾部位移 0x11c（`script_owner` 用的那个，
   th12 `0x174c` → 端口 `0x1630`）是 **0x14f0..0x14fc** —— **差 4 字节，必须读端口自己的
   字段表来定**，不能掐指一算。
2. 端口在玩家侧**没有**这张 4 槽表的等价物，所以还要先弄清它到底是什么。

**所以本轮停在这里**，把证据全部记下来，下一轮第一件事就是它。
（顺带：浏览器加 `&stage=4` 没有用，仍旧报 411 —— 那个参数被忽略了，跑的还是第 1 关那条路。）

### 37.4 证据

- 探针 12000 帧：**2/3/4/5/6 跑满**，1 关 2970→411、7 关 1300→455；
- `th12-*` 12/12；**7 个闸门** exit 0；
- `build-sdl.mjs` exit 0（sha256 `42da586d…`）；
- 浏览器：`traps: 0`、60 FPS、`error="… -1001 ECL opcode 411"`（见 37.3，这是**已知且已定位**的阻塞）。
## 38. 本轮：实现 411 与 427 —— 第 1 关从 411 推进到 526

### 38.1 411 的两个未知，都用证据定了

**（一）四个字段是什么？** 不看反编译的算术，去看**消费者**。
`FUN_0041aba0` 正是读 `+0x1608` / `+0x160c` 的地方：

```c
piVar1[9] = (e[0x1608] * 5.8904862) / e[0x160c] + 0.3926991;
... 循环 0x1f = 31 次：
    FUN_0041c580(local_1c+2, local_24, (float)piVar1[0x11]);
    ...
    fVar5 = FUN_004646e0((float)piVar1[9] * 0.03125 + local_24);
```

`5.8904862 = 1.875π`、`0.3926991 = π/8`，配上**31 个点**的闭环，这就是一个**圆环/多边形**：
`+0x1608` 是**尺度**、`+0x160c` 是**边数**、`+0x1610` 是尺度的副本、`+0x1614` 是尺度的 7 倍。

**（二）`FUN_004126f0` 是什么？** 只有 26 字节：

```c
*(u32 *)(DAT_004b43e4 + 0x6cf8 + index*8) = b;
*(u32 *)(DAT_004b43e4 + 0x6cfc + index*8) = a;
```

即**游戏侧**（`DAT_004b43e4`，与 418 拆对话同一个基址）一张 **4 条 × (int,float)** 的表。
它在 `flags & 0x400000` 保护下被整体清零。**这是端口不拥有的游戏侧状态**——
和端口已经明确记录「不建模声音通道队列」是同一类。所以这里**如实记录、不臆造**。

于是 `case 0x19b` 落地为：写入四个 ring 字段 + 置 `flags |= 0x20000000`。
四个字段加在端口**自己的** `EnemyState` 末尾（`sizeof` 断言 0x1658 → 0x1668、
`sizeof(Enemy)` 0x2694 → 0x26a4 同步更新）——因为端口的断言是**它自己的布局**，不是 th12 地址。

### 38.2 路由闸门又一次抓到残留

把 411 移出碰撞名单后，路由闸门**立刻 exit 1**：**发射器闸门也声明了 0x19b**，
于是它抢在新实现前面。而 th12 的调度器给 0x19b 的是圆环描述符，**不是发射器 body**——
所以这处声明又是 th11 残留（和第 33 轮确立、33–35 轮陆续清掉的是同一类），标签移除。

### 38.3 顺手发现的两个「尸体」，其中一个暴露了新的探测盲区

* 发射器文件里的 `if(op==0x19b){...}`（th11 的「仅复制发射器、会静默保留旧 offset/origin」那段）
  在外层声明移除后**已经永远不可能执行**。
* **`th12-dispatch-gate.mjs` 看不见它**——因为它遍历的是 `case` 标签，而这是一条 `if`。
  **和第 35 轮路由闸门那个盲区是同一种形状**，已记录，下一轮要把这类 `if` 也纳入检查。
* 还有一段**陈旧注释**仍写着「0x19b 在 kTh12CollidingOpcodes 里」，一并改正。

### 38.4 427（0x1ab）只需要「离开名单」，不需要新代码

th12 的 `case 0x1ab` 只做一件事：往**同一张游戏侧表**写一条
（`table[i(0)] = (i(2), f(1)/ring_sides)`），别无其它。而发射器闸门**本来就声明了 0x1ab**，
内层 switch 里**没有**它的 case，于是自然落到函数末尾的 `return true`（no-op）——
**这恰好就是正确行为**。所以 427 只需移出碰撞名单，另加一段注释说明为什么它是**有意**的 no-op。

### 38.5 结果

| 项 | 变化 |
| --- | --- |
| 第 1 关 | 411 → **427 → 526** |
| 判决表 | `collision` 25 → **23**，`implemented-collision` 21 → **23** |
| 7 个闸门 | 全部 exit 0 |
| 浏览器 | 阻塞点从 411 前进到 **526**（且 526 是**未实现的 todo**，不再是「碰撞即拒绝」） |

### 38.6 教训（工具层面）

本轮有三段补丁脚本**在写入前抛错**，等于什么都没改（好在构建产物与上一状态一致，
没有产出半成品）。原因都是锚点写得比实际文件"整齐"——注释被我当成相邻两行、
`if(op==0x1ab){` 压根不存在。**修法已经固定下来：全部改动在内存里做,
校验通过后一次性写盘**，失败就什么都不落地。这条要一直用下去。

### 38.7 下一轮

1. **526（0x20e，16 次使用）**：第 1 关新阻塞点，`todo` 类，需要真正实现；
2. **455（0x1c7）**：第 7 关；
3. 把 `if(op==…)` 也纳入 dispatch 闸门的「无人释放」检查（38.3 的盲区）。

### 38.8 证据

- 探针 12000 帧：2/3/4/5/6 跑满，1 关 2970→526、7 关 1300→455；
- `th12-*` 待本轮结束重跑；`build-sdl.mjs` exit 0（sha256 `ba5dace1…`）；
- 浏览器：`traps: 0`、59 FPS、`error="… ECL opcode 526"`。
## 39. 本轮：实现 526 —— 第 1 关从 526 推进到 424，并**更正上一轮的一处误判**

### 39.1 526（0x20e）：又一处「端口自己已经声明过」的效果系统缺口

th12 的 `case 0x20e`：

```c
if (e[0x1750]) FUN_00402f20();          // 销毁上一实例
e[0x1750] = 0;
e[0x1754] = f(0);                       // 持续时间
e[0x1758] = 0x41800000;                 // 固定 16.0f 缩放
e[0x175c] = i(1);                       // 精灵/效果 id
FUN_004061b0(e+0x1760, 0.0f); FUN_004061b0(e+0x1764, 0.0f);   // Vec2 清零
if (e[0x1754] > 0) e[0x1750] = FUN_0040ff10(0x11);            // 工厂 id 0x11 建 18 字节实例
```

关键点是：**端口自己早就声明过这个缺口**。`EnemyStateCommands.cpp:132` 写着

> 「+0x430/+0x434/+0x438 - a visual effect instance. **This port has no effect system to
> spawn into: there is no Effect or Particle type anywhere under …**」

这正是 526 的情形。所以本轮**沿用端口对 0x1c6 已有的处置**：把引擎存下来的每个参数都留下，
**不为实例发明渲染器**。字段加在端口自己的 `EnemyState` 末尾
（`effect_active / effect_duration / effect_scale / effect_id / effect_position`），
`sizeof` 断言同步 0x1668 → **0x1680**、0x2694 → **0x26bc**。

结果：`implemented` 124 → **125**，`todo` 22 → **21**；第 1 关从 526 推进到 **424**。

（附带确认：0x20e **不在**碰撞名单里——脚本先断言再决定，没有想当然。）

### 39.2 424（0x1a8）读完了，同样先不动手

```c
case 0x1a8: FUN_0041c550(i(0)); break;
```

而 `FUN_0041c550` 只有 19 字节：

```c
old = obj[0x78];  obj[0x78] = arg;  if (old != arg) obj[0x80] = 0;
```

`in_EAX` 是调用者在寄存器里传的对象指针（反编译器又把它丢了，和 413 一样）。
**但这次端口自己的断言就够定位**：`EclOwner::program==0x102c`、`threads==0x1030`，
所以 `+0x78` 落在 **`EclContext root` 内部**（即 `EclContext+0x68`），**根本不是发射器**。

而且**端口现在的 `case 0x1a8` 是一段发射器速度体**
（`b.speed=(d-a)*r/2048+a`）——**又是一处残留**：th12 的 0x1a8 完全不碰发射器。
所以 424 要先弄清 `EclContext+0x68/+0x70` 的含义，记入下一轮。

### 39.3 更正：上一轮我对 dispatch 闸门的判断是**错的**

第 38 轮我写「`th12-dispatch-gate.mjs` 看不见那条死在 `if(op==0x19b)` 里的 body，
因为它遍历的是 `case` 标签」。**这个归因不成立。** 本轮读了闸门源码：

* 它**本来就**会把外层 gate 与内层 switch **之间**出现的 `if(op==0x..)` 记为
  「已释放」（第 16 轮为发射器那两个双输入拷贝加的，源码注释里写着）；
* 所以那条死 body 之所以没被报，是因为**它的 opcode 已经离开了 gate**，
  闸门根本没有东西可以拿来比对 —— 这是**超出它的检查范围**，不是它的盲区。

我真正需要的是一个**新的**检查：**命令文件里任何 `if(op==0xNN){…}` 实现体，
如果它的 opcode 不在该文件的 gate 里，就是一条孤体（orphan body）**。
这才是能抓住 0x19b 那类情形的检查，记入下一轮。

### 39.4 证据

- 探针 12000 帧：2/3/4/5/6 跑满，1 关 2970→424，7 关 1300→455；
- `th12-*` 12/12；**7 个闸门** exit 0；
- `build-sdl.mjs` exit 0（sha256 `f9730348…`）；浏览器 `traps: 0`、60 FPS、
  `error="… ECL opcode 424"`（阻塞点已从 526 前进到 424）。
## 40. 本轮：实现 424 + 新增「孤体」探测器（并先把它证伪）

### 40.1 424：反汇编是决定性的——它**根本不碰敌人**

```
xor  ecx,ecx
mov  eax,ebx          ; ebx 是敌人……然后再也没被用过
call 0x41a900         ; i(0)
mov  ecx,eax          ; __fastcall 的实参
mov  eax,0x4b0c40     ; ← 一个**全局**结构体的基址，不是敌人
call 0x41c550
```

`FUN_0041c550` 只有 19 字节：`old = g[0x78]; g[0x78] = arg; if (old != arg) g[0x80] = 0;`。

`DAT_004b0c40` 在**四处**被当作**滑动最大值**维护
（`FUN_00420e70` / `FUN_00421cd0` / `FUN_00431b30` 都是 `if (DAT_004b0c40 < x) DAT_004b0c40 = x;`），
并被 `0x41f040 / 0x41fcc0 / 0x420e70 / 0x421cd0 / 0x425c20 / 0x431b30` 这一族写入。
**这是端口不建模的游戏侧状态**——和 411 清的那张表、427 写的那张表同一类。
所以 424 与 427 同样处置：移出碰撞名单，**如实记录、不臆造**。

同时处理掉一处 th11 残留：发射器文件里原来的 `case 0x1a8` 是一段**发射器速度体**
（`b.speed=(d-a)*r/2048+a`），而 th12 的 0x1a8 **完全不碰发射器**，故随声明一并删除。

### 40.2 一个我亲自踩到的陷阱：`implemented-collision` **不代表有人处理**

把 424 移出名单后，判决表写的是 `implemented-collision`，可**探针依旧卡在 424**。
去读 `tools/th12-opcode-map.mjs:135` 才看清：

```js
collision ? (refused.has(id) ? 'collision' : 'implemented-collision') : ...
```

即 **`implemented-collision` 的含义是「th12 里是碰撞 + 端口的名单不再拒绝它」**，
**完全没说有任何代码处理它**。而且 `refused` 就是那份**名单**，不是运行时行为。
所以：**判决表的计数描述的是名单，只有探针才反映真正的拒绝**。
这正是「探针只能说『不再被拒绝』」那条纪律的延伸——名单连这句都做不到。

结论：**no-op 必须显式写出来**——链条的兜底会拒绝任何没有 case 的 opcode。
补上 `case 0x1a8:break;` 之后，第 1 关 2970 → **2971** 帧，阻塞点 424 → **423**。

### 40.3 新增探测器：`tools/th12-orphan-bodies.mjs`（孤体）

这是第 39 轮更正里说「真正需要的那个检查」：

> **命令文件里任何 `if(op==0xNN){…}` 实现体，如果该文件的**任何** gate 都没有声明这个 opcode，
> 它就永远不可能执行。**

判据刻意保守，以免误报：只检查**有 gate 形状 `switch(op)`**（体里只有标签、`break` 和
`default:return false;`）的文件，没有这种 gate 的文件直接跳过；只有当**没有任何 gate** 声明该 opcode
才报。gate 已声明的 `if` 体是正常接线，不报。

**先证伪，再相信**（这是纪律，不是客套）：
* 干净树上：`command files with a gate: 1, without: 10, if-bodies seen: 1` → **0 条，exit 0**；
* **种一个诱饵** `if(op==0x999)` 后：`ORPHAN EnemyEmitterCommands.cpp:149: if(op==0x999) is unreachable…`
  → **exit 1**，说明它**真的会响**；
* 移除诱饵后：回到 **0 条，exit 0**，说明它**不误报**。

「找不到东西的探测器什么都没证明」——现在它两件事都证明了。

### 40.4 结果与证据

| 项 | 变化 |
| --- | --- |
| 第 1 关 | 2970 → **2971** 帧，阻塞点 424 → **423** |
| 判决表 | `collision` 23 → **22**，`implemented-collision` 23 → **24**（含义见 40.2：**少了一条被名单拒绝的**） |
| 闸门 | **8 个**全部 exit 0（新增 `th12-orphan-bodies.mjs`） |
| 测试 | 12/12 |
| 浏览器 | `traps: 0`、60 FPS、`error="… ECL opcode 423"` |

`build-sdl.mjs` exit 0（sha256 `dee8d5a4…`）。探针：2/3/4/5/6 跑满，7 关 1300→455。

### 40.5 下一轮

1. **423（0x1a7）** 及其后的 422 / 419 / 417 / 415 …（碰撞名单余 **22** 条）；
2. **455（0x1c7）**：第 7 关；
3. 余下 **21** 条 `todo`。
## 41. 本轮：实现 422/423（一对 load/unload），并**从 exe 里读出** 529 家族的回调表

### 41.1 422/423 是一对：围绕**游戏侧加载器全局**的装载与卸载

**422（0x1a6）**的 body 与 **428、437、438、439** 共用
（`th12-case-body.py` 报 `shared with opcodes [422, 428, 437, 438, 439]`）：

```
0x41887c..0x4188d3  把指令里的一段字符串**异或解密**到栈缓冲：
                    cl 初值 0x77，每字节先 +7，之后 +0x10
0x4188e5..          按 opcode 取偏移：437/438/439 → DAT_004b0ca8 的 +0 / -1 / -2
0x418918..          FUN_00468e20(…,2)、FUN_00468e20(…,1)、FUN_0040e060(名, …)
                    —— FUN_0040e060 是 1359 字节的**加载器**，把名字装进全局 DAT_004b43cc
结尾                +0x161c |= 1；+0x1614 = +0x1608 * 7；**落进 413**
```

关键细节：422 的 body **结束于 0x418963**，而 **413 的 case VA 正是 0x418963** ——
所以它**直接落进 413 的生命周期重置**。

**423（0x1a7）**是卸载半边：`FUN_0040e5e0`（321 字节）拆掉同一个全局，再清掉 `+0x161c` 的 bit 0。

字符串解密与加载器是**宿主侧**的：端口在启动前就把资源载入，没有 `DAT_004b43cc` 对应物，
所以**如实记录、不重造**。**是敌人状态的照旧保留**：新的 `ring_flags` 的 bit 0、圆环步长、
以及落进 413 的生命周期重置。发射器里原来的 `case 0x1a6:case 0x1a7`
（`b.speed=f(rank_pair(...))`）是 th11 残留，随声明删除。

结果：`collision` 22 → **20**，`implemented-collision` 24 → **26**；
第 1 关从 2971 帧前进到 **529**——顺带说明 **415/417/419 在这里并不构成阻塞**。

### 41.2 529/530/531/534：一个**函数指针表**家族，表内容直接从 exe 读出

```c
case 0x211: e[0x1768] = DAT_004af0fc[i(0)];   // 存入一个回调
case 0x212: e[0x176c] = DAT_004af118[i(0)];
case 0x213: e[0x1770] = DAT_004af120[i(0)];
case 0x216: DAT_004af0fc[i(0)]();             // 调用
```

把这些表**直接从 `th12.exe` 读出来**（只读，绝不入库；`va2off(0x4af0fc)`）：

| 表 | 条目 |
| --- | --- |
| `0x4af0fc`（7 条） | `0` · `0x41aa70` · `0x41b5f0` · `0x41b740` · `0x41bb40` · `0x41bd20` · `0x41bf50` |
| `0x4af118`（2 条） | `0` · **`0x41aba0`** |
| `0x4af120`（2 条） | `0` · `0x41b4d0` |

**这张表把第 37 轮的 411 闭环了**：`0x41aba0` 正是我那时通过消费者认出来的
**圆环渲染器**。于是整条链是：

* **411** 写圆环描述符（scale / sides / 副本 / ×7）；
* **530（0x212）** 把**圆环渲染器 `0x41aba0`** 选为该敌人的回调；
* **534（0x216）** 调用回调。

即**数据驱动的渲染管线**。529（0x211，70 次使用）是第 1 关当前的阻塞点，531（0x213）在 `todo` 里。

### 41.3 证据

- 探针 12000 帧：2/3/4/5/6 跑满，1 关 2971→**529**，7 关 1300→455；
- `th12-*` **12/12**；**8 个闸门**全部 exit 0；
- `build-sdl.mjs` exit 0（sha256 `660590f9…`）；
- 浏览器 `traps: 0`、61 FPS、`error="… ECL opcode 529"`。

### 41.4 下一轮

1. 用读出来的表条目实现 **529/530/531**（回调选择）与 **534**（回调调用）；
2. **455（0x1c7）**：第 7 关；
3. 碰撞名单余 **20** 条、`todo` 余 **20** 条（529 落地后）。
## 42. 本轮：实现回调家族 529/530/531/534；并记录一次**部分写入**

### 42.1 反汇编定下了 534 的实参

反编译器把 534 写成 `(**(code **)(&DAT_004af0fc + n*4))();`——**看不出实参**。反汇编补上：

```
534 (0x216): eax = i(0); edx = DAT_004af0fc[eax]; ecx = ebx（敌人）; call edx
530 (0x212): eax = i(0); e[0x176c] = DAT_004af118[eax]
531 (0x213): eax = i(0); e[0x1770] = DAT_004af120[eax]
```

即**回调以敌人为实参**（`__fastcall` 约定，实参在 ECX；函数开头那个 `mov eax,ebx` 会被
`FUN_0041a900` 覆盖掉，是无关的）。529 同形，写入 `e[0x1768]`。

### 42.2 实现

* **529/530/531** 三个槽存**被选中的下标**（th12 存的是函数指针，指针在 wasm 里没有意义）；
  表内容写进代码注释，供将来的渲染器派发：`0x4af0fc` 七条（`0, 0x41aa70, 0x41b5f0, 0x41b740,
  0x41bb40, 0x41bd20, 0x41bf50`）、`0x4af118` 两条（`0, 0x41aba0`）、`0x4af120` 两条（`0, 0x41b4d0`）。
* **534 = 有意的 no-op**：那些回调画的是自定义几何（`FUN_0041aba0` 画的就是 31 点闭环），
  端口没有可落笔的**敌人效果实例系统**——0x1c6 与 526 已记录过的同一缺口。
* 下标越界用 `__builtin_trap()` 守（与端口既有的发射器拷贝写法一致）：坏下标是**响亮的陷阱**，
  而不是静默越界。
* **留给将来**：渲染器按这三个下标派发即可，`callbacks[1]==1` 就是圆环渲染器，
  而它要读的描述符 **411 已经保留**（`ring_scale / ring_sides / ring_saved / ring_step`）。

### 42.3 结果

| 项 | 变化 |
| --- | --- |
| 判决表 | `implemented` 125 → **129**，`todo` 21 → **18**，`unused` 29 → **28** |
| 第 1 关 | 2971 帧 → **445**（0x1bd，碰撞名单内的条目） |
| 闸门 | 8 个全部 exit 0；`th12-*` 12/12 |
| 浏览器 | `traps: 0`、61 FPS、`error="… ECL opcode 445"` |

### 42.4 一次**部分写入**：我的规则漏了半条

补丁脚本在**最后一行**断言 `529 was not in the collision list` 时抛错——
因为我**想当然**以为 529–534 在碰撞名单里，其实它们是 `todo`，**根本不需要移出名单**。
问题在于：抛出时**前面两个文件的写入已经落盘**了。

这正是第 37 轮定下的「改动在内存里做、最后一次性写盘」想防的失败模式，
而我把它实现成了「逐个文件写下去」。**规则要补完整**：

> 不只是「最后写一次」，而是**在第一次写入之前**校验**每一个**输入与锚点。

第 37 轮那次侥幸什么都没留下（抛错在所有写入之前）；这次留下的是**本来就要的改动**，
所以无害；但下一次未必。**故本轮没有相信脚本**，而是**逐项手工核对落地状态**：
四个 case 都在（第 375–381 行），碰撞名单与上一轮**逐字节一致**（没有多余移出），
再重跑构建 / 闸门 / 探针 / 测试 / 浏览器确认。

### 42.5 下一轮

1. **445（0x1bd）**：第 1 关新阻塞点，碰撞名单内；
2. **455（0x1c7）**：第 7 关；
3. 碰撞名单余 **20** 条、`todo` 余 **18** 条。
## 43. 本轮：实现 445 —— 并且「先校验后写」这条规则当场救回一个真漏

### 43.1 445（0x1bd）真正是什么：一次全局扫描

它只有三个字节：`call 0x428670`（没有 `FUN_0041a900`，**不读任何实参**）。被调的是 121 字节的
`FUN_00428670`：

```c
for (obj = *(DAT_004b44f4 + 0x18); obj != 0; obj = obj[2]) {
    if (!(obj[0x112] & 1)) { obj[0x110]=0; obj[0x10f]=0; obj[0x10e]=-999999;
                             obj[0x111]=&DAT_004b2ed0; obj[0x112]|=1; }
    obj[0x110]=0; obj[0x10f]=0; obj[0x10e]=-1; obj[0x113]=0;
    (*obj->vtbl[0x14])(1, 0);
}
```

字下标 `0x10e..0x113` 就是字节偏移 **0x438..0x44c**——**正是**端口自己在 0x1c6 处已命名的
「visual effect instance」字段；而 `&DAT_004b2ed0` 也正是 `FUN_0040e060` 装进去的那个哨兵值。
**两处彼此独立的证据对上了同一个布局。** 所以 445 = 「重置**每个**敌人的效果实例，并用
虚表槽 5 通知它（1,0）」；端口没有这套敌人效果实例系统 → **有意的 no-op**，证据留在注释里。

### 43.2 「先校验、后写入」当场抓住一个我本来会掩盖掉的漏

第一版补丁在 `case 0x1bd already present` 上抛错——**发生在任何写入之前**，
所以树**原封不动**（判决表、探针、构建产物都和上一轮一致，我逐一核对了）。

而它暴露的事实是：**445 根本不是「没实现」**。端口原有的 `case 0x1bd` 做的是

```cpp
case 0x1bd:{const i32 id=i(0); if(u32(id)>u32(EnemyCollision::Arc))return -2;
            e.collision_callback=EnemyCollision(id);break;}
```

可 th12 的 0x1bd **不读任何实参**（反编译里没有 `FUN_0041a900`，反汇编就是一条裸 `call`），
所以这段 body 带着一个 **TH11 的 opcode 编号**——和发射器里那些残留同一类。

**第 41 轮补上的那半条规则在这里发挥了作用**：如果我只写不查，就会直接覆盖掉它，
而且**永远不会注意到**「这里本来就有一个 case」。

### 43.3 我拒绝猜的那一步

覆盖它之后，**「th12 到底在哪里设置 collision callback」就成了一个悬空的问题**。
我把它**显式记录下来**，而不是顺手改个号糊过去：`0x1bc`（444）不在碰撞名单里，**可能就是**
真正的设置点，但那需要证据，留给下一轮。

### 43.4 结果

| 项 | 变化 |
| --- | --- |
| 判决表 | `collision` 20 → **19**，`implemented-collision` 26 → **27** |
| 第 1 关 | 2971 帧 → **409** |
| 闸门 / 测试 | 8 个全 exit 0；12/12 |
| 浏览器 | `traps: 0`、60 FPS、`error="… ECL opcode 409"` |

`build-sdl.mjs` exit 0（sha256 `daa9a24d…`）。

### 43.5 交给下一轮的 409（0x199）：先排除一个已知的错位

端口现在的 `EnemyEmitterCommands.cpp:66` 是把 `i(1)` 当发射器槽、写 `b.transforms[slot]`
（子弹变换）——但这**不是** th12 的 0x199。同一文件第 93 行的注释已经写明：

> 「TH12's **0x1fd** is TH11's **0x199** field for field」

也就是说端口**自己就知道**子弹变换设置器在 th12 里是 **0x1fd（509）**。所以它的 `case 0x199`
是一段**按 th11 编号映射过来的** body，th12 的 **409 需要单独解码**。下一轮从这条线索开始。

### 43.6 下一轮

1. **409（0x199，61 次使用）**：第 1 关新阻塞点，碰撞名单内，先按 43.5 排除错位；
2. **455（0x1c7）**：第 7 关；
3. 悬空问题：th12 在哪里设置 collision callback（候选 444）；
4. 碰撞名单余 **19** 条、`todo` 余 **18** 条。
## 44. 本轮：实现 409；且「先校验」两次拒写，第二次教了我一件事

### 44.1 409（0x199）：一个四元数组的第 0 槽卸载

body 只有五条指令：

```
lea eax,[ebx+0x34] ; lea esi,[ebx+0x1620] ; call 0x412100
```

`FUN_00412100`（52 字节）：

```c
if (e[0x1620] != 0) FUN_004273f0(e+0x34, &e[0x1620], *(&e[0x1620]), e+0x34, -1.5707964, 2.2);
FUN_00412140(&e[0x1620]);
e[0x1620] = 0;
```

**邻位把这个数组说清楚了**：

| opcode | body |
| --- | --- |
| **407（0x197）** | `e[0x1620 + i(0)*4] = i(1)` —— 填充 |
| **408（0x198）** | `e[0x1670] = f(0)`；`e[0x1674] = f(1)` |
| **409（0x199）** | 卸载第 0 槽 |
| **410（0x19a）** | `e[0x1620] = i(0)` |
| 406（0x196） | `memset(e+0x1624, 0, 0x4c)` |

于是 `+0x1620` 是**四元 id 数组**，其后 `+0x1624` 起还有 `0x4c` 字节的块。
`FUN_004273f0` 有 **1798 字节**，按存下来的值分派（`param_3 == 9`、`10..15`、`0x10..0x12`），
落进**与 445 那次扫描同一族**的管理器（`DAT_004b44f0` / `DAT_004b44f4`）——
所以槽里存的是**效果/使魔 id**；`FUN_00412140`（451 字节）用随机散布把它摘下来。

即 **409 = 卸载第 0 槽**。卸载是宿主侧的（0x1c6 / 526 / 534 / 445 已记录的同一缺口），
端口**保留引擎自己的数据**：新增 `effect_ids[4]`（与 411 保留圆环字段、526 保留效果参数同一政策），
并把第 0 槽清零。

### 44.2 两次拒写：第二次教了我「断言要好，定位器更要好」

第一版补丁在 `case 0x1fd is not the transform setter` 上**拒写** → **树原封不动**。
随后 grep 查明：`case 0x1fd`（第 100 行）**确实**带着一段与 0x199 **逐字节相同**的 transform body，
文件注释也明确写着这条映射。**问题出在我的定位器**：注释块里也出现了 `0x1fd` 字样，
`find(l => l.includes('case 0x1fd:'))` 先匹配到了**注释行**，于是断言是拿**散文**在跟**代码**比。

改成匹配 **case 行本身**（`trimStart().startsWith('case 0x1fd:')`）后通过。

**教训**：写入前的断言，其价值取决于**定位器**。「grep 一行里含 X」可能命中**注释**，
于是产生**假拒写**（无害，本轮就是）；但更糟的是可能产生**假通过**——如果它匹配到的是**别的** body。
**凡是守着「删除」动作的断言，必须定位到那个确切的构造，而不是任何提到它的地方。**

这枚断言的价值也在此：没有它，补丁就会删掉一段本应先在别处确认存在的 body；
这次「别处确实存在」是**被这条断言证明的**，不是被假设的。

### 44.3 结果

| 项 | 变化 |
| --- | --- |
| 判决表 | `collision` 19 → **18**，`implemented-collision` 27 → **28** |
| 第 1 关 | 2971 帧 → **415** |
| 闸门 | 8 个全 exit 0 |
| 浏览器 | `traps: 0`、59 FPS、`error="… ECL opcode 415"` |

`build-sdl.mjs` exit 0（sha256 `a0bd8611…`）。

### 44.4 下一轮：415（0x19f）

现有笔记已提示：发射器文件里的 `0x19f..0x1a3` 一组，**0x19f / 0x1a1 / 0x1a3 是 th11 独有的**——
所以 415 很可能又是**同一种残留**。下一轮先按这个假设去**证伪**，再决定是实现 th12 的 415 还是替换残留。

其余：**455（0x1c7）** 第 7 关；悬空的 collision callback 问题（候选 444）；
碰撞名单余 **18** 条、`todo` 余 **18** 条。

## 45. 本轮：实现 415；以及「定位器」第三次咬我、和一次真正让构建变红的放置错误

### 45.1 415（0x19f）不是残留，是一条真指令

反汇编：

```
call 0x41a900          ; i(0)
push eax
lea  eax,[ebx+0x1690]  ; 敌人 +0x1690 处的计时器
call 0x4067e0          ; FUN_004067e0 = Timer::set（与 413 调用的是同一个函数）
```

即 **415 = `Timer::set(e+0x1690, i(0))`**，一次普通的计时器重置。
端口原来的 `case 0x19f` 与 **TH11 独有的 `0x1a1`/`0x1a3`** 同组，本轮把它**拆出来**单列。
新字段命名为 **`timer_1690`（按偏移命名）**——因为「th12 拿这个计时器做什么」**尚未确定**，
宁可记下偏移，也不给它编一个语义。

### 45.2 定位器第三次咬我，而且这次的 `includes` 命中的是**真代码**

`l.includes('op==0x19f')` 命中了第 88 行的**复合条件**：

```cpp
if(op==0x19e||op==0x19f){const float y=f(2),x=f(1);const Vec3 value{x,y,0};
    if(op==0x19e)b->position=value;else std::memcpy(...b+si...);}
```

那是一段**真的 TH11 残留**（往子弹里写位置）。所以断言**在精神上是对的、在措辞上是错的**
（它报的是「已经显式处理」，实际是「被一段残留占着」）。
**这是「整文件 includes」第三次定位错构造**（42 轮命中真实 case、43 轮命中注释、本轮命中复合条件）。

第二版修复脚本又**拒写**一次，这次是因为我把 `switch(op){` 的**缩进写成了 6 个空格**，
而文件里是 4 个。于是又多一条同类教训：

> **定位要按结构（`trimStart().startsWith(...)`）或不含缩进的内容做，
> 绝不能凭记忆写死一个列位。** 连「精确字符串」也只和它假设的空白一样可靠。

### 45.3 一次真正让构建变红的放置错误：静态校验管不了作用域

我第一版补丁把 415 的处理插在

```cpp
const u16 op=c.instruction->opcode;if(!w.lasers)return -2;auto& lasers=*w.lasers;
```

**这一行之前**——可 `op` 就声明在**这一行上**，`i` lambda 在下一行。于是构建报
`use of undeclared identifier 'op' / 'i'`。

「放在守卫之前」不可能按字面实现，因为声明和守卫**在同一行**。修法保持了原意、换了形式：
**把那一行拆开**——先声明 `op`，再声明 `i`/`f`/`origin`，然后处理 415，**最后**才做激光守卫；
`lasers` 只在后面的 switch 里用，所以守卫下移不改变别的行为。

**过程要如实记**：畸形版本**确实一度在树里、构建**确实**是红的。我**没有提交它**；
修复脚本两次「先校验后写」都拒写（都没落盘）。但要点在于：

> **「先校验后写」管得住文本，管不了语义。** 校验能证明锚点对、构造对，
> 但证明不了**声明的作用域**。**构建才是语义闸门**——它在本轮先于任何提交跑过了。

另外，第 88 行那个 `op==0x19f` 分支现在**不可达**了。我**留着没清**：它的 `0x19e` 分支属于
**414**，而 414 **不在**碰撞名单里，在没有证据的情况下动它就可能回归 414。

### 45.4 结果

| 项 | 变化 |
| --- | --- |
| 判决表 | `collision` 18 → **17**，`implemented-collision` 28 → **29** |
| 第 1 关 | 2971 帧 → **404** |
| 闸门 / 测试 | 8 个全 exit 0；12/12 |
| 浏览器 | `traps: 0`、60 FPS、`error="… ECL opcode 404"` |

`build-sdl.mjs` exit 0（sha256 `7954181a…`）。

### 45.5 下一轮：404（0x194）

现成线索有两条：一是发射器文件的 claim 列表里**就有 `0x194`**（同一种「占用」形态）；
二是该文件自己的注释已经写明：

> 「TH11's **0x194**, which set **angle and spread**, is a different instruction and **stays where it is**」

所以 404 很可能又是「端口按 th11 编号占着位置」的形态——**先按此假设去证伪**，
再决定是实现 th12 的 404 还是替换残留。

其余：**455（0x1c7）** 第 7 关；悬空的 collision callback 问题（候选 444）；
碰撞名单余 **17** 条、`todo` 余 **18** 条。

## 46. 本轮：实现 404；**浏览器第一次不再报错**

### 46.1 404（0x194）：一个标志位 + 四个浮点

反汇编与反编译一致：

```
or  dword ptr [ebx+0x16b8], 0x10000
f(0) -> [ebx+0x15f4] ; f(1) -> [ebx+0x15f8] ; f(2) -> [ebx+0x15fc] ; f(3) -> [ebx+0x1600]
```

而 **405（0x195）= `flags &= ~0x10000`**，正好是配对的那一半。

> 顺带一条值得记住的读反编译经验：decompiler 里的 `1.4013e-45`、`2.8026e-45`、`4.2039e-45`
> **不是常量**，而是 `ecx` 里那几个小整数 **1、2、3 的位模式**被当成了 float。
> 反汇编一读就明白：`mov eax,[esi+4]; xor ecx,ecx; call 0x468ec0`——`FUN_00468ec0` 是
> **取浮点实参**的函数（408 也用它），`ecx` 是**下标**。**反编译里的浮点字面量可能是寄存器值。**

端口原来的 `case 0x194:b.angle=f(1);b.spread=f(2)` 正是它**自己文件注释里点名的 TH11 残留**
（"TH11's 0x194, which set angle and spread, is a different instruction"）。本轮把它替换掉、
并从发射器 claim 列表里移除（于是路由落回主链）；**0x195 保持被 claim**——它仍在碰撞名单里，
是下一轮的目标。新字段按偏移命名为 `quad_15f4[4]`：「th12 拿这四个浮点做什么」**尚未确定**。

### 46.2 ★ 里程碑：浏览器不再报错

| 指标 | 本轮之前 | 本轮之后 |
| --- | --- | --- |
| 第 1 关 | 2971 帧后停在 404 | **跑满 12000 帧预算** |
| 第 2–6 关 | 跑满 | 跑满 |
| **浏览器** | `error="… ECL opcode 404"` | **`error=""`**、`traps: 0`、60 FPS |

这是本会话有测量记录以来，**第一次** th12 浏览器运行**没有**因为 ECL 指令被拒而中断。
第 7 关仍停在 **455**。

### 46.3 但这**不**等于「对了」

必须把话说清楚，这是本项目一贯的纪律：

> **探针只能说「不再被拒」，它说不出「是谁处理的」，更说不出「处理得对」。**

所以这是一次**可达性**里程碑，**不是保真度**里程碑：404 的四个浮点**存下来了，但端口里还没有
任何东西读它们**；`flags` 的 `0x10000` 位**置上了，其消费者尚未核实**；第 7 关仍在拒绝 455；
`todo` 仍有 **18** 条；主链里还带着 TH11 架构的残留。

**「浏览器跑起来了」≠「游戏是对的」。** 本轮的结论到此为止。

### 46.4 结果

| 项 | 变化 |
| --- | --- |
| 判决表 | `collision` 17 → **16**，`implemented-collision` 29 → **30** |
| 第 1 关 | 2971 帧 → **跑满 12000 帧** |
| 闸门 / 测试 | 8 个全 exit 0；12/12 |
| 浏览器 | **`error=""`**、`traps: 0`、60 FPS |

`build-sdl.mjs` exit 0（sha256 `ff10cb83…`）。

### 46.5 下一轮

1. **405（0x195）**：`flags &= ~0x10000`，与 404 配对的半个；注意它**仍被发射器 claim**，
   所以要连同 claim 标签一起搬到主链；
2. **455（0x1c7）**：第 7 关（1300 帧后）；
3. 悬空问题：th12 在哪里设置 collision callback（候选 444）；
4. 碰撞名单余 **16** 条、`todo` 余 **18** 条。

## 47. 本轮：实现 405；并**完整解开 455**，顺带发现端口已经有了它的一半

### 47.1 405（0x195）：与 404 配对的另半个标志位

反汇编与反编译**双双确认**，body 只有这一条：

```
0x00417567  and dword ptr [ebx + 0x16b8], 0xfffeffff
```

即 **`e.flags &= ~0x10000`**。端口原来的 `case 0x195:b.speed=f(1);b.slow_speed=f(2)`
是与 0x194 **同一类**的 TH11 残留，本轮**从 claim 行和内部 case 两处同时移除**，
于是路由落回主链、真 body 在链上生效。

至此**旗标对（404/405）与整个邻域**都已摸清：

| opcode | th12 body | 端口状态 |
| --- | --- | --- |
| 404（0x194） | `flags |= 0x10000`，`f(0..3)` → `+0x15f4..0x1600` | 已实现 |
| **405（0x195）** | `flags &= ~0x10000` | **本轮实现** |
| 406（0x196） | `memset(e+0x1624, 0, 0x4c)` | **解码，端口侧状态未核实** |
| 407（0x197） | `e[0x1620 + i(0)*4] = i(1)` | **解码，端口侧状态未核实** |
| 408（0x198） | `e[0x1670]=f(0)`；`e[0x1674]=f(1)` | **解码，端口侧状态未核实** |
| 409（0x199） | 卸载效果 id 数组第 0 槽 | 已实现 |
| 410（0x19a） | `e[0x1620] = i(0)` | **解码，端口侧状态未核实** |

（406/407/408/410 **不在**碰撞名单里，所以端口当前「自称」处理了它们——**这个自称需要核实**，
列为下一轮候选。）

### 47.2 455（0x1c7）完整解开：一次「存在性测试」写入脚本变量

三个此前身份不明的辅助函数，本轮全部定名：

* **`FUN_00412500(id)`**：遍历敌人链表 `DAT_004b43dc+0x68`，**若某个敌人的 `+0x27b4` 等于该 id
  则返回 1，否则 0** —— 一次**存在性测试**；
* **`FUN_00412530(id)`**：同一次遍历，返回**那个敌人对象指针**；
* **`FUN_0041a910(enemy)`**：返回**脚本局部槽的地址**（线程局部数组 `+0x100c`，特殊情况走虚调用）。

所以：

> **455 = `*局部槽 = (存在 id 为 i(1) 的敌人)`**

而下一行 456（0x1c8）是 `*浮点槽 = FUN_00412530(i(2))->[0x1074]`（取找到的敌人的某字段）。

### 47.3 关键发现：端口**已经有了** 455 的一半

| 需要什么 | th12 | 端口 |
| --- | --- | --- |
| 脚本局部槽地址 | `FUN_0041a910` / `FUN_0041a960` | **已有**：`EclContext::integer_reference(u32, EclGlobals&)`、`float_reference`——**功能等价**，而且还会记录 `ecl_last_integer_access` / `ecl_last_integer_argument` |
| **敌人实例 id** | `+0x27b4`（由 `FUN_00412990` 从 `+0x74` 写入；`FUN_0043a480` / `0044a2d0` / `0044a5d0` / `0044ab60` / `0044ac00` 都在比它） | **缺失**：端口只有 ANM 虚拟机的 `AnmVm::id`，**没有敌人 id** |

**所以 455 很近，但卡在一个结构性缺口上**：没有敌人 id，就无法算出 `FUN_00412500(i(1))`。
在没有证据说明 id 从哪来的情况下把它编出来，违反本项目一贯纪律——**记下来，不猜**。

顺带一个**有价值的发现**：`integer_reference` / `float_reference` 的存在，
等于**一次性解锁了整族「写变量」指令**（455、456/0x1c8、500……），
这让 455 的实现从「重活」变成「填空」——只差 id。

### 47.4 结果

| 项 | 变化 |
| --- | --- |
| 判决表 | `collision` 16 → **15**，`implemented-collision` 30 → **31** |
| 第 1–6 关 | 全部跑满 12000 帧 |
| 第 7 关 | 仍停在 **455** |
| 闸门 / 测试 | 8 个全 exit 0；12/12 |
| 浏览器 | **`error=""`**、`traps: 0`、61 FPS |

`build-sdl.mjs` exit 0（sha256 `c9db29ee…`）。

### 47.5 下一轮

1. **敌人实例 id**：查清 th12 的敌人从哪拿到 `+0x27b4`（线索：`FUN_00412990` 从 `+0x74` 写它），
   给端口补上等价物——**这是解锁 455/456/500 那一族的前提**；
2. **核对** 406/407/408/410 在端口侧的真实状态（它们不在碰撞名单里，属于「自称已处理」）；
3. **455（0x1c7）**：第 7 关；
4. 碰撞名单余 **15** 条、`todo` 余 **18** 条。

## 48. 本轮：实现 455 + 补上敌人实例 id；**七关全部跑满预算**

### 48.1 敌人实例 id：`FUN_00412990` 说得很清楚

```
*(u32*)(enemy + 0x27b4) = *(u32*)(DAT_004b43dc + 0x74);            // 实例 id
*(u32*)(enemy + 0x26b8) = (*(u32*)(DAT_004b43dc + 0x74) & 1) + 3;  // 同一计数的**奇偶**用法
```

也就是说 id 是**管理器侧的一个递增计数**。而端口 **早就有** 这个计数：
`EnemyManager::total_created`，并且**以同一种形状**使用它——
`e.death_sound = i32(total_created & 1) + 2`。

> **这个「同形状奇偶用法」就是计数同一性的证据**：th12 是 `(id&1)+3`，端口是 `(total_created&1)+2`。
> `+2` 与 `+3` 的差异**尚未解释**，本轮**不动它**，只记下来。

新增 `EnemyState::instance_id`，**在 th12 赋值的位置赋值**：参数拷贝之后、第一帧之前
（`EnemyManager::spawn` 中 `memcpy` 与 `damage_immunity.set` 之后）。

### 48.2 455 的目标槽：靠比较调用点定下来

```
case 0x1c7 (455): *FUN_0041a910() = FUN_0041a900(1)
case 0x1b0:       *FUN_0041a910() = FUN_0041a900(2)
case 0x1b1:       *FUN_0041a910() = FUN_0041a900(4)
```

可见 `FUN_0041a910()` 取的是**第 0 号实参**的引用；而它内部的两个分支
（下标非负 → 线程局部数组 `+0x100c`；否则走虚调用取全局）与端口的
`EclContext::integer_reference` **逐条对上**（非负 → `stack.data + frame_base`；否则委托
`globals.integer_reference`）。

于是 **455 = `*arg0 = (存在实例 id 为 i(1) 的敌人) ? 1 : 0`**，
即 `FUN_00412500` 的返回值；端口用新增的 `EnemyManager::enemy_exists` 走同一条 `manager_link` 链。

### 48.3 ★ 七关全部跑满 12000 帧

| 关卡 | 本轮之前 | 本轮之后 |
| --- | --- | --- |
| 第 1–6 关 | 跑满 | 跑满 |
| **第 7 关** | 1300 帧后停在 **455** | **跑满 12000 帧** |
| 浏览器 | `error=""` | `error=""`、59 FPS、`traps: 0` |

**但同样要把话说完**：「不再被拒」不等于「处理得对」。尤其是 455：
「目标是第 0 号实参」这个结论建立在**「`+0x10` 就是指令的第一个实参」+ 调用点形状**之上——
**强，但没有被证明**。若目标取错，写进去的会是一个**合法但错误**的槽位，
**探针完全看不见**。这正是「可达性 ≠ 保真度」的教科书例子：
**关卡跑通了，而一个写错的变量目标可以是隐形的。** 这一条已列为**首要待证伪项**。

### 48.4 又一次红构建：声明不是定义

455 的补丁在头文件里**声明**了 `EnemyManager::enemy_exists`，却**忘了写定义**，于是链接报

```
wasm-ld: error: undefined symbol: th11::EnemyManager::enemy_exists(int) const
```

**我的静态校验为什么没抓到**：它验证了「声明是新增的」「之前没有」，
但**没有任何一条要求存在匹配的定义**。

> **声明不是定义。只加了一半契约的补丁，只有链接器抓得住。**
> 这与第 44 轮的作用域错误是同一类：静态校验守的是**文本与锚点**，链接器守的是**符号**。

另外：本轮我在**运行前**抓到了自己脚本里的一个 bug（`tc =` 漏了声明，
在 ES module 里会抛 ReferenceError，而抛出点**在后面两次写入之后**）——
说明「先校验后写」这条规则**连写脚本的人自己都要守**。

红构建的代价如实记：测试掉到 1/12、探针没有输出、浏览器跑的是**上一轮**的 wasm。
修复后**全部重跑**才得出结论；**红灯期间没有任何提交**。

### 48.5 结果

| 项 | 变化 |
| --- | --- |
| 判决表 | `implemented` 129 → **130**，`todo` 18 → **17** |
| 关卡 | **七关全部跑满 12000 帧** |
| 闸门 / 测试 | 8 个全 exit 0；12/12 |
| 浏览器 | `error=""`、`traps: 0`、59 FPS |

`build-sdl.mjs` exit 0（sha256 `86c58560…`）。

### 48.6 下一轮

1. **证伪 455 的目标槽**（首要）：用 replay 变量对照，验证「第 0 号实参」这一结论；
2. **核对** 406/407/408/410 在端口侧的真实状态（不在碰撞名单里 = 自称已处理）；
3. 悬空问题：th12 在哪里设置 collision callback（候选 444）；
4. `+2` vs `+3` 的差异（`+0x26b8` 对应端口哪个字段）；
5. 碰撞名单余 **15** 条、`todo` 余 **17** 条。

## 49. 本轮：**证伪失败（= 被三条独立证据证实）**；并**推翻我自己 43/44 轮的结论**

### 49.1 优先项一：证伪 455 的目标槽 —— 结果反而把它证实了

上一轮 455 的目标槽结论是「第 0 号实参」，建立在**调用点形状**上。本轮去证伪，用的是**另一类证据**：
**运行时结构体布局**。

端口自己的 `EclInstruction` 就是答案：

```cpp
struct EclInstruction {
    i32 time; u16 opcode, length, references; u8 difficulty, parameter_count; u32 stack_adjustment;
    template<class T=T> T argument(u32 index=0){ memcpy(&v, (const u8*)this + 16 + index*4, 4); }
};   // sizeof == 16
```

`argument(0)` 在 **+16 = 0x10**，而 `references` 正是 **+8** 处的 u16。
th12 的 `FUN_0041a910` 读的恰恰是 `*(instruction + 0x10)`，判断的恰恰是 `*(byte*)(instruction + 8) & 1`
——**就是 `references` 的第 0 位**，也正是端口的
`instruction->references & (1u<<(index&31))` 在 `index==0` 时检查的那一位。

于是 **三条互相独立的证据一致**：

| 证据 | 结论 |
| --- | --- |
| 调用点形状（0x1c7 存 arg1、0x1b0 存 arg2、0x1b1 存 arg4） | 目标是**第 0 号实参** |
| 运行时指令布局（args 起于 +16） | `+0x10` **就是**第 0 号实参 |
| 端口自身访问器（`argument(0)` 在 +16；`references` 在 +8） | 同上，且引用位判定一致 |

**残留不确定（照实说）**：th12 的 `+8 & 1` 与端口的 `references` 第 0 位**是否同一个标志**，
是**结构上一致**而**推论**得来，未被独立证明。所以 455 是「**强支持，但仍未证明**」。

### 49.2 优先项二：核对 406/407/408/410 —— 全部正确，却**推翻了我自己 43/44 轮的结论**

先看端口的 drop 结构：

```cpp
struct EnemyDrop {i32 primary,counts[19];Vec2 spread;};   // sizeof == 0x58
```

对 offset 一算，四个「自称已处理」的指令**全部精确吻合**：

| opcode | th12 | 端口 | 判定 |
| --- | --- | --- | --- |
| **406** | `memset(e+0x1624, 0, 0x4c)` | `counts` 清零 | **对**：19×4 = 76 = **0x4c**，且 `+0x1624` **正是** `counts` 的起点 → **`primary` 被保留** |
| **407** | `e[0x1620 + i(0)*4] = i(1)` | `((i32*)&drops)[index] = count` | **对** |
| **408** | `e[0x1670]=f(0)`；`e[0x1674]=f(1)` | `drops.spread.x/.y` | **对**：`0x1620 + 0x50 = 0x1670`，而 `spread` 正是 +0x50 的 `Vec2` |
| **410** | `e[0x1620] = i(0)` | `drops.primary = i(0)` | **对** |

**而同一套算术否证了 43/44 轮写下的东西**：那两轮把 `+0x1620` 叫作
「**四元效果 id 数组**」——**错的**。`+0x1620` 是**掉落描述符的 `primary` 字段**，
其后紧跟 **19 个计数**与 `spread`。

所以 **409 不是「卸载效果槽 0」，而是掉落生成器**：`FUN_00412100` 读 `*(e+0x1620)`（= `drops.primary`）
传给 `FUN_004273f0`——那是个 **1798 字节、按该值分派**的函数（`param_3 == 9`、`10..15`、`0x10..0x12`，
即**道具种类**），落进 `DAT_004b44f0` **道具管理器**族，固定 `-π/2` 与 `2.2`，
再经 `FUN_00412140` 摘除，最后写 `*(e+0x1620) = 0`。

**本轮落地**：删掉 43 轮那个**冗余且错误**的 `effect_ids` 字段；把 409 改为清 `drops.primary`；
把四个已验证的指令连同 offset 算式**作为「已验证」记录在代码里**。

> **这是纪律朝另一个方向起作用**：一个本该用来核对**别人**工作的检查，
> **否证的是我自己**早先的结论——而且旧结论被**点名保留在案**，不是悄悄改掉。

### 49.3 结果

| 项 | 变化 |
| --- | --- |
| 七关 | **全部跑满 12000 帧** |
| 结构体 | `EnemyState` 0x16c8 → **0x16b8**，`Enemy` 0x2704 → **0x26f4**（移除多余字段） |
| 闸门 / 测试 | 8 个全 exit 0；12/12 |
| 浏览器 | `error=""`、`traps: 0`、61 FPS |

`build-sdl.mjs` exit 0（sha256 `0b0e9169…`）。

### 49.4 下一轮

1. **悬空的 collision callback**（候选 444）：th12 到底在哪里设置它；
2. **`+2` vs `+3`**（`+0x26b8` 对应端口哪个字段）；
3. **409 的完整保真度**：道具生成在宿主侧、未建模——已记录，未实现；
4. **一个策略性缺口**：目前**没有参照物**（没有可比对的原版构建），
   变量语义这类「合法但错误」的写法**探针看不见**——replay 对照是目前唯一想到的路线，需要立项；
5. 碰撞名单余 **15** 条、`todo` 余 **17** 条。

## 50. 本轮：**浏览器 Runtime 第一次有了「真的在渲染」的证据**

### 50.1 先承认此前的证据有多弱

此前每一轮的浏览器证明，记录的都是 **DOM 字符串**与**「没有报错」**。
而这两样东西——**一个空白画布配一个渲染循环，全都能满足**。
所以「做出可运行的 th12 浏览器 Runtime」这句话，**一直没有渲染层面的证据**。

### 50.2 探针，以及**先证伪它**

新增 `tools/th12-frame-proof.py`。它只在两种**毫不含糊**的情况下失败：

* 某一帧是**单一纯色**（空白/清空的画布）；
* 两个**连续的后段帧完全相同**（渲染器冻住）。

其余一切**只打印数字供人判断**——不设「差异像素够多才算过」这种阈值，
**因为那是在猜**。

**先证伪探针**：塞入一张纯黑帧与一对相同帧 → **exit 1**，
且三条理由都精确命中（`blank.png`/`frozen-a`/`frozen-b` 各自「single solid colour」）。
**探针可信，才拿来用。**

### 50.3 ★ 结果：确实在渲染，而且变化剧烈

| 帧 | 字节 | 背景占比 |
| --- | --- | --- |
| `r49.png`（启动瞬间） | 11,279 | **89.4%** |
| `r49-1.png` | 371,463 | **3.3%** |
| `r49-2.png` | 361,202 | 17.6% |

连续帧差异：**90.57%**，随后 **52.81%**。

**两次独立运行复现**（r48 / r49）：3.4% / 3.3%、90.57% / 90.57%、52.82% / 52.81%
——**确定性**，因此这个测量是可靠的。

怎么读：启动帧**大部分是背景**；第一帧游戏画面里 **96.7% 的像素是内容**；
而 40 秒间隔的两帧之间有 **52.81% 的像素发生变化**。
**「空白」与「冻住」两种可能，现在都被排除。**

### 50.4 但它仍然不能证明什么（照实说）

**像素 ≠ 正确。** 它说明**有东西被画出来且在动**，
**不**说明那东西是 th12 的关卡——**一个渲染得很丰富的错误关卡同样能通过**。
它也完全没说剩下那批 `todo` 的语义对不对。

> 于是本轮的结论要分两半说：**「在渲染」已有证据；「保真」仍然未证。**

### 50.5 一次流程教训

本轮有一条 `pwsh` 调用因为替换文本里嵌了引号而**解析失败**——
**PowerShell 会先解析整个脚本，所以那一整次什么都没执行**（这条老笔记又生效了一次）。
改用**文件编辑工具**、避免嵌入引号即可。

> 值得记下来的规则：**没有任何理由把「替换后的文本」塞进 `pwsh` 命令行；用编辑工具。**
> 这是第四次因为把带引号的文本塞进 `pwsh -Command` 而白丢一次调用。

### 50.6 结果与下一轮

构建 OK；8 个闸门 0 失败；12/12 测试；浏览器 `error=""`、`traps: 0`、59 FPS；
帧证明 **exit 0**（自此成为验证配方第 9 步）。本轮**未改动任何 Runtime 源码**，
因此没有重新生成 SDL harness，也就**不声称**它的哈希。

下一轮：444（collision callback）、`+2` vs `+3`、409 的道具生成（宿主侧未建模）、
以及余下的 **15** 条碰撞与 **17** 条 `todo`。
而**缺口现在更清晰了**：渲染有证据、**正确性没有证据**——
replay 对照仍是目前唯一想到的保真度路线，需要立项。

## 51. 本轮：**最大的那条 `todo`（257，135 次使用）完全解码 —— 而且它根本不是「没实现」**

### 51.1 257 的真身：生成子敌人，仅此而已

```
switchD_00415546_caseD_101:                      // 257 (0x101)
  iVar10 = (arg0 + 4 + ((arg0+4) >> 31 & 3)) >> 2;   // 注意：是一个**字索引**
  memset(&spawn, 0, 0x50);
  spawn.x   = FUN_0041a9b0(1, arg[iVar10+4]);
  spawn.y   = FUN_0041a9b0(2, arg[iVar10+5]);
  spawn.<整数> = FUN_0041a970(enemy, 3), (4), (5);
  复制 12 个字：enemy+0x23c -> spawn;                 // 父敌人的 48 字节块
  FUN_00412990(instruction + 20, &spawn);            // 第 47 轮读过的那个生成器
```

三个「未知依赖」全部落地：

| 未知项 | 实际是什么 |
| --- | --- |
| `0x477420` | 只是个 `memset` 包装（**不是**什么子系统） |
| `FUN_0041a9b0(k, raw)` | 「`references` 第 k 位若置位则解析 raw，否则原样返回」= **端口已有的 `c.resolve_float`** |
| `FUN_0041a970(enemy, k)` | 整数版本 = **端口已有的 `c.resolve_integer`** |

后两条**关掉了第 46 轮留下的两个未识别项**。

而端口**早就**把 0x101 送进了 `command()` 的生成分支——
也就是说**判决表把它记成 `todo`，但它其实是被处理的**：一条**假 todo**。

### 51.2 `mffSSS` 签名也就此解释清楚

* `m`：管理器生成；
* `ff`：两个**按字索引**定位的浮点（在绝对实参 `iVar10`、`iVar10+1`，引用位却是 **1 和 2**——
  **位的下标 ≠ 实参下标**）；
* `SSS`：三个**绝对**实参 3、4、5。

### 51.3 发现两处偏差，**只落地了可证明的那一处**

**可证明的**：th12 的起点是**字索引** `(arg0+4)/4`，端口用的是**字节**偏移 `20+string_bytes`；
只要名字长度不是 4 的倍数，端口就会**落在字中间**。
改为向上取整（`20+((string_bytes+3)&~3u)`）。
两者在 `string_bytes % 4 == 0` 时**完全一致**，所以这次改动只影响未对齐的情形。

**故意没有落地的**：`FUN_0041a970(3)/(4)/(5)` 是**绝对**下标
（455 的 `FUN_0041a900(1)` 已经证明这一族是绝对的），而端口按**相对**读。
**这意味着整个 0x100 生成族的 health/score/drop 可能取自错误的字。**
但这需要先把「arg0 与名字的关系」从反编译上下文里坐实，**在坐实之前不改**。

> 值得点明：这类错误**不会崩**（生命值取错照样运行），
> 正是第 49 轮那条「合法但错误、探针看不见」的典型。

### 51.4 结果

构建 OK；七关全部跑满 12000 帧；8 个闸门 0 失败；12/12；浏览器 `error=""`、`traps: 0`、60 FPS；
帧证明 exit 0（3 帧、2 对在变化、无空白）。

### 51.5 目标状态的**如实**陈述（本轮必须说清）

长期目标**远未完成**，且**不会**在本轮或下一轮完成：

* **th12**：一部能跑、能渲染的 Runtime；判决表 `implemented` 130、`todo` 17、碰撞 15；
  仍有未建模的宿主侧子系统；
* **th13 / th14 / th16 / th17 / th18**：**尚未开始**（管线与证据方法已有，作品本体没有）；
* **host 平台**（启动器/协议/存档/Replay/触控）：目前只有**开发用 server** 与 SDL harness，
  **不是**目标里说的那个平台。

目标保持 **active**。

### 51.6 下一轮

1. **坐实 0x100/257 的整数下标基准**——这是目前找到的**最高价值保真度缺口**；
2. 对齐改动的可观测性；
3. 444（collision callback）；`+2` vs `+3`；
4. 余下 **15** 条碰撞、**17** 条 `todo`，以及**判决表的假 `todo`** 清理。

## 52. 本轮：**撤回我上一轮的结论**；并修掉自己仪器里的一个假信号

### 52.1 撤回：第 50 轮「整数是绝对下标」的结论是**错的**

第 50 轮我写道：`FUN_0041a970(3)/(4)/(5)` 是**绝对**下标，
「整个 0x100 生成族的 health/score/drop 可能取自错误的字」，**并且没有落地修改**。
本轮读了这个访问器的函数体：

```c
this_00 = script->active;
if ((1 << (param_1 & 0x1f) & instruction->references) != 0)
    return FUN_00468f70(this_00, in_EAX);      // 解析的是 EAX 里的**原始值**
return CONCAT44(this_00, in_EAX);
```

**原始值走的是 `in_EAX`，不是参数**——反编译器把这个寄存器藏掉了。
而第 50 轮我自己读过的反汇编其实已经写明了调用点：

```
mov eax,[edi + esi*4 + 0x18]   ; = arg[iVar10 + 2]
push 3 / call 0x41a970          ; 引用位 3
```

所以五个实参**全部相对于同一个 `iVar10`**：浮点在 `arg[iVar10+0/+1]`（位 1、2），
整数在 `arg[iVar10+2/+3/+4]`（位 3、4、5）。
端口两者**完全对上**——算术也对上（端口 `20+sb+8`，th12 `16+4·iVar10+8 = 28+sb`）。
**所以本就不需要行为修改**；需要修的是我上一轮写进代码的**那段错误注释**（已改）。

> **这是第三次被反编译产物误导**：第 45 轮那个其实是寄存器的浮点字面量、更早的 `extraout_ECX`、
> 以及本轮的 `in_EAX`。
> **规则**：当一个访问器的参数表**解释不了它的值从哪来**时，
> **先读调用点的反汇编，再下结论。**

### 52.2 修掉自己仪器里的假信号

`tools/th12-opcode-map.mjs` 判定「已实现」**只看有没有 `case 0xNNN:` 标签**：

```js
: handled.has(id) ? 'implemented' : used > 0 ? 'todo'
```

于是 **257 明明被管理器闸门处理，却被记成 `todo`**。
这恰是第 43/44 轮那条教训的**反面**：
**有 `case` 不等于被处理；没有 `case` 也不等于没被处理。**

修法**不是**手改判决，而是一张 `MANAGER_GATES` 表：每条都写明**文件**与**必须存在的代码片段**，
在运行时校验，**代码一旦不再匹配就抛错**。

**先证伪**：把 `op!=0x101` 改成 `op!=0x9f9` → 工具**抛出**；
恢复后重新运行正常。

结果：**`implemented` 130 → 131**，**`todo` 17 → 16**。

### 52.3 一次被自己拦下的补丁

该补丁的**第一次尝试**假定存在 `GAME_DIR` 这个绑定，而它并不存在——
**在写任何文件之前就抛错**（判决数字未被改动，**没有半成品状态**）。
读了工具头部（第 19 行导入 `readFileSync`、第 24 行定义 `repo`）后，
改成**自包含**的版本才落地。**这条「先校验后写」的规则这回救了自己。**

### 52.4 结果与状态

构建 OK；七关全部跑满 12000 帧；8 个闸门 0 失败；12/12；浏览器 `error=""`、`traps: 0`、60 FPS；
帧证明 exit 0。

目标状态与 §51.5 一致，**未变**：th12 是一部能跑能渲染的 Runtime（`implemented` 131、`todo` 16、碰撞 15）；
th13/14/16/17/18 **尚未开始**；目标里的 host 平台**尚不存在**。目标保持 **active**。

下一轮：余下 **16** 条 `todo`、**15** 条碰撞、444、`+2` vs `+3`。

## 53. 本轮：428/437/438/439 归位到 422 的共享体——**碰撞 15 → 12**

### 53.1 为什么先挑碰撞

`todo` 是「还没处理」，而**碰撞**是「TH12 的签名与它实际落到的 TH11 处理器不一致」——
**已经在跑错的代码**。后者更响，优先。

437/438/439 在碰撞名单里，428 则落进了 TH11 的激光处理器。

### 53.2 共享体，以及**决定性的那一段反汇编**

`tools/th12-case-body.py` 直接给出：**422、428、437、438、439 共用 VA `0x41887c`** 一个体。

```
0x4188e5  movsx eax, word [eax+4]        ; 取指令的 opcode
0x4188e9  sub   eax, 0x1b5
0x4188ee  je    0x418912                 ; 437 -> esi += DAT_004b0ca8
0x4188f0  sub   eax, 1
0x4188f3  je    0x418906                 ; 438 -> esi += DAT_004b0ca8 - 1
0x4188f5  sub   eax, 1
0x4188f8  jne   0x418918                 ; 439 -> esi += DAT_004b0ca8 - 2
...
0x418942  call  0x40e060                 ; 拿到 esi 的那个 loader
0x418947  or    dword [ebx+0x161c], 1    ; 敌人标志位——端口侧**唯一**的副作用
```

**逐字节的差别只作用在 `esi` 上**，而 `esi` 是喂给 `FUN_0040e060` 的指针——
**端口明确不建模的那个游戏侧 loader**。
端口**真正建模**的部分（XOR 字符串解码的结果、敌人标志位、随后 413 的 lifetime 复位）
**与 opcode 无关**。

⇒ 这四个兄弟**在端口看来就是 422 的同一个体**，于是把它们**路由过去**，
而不是去发明什么。

> 这正好是第 50 轮错误的**反面**：那一轮我在一个**对端口毫无影响**的「逐 opcode 差异」上下错了结论。
> 本轮先问的是「**这个差异有没有触及端口建模的任何东西**」，然后才敢复制体。
> **「共享体」不等于「共享端口侧效果」——必须证明差异到底落在哪一段。**

### 53.3 落地

* `EnemyStateCommands.cpp`：`case 0x1a6:case 0x1ac:case 0x1b5:case 0x1b6:case 0x1b7:` 共用一个体；
* `EnemyEmitterCommands.cpp`：删掉 TH11 的 0x1b5/0x1b6/0x1b7（含外层认领行，否则会**遮蔽**真正的处理器）；
* `EnemyLaserCommands.cpp`：激光组里删掉 0x1ac；
* `EnemyScript.cpp`：**437/438/439 移出碰撞名单**。

### 53.4 结果

| 指标 | 变化 |
| --- | --- |
| `collision` | **15 → 12** |
| `implemented-collision` | 31 → **34** |
| `implemented` / `todo` | 131 / 16（不变） |

构建 OK；七关全部跑满 12000 帧；8 个闸门 0 失败；12/12；
浏览器 `error=""`、`traps: 0`、61 FPS；帧证明 exit 0（3 帧、2 对在变化、无空白）。

### 53.5 状态与下一轮

目标状态与 §51.5 一致，**未变**：th12 是一部能跑能渲染的 Runtime；
th13/14/16/17/18 **尚未开始**；目标里的 host 平台**尚不存在**。目标保持 **active**。

下一轮：余下 **16** 条 `todo`、**12** 条碰撞
（`277,278,281,300,320,321,325,417,419,440,442,443`）、444、`+2` vs `+3`。

## 54. 本轮：**三个"已有 case"的碰撞，全部是 TH11 残留**——碰撞 12 → 9

### 54.1 先看共享体，再看反汇编

把余下 12 条碰撞一次性喂给 `tools/th12-case-body.py` 看共享关系，
发现 **440、442、443 三条已经有端口 case**——也就是说它们**不是"没实现"，而是"在等核对"**。
三者实体都极小（14、10、26 字节），于是直接反汇编：

```
// 442 (0x1ba) @ 0x418986
mov eax,[0x4b43cc]          ; 游戏侧 loader 全局
or  dword [eax+0x7c], 8     ; 置第 3 位
jmp 0x41962b

// 443 (0x1bb) @ 0x418994
call 0x4127b0
jmp  0x41962b

// 440 (0x1b8) @ 0x41936d
xor  ecx,ecx / mov eax,ebx / call 0x41a900   ; i(0)
mov  edx,[0x4b43e4]
mov  [edx+0x6cf4],eax       ; DAT_004b43e4+0x6cf4 = i(0)
jmp  0x41962b
```

**三条都以 `jmp 0x41962b`（调度器共享尾）结束**，这也反过来印证了「opcode → case VA」的映射没错。

**结论：三个端口实体全是 TH11 的含义，全错。**

| opcode | TH12 真正做什么 | 端口原来做什么 |
| --- | --- | --- |
| **442** | `manager_flags |= 8`（第 3 位，**不读任何实参**） | 读 `i(0)`，写**第 0 位** |
| **443** | `manager_flags |= 0x10`（第 4 位）+ 拆掉 `+0x20` 的对象 | 读 `i(0)` 存进 `tick_callback` |
| **440** | `[DAT_004b43e4+0x6cf4] = i(0)` | 创建 deformation |

`FUN_004127b0`（443 调用的）本体：`DAT_004b43cc+0x7c |= 0x10`，
再 `FUN_00461a70(param_1, *(DAT_004b43cc+0x20))` 并把该槽清零——
即**拆掉 loader 全局持有的那个对象**；那属于端口不拥有的宿主侧对象，故只保留标志位。

### 54.2 落地

* **442** → `w.manager_flags|=8u;break;`；
* **443** → `w.manager_flags|=0x10u;break;`（对象拆除作为宿主侧、已记录）；
* **440** → `case 0x1b8:{w.value_6cf4=u32(i(0));break;}`——
  `DAT_004b43e4+0x6cf4` 端口尚未命名，就**按其偏移命名**（与既有的 `quad_15f4`、`timer_1690` 同一约定），
  **不去猜它是什么**；
* 顺带修掉 `EnemyLaserCommands.cpp` 里那句把 0x1ba 说成「toggles it」的注释——**它正是这个残留的辩护词**。

### 54.3 **差点踩进可达性陷阱**

改完就提交是不行的：**440/442/443 仍在 `kTh12CollidingOpcodes` 里**，
而该表确实**拒绝**它们——`colliding(opcode)` 会写入 `error` 结构：

```cpp
if(colliding(context.instruction->opcode)){
    error={context.instruction,context.thread_id,context.time,context.instruction->opcode};
```

所以**新写的体全是死代码**。移出名单（440、442、443）后重新构建、重新验证。

> **「写对了」不等于「跑得到」**——这条在第 42 轮就付过学费，本轮在提交前又拦下一次。

### 54.4 结果

| 指标 | 变化 |
| --- | --- |
| `collision` | **12 → 9** |
| `implemented-collision` | 34 → **37** |

构建 OK；七关全部跑满 12000 帧；8 个闸门 0 失败；12/12；
浏览器 `error=""`、`traps: 0`、60 FPS；帧证明 exit 0。

余下 **9** 条碰撞：`277,278,281,300,320,321,325,417,419`。

### 54.5 状态与下一轮

目标状态与 §51.5 一致，**未变**：th12 是一部能跑能渲染的 Runtime；
th13/14/16/17/18 **尚未开始**；目标里的 host 平台**尚不存在**。目标保持 **active**。

下一轮：余下 9 条碰撞（`277,278,281,300,320,321,325,417,419`）、16 条 `todo`、
444（collision callback）、`+2` vs `+3`。

## 55. 本轮：三条碰撞**故意保持拒绝**，并把错误体位换成显式拒绝

### 55.1 三个更小的体，全部是 TH11 残留

281（40 字节）、417（52）、419（39）直接反汇编：

```
// 281 (0x119) @ 0x415ce5
push 1 / call 0x468e20            ; i(1)
push 0 / call 0x468e20            ; i(0)
mov [ebx + eax*4 + 0x1e0], esi    ; enemy[i(0)*4 + 0x1e0] = i(1)，无越界检查
jmp 0x41962b

// 417 (0x1a1) @ 0x4187df
i(2)、i(1)、i(0) 依次经 FUN_0041a900
push 1 / call 0x4529a0            ; FUN_004529a0(1, i(0), i(1), i(2), 0, 0x46)

// 419 (0x1a3) @ 0x41883d
mov eax,[0x4b43e4] / cmp [eax+0x6d30],0 / je 尾   ; 全局为空 -> 直接返回
call 0x412720                     ; 返回 [全局+0x6d30]+0x8c
test eax,eax / jne 尾
or eax,0xffffffff / jmp 0x41962d  ; return -1
```

`FUN_004529a0` = `operator_new(0x44)` + `FUN_00452a60(对象, 参数…)` + 标志位——
**构造一个端口未建模的类，且返回值被丢弃**；
`FUN_00412720()` = `[对象+0x8c]`——**对未建模的宿主对象做致命错误判定**。

三条端口原有体位分别是：**移动插值器设置**（281）、**激光宽度**（417）、**激光角度**（419）——**全错**。

### 55.2 为什么**不**实现它们——拒绝才是正确答案

* **281** 的目标字段落在**插值器块内部**（端口自己的断言：`absolute_position==0x174`、`absolute_angle==0x20c`），
  该字段**并未确立**；**按偏移命名就等于重犯第 43 轮 `effect_ids` 那个「凭空发明字段」的错误**（后来已删除）；
* **417 / 419** 需要端口**没有的游戏侧对象**。

⇒ **无法在不发明行为的前提下实现**，于是**它们继续留在碰撞名单里**。
**碰撞数仍是 9，这不是没进展，而是诚实的答案。**

### 55.3 改的是**体位**：显式拒绝

错误体位**必须消失**——否则将来有人从名单里移除条目，
就会**悄悄激活**一段 TH11 代码。现在它们明确拒绝：

* `case 0x119:return -2;`（0x11b 拆出并保留，其 `e.relative` 随拆分修正）；
* `case 0x1a1:case 0x1a3:return -2;`。

### 55.4 **★ 我自己犯的两个错，都被闸门抓住**

1. **编译器**：`duplicate case value '418'` —— **0x1a2 本来就有自己的 case**，
   说明我那句 `else if(op==0x1a2)` **一直是死代码**。
   ——而且那一轮的 stage 输出**毫无意义**（构建失败 ⇒ 用的是**旧 wasm**），**必须重跑**。
   **构建才是语义的闸门**（第 44 轮的规则）。
2. **dispatch 闸门**：`UNREACHABLE … missing from routing: 0x19e`。
   我把**条件分支**（`if(op==0x19e||op==0x19f)`）提升成了 **case 标签**，
   造出了外层路由**永远不会释放**的 case。闸门那句话本身就是准则：
   > *A case that nothing releases or routes does nothing, no matter how correct it is.*
   它同时**证明了 0x19e/0x19f 在我改动之前就已经不可达** ⇒ 删掉不损失任何东西。

> 这正好是第 51 轮的**镜像**：那时「有处理、无标签」；这时「有标签、无路由」。
> **两个闸门合起来，把两个方向都关上了。**

### 55.5 结果

构建 OK；七关全部跑满 12000 帧；**8 个闸门 0 失败**；12/12；
浏览器与帧证明**作为提交门控**通过。`collision` 保持 **9**（有意为之）。

余下 9 条碰撞：`277,278,281,300,320,321,325,417,419`——
其中 **281/417/419 的语义已记录、故意保持拒绝**；
**278,300,320,321,325,277 这 6 条仍带着待核对的体位**。

### 55.6 状态与下一轮

目标状态与 §51.5 一致，**未变**：th12 是一部能跑能渲染的 Runtime；
th13/14/16/17/18 **尚未开始**；目标里的 host 平台**尚不存在**。目标保持 **active**。

下一轮：核对余下 6 条带体位的碰撞（`278,300,320,321,325,277`）、16 条 `todo`、444、`+2` vs `+3`。

## 56. 本轮：300（0x12c）真正修好并移出名单——**碰撞 9 → 8**

### 56.1 300 的 TH12 体可以逐字转写

`@ 0x4165aa`，181 字节，**与 302（0x12e）共用**：

```
lea edi,[ebx+0x68] / cmp ax,0x12c / je ... / lea edi,[ebx+0x9c]
                                  ; edi = &Enemy+0x68（absolute）或 &Enemy+0x9c（relative）
f(0) -> [edi]        （带守卫）
f(1) -> [edi+4]      （带守卫）
and dword [edi+0x30], 0xfffffffc  ; **清除**标志位 0、1
fld [ebx+0x9c]; fadd [ebx+0x68] ...  ; combined = relative + absolute
mov [ebx+0x3c], combined.z / call 0x413700
```

**关键的三点：**

1. 比较用的常量在 `0x4a4440`，是双精度 **`-999999.0`**——
   **正是端口一直称为 `missing` 的那个值**！其它所有移动类 opcode 都用 `> missing` 守卫；
   而 `fcom`/`fnstsw` 那一对在**无序（NaN）**时跳过写入，
   与 `x > missing` 对 NaN 恒为假**完全一致** ⇒ **端口既有的写法本来就忠实**。
2. `Enemy+0x68` / `+0x9c` 就是 **`Movement` 的 absolute / relative**，
   即端口的 `e.absolute` / `e.relative`（端口自己在 0x140/0x141 的注释里已经确立）。
3. 端口**旧体**把参数读成 angle/speed/radius/radial/axis/ratio **六个**，
   并且 **置**标志位 0、1——**与"清除"正好相反** ⇒ **是 TH11 的体**。

新体：

```cpp
case 0x12c:case 0x12e:{
    auto& m=op==0x12c?e.absolute:e.relative;
    const float x=f(0),y=f(1);
    if(x>missing)m.position.x=x;if(y>missing)m.position.y=y;
    m.flags&=~3u;m.refresh_position();e.combine_movement();break;
}
```

`0x12a/0x12b` 的 `[[fallthrough]]` **原样保留**——那两号本来就读 `f(0),f(1)`，与 300 的入口**一致**。

### 56.2 **★ 可达性问题，彻底查清**

`EnemyScriptServices::command` 在**进 switch 之前**就拒绝名单里的每个 opcode：

```cpp
if(colliding(context.instruction->opcode)){
    error={context.instruction,context.thread_id,context.time,context.instruction->opcode};
    return -2;
}
```

⇒ **第 53、54 轮的理由是对的**：**忠实写好的体，在 opcode 离开名单之前是死代码。**
⇒ 所以正确做法是**实现与移出名单同时做**——本轮正是如此。

而 **dispatch 闸门量的是另一条轴**（家族路由），所以它对其它 case 不报警。
⇒ **一共有三条独立的可达性轴**：*拒绝名单*、*家族路由*，以及第 51/54 轮碰到的 *case 标签*。**三条都要查。**

### 56.3 277 / 278：记录而不实现

两号都把 `&Enemy[0xe0 + i(0)*4]` 交给 **`FUN_00461c50`**（一张端口未建模的**指针表**），
再写它返回对象的字段：**277** 写 `+0x2c` 并置标志位 4；**278** 把同一个浮点写进 `+0x40` 与 `+0x44` 并置标志位 8。
那是一个**端口不拥有的类**，故两号**拒绝**。
同时**改正一句错误的注释**：那两句说「原版不取参数直接成功」——**只对 0x1f4 成立，对 0x116 不成立**。

### 56.4 结果

| 指标 | 变化 |
| --- | --- |
| `collision` | **9 → 8** |
| `implemented-collision` | 37 → **38** |

构建 OK；七关全部跑满 12000 帧；8 个闸门 0 失败；12/12；浏览器与帧证明作为提交门控通过。

### 56.5 状态与下一轮

目标状态与 §51.5 一致，**未变**：th12 是一部能跑能渲染的 Runtime；
th13/14/16/17/18 **尚未开始**；目标里的 host 平台**尚不存在**。目标保持 **active**。

余下 8 条碰撞：`277,278,281,320,321,325,417,419`——
其中 **277/278/281/417/419 已解码、故意保持拒绝**；
**320（361 字节）、321（715）、325（397）仍带着未核对的体位**。

下一轮：核对 320/321/325（三者分别与 322/323/326 共享体）、16 条 `todo`、444、`+2` vs `+3`。

## 57. 本轮：查清 host 的真实状态；发现端口**早就握着 320 的体，只是挂错了号码**

### 57.1 先查 host —— 结论：**现阶段它不该动**

`host/` 是**空的**（0 个文件），`shared/eagler-common/` 是**只读参考**的逐字副本。
读工作区自己的计划文件后，结论与我先前的推测一致但要精确得多：

* `docs/ARCHITECTURE.md`：Host 拥有作品目录/包安装/生命周期/输入镜像/缩放，**存储只经协议**
  `list/read/write/remove/sync`；Runtime 拥有游戏状态机、60Hz 逻辑、`/savesth12` 挂载、
  **原版存档与 Replay 格式**、全部渲染。**协议细节以
  `reference/eagler-touhou/docs/ADAPTING_A_GAME.md` 为准**，不另立一份。
* `docs/ROADMAP.md`：**M6 才是**「`eagler-touhou/1` 接入 Host」；
  M4 玩法层、M5 外壳层都在它前面。**当前阶段是 M3 引擎层**——正是这几轮在做的事。

⇒ **我这几轮的方向没有偏**：host 不是下一个瓶颈，M3 才是。
⇒ 但 ROADMAP 里写着「**46 个号码撞车、65 个待抄写**」——**已严重过时**，
而实测是 **8 / 16**。**计划文件在低报自己的进度**；本轮把它改成实测数字。

### 57.2 ★ 320（0x140）的体，端口**本来就有**

`@ 0x417093`，与 322（0x142）共用：

```
lea esi,[ebx+0x68] / cmp / lea esi,[ebx+0x9c]     ; absolute 或 relative Movement
f(0)..f(5)                                        ; 六个 FLOAT 读
if(!(flags&1)) [esi+0x0c] = [esi+0x00]            ; velocity = position
FUN_00408910(esi, f(0))   ; = esi[+0x1c] = FUN_004646e0(FUN_004646e0(f(0)))   ; 角度归一化，**套了两次**
然后带守卫地写 [esi+0x18]、[esi+0x20]、[esi+0x24] …
```

端口的 `Movement`（`static_assert(sizeof==0x34)`）：

| 偏移 | 字段 | 320 写入的自变量 |
| --- | --- | --- |
| +0x18 | `speed` | **f(1)** |
| +0x1c | `angle` | **f(0)**（经归一化） |
| +0x20 | `radius` | **f(2)** |
| +0x24 | `radial_velocity` | **f(3)** |
| +0x28 / +0x2c | `ellipse_angle` / `ellipse_ratio` | 待读 |

**⇒ 这与第 56 轮刚从 `0x12c` 换掉的那个体位，自变量逐一对上**：
`angle=f(0)`（经归一化）、`speed=f(1)`、`radius=f(2)`、`radial=f(3)`，
以及 `if(!(m.flags&1)) m.velocity=m.position`。
**即：端口早就握有 TH12 的 0x140 体，只是挂在 TH11 的 0x12c 号码上。**

**仍不落地**，因为还差两件事没读清：`FUN_004646e0` 连用两次是否就等于端口的 `normalize_angle`，
以及 320 的 flags 尾巴。**本轮只记录，不猜。**

### 57.3 结果与状态

`EnemyScript.cpp` 的碰撞名单上现在有 320 的完整解码与上述「挂错号码」的发现；
`docs/ROADMAP.md` 的数字改为实测值。**本轮不减少碰撞数**（仍是 8）——
本轮的价值是**一个可立即落地的发现**与**一份不再低报进度的计划**。

构建 OK（**本轮只改注释与文档，目标代码未变**，故第 55 轮的浏览器证明仍然适用）；
8 个闸门 0 失败；12/12。

目标状态与 §51.5 一致，**未变**：th12 是一部能跑能渲染的 Runtime；
th13/14/16/17/18 **尚未开始**；目标里的 host 平台**按计划排在 M6，尚未开始**。目标保持 **active**。

下一轮：把 320/322 落成 `case 0x140:case 0x142:`（先读 `FUN_004646e0` 与 flags 尾巴），
然后 321/325，再 16 条 `todo`、444、`+2` vs `+3`。

## 58. 本轮：320 落地——**碰撞 8 → 7**；再被路由闸门抓住一次

### 58.1 两个悬而未决的细节，全部查清

1. **`FUN_00408910(m,v)` = `m[+0x1c] = FUN_004646e0(FUN_004646e0(v))`**，
   而 **`FUN_004646e0` 就是角度归一化**：`> 3.1415927` 时循环减去 `6.2831855`，最多 `0x20` 次。
   ⇒ 它就是端口的 `normalize_angle`。
   **套两次**只在「第一次撞到 32 次上限」时才与套一次不同 ⇒ 即 `|angle| ≳ 201` 弧度。
   **对一切可达输入，一次调用是忠实的**；这个差异**记录在案，而不是悄悄抹掉**。
2. **320 的尾巴**：`f(5) → [esi+0x2c]`；`or dword [esi+0x30], 3`；`call 0x464eb0`；`call 0x413700`
   ⇒ **`flags|=3`、Movement 刷新、以及和 300 尾巴同一个 combine 调用**。

### 58.2 映射逐字段对上

| Movement 偏移 | 字段 | 320 的自变量 |
| --- | --- | --- |
| +0x0c | `velocity` | `if(!(flags&1)) velocity = position` |
| +0x18 | `speed` | **f(1)** |
| +0x1c | `angle` | **f(0)**（经归一化） |
| +0x20 | `radius` | **f(2)** |
| +0x24 | `radial_velocity` | **f(3)** |
| +0x28 | `ellipse_angle` | **f(4)** |
| +0x2c | `ellipse_ratio` | **f(5)** |

**每一项都落在有名字的字段上**——这正是它能被转写的原因。
而它与第 56 轮刚从 `0x12c` 换掉的体位**自变量逐一对上**：
**端口早就握着 TH12 的 0x140 体，只是挂在 TH11 的号码上。**

**反汇编还逼出一处修正**：带守卫的写入全部使用**朴素的** `fcom`/`test ah,0x41` 模式，
**只有 f(0) 走归一化调用** ⇒ **TH12 并不归一化 ellipse_angle**，而旧体位归一化了。
**以反汇编为准。**

### 58.3 **★ 路由闸门又抓住我一次**

落地之后，`tools/th12-handler-routing.mjs` 报：

```
0x142: enemy_movement_command runs first, EnemyStateCommands.cpp also handles it and never runs
```

即 **0x142 本来就已经被处理**，我的新标签会**遮蔽**它。
⇒ 我的「写前校验」只查了 `EnemyCommands.cpp`——**查错了文件**。
规则 r41 说「校验每一个输入」，我在**定位器**这一维上违反了它。

闸门**只报了 0x142**，反过来说明 **0x140 确实空闲且被路由** ⇒
**目标 opcode（320）落地，322 的既有处理器原样不动。**

> 这是**连续第二轮**被闸门救下（第 54 轮是重复 case + dispatch，本轮是路由）。**这套闸门在做实活。**

### 58.4 结果

| 指标 | 变化 |
| --- | --- |
| `collision` | **8 → 7** |
| `implemented-collision` | 38 → **39** |

构建 OK；七关全部跑满 12000 帧；8 个闸门 0 失败；12/12；浏览器与帧证明作为提交门控通过。

### 58.5 状态与下一轮

目标状态与 §51.5 一致，**未变**。目标保持 **active**。

余下 7 条碰撞：`277,278,281,321,325,417,419`——
其中 **277/278/281/417/419 已解码、故意保持拒绝**；
**321（715 字节）与 325（397）是最后两条带着未核对体位的碰撞**。

下一轮：321 / 325，然后 16 条 `todo`、444、`+2` vs `+3`。

## 59. 补充：交接文件；以及一次**我自己的流程错误**

### 59.1 `docs/HANDOVER.md`

余下的 th12 工作**不再是「还没抄」，而是「端口还没有那个子系统」**，
所以本阶段最有价值的产物是一份**有证据的交接说明**。新增 `docs/HANDOVER.md`，并在 README 里挂上入口。

它写清了：**有什么**（一部能跑能渲染的 th12 Runtime：131/16/7，七关跑满 12000 帧、8 闸门、12/12、浏览器证明）；
**没有什么**（th13/14/16/17/18 零行代码；`host/` 是空目录；host 接入按 ROADMAP 排在 M6）；
**六部通用的方法论**（证据优先级、三次反编译陷阱、两步映射、三条可达性轴、写前校验、闸门纪律、
操作纪律）；**逐条可继续的工作**（7 条碰撞各自的现状与阻塞原因、16 条 `todo`、444、`+2` vs `+3`、
存档/Replay 偏移、已知的 122 个测试失败及其三种成因）；**照抄即可的重建与验证命令**；
以及**最大的风险：没有原版 oracle ⇒ 合法但错误的写入不可见**。

### 59.2 ★ 流程错误：**闸门红了，我却提交了**

提交交接文件那一轮，`th12-opcode-map.mjs` 报
`docs/th12/ecl-extended-opcodes.json is stale - rerun the generator`——
因为该闸门会**对源文件取哈希**，而我这轮改过 `EnemyScript.cpp` 的注释。
**我数了失败个数，却仍然让提交继续跑了。**

**这是错的。** 浏览器证明那一环我用的是「条件提交」，闸门这一环却只是计数。
**计数不是闸门。** 已修正：重新生成判决表 → 8 闸门全绿 → 测试 `fail 0` → **才**提交本轮的判决表。

> **规则（新增）**：**任何**提交都必须以「全部闸门 exit 0 且测试 fail 0」为**前置条件**，
> 而不是以「我看到了失败个数」为结论。

### 59.3 当前状态

th12：**131 implemented / 16 todo / 7 collision / 39 implemented-collision**；
8 闸门 0 失败；12/12；七关跑满 12000 帧。
th13/14/16/17/18 **尚未开始**；host 平台**尚未开始**（按计划在 M6）。目标保持 **active**。

## 60. 收尾一轮：把 16 条 `todo` 的真实清单与「同一类」结论写进交接文件

### 60.1 先纠正交接文件里的一处错

`docs/HANDOVER.md` §4.2 早先把 **257（0x101）** 写成了「最大的一条待办」。
**它是错的**：257 早已被管理器闸门处理（§52），**根本不在那 16 条里**。
本轮以 `docs/th12/ecl-extended-opcodes.json` 的 `entries` 为准，把**准确的 16 条**列成了表，
并注明字段名是 `id` / `usedInTh12Dat` / `decompiled`——**不要猜字段名**（我自己猜错了两次）。

### 60.2 16 条 `todo` 与 7 条碰撞是**同一类**工作

以使用最多的 **602（0x25a，98 次）** 为例，它的体在调度器里（`FUN_004154d0` 第 2124 行 `case 0x25a:`）：

* `_memset(&local_2a8, 0, 0x1e8)`；
* `FUN_0041a900(0)`——**整数自变量 0 当索引用**；
* 从 `(iVar10*0x214 + param_1) + 300` 整块**复制 108 个浮点**到栈上；
* 读 `param_1 + iVar10*0xc + 0x152c/0x1594/0x1530/0x1534`，并加上 `param_1 + 0x34/0x38/0x3c`（坐标）。

即 **`0x214` 步长的索引槽位数组 + `0xc` 步长的表 + 一个 0x1e8 的局部结构**。
**在这三者的语义确立之前，转写只会得到外表合理、含义错误的写入**——也就是这个项目
**没有 oracle 时看不见的那类错误**。

> **结论**：余下的 `todo` 与余下的碰撞**都不是「还没抄」，而是「端口还没有那个子系统」**。
> 下一步的正确顺序是**先补子系统**，而不是继续按计数器抄 opcode。

### 60.3 一并记录的两点

* `decompiled` 字段的含义：`inline` = 体在调度器里；`fallthrough` = **会落到下一个 opcode 的体**
  （312 → 313）；`absent` = 反编译输出里没有（600、700，需先读反汇编补上）。
* **提交纪律**（§59.2 的规则）本轮**照做**：8 闸门 exit 0 且测试 `fail 0` **之后**才提交。

## 61. 第 60 轮末：**最终验证记录**与**仍然缺失的东西**

### 61.1 最终验证（对提交 `9a55295` 的树，工作区干净）

| 检查 | 结果 |
| --- | --- |
| 核心构建（wasi-sdk → wasm32-wasip1） | **OK** |
| 8 个闸门 `--check` | **8/8 exit 0** |
| 核心测试 | **tests 12 / pass 12 / fail 0** |
| 七关模拟预算 | **七关全部 started，survived 12000 frames，ran the full budget** |
| 浏览器实跑 | **`error=""`、`health: 61 FPS`、`traps: 0`** |
| 帧证明 | **exit 0；3 帧、2 对变化帧、无空白帧**；相邻帧像素变化 90.57% / 53.08% |
| 判决表 | `implemented 131 / collision 7 / todo 16 / implemented-collision 39 / unused 28 / noop 1` |

**这七行共同证明的是「能跑、能渲染、在动」。它们不证明「和原版一样」。**

### 61.2 仍然缺失的东西（不许含糊）

* **th13 / th14 / th16 / th17 / th18：零行代码。**
* **host 平台：`host/` 是空目录。** 启动器 / 协议 / 存档 / Replay / 触控**都还没有实现**。
  按工作区自己的 `docs/ROADMAP.md`，host 接入是 **M6**，前面还有 **M4 玩法层**与 **M5 外壳层**；
  当前停在 **M3 引擎层**。
* th12 的 **M4 / M5 / M6 均未完成**；余下 **7 条碰撞**与 **16 条 `todo`**（§4.1/§4.2）。

### 61.3 因此，关于「1:1」这个措辞

六部里**有一部**能在浏览器里跑起来并渲染，方法是**逐条读原版机器码转写**；
**其余五部尚未开始**，**host 尚未开始**。
且在**原版 oracle 建成之前**（见 `docs/HANDOVER.md` §5），
「1:1」只能读作「按反汇编逐条转写」，**不能**读作「与原版行为等价」——
**合法但错误的写入在这一条件下不可见**。

工作区自己的路线图对这个规模有判断：*「单部作品是数千函数级的重建；六部合计以年计」*。

### 61.4 最后一轮我自己又犯了一次同类错（第 5 次）

提交 §61 的记录时，我把提交信息写成了 `git commit -m "…… error \"\" ……"`，
**转义引号把参数切碎了**，git 报 `Filename too long`——**提交没成功**（文件已 `git add`，但没有 commit）。

**这与「绝不要把替换文本塞进 `pwsh -Command`」是同一条规律**：
**任何带引号、换行、反斜杠的文本，都不要放在命令行参数里，要放进文件。**
这条规则本工作区**已经**记在 `docs/HANDOVER.md` §3.7，我**违反了它**——这是**第 5 次**。
改用 `Set-Content` 写信息文件 + `git commit -F` 后立即成功。

> 教训：**规则写在文档里不等于会被遵守**；命中率靠的是**默认动作**，不是记性。
> 所以这里把动作固定下来：**提交信息一律走文件 + `git commit -F`。**

## 62. 打开 oracle 通道的第一步：那 109 个测试**从来没跑到过断言**

### 62.1 病灶

`runtimes/th12/th12_web/tests/cpp/helpers.mjs:15` 原本写死：

```js
const m=await NativeMachine.create(bytes,{wasmBinary:readFileSync(resolve(root,'reference/native/unicorn-bounded.wasm'))});
```

而 `reference/native/unicorn-bounded.wasm`（「带指令预算钩子的定制 Unicorn 构建」）**从未随仓库分发**。
于是 **109 个测试在加载阶段就 ENOENT**，**一个断言都没执行**。

而 `scripts/native/machine.mjs:8` 早就默认用 npm 的 `@alexaltea/unicorn-js`，
`wasmBinary` 只是**可选覆盖**；`docs/verification/2026-10-03-toolchain-bringup.md` 也明确写了
「`machine.mjs` 已改为使用 npm 的 `@alexaltea/unicorn-js`，因此**可以不依赖那个定制构建先跑起来**」。
**改了口子，却没改调用方。**

### 62.2 改动与前后对比

`helpers.mjs` 不再传那个不存在的 `wasmBinary`（引擎落到 npm 的 Unicorn）。

| | 修前 | 修后 |
| --- | --- | --- |
| `unicorn-bounded` ENOENT | **109** | **0** |
| 失败原因 | 「文件不存在」，**断言不可达** | **`uc_emu_start failed with code 6`**（`UC_ERR_READ_UNMAPPED`） |
| tests / pass / fail / skipped | 143 / 15 / 122 / 6 | 143 / 15 / 122 / 6 |

**计数没变，性质变了**：失败从「测试根本没跑」变成「测试跑了，并报出真实的模拟器故障」。
这才是**可以被修**的东西。

### 62.3 现在真实的三份欠账（oracle 通道）

| 数量 | 症状 | 性质 |
| --- | --- | --- |
| **109** | `uc_emu_start failed with code 6` | **harness 还是 th11 形状**：`helpers.mjs` 把 th11 的 `malloc`(0x460192)/`free`(0x45fc3b)/`memcpy`(0x46d630) 与 `Controller` 初始化入口(0x48abf0) **直接打进 th12 的镜像**并调用。th12 需要重新定位这四个地址。 |
| **12** | `ENOENT ...\[th11] 东方地灵殿 (汉化版+日文版)\th11.dat` | 非 oracle 测试仍硬编码 th11 数据路径，应改读 `target.json`。 |
| **1** | `artifacts/cpp/analysis/jp/functions/004526…` 缺失 | 需要生成分析产物。 |

**核心通道不受影响**：12/12、8 闸门 0 失败（本次提交即以此为门控）。

### 62.4 意义

原版对照（oracle）一旦真的能跑，「1:1」就从**断言**变成**可验证的差异报告**——
这也是余下 7 条碰撞与 16 条 `todo` 能被可靠推进的前提。
本轮的价值是：**把一堵「文件不存在」的墙，换成了三份写着具体地址与具体数字的欠账单。**

## 63. oracle 通道：把 harness 从 th11 形状改成 th12 形状，模拟器**真的启动到了原版 CRT**

### 63.1 三份欠账里的第一份（也是最大的一份）已解决

`helpers.mjs` 里的四个地址**一直是 th11 的**。th11 注释原话是「original CRT initializer 48abf0」，
而 th12 的对应物可以**按符号名直接查到**——`reference/th12-decomp/decomp_out` 恢复了 CRT 名字：

| 角色 | th11（原本写死的，错） | **th12（已换）** | 证据 |
| --- | --- | --- | --- |
| malloc | 0x460192 | **0x46d04a** | `_malloc_0046d04a.c`「void * __cdecl _malloc(size_t)」|
| free | 0x45fc3b | **0x46c941** | `_free_0046c941.c`「void __cdecl _free(void *)」|
| memcpy | 0x46d630 | **0x47a330** | `_memcpy_0047a330.c`「void * __cdecl _memcpy(...)」|
| CRT 初始化 | 0x48abf0 | **0x472d44** | `__cinit_00472d44.c`，VS2008 Release「Library Function - Single Match」|

换之前：把 th11 的地址打进 th12 镜像 = **把四个无关的 th12 函数改写成跳转**，再调 th11 的入口。
换之后，109 个测试的报错**三次变形**，每一步都更靠近真相：

| 阶段 | 报错 | 含义 |
| --- | --- | --- |
| 本轮之前 | `ENOENT unicorn-bounded.wasm` | 测试**一个断言都没跑到** |
| 换地址前 | `uc_emu_start failed with code 6` | 模拟器跑起来了，但进了被改坏的代码 |
| 换地址后 | `Unimplemented kernel32.dll!GetModuleHandleA` | **th12 的 `__cinit` 真的被启动了** |
| 补 kernel32 桩后 | `Unimplemented kernel32.dll!GetProcAddress` | CRT 继续往下走 |
| 再补 40 项 kernel32 桩 | `uc_emu_start code 6`，pc=**0x400003** | 走到 CRT 初始化函数**内部**了 |

### 63.2 故障机制已精确定位（含反编译器又一次的 `in_EAX` 陷阱）

`__cinit` 的反汇编：

```
0x472d6b  call 0x47c20c                 ; __initp_misc_cfltcvt_tab
0x472d70  push 0x498354 / push 0x498338 ; 起止
0x472d7a  call 0x472ca8                 ; __initterm_e(start,end)
0x472d85  push 0x47b343 / call 0x46da32 ; _atexit
0x472d8f  mov  eax, 0x498304            ; ← __initterm 的【起点】在 EAX
0x472d94  mov  dword [esp], 0x498334    ; ← 【终点】在栈上
0x472d9b  call 0x472c8b                 ; __initterm
```

反编译把它写成 `__initterm((undefined4 *)&DAT_00498334)` + `in_EAX`——
**参数表解释不了起点，起点在 EAX**：这是同一个陷阱的**第 4 次**出现，与第 50 轮 `FUN_0041a970` 同类。

而 `__initterm`（0x472c8b）就是 `mov esi,eax` 之后逐个 `call` 表里非零项。
dump **0x498304..0x498334 的 12 个 dword**：**全部是合法 .text 指针**（0x497800 / 0x497820 /
0x497850 / 0x497860 / 0x497870 / 0x497880 / 0x4978a0 / 0x4978b0 / 0x4979d0 / 0x4979e0 / 0x4979f0），
没有 0x400003。

⇒ **表是干净的**，故障发生在**这些 C 初始化函数内部**，不是 CRT 表本身。
（顺带：之前 dump 的 0x49f344 是 `.rdata` 里 "softwarePresenter"/"KERNEL32" 之类的字符串，
所以故障时那份「调用栈」并不是调用栈。）

### 63.3 下一步的设计（已想清，含一处必须处理的坑）

th12 的静态初始化会**动态解析 DLL 函数**（`LoadLibraryA`/`GetProcAddress`）。
现在我对这两个返回 **0**——「诚实但没用」：代码随后 `call` 这个 0，就是 pc=0x400003 那类崩溃。

正确做法是把动态解析**接进 PE 导入同一套桩机制**：

* `LoadLibraryA/W(name)` → 返回一个**按名字区分的假模块句柄**（非 0，让代码相信装载成功）；
* `GetProcAddress(module,name)` → 调用 `machine.registerImport({dll,name})`，返回**桩地址**；
* 于是每一次动态解析的调用都会在 `onImport` 里**报出 `dll!name`**，而不是崩在野指针上。

**坑**：Windows API 是 `stdcall`，**参数由被调方弹出**；而 `GetProcAddress` 不携带参数个数，
桩不知道要弹出几个字。所以这一步必须**显式处理栈平衡**（维护一张 arity 表，或对未知名保守处理），
否则栈会错位、症状比崩溃更难查。**这一点先记下来，不带着它硬写。**

### 63.4 状态

| | 值 |
| --- | --- |
| tests / pass / fail / skipped | **143 / 15 / 122 / 6** |
| 变化 | 计数未变，但 109 个的报错从「文件不存在」→「模拟器启动并停在具体导入」 |
| 核心通道 | **12/12、8 闸门 0 失败**（本次提交的门控） |

余下两份欠账未动：**12** 个测试硬编码 `[th11] 东方地灵殿…\th11.dat` 路径；
**1** 个缺 `artifacts/cpp/analysis/jp/...` 分析产物。

## 64. oracle 通道：**修掉我自己上一轮埋的 ESP 写坏**；故障推进到「跳到空函数指针」

### 64.1 ★ 一个我自己造出来的 bug（靠故障数据抓到的）

上一轮我给 kernel32 加桩时写的是 `m.ret(stub(), e.argc)`。
而 `pe.mjs` 第 15 行只记录 `{dll, name, address}`——**PE 导入根本不带参数个数**。
于是 `e.argc` 是 `undefined` ⇒ `sp + 4 + undefined*4` = **NaN** ⇒ `reg_write_i32(id, NaN|0)` 把 **ESP 写成 0**
⇒ 下一次返回就从地址 0 取值。

这和当时观察到的故障**完全吻合**：`address: 0x0`。**这也是我上一轮标记的「stdcall arity 坑」的真身。**

**修正**：kernel32 表改成 `[handler, argc]` 显式携带**文档化的 stdcall 参数个数**
（Windows API 由被调方弹栈）。修完 `address 0x0` 立即消失。

> 教训：**桩函数必须自己声明参数个数**，不能指望调用方传进来的元数据存在。
> 以及：**我上一轮把「诚实但没用」的返回值当成了问题，其实栈平衡才是真问题。**

### 64.2 故障推进（又两格）

| 阶段 | 报错 | 含义 |
| --- | --- | --- |
| 修 arity 前 | `address 0x0` | **ESP 被我的桩写坏** |
| 修 arity 后 | `Unimplemented kernel32!TlsGetValue` | 栈正确了，CRT 前进到线程局部存储 |
| 补 TLS/线程批后 | `UC_ERR_FETCH_UNMAPPED`，**pc=0x0 / address=0x0** | **跳到空函数指针** |

补的批次（`TlsAlloc/Free/GetValue/SetValue`、`Fls*`、`GetCurrentThread`、`Sleep`、`SwitchToThread` 等）
语义都无歧义：分配索引、取值为 NULL（线程槽从未设置，这就是真话）。

### 64.3 一次**被证伪**的猜测（记下来，因为它花掉了几次探测）

故障栈顶 `0x475407` 引出候选调用点 `0x47545c: call dword ptr [0x49813c]`（在 `__getptd_noexit` 附近）。
但用 PE 阅读器直接核对：

* `0x49813c` 在 **`.rdata`**，flags `0x40000040` ⇒ **只读**；
* 静态值 **`0x000acc9a`** ⇒ **低于 0x10000，不是合法代码地址**；
* 只读内存不可能在运行时被改成有效指针。

⇒ **这条调用路径不是故障点**。猜测作废，**不是「大概就是它」**。

### 64.4 现有认识与下一步

栈上出现 `0x48b4db`、`0x473e82`（`___initmbctable`，`__initterm_e` 表项之一）⇒
故障发生在 **CRT 的 C 初始化链内部**，那里有东西调用了空指针。

**最可能的根因**：VS2008 的 `_cinit` 正常是**排在 `_heap_init` / `_mtinit` 之后**执行的；
而 harness 现在**直接 `call 0x472d44`（`__cinit`）**，等于**跳过了前面那些 CRT 阶段**，
于是某个初始化器解引用了尚未建立的状态。

**下一步**：按符号名找出并**按顺序**调用 `__heap_init`（`__heap_init_0046ea5c.c` 已定位）、`_mtinit` 等前置阶段，
而不是继续在初始化器内部追。

### 64.5 状态

| | 值 |
| --- | --- |
| tests / pass / fail / skipped | **143 / 15 / 122 / 6** |
| 109 个的报错 | 从「文件不存在」→ 具体导入 → 具体驱动状态（**两格推进**） |
| 我造的 bug | arity 缺失已修，注释里写明了原因与后果 |
| 核心通道 | **12/12、8 闸门 0 失败**（本次提交门控） |

## 65. ★ oracle 通道打通到「执行 th12 代码」：未实现导入归零，**首次有测试跑到断言**

### 65.1 不再猜 CRT 阶段顺序——**照抄 th12 自己的入口点**

反汇编 th12 PE 入口（`pe.mjs` 给出 `entry = 0x46e81d` → `call 0x47b369; jmp 0x46e69f`），
真正的 `mainCRTStartup` 体在 **0x46e69f**，启动顺序是**写死的**：

```
0x46e6b0  call [0x4981bc]              ; GetStartupInfoA
0x46e70d  push 1 / call 0x46ea5c       ; __heap_init(1)
0x46e71f  call 0x47562a                ; __mtinit
0x46e730  call 0x47b31d                ; __RTC_Initialize
0x46e738  call 0x47b07b                ; __ioinit
0x46e749  call [0x4981f4]              ; GetCommandLineA
0x46e754  call 0x47af44                ; __crtGetEnvironmentStringsA
```

harness 原本**直接跳 `__cinit`**，把这一整段全跳过 ⇒ 某个 C 初始化器解引用了从未建立的状态
⇒ 就是那个 `UC_ERR_FETCH_UNMAPPED, pc=0`。现在按原顺序调用，**故障立刻消失**。

> `__heap_init` 的反编译签名写着 `int __cdecl __heap_init(void)`，
> **但它读 `[esp+4]`**——原版入口确实 `push 1`。**又一次签名不可信**（同一类陷阱的第 5 例）。

### 65.2 结果：`Unimplemented` **归零**

补完 kernel32 的文件/区域设置面与环境块后（环境块返回**合法的空块**——这台 host 确实没有环境变量，
这是真话，不是编造），**整份套件里已经没有任何未实现导入**。

故障从「109 个卡在同一个导入」**散开成多种真实位置**：

| 形式 | 数量 | 位置 |
| --- | --- | --- |
| `FETCH_UNMAPPED` pc=0x0，**栈全零** | 43 | 待查（下一轮的靶子）|
| `READ_UNMAPPED` | 32 | 散在 th12 .text，如 0x412e30 / 0x45d900 / 0x406103 / 0x436420 |
| `WRITE_UNMAPPED` | 7 | |
| 缺 `reference/native/d3dx9_37.dll` | 11 | **新暴露的缺件** |
| 硬编码 th11.dat 路径 | 15 | 已知欠账（从 12 升到 15 ⇒ 它们也走得更远了）|
| 缺 `reference/assets` 目录 | 2 | **新暴露的缺件** |

### 65.3 ★ **首次有测试跑到断言**（本项目的第一次）

`hud-score`、`laser-probe-cancel`、`replay-recorder`、`sound-effects` 四个测试
**不再崩在模拟器里，而是执行到断言**——说明 oracle 真的跑了 th12 代码、产出了可对照的值。
（其余测试的断言现在报的是具体差异，例如 `probe 0 426fd0`。）

**这才是 oracle 的意义**：从「文件找不到」→「模拟器崩」→「跑出值再比对」。
计数仍是 **143 / 15 / 122 / 6**，但**失败的性质已经换了一代**。

### 65.4 下一步

1. **43 个「栈全零」的 pc=0**：最集中的剩余故障，先查它（栈全零意味着进入时栈本身不对）；
2. 散落的 `READ/WRITE_UNMAPPED`：逐个定位（现在每个都有明确的 pc）；
3. 两份新缺件：`d3dx9_37.dll` 与 `reference/assets`；
4. 已知欠账：12→15 个 th11.dat 硬编码路径、1 个缺失分析产物。

## 66. oracle 重指：**规模已测清（265 调用点 / 169 地址）**，并证明它「不能机械替换」

### 66.1 先更正我在 §65 的一处措辞

§65 我写了「43 个 `FETCH_UNMAPPED` 的**栈全零**」——**不准确**。
实际看一眼就知道栈顶有返回地址（例：`stack:["0x4520f4","0x0",...]`）。
那不是"栈全零"，只是故障详情里 `stack` 的前几项恰好为 0。**这里的结论按实际数据更正。**

### 66.2 病根与 §63/§64 修的是同一类，但散布在每个测试里

测试是从 th11 工程整套继承的，每条断言把 port 导出函数与**原版函数地址**配对：

```js
assert.equal(c.enemy_command(fixture,context), m.call(0x412e30,{ecx:q}), ...);
```

`0x412e30` 是 **th11 的地址**，却打进 th12 的镜像。实测规模：

| 项 | 值 |
| --- | --- |
| `m.call(0x......)` 调用点 | **265** |
| 去重后目标地址 | **169** |

### 66.3 ★ 最高复用的那一项：地址能推出来，**但不能直接替换**

`0x412e30` 被 11 个测试共用，配对关系明确（`c.enemy_command` / `c.bm_enemy_fire` / `c.cx_enemy_command` ↔ `m.call(0x412e30,{ecx:...})`）
⇒ th11 的它 = **敌机 ECL 命令分发器** = th12 的 **`FUN_004154d0` @0x4154d0**
（port 自己在 10 处以上写明：`EnemyScript.cpp:14`「until each of these is transcribed from
FUN_004154d0 (@0x4154d0, th12-decomp)」等）。

**但**：

```
/* undefined __fastcall FUN_004154d0(void * param_1, int * param_2) @ 004154d0  16758 bytes */
```

`__fastcall` **两个参数**（ECX+EDX），而测试只给了 th11 的一个 ECX。
⇒ **地址换了，调用约定与参数个数也换了。**
**这一条拦下了一次 265 个调用点的大规模错误 sed。** 结论：重指是**逐项语义工作**，不是文本替换。

### 66.4 两个被证伪的猜测（避免重复走）

1. 「`th12-function-map.json` 为空是因为立即数范围过滤太窄」——**错**：
   118 个断言语字面量**全部**在 `0x49f460` 一带，**0 个**在范围外。
2. 「`.text` 里有指向这些字面量的立即数」——**错**：
   扫过 `.text` 全部 617469 个位置，精确命中仅 **1 次**。这些字面量不是从代码直接引用的，
   靠它们反推函数归属走不通（该工具当前不可用，但它仍产出了 `distinctFiles: 44` 的原版源文件名清单）。

### 66.5 产物与方法

新增 **[oracle-repointing.md](oracle-repointing.md)**：完整清单（按复用率排序的前 20 项 + 使用者）、
推导方法（测试同行配对 ⇒ port 的 `FUN_xxxxxxxx` 引用，实测 95 处 / **49 个不同 VA** ⇒ 反编译签名 ⇒ 语义核对）、
以及每一项的完成定义。

**状态：0/169 已重指。** 这是清单与方法的起点，不是完成报告。
