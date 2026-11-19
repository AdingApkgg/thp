# TH06 New Classic 资源格式证据

适用原版：`H:/Games/th/06nc/th06nc.exe`，PE32+ x64，映像基址 `0x140000000`。
SHA-256：`07850c8c6e469c0e82c13423e6d0d096a88d693455bdacacbb44c0aa3bcce473`。
以下是资源格式记录，不代表原版执行器或完整玩法已经移植。

## PKGL

头部为四字节 `PKGL` 和 little-endian u32 加密目录长度，目录紧随头部。
`0x140059e20` 取文件 basename、去除最后一个扩展名，再按大小写敏感的字节计算 CRC32。
`0x140059cb0` 用该 u32 seed 生成 16 字节循环 XOR key：

1. `state = ((seed << 32) XOR (seed * 0x9e3779b1 + 1)) mod 2^64`。
2. 生成两个标准 SplitMix64 输出，每个按 little-endian 八字节排列。
3. 解码输入的第 i 个字节与 key 的 `i & 15` 字节异或。

目录加载路径 `0x140059fb0`，magic 校验位于 `0x14005a094`。
每条记录的固定部分为 32 字节，无结构对齐，之后紧跟 UTF-8 文件名：

| 偏移 | 类型 | 含义 |
| --- | --- | --- |
| 0 | u16 | flags，bit 0 表示 Zstandard |
| 2 | u32 | 此条目的 XOR seed |
| 6 | u64 | 解码后长度 |
| 14 | u64 | 包中长度 |
| 22 | u64 | 数据相对归档开头的绝对偏移 |
| 30 | u16 | 文件名字节数，原版要求小于 256 |
| 32 | byte[] | 文件名，无 NUL 终止符 |

文件加载器 `0x14005a470` 按记录偏移读取，先 XOR，再在 bit 0 为 1 时解 Zstandard，
最后校验输出长度。浏览器读取器与 Python 实现各自解析目录并完整解码全部文件；
`tools/tests/test_th06nc_pkgl.py` 直接执行原版 seed/XOR 函数，覆盖路径形式、
所有条目 seed 和跨 16 字节边界的长度。

## ECL 结构

从七个实际资源测得：u16 子程序数、u16 保留值 0、三个 u32 时间线偏移，
随后是每个子程序的 u32 文件偏移。此版本只有第一条时间线非零。

子程序指令：i32 时间、i16 opcode、u16 总长度、四字节控制字段，再跟参数。
终止记录为 time=-1、opcode=-1、总长度 12。
时间线指令：i16 时间、i16 arg0、i16 opcode、u16 总长度，再跟参数；
时间线以 time=-1 的四字节记录结束，不能按八字节普通头继续读取。
读取器要求各段完整消费，拒绝指令跨越相邻子程序或时间线边界。

该布局与旧版 TH06 参考实现的结构声明相近，但不能由此断言指令行为相同。
新读取器只返回结构和参数字节；原版执行分发表与逐指令语义尚待核验。

## 未完成部分

- ANM / STD 的执行与纹理引用仍须核验，PKGL 中存在 DDS 纹理。
- `data/bgm` 与 `data/bgm2` 各有 18 个 `.opus` 文件，开头为自定义头而非 `OggS`，
  不能直接作为普通 Ogg Opus 交给浏览器。
- 没有将旧版 TH06 网页 runtime 标记为 New Classic 的完成移植。

## DDS 加载层（2026-11-14）

`shared/th06nc/dds.mjs` 提供独立于 Node 的纹理读取接口。实际资源有两种布局：
旧式 32 位 BGRA（转为紧密排列 RGBA8，保留 alpha）和 DX10 BC7_UNORM
（DXGI 98，保留压缩块）。读取器逐级返回尺寸和数据，检查二维布局、mip 范围、
像素数据长度及行跨度，拒绝未支持的格式与数组／立方体／体积纹理。
实际部分二维文件的 depth 字段为 1，且未设置体积标记；读取器接受此布局。
大纹理的默认像素预算为 8192×8192。

运行 `node tools/th06nc-dds-check.mjs` 对七包中的全部 DDS 逐个解包并读取，
生成 [逐纹理元数据和摘要](th06nc-dds-verified.json)。原始资源不写入版本库。
`node --test shared/th06nc/dds.test.mjs` 覆盖 BGRA 通道与 alpha、行填充、
非零输入偏移、非四倍数 BC7 尺寸、多级数据边界以及损坏／不支持的头部。

这一步是资源加载能力，不是 BC7 软件解压、浏览器 GPU 上传或实际渲染验收。
BC7 后续需提供浏览器支持检查和可用的回退路径；ANM／STD 执行、标题、
ECL 与玩法、输入、存档和自定义音频仍未实现。`completeGame=false` 保持。

## ANM 加载层（2026-11-14）

`shared/th06nc/anm.mjs` 读取当前 125 个资源的 2,273 条精灵记录、
1,062 条脚本表记录和 11,935 条指令（含停止记录）。文件布局为 64 字节头、
每精灵一个 u32 偏移、每脚本一对 u32 ID／偏移、纹理名字及填充、精灵、脚本。
纹理名字空间以自身起点为基准补齐至 16 字节倍数，并非绝对文件位置对齐。
精灵记录为 ID 加六个 float，共 28 字节；后两个字段暂以 `extra` 保留。
脚本指令为 i16 时间、u8 opcode、u8 参数字节数，随后是参数。
opcode 0 的零参数记录结束脚本，随后可能有四字节零填充。

原程序加载入口为 `0x1400020b0`；`0x1400024e0` 从精灵偏移读取六个 float，
`0x1400026cd` 将脚本地址以 ID 加调用者基数写入表。原版允许重复 ID，按文件
顺序覆盖，不能因重复就拒绝资源。

`tools/th06nc-anm-native-check.py` 在 Unicorn 中执行原版
`[0x1400024ae, 0x14000270b)`，不调用游戏、Steam 或 GPU；对 125 个真实
资源检查最终绑定的 2,273 个精灵 UV／宽高及 1,061 个脚本地址，全部一致。
这里脚本绑定数少于记录数是重复 ID 覆盖所致。
[原码对照收据](th06nc-anm-native-verified.json)、[结构统计](th06nc-anm-verified.json)。

运行 `node --test shared/th06nc/anm.test.mjs` 与
`node tools/th06nc-anm-check.mjs` 可重跑结构检查；原码对照需 Python 的
Unicorn 和 Capstone。此证据不覆盖 ANM VM、渲染或整体游戏行为。
下一步优先核对原版 ANM 更新分发表和标题脚本，再接纹理选择、STD、ECL 与游戏生命周期。

## ANM 单指令执行（2026-11-14）

更新器已定位至 `0x1400069b0`，分发表位于 `0x140007494`。
`shared/th06nc/anm-command.mjs` 按原版 0x120 字节状态布局实现指令写入，
覆盖缩放、alpha／RGB、翻转、旋转／角速度、缩放速度、位置、插值起点与目标、
纹理偏移、混合及绘制标志。跳转、退出、精灵／随机精灵及中断返回控制请求，
尚待完整调度器消费；此模块本身不提供跨帧运行能力。

`tools/th06nc-anm-command-native-check.py` 从真实 ANM 取去重参数，在
两种初始标志状态下直接执行原版分发表指向的单条指令代码，到公共前进位置
`0x1400070e3` 为止，逐字节比较完整 288 字节 VM 状态。该区间不作 API 替换。
另外补三个未出现于实际脚本的无参数指令（6、8、33）控制用例。
共 3,714 组、1,069,632 字节全部一致，覆盖 29 个 opcode；
排除 0、1、5、15、16、21、24 的控制行为。
[单指令原码对照收据](th06nc-anm-command-native-verified.json)。

对照初次运行发现测试器未设置分发时的 opcode 寄存器，以及实现中的绘制标志
掩码错误；分别修正后全部通过。此处不据单指令检查声明完整 VM 或标题已通过。
下一步接入 `0x140006e0a` 开始的角速度、缩放／透明度／位置跨帧更新，
以及脚本时间推进和控制请求；之后用标题脚本逐帧对照原版更新器。

## ANM 跨帧与标题脚本调度（2026-11-14）

`shared/th06nc/anm-frame.mjs` 接入角速度、缩放、颜色与位置插值及时间推进。
3,714 组独立单指令状态各执行四次原版 post-command 更新，共 14,856 次、
4,278,528 字节全部一致。[跨帧收据](th06nc-anm-frame-native-verified.json)。
位置插值先使用当前计时器再递增，而缩放和颜色先递增再计算，这个顺序保留原版。

`shared/th06nc/anm-vm.mjs` 将命令与跨帧更新组合起来，接入跳转、精灵选择、
等待、标签和中断处理。随机精灵依赖调用者提供共享 RNG，未提供则明确报错。
当前绑定使用同一 ANM 资源内的精灵；应用层跨资源、全局基数还未接入。

`tools/th06nc-anm-vm-native-check.py` 对 title00–title06 的 113 个真实脚本
分别执行普通和外部中断两组、每组 360 次更新。中断组在第 45、120、180 次
索引处分别请求首个标签、不存在的标签、最后标签（无标签时请求不存在的标签）。
226 组共 81,360 次完整原版更新器调用，23,431,680 字节状态与返回值全部一致。
[完整更新器对照收据](th06nc-anm-vm-native-verified.json)。

这组对照从双方共享的初始化状态开始，执行原版 `0x1400069b0`，未用指令桩替换
更新器。脚本地址规范化为文件偏移、精灵地址规范化为本地 ID，其余状态逐字节比较。
它不验证原版启动／setter、真实菜单驱动的中断时机、全局 RNG、GPU 绘制或标题
整体生命周期。下一步接纹理绑定及渲染，继续核对原版标题的布局、调用与菜单输入。

## 浏览器纹理上传（2026-11-14）

`shared/th06nc/texture-gl.mjs` 已接入 RGBA8 与 BC7 的 WebGL2 上传。
BC7 使用 `EXT_texture_compression_bptc`，当前没有软件回退，不支持时明确报错。
颜色空间沿用 DDS 声明，不自动翻转像素或预乘 alpha。此接口只创建纹理；
实际游戏的采样、混合、精灵顶点与绘制次序仍待原版对照。

本机诊断运行方式：先 `node tools/th06nc-texture-prepare.mjs`，再
`python tools/th06nc-preview.py`，打开
`http://127.0.0.1:8268/runtimes/th06nc/texture-lab.html`。
资源导出只写入忽略目录，并与已有原始 DDS SHA-256 核对。
Windows 上默认 Python HTTP 服务把 `.mjs` 当作 `text/plain`；专用服务显式
设置 JavaScript MIME，修复了页面停在加载中的问题。

实际 headless Chrome 已上传并绘制 `title00.dds`（2048×2048 BC7）和
`eff00.dds`（512×512 BGRA 转 RGBA8）。两例均 BPTC 可用、GL 错误为 0，
640×640 回读含非零 RGB；截图已人工查看标题纹理图集。
[浏览器收据](th06nc-texture-browser-observed.json)。
这是纹理图集诊断，尚非真实标题画面；无原版 GPU 像素对照，也不证明其他设备
兼容性、完整纹理集显示或 BC7 回退。原有标题 ANM 执行对照保持各自独立范围。

## 精灵顶点与标题背景片段（2026-11-14）

`shared/th06nc/anm-quad.mjs` 重建无旋转、无裁剪的顶点／UV 路径。
位置按实际输出高度／480 换算，精灵素材宽高按输出高度／1080 换算，
锚点模式遵循原版 `0x700` 标志分支。旋转及裁剪暂明确报错，避免按错误路径绘制。
`tools/th06nc-anm-quad-native-check.py` 执行原码
`[0x140002ba1, 0x140002e05)`，直接读取四顶点的 XY／UV；
对标题脚本实际状态进行 2,382 组、480／1080／1440 三种输出高度检查，
152,448 字节全部一致。[顶点收据](th06nc-anm-quad-native-verified.json)。

`shared/th06nc/anm-renderer-gl.mjs` 接入顶点、纹理、VM 颜色以及默认／加算混合。
当前混合与采样仅完成实现，尚无原版像素对照。
本机 `http://127.0.0.1:8268/runtimes/th06nc/title-animation.html?frame=360`
可显示 title00 的两层背景片段：第 1 次更新索引明确注入中断 1，随后执行至
第 360 次更新，绘制两层。浏览器截图已查看，背景、边框和署名可见，
GL 错误为 0，回读非黑；[浏览器片段收据](th06nc-title-fragment-browser-observed.json)。
初次不触发中断时正确停在隐藏等待状态，并未将黑屏判为显示成功。

这不是完整标题生命周期，也未接入菜单、logo、真实标题 owner 的更新／中断／
绘制顺序。下一步扩展旋转路径并重建原版标题 owner，让真实菜单状态驱动动画。

## 旋转顶点与全局 ANM 表（2026-11-14）

旋转路径已加入 `anm-quad.mjs`，保留原版旋转前的缩放及旋转后的锚点平移。
新版几何对照共 2,412 组，其中 30 组为真实标题状态的非零旋转；三种输出高度
合计 154,368 字节一致。旋转原码运行范围从 `0x1400037a5` 开始，检查双方
使用相同 float32 正弦／余弦输入时的几何运算，不覆盖原版 CRT 的三角函数精度。
之前“旋转明确报错”的描述属于上一版本；裁剪路径仍未实现。

新增 `shared/th06nc/anm-bank.mjs` 管理局部 ID 加调用者基数后的全局表。
脚本和精灵独立发布，纯精灵资源覆盖不会抹掉原有脚本；VM 的精灵绑定及几何
读取跟随实际精灵资源，允许脚本和纹理来自不同资源。这层实现已用标题资源的
非零基数和纯精灵覆盖两项测试检查，尚未单独进行完整标题资源生命周期的原码对照。
原有 81,360 次完整 ANM 更新器对照重新通过，10 项结构／格式／绑定回归通过。

原版标题加载代码 `0x140047b8b` 起发布 title01 等资源；后续继续核对其实际基数、
阴影覆盖、标题 owner 的初始化、中断、更新和绘制顺序。完整标题、菜单和玩法均未验收。

## 标题资源及动画组初始化（2026-11-14）

`title-layout.mjs` 记录九个实际加载资源的 slot／基数及 owner 的 VM 位置，
`title-animations.mjs` 按该表加载全局 ANM bank，并立即执行各 VM 的零时刻指令，
再复制 sprite ID 和设置原版 wrapper 的 bit 13。
title01／02／03／04／01s／04s／05／00／06 的基数依次为
`0x100, 0x133, 0x13c, 0x146, 0x1ad, 0x1e0, 0x217, 0x218, 0x21a`。

`tools/th06nc-title-layout-native-check.py` 执行原版初始化的两个指令区间，
在外部加载／setter 入口记录参数后返回成功，分别核对全启用和每三项禁用一项
两种条件的加载／创建顺序。[调用布局收据](th06nc-title-layout-native-verified.json)。
此工具不将已跳过的外部调用当作实际执行证据。

另由 `tools/th06nc-title-init-native-check.py` 实际执行原版 ANM 表加载片段及
`0x140046dc0` setter（包含原版初始化及首轮更新），与当前 JS 标题动画组的
132 个槽位状态逐字节对照，全部一致，地址作与前述 VM 检查相同的规范化。
[初始化收据](th06nc-title-init-native-verified.json)。
其中 19 个全局脚本 ID 实际为空；显式 `allowMissing` 选项保留原版的空闲 VM，
默认缺失脚本仍报错。它们不是缺失玩法的替代实现，也没有合成脚本。

这些证据覆盖基础日文九份 ANM 的资源／VM 初始化，不覆盖 owner 的禁用条件
计算、本地化资源选择、实际输入、中断时机、更新／绘制顺序、音乐或完整标题。
下一步继续追踪 title owner 的 tick／draw 及输入状态转换。

## 标题六层背景过渡（2026-11-14）

`title-backdrop.mjs` 重建原版 `0x140047080` 的过渡请求与
`0x140046ef0` 的背景更新：依次 tick 两层 title00 与四层 title06，再按 owner
计时器对三层执行平方缓出缩放；请求 2 在当前过渡或插值忙碌时转为请求 5，
保留一帧等待。请求 1 清空 owner 过渡数据并向四层 title06 发出中断。

`tools/th06nc-title-backdrop-native-check.py` 覆盖请求 1–7 以及空闲、owner
过渡中、VM 插值中三种初始条件。21 组请求及随后各 70 次更新（合计 1,470）
的控制区、缩放写入、中断字段全部一致，六个 ANM 更新调用的顺序也逐次核对。
为隔离 owner 运算，这组测试在 ANM updater 入口返回，不冒充实际 VM 已执行；
ANM 执行器保留此前独立检查范围。[背景过渡收据](th06nc-title-backdrop-native-verified.json)。

浏览器片段现改用实际标题资源组及此 helper，明确请求背景中断 1 后执行 360 次
更新。已上传 title06 DDS，六层绘制均返回成功、GL 错误为 0，截图可见人物与场景。
[六层浏览器收据](th06nc-title-backdrop-browser-observed.json)。页面链接保持
`http://127.0.0.1:8268/runtimes/th06nc/title-animation.html?frame=360`。
上文两层 title00 截图收据保留为历史版本，不作为当前文件的源码身份。

当前六层按已核对的更新顺序诊断合成；原版 draw 次序、完整标题 input/state
转换和其他菜单层仍待重建，不将本片段认定为原版完整标题显示。

## 背景绘制分支（2026-11-14）

`title-backdrop-draw.mjs` 接入基础背景资源可用时的原版分支
`[0x14005499e, 0x140054bcc)`。顺序为 title00 第一层、title06 前三层，
title06 第四层只提供加色控制，不单独绘制；title00 第二层位于原版更晚的
`0x140055757` 分支，中间的菜单层尚未接入。
保留临时横向缩放、临时颜色替换及调用后的状态恢复。

`tools/th06nc-title-backdrop-draw-native-check.py` 覆盖 32 种 alpha 开关组合
及三种缩放，共 96 组、192 次绘制调用。调用顺序、缩放位、颜色、加色参数
和 draw 的 snap 参数全部一致，owner 状态及外部颜色项在调用后恢复。
测试在绘制与颜色 API 入口观察并返回，不是原版 GPU 执行。
[分支收据](th06nc-title-backdrop-draw-native-verified.json)。

renderer 已接入加色项及像素取整。PE 导入表表明原版取整调用是 `rintf`，
当前使用 ties-to-even；原有 2,412 组几何检查仍覆盖不取整路径，不扩称取整
路径已完成原码差分。颜色合成曾误接为乘法，截图出现黑色人物剪影，已改为
加色后重查人物可见；这处 shader 公式仍需原版 GPU 像素对照进一步确认。

新版浏览器片段发出五次实际绘制，GL 错误为 0，人物、场景和边框可见。
[当前浏览器收据](th06nc-title-backdrop-draw-browser-observed.json)。
上文“六层分别绘制”保留为诊断旧版范围，当前不再绘制颜色控制层。
完整标题菜单、输入状态转换及原版像素验收仍待完成。

## 菜单项选中表现（2026-11-14）

`title-menu-item.mjs` 重建 `0x14004d8e0` 的完整菜单项表现更新，并通过
`TitleAnimations.presentItem` 接入动画组。调用者传入当前活动组、项目编号、
选中项及 pulse 时钟；该接口本身不处理按键或改变 owner 菜单状态。
选中项使用 `0x100..0x132` 加 `0xad`、`0x146..0x17c` 加 `0x9a` 的阴影
精灵；未选中项恢复保留的原精灵与单位缩放。非活动组 alpha 为 135，活动组
选中项按 72 帧周期改变 alpha，其余 alpha 为 255；位置偏移按原版清零。

`tools/th06nc-title-menu-item-native-check.py` 以九份实际标题资源建立原版全局
精灵表，然后执行完整原版 helper（包含真实 SetActiveSprite）。覆盖七个精灵
ID、组和项目匹配／不匹配、周期分段边界及负时钟控制，共 280 组、80,640
字节完整 VM 状态全部一致。[菜单项收据](th06nc-title-menu-item-native-verified.json)。
原码检查初次暴露 fixture 未将未加载精灵槽标记为 -1，已按原版 manager
构造器补齐；当前缺失阴影精灵会保留旧绑定，与原版一致。

新增 `tools/th06nc_native.py` 供后续检查复用固定可执行文件身份和真实标题表
加载。实际菜单调用矩阵、按键切换、确认／取消及绘制层仍未接入；背景诊断页面
不会据本次 helper 通过冒充可操作菜单。

## 菜单输入导航与长按重复（2026-11-14）

`title-navigation.mjs` 接入原版 `0x14004d1f0` 的上下导航及输入采样后的
`[0x140079d37, 0x140079d7a)` 长按阶段。Up／Down 分别为 `0x10`／`0x20`，
Up 有优先级；新按下或 repeat 非零才移动，移动后按项目数循环。未移动时保留
选择值，不擅自将异常值归一化。光标音效 12 按原版三槽规则排队，未打开音频设备。

`tools/th06nc-title-navigation-native-check.py` 执行完整导航 helper，覆盖
三种项目数、边界选择、双向按键组合、前帧按键、repeat、禁音与不同音效队列，
3,072 组选择、返回方向、音效队列全部一致。
[导航收据](th06nc-title-navigation-native-verified.json)。

`TitleInput.sample` 以完整 held mask 是否变化重置计时；不变化时，在旧计时器
至少为 30 且低三位为零时触发 repeat，达到 38 后先重置为 30 再递增。
它不使用浏览器 KeyboardEvent.repeat 的节奏。
`tools/th06nc-title-input-native-check.py` 对保持、上下同时按、快速换方向、
叠加确认键、松开再按等七条序列共 3,750 个采样 tick 做原码检查，按键边界、
repeat 和时钟一致。[输入重复收据](th06nc-title-input-native-verified.json)。

上述检查从物理输入轮询之后开始，不覆盖浏览器／手柄键位映射、禁用菜单项跳过、
主菜单确认／取消及 owner 状态转换。下一步连接主菜单 state 3 的导航、项目表现
和确认分支，再逐步接入其他菜单；当前背景预览仍不冒充完整可操作标题。

## 主菜单 state 3 组合更新（2026-11-14）

`title-main-transition.mjs` 重建原版确认／取消判断，保留至少 20 帧的输入门槛、
按键边沿、Extra 解锁限制、难度修正、Practice／Spell 标记、目标状态及动画中断。
同帧确认后仍检查取消和返回键，不将多键输入简化为互斥选择。
`tools/th06nc-title-main-transition-native-check.py` 执行原版判断阶段，
420 组覆盖全部十项、未解锁／已解锁、门槛前后与同帧组合，状态及 fade／sound
调用参数全部一致。[确认阶段收据](th06nc-title-main-transition-native-verified.json)。

`title-main-update.mjs` 进一步组合导航、Extra 跳过、旧选中项淡出、主菜单十项
精灵／颜色表现和上述转换。主菜单表现有别于通用菜单项 helper：未选中 alpha
为 128，旧选中项保留 15 tick 的淡出，Spell Practice 使用第 50 号动画槽。
时钟、解锁结果、音效队列由调用者提供并延续；进入其他状态后拒绝继续调用此
state-3 更新器，不冒充后续菜单已实现。

`tools/th06nc-title-main-update-native-check.py` 从原版 `0x140048174` 开始执行
实际导航、精灵绑定、表现和确认代码，到公共 owner 后处理之前停止。80 组涵盖
十项、导航／确认／取消及 Extra 条件，owner 字段、淡出计时、事件／音效队列和
132 个初始化 VM 均一致，共 10,560 份完整 VM 对照。
[组合更新收据](th06nc-title-main-update-native-verified.json)。
两组检查均观察 fade／sound 外部调用后返回；不代表效果交付、公共 owner 更新、
浏览器键位、绘制、各目标菜单或游戏开始已通过。后续继续连接 owner 公共更新与
实际菜单绘制，再接目的菜单。

## 稳定主菜单连续更新与浏览器交互（2026-11-14）

`title-main-advance.mjs` 接入保持 state 3 时的公共时钟、进入菜单暂停脉动、
倒计时、菜单 VM、logo VM 与背景推进。回主菜单 tween、菜单 slide、状态改变
后的公共路径仍不支持。`tools/th06nc-title-main-advance-native-check.py` 执行
完整原版公共指令及真实 VM 更新，24 组边界条件、3,168 份 VM 状态全部一致。
[连续推进收据](th06nc-title-main-advance-native-verified.json)。

`title-main-draw.mjs` 接入稳定 state 3、无 slide 时的菜单绘制循环，保留
owner 临时位置偏移与调用后的恢复。全启用和部分禁用两组的 196 次调用、位置
字节及持久状态恢复与原版一致；GPU draw 入口仅观察，不扩称原版像素一致。
[菜单绘制收据](th06nc-title-main-draw-native-verified.json)。

新增 `http://127.0.0.1:8268/runtimes/th06nc/main-menu-lab.html`，直接以诊断方式
进入主菜单并向十项菜单发出中断 2，背景发出中断 1，不冒充原版 boot 流程。
真实图集已显示十项菜单，按“向下”按钮由 Start 跳过未解锁 Extra 到 Practice
Start；确认 Start 发出 state 8、45 帧 fade 及 sound 10 的请求后停在尚未实现的
目标状态。截图已查看、GL 错误为 0，15 次实际绘制。
[浏览器交互收据](th06nc-main-menu-browser-observed.json)。
页面提供方向键与确认／取消键映射，当前浏览器证据使用按钮，尚未独立验收
物理键盘输入。加载完毕前按钮禁用；并行浏览器冷启动曾使早期点击落在加载中，
未将该结果判为操作通过，最终串行等待加载后重测。

菜单实图纠正先前命名：第 2 号（第三项）是 Practice Start，不是 Replay；
Replay 是第 4 号。代码将 owner `0x168d1` 的字段从 `replay` 改名为 `practice`，
原码字节和目标状态未改，420 组确认与 80 组组合检查重新通过。

title05 DDS 为 1920×805 BC7，直接 WebGL 压缩上传触发 1282。现按原压缩块
覆盖范围上传到 1920×808，并传递 `805/808` 的 V 比例修正；未解压或重压缩。
此路径目前仅支持单级 mip，shader UV 修正已用于实际菜单加载，仍需原版像素
对照验证边缘采样。未支持的 BC7 padded mip 链和无 BPTC 设备仍属未完成项。

下一步继续 state 8 过渡、难度／自机菜单及状态改变后的公共处理，随后再接游戏。

## state 8 资源更替与选择动画入口（2026-11-14）

`title-selection-layout.mjs` 实现 state 8 在第 50 帧开始的资源计划：停用标题背景，
卸载 slot 21–29、65–67，按 Spell／Practice／Extra／普通优先选择 select00
背景，再装入十一份 ANM（slpl00a/b、slpl01a/b、select01/02/05/03/04/06/07）。
`tools/th06nc-title-selection-plan-native-check.py` 在原版资源 API 入口记录参数
并返回成功，24 组帧边界与模式组合的顺序、基数和背景路径全部一致。
[计划收据](th06nc-title-selection-plan-native-verified.json)。不扩称真实加载及失败清理通过。

基础选择入口随后在 owner `0x122e0` 起建立 22 个 VM（ID 0x17d–0x192），
保留原版零时刻执行、颜色／标志设置、位置偏移清零及 sprite ID 保留。
`tools/th06nc-title-selection-init-native-check.py` 实际执行原版 setter 与初始化
循环，从初始零状态检查全部 22 个 VM，逐字节一致。
[选择动画收据](th06nc-title-selection-init-native-verified.json)。Spell 特殊槽位尚未实现。

`finishSelectionEntry` 接基础入口尾部：进入 state 9，重置时钟及淡入字段，
普通模式选择配置难度、Extra 选择 0，广播 6／18 号中断并清掉四个角色层的中断。
48 组普通／Extra、配置难度、fastEntry 与淡入时长条件的 owner 字段、中断数组
和原版 fade 对象请求一致。[入口尾部收据](th06nc-title-selection-tail-native-verified.json)。
请求尚未由浏览器逐帧交付，不作为完整淡入动画通过。

ANM bank 新增按资源 slot 卸载和持久的精灵槽绑定对象。已有 VM 会观察到同一
槽被覆盖后的新精灵；卸载后绑定失效，不再继续绘制旧缓存。加载选择资源前先检查
资源是否齐备。原版卸载表清除前缀的九次卸载、1,314 项精灵可用性及 1,017 项
脚本指针检查一致；纹理句柄和 allocator release 未纳入该检查。
[卸载表收据](th06nc-anm-unload-native-verified.json)。
既有 81,360 次 ANM 更新、80 组主菜单组合和 11 项回归重新通过。

当前浏览器主菜单页仍在 state 8 请求处停住；上述入口尚未连接真实纹理更替、
状态改变公共处理、state 9 难度更新与后续角色／射击选择。下一步继续这些路径，
不将资源初始化标为已经可以开始游戏。

## 难度选择与 Start 浏览器路径（2026-11-14）

`title-difficulty-update.mjs` 接入完整 state 9 分支：普通四档导航、Extra 专用
标签、脉动颜色、输入门槛、返回时保存配置难度、确认后的角色初选及解锁回退。
确认／返回前按原版补跑至 30 帧的菜单动画，再设置下一阶段中断；不省略这段更新。
`tools/th06nc-title-difficulty-native-check.py` 执行原版完整分支及真实 ANM，
80 组覆盖普通／Extra、帧边界、选择边界、确认／返回及同帧组合，12,320 份
完整 VM、owner 状态、配置与外部事件参数一致。
[难度分支收据](th06nc-title-difficulty-native-verified.json)。

`title-owner-advance.mjs` 新增已实现主菜单／Start／难度路径的公共推进，包含
state 3 退出时背景过渡中断、时钟条件、动画可用性检查、logo 及背景更新。
支持的状态对是 3→3、3→8、8→8、8→9、9→9、9→10、9→11、11→11；
其它 owner 和回主菜单 tween 仍不支持。192 组使用基础标题资源的原码对照，
25,344 份 VM 状态一致；该组不冒充真实资源更替的完整原码对照。
[公共推进收据](th06nc-title-owner-advance-native-verified.json)。

浏览器主菜单诊断现已连接 3→8→9，使用实际选择 ANM／DDS，并在 bank 卸载后
停止更新失效的旧绑定。原版选择背景纹理、全局淡入淡出和音频事件交付还未接入，
因此难度画面当前背景为黑色，页面明确列出未完成范围。原码分支未实现的 state
10／11 会停在请求处，不能据可见角色动画片段认定角色菜单已完成。

`tools/th06nc-menu-browser-check.mjs` 等待实际页面就绪后操作可见按钮，依次观察
Start → 默认 Normal → 向下选 Hard → 确认发出角色状态 11 请求。
状态序列为 3、9、9、11，选择序列为 0、1、2、0，GL 错误为 0，无页面异常。
[当前浏览器路径收据](th06nc-difficulty-browser-observed.json)。它验证诊断按钮路径，
未验证物理键盘、原版 boot、GPU 像素或完整游戏；此前“确认停在 state 8”的记录
只保留旧版本范围。下一步接角色／射击选择和退出返回路径，并补选择背景及淡入淡出。

## 角色、机体、模式与最终开始确认（2026-11-14）

基础选择流程继续实现 state 11 角色左右切换、state 13 机体上下切换、
state 14 模式、state 24 最终开始确认。输入门槛、重复输入、取消优先级、
配置写回、Extra 的角色／机体解锁回退、30 帧前补跑动画和完整中断数组均从原码恢复。
原码对照分别运行 112／224／224／224 组，比较 owner、配置、事件参数及
全部 154 个 VM 的 288 字节状态；模式确认还真实执行了原版 `4da80` 过渡 helper。
[角色收据](th06nc-title-character-native-verified.json)、
[机体收据](th06nc-title-shot-native-verified.json)、
[模式收据](th06nc-title-mode-native-verified.json)、
[最终确认收据](th06nc-title-launch-native-verified.json)。
上述入口不代表已完成 Practice／Spell 或 Extra 的完整可操作流程。

菜单绘制补上 state 11 已选角色的 RGB 脉动及绘制后状态还原；
160 组、3,280 次绘制入口调用的顺序、位置、颜色和状态恢复与原码一致，
此项观察 GPU 调用入口，未验证最终像素。
[选择绘制收据](th06nc-title-selection-draw-native-verified.json)。
公共 owner 支持的状态对扩展到角色／机体／模式／开始确认与淡出等待，
456 组、60,192 份基础标题资源 VM 比较通过；仍不覆盖真实资源更替和所有其它 owner。
[公共推进收据](th06nc-title-owner-advance-native-verified.json)。

新增全局 `NativeFade`，保留原版 56 字节对象布局、淡出／淡入请求、
已有 alpha 下的起始时钟、f32 插值、完成后 mode 2 保持及 mode 0 隐藏。
50 组请求、5,000 次 tick 的对象逐字节一致。
[淡出收据](th06nc-fade-native-verified.json)。
浏览器按原版选择资源计划显示真实 select00 系列 DDS，并实际渲染全屏 fade；
背景图片和 fade 的 GPU 像素、调度器全局时序尚未做原版完整画面对照。

更新后的浏览器检查覆盖 Start → Hard → 物理右键换角色 → 机体切换 →
两级返回 → 保留角色／机体重新进入 → 模式切换及返回 → 保留模式 →
最终确认及返回 → 最终开始 → 淡出完成。全部 20 个观测点 GL 错误为 0、
无页面异常；最后 fade mode 为 2、alpha 为 255。
[当前浏览器收据](th06nc-difficulty-browser-observed.json)。

现阶段会在 state 25 的真实淡出完成条件处留下游戏交接请求。
**关卡对象创建、ECL 执行、自机／弹幕／碰撞、STD、音频交付、存档和录像仍未实现，
不能将这一菜单路径记为游戏完成。** 先前停止在 11／14 的记录是旧版本范围。

## ECL 执行层与敌人动画（2026-11-14）

定位原版脚本执行循环 `22170..28840`，两级分发表 `28f5c/28d78`。
`EclOperands` 实现浮点／整型源操作数、共享 16 位 RNG、距离、特殊变量赋值、
带实时引用别名的四则运算。乘法 helper 比其它四则运算多一次原始整型源变量
预处理，会影响随机数计数，已按原版保留。
操作数 794 组、赋值 1,023 组、四则运算 2,900 组的完整敌人字节、共享 scratch
和 RNG 状态一致。角度和浮点余数的 CRT thunk 用共同结果供给，原生 CRT 精度
仍排除在这些证明之外。
[操作数](th06nc-ecl-operands-native-verified.json)、
[赋值](th06nc-ecl-assignment-native-verified.json)、
[四则运算](th06nc-ecl-arithmetic-native-verified.json)。

`ecl-command.mjs` 在该阶段包含 54 个无需额外动画服务的指令，以及 97／99 两个
依赖 ANM bank 的动画绑定指令。脚本实际参数去重及补充参数覆盖了运动参数、
范围、生命、计时、状态标志、声音队列、随机赋值、算术和比较；2,142 组单指令
原码比较通过。它本身不是跨帧解释器。
[单指令收据](th06nc-ecl-command-native-verified.json)。

`EclDispatch` 组合时间相等判断、难度掩码、循环及六种比较跳转、子程序参数、
96 字节调用上下文、八层存储的原版计数行为、六种条件调用、中断、返回和删除。
将脚本执行与后续敌人运动及最终时钟提交分开。174 组合成程序执行原版完整
脚本循环、逐字节比较敌人状态，并检查执行指令数量和下一条位置。
[调度收据](th06nc-ecl-dispatch-native-verified.json)。

对七份真实 ECL 的全部子程序从受控上下文开始运行，最多观察前四个脚本时钟，
在首个未移植指令或根返回前明确停止；不把停点之后的脚本当作执行过。
基础命令路径有 319 个子程序、3,394 条连续指令、1,609 个比较状态通过。
[基础前段](th06nc-ecl-prefix-native-verified.json)。

`rebindAnm` 保留原版 setter 未清除的字段，重置必要状态后执行原版零时刻动画。
464 组比较真实执行了原版 ECL 97／99、setter 和 ANM tick，覆盖 12 份关卡敌人
资源的全部最终脚本绑定及缺失脚本情形。
[敌人动画绑定](th06nc-ecl-anm-native-verified.json)。
`stageAssetPlan` 采用原版七关表，敌人主／附 ANM 分别在 slot 8／9，均以 0x100
为精灵和脚本基数；ECL 文件按关卡选择。原版调用参数顺序检查通过，资源 API
返回成功不代表整个关卡初始化已完成。
[关卡计划](th06nc-stage-plan-native-verified.json)。

将这些真实敌人 ANM 加入同一脚本执行前段后，扩大到 408 个子程序、5,470 条
连续指令、2,054 个完整敌人状态比较通过；仍在首个未移植指令和运动阶段前停止。
[带敌人动画的前段](th06nc-ecl-prefix-anm-native-verified.json)。

`advanceEclMotion` 实现脚本后的模式切换、极坐标速度、受限角度归一化、
五种缓动、计时及目标完成边界。1,920 组在原码 `28840..28a7d` 比较全部敌人
字节及数学 thunk 输入一致。三角函数使用同一供给结果，不作为 native CRT
精度通过；此阶段尚不包含 manager 的位置积分、发弹、自动转向动画或碰撞。
[运动阶段](th06nc-ecl-motion-native-verified.json)。

浏览器尚未将菜单 state 25 之后接到实际关卡。STD、时间线敌人生成、完整 ECL
指令、弹幕、自机、碰撞及音频／存档／录像仍有必要工作，整作目标继续进行。

## 时间线、敌人池与连续更新（2026-11-14）

ECL 命令增加 51–64 移动／缓动，以及 67–81、201 的弹幕参数、rank 修正、
随机间隔和发射请求。当前单命令列表共 84 个 opcode，另有依赖 ANM bank 的
97／99；实际参数与补充样本的 3,854 组原码比较通过。弹幕管理器调用被记录，
这里尚未实际生成子弹。1,110 组 rank 0／8／16／24／32 对照同时检查数量、
速度、间隔、RNG 和发射参数。
[更新命令收据](th06nc-ecl-command-native-verified.json)、
[rank 收据](th06nc-ecl-shot-rank-native-verified.json)。

`finishEclEnemyFrame` 处理重复发射请求、移动方向变化后的 ANM 重绑、自定义
回调和脚本时钟提交。864 组原码比较执行了实际 ANM setter／tick；子弹及自定义
回调作为观测服务替代，不扩称实际弹幕行为通过。
[帧尾](th06nc-ecl-enemy-tail-native-verified.json)。
`tickEclEnemy` 将脚本、运动和帧尾组合，174 组合成程序执行至原码 ECL 更新器
尾部全部一致。[组合 tick](th06nc-ecl-tick-native-verified.json)。
七份真实脚本在同一组合下的受控前段，现在有 424 个子程序、10,994 条连续
指令、2,149 个完整敌人状态检查通过。仍在首个未移植指令／根返回前停止，
世界 manager、玩家和真实子弹不在该检查内。
[真实脚本组合前段](th06nc-ecl-prefix-tick-native-verified.json)。

`createEnemyTemplate` 与 `EnemyPool.spawn` 保留原版 0x10b0 字节模板、256 槽
扫描、调用者变量复制、出生位置、生命／道具／分数覆盖和出生即执行第一次 ECL。
108 组实际执行原版模板构造和普通生成 helper，比较模板及生成后的全部敌人
字节与 RNG。阶段 1 的真实 ECL／ANM 在这里执行；数学 thunk 供给同一结果。
[敌人池](th06nc-enemy-pool-native-verified.json)。
`integrateEnemyPosition` 单独实现 manager 在 ECL 前的位置积分、镜像 X 速度与
边界约束，120 组原码逐字节比较通过。
[位置阶段](th06nc-enemy-position-native-verified.json)。

`EclTimeline` 接普通时间线 0–12 号行为：普通与随机位置生成、生成后镜像、
角色对应的对话请求、等待条件、预留敌人中断、参数字及指定槽等待。
七份实际时间线的每个事件附近，7,305 组时刻／控制组合、2,713 个外部事件及
controller／RNG／镜像位比较通过。生成与对话 API 被观察，不能据此宣称完整
敌人或对话世界已运行；Spell 分支及 checkpoint/resume 边界尚需额外验收。
[时间线](th06nc-ecl-timeline-native-verified.json)。

`advanceEnemyAnimations` 与 `drawEnemyAnimations` 连接主动画、八个附属动画、
结束后的 ID 清除、移动方向角、绘制层次和游戏区域偏移。原版实际 ANM 更新、
16 组 owner 绘制条件、36 个底层绘制调用及完整敌人状态一致。
[敌人动画与绘制](th06nc-enemy-animation-native-verified.json)。
原版 3D ANM／GPU 像素仍未实现。

`tickOrdinaryEnemy` 组合 manager 的位置积分、首次入场标志、出屏回收、ECL、
动画、碰撞／伤害请求、模式伤害换算、得分、目标坐标、受伤闪烁和生命时钟。
30 个场景连续执行原版 manager 共 7,200 帧，559 个完整状态检查点一致；
首个场景的 240 帧全部逐帧比较。三角函数、玩家伤害／身体碰撞、发弹和时间线
作为受控服务提供，不能据此认定真实玩家、弹幕、碰撞或关卡已通过。
该模块遇到 boss、死亡、阶段转换和关联效果时明确报未实现。
[普通敌人连续更新](th06nc-enemy-ordinary-native-verified.json)。

## 普通敌人的死亡、阶段与关卡组合（2026-11-14）

`finishOrdinaryEnemyDeath` 实现普通敌人死亡时的八种标志分支、得分、
道具掉落循环、音效、效果请求和死亡脚本切换。1,728 组直接执行原版死亡段，
完整敌人内存、事件顺序、掉落计数及音效队列一致。实际道具和效果实体仍由
待实现的管理器提供；boss 清弹与结算不在此验收范围。
[死亡段对照](th06nc-enemy-death-native-verified.json)。

`advanceOrdinaryEnemyPhase` 接生命阈值与超时转换，并同步处理其他普通敌人的
生命清零和死亡脚本跳转。180 组场景、900 次完整敌人状态比较通过。
超时清弹入口被观察；测试中弹池为空，尚未验证真实子弹／激光的清除。
[阶段转换对照](th06nc-enemy-phase-native-verified.json)。
上述两段已接回 `tickOrdinaryEnemy`；72 个场景连续执行原版 manager 共
17,280 帧、1,021 个检查点通过，覆盖死亡类型、受伤、超时和阈值路径。
该验收仍使用受控的玩家查询和数学服务。

ECL 单指令支持扩展到 92 项，新增随机方向、弹幕附加参数、音效标志、
激光槽索引、方向 ANM、无栈调用标志、激光指针清空和极坐标发射偏移。
4,098 组原版完整敌人状态／RNG／scratch 对照通过。
110 号立即中断调用接入 dispatch，180 组脚本调度对照通过。
[单指令](th06nc-ecl-command-native-verified.json)、
[脚本调度](th06nc-ecl-dispatch-native-verified.json)。

`EnemyWorld` 按原版顺序组合时间线、敌人生成池、256 个槽位的敌人更新、
动画与世界时钟。验收脚本最初扩展 JS 到 1,200 帧时漏改了原版侧的 360 帧
循环，因此当时的 9,600 帧／744 检查点统计无效。现已统一两侧帧数来源，
并断言每个声明的检查点都实际被比较，重新执行第一面前 1,940 帧。
四个难度、两种受控伤害下，共 15,520 帧、1,176 个检查点和 13,837 次完整
敌人状态比较通过。生成、镜像、脚本、动画、死亡、槽位复用、RNG、得分、
时钟，以及首次 boss 注册、血条和章节计时在这一范围内一致。
[关卡组合对照](th06nc-enemy-world-native-verified.json)。
这不是完整游戏验收：子弹、道具、效果、玩家实体、boss、背景、音频与 GPU
仍有待实现部分。探索运行在第一面第 1,883 次 manager 更新遇到尚未实现的
101 号 boss 注册指令（现已实现，详见下节）；菜单的 state 25 也尚未正式
交接到完整游戏。

## Boss 状态与效果管理器（2026-11-14）

`boss-state.mjs` 连接 101 号注册／注销、八个保留槽和游戏时间线的生成抑制，
实现 manager 的两条血量比例计算。40 组注册与 720 组血条数值直接运行原码
比较通过，包含非正最大生命、阈值、对话时保持原值等边界。
[Boss 状态](th06nc-boss-state-native-verified.json)。
阶段转换对照扩展为普通敌人和 boss，360 个场景、1,800 次敌人完整状态比较
通过，并比较 boss 倒计时。完整 boss 死亡、结算和 Spell Practice 完成分支
仍未实现。126 号章节指令已连接章节值及 messageClock 加 1,800 的行为。

原版精灵缓存的 `+1c/+20` 是逻辑高／宽；文件 `extra` 的实际顺序是宽／高。
零值按对应像素尺寸乘 480、再除 1,080，并分别舍入至 float32 补齐。
`spriteLogicalSize` 已用于出入场判定；全部 125 份 ANM、2,273 个精灵的逻辑
尺寸通过原版 loader 核对，其中 1,741 个精灵至少一个维度需要默认值。
[逻辑尺寸](th06nc-sprite-layout-native-verified.json)。

`common-layout.mjs` 从原版调用点确定 etama3（slot 6/base 512）、
etama3_2（slot 52/base 666）、etama4（slot 7/base 698）。效果脚本主要来自
etama4，不能把未被该调用点加载的 eff00 代入。各关效果资源 slot 11/base 723；
第 1–7 面实际使用 eff01、02、03、04、05、05、04。资源 API 对照通过。
[公共资源计划](th06nc-common-layout-native-verified.json)。

`EffectPool` 实现 512 个效果槽、额外耗尽返回槽、循环扫描与复用、全部 21 种
效果的创建和真实 ANM 绑定。378 组原版 helper 比较完整池内存、返回槽、
游标与 RNG 通过；测试使用原版对应的 etama4 和第一面效果资源。
[效果生成池](th06nc-effect-pool-native-verified.json)。
`effect-update.mjs` 与 `effect-orbit.mjs` 已接常见爆炸漂移、线性运动、boss 光环
的轴归一化／四元数／矩阵变换及结束后的缩放淡出。540 组回调状态以及 18 个
场景、2,160 帧实际效果 manager／ANM 连续对照通过。光环使用相同受控三角
函数结果；其余回调、原版 CRT 精度、绘制和 GPU 尚未因此验收。
[效果更新](th06nc-effect-update-native-verified.json)。

102 号指令连接真实效果状态句柄，`enemy-linked-effects.mjs` 处理跟随位置、
强度增长、角度循环和回收通知。242 组原版块比较通过；创建在此专项测试中
是受控服务。该专项验收之后增加了下述联合运行验证。
[关联效果](th06nc-enemy-linked-effects-native-verified.json)。

## 联合效果运行与 boss 结束路径（2026-11-14）

`StageWorld` 接敌人 priority 9、效果 priority 10 的同帧顺序；效果共享游戏 RNG，
敌人死亡及 102 号关联效果直接创建 `EffectPool` 实体，之后实际执行效果回调
与 ANM。第一面 Easy／Normal 前 5,000 帧、Hard／Lunatic 前 2,200 帧，分别在
两种受控伤害下，原版两套 manager 共 28,800 帧通过；2,012 个检查点、31,371
次敌人完整状态及整个效果池比较一致。Easy／Normal 范围已包含中 boss 的
死亡／退出、死亡子脚本、关联效果淡出及后续普通波次。
此处发弹、道具生成和玩家查询仍是受控服务，没有证明真实弹幕或玩家世界。
[敌人／效果联合运行](th06nc-stage-world-native-verified.json)。

`endSpell` 对接 94 号指令，包含转换请求、符卡奖励的有符号整数计算、HUD
奖励状态、普通／Spell Practice 捕获计数、最近五个角色历史、录像时跳过
成绩写入及 Extra 特例。896 组直接执行原版指令块，比较全记录、奖励、成绩、
计数和服务事件通过。UI 绘制和磁盘持久化仍未完成。
[符卡结束](th06nc-spell-end-native-verified.json)。

`cancelBossProjectiles` 实现 boss 死亡时扫描 640 个子弹槽、设置转换状态 5、
递增点数标签，以及 64 个激光槽的结束模式／时钟设置。18 组完整池比较通过。
子弹实体位置在槽 `+30`、状态在 `+44`；原版 manager 的第一个槽位于 `+8`，
不能把位置指针误当作槽起点。
[死亡清弹](th06nc-projectile-cancel-native-verified.json)。
该接口已接回敌人死亡段，1,728 组 boss 死亡原码比较覆盖生命、类型分支、
全敌人状态、得分、清弹池、奖励提示和事件顺序。原版段中的活动 boss 标志
清除、关联效果结束通知、死亡子脚本及普通道具掉落同时保留。
[Boss 死亡](th06nc-boss-death-native-verified.json)。
这仍不是整个 boss 战的联合验收：StageWorld 需要真实弹幕 manager 提供清弹
服务；当前联合 fixture 的发弹被观察，子弹池为空。

118／119／124 号指令接效果、随机散布道具及指定道具请求；119 号包含 power
低于 128 时首个大 power、后续小 power，以及高 power 的 point-item 创建边界
和 Spell Practice 跳过分支。120 组原码请求／RNG 比较通过。时间线 11 号设置的
word 同步到 `environment.playerPower`；全部时间线的 7,305 组对照仍通过。
[生成服务](th06nc-ecl-spawn-services-native-verified.json)。
下一段真实第一面流程在 Hard 的中 boss 阶段转换遇到 93 号符卡开始；该段
包含名称翻译、UI 动画／文字、记录校验和与尝试计数，尚待接入。

`messagepack.mjs` 已读取 th06IN.dat 中原版 `localization.msgpack` 和
`spellpractice.msgpack`。独立 Python msgpack 解码逐树比较通过，包含 1,152 个
本地化 key、13,824 条语言文本和 131 条版本 6 的符卡练习记录。
该证据只覆盖二进制读取，尚未把语言选择、文字绘制或练习流程算作完成。
[MessagePack 数据](th06nc-messagepack-verified.json)。

## 符卡开始状态与激光创建（2026-11-14）

`beginSpell` 接入 93 号指令的名称 key、演出请求、音效 14、捕获状态、134 项
基础奖励表、清弹请求、背景控制和发弹 rank 参数复位。符卡记录采用原版
`0x180` 字节布局，保留普通尝试／捕获、五次角色历史、成绩及练习模式计数。
名称校验和变化时按原版清空 `+3c..+17f`，并区分录像与 Spell Practice 分支。
576 组完整敌人／记录／全局状态比较及全部 134 项奖励表核对通过。
[符卡开始状态](th06nc-spell-begin-native-verified.json)。
这里的文字翻译、字体和 HUD ANM 发布仍是接口，尚未被该状态验收证明。
联合 fixture 在原版同一发布边界跳过 UI 段，仅继续执行已对应的状态段。

联合关卡验证随后扩展为：Easy／Normal、Hard／Lunatic 无伤害各前 5,000 帧，
Hard／Lunatic 有伤害各前 2,330 帧，总计 34,660 帧、2,378 个检查点、43,000 次
敌人状态及完整效果池比较通过。增加了符卡控制与原版记录字节比较，Hard／
Lunatic 已覆盖中 boss 的符卡开始，停止点位于尚未连接的激光更新之前。
[当前联合验证](th06nc-stage-world-native-verified.json)。

`LaserPool` 实现原版 64 槽激光构造、池满返回槽、两份真实 ANM 绑定、颜色
精灵映射、瞄准角、模式／时钟／参数复制及练习结束抑制。768 组原版 helper
比较完整激光池、返回句柄和 RNG 通过。
[激光创建池](th06nc-laser-pool-native-verified.json)。
85／86 号 ECL 指令已配置激光描述符并保存句柄，148 组原版指令体比较通过，
包含真实脚本参数、变量解析与构造服务失败。激光的逐帧生命周期、碰撞、
绘制及 StageWorld 中的实池接线尚未实现，不能据此宣称已完成激光弹幕。
[ECL 激光配置](th06nc-ecl-laser-native-verified.json)。

## 激光逐帧、接触与绘制（2026-11-14，续）

上节的“尚未实现”描述对应当时的构造阶段，后续已接入 `StageWorld` 的真实
激光池。原版任务顺序为敌人 9、效果 10、弹幕 11。激光预警、持续、消退、
尾端裁剪、时钟及主 ANM 更新通过 972 组完整状态比较；ECL 88～92 的保存
句柄控制通过 720 组比较。`spellCounter` 同时控制敌人符卡期间的伤害缩减，
不能只把捕获资格 `spellActive` 当作该条件。
[激光逐帧](th06nc-laser-update-native-verified.json)、
[激光句柄控制](th06nc-ecl-laser-control-native-verified.json)。

第一关四难度、伤害 0／20 的八组场景均真实执行 5,000 帧，总计 40,000 帧、
2,712 检查点，比较敌人、效果及激光池。该版本普通子弹／道具／UI 发布仍是
受控服务。另一组接触验证使用实际 `6aba0` helper，四难度各两个靠近激光的
静止自机位置，共 40,000 帧；断言实际覆盖 2 个命中场景及 2 个擦弹场景。
自机中弹后的死亡／重生时序尚未执行，不能把静止自机接触证明扩大为完整玩法。
[联合世界](th06nc-stage-world-native-verified.json)、
[实际激光接触联合验证](th06nc-stage-contact-native-verified.json)、
[独立接触 helper 1,800 组](th06nc-player-laser-contact-native-verified.json)。

激光 draw owner 的束身／起点位置、缩放、颜色和调用顺序通过 168 组、432 次
绘制请求比较。浏览器初次截图暴露了两者脱开的偏差：束身原版走 `4dc0`
世界坐标绘制，起点走 `67f0` 二维绘制；统一走二维会把束身长度缩短。
新增 `anm-world-quad.mjs` 按原版 UV 矩阵、256 单位底板、XYZ 旋转和锚点
生成世界顶点；实际执行原版底板初始化，320 组 XYZ／UV 字节比较通过。
WebGL 的束身已使用世界坐标路径，起点保持二维路径，截图中的断开已修正。
当前投影只支持 Z=0 游戏平面，非平面顶点明确报错，STD 相机仍待实现。
[绘制 owner](th06nc-laser-draw-native-verified.json)、
[世界顶点](th06nc-anm-world-quad-native-verified.json)、
[浏览器五阶段检查](th06nc-laser-browser-observed.json)。

## 普通子弹构造和逐帧管理（2026-11-14）

`bullet-pattern.mjs` 覆盖原版 `f870` 的全部 9 种角度／速度分布，包括逐层减速、
奇偶排列、圆周排列、随机角度和随机速度。1,512 组比较同时核对共享 RNG
种子、计数和有限次数角度归一化。
[发弹分布](th06nc-bullet-pattern-native-verified.json)。

`BulletPool` 实现 640 个 `0x620` 字节槽、循环寻找空槽、十类五 ANM 模板、
出场动画选择、颜色绑定、消弹动画、变速／转向参数及音效队列。实际执行
原版模板初始化后逐类比较，再核对 1,560 组完整子弹池、池指针及 RNG。
核对发现并修正：主精灵按颜色切换后，消弹颜色映射必须读取新精灵的逻辑
尺寸；原版第十类模板的部分颜色会跨越尺寸分类。
[构造与模板](th06nc-bullet-pool-native-verified.json)。

`bullet-motion.mjs` 接入初速衰减、直角加速、角速度／速度加速、定时相对／绝对
／瞄准转向，以及四边或三边反弹。1,620 组完整子弹字节比较覆盖周期前后、
复合 flag 优先顺序及离屏边界。
[运动](th06nc-bullet-motion-native-verified.json)。

`bullet-update.mjs` 接入出场、普通及消弹状态、真实 ANM tick、离屏回收、256 帧
离屏保留、擦弹、碰撞服务和最终时钟。第一组完整原版管理器调用比较包含
70 个场景、8,400 帧、420 检查点，使用静止无敌自机关闭擦弹，炸弹区域和
点道具更新仍为受控服务。故该证明尚不覆盖擦弹反应或实际道具实体。
[逐帧管理](th06nc-bullet-update-native-verified.json)。

另已实现原版 `6a980` 普通弹接触 helper，含圆形／矩形检测、炸弹区域优先
取消、实际中弹效果和反应字段；1,800 组原版 helper 比较通过。
自机控制与死亡／重生循环仍待接入。
[普通弹接触](th06nc-player-bullet-contact-native-verified.json)。

第一关联合验证随后纳入真实普通弹池：八种难度／伤害组合各 5,000 帧，总计
40,000 帧、2,712 检查点、46,173 次敌人状态比较，额外比较完整普通弹池、
分配指针、活动数及原有效果／激光池。仍使用受控自机查询、炸弹区域、道具
和 UI 发布服务，未声称覆盖实际玩家操控或完整关卡。
[含普通弹的联合世界](th06nc-stage-projectile-native-verified.json)。

联合执行在第 3,328 帧发现 boss 超时的原版内联清弹未接入实际子弹池。
`cancelTimeoutProjectiles` 现按 `37039..3709f` 将普通弹转入消弹状态并终止
激光，且不发布成绩／道具。修复后上述 40,000 帧全部通过，另有 18 组完整
池边界比较通过。普通清弹、超时清弹及 boss 击破的加分清弹具有不同语义。
[超时清弹](th06nc-timeout-projectile-native-verified.json)。

普通弹绘制已接入原版四次尺寸／脚本分类遍历，选择当前状态的 ANM，更新
位置、旋转和颜色。14 组、96 次原版绘制请求及完整池字节比较通过；浏览器
验证加载真实 ANM／DDS，显示 162 发普通弹的九种发弹分布，生成、出场、
飞行、消弹及清空五个阶段均通过像素存在性／GL 错误检查。该检查没有比较
原版像素，也没有模拟自机操控。
[普通弹绘制](th06nc-bullet-draw-native-verified.json)、
[浏览器观察](th06nc-bullet-browser-observed.json)。

随后联合执行真实普通弹／激光接触 helper 与真实效果池：四难度、两个静止
自机位置各 5,000 帧，共 40,000 帧、2,712 检查点、21,682 次敌人状态比较。
断言覆盖 2 个中弹场景、3 个擦弹场景，同时比较完整普通弹、激光、效果池、
共享 RNG、分数、音效及中弹反应字段。自机位置固定，中弹后保持状态 2，
没有死亡／重生循环；炸弹区域和道具仍为受控服务。
[实际弹幕接触联合验证](th06nc-stage-projectile-contact-native-verified.json)。

## 自机移动、状态与射击（2026-11-14）

`PlayerState` 使用原版 `0xa2b8` 字节 owner 布局，并向既有接触 helper 提供
position、state、hitRadius、死亡决死窗口及动画时钟接口。两角色／四机体的
真实 `player00/01.anm` 初始化、普通／Spell Practice 入场区别，8 组完整 owner
和 RNG 比较通过。输入的全部 256 个低字节组合、低速和斜向速度选择通过
1,024 组比较；位置积分／边界／查询区域通过 2,560 组比较。
[初始化](th06nc-player-init-native-verified.json)、
[输入](th06nc-player-input-native-verified.json)、
[位置](th06nc-player-motion-native-verified.json)。

连续方向输入时接入真实左右转身 ANM 绑定，四机体共 1,024 帧完整 owner 比较
通过。僚机展开／收束与中途反向通过 280 组状态比较。中弹后的决死窗口、
掉落请求、火力损失、死亡缩放、重生、残机／炸弹补充、无敌闪烁及清弹时钟
通过 1,920 组原版状态段比较；该独立证明将动画发布／掉落实体作为明确边界。
[连续移动与动画](th06nc-player-movement-native-verified.json)、
[僚机转换](th06nc-player-options-native-verified.json)、
[生命状态](th06nc-player-life-native-verified.json)。

从已核对散列的原版 EXE 提取四机体、36 个火力区间、193 条 36 字节发弹
记录，保留原始浮点位。通用 shot builder 的周期、僚机起点、激光通道冷却、
伤害、速度、ANM 和音效通过 2,702 组原版 wrapper 比较；80 槽分配／激活和
发射时钟通过 1,728 组比较。自机弹直行、追踪、加速、激光长度、通道中断和
ANM 寿命通过 72 场景、8,640 帧、432 检查点比较。
[发弹表](th06nc-player-shot-programs-extracted.json)、
[构造](th06nc-player-shot-build-native-verified.json)、
[分配与时钟](th06nc-player-fire-native-verified.json)、
[自机弹更新](th06nc-player-shot-update-native-verified.json)。

随后真实执行整个原版 `68820` 自机更新函数，对四机体、火力 0／128、普通／
入场／中弹三个初态各运行 180 帧：24 场景、4,320 帧、264 检查点全部通过。
比较完整 owner、自机及所有 shot ANM、共享 RNG、掉落请求、残机、火力、
炸弹数和音效队列。此时仍未实现炸弹 callback，自机按炸弹键会明确报未实现；
掉落实体、对敌伤害查询、键盘交付及 GPU 绘制也不在此验收范围内。
[完整自机更新顺序](th06nc-player-update-native-verified.json)。

`queryPlayerDamage` 接入实际普通弹、爆炸弹／激光和 32 个炸弹伤害矩形，处理
命中 ANM、爆炸范围／伤害衰减、慢速消失、效果请求和 critical 标记。576 场景、
1,728 次重复查询比较完整自机 owner、伤害、critical、效果及 RNG 通过。
[对敌伤害](th06nc-player-damage-native-verified.json)。

`StageWorld` 现按原版 priority 7／9／10／11 顺序执行真实自机、敌人、效果和
弹幕，自机弹伤害直接由敌人查询。Normal 四机体各连续移动／射击 5,000 帧，
使用真实三角函数数值，共 20,000 帧、1,548 检查点、15,148 次敌人状态比较
通过；四组均覆盖中弹、擦弹、死亡和重生。起始残机为 9，以保持自动运行，
道具实体、符卡 UI 和部分清弹发布仍是受控边界，未完成整关流程／炸弹回调。
联合比较暴露并修正了普通弹擦弹扩展值：原版擦弹用 20，炸弹区域预查询用
18.888889，两者不能共用常量。也将自机 owner 长度收紧到构造函数实际清空的
`0xa2b8`，避免把紧邻的音效全局区混入 owner；受影响的六项自机比较均重跑通过。
[真实自机战斗联合验证](th06nc-stage-live-player-native-verified.json)。

自机绘制 owner 的子弹旋转、主精灵／僚机位置、可见性和绘制顺序通过 128 组、
2,800 次原版请求比较。浏览器真实 keyDown／keyUp 验证四机体的方向键移动、
Z 射击、Shift 低速、松键停止移动及弹体自然结束，检查可见像素和 GL 错误。
魔理沙 B 的原版激光通道持续 330 帧，松开 Z 后现存激光仍按该时序结束。
该浏览器检查使用手动帧推进，不声称覆盖实际墙钟帧率或原版像素等价。
[自机绘制](th06nc-player-draw-native-verified.json)、
[自机浏览器输入](th06nc-player-browser-observed.json)。

## 道具池与运动（2026-11-14）

`ItemPool` 接入原版 `426e0`：普通掉落与清弹小点共用 1,024 个 `0x160` 字节
槽，另有原版保留槽。七类道具、三种掉落模式（普通／自动回收／死亡散落）、
练习过滤、边界限制、循环分配、池满和真实 ANM 绑定共 1,512 组完整池／RNG
比较通过。死亡散落参数保留两次原版 float01 的精确消耗及计算顺序。
[道具构造](th06nc-item-pool-native-verified.json)。

`advanceItemMotion` 接入下落、上部回收线追踪、无效自机状态下取消自动回收、
死亡散落的 60 帧插值及离屏回收；675 组完整 item 字节比较通过，覆盖回收线
128 的边界、插值终点和 Y=464 的消除。这里只验证运动段，尚未实现拾取后的
火力／残机／炸弹／分数结算，也尚未把实际道具池接入 StageWorld。
原版道具更新实际由 priority 11 的弹幕任务在普通弹更新前调用，并非单独的
priority 8 任务。死亡掉落使用 mode 2，不能在接线时丢失成普通布尔标记。
[道具运动](th06nc-item-motion-native-verified.json)。

## 道具拾取、消弹转换与实战接线（2026-11-14）

在上述阶段后，七类拾取分支 `42d5a..43796` 已实现：小／大火力、点道具、
炸弹、满火力、残机与消弹星点，包括火力等级提示、满火力道具连锁分数、
难度相关点道具价值、残机保护、计数器回绕及声音队列。3,024 组完整道具、
515 槽分数弹字池、全局数值和提示数据对照通过。
`4ff0dd` 的真实含义是数字型满火力道具连锁计数 `powerItemChain`；此前
自机代码将其命名为布尔标记，现已纠正，并重跑自机生命和整帧对照。
[拾取结算](th06nc-item-collect-native-verified.json)、
[分数弹字双环](th06nc-score-popup-pool-native-verified.json)。

`ItemPool.tick` 完成 `42980` 的整帧顺序：运动、拾取矩形、结算或 ANM／计时、
整帧一次拾取音。36 场景、4,320 帧、216 检查点的完整池、弹字、火力、
残机／炸弹、分数及 RNG 对照通过。原版 C++ TLS 静态初始化由夹具预置，
三角函数由两端提供相同结果。[道具整帧](th06nc-item-update-native-verified.json)。

默认 `StageWorld` 现实际拥有道具池与弹字池：自机 priority 7，敌人 9，
特效 10，道具随后在 priority 11 中先于普通弹／激光更新。自机死亡掉落
明确保留 mode 2。显式提供旧 dropItem 观察服务的夹具继续控制道具边界。
四自机 Normal 各 5,000 帧、合计 20,000 帧、1,548 检查点通过真实自机、
敌人、子弹、激光、道具、特效、分数和 RNG 联合对照。
[实战道具](th06nc-stage-live-items-native-verified.json)。

`projectile-clear.mjs` 实现完整 `EF00` 和 `F300`。前者清除普通弹槽并转星点，
或启动消弹动画；后者保留消弹态、发布逐弹分数并合计入总分。激光转点
沿束每 32 单位采样，`F300` 额外在激光原点生成一点；已进入淡出态的激光
不重复生成。两函数分别 72 组完整三种实体池／游标／RNG 对照通过，涵盖
道具池满及溢出保留槽；计分版本额外核对全部弹字和 HUD 提示。
[EF00](th06nc-projectile-clear-native-verified.json)、
[F300](th06nc-projectile-score-clear-native-verified.json)。

默认关卡服务已采用真实转换。在 20,000 帧联合夹具中，于 3,700 帧注入一次
满火力拾取、3,800 帧调用计分转换，两路径分别实际执行 4 次；完整实体池、
连锁数、点道具计数、分数和 RNG 继续通过。该注入用于覆盖路径，并非声称
第一关这两个时间点原本就会触发上述事件。
[联合转换](th06nc-stage-live-item-conversion-native-verified.json)。

`item-draw.mjs` 实现 `11b0a..11c2a` 的道具位置、屏外箭头、透明度下限及回到
场内的图标恢复，32 组／112 次绘制调用和完整实体池对照通过。
浏览器 [item-lab](../../runtimes/th06nc/item-lab.html) 使用真实 ANM／DDS，
四场景按钮、掉落、屏外箭头、死亡散落和七类自动拾取通过 CDP 检查，
WebGL 无错误，截图已检查。自动回收场景中七件全部拾取，火力 128、残机 3、
炸弹 3、点道具计数 1、总分 101,860。分数弹字仍仅有状态／数位数据，
字体绘制未接入。[道具绘制](th06nc-item-draw-native-verified.json)、
[浏览器检查](th06nc-item-browser-observed.json)。

这些是已注明边界的子系统证据，不等同整作完成。完整关卡／模式、炸弹、
STD 背景、消息与字体、音频、菜单到游戏交接、录像和存档等工作仍需继续。

## 分数弹字更新与真实字形（2026-11-14）

在上述道具接线之后，补上原版共用文字任务的弹字部分：priority 1 的
`90d0` 每帧上浮 0.5、递增计时并在新计时大于 60 时删除。故事／结束等 UI
接管时暂停普通弹字；112 组全 515 槽、计时有符号边界、失活槽及 UI 标记
组合对照通过。[弹字更新](th06nc-score-popup-update-native-verified.json)。

`score-popup-draw.mjs` 完成 `9790` 的数字 VM 初始化与 `92a0` 的全部数字绘制，
使用 th06IN.dat 的 `ascii.anm`／`ascii.dds`。按逆存数字顺序绘制，保持原版
共用 VM 的直接精灵指针切换，以及 Power Up 字样前后的 UV 尺寸变更。
36 组／180 次绘制调用及 VM 字节对照通过。
[数字绘制](th06nc-score-popup-draw-native-verified.json)。

默认 StageWorld 已在自机更新之前运行弹字更新，并由
`popupUiActive`／`gameOverRequested`／`hideDuringRespawn` 或显式的
`popupSuspended` 服务决定暂停。带两次受控转换的 20,000 帧联合夹具重新
通过，弹字池现在也比较逐帧上浮和到期后的结果；其证据对应最新 StageWorld。
[带弹字更新的联合对照](th06nc-stage-live-popup-native-verified.json)。

道具浏览器页已显示真实 ASCII 数字／Power Up 字样，拾取后第 30、60 帧
可见弹字，第 120 帧全部消失；四场景、结算、像素存在与 WebGL 检查再次
通过，并检查了实际截图。上节“字体绘制未接入”仅描述此前的阶段，当前
数字弹字已接入；剧情文字和通用字体消息仍未完成。

继续向后运行第一关时，当前流程在时间轴 5,092 帧到达实际剧情消息入口。
该位置已明确抛出尚缺消息服务，未跳过对话来宣称关卡完成；后续需实现消息
资源、消息状态及其与时间轴等待／Boss 战的衔接。

## 剧情消息结构与开场状态机（2026-11-14）

`tools/th06nc-message-prepare.mjs` 按独立 PKGL 解包证据的 SHA-256 提取七份
`msg1.dat`～`msg7.dat`。`message.mjs` 读取 u32 脚本数／偏移表和
u16 时间、u8 指令、u8 参数长度的记录，保留脚本别名。独立 Python 解码
逐表／逐记录核对通过：92 个脚本 ID、43 段唯一脚本、49 个别名表项、
2,823 条记录，全部 0～14 号指令均存在；6 种损坏边界输入被拒绝。
[消息结构](th06nc-message-structure-verified.json)。

`message-open.mjs` 对应 `3ece0`，恢复原版消息窗口三段清零、默认颜色、
文字模式、脚本指针、消弹和特殊关卡资源请求。七文件全部脚本 ID、越界 ID、
阶段条件及旧数据保留共 594 组完整 HUD 字节／弹幕池／资源请求对照通过。
`MessageState` 保存原版 HUD 偏移和真实 ANM 视图。
[消息打开](th06nc-message-open-native-verified.json)。

`message-command.mjs` 实现 0／1／2／3／4／5／6／8／10／13 的结束、肖像脚本
与精灵、两类台词、等待、动画中断、同步信号、保持和跳过控制。7,990 组
原版记录及输入变体的消息字段、肖像 ANM 和文字发布参数对照通过；原版
清第二行实际发布一个空格，而非空字符串。
[通用消息指令](th06nc-message-command-native-verified.json)。

正数音乐指令 7 已接入真实音乐标题 VM、标题键、播放路径及特殊 HUD 恢复；
`stage-music.mjs` 直接读取 STD 头中原版使用的四组标题／路径字段，此模块
不代表 STD 的 3D 背景程序已移植。文字贴图发布、本地化查找和音频传输在
此对照中是可观察服务。`message-update.mjs` 执行整帧时序、输入门控、七个
ANM 更新和消息框渐显。第 1～6 关、两个角色、自然等待／跳过／按键推进
共 36 场景、80,016 帧、3,349 检查点的完整消息 owner 对照通过。
[开场消息整帧](th06nc-message-update-native-verified.json)。

原版 `41d58` 为调用消息更新的任务设置 priority 12。可选 `messageProgram`
已连接 StageWorld 的默认打开服务，并在弹幕 priority 11 之后更新消息；
自机和敌人则读取上一帧消息字段。四种自机 Normal 各 7,000 帧、合计
28,000 帧／2,048 检查点／21,023 个敌人状态的联合对照通过，覆盖第一关
5,092 帧的消息入口、对话推进及其后的 Boss 战。该夹具仍控制台词贴图／
本地化／音频传输，并未运行整个 HUD 更新或验证消息像素。
[带消息的关卡联合对照](th06nc-stage-live-message-native-verified.json)。

此阶段尚未实现的消息路径为负数音乐停止及 9／11／12／14 的后段关卡／
结束过渡；后续实现与验证见下文。不能据开场对话通过推断全关卡或全部模式已经完成。

## 原版字形图集与排版（2026-11-14）

确认 th06FN.dat 提供按字号、四组颜色和语言分组的字形资源；除了
TexturePacker JSON／DDS，原版还读取独立的 `advance_<key>.txt` 浮点字距。
`tools/th06nc-font-prepare.mjs` 按原有独立解包哈希核验并提取全部 165 组元数据，
合计 27,187 个字形条目／117,090,517 字节。原始归档中有 20 组元数据没有
同名 DDS，清单明确记录 `bitmapAvailable:false`；没有生成替代贴图。
当前对话的白字、淡色字和音乐标题所需图集均存在。

`font-atlas.mjs` 合并字距与精灵矩形，保留仅有字距的空格，并实现原版
`7d455..7d624` 的整数落点、double 精度小数字距累加、未知字形默认前进
18 以及文字边界结果。全部 165 组图集、1,650 例、56,224 次字形 blit 请求
与原生段对照通过，包括 ASCII、多语言、缺字和 NUL 结束。UTF-8 解码、
缓存查找、modf 与底层图形调用由夹具提供；这证明排版／边界，不证明 GPU
文字贴图已经发布。后续仍需把真实图集 blit、动态文字 ANM 和消息绘制接回。
[字形排版](th06nc-font-layout-native-verified.json)。

## 原版消息资源接线纠正与文字发布（2026-11-14）

继续核对 HUD 初始化 `3d500` 后，纠正此前受控夹具的资源假设：消息背景
由 slot 64、基址 `0x785` 的 `msgframe.anm` 提供；台词、音乐标题等使用启动
`7a817` 加载的 slot 0、基址 `0x72f` 的 `text.anm`。后者贴图名为 `@`，
表示 2,048×2,048 可写文字贴图，并非 DDS 资源。`0x730` 是该资源的音乐
标题脚本，不能当作消息背景脚本。肖像资源实际使用 slots 15～20；第六关
预载 face09b／face10a／face10b，第七关预载 face08a／face12a／face12b。
`message-layout.mjs` 的全部七关／两角色、14 组加载请求已与实际初始化
代码比较通过。[消息资源布局](th06nc-message-layout-native-verified.json)。

StageWorld 现要求真实 `0x731` 台词及 `0x785` 消息背景脚本。通用指令
7,990 例、完整开场 80,016 帧，以及关卡联合 28,000 帧都在纠正后的资源上
重跑通过。关卡联合夹具的 stageIndex 同时设为原版第一关的值 1，不再使用
此前受控值 0。旧阶段的状态哈希不可当作新资源接线后的状态哈希；最新 JSON
已记录此次源文件与结果。

`anm-quad.mjs` 实现 `2af1..2e05` 的文字裁剪几何：VM 的 `10c/110/114/118`
为贴图内像素坐标及文字边界，UV 使用这些绝对坐标。七种锚点、正负缩放、
三种视口高度及裁剪矩形共 1,008 组 float32 顶点字节对照通过，并修正
`0x500` 锚点的顶部对齐。原有普通几何 2,412 例继续通过。旋转裁剪仍明确
报未验证；此消息路径的文字无需该分支。
[裁剪几何](th06nc-anm-crop-native-verified.json)、
[普通几何回归](th06nc-anm-quad-native-verified.json)。

`font-publish.mjs` 对应完整 `7530`：从字号字节和四组颜色选择字库，重绘
目的贴图的 36 像素高区域、写入字形排版边界并设置 VM 可见位。字库缺失时
按原版保留旧边界。270 例完整 VM／发布参数对照通过，包含 210 次实际发布
与 60 次缺失字库分支；底层字体/GPU 作为已注明的服务边界。
[文字发布](th06nc-font-publish-native-verified.json)。

`message-draw.mjs` 对应 HUD `3d023..3d0ad`：先两个肖像、消息框、两行台词，
再两行附加文字；第六关结束消息 1／11 不绘制这一组。120 例／560 次真实
ANM 绘制调用和状态保持比较通过。
[消息绘制](th06nc-message-draw-native-verified.json)。

`FontTextureGl` 使用原版 DDS 字形和已验证落点，在 Canvas2D 中 source-over
合成可写文字贴图，再上传受影响的行。此合成后端尚未与原版 GPU 像素比较，
不能据此声称采样、透明混合或最终画面一致。原版 `text.anm`、真实文字裁剪
及其 VM 仍负责屏幕位置、渐显和缩放，没有用网页默认字体替代字形。

浏览器 [message-lab](../../runtimes/th06nc/message-lab.html) 已运行第 1～6 关、
两角色的中文开场：12 场景的逐帧按钮、真实 Z 按键推进与 Ctrl 跳过通过；
台词贴图有非透明字形像素，对话最终结束、消息绘制归零，音乐请求路径正确，
没有 WebGL 或运行时错误。已检查实际灵梦与魔理沙截图。此页不播放音频，
也不是完整游戏；消息后的过渡指令、完整 HUD、场景背景和其他系统继续推进。
[消息浏览器检查](th06nc-message-browser-observed.json)。


## 后段消息与第一关结束请求（2026-11-14）

`message-progress.mjs` 实现消息 9 的关卡成就／加载动画请求、11 的下一场景
状态、14 的 Extra 隐藏分支。消息 7 的负值按原版停止并释放有效音乐句柄，
12 设置 240 帧淡出状态；没有句柄时保留原版未重置的播放／淡出字节。
成就、句柄停止／释放为明确的服务调用，未向外部账户发送请求。
StageWorld 在缺少相应宿主时收集本地音频／成就请求，供之后的宿主消费。
296 组原生分支对照通过，覆盖七关、五难度、两种录像标志、生命保护、
Extra 捕获数、死亡数及各种音乐状态。
[后段消息分支](th06nc-message-progress-native-verified.json)。

完整脚本对照扩展至七文件的全部 43 段唯一消息，使用代表 ID（全部 92 个
ID 与别名关系已在前述结构／打开对照覆盖）。自然等待、Ctrl 跳过、按键
推进、有效／无效音乐句柄，以及 Extra 两种捕获分支共 270 场景、448,898
帧、11,056 检查点通过。比较完整消息 owner、场景／音乐全局字段以及有序
文字、音乐、成就服务请求，执行至结束或场景请求；这不是实际宿主切换、
音频播放、外部成就持久化或 GPU 像素验收。
[全部消息脚本](th06nc-message-all-native-verified.json)。

第一关四种自机 Normal 联合对照进一步推进至 Boss 战结束、关尾对话、加载
动画与下一关请求：52,347 帧、3,570 检查点、39,282 次敌人状态比较通过，
包括自机受击／擦弹、弹幕、激光、道具、得分、符卡和消息状态。原有受控
满火力拾取／得分消弹保留；此演员夹具没有安排 Game Over 场景替换，因此
不能作为正常有限残机通关的证据，也没有验证实际第二关创建。
[第一关关尾联合对照](th06nc-stage-end-message-native-verified.json)。

## STD 背景结构、初始化与更新（2026-11-14）

`std.mjs` 读取原版 `785c0` 使用的结构：`0x490` 开始的对象偏移表、28 字节
对象头、带负类型终止符的 28 字节面、16 字节实例及固定 20 字节相机指令。
七关实际资源包含 39 个对象、765 个面、495 个实例及 300 条非终止指令。
每个面引用局部 ANM 脚本，背景 ANM 在 slot 4、基址 `0x320` 加载。

`initializeStd` 保留输入资源，创建可变 STD 副本、原版 `0x220` 背景 owner
和每面 288 字节 ANM；将对象置为活动并写入分配的 VM 索引。全部七关的
真实原生初始化对照通过：比较完整可变文件、全部 ANM、owner、对象指针表、
资源请求、分配大小和雾渲染请求。修正了 Node Buffer 非零 byteOffset 下的
副本视图，浏览器 Uint8Array 与 Node 输入均使用独立连续存储。
[STD 初始化](th06nc-std-init-native-verified.json)。

`advanceStd` 对应任务 `77bb0..78261`，实现六种相机指令、位置插值、方向
过渡、雾色／雾距过渡、等待信号、相机状态保存／恢复、暂停以及活动对象的
ANM 更新。七个实际 STD 各 16,000 帧，共 112,000 帧、1,834 检查点的完整
owner、ANM 池、可变 STD、方向全局量及有序雾服务请求与原版一致。等待
信号和暂停由夹具注入；没有把它误当成关卡事件接线的证据。
[STD 更新](th06nc-std-update-native-verified.json)。

背景实例裁剪、3D 投影和绘制尚未接入，符卡叠加背景路径明确报未连接；
STD 当前也尚未加入 StageWorld 的 priority 6 任务。完整宿主切换、Bomb、
音频交付、录像、存档及其余全模式验收仍需完成；上述报告均不代表整作完成。


## STD 实例绘制、真实相机与浏览器背景（2026-11-14）

`std-draw.mjs` 对应 `78cb0`。原版使用对象头的有符号层号，并按实例表顺序
遍历。包围盒裁剪实际只检查八个角点投影后的 Y 值；没有擅自增加 X／Z
裁剪。绘制每个面会改写共享 VM 的世界位置、指定尺寸缩放；模式 2 则再
投影为屏幕位置、深度及等比缩放，调用屏幕绘制器。调用之间的这些改写会
保留，因此不能把同一 VM 的所有实例一次性排队后再读取其最终位置。

`matrix.mjs` 保留 `566d0` 的逐步 float32 乘加和 `565b0` 的齐次除法阈值。
七关、多种实际动画帧、四层、正交／透视／实际相机、强制屏幕模式组合的
336 例、45,310 次有序 ANM 绘制调用及完整池字节与原版一致。比较原版
矩阵函数真实执行结果，不在夹具中用 JS 代替原版矩阵函数。
[STD 绘制调用](th06nc-std-draw-native-verified.json)。

`std-camera.mjs` 对应 `3bc10` 与 `56af0`，从逻辑视口尺寸及 STD 发布的方向
构造左手相机与透视矩阵；保留原版退化向量处理、float32 运算顺序、
100 近裁面及 10,000 基础远裁面。54 例完整 view／projection 字节和距离
字段对照通过，包含零方向、负方向、不同宽高比及深度偏移。三角库函数
由夹具向两侧供应同一算法；GPU 矩阵交付为观察边界。
[STD 相机](th06nc-std-camera-native-verified.json)。

七张真实背景 DDS 已按独立解包哈希提取，合计 3,933,196 字节。
`StdRendererGl` 使用已有世界 ANM 几何及相机矩阵进行透视、深度和纹理绘制；
`std-lab` 将四层绘制接到原版 STD／ANM／DDS，以逻辑 384×448、物理
864×1008 游戏区运行。此浏览器后端的雾插值、采样、透明／深度行为仍未
经过原版 GPU 像素验收，不能以 CPU 字节对照代替像素等价。

浏览器 [STD 背景页](../../runtimes/th06nc/std-lab.html) 已跑七关：选择、60 帧、
再 300 帧、外部等待信号均通过，实际 framebuffer 有非均匀像素，未出现
WebGL 或运行时错误。第三关与第六关截图已人工查看，呈现原始云层与
红魔馆图案。当前尚未显示符卡叠加，也尚未接完整战斗／宿主切换。
[七关背景浏览器检查](th06nc-std-browser-observed.json)。


## 符卡背景叠加与战斗接线（2026-11-14）

`std-pass.mjs` 复现背景的前后两个绘制任务 `78290`／`78390`，包括分层、
HUD 隐藏门控、深度／剔除状态、雾恢复及前景叠加。原版背景 viewport 的
深度范围为 0.5～1。符卡开始将背景 mode 置 1、frame 置 0、bind 标志置 1；
前景绘制首次绑定真实 `0x2d3` 叠加 ANM 并立即更新。更新在旧 frame=60 时
将 mode 增至 2，随后基础背景被隐藏。绘制前的黑色遮罩使用原版矩形
`[236,16,620,464]`；前景完成后雾范围恢复至 `[1000,2000]`。

七关效果资源、两个绘制任务、三种 mode、四种 frame、初始化标志、HUD
隐藏和雾刷新组合，共 1,344 例完整 owner 及有序渲染服务请求原生对照通过。
[背景绘制任务](th06nc-std-pass-native-verified.json)。另以反复开始／结束符卡、
暂停、更新和两次绘制组成连续循环，七关 3,500 帧／924 检查点的完整背景
owner（含叠加 ANM）、基础池、描述符、方向及雾请求对照通过。
[符卡背景连续循环](th06nc-std-spell-native-verified.json)。基础初始化、112,000
帧更新及 336 组实例绘制亦在本次源文件上重跑通过。

StageWorld 新增可选 `stdProgram`，在自机 priority 7 前运行背景 priority 6。
EnemyWorld 的符卡状态字段直接映射到背景 owner，开始／结束时不再维护
独立副本；宿主通过 `drawBackground(0/1)` 安排绘制任务。ECL 125 原版
`284cf` 写入背景等待信号，现已连到同一份背景数据；四种旧值的完整背景／
敌人字节对照通过。[ECL 背景信号](th06nc-ecl-background-native-verified.json)。

四种自机第一关联合对照已包含真实 STD 更新、符卡叠加更新和绘制任务，
推进至关尾下一关请求：52,347 帧、3,570 检查点、39,282 次敌人状态比较通过。
背景基础层几何调用、GPU、本地化／文字、音频、成就服务仍为注明的观察
边界，Game Over 场景替换和 Bomb 未参与该受控夹具。
[带背景的第一关联合对照](th06nc-stage-background-native-verified.json)。

浏览器背景页新增符卡开始／结束控件，使用原版效果 DDS；最新七关检查
覆盖 frame=61 后基础层隐藏、叠加显示、结束后背景恢复，均无 WebGL／
运行时错误。叠加使用游戏区偏移与裁剪，已查看更新后的截图。该诊断页
逻辑横坐标游戏区为 236～620，物理游戏区为 864×1008；完整 HUD 尚待接入。
原始背景及效果纹理共 12 张、5,430,768 字节，均核验独立 DDS 哈希。

继续试跑第三关至第 3,475 帧，遇到尚未实现的 `14002a410` 特效回调；记录
位于 `artifacts/th06nc/stage3-background-probe.txt`。这是下一个实现缺口，不能
将第一关或七个独立背景通过扩大为所有关卡已经完成。完整场景创建、音频、
Bomb、录像与存档等整作要求仍在推进。


## 后续关卡试跑、完整特效表与新增 ECL 路径（2026-11-14）

补齐特效 20 的 `2a410` 漂移回调，以及特效 17／18 的 `2ae30`／`2af80`
径向回调。前者保留 `/60` 初速度与原版减速系数；后两者随机方向、保存
生成中心，并使用不钳制的 60／240 帧半径变化。存活结束由真实 ANM 管理，
没有擅自提前回收。当前 21 项特效表的所有回调均已实现；810 组独立回调和
21 场景、2,520 帧完整特效管理器对照通过。三角库函数仍由夹具向两侧
供应相同结果，绘制／最终 GPU 像素不在此证明内。
[完整特效回调](th06nc-effect-update-native-verified.json)。

ECL 18／19 原版对目标的原始 32 位字自增／自减；即使目标是浮点变量，也
不是浮点数加减 1。实现包括局部、难度、自机坐标、临时计算值和随机操作数；
未识别目标按原版修改该条指令自身的参数字。744 组完整敌人／指令参数／
全局量／scratch／RNG 对照通过；StageWorld 对自机坐标的写入同步到实际
自机状态。[原始位自增／自减](th06nc-ecl-increment-native-verified.json)。

ECL 95 接入真实敌人池子敌生成，按原版解析位置操作数、生命／掉落／分数
及父脚本上下文。96 遍历全部 256 敌人，清除符合条件的生命值，并按碰撞
标志决定是否立即进入死亡子程序；Boss 和非活动槽保持不动。24 组子敌
请求及四组整池、1,024 敌人状态对照通过。
[ECL 敌人服务](th06nc-ecl-enemy-services-native-verified.json)。
第四关 1,000 帧的实战联合对照实际执行原版子敌分配和首次 ECL 更新：20 次
生成中有六次来自 95，81 检查点、392 个敌人状态比较通过。这一项没有将
子敌分配替换成请求桩，仍以注明的服务边界观察文字／音频／GPU。
[第四关生成实战前段](th06nc-stage4-spawn-native-verified.json)。

ECL 83 接入已实现的 EF00 带道具消弹，36 组压力／游标／弹幕与激光变体
比较全部弹幕、激光、1,025 道具槽、游标和 RNG 通过。
[ECL 消弹](th06nc-ecl-projectile-clear-native-verified.json)。
122 现按原版 20 项专用回调表设置／清除敌人回调地址；这只证明注册，
不代表专用回调函数体已完成。通用单指令回归扩展至 4,172 例，包含全部
20 个回调注册项及真实脚本参数。
[通用 ECL 回归](th06nc-ecl-command-native-verified.json)。

修正此前将 ECL 102 颜色表误截为 16 项的问题：原版颜色区实际有 28 项，
第四关使用的 16／22／25 均有有效颜色。扩展后 278 组挂接、跟随、角度／
强度更新及释放对照通过。
[挂接特效颜色与管理](th06nc-enemy-linked-effects-native-verified.json)。

`tools/th06nc-stage-coverage-probe.mjs` 探索性运行七关 Normal 灵梦 A，保留
既有受控满火力拾取和得分消弹，并跳过 Game Over 场景替换。最新结果及
源文件哈希保存在 `artifacts/th06nc/stage-coverage-probe.json`：第三关此路径
已运行 22,597 帧并提出下一关请求；其余主要缺口集中在 121 专用即时回调
和注册后的逐帧专用回调。此探索没有原生逐帧比对，亦不代表有限残机通关、
所有分支、全难度或真实下一场景创建；仍需继续实现并验证。


## 第二关专用弹幕回调与关尾联合对照（2026-11-14）

`ecl-custom-projectiles.mjs` 实现专用表 0／1（`32970`／`32b60`），通过 ECL
121 调用。0 为符合条件的整池弹幕重新绑定颜色精灵，按 mode 停速或设置
220 帧加速度及随机方向；跳过非活动和消除状态，保留其他状态。1 在原版
矩形范围随机选取发射点，再使用普通发射服务。24 组 mode／种子变体比较
完整 640 槽弹幕池、敌人、特效／发射请求和 RNG 通过，精灵绑定函数实际
执行；底层特效／发射实体创建在这一单元对照中为服务边界。
[第二关专用回调](th06nc-ecl-custom-stage2-native-verified.json)。

第二关 Normal 灵梦 A 实战另运行至关尾下一关请求：18,088 帧、1,205 检查点、
12,847 次敌人状态比较通过，包含原版专用回调、真实弹幕分配、碰撞、完整
道具／特效／背景池和消息。受控夹具仍不安排 Game Over 场景替换或 Bomb；
音频／文字／成就／GPU 为注明的观察边界，不代表有限残机或完整模式验收。
[第二关关尾联合对照](th06nc-stage2-custom-native-verified.json)。

第四关专用表 12（`351b0`）已接回 ECL，遍历前八个有效保存激光发射普通
弹幕；保留原版顺序运算，其 Y 结果使用已经计算的 X，并非标准旋转公式。
48 例完整敌人及有序发射请求对照通过。
[保存激光发射回调](th06nc-ecl-custom-lasers-native-verified.json)。表 3 的
四种自机局部变量配置也已实现，16 例完整敌人字节对照通过。
[第四关自机配置](th06nc-ecl-custom-profile-native-verified.json)。

第四关受控试跑现运行至 25,721 帧的关尾请求；其长程原生联合对照在
第 10,256 帧发现道具池分歧，正在定位。不能将独立回调通过或试跑成功
当作第四关联合验收通过。专用表其余条目、全部分支／模式，以及完整宿主
切换、音频、录像和存档等要求继续推进。


## ECL 119 满火力道具分配纠正（2026-11-14）

第四关第 10,256 帧的差异已定位到 ECL 119 的满火力内联分配：原版
`2807f..28083` 写入道具 type=1、mode=0，绑定脚本 `0x216`，即普通蓝点；
此前 StageWorld 将该请求误接成 type=6、mode=1 的自动回收消弹星点。
现已改为普通蓝点分配。消弹／得分清除仍使用各自原版星点路径。

新增完整 119 分配对照，直接运行原版内联分配和实际 StageWorld 服务，
不再只观察请求边界。360 组火力／符卡练习／数量／位置／池压力／游标
组合比较全部 1,025 道具槽、游标和 RNG 通过；夹具还恢复了原版分发表
提供的 376 右边界寄存器。[ECL 119 完整分配](th06nc-ecl-item-scatter-native-verified.json)。
此前仅观察高火力请求的服务对照，不能当作该内联分配已经验证的证据。
第四关长程联合对照正在基于本次修正重跑，仍须以其实际结果为准。


## 第四关关尾联合对照重跑结果（2026-11-14）

ECL 119 修正后的第四关 Normal 灵梦 A 长程对照已通过：25,721 帧、1,682
检查点、36,239 次敌人状态比较，运行至关尾下一关请求。原生实际执行
399 次敌人生成（44 次由 ECL 95 触发）、专用回调 3／12、30 次普通消弹和
一次受控得分消弹，比较完整自机／敌人／弹幕／激光／道具／特效／背景／
消息等状态。第 10,256 帧原有分歧已在整条测试路径上消除。
[第四关关尾联合对照](th06nc-stage4-custom-native-verified.json)。

此结果仍是一个 Normal 自机路径的受控原生对照，保留此前明确的 Game Over
场景替换／Bomb 排除项和 GPU／文字／音频／成就服务边界，不能扩大为所有
角色、所有难度或完整游戏已经完成。下一项是第五关专用回调 4／5；已确认
其中的全局 `4f27b9` 同时门控自机、道具／弹幕／激光任务、敌人计时、背景
和 HUD 消息更新，需要连同相应时序一起实现。


## 第五关时间停止与专用回调 4／5（2026-11-14）

`ecl-custom-time-stop.mjs` 实现表 4（`333e0`）及表 5（`33a30`）。
4 的 mode<2 生成特效并写入共享时间停止字节，保留负数模式的低八位；
其余模式遍历有效大弹，按原版顺序筛选、消耗 RNG、重绑颜色并计算速度。
低难度最多选择 14 发、高难度 52 发；距离与大小阈值分别为 128 和 30。
120 例四难度／模式／种子／大弹密度对照比较全部 640 槽、敌人、请求及 RNG 通过。
[时间停止指令](th06nc-ecl-custom-time-stop-native-verified.json)。

5 每九个 ECL 时钟生成九组旋转发射点，保留 float32 分步计算、近零向量、
奇偶组和难度分支，以及音效 7 的排队／去重规则。3,456 例完整敌人、发射
描述符已初始化的 0x50 字节及音效队列对照通过，覆盖固定三角服务返回值和
实际宿主三角库返回值。描述符后部为未初始化原生栈，既不作为发射输入，也
不虚构其确定内容。实体分配在此单元测试中为观察边界。
[时间停止扇形回调](th06nc-ecl-time-stop-fan-native-verified.json)。

StageWorld 按实际任务优先级读取同一标志：背景／自机在敌人任务之前检查，
道具／弹幕／激光／消息在之后检查；因此停止或恢复当帧并非所有任务同时
切换。敌人本体计时器暂停，ECL 时钟、时间线、特效和分数弹字继续运行。
原生完整 owner 哨兵对照另验证标志 1／255 的八例门控行为，仅背景额外写入
`1bc=60803030`。[原生任务门控](th06nc-time-stop-gates-native-verified.json)。

受控 Normal 灵梦 A 探索已运行第五关 24,908 帧至下一关请求，整关联合
原生对照正在执行，尚不能将该探索当作通过。第六关当前首先缺少表 6 的
逐帧回调，Extra 首先缺少表 13 的即时回调。完整宿主场景、Bomb、音频、
录像和存档等既定范围仍未完成。


## 第五关关尾联合对照结果（2026-11-14）

第五关 Normal 灵梦 A 联合对照已通过：24,908 帧、1,631 检查点、17,772
次敌人状态比较，运行至下一关请求。原生实际运行 180 次敌人分配（48 次
ECL 95 子生成）、25 次普通消弹、一次受控得分消弹，以及专用 4／5 回调和
真实普通弹幕分配。比较自机、全部敌人／弹幕／激光／道具／特效／背景池、
消息、停止标志和 RNG；实际执行原版 `3cc50` 消息任务门控，HUD 内容更新
本身仍为服务边界。[第五关关尾联合对照](th06nc-stage5-time-stop-native-verified.json)。

GPU／文字／音频／成就仍是服务边界；此受控夹具跳过 Game Over 场景替换
和 Bomb，不代表有限残机通关、全难度／全角色或完整游戏验收。后续继续
补齐第六关及 Extra 专用回调，并完成既定整作范围。


## 第六关配对粒子专用回调 6（2026-11-14）

`ecl-custom-particles.mjs` 实现专用表 6（`33e60`）：保留逐帧旋转、
2／4／8 帧分段生成频率、相同时钟跳过、随机环带位置、两侧粒子的
float32 速度及加速度。退场标志分支释放敌人已挂载特效，保持其他字段。
每个 EnemyPool 槽位现在将默认逐帧回调绑定到自己的 services，确保其
linkedEffects／laserBindings 等句柄属于实际敌人，包括生成时的首次执行。

1,152 例原生回调对照通过，实际运行原版特效分配与 ANM 绑定；比较完整
敌人、全部 513 个特效槽、游标、请求及 RNG。覆盖计数边界／重复计数、
旋转、负值、挂载特效释放和 0／511／512 槽占用的正常／耗尽分配。
[配对粒子原生对照](th06nc-ecl-particles-native-verified.json)。

受控第六关探索从原先第 4,566 帧推进至第 7,488 帧，下一缺口为即时表 7。
本次前 7,487 帧联合原生对照正在执行；第六关消息切换 `eff05`→`eff06`
需要动态加载服务，夹具已补充实际原版 ANM 绑定与有序加载请求检查。
探索及单元对照均不等于整关或整作完成。


## 第六关专用回调 6 联合前缀对照结果（2026-11-14）

第六关 Normal 灵梦 A 前 7,487 帧联合原生对照已通过，含 543 检查点、
6,759 次敌人状态比较、126 次敌人生成、5 次普通消弹及一次受控得分消弹。
全部自机／敌人／弹幕／激光／道具／特效／背景／消息状态和 RNG 比较通过，
实际执行回调 6、特效分配及动态 `eff06` 原版 ANM 绑定。对话资源加载请求
也参与比较，原版 `data/` 路径前缀在服务记录中按文件名归一化。
[第六关前缀对照](th06nc-stage6-particles-prefix-native-verified.json)。

范围止于第 7,488 帧首次调用尚未实现的即时表 7 之前，不能描述为第六关
整关通过。资源解码、HUD 内容更新及此前列出的 GPU／文字／音频／成就
仍为服务边界；Game Over 替换／Bomb 继续不在此受控夹具验收范围。


## 第六关专用回调 7／8／9／10／11（2026-11-14）

新增 `ecl-custom-rings.mjs`，实现表 7（`34350`）两组八边形、每组三层
的发射点。激光／普通子弹分支分别使用普通构造服务；保留原版角度累加，
不以标准化角度替代多次 float32 运算。96 例完整敌人、48 次有序发射请求
及 RNG 对照通过，覆盖四难度、零／非零模式、种子和位置；此专项测试的
实体分配仍为观察边界。[环形发射](th06nc-ecl-rings-native-verified.json)。

表 8（`34950`）在逐槽访问时筛选活动大弹，从其位置发射零速小弹，最后
写入局部计数。实际分配可改变后续槽位，因此不能预先复制符合条件的列表。
48 例直接运行原版普通弹幕构造，比较完整 640 槽、敌人、游标、请求及 RNG，
涵盖混合／全大弹、0／100／639／640 槽初始占用和跨池尾游标，均通过。
[大弹派生分配](th06nc-ecl-large-bullets-native-verified.json)。

新增 `ecl-custom-acceleration.mjs`，实现表 9／11（`34b50`／`34df0`）对
静止小弹重绑颜色、设置 120 帧加速度。9 按距离叠加共享随机角，11 在固定
随机数预消耗后逐弹随机方向；保留速度向量和显示角字段。12 组整池混合
状态对照通过，逐槽覆盖零／负零／非零速度、距离阈值和大小筛选，比较
完整敌人、全部弹幕、特效请求与 RNG；实际特效创建是单元服务边界。
[静止小弹加速](th06nc-ecl-acceleration-native-verified.json)。

新增 `ecl-custom-boss.mjs`，实现表 10（`35050`）组合表 6 配对粒子，并
根据自机 Bomb 标志切换 Boss ANM、碰撞标志和 60 帧恢复时钟。720 例原生
实际 ANM／特效分配对照通过，覆盖存活状态、Bomb 开关、自动动画标志、
恢复时钟边界和耗尽特效池；比较完整敌人／特效池、游标、请求、RNG。
此结果验证的是 Boss 对 Bomb 标志的响应，自机 Bomb 回调本身仍待实现。
[Bomb 响应 Boss](th06nc-ecl-bomb-boss-native-verified.json)。

受控第六关 Normal 灵梦 A 探索现运行 34,746 帧到结尾场景请求 10，长程
联合原生对照正在执行。夹具改用分行 JSON 输出完整检查点，避免大场景下
单个 JSON 字符串的引擎长度限制，并对每次原生任务执行检查真实返回地址。
探索成功不能替代整关联合对照、宿主场景创建或完整游戏验收。


## 第六关关尾联合对照结果（2026-11-14）

第六关 Normal 灵梦 A 长程联合原生对照已通过：34,746 帧、2,247 检查点、
73,464 次敌人状态比较，运行至结尾场景请求 10。实际执行 606 次敌人生成
（480 次 ECL 95 子生成）、48 次普通消弹、一次受控得分消弹及专用回调
6..11；完整自机／敌人／弹幕／激光／道具／特效／背景／消息、RNG 和加载
请求均参与比较。[第六关关尾联合对照](th06nc-stage6-custom-native-verified.json)。

此结果仍是一个 Normal 自机的受控路径，保留 Game Over 替换／自机 Bomb
排除项，以及注明的资源解码、GPU、文字、音频、成就和 HUD 服务边界。
结尾场景请求不等于实际结尾宿主已创建。整作和全模式验收仍未完成。

## Extra 专用回调 13／14／15 接入（2026-11-14）

新增 `ecl-custom-extra.mjs` 并接入即时／逐帧分发表：13 每六次调用按固定
中心 (192,224) 的圆周位置发射，局部角度保留，计数无论是否发射都递增；
14 遍历前八个活动保存激光，按 48 间隔沿有效区间发射，活动但空区间也
计入局部计数。分别 378／240 例完整敌人和有序发射请求对照通过，实体
分配仍为单元服务边界。
[Extra 轨道发射](th06nc-ecl-extra-orbit-native-verified.json)、
[Extra 激光沿线发射](th06nc-ecl-extra-lasers-native-verified.json)。

15 逐个大弹激活距离小于 64 的静止小弹，以原版非标准角度插值设置
加速度、速度、颜色及重绑精灵，然后组合 Boss 回调 10。18 例全池／完整
敌人／RNG 原生对照通过，包含单个／多个大弹、距离 64 边界、动态筛选和
存活／死亡分支；后续特效创建为服务边界，完整 Extra 长程仍未验收。
[Extra 邻近激活](th06nc-ecl-extra-proximity-native-verified.json)。

探索工具已将第七关难度从此前统一 Normal 修正为实际 Extra 参数 4，并
记录每条结果的难度。旧的 Normal 第七关探索只保留其原有注明范围，不
扩大成 Extra 模式的验收证据。下一轮依实际 Extra 结果继续定位专用分支。


Extra 实际难度 4 的受控探索在本次接入后运行至第 18,168 帧，下一项
明确缺口为 ECL 25（脚本偏移 16960）。该结果包含已接回运行路径的
13／14／15，但尚无完整 Extra 长程原生比较，不能扩大其验收范围。
后续先按原版指令体确认 25 的真实行为，再继续其他专用回调和整作需求。


## ECL 25／26 的真实指令体与操作数别名（2026-11-14）

ECL 25 的原版入口 `237e1` 调用 `325f0`，将四个浮点源依次解析为引用，
在全部解析完成后计算 `atan2(y2-y1,x2-x1)` 写入允许的浮点目标。它不是
浮点自增。computed 目标只计算其对应临时值；无效／整数目标不解析源。
共享 RNG／临时槽的引用别名必须保留，不能将每个源在解析时立即复制值。

26 读取 raw-ID 目标当前浮点位型，以 float32 累加 ±2π 并保留原版迭代
上限，再走普通赋值助手。computed／随机目标的赋值副作用也参与运算。
新增 1,767 例完整敌人、指令、全局量、临时槽、RNG 及 atan2 输入对照，
覆盖所有目标、引用别名、正负零、无穷、NaN、极端角度，均通过。
[角度指令对照](th06nc-ecl-angle-native-verified.json)。常规指令集合当前
4,190 例对照也通过。[常规 ECL 指令](th06nc-ecl-command-native-verified.json)。

## Extra 专用回调 16～19（2026-11-14）

16 根据带符号 owner 时钟在 7200 帧关闭生命值缩放，mode=0 写入比例与
整数局部值，其余 mode 生成生命值相关矩形范围的随机坐标。18 写入最终
阶段浮点参数和三个整数局部值；整数乘法保留 32 位溢出后再带符号除法。
二者分别 480 例完整敌人及 RNG 原版对照通过。
[生命值参数](th06nc-ecl-extra-health-native-verified.json)、
[最终阶段参数](th06nc-ecl-extra-final-native-verified.json)。

17 是原版跳转至 10 的别名；19 的 Bomb 响应与 10 相同，恢复时改用脚本
`1b0` 和自动动画索引 `b0`。17／19 各 720 例实际 ANM／特效分配对照通过，
包含 Bomb、存活、动画状态、计数与耗尽特效池；10 的默认恢复路径也已
回归通过。自机 Bomb 功能本身仍不在这些专用回调测试的验收范围。
[Extra Boss 别名](th06nc-ecl-extra-boss-native-verified.json)、
[最终 Boss 恢复](th06nc-ecl-extra-final-boss-native-verified.json)。

当前 Extra 难度 4 的受控探索运行 73,379 帧至场景请求 7，所有活动敌人
均已退出；Game Over 替换仍跳过。该观察不能代替原生长程或宿主切换。
前 20,000 帧联合原生对照正在执行，包括 ECL 25 和专用 13～15，夹具
分离 ANM、ECL、消息、STD、动态资源地址，避免资源数增加后的区域重叠。
专用表仅条目 2 仍待实现，其余整作／全模式需求继续保留。


Extra 联合夹具在第 6,240 帧首次报告场景状态差异。写入观察进一步定位到
第 6,234 帧原版 `bcc4`：分数弹字任务 `90d0` 依据 Game Over 标志调用
`b4f0` 结束菜单，其 Extra 分支提出场景 7 请求。JavaScript 受控夹具仅
暂停弹字，不执行该菜单；二者此前声明的 Game Over UI 边界实际上不一致。

现已在原生 `b4f0` 的精确调用边界停止该菜单，保留 Game Over 标志、
弹字暂停和所有已纳入比较的战斗状态，并统计被观察的菜单调用。该修改
仅修正联合测试的既定排除边界；实际结束菜单／宿主流程仍属于未完成项，
不能据此宣称 Game Over 功能已实现。前 20,000 帧联合对照正按此边界重跑。


## Extra 前 20,000 帧联合对照通过（2026-11-14）

统一 Game Over UI 边界后的 Extra 灵梦 A 联合原生对照已通过 20,000 帧、
1,325 检查点和 20,244 次敌人状态比较，含实际 ECL 25 执行、381 次敌人
生成（41 次子生成）、28 次普通消弹及一次受控得分消弹。全部已纳入范围
的实体池、自机、背景、消息、RNG 和动态资源请求比较一致。
[Extra 前缀联合对照](th06nc-extra-prefix-native-verified.json)。

原版 Game Over 菜单在精确边界被观察并跳过 13,767 次，保留其标志和
弹字暂停；实际菜单／场景替换仍未实现。前缀结果不证明 20,000 帧以后的
流程或每一专用条目都在此路径被调用；条目级证据使用各自专项对照。
最新独立 Extra 探索仍在 73,379 帧提出关尾请求，但后半段尚无原生联合
验收。下一步补专用表条目 2，并继续长程、模式及真正浏览器宿主的工作。


## 专用回调表条目 2 与共享五边形路径（2026-11-14）

新增 `ecl-custom-stage3.mjs` 并接回即时及逐帧分发表。条目 2（`32cf0`）
保留全局敌人／自机位置快照和六个角度，不按敌人复制。每 30 tick 更新
角度序列，每 6 tick 沿五段插值发射，按原版顺序临时改变／恢复速度并
逐发扣减角参数；达到局部上限后清除注册回调。2,112 例完整敌人、共享
位置／角度、发射请求、音效队列及 RNG 对照通过。
[条目 2 专项](th06nc-ecl-stage3-pattern-native-verified.json)。

另有 18 个持续场景、2,736 次调用的联合原生对照，使用两个交错启动、
位置移动的敌人，实际执行普通子弹分配；逐次比较全部 640 槽及游标，
涵盖发射模式 0／3／8 和 0／639／640 槽占用。第二个敌人重新初始化的
共享状态确实影响第一个敌人的后续调用。
[共享状态与实际分配](th06nc-stage3-pattern-pools-native-verified.json)。

核查原版全部 ECL 的 122 注册项，仅出现 2／5／6／10／15／17／19 和 -1，
均已接入对应逐帧处理。20 项专用表现在均有实现，但这不证明全部实战路径
或整作完成。音效队列的核对另发现条目 5 的空槽优先顺序差异，已修正为
原版逐槽检查；扩展后的 4,608 例扇形回调对照通过。

## Extra 关尾联合原生对照（2026-11-14）

Extra 灵梦 A 的受控联合对照已运行 73,379 帧到关尾场景请求 7，通过
4,663 检查点和 113,708 次敌人状态比较。原版实际执行 681 次敌人生成
（341 次子生成）、109 次普通消弹和 5 次得分消弹；此前前缀后的所有已
纳入比较状态也一致。[Extra 关尾对照](th06nc-extra-custom-native-verified.json)。

保留 Game Over UI 精确调用边界：67,146 次菜单调用被观察并跳过，其他
战斗及弹字暂停标志保留。Bomb、资源解码、实际音频、HUD／成就／文字 GPU
和宿主场景替换等原有排除边界继续适用。此单一受控自机路径不代表有限
残机通关、隐藏分支、全角色／全难度或完整浏览器验收。

## 浏览器普通流程入口接线（2026-11-14）

新增 `runtimes/th06nc/game.html`，复用标题原版状态模块，实际衔接到
StageWorld，并接入背景、自机／敌人、特效、道具、子弹／激光、分数弹字
和对话字体。原版 `2b310` 的特效位置发布与世界 VM 绘制请求也已补齐，
8 例完整 owner 对照通过，GPU 仍为边界。
[特效绘制请求](th06nc-effect-draw-native-verified.json)。

`th06nc-game-texture-prepare.mjs` 补齐关卡等 ANM 引用的 56 张原始 DDS，
共 213,804,204 字节；逐张对独立原生 DDS 哈希核验，不做格式／像素替换。
新浏览器检查实际走过标题、难度、自机、机体、模式、开始确认和淡出，
创建第一关并验证真实键盘移动／射击、暂停／恢复、早期敌人和弹幕。
WebGL 错误为 0，截图保存于 `artifacts/th06nc/game-browser/`。
[浏览器主流程检查](th06nc-game-browser-verified.json)。

当前入口是开发版：直接进入主标题 owner，未含原版 boot/splash；只接通
普通 mode 0，其他菜单和模式仍提示待接入。HUD、暂停／Game Over 和结尾
界面使用临时宿主显示，原版对应 owner、Bomb、音频输出、录像及持久化
尚未完成。背景／角色投影和字体 GPU 亦尚未做原版像素等价验收；新入口
不能被标记为整作完成。普通后续关卡的宿主重建已接线，仍需实际验收。


## 浏览器音效、Opus 封装与 BGM 运输（2026-11-14）

`shared/th06nc/sound-queue.mjs` 从原版 `3de430` 及 `3091a0` 表恢复
34 个独立音效句柄、28 个 WAV 来源和逐编号衰减。`76a30` 消费三个队列槽，
遇到首个负值立即停止；音量配置为 0 时完全保留队列。非负槽即使句柄为 -1
也会清空。每次播放先写 DxLib 音量 `7300 + config*300 + attenuation`，
再以 mode=1/restart=1 播放。`76af0` 入队在遇到首个负值或相同 ID 时停止。
`th06nc-sound-queue-native-verified.json` 覆盖 1,020 组消费，
`th06nc-audio-control-native-verified.json` 另覆盖 408 组入队。

`music-update.mjs` 实现全局 `79c84..79d26` 淡出更新，1,680 组原版对照。
沿用先前消息证明的属性映射：fadeStart 对应 509660，是递减倒计时；
fadeFrame 对应 509664，是固定除数。倒计时到零时按原版顺序 stop/release，
清除 fading/playing、handle=-1、pendingValue=0，保留 requestActive。
静音时调用 mute；否则音量为 `2300 + config*300 + trunc(imul(countdown,5000)/divisor)`。
`music-loop.mjs` 对 8 字节 .pos 中两个有符号 44.1 kHz 样本位置进行
`trunc(value*480/441)` 换算，39 组正负及边界数据与 `7be52..7bea4` 对照通过。

`opus-container.mjs` 恢复 `7ea60` 初始化及 `7ec80` 包读取：
magic 80000001、声道 byte9、固定包跨度 i16@0a、采样率 48000@0c、
数据块偏移 i32@10、预跳过 i16@1c；数据块 magic 为 80000004，随后长度。
每个固定槽首四字节是 big-endian 有符号有效长度，接着四字节保留值，
有效长度不在 (0,stride-8] 时原版使用 stride-8。数据按固定 stride 前进。
`th06nc-opus-native-verified.json` 直接执行上述两个原版函数，覆盖 bgm/bgm2
各 18 首、共 36 首与 207,400 个包，逐包送入解码器的所有字节均一致。
该证明将文件回调、分配和 Opus 解码调用作为边界，不宣称 PCM 解码等价。

`tools/th06nc-game-music-prepare.mjs` 不重编码 Opus 包，仅补 Ogg 页、
校验和、OpusHead/OpusTags 和样本时间戳，输出 36 个 Ogg（105,570,632 字节）。
循环元数据来自 th06MD.dat，清单保留原文件、.pos、Ogg 的 SHA-256。
独立 FFmpeg 完整解码全部 36 首，逐帧累加采样数全部等于原版
`packetCount*960-preSkip`，见 `th06nc-music-decode-verified.json`。
bgm/th06_07 的原始请求循环终点比有效流长 627 个 48 kHz 样本；
浏览器运输层暂将终点限制到 buffer 时长，原版 DxLib 在该边界的实际循环
行为尚须核验，不能以本节推断全部循环行为等价。

浏览器入口 `game-audio.mjs` 已连接解码、用户按键解锁、逐编号独立音效句柄、
同编号重播、BGM 切换、循环及淡出。主流程从原版 `3b60a..3b61b` 所示的
关卡初始化位置请求 STD 第一首音乐，消息 opcode7 可请求后续音乐。
标题最终确认传入 musicActive 并交付原有 musicFade(30) 效果。
`tools/th06nc-game-audio-prepare.mjs` 从 th06IN.dat 原样导出 28 WAV，
共 1,776,716 字节，并保留 SHA-256 清单。

更新后的 `th06nc-game-browser-verified.json` 实际走标题选人至第一关 779 帧，
验证真实按键后音频上下文 running、28 WAV 解码、射击音效触发；
对 34 个 ID 分别用 OfflineAudioContext 生成非零 PCM，逐样本等于解码
输入乘运输层增益（本次最大误差 0）；0/1 两个 ID 共用 WAV 但保持两个
声音，重复 ID0 只替换自身，混合输出对照通过。还验证标题 th06_01、
30 帧淡出中间值、关卡 th06_02 切曲，以及 th06_02 的循环接缝 3,072 个样本
与 loopStart 对应解码输入一致（最大误差 0）。

这些结果证明音频资源和浏览器运输已经工作，仍不代表原版嵌入 Opus 解码器、
DxLib/设备混音器、重采样器、全部音乐请求 owner/缓存分支或所有配置等价。
音乐请求 owner、其他模式及 bgm2 配置选择仍需接入及对照。Bomb、原版 HUD、
原版暂停/GameOver/结尾、录像/成绩/存档等也继续保持未完成。


## Bomb 公共入口、魔理沙 B 与屏幕震动（2026-11-14）

`player-bomb.mjs` 实现原版自机 owner `689a8..68acb` 的公共入口。
已激活时先调用所选更新回调；新启动要求无对话、deathBombFrames 非零、
有符号 Bomb 数量大于零、X 输入上升沿且更新指针非零。启动扣 Bomb、
递增 4f1e64 对应的 bombCount，更新 inputFlags，设置 9ec8=1、
7ac0=-999、7ac4=0、9f20=999 后立即调用回调。回调后清除 spellActive，
并将 badf64 对应 spellBombFlag 写为 spellCounter!=0。非 replayPlayback
且原状态为 2 时发出 Achievement20/commit。平台成就交付仍是服务边界。
`th06nc-bomb-entry-native-verified.json` 覆盖 2,400 组完整 owner/全局写入，
包括普通/死亡状态、回放开关、空回调、对话、死亡窗口、负 Bomb 数量及输入边沿。
自机更新不再统一拒绝 Bomb，而是分派到已实现的回调；其他回调仍明确报未实现。

`player-bomb-marisa-b.mjs` 实现 `e7f0..ebd9` 更新和 `ebe0..edd1`
绘制发布。首帧把前 1024 个活动道具设为 mode1，保留第 1025 哨兵；
设置持续 300 帧、受击无敌计时 360、普通/低速倍率 0.3，初始化
四个 ANM 428..42b、复制四组起点，按原版顺序排入音效 19。后续四帧中
三帧发布宽 384、高为当前自机 y 的伤害/消弹矩形，伤害 12；
时钟 60 请求 (60,1,7) 震动，120 请求 (200,24,0)。
到时清除活动标志并将两个速度倍率恢复为 1。四个真实 ANM 每帧推进，
绘制用缓存逻辑高度和缩放计算原点及归一化旋转，依次交付 67f0。

新增 `anm-initialize.mjs` 对应便利初始化器 2760，除 selective setter
之外还清除位置 c8/d0 与偏移 18/20，设置 108=f0f。
其与 1da0 的区别对 Bomb 的完整 owner 字节很重要。
`th06nc-bomb-marisa-b-native-verified.json` 覆盖 16 场景、每场 302 帧，
共 4,832 帧、208 检查点；完整自机、1025 道具槽、四个绘制 VM、声音、
震动请求与 RNG 均对上。三角函数服务分别使用固定值及独立 Python scalar
sin/cos 对浏览器 Math，字体/HUD、震动任务执行和 GPU 作为该测试的服务边界。

`player-bomb-cancel.mjs` 实现 `6a8c0` 的 16 个消弹矩形查询，
只在宽为零时跳过，保留有符号宽高及浮点 unordered 行为，边缘相碰也命中。
`th06nc-bomb-cancel-native-verified.json` 的 840 组覆盖各槽位置、
零/负/非有限宽高、边缘及非有限输入，原版返回值与完整只读区域一致。

`screen-shake.mjs` 恢复优先级 14 的 `76310` 更新和 `76530` 初始计时。
760f0 的后三参数是 duration、startAmplitude、endAmplitude，
不是效果枚举。每帧在两端幅度间按 float32 插值，各取一次 next32()%3
决定 x/y，直接写原版逻辑 playfield [236,16,384,448] 的平移/缩减值，
共消耗四个 next16；timeStop 时保留 owner/RNG 并恢复默认矩形，过期时
递增计时后恢复矩形并退出。`th06nc-screen-shake-native-verified.json`
覆盖 504 场景、4,032 次更新，包括冻结、过期、有符号插值和溢出边界。
该证明不涵盖 task-list 分配/删除和最终 GPU viewport 像素。

StageWorld 已把 Bomb 接入自机优先级 7、真实 item pool、bullet-area
query 和优先级 14 的震动池。grazeCountersDisabled 现在绑定自机
9ec8（原版全局 509268 的同一地址），使 Bomb 期间擦弹计数/点道具估值
读取同一个状态。标题/主流程仍保留临时 HTML HUD；Bomb 名称用原版
本地化键显示，原版 3d370 名称 HUD owner 仍待完整移植。

`tools/th06nc-stage-bomb-marisa-b-native-check.py` 实际执行第一关 2,000 帧，
第 700/1400 帧各用一次 Bomb，在每次之前插入一枚受控活弹，
确保覆盖真实 6a8c0 查询和子弹转点道具，未把查询替换为固定返回值。
真实自机、敌人、效果、640 弹池、64 激光池、1025 道具槽、515 分数文字槽、
伤害、声音、viewport 和 RNG 共 165 检查点及 1,135 份敌人状态全部对照通过，
见 `th06nc-stage-bomb-marisa-b-native-verified.json`。
该短程证明没有命中/擦弹场景，不宣称这些分支由本次新增测试覆盖；
caption、平台成就、task 分配和 EF00/F300 仍是明确边界，未执行 STD/MSG/音频/GPU。

浏览器检查增加 `--marisa-b-bomb`，真实走标题选择魔理沙 B，
移动/射击/暂停恢复后以真实 X 键启动，断言只扣一枚、Bomb 时钟 121 时
仍有光束和震动、结束后恢复默认 viewport，至第一关 1,110 帧通过。
`artifacts/th06nc/game-bomb-browser/bomb.png` 已目视检查，原始四束光束
和魔理沙可见，GL error=0；原版像素等价仍未证明。
见 `th06nc-game-bomb-browser-verified.json`。

灵梦 A/B、魔理沙 A Bomb 更新/绘制尚未实现；魔理沙 B 的原版名称 HUD
也未接通。Boot、其他菜单/模式、原版暂停/GameOver/结尾、录像/存档、
所有自机难度完整通关路径及音画等价性继续保持未完成，整作目标未达成。


## 四组 Bomb 回调接通与消弹边界修正（2026-11-14）

本节更新上节“其他三组 Bomb 尚未实现”的当前状态：有效的四组原版
更新/绘制指针现在全部有独立实现，并接入 StageWorld/浏览器。
`player-bomb.mjs` 继续对未知指针明确报错；原版名称 HUD 仍是未完成边界。

`player-bomb-marisa-a.mjs` 对应 e270/e650。首帧自动回收活动道具，
设置持续 250、受击计时 310，初始化 425..427 循环的八个 ANM，
八方向速度为 2，声音 6，震动 (120,4,1)。后续每帧推进位置和 ANM，
时钟不是 3 的倍数且与 previous 不同的帧发布 128 方形消弹/伤害区，
伤害 8。每个星弹依次画三层，缩放 3.2/2.2/1，并按原版顺序
用速度及 32/64 偏移形成拖影，最后的 VM 位置/缩放保留为原版末次绘制值。
`th06nc-bomb-marisa-a-native-verified.json` 覆盖 16 场景、
4,032 连续帧、208 检查点，完整 owner、item pool、绘制请求与副作用一致。

`player-bomb-reimu-b.mjs` 对应 db50/e130。持续 140、受击计时 200，
初始化 4a9..4ac 四个 ANM，保存交叉带状原点及 z=.42/.415/.41/.405，
声音 6、首帧震动 (60,2,6)，时钟 60 再请求 (80,20,0)。
首帧之后每帧填充交替的 62×448、384×62 消弹区尺寸；奇数帧且
clock!=previous 时，用刚推进的 VM 偏移加保存原点发布中心和伤害区，
伤害 8。绘制同样读取原点加 VM 偏移，四次交付 67f0，绘制 z 为 0。
`th06nc-bomb-reimu-b-native-verified.json` 为 16 次连续场景运行、
2,272 帧、208 检查点；其中两种三角函数服务配置对该回调行为相同，
不能把重复运行数当作额外的三角函数覆盖。

`player-bomb-reimu-a.mjs` 对应 d1a0/d9c0。持续 300、受击计时 360，
首帧清除八槽活动状态、自动收道具、生成 effect12，并发布自机附近
256 方形消弹区。原版在时钟 80/96/112/128/144/160/176 分别启动
槽 1..7；槽 0 在这一时序中跳过。每槽含四个 ANM（4a5..4a8），
随机初速 4，目标 x 严格大于 -100 才使用锁定目标，否则追踪当前自机。
转向/归一化保持原版 float32 顺序，速度限制为 1..10。追踪态发布
48 方形区域和伤害 8；累计伤害达到 100 或时钟达到 duration-30 时
切爆炸态，区域扩大到 256、伤害 200，生成 effect6×8/effect12×1、
声音 15 及 (16,8,0) 震动，四个 VM 的中断字段 8a 写 1；
爆炸态计数到 30 后停用。绘制按原版顺序发布保存位置加各 VM 偏移的
全部三轴坐标。
`th06nc-bomb-reimu-a-native-verified.json` 覆盖有效目标/阈值回退目标、
强制累计命中爆炸/自然到时爆炸、固定/独立 scalar 三角函数以及声音槽组合，
共 64 场景、19,328 帧、2,112 检查点，完整自机、1025 道具槽、
所有灵球 VM、RNG 和服务请求逐项通过。该单位证明观察效果生成请求，
不在其中执行实际效果池。

在四自机整池对照中发现并修正普通弹外围消弹查询的扩展宽度：
原版 1110c7/11133 从 30cecc 读取 20，而早期浏览器实现使用了
18.8888889。`bullet-update.mjs` 已改为原版 float32(20)。
更新 `th06nc-bullet-update-native-check.py` 后直接观察 6a8c0 的
left/top/right/bottom 参数，70 场景、8,400 帧、420 检查点通过。
原有该测试只控制查询返回值为 0，未核对参数；早期通过记录不能证明
Bomb 消弹边缘的正确性。本次新增实际矩形查询/转道具组合才覆盖此差异。

`tools/th06nc-stage-bomb-native-check.py` 现对四种自机各运行第一关
2,000 帧，均在 700/1400 帧启动 Bomb，并各在前一帧插入受控活弹，
保证消弹和转点道具路径实际执行。原版自机/敌人/效果/弹/激光/道具/
分数文字池、伤害累计、viewport、声音和 RNG 全部对照通过：
共 8,000 帧、660 检查点、4,399 份敌人状态，状态摘要
cb77c16eec5288990190ff720614f70252c2d3f69d0d49217640ca65c8b550bc。
其 caption/平台成就、震动 task-list 分配和 EF00/F300 为服务边界，
没有执行完整 MSG/STD/音频/绘制，也不证明完整关卡或全部难度通关。
见 `th06nc-stage-bomb-native-verified.json`。

浏览器检查现在接受 `--bomb-profile=0..3`（原 `--marisa-b-bomb` 仍可用），
分别真实经过选人/选武器、移动射击、暂停恢复、X 启动、扣一枚、活动效果
绘制、结束与 viewport 恢复，四组都至第一关 1,110 帧通过。
三组新增截图 `game-bomb-reimu-a-browser/bomb.png`、
`game-bomb-reimu-b-browser/bomb.png`、`game-bomb-marisa-a-browser/bomb.png`
均已目视检查；Master Spark 图沿用 game-bomb-browser。
原版名字目前通过本地化键显示在临时 HTML HUD；CPU/绘制请求对照
不意味着原版 GPU 或 HUD 像素等价。四个浏览器报告均保留
completeGame=false/nativeEquivalent=false。

当前原版 Bomb 有效回调已接通；名称 HUD、其他 HUD/暂停/GameOver/结尾、
Boot/菜单/全部模式、录像/成绩/存档以及整作完整通关和音画等价验收仍未完成。


### Bomb 名称 HUD 与普通背景框架（2026-11-14 续）

前一节所述临时 HTML Bomb 名称已被原版 ANM 绘制替换。
MessageState 新增可选 storage，浏览器使用原版 HUD 的 0x4228 字节分配；
旧 MSG 对照默认仍为 0x4000 字节。hud-bomb-name.mjs 恢复 3d370
发布、3df89 底条初始化、3ff76 的立绘/名称更新、3cca0 立绘绘制及
41987 的底条/文字绘制。玩家 face 的 B/C 资源分别提供两种 Bomb 立绘，
名称使用 text.anm 的 735 脚本、原版本地化键和
[f0f0ff,0,10101,40202] 字体调色板，真实字体发布服务返回裁切尺寸。
发布同时设 c21974=3 并入队声音 14；退出在名称 VM 的 8a 中断字段写 1。
底条每次复制文字三轴位置，x 减 float32(7.111111164093018)，
横向缩放为 (裁切宽度+32)/精灵原始宽度。浏览器按照真实 viewport
暂时平移立绘和名称，绘制后恢复位置，避免误画到左侧边栏。

th06nc-hud-bomb-name-native-verified.json 覆盖 32 场景、5,760 帧、
320 检查点，完整 owner、声音槽、模式字段、绘制顺序与 VM 请求一致。
字体绘制在该检查中使用受控裁切尺寸，不证明字形/GPU 像素一致。
消息流程及四自机第一关整池 Bomb 对照重新通过。
四自机浏览器均检查真实 X 启动、15 帧名称/立绘可见、活动效果、
330 帧后名称/立绘不可见、扣弹与 viewport 恢复；每组到第一关
1,110 帧。四组 bomb-name.png 已目视检查。两次 Master Spark 启动时
浏览器未在 40 秒内进入标题，各自独立重跑通过；启动耗时原因尚未定位，
检查器现于超时输出 document.readyState 和游戏报告，供后续诊断。

hud-background.mjs 恢复原版 frame.anm 的 779/77a 两个 VM，分别位于
owner 31e0/3300；后者初始位置为 (213,0)。原版只在普通 HUD 更新中
推进 31e0。优先级 4 背景绘制任务 415d0 先设置深度范围 [0,1]，
在全局配置 c21dc0 的 bit 0x10 未置位时将主框架位置设为 (0,0,1)，
按 31e0/480/5a0/3300 顺序提交不透明白色调制绘制，最后用
509ba0 的 RGB 加不透明 alpha 覆盖 [236,16,620,464] 游戏区域。
480/5a0 的初始化和其他 HUD 所有者尚未恢复；当前保持非活动。
原版截图叠加分支单独存在，尚未实现。

th06nc-hud-background-native-verified.json 对真实 frame.anm 初始化、
120 帧更新及实际 415d0 绘制任务做 6 场景、720 帧、42 检查点对照，
覆盖隐藏标志和三种颜色，完整 owner 与相机/绘制/覆盖请求全部通过。
该证明不执行 GPU 或截图叠加。纹理清单加入原版 frame.dds 后为
58 文件、223,241,684 字节，均核对独立原版 DDS 摘要。

计分、最高分、残机/Bomb 图标、各仪表及暂停/GameOver/结尾 HUD
仍未完整迁移；Boot/其余菜单和模式、录像/成绩/存档、完整通关及
原版音画等价验收继续保持未完成，completeGame/nativeEquivalent 均为 false。


### 残机与 Bomb 图标（2026-11-14 续）

hud-stock.mjs 恢复 front.anm 连续 33 个 VM 的初始化
（owner cc0 起，步长 120，脚本 620..640）。当前普通更新恢复其中
32 个动画，槽 19 的敌人血条由独立特殊状态机处理，尚未接入，
因此明确仅实现 inactive 分支，不以普通 tick 代替活动血条行为。
40df3..41057 的残机/Bomb 绘制已恢复：x 从 809 以 -13 向左排列，
空图标在前，实图标随后；y 分别为 118/142，z=float32(.49)。
计数读取有符号 byte，保留负值产生超过八个空槽的边界；超过八时
保留八个实槽。绘制检查 inputFlags 的 3/c 掩码和配置强制绘制标志。
特殊生命模式改为一个图标和 deathCount 的 %d 数字请求。
原版普通标签绘制会先将刷新标志设为 2aa；当前浏览器在该标签所有者
尚未恢复期间显式提供这一标志，HTML 数值标签仍为临时显示。

th06nc-hud-stock-native-verified.json 覆盖真实 33 个 ANM 初始化、
120 帧普通 inactive 更新的六个检查点，以及 176 组有符号数量、
刷新掩码、强制绘制和特殊生命模式组合，共 3,312 次绘制/数字请求；
完整 owner 和请求均与原版一致。数字绘制在此处为请求边界，
没有验证特殊生命模式的字形/GPU、活动敌人血条或其余 HUD。

接入图标后的四自机浏览器回归再次全部到 1,110 帧通过，核对每帧
16 次普通残机/Bomb 绘制请求；最新截图已检查。四自机 8,000 帧
整池对照再次通过；相关九份 CPU/浏览器报告的源文件摘要均与当前文件一致。


### 原版标签、ASCII 数字及计分更新（2026-11-14 续）

hud-labels.mjs 恢复 3dcc3 的难度精灵选择和 3dcde 的模式标签开关。
后者实际读取 4f27c4，即 lifeProtection；不是紧邻的 4f27c5。
普通模式现在隐藏 Challenge Mode。40b51..40d43 按原版顺序提交
六个旋转路径和九个普通路径标签 VM，并将刷新标志设为
(flags & fffffeaa) | 2aa。hud-stock 对照现另有 80 组标签场景、
600 次绘制请求，覆盖五难度、两种模式标记、隐藏与四组刷新标志。
初始化后的完整 owner、精灵绑定、可见标志、绘制请求和刷新值一致。

ascii-text.mjs 恢复 9790 的完整 dbb8 字节 ASCII 管理器初始化、
9b07 格式化后文本入队和 9890 的真实字体绘制。256 项缓存逐项保留
缩放、颜色、相机模式、位置和备用字符集标志。普通字符指向
ASCII 码-21 的精灵，备用字符集使用 ASCII 码+98；不重绑 UV 矩阵。
空格/无效字符仍推进 float32(scaleX*12)，换行使用 scaleY*16 并恢复
起始 x；完整缓存按原版忽略新增请求。当前输入接口限制为每项
63 字节 Latin-1 文本，其他本地化正文继续使用原版字体图集发布。
入口不模拟超长文本覆盖缓存邻接字段的行为。
th06nc-ascii-text-native-verified.json 的 6 场景、24 次入队检查点、
60 次字形绘制对照完整管理器、缓存、VM、模式切换和相机请求；
格式化为预置输入，GPU 像素不在该证明范围。

hud-numbers.mjs 恢复 413c0..415b2 的分数/最高分、擦弹/点道具数字
请求和五组两位刷新计数退休。分数用 %.9llu、至少九位零补齐，
每多一位将起始 x 向左移 12；默认 x=723，分数 y=78、最高分 y=53。
擦弹 y=207、点道具 y=232；点道具读取无符号 16 位数量。
th06nc-hud-numbers-native-verified.json 覆盖 180 组数值/刷新/强制绘制，
690 次请求，直接调用 Windows UCRT 的 __stdio_common_vsprintf
核对 %.9llu/%d 的真实输出，坐标、文本和最终刷新标志一致。

score-update.mjs 恢复 Game owner 的 3a626..3a7bd。实际得分达到
10,000,000,000 时封顶 9,999,999,990；显示值以原版有记忆的步幅
逐步追上实际值，并保留 uint64 运算与追及边界。高分随显示分数更新。
原版五个奖残机阈值为 10,000,000 / 20,000,000 / 40,000,000 /
60,000,000 / 1,900,000,000。环境中现有 continueState 名称对应的
同一 byte d292 在此处用作奖残机索引，-1 会跳过奖残机；不应另建
互不相干的扩展次数字段。普通生命计数未满八时加一，特殊生命模式
减死亡次数，入队声音 28 并发布刷新标志。每帧至多前进一个阈值。
th06nc-score-update-native-verified.json 覆盖 504 场景、4,032 帧，
完整 owner、刷新和声音队列一致；持久成绩、完整宿主和帧任务不在证明内。

浏览器已接入这些模块，并停用临时 HTML 计分 HUD。当前分数与各数字
使用原版 ASCII 纹理绘制，标签、难度、残机/Bomb 与背景也来自原版 ANM。
计分更新与 StageWorld 每个逻辑帧相接，但整个 Game owner 的暂停、
任务和持久成绩仍未完全恢复，不能将上述单位证明扩大为整作等价。
Power 仪表、活动敌人血条、其他通知与结尾 HUD 仍待继续移植。


上述标签/ASCII/计分接线后的最终四自机浏览器回归全部通过，均到
第一关 1,110 帧。检查每次普通 HUD 绘制的 15 个标签、16 个残机/Bomb
图标、4 个数字文本及至少 20 次 ASCII 字形提交，并核对普通模式
Challenge 标签不可见、显示分数不超过实际值、最高分不低于显示值。
四份最新 bomb-name.png 已逐一目视检查。四自机 8,000 帧整池 Bomb
对照再次通过；该整池检查仍排除新增 HUD 和完整 Game owner。
本阶段十二份相关报告的源文件摘要均已核对当前文件，无过期项。


### Power 仪表与敌人血条更新（2026-11-14 续）

hud-power.mjs 恢复 3dd07..3ddd6 的初始几何和包装对象保存的精灵、
边距、原始像素宽度及逻辑宽度。仪表底和填充位于 owner 2a00/2b20，
位置依据原版 700/186/15.4/2.4 等 float32 常量逐项计算；游标 VM
位于 2c40。41057..413c0 未满火力分支直接改写共享精灵缓存的
右像素边、右 UV、原始宽度和逻辑宽度，并重算 VM 的 UV 矩阵；
满火力改绑下一张精灵，显示原版 MAX 图片。零火力不画填充，
保留游标和数值；未满火力的数值位于 (723,179.5,0)。

移植以 bank binding 中的 sprite 写时复制实现缓存变化，原始 ANM
资源保持只读，因此其他 bank/下一关重新加载不会继承裁切。所有
指向同一 binding 的 VM 仍可观察到同一缓存变化，不是单纯缩放四边形。
th06nc-hud-power-native-verified.json 覆盖 20 场景、360 连续绘制帧、
1,098 次绘制/数字请求，对照完整 owner、保存的度量和四个完整
64 字节精灵缓存，包括 0/1/15/16/31/32/63/64/127/128/129/65535
与 MAX 后退回低火力/零火力。完整原版缓存的 loader publication serial
在每个独立场景重建管理器时归零，不冒充跨资源加载标识的证明。
原始资源未修改亦被检查。该证明排除 GPU 像素及 front 缺失/卸载分支。

浏览器已绘制原版 Power 仪表。新增仅手动测试模式可调用的
previewHudPower，用受控数值绘制并恢复实际火力，不推进玩法或伪装成
实际收集道具。检查器保留独立 powerEvidence，覆盖 1/64/127/128/64/0，
核对原版 2/3 次绘制分支和数字在 MAX 时消失。power-64.png 和
power-128.png 已目视检查，正确显示半条/游标/64 及原版 MAX。
四自机均完成此前的实际键盘/战斗检查和这组受控 Power 绘制检查。

hud-enemy-life.mjs 恢复完整 front ANM 循环 3fcf6..3ff48：槽 19 在
没有对话时执行敌人血条进场/退场状态机，进场重绑 633，退场重绑
634；保留退场首帧重绑后的额外 tick。淡入按 4 到 255，淡出按原版
整数减 4，结束清零平滑值、三个分段和透明度。模式 >=2 时，生命
比例以 float32(.01) 向上、float32(.02) 向下追踪目标并保持夹取顺序。
在对话期间，槽 19 与其他槽一样推进普通 ANM，不执行该状态机。
此前 inactive helper 一律跳过槽 19，不能覆盖这个对话分支；浏览器
现使用完整 advanceHudFront 并连接已有 EnemyWorld.bossState。

th06nc-hud-enemy-life-native-verified.json 覆盖 144 场景、34,560 帧、
1,440 检查点，完整 owner 和包装对象头部一致，包括 0..3 初始模式、
异常透明度、超界比例、活动切换、对话及两个追踪方向。此证明仅涵盖
更新，不涵盖血条绘制、ECL 分段图遍历和倒计时文字/声音。
下一部分需恢复 40670..40b0e 的绘制所有者，并连接 21dc0/21fb0
对 ECL 回调/血量阈值的递归查询，不能用空分段数组替代真实查询。


### 血条分段查询与启动读取诊断（2026-11-14 续）

ecl-life-query.mjs 已单独恢复 21dc0 的结构遍历和 21fb0 查询接口。
它依据难度掩码扫描指令，不判断指令时钟、不执行条件表达式；
35/37..42 均递归扫描其目标子程序。93 设置 containsSpell，111 立即
成功返回，113/114 保存后续血量阈值和回调子程序。共享 visited[1024]
防止循环，层数大于八停止；当前指令位置和预排除回调参与遍历。
这些规则来自原版跳转表，不能用正常 ECL 解释器执行后的状态替代。
th06nc-ecl-life-query-native-verified.json 对七个原始文件、574 个
子程序及五难度做 17,241 次真实 21dc0 调用，逐一核对成功返回值、
完整元数据与 1024 字节访问集摘要，包括子程序中途、预排除、
层数八/九边界、末尾 sentinel 和非法索引。所有查询通过；
该结构查询尚未连接浏览器血条绘制；随后另执行 11,501 次真实
21fb0 包装入口，七个已加载程序的返回字段与访问集也全部一致。

血条绘制 40670..40b0e 尚待移植。现有信息：首次 dirty 时清空三个
分段；若当前 spellCounter 非零先记录比例 1，否则从第一个 boss 槽
当前子程序/PC 结构查询 containsSpell，并预排除其后续血量回调。
随后沿 a0/a4 的阈值/子程序链最多记录三段，只记录未来包含 93 的
阶段，比例为 min(1, float32(threshold)/float32(maxLife))。
主条 VM 在 2460，临时分段副本位于 3ec8，依次叠加三种 RGB
ffff8fa3/ffe62f4f/ffa855e0，保留主条 alpha。包装对象偏移零的数字
实际是 EnemyWorld.chapter（已有整关 native 检查覆盖），不是另造的
残余生命计数；倒计时来自已有 bossState.remainingSeconds。原版直接
调用 2a80，须核对其屏幕坐标，不能机械套用 67f0 立绘的 viewport 平移。

本次浏览器回归再次发生启动失败，新增超时报告明确显示 phase=error、
GameAudio 已解码 27 个 WAV，最后一次 GameAssets.load 抛 Failed to fetch。
因此前述未定位的启动问题已有具体资源传输失败证据，不能仅增加等待
时间掩盖。GameAssets 现限制同时六个字节读取，只对 TypeError 网络/
读取失败最多尝试三次，100/200ms 间隔；HTTP 错误立即失败，最终错误
带资源路径。失败的缓存 Promise 移除，以便后续显式重新请求。
th06nc-game-assets-verified.json 用受控 fetch 核对 24 请求峰值六、
去重/缓存、一次网络失败恢复、持续失败恰好三次、HTTP 404 不自动重试、
拒绝缓存清理。修复后的四自机实际浏览器回归均通过。该网络处理证明
不等于完整宿主/原版资源请求所有者等价，也不保证未来所有平台均无故障。

最终四自机浏览器回归再一次全部通过（每组至第一关 1,110 帧，
另有受控 Power 绘制证据）；四自机 8,000 帧整池回归通过。
本阶段十六份相关报告的当前源文件摘要与浏览器/整池公共模块清单
均已核对；Power GPU 像素、完整 Game owner、血条绘制与整作验收仍未完成。


### 敌人血条绘制入口与实际中 Boss（2026-11-14 续）

hud-enemy-life-draw.mjs 已恢复 40670..40b0e 的完整血条绘制前缀，
包括真实 ECL 分段查询、主条和临时分段 VM 拷贝、章节数字、倒计时
颜色/文字及不足十秒时变化触发声音 29。未满十秒且计数未变化时不
重新请求提示音；显示最多 99，保存的 previousSeconds 仍保留原数值。
%.2d 对负数的格式亦直接使用 Windows UCRT 核对。

Dirty 会先清除，但只有首 Boss 存在且 maxLife>0 才重建分段；
否则原版保留旧分段。本次整个入口对照发现并纠正了先无条件清空
分段的偏差。主条 anchor 设置、(300,24,0) 位置、float32(比例*288/14)
宽度、三个颜色副本和完整临时 VM 均与原版逐项一致。直接 2a80 绘制
使用 HUD 坐标，不额外添加 gameplay viewport 平移。

th06nc-hud-enemy-life-draw-native-verified.json 使用七个原始 ECL，
真实执行 21dc0/21fb0，覆盖 1,120 个受控 Boss 场景、3,030 次绘制/
数字请求。完整 4228 字节 HUD、54 字节任务头、分段 VM、dirty、
previousSeconds、字体颜色和声音队列全部对照通过；含缺少 Boss/
程序、零 maxLife、对话、进退场/透明度、显示溢出与负倒计时。
只替代 GPU 绘制、标准内存/栈检查服务和文字请求边界；请求中文字
通过真实 UCRT 格式化，不证明 GPU 像素或原版混音等价。

GameRenderer 已在原版 HUD 顺序中接入该入口，并连接实际
EnemyWorld.bossSlots[0]、program、chapter、spellCounter、remainingSeconds
和共用声音槽。浏览器检查新增 --enemy-life：沿实际第一关时间线推进，
1400/1750 帧使用普通 Bomb 输入掩码延长生存，不注入 Boss/HP 数据。
四自机均在 1883 帧实际观察到中 Boss 注册，在 1973 帧检查主条、
倒计时、dirty 退休及平滑生命值。633 进场 ANM 在时钟 61 结束，
此后才开始追踪生命比例；检查等待 90 帧，保留原版延迟。

四组 enemy-life.png 已产生，Master Spark 与灵梦 B 图已目视检查，
可见游戏区左上 Enemy 章节数字和白色生命条、右上倒计时。每组
报告将 enemyLifeEvidence 与此前至 1110 帧的普通流程、受控 Power
预览分开记录；这不是击败中 Boss、完整第一关或整作通关证明。
普通四自机 8,000 帧整池 Bomb 回归仍通过，其范围仍排除完整 HUD。

符卡名称/敌人立绘、奖励/其他通知、暂停/GameOver/结尾等 HUD 与
Boot/其余菜单和模式、录像/持久化、完整通关及原版音画像素验收继续未完成。

### 符卡名称、敌人立绘与三类奖励通知（2026-11-14 续）

hud-spell-name.mjs 已接入实际 opcode 93 的 publishSpellIntro 服务，
恢复 2787d..279a3 的立绘/文字 VM 重绑和 sprite 选择，以及专用字体
色组。3da0 名称底条初始化、4108/838 更新和 41a29..41abb 的底条/
文字绘制使用原始 ANM；取消字段直接别名到 HUD 8c2，由 opcode 94
写入并由 ANM 在同帧消费。该发布段不额外排声音，声音 14 由已有
beginSpell 随后请求。

th06nc-hud-spell-name-native-verified.json 覆盖七关实际使用的十种
(stage,portrait) 组合、两种自机角色、两种受控裁切宽度，共 40 场景、
9,600 帧、400 检查点。完整 4228 字节 HUD 与有序摄像机/绘制/文字
请求均通过；字体绘制边界仅提供受控尺寸，未证明字体或 GPU 像素。

hud-notifications.mjs 将三类通知直接绑定到实际 28 字节 HUD 记录：
Boss Bonus 6c0、Full Power 6dc、Spell Card Bonus 6f8。更新恢复
3fffb..401a0 的进场位置、float32 运算、计时溢出和 250/180/280 帧
失效；绘制恢复 3d0cd..3d34d，包括颜色、两倍奖励数字和游戏区裁切。
ASCII 渲染器使用请求中的 camera 字段启用 gameplay scissor，通知
坐标仍为完整 HUD 坐标。

th06nc-hud-notifications-native-verified.json 的 792 个场景执行原版
通知更新与实际 ASCII 入队入口，使用 Windows UCRT 格式化，逐字节
比较整个 HUD 和整个 ASCII manager 队列，含队列 255/256 边界。
发布链路另由 spell-end 896、boss-death 1728、item-collect 3024
场景验证：新增完整 HUD owner 摘要，证明生产者写入与上述别名一致。
这些生产者测试仍保留各自原有实体服务边界，未扩展为完整战斗验收。

另修正 HUD 点道具计数的语义接线：原版 41500 读取 4f27ba，即本关
pointStageCount，累计 pointTotalCount 位于 4f27bc。此前孤立算术
检查使用相同数值未暴露语义差异；现在传入刻意不同的累计值，确认
HUD 始终选取本关值，180 场景、690 请求仍通过。

浏览器 --spell-hud 与 --notifications 为受控预览：实际调用已接入
的名称发布服务，检查 15/45 帧立绘和名称、取消后隐藏；通知预览检查
四条文字请求与 281 帧后全部过期，最后恢复真实关卡状态。截图已
目视检查。它们不代表自然推进到 opcode 93 或捕获符卡。自然中 Boss
血条仍沿实际关卡推进至 1973 帧，不注入 Boss 或生命数据。

其余 HUD/暂停/GameOver/结尾、Boot 与其余菜单和模式、录像/持久化、
完整通关和原版音画像素验收仍未完成，整作目标保持进行中。

本阶段最终四自机回归均通过：真实菜单、物理 X、Bomb 结束和受控
Power 预览、实际中 Boss 血条至 1973 帧，以及受控符卡名称/三类通知。
四自机 8,000 帧、660 检查点整池回归也通过；该整池范围仍排除 HUD。
上述十八份 CPU 报告与四份浏览器报告共二十二份，当前源文件摘要
及浏览器/整池公共模块完整清单均已核对通过。资源请求并发/重试检查
另单独通过；所有报告均保持 completeGame=false。

### 原版普通游戏暂停对象与浏览器接入（2026-11-14 续）

pause-menu.mjs 恢复 ASCII manager +52d0 的 da0 字节暂停对象，使用
原版 a120 更新、aee0 绘制、9e80 菜单标签发布。资源为 intext.anm，
slot 53/base 76b；动态文字仍绑定 text.anm 的 740 起 sprite。
正常菜单是解除暂停、返回主菜单、从头再来。方向键使用边沿触发，
前四帧忽略选择/确认；Esc 对应退出暂停的 400 位。恢复要等待二十帧
退场，重新开始同样等待二十帧；返回标题先退场，再由真实 NativeFade
执行三十帧黑场。确认默认选“否”，方向键切换，X/否返回菜单。

标签先清理 VM 再绑定 sprite，不运行文字脚本；字体正常色组是
[ffffff,0,10101,40202]，选中色组是 [c0e0ff,302080,10101,40202]。
原版文字 VM 的 b4=-1，区别于脚本重绑的 -999。暂停进场的 c70 VM
需要 interrupt 1；这两个细节由完整对象比较发现并修正。确认时默认
“否”的时钟从零开始，位置插值 Z 也为零，未把反汇编中被覆写的
寄存器旧值误作常数。

th06nc-pause-native-verified.json 覆盖 96 场景、8,840 帧：菜单等待、
进场按键门槛、上下/同时上下、确认恢复、Esc、返回标题确认、取消、
重新开始、两个快捷位、禁音/队列满，以及同一对象退场后再次打开。
逐帧比较整个 da0 字节对象、全部有序字体请求、绘制 VM、声音槽、
暂停 active 字段、Supervisor 请求（返回标题 1/重开 12）和 56 字节
fade。执行真实 setter/ANM/绑定/绘制和
fade 代码，仅将本地化查找/字体绘制、GPU/摄像机与栈检查作为边界。
字体边界使用受控 crop，音乐 handle 固定 -1，截图捕获关闭；不证明
这些平台服务或其他模式的 handoff 与原版等价。

网页普通游戏已用该对象替换临时 HTML 暂停面板；Esc 和失焦进入暂停，
暂停期间 StageWorld 不 tick。恢复后复用同一对象，下一次打开保留
原版未清理字段；新关卡才换对象。渲染按 gameplay viewport 平移和
裁切。新增两组已有字体资源和原始 intext.dds，资源清单增至 59 文件、
227,436,136 字节，每个 DDS 继续与已有独立原版摘要核对。

浏览器检查真实 Escape 输入后等待菜单稳定，确认游戏帧不变，再检查
二十帧退出期间仍冻结，之后恢复关卡。--pause-workflows 进一步通过
真实方向/Z/X 输入执行默认否确认、取消回菜单、确认重新开始（原
机体、分数零、Bomb 3、第一关新开）、确认返回标题及标题 BGM 切换。
这些 handoff 接到当前网页普通游戏入口，并非原版完整 Supervisor、
录像、种子/存档或音乐 pause/resume 状态验收。pause.png 和
pause-confirm.png 已目视检查，原始位图标题/确认文字仍是日文素材，
菜单标签使用已有中文本地化字体。

GameOver/结尾、其余模式与菜单、录像/存档、完整通关、暂停可选截图
和原版 GPU/音乐 owner 等价继续未完成，整作目标保持进行中。

本阶段最终四机体浏览器回归（含 --pause-workflows）全部通过，受控
符卡/通知和真实中 Boss 血条至 1973 帧也继续通过；随后每组确认重开
和返回标题。四机体 8,000 帧整池回归仍通过。十九份相关 CPU 报告与
四份浏览器报告共二十三份，已核对当前源码摘要、163 个公共模块
完整清单，以及 59 个实际纹理文件和各浏览器资源清单摘要。资源传输
并发/有限重试检查另行通过。所有报告继续保持 completeGame=false。

### Game Over / 普通续关对象（2026-11-14 续）

game-over-menu.mjs 已恢复 ASCII manager +6070 的 da0 字节对象，
执行 b4f0 更新与 bce0 绘制。继承暂停对象的 VM 视图、选择性重绑和
声音服务，但使用独立状态与四个菜单 VM：771、772、76f、770；c70
背景仍为 773。初始默认“否”，等待三十帧后才能切换/确认；“是”
状态输入门槛四帧。X 和 Esc 不替代确认键。确认续关先等待三十帧
退场，然后清除 gameOverRequested，沿当前 Player state 1 继续复活，
不重新创建关卡或自机。拒绝续关等待二十帧，再请求 NativeFade 的
三十帧黑场，最后请求原版 Supervisor state 7（成绩登记）。

普通游戏仅允许 continuesUsed<3 且 difficulty<4；次数位于 4ff0dc，
不是 4ff0f2 的 score-extend index。确认后次数加一，分数及显示分数
都设为该次数的 uint64 值，scoreDisplayStep 清零；残机/Bomb 取配置
c21de0/c21de1，inputFlags 清/置为原版 2aa 格式。totalGraze、Power、
pointStageCount、score-extend index 清零；pointTotalCount、stageGraze、
highScore 和死亡数等原版未写字段保留。额外/练习/录像/符卡练习的
分流也按原版形成请求，后续目标对象继续独立验收。

绘制还会把 120 的 VM 完整拷贝到 480，x 加 float32(scaleX*8)，
仅替换 sprite 指针为 ASCII 数字 3-continuesUsed，不重新绑定/改写
UV 或 sprite ID。该副本的持久字节和临时绘制副本均参加对照。菜单
选择脉冲按原版七十二帧周期、颜色/透明度和 -11.11111068725586 的
临时 y 偏移处理。

th06nc-game-over-native-verified.json 覆盖 170 场景、6,254 帧，逐帧
比较整个暂停形状 owner、全部有序绘制 VM、声音槽/禁音字段、56
字节 fade，以及二十一个实际环境字段。包括各续关次数/额外难度
限制、默认否、输入门槛与同时上下、声音满队列、同一个 owner 连续
重开三次续关并触发次数上限，以及练习/录像/符卡练习分流。实际
setter/绑定/ANM/float/int/fade 均执行，GPU/摄像机/栈检查为观察边界，
可选 screenshot 捕获关闭；成绩登记/录像/符卡练习目标仅验证请求，
不代表这些模式或整个游戏完成。

网页普通死亡已接入该对象，替换原 Game Over 静态 HTML 面板；菜单
运行期间 StageWorld 冻结。续关保留同一关卡/敌人/项目状态，交给
现有真实 PlayerLife 继续复活和消弹。新关卡才换 GameOver 对象。
拒绝续关后的原生成绩登记对象尚未移植，目前停在明确的 score-entry
阶段，保留 scoreEntry 请求并显示临时结果面板，不直接当作原版标题
返回或宣称成绩已经保存。

浏览器 --game-over 先沿实际第一关使用普通射击输入，直至真实零残机
请求（不注入自机/生命/Boss），等待四十五个菜单 tick，确认冻结；
然后实际 Up/Z 确认、三十帧退出，再检查分数/残机/Bomb/Power/本关
点数重置和六十帧真实复活无敌过程。game-over.png 和 continued.png
已目视检查，包含原始日文续关/是/否位图、剩余三次数字，以及续关后
分数 1、Graze/本关点数零。只是有限关卡轨迹，未证明完整战斗/通关。

另增独立 th06nc-game-over-decline-browser-verified.json：魔理沙 B 在
第一次续关后继续普通关卡输入，第二次自然零残机发生于 7,745 帧；
实际 Z 接受默认“否”，经过原版退场和黑场，原关卡帧保持不变，
发出 scoreEntry 请求。后续明确为临时结果面板，成绩登记/持久化仍
未完成，未把该请求误作已登记成绩。

本阶段最终四机体浏览器（--game-over 与 --pause-workflows 同开）
全部通过：灵梦 A/B 自然死亡帧为 2690/2260，魔理沙 A/B 为 2852/2852，
每组续关后实际再运行六十帧，并继续完成暂停的取消/重开/返回标题。
此前中 Boss 血条至 1973 帧、受控符卡/通知和物理 Bomb 检查也通过。
普通四机体 8,000 帧整池回归继续通过，其范围仍排除完整菜单对象。
二十份相关 CPU 报告与五份浏览器报告共二十五份，当前源码摘要及
164 个公共模块完整清单已核对；全部保持 completeGame=false。

### score.dat 封装与排行数据（2026-11-14 续）

新增 score-file.mjs，恢复原版 6ca60 的链式异或解码/十六位校验和与
74a3a..74aa2 的编码。byte 1 是初始链值；每步先做 uint8 加法再 ror 5，
解码出的明文字节继续参与下一步链值。校验和为明文 byte 4 起全文件
之和模 65536。常规头长 20，8 处 int32 指向首记录，10 处 int32 为
声明结束；每块 tag 后的 ushort +4 为跨度。必须包含 TH6K 标记。
API 保留原始头、未知记录及尾部字节，均返回独立字节副本；对越界、
零长度记录等另做有限解析保护，不宣称原版所有畸形输入也安全拒绝。

实际 score.dat 只读验证：51,600 字节、140 块（TH6K 1、CLRD 4、
CATK 134、MUSC 1），解码后重新编码与原始文件逐字节一致。未将用户
存档复制进网页资源，也未改写 H:/Games/th/06nc/score.dat。
th06nc-score-file-native-verified.json 将原始文件与不同种子/跨度的
合成容器交给真实原版解码和编码块：30 组解码/重编码均一致，30 组
单 bit 损坏均拒绝，另有四组严格截断检查。只替代分配/拷贝/释放；
不包含磁盘 I/O、全记录序列化或结果画面。

score-tables.mjs 恢复六十组排行（3 mode * 5 difficulty * 4 profile），
每组初始十条 SYMD 占位，从 1,000,000 每名递减 100,000，默认姓名
八字节“Nanashi ”。真实 HSCR 为 36 字节：score uint64 +0c，profile/
difficulty/mode/stage 各 byte +14/+15/+16/+17，八字节姓名和 NUL 位于
+18..+20。姓名初始化逐原始 UTF-8 字节过滤到 ASCII 20..7e，遇 NUL
或不足八字节后补空格。默认占位与实际 HSCR 保持不同 tag。

实际 6cbc0 以无符号 uint64 降序插入，新同分条目放到旧同分之前。
插入本身不截断链表；写出时每组只遍历前十个节点，遇 SYMD 不写出，
但占位仍消耗名次。HSCR 写出重设两个长度、+8 的版本 0x15、+9 保留字节和
三种分组字段，然后按 mode/difficulty/profile 顺序串接。

th06nc-score-tables-native-verified.json 比较完整 600 条默认原始记录、
64 场景/1,536 次真实链表插入后的名次和有序原始记录、九种姓名输入。
包括零分、同分、32 位以上与 uint64 高位/最大值。默认记录创建子检查
仅观察其 list 服务，插入逻辑另执行真实 6cbc0；未比较无用途的宿主
链表指针布局。姓名检查在跳往结果状态前结束，不代表键盘选字界面。

th06nc-score-table-io-native-verified.json 再执行真实默认创建、74219
加载筛选与 7458e..747a4 的 HSCR 写出前缀，覆盖所有六十组。725 个
输入（含不匹配版本/分组与未知 tag）加载后连同占位共 1,320 个节点；
最后写出的 420 条 HSCR 字节与移植一致。只替代分配；其他记录类型的
canonical 写出、完整存档 owner、磁盘提交和 UI 仍未验收。

这些模块目前作为成绩登记的数据基础，尚未接入网页结果界面或本地
持久化。网页 GameOver 之后仍停在已记录的临时 score-entry 结果面板。
本阶段没有改变已运行的玩法/渲染/浏览器模块，不重复运行其完整关卡
测试，也不以此前浏览器报告声称新数据层已完成浏览器保存验收。

本阶段三个新原版检查均通过。原有二十五份报告所列依赖文件仍与当前
字节一致，三份新报告覆盖新增数据模块，共二十八份报告逐项核对
通过。旧浏览器报告的公共模块清单仍冻结在此前版本；新模块没有
被当前网页加载，不能把这次摘要核对理解成新增 UI/持久化已验收。
原始 score.dat 文件摘要也再次确认未变化。整作目标继续保持进行中。

### 姓名输入、登记资格与结果动画对象（2026-11-14 续）

score-name-input.mjs 恢复 state 9 的 70dca..71435 输入段和 6d190
光标初始化。字符表是原始 30c250 的 96 个单字节格，分成六行十六列，
94 为空格按钮、95 为结束；方向移动按行/列回绕并跳过空白格。已有
姓名先统计八字节内的非 NUL 长度，再去掉末尾空格；非空时选结束，
空名时选首字母。保存编辑长度独立于八字节缓冲区，不把补齐空格当
作用户已输入内容。

输入门槛三十帧；方向、Z、X 都接受边沿或 repeat，Esc 仅接受边沿。
多键依原版顺序处理：上、下、左、右、确认、删除、Esc。第八个字符
输入后自动移到结束；满八字节时仍可在字符格替换最后一字节。X 从
末尾删除并写空格。结束/Esc 请求 Achievement21 和保存前次姓名，
随后改状态 15、清帧计数、给 38 个 VM 写 interrupt 2，将姓名复制到
9e88 缓冲。Steam 成就与配置写盘均作为服务请求，不调用外部平台。

th06nc-score-name-input-native-verified.json 对照整个 bb48 字节 owner、
三声音槽和有序服务请求，覆盖所有 96 格、长度 0/1/7/8、组合/保持/
重复输入、29/30 帧门槛，共 24,576 场景和八种光标初始化。2,682 个
结束请求及其字段写入一致。服务仅观察，ANM/共用尾部/绘制/配置文件
并未包含在这个输入段证明中。

result-state.mjs 定义结果资源计划与 60 个真实 VM：五个 result.anm
背景从 3d70 开始，38 个 result00..03 前景从 b0 开始，十六个 text
sprite 从 2b70 开始，difficulty sprite 在 4310。原版 result00..03
加载 base 分别为 798/7a0/7a7/7bd，背景 base 7d0，难度 sprite 792。
这些位于 th06TL.dat，动态 text.anm 仍在 th06IN.dat 的 slot 0/base72f。

恢复了 7583c 的五背景重绑、73e93 的前景/文字初始化、72743..727ef
的公共 ANM tick 与帧/pulse 更新。纯 sprite 重置的 b4=-1、可见位为
1，区别于脚本发布的 -999 与初始不可见；整对象对照发现并修正了
文字/难度 VM 可见位的差异。这里的 ResultState 仅含原始 VM/字段，
不把宿主排行数组指针伪装成原版地址。

th06nc-result-animation-native-verified.json 使用七个真实 ANM 资源，
40 场景/4,800 帧比较完整 bb48 字节（仅资源/精灵地址正规化），覆盖
八种 interrupt、0/1/9/15 状态关系、pulse 回绕和 int32 帧溢出。初始化
与公共尾部通过，不等于完整状态派发、结果绘制或资源 I/O 已接通。

score-qualify.mjs 恢复 70bab..70dca 的待登记记录和前十判断。候选
记录直接位于 owner 9e58，临时版本 byte +8 为 0x10、+9 为 1，长度字段
仍由最终 HSCR writer 补写；不能把它当作已经编码好的磁盘记录。
分组来自 owner +4/+a8/+ac 和当前 shot，过关标记为真时 stage 写 99，
否则写实际关卡。以真实无符号分数插入后，rank<10 保持 state9 并
初始化姓名光标，rank>=10 转 state15 并给 38 个 VM 写退出 interrupt。
排行里保留候选缓冲的 view，编辑姓名时同一条记录随之变化。

th06nc-score-qualify-native-verified.json 覆盖 1,920 个角色/机体/难度/
模式/分数/过关标志/前次姓名场景，原版实际执行登记段、6cbc0 插入
与前次姓名读取，1,280 个合格、640 个不合格。完整 owner 仅将所选
rank-head 的宿主地址字段正规化为零，并比较真实有序链表记录。所有
1,280 个合格场景再接真实姓名输入段，输入 A 后结束，确认已在排行里
的候选记录确实原地改名，而非修改脱离排行的副本。分配/memset 和
成就/配置请求是边界；标签发布、共用 ANM tick、完整 UI 未包含。

三个新模块目前是原生结果界面的基础组件，尚未接入浏览器 GameOver
之后的临时 score-entry 面板。结果绘制、其余状态、配置/成绩落盘和
页面重载后的恢复继续未完成。玩法/渲染入口本阶段未修改，不用旧
浏览器回归为这些新组件或完整保存流程背书，整作目标保持进行中。

本阶段三个新增原版检查全部通过，且三十一份相关报告逐项源码摘要
核对通过，所有一百六十九个公共模块均在各自范围的报告中有记录。
旧浏览器快照仍保持此前模块清单，并不覆盖本次未接入的新组件；
没有用更新摘要冒充新的浏览器交互验收。原始 score.dat 摘要也未变化。


## 普通 GameOver 后姓名登记页接入（2026-11-14）

result-name-draw.mjs 恢复 72890 的 state9/viewMode!=8 分支：五个背景、
38 个前景 VM、两列机体标签和各十名记录、当前候选颜色/姓名光标下划线、
96 格字符与 SP/END。保留 float32 位置、缩放和原始绘制顺序；恢复临时
位置，保留原版持久标签字段修改。文字使用原版 ASCII 队列及容量门限。
其 th06nc-result-name-draw-native-verified.json 为 360 场景，比较完整
bb48 owner、dbb8 ASCII manager 与有序绘制请求；仅正规化资源和逻辑
链表指针。真实 9aa0/38740 与 UCRT 格式化仍执行，GPU 和独立 supervisor
尾部在范围外。九位分数字段是空格填充，未改成补零。

result-name-scene.mjs 连接 state9 首帧角色/难度/模式初始化、两个本地化
机体标签（%s / %s）、资格判定、姓名编辑、公共 ANM 尾部与 NativeFade。
模式字段按 lifeProtection 布尔值取值。姓名修改保持排行候选记录的活视图。
th06nc-result-name-scene-native-verified.json 执行原版完整 6e3a0 dispatcher，
96 组场景共 2,784 帧比较 owner、fade、声音和字体/成就/配置请求；真实
结果 ANM 和插入链表执行。字体裁剪、成就与配置写入仍是受控服务边界。
未以服务请求代表真实成就或磁盘保存。

普通 GameOver 拒绝续关现在加载真实结果 ANM、原版 DDS、text.anm 和 ASCII，
进入上述姓名页。六张额外结果纹理经独立 DDS 原版摘要校验，纹理清单现有
65 项、251,816,416 字节。动态字体使用现有原版字体缓存。
浏览器 th06nc-game-over-decline-browser-verified.json 从自然残机耗尽开始，
先续关一次、再次耗尽后物理 Z 接受默认 No，等待退出与淡出，再检查排行和
96 格字符表。物理 Z/右/X/Escape 完成 A、AB、删除 B、补回 B、结束登记，
最终是原版 state15 交接，关卡时钟持续冻结；WebGL 无错误。检查了实际
name-entry-filled.png，双列中文标签、候选 AB 下划线和字符表均可见。
本次浏览器仅为普通模式的指定机体路径，不代表所有模式/难度的登记验收。

登记后仍显示明确标注未移植的临时汇总面板；尚未接入原版汇总绘制、录像
选择或持久化。前次姓名只保存在当前网页会话变量，各次排行仍从默认表开始；
没有写原始 score.dat、浏览器持久存储或冒充存档成功。

result-summary.mjs 继续恢复 726c6..72743 的 state15/16 输入段：clock<=30
向前景37写 interrupt16；clock>=90 的确认按下边沿进入16并清零时钟；16在
clock>=30时设 clock59、state10，公共尾部后是clock60。暂未连接浏览器。
th06nc-result-summary-native-verified.json 为 288 组边界状态，覆盖按住/
松开/复合输入、30/90帧门限与 int32 溢出，比较原版完整 dispatcher 和
公共 ANM tick 后的 bb48 owner。此证明不覆盖汇总绘制和 state10 后续行为。

本次补跑四机体合计 8,000 帧玩法原版对照，660 个检查点、4,399 次敌机状态
比较通过，状态摘要保持 cb77c16eec5288990190ff720614f70252c2d3f69d0d49217640ca65c8b550bc。
整作目标继续 active；汇总/录像/保存、其余模式菜单和原版像素等验收仍未完成。


本阶段四机体浏览器回归全部通过，覆盖 Bomb、受控字幕/通知预览、自然
GameOver 后续关、暂停取消确认/重开/返回标题；各自玩法恢复检查点仍为
2750/2320/2912/2912。首次启动补跑曾遇到 ES module 连接拒绝，预览服务器
将 Windows 监听队列从默认值扩大到128，并将日志输出到文件；随后三种
机体连续回归通过。浏览器检查增加网络失败诊断，不把超时写成通过报告。

th06nc-source-current-audit.json 记录本阶段当前95份源码摘要一致的报告及
65份历史摘要不同的报告，172个公共模块均有当前摘要记录；原始score.dat
SHA256仍为44805e2691e6d208290a9ecdbe3eec26d7d1a7ddb6e84ca21d2a502732609441。
这只是源码快照核对，各报告仍仅支持自身声明的范围，未重写旧摘要充当回归。


## 成绩汇总绘制、速度统计与录像询问基础（2026-11-15）

result-summary-draw.mjs 恢复 72890 的 state15/16 路径，包括退出中的双列
排行（与 state9 不同的表索引/颜色）、公共背景/前景、难度 sprite，以及
最终得分、模式、进度、续关/Miss/Bomb/符卡取得数和处理落率八项文字。
进度分母按难度分为89500/39600；非Easy且cleared时固定100%。运行速度
分数按float32比例、[0,1]裁剪及原版%3.2f格式显示，保留零分母的原版
-nan(ind)%边界。模式标签来自原版静态Standard/Challenge字节串，不替换为
另一个格式。th06nc-result-summary-draw-native-verified.json 共288场景，
覆盖15/16、四个排行索引、离场位置、ASCII队列临界容量、不同难度/模式/
进度/统计输入，比较bb48结果对象、dbb8文字对象和有序VM/相机请求。
真实UCRT格式化执行；资源和逻辑排行指针正规化，GPU像素仍不在范围内。

result-name-scene.mjs 现在继续更新 state15/16，使用同一输入历史、ANM对象
和淡入状态，直到原版state10/clock60。姓名登记的旧96场景原版检查重跑，
2,784帧摘要不变。新增th06nc-result-summary-scene-native-verified.json
执行完整6e3a0，96场景/16,512帧包含过早确认、合格/不合格成绩、姓名编辑、
汇总等待、确认和退出，最终进入录像选择交接。比较完整对象、声音、淡入
和服务请求；字幕裁剪和成就/配置写入仍为服务，未证明磁盘保存。

runtime-speed.mjs 恢复3c66e..3c6da的速度统计：每个采样窗分母加60，FPS
严格大于54/42/30时分子分别加60/48/36，否则加30，float32累加。
th06nc-runtime-speed-native-verified.json 600个阈值/停用/精度样本通过；
th06nc-runtime-speed-window-native-verified.json 进一步执行3c5ec..3c6da，
受控微秒时钟共1,200次采样，比较半秒门限、帧计数/时间和两项统计字段。
只把FPS文字输出与时钟获取视为服务，未证明Windows限速/睡眠和完整生命周期。
网页使用performance.now提供平台时钟；手动CDP运行使用明确记录的60Hz
受控时钟，不把其处理落率当作实际性能测量。重新开始时清统计分子/分母。

浏览器GameOver拒绝续关后已用原版汇总替换临时HTML成绩面板，绘制字段
来自当前游戏/符卡/时间状态。指定魔理沙B路径检查了八项排队文字、难度
图标、冻结的关卡时钟、提前确认无效、90帧后物理Z接受和退出30帧。
result-summary.png及result-summary-settled.png分别留存进入及稳定画面。
最终仍在录像选择入口显示未移植提示；未构造可保存录像、未写原版文件，
前次姓名/默认排行处理沿用上一节所述的会话内行为。四机体原有Bomb/HUD/
自然GameOver续关/暂停取消确认/重开/回标题浏览器回归再次全部通过。

result-replay-gate.mjs 继续恢复state10/11的询问基础：clock60按是否续关
选择interrupt9或12；续关时转不可保存提示11，提示20帧后仅Z/X确认离开。
普通询问80帧后才接受左右循环选择，左优先、支持repeat；X/Escape取消，
No确认退出到state2，Yes请求6d310录像列表服务。保留两个选项的原版颜色
位操作、声音队列和38个退出interrupt。此组件尚未接入网页。
th06nc-result-replay-gate-native-verified.json 1,280组边界状态执行完整原版
dispatcher与公共ANM尾部，比较bb48对象、声音和列表请求；6d310作为明确
服务边界，文件/列表读取和真实录像保存不在范围内。下一步继续恢复它的
状态/列表加载，再接上状态2退出；不以一次服务请求代表保存成功。

本阶段最终源码快照核对：99份报告摘要一致、66份保留为历史快照，
175个公共模块均有当前摘要记录。浏览器稳定汇总截图已检查，文字/图标
完整可见；原始score.dat摘要未变，目标继续进行中。


## 录像页绘制、资格提示与结果淡出（2026-11-15）

result-replay-draw.mjs 恢复72890中state2及10..14/viewMode!=8的绘制：公共
背景/前景与退出排行、重复绘制的六个控制VM、表头、每页十五个/共六十个
录像槽位、无效/空槽占位、有记录时的姓名/日期/自机/模式/难度或SpellPr
编号、state13当前姓名/日期和下划线及96格字符。保留Native的标准标签字节
和格式宽度；日期/姓名来自原始120字节头，当前编辑来自owner字段。Native
仅在合适模式/难度时绘制复用的难度VM。th06nc-result-replay-draw-native-
verified.json覆盖864场景，实际原版72890及UCRT格式化执行，比较完整结果/
文字对象与有序绘制请求，包含2/10/11/12/13/14、分页、有效/无效版本/空槽、
四模式/四自机、候选编辑和ASCII满队列边界；GPU像素仍不在范围内。

result-exit.mjs 恢复state2/6f9c5..6faaf：仅首次请求淡出，普通流程30帧
白色、独立结果10帧黑色，等待fade.mode2。普通流程还要求owner无符号时钟
至少30，任务完成时跳过公共ANM/时钟尾部，并请求supervisor状态1。
th06nc-result-exit-native-verified.json执行完整原版dispatcher及真实淡出，
30场景/519帧比较结果对象、淡出对象、task返回值与supervisor状态，包含
独立标志、负时钟、30帧边界和不同初始透明度。写盘与销毁仍未包括。

result-name-scene.mjs 接上state10/11询问和state2退出。普通No或X/Escape
取消以及续关后的不可保存提示可走真实退出；Yes仍交接replayListRequested，
不伪装成已保存。th06nc-result-replay-gate-scene-native-verified.json扩展
完整流程为384场景/86,016帧，执行9/15/16/10/11/2，比较bb48对象、淡出、
声音和标签/姓名/列表请求，最终是真实任务返回0或列表服务交接。6d310
列表读取在这个全流程证明内仍为服务，单独的初始化证明见下段。

浏览器自然耗尽残机、续关、再次结束、输入AB、汇总确认后，现展示原版
“续关后不可保存录像”提示，再物理Z进入state2，原版白色淡出完成后返回
标题并切回标题BGM。replay-not-eligible.png已检查文字和版面完整可见，
整段WebGL无报错；四机体原有Bomb/HUD/GameOver续关/暂停确认回归再次通过。
校正浏览器诊断推进帧数：press辅助函数自带一次松开tick，故在state16
确认后再推进29帧恰到state10/clock60，下一帧才进入11；未修改原版门限
以迁就测试。完整录像列表的Yes分支仍显示明确的未移植提示。

result-replay-list-init.mjs 恢复6d310..6d451与实际6d1e0初始化：声音10、
state12、38个VM interrupt10、从4438恢复所选槽、清时钟，建立replay目录，
按replay/th6_01.rpy到th6_60.rpy依序请求六十个已验证/解密的头，复制前
120字节；不存在的槽保持旧内容。th06nc-result-replay-list-init-native-
verified.json为24个场景，执行真实函数，比较完整对象、声音、目录和六十次
文件请求，覆盖全空、间隔/全部存在、旧槽内容和分页选择。目录、格式化、
文件读取/解密和free仍为服务；此组件尚未连接网页列表导航。

replay-file.mjs 恢复6af60的文件体解码、6b110校验和6c908..6c93f已组装
文件编码。T6RP签名/version010f，seed在0x12，从0x13起逐字节减/加seed，
每字节seed加7回绕；checksum是0x2f10a329加0x12到文件尾的字节和。
解码后日期+0x1c与姓名+0x25置零、checksum字段清零，七个stage地址在JS
保留相对偏移；与Native比较时将其真实堆指针正规化。主机明确拒绝120字节
不足或非零stage偏移落到文件外/头部，不复现原版未检查边界的内存读取。

th06nc-replay-file-native-verified.json使用32个不同长度/seed的已组装样本，
执行实际原版checksum/加密和解码/地址修正，全部编码、解码及再编码一致；
32个损坏文件拒绝、4个主机截断检查通过。这里只证明codec，不把人工组装
的样本当成实际游戏录像，也未接上录制、播放、列表持久化或磁盘写入。
原目录目前只有steam_autocloud.vdf，没有可用真实.rpy样本；未修改原始文件。
整作目标继续active，后续仍需列表导航、名称/覆盖确认、录制/保存/回放等。

本阶段最终快照由tools/th06nc-source-current-audit.py生成：103份报告
源码摘要一致，67份历史报告保留，179个公共模块均有当前摘要记录。
这只是范围不变的源码核对，不将快照包含视为功能执行。原始score.dat
摘要仍为44805e2691e6d208290a9ecdbe3eec26d7d1a7ddb6e84ca21d2a502732609441。


## 录像列表导航、覆盖确认和姓名编辑（2026-11-15）

result-replay-list.mjs 恢复state12/14的输入更新。列表首帧沿用独立的头读取
服务，20帧后接受输入；上下逐项回绕60个槽，左右分别加45/15模60，均支持
repeat；上下及左右各自依序处理，组合输入不误改成单方向优先。4438保留
所选槽。Z确认优先于X，生成本地日期并复制录制元数据mode/detail；空槽或
不支持版本进姓名编辑13，有效T6RP/010f槽转覆盖询问14，所选行interrupt14。
X返回普通保存询问10或独立结果关闭2，Escape在列表12中按原版忽略。

覆盖询问先更新选项颜色，20帧后左右选择（左优先），Yes进入13并初始化
追加光标，No/X/Escape调用真实列表初始化返回12。姓名光标从9e88读至8字节
并去尾空格，与成绩候选姓名9e70分开。th06nc-result-replay-list-native-
verified.json覆盖4,608个列表/覆盖边界、槽位、已有文件、独立标记、组合/
按住/repeat场景，执行完整6e3a0及实际6d310/6d1e0，比较bb48对象、声音与
文件读取请求；日期与已验证头作为受控服务。头初始化检查重跑24场景，
摘要8d4d96fb30b56179d38a7121cb8a51b4624c0246d601917097db1ebc3dd4b307不变。

result-replay-name-input.mjs 恢复state13/7169f..71b7c，使用原版96格表、
30帧门限和9e88姓名。End与成绩登记不同：先请求录像写入和前次姓名配置，
转2/清时钟/38个退出interrupt，然后仍执行共用长度增加和声音10尾部；
不能提前return略过这些字段。X继续删除，Escape返回列表；End+Escape组合
可在同一帧先请求写入再回列表，服务参数必须在后续修改前复制。没有为它
添加成绩登记的成就请求。th06nc-result-replay-name-input-native-verified.json
共24,576场景及8组光标初始化，比较完整对象、声音和写入/姓名请求，覆盖
全部格子、0/1/7/8字长度、组合输入、禁音及队列已满；实际文件写入在边界外。

ResultNameScene通过replayServices接入上述12/13/14流程；保留不提供列表
服务时的明确交接，供范围较早的CPU检查使用。实际网页提供当前玩法的mode/
难度元数据和本地日历，空槽列表可导航、进入姓名、取消回列表、X回询问、
No后走原版白色淡出返回标题。当前没有录制器和已保存文件服务，列表为空，
输入End会明确提示“当前尚未生成可保存的录像数据”，不会产生占位.rpy或
显示保存成功。前次姓名仍只有当前网页会话变量，未做磁盘/浏览器持久化。

th06nc-result-replay-list-scene-native-verified.json执行完整6e3a0、真实列表
初始化/公共ANM/淡出，64场景/25,376帧包括四机体、两难度/模式、空槽与已
占用槽、覆盖No/重进/Yes、姓名导航/输入、Escape取消或End写入请求，最后
任务返回0到标题。比较结果/淡出对象、声音和服务事件。录制文件writer和
配置调用仍仅观察请求，文件头读取/本地时间受控；绘制/真实写盘/回放未证明。

新增浏览器--replay-list走自然未续关GameOver、成绩登记/汇总到默认Yes，
验证20帧列表输入门限、上翻0到59、右翻到14、下移到15、第二页显示、空槽
姓名删除、Escape返回所选槽、X回询问和No淡出。replay-slots-page-2.png与
replay-name.png已视觉检查，当前日期、自机、模式、难度与光标显示正确。
--replay-list-save-request另验姓名End显示录制器未接入提示，再以物理鼠标
点击返回标题；不把它称为录像保存。已有的续关后不允许保存路径也补跑通过。
浏览器加载门限改为60秒并在超时边界再读取一次真实条件，避免已抵达标题
却在最后一次轮询边界被误判为启动失败；网络/脚本异常仍保留诊断。

最终四机体新增列表流程浏览器检查全部通过，各自报告/截图独立保留；
续关后不可保存路径和录制器未接入提示路径也通过。源码快照核对为105份
当前报告、73份历史快照、181个公共模块，无未记录源码；原始score.dat
摘要未变。目标保持active，下一步继续真实录制、stage数据组装与持久保存/回放。


## 实际录制、完整录像组装与浏览器持久保存（2026-11-15）

replay-recorder.mjs 恢复1a0字节录制owner的构造字段、6bfd0关卡初始化、
6b970输入变化记录和6c3a0封口。首次建立T6RP/010f头，记录profile、模式/
难度、默认NO NAME；每关分配原版0x9e33c容量，20字节关卡头保存初始seed、
pointTotal、Power低字节、残机/Bomb/道具chain和Miss低word。下一关初始化
把上一关score写到上一关头0..7。输入仅在低10位变化时追加12字节记录：
int32帧号、当前按键、上一帧按键；初始记录全零。active停用或owner+9封口
后不计时。封口追加当前帧的零输入及9999999哨兵，只执行一次。

th06nc-replay-recorder-native-verified.json执行原版构造字段/初始化/tick/
封口，64组角色/机体/难度/模式/SpellPr/1-2-3与Extra起始序列，共12,800
检查点。完整owner/header及已用stage字节比较，堆地址正规化为稳定身份。
malloc未使用填充在fixture内为零；分配器垃圾字节、任务注册、种子生产者
和实际游戏调度不在证明内。主机容量越界明确拒绝，不复现原版越界写入。

replay-assemble.mjs 恢复完整record-mode writer 6c420：封口、更新末关真实
score、构造120字节头（文件score字段来自displayScore）、日期/姓名、处理
落率及偏移1.12/2.34、stage偏移表和连续数据块；再执行原版codec。消耗
四个next16，依次生成seed(低7位+64)、byte19、byte16、byte17；不使用另一
个临时随机源。保留/释放recording由原版standalone参数决定，常规保存清
stage引用。返回已编码字节，不自行宣称文件已写入。

th06nc-replay-assemble-native-verified.json执行实际完整6c420、封口、RNG、
checksum和编码，72个角色/模式/关卡序列/保留标志/速度比例场景逐字节比较
交给文件服务的输出，并比较后置owner/header和RNGseed/count。日期、内存
服务、memcpy、任务移除和文件交付为边界，stack未初始化padding控制为零。
因此此证明不意味着任意原版堆/栈padding的字节等价或真实磁盘交付已验证。

实际游戏现于openStage初始化录制头，每个真正玩法tick之后记录输入；暂停、
GameOver和结果页不记录。进入下一关前封口，重开新建owner。保存使用当前
真实recording header代替先前仅供显示的两字段元数据，不制造占位stage。
种子从当前初始化前rng.seed捕获，调度/种子生产者与Native完整engine的
对应仍需进一步证明，不能仅凭文件能解码声称Native运行时完全等价。

runtimes/th06nc/game-save.mjs 使用IndexedDB th06nc-save-v1，replays按
replay/th6_01.rpy..th6_60.rpy存储完整原版格式ArrayBuffer，启动验证/解码
后提供列表头。仅在readwrite事务complete后更新内存列表与成功路径；abort/
error显示失败和重试，保留已组装字节。保存时冻结后续结果tick，提交成功
后继续原版白色淡出到标题。页面重载重新读库，损坏文件按原版头服务语义
不进入列表而保留诊断，不自动删除用户数据。与录像同事务存储前次姓名；
只登记成绩/取消录像时的姓名配置及score.dat持久化仍待接入。

浏览器--replay-list-save-request现为实际录制/保存/重载检查，不再是“录制
未接入”提示检查。自然未续关游戏结束后选槽16、编辑姓名并End，确认事务
提交与标题返回。读取真实已存字节，用Native已对照codec解码，检查关卡1
偏移120、seed0xbeef、profile/难度、初始零记录、真实输入变化、结束帧等于
冻结玩法帧及9999999哨兵。真实Page.reload后逐字节读回一致；所有数据来自
本次实际游戏，不是手工插入的录像样本。四机体分别保留独立报告与截图。

--replay-overwrite再加载一次真实已存文件，实际开始第二轮自然游戏，选
已有槽16，覆盖No后检查原字节未变，再重进选Yes、姓名改B、保存并重载，
验证仍只有一个槽、替换字节及前次姓名B完整恢复。此流程不注入HP/分数或
伪造槽位。预览服务器改为HTTP/1.1连接复用，避免大型ES模块图在反复启动
时耗尽系统网络缓冲；遇到的连接失败未记录为通过，修复服务器后补跑。

## 回放核心及玩法闭环（2026-11-15）

replay-playback.mjs 恢复6c1b0初始化、6ba40每帧输入和6b9f0对话任务返回值。
从首个存在的关卡恢复默认残机/Bomb，从所选stage恢复RNGseed/count0、
pointTotal、Power/残机/Bomb/chain和有符号Miss；跨关分数来自上一关头。
profile拆为角色/shot，非SpellPr恢复难度，Challenge恢复lifeProtection。
每帧按下一记录帧推进，保留当前输入高位、重建低10位与previous，清repeat/
repeatClock，递增clock。对话任务码6单独恢复，尚未把它错误映射为某按键。

th06nc-replay-playback-native-verified.json为16场景/2,440检查点，执行真实
初始化、输入和对话返回函数，覆盖四种header mode、普通/Extra起始、跨关
和缺失关卡，比较完整owner及输入/环境/RNG全局。解码文件是控制输入，
6bab0回放文字overlay初始化、完整任务调度、浏览器播放入口仍未包含。

th06nc-replay-world-verified.json进一步做主机玩法闭环：四机体有限残机的
真实StageWorld各2,000帧，自然敌机/子弹/道具/碰撞及两次按键Bomb，录实际
输入、组装/编码/解码后从stage header恢复初始状态，再消费记录输入运行
全新world。录制与回放各8,000帧、324个检查点比较完整player/enemy/effect/
bullet/laser/item/popup缓冲、关键计数及RNG均一致。未注入Boss/HP或人工
子弹。此项是主机round-trip证据，不能替代新的原版全world对照；不包含
HUD/STD/MSG/渲染/音频、菜单调度、跨关完成或浏览器回放UI。


保存异步边界另处理End+Escape组合：原版先完成写入再返回列表；网页在
IndexedDB提交后若owner已为12，重新加载头字段而不重置ANM/时钟，避免
仍显示旧空槽。已消耗的recording同时标记不可再次组装，防止从已释放的
stage生成文件。--replay-save-cancel-chord实际同时物理按下Z/Escape，验证
提交后仍在12、槽16已出现T6RP头、可取消到标题且刷新后字节一致。

最后核对日期时发现原版30c22c格式串是%D，即月/日/两位年；此前平台
适配器误用了年/月/日，现已修正。replay-date.mjs以原版格式为准，
th06nc-replay-date-native-verified.json直接调用UCRT strftime并核对exe
原始%D字串，72个年/月/日组合全部匹配。此前CPU检查中的26/11/15是受控
日期服务字节，不证明原版日历格式；旧浏览器日期截图亦不作该项证据。
当前浏览器检查独立断言实际本地日历按MM/DD/YY存入文件和读回的列表中。

修正日期后，四机体实际保存/重载路径再次通过；Marisa B另覆盖原文件
No取消/Yes改名覆盖以及End+Escape异步提交路径。已视觉复查覆盖确认页，
显示11/15/26。th06nc-replay-browser-files-native-verified.json将这批浏览器
实际生成的六份.rpy交给原版6b00b..6b0e0解码/校验，再规范化关卡指针并
逐字节与网页解码结果比较，全部通过。此项不是原版文件系统写入或整局
玩法证据；最后的已消耗录制提示文案修正后，该文件检查记录了当前源码，
先前浏览器报告保留实际运行时的源码快照，不人为刷新哈希。

### 标题回放入口的独立流程（尚未接入浏览器界面）

继续核对原版后确认：标题主菜单第4项（从0开始）进入owner状态15，
状态16枚举文件，17加载replay00.anm与select00d背景，18选择文件，20选择
关卡，26等待启动淡出。结果owner的状态8实际属于符卡成绩页，不是标题
回放界面；结果12是保存列表，不能拿来代替上述回放选择owner。

title-replay-launch.mjs恢复实际4d680启动函数：回放文件路径、机体、模式、
难度、首个记录关卡的残机/Bomb、选定起始关卡、30帧黑色淡出及owner26。
SpellPr通过受控符卡目录匹配原版ID，找不到时保持原状态并返回失败；目录
构建76b90为外部服务。标题关卡索引在此仍为从0开始，实际关卡初始化负责
后续转换。th06nc-title-replay-launch-native-verified.json执行真实原版
函数，864组比较返回值、启动全局、路径、音效队列、状态/时钟及完整fade
56字节，全部一致；不包含文件加载、菜单绘制或实际玩法。

title-replay-navigation.mjs恢复18的上下导航与15行翻页，以及20的上下
跳过未录制关卡。左右同时按时左优先，分页补齐后越界夹到最后文件；上下
先于翻页处理，40帧门限保持。th06nc-title-replay-navigation-native-
verified.json在真实原版48b45..48c48与48eef..48f90中执行4d1f0和音效队列，
6,560组完整title owner字节比较通过；不包含确认/取消、ANM公共尾部或绘制。

title-replay-stage-entry.mjs恢复48cf7..48e77：26个回放ANM的17号标签，
当前页选中行16号标签，记录文件选择后进入20、清空时钟/pulse，再读完整
录像并从缓存头选择首个非空关卡。th06nc-title-replay-stage-entry-native-
verified.json为72组完整owner比较，文件解码作为记录调用参数的外部服务，
其余实际原版指令/音效执行；ANM tick、公共尾部和实际回放仍未包含。

这三部分尚未改动生产TitleScene或接通浏览器回放入口。仍需完成回放资源
初始化、绘制、取消返回/公共尾部、实际Playback生命周期和对话任务调度。
当前源码审计108份报告快照仍匹配、84份历史快照保留，188个shared模块
均有当前快照覆盖；覆盖仅表示被报告记录，不扩大各报告的执行范围。

### 标题录像选择与实际浏览器回放接线

上述“尚未接入浏览器界面”是前一检查点的状态。现TitleScene已接通标题
Replay入口、空列表、文件列表18、关卡页20及启动淡出26，并在文件/关卡
选择间取消返回。IndexedDB已有录像按路径排序后压紧为实际文件行，标签
仍保留原槽号。选中关卡通过已验证的4d680语义传递到ReplayPlayback，
在Player/StageWorld构建前恢复header中的初始状态；播放时每帧使用录像
held/previous，正常物理游戏按键不覆盖录像。播放不创建录制器，也不进入
成绩登记/录像保存；自然GameOver返回关卡选择。回放暂停的返回选择和
重新播放分支已接线。整个标题任务的原版重建/退出时序尚未整体对照。

title-replay-layout.mjs恢复replay00的26个VM及difficulty显示VM。
title-replay-draw.mjs恢复55266..556a7的文件表头/行、选中行闪烁及高亮
字库标志、难度sprite、减速率、七关LastScore。draw-native报告为320场景，
使用真实ANM、实际原版文字缓存/UCRT格式化，比较完整ASCII owner与有序
难度绘制VM，并验证27个VM初始化。它不包含GPU像素或完整标题绘制。

公共更新已扩展15/16/17/18/19/20/26。title-owner-advance-native报告
现为744组、98,208次VM比较，包含新增回放状态对；该报告仍使用基础标题
资源，不把资源替换和回放背景整体纳入它的范围。

视觉复查发现两个实际缺口并修正：原版选中行使用asciis.anm而不只是
ascii.anm；回放背景select00d.dds是4096平方图集，不能直接铺满画布。
ascii-layout.mjs现按原版9700发布普通slot1/base0、高亮slot2/base0x77；
ascii-layout-native报告观察实际两次原版加载调用，ascii-text-native报告
也以真实双字库重新执行6场景/24次入队/60次绘制请求。字体已在标题、
结果和玩法bank中绑定，避免缺失高亮glyph时沿用旧sprite。

title-replay-background.mjs改用原版select00d五层ANM，初始化7583c、关闭
75ad0、后层75a50及标题前层557c6。background-native报告覆盖打开和关闭
两条各180帧的路径、1,800次有序绘制请求，比较完整VM状态；CPU检查不
执行GPU。截图已视觉复查，背景角色/边框及高亮文字显示正常。游戏纹理
导出清单现68项/273,050,524字节，新增replay00/select00d/asciis均核对
已有独立原版DDS哈希。

浏览器--replay-playback为四机体分别独立运行：先访问空列表，确认空槽
不能开始且可取消回标题，再进行真实有限残机玩法、实际输入Bomb、自然
未续关GameOver、结果保存完整.rpy并刷新页面。由真实标题按键进入压紧
文件列表、选择录制关卡、上下跳过空关、取消回文件页再重入，最终启动
播放。播放期间传入1023的相反实时游戏mask，确认由文件输入接管。
四份game-replay-playback-*-browser报告各比较11个检查点（779..2190），
合计44点，覆盖完整player/enemy/effect/bullet/laser/item/popup缓冲、
score/displayScore、库存/Power/Miss/Graze/Point、RNG种子/计数及Bomb数。
每局2260帧后自然结束返回关卡页，并另验回放暂停返回选择。

完整缓冲包含原版绘制保留的ANM坐标；浏览器原录制/回放检查因此重现
同一绘制帧序列，而不是把不同绘制频率留下的缓存当作玩法漂移。只读
gameplayDigest记录各池及合并哈希，手动检查模式记录绘制帧，不改录像
格式或原游戏数据。这是网页闭环证据，不是新的一整局原版任务调度对照；
MSG/STD/HUD完整owner、回放overlay/对话加速调度、多关/全模式、完整音频
与原版GPU像素仍未由这些检查证明。

四份本批新录像连同先前六份保存/覆盖产物，合计十份，又交给实际原版
6b00b解码/校验并逐字节比较，均通过（browser-files-native报告）。
当前审计114份快照匹配、85份历史快照保留，192个shared模块均有当前
快照覆盖。原游戏score.dat仍保持44805e26...2609441，整作目标继续进行。

### 回放对话任务的链头重启语义

原版6b9f0不是“跳过本次对话tick”：当active、MSG+36b0非负、MSG+3900
指示为真且回放owner帧除3余数不为2时，它返回任务码6。实际更新调度器
3be80收到6会回到全局更新链头；6ba40回放输入在priority5，对话判断任务
在priority16，所以此前的输入/自机/敌机/效果/弹幕/消息等更新会再次执行。
不能把它替换为一个输入位，也不能只额外推进MessageState。

新增task-update-chain.mjs恢复3be80调度：2重复当前任务，6重新从链头
执行，0先取得下一节点再删除/析构，3停止返回0，4/5设置外部状态1/2并
返回1；正常链尾和停止路径各只消费一次音效队列。执行计数在6重启时
保留。调用上限是宿主避免无穷循环的显式保护，不声称原版有此检查。
task-update-chain-native报告运行真实3be80及126e0删除，72组比较完整
调用/析构/音效轨迹、节点链接、返回值和状态；堆归属/free为受控服务。

replay-dialogue-chain-native报告进一步在同一真实原版链中运行6ba40与
6b9f0，窗口化的MSG字段/指示位是受控世界回调。四场景合计400次外层
更新，逐次比较回放输入帧、输入全局、世界回调次数与音效flush次数一致。
该检查验证“链头重启”的实际组合，而不是仅分别检查两个返回值函数；
但实际MSG程序、所有游戏任务注册/优先级、绘制及浏览器调度仍未包含。
生产浏览器尚未使用新调度器，继续接线前需保留上述范围区别。

### 实际 MSG 与生产浏览器的回放重启接线

前述“尚未使用新调度器”是前一检查点。现replay-frame.mjs使用已对照的
runUpdateChain，在priority16对话判断前重复完整的回放采样/世界更新
回调。game.mjs将原单次tick拆为外层分派与tickOnce，播放且处于game
阶段时使用新协调器；场景已转移或播放对象被替换就停止重启。每个逻辑
更新仍推进输入owner、StageWorld、MSG和计分。普通录制/非回放菜单保留
单次更新路径。回放世界的音效队列现在由外层链结束时统一消费一次，
避免同一显示更新中的多个逻辑更新分别清空队列。

replay-message-verified为真实MSG程序的宿主组合检查：stage1..6、两角色、
passive/skip/advance三种实际输入序列共36场景。基准逐逻辑帧录制输入，
组装/编码/解码后用ReplayPlayback恢复，再经新协调器加速执行。每次逻辑
更新都比较完整MSG缓冲及文字/音乐服务请求；80,016次逻辑更新逐步一致，
对应28,684次外层更新及51,332次链头重启，每次外层只flush一次音效。
此项是宿主组合证据，不能冒充新的整链原版MSG执行；原版链头重启与
输入/对话函数组合已有前述400次原版检查，单次MSG另有真实原版36场景
80,016帧检查。实际所有应用任务的注册顺序及音频平台仍未整体证明。

四机体--replay-playback再次运行实际保存/刷新/播放路径，原44个完整
actor/counter/RNG检查点、自然结束及暂停返回均通过。新协调器未改变
这些短录像的逐点结果；十份实际保存/覆盖文件再次通过真实原版解码。

另增replay-natural-dialogue-*-browser检查两角色的自然Boss对话路径。
这是明确的受控录像fixture：Challenge头、Power128、初始两残机、种子beef，
50,000帧持有射击；写入隔离浏览器IndexedDB后，通过真实标题选择文件/关卡
启动。此后没有写自机、Boss、HP或MSG owner，也没有直接打开对话，而由
原始stage1 ECL/玩法自然到达Boss并开启、完成MSG。Reimu A在6,720次外层
更新达到逻辑9,803帧，Marisa B在6,240次外层达到8,333帧；对话窗口中观察到
逻辑增量大于请求的外层帧数，退出后回到普通增量。截图已视觉复查。
该fixture不是玩家真实录制的Challenge通关证据，也不是普通有限残机的
长局验收；它验证生产协调器的自然触发/退出，完整模式与跨关仍未完成。

当前源码审计119份报告匹配、85份历史快照保留，194个shared模块均有
当前快照覆盖。回放overlay显示、完整应用任务顺序、原版返回/重建生命周期、
成绩/配置持久化、全部模式与完整通关等仍继续推进，整作尚未标记完成。

### 普通回放状态提示

replay-indicator.mjs恢复6bab0的普通提示初始化与6bf52绘制分支。提示VM
直接使用Playback 1a0字节owner的+78视图，绑定原text.anm sprite73f，
EXE_REPLAY_INDICATOR本地化文字使用15号字库和ffffff/0/10101/40202
颜色。保持原版crop指标、+19c宽度副本、屏幕坐标(4,428,0)，初始化
无符号显示计数+198为0。绘制的120次往返闪烁由128到255，按显示调用
递增而非按逻辑更新递增；停止采样的暂停画面仍能继续闪烁。

replay-indicator-native报告执行真实6bab0初始化和6bc30普通绘制路径，
160组比较完整1a0 owner、camera及有序绘制VM请求。包含字体缓存有/无、
已有crop/位置/颜色状态下重初始化、播放/全局开关，以及0、59/60、119/120、
INT_MAX、UINT_MAX等显示计数边界。字典查找与字体纹理发布是受控服务，
不将它解释为原版字形/GPU像素对照。0x8000诊断统计分支仍未移植。

生产openStage在Player/MSG资源绑定后发布提示文本；渲染位于普通世界/
暂停菜单之后、全屏淡出之前。game-playback四机体实际回归通过：crop宽度
非零、位置精确(4,428,0)、显示计数递增；暂停时advance(0)保持世界帧而
使提示计数加一。四组44个actor/counter/RNG检查点仍一致。暂停与自然
对话截图已视觉复查，左下角显示原本地化《REPLAY》；两角色自然Boss对话
再次通过，外层/逻辑帧计数保持前次6,720/9,803与6,240/8,333。

十份实际保存/覆盖录像再次通过原版解码，原score.dat哈希仍不变。当前
120份报告快照匹配、85份历史快照保留，195个shared模块有当前快照覆盖。
普通提示已接通，但诊断覆盖层、完整任务注册顺序/生命周期、成绩/配置
持久化及其他模式、通关/结尾等仍未完成；整作目标继续进行。

### 普通成绩提交与失败重试

ScoreSave组合已经原版对照的HSCR表与score.dat容器，在Result退出事件时
提交浏览器IndexedDB，包含选择“不保存录像”的正常出口。Result使用同一
成绩表，后续开局读取对应普通模式/难度/机体最高分；名称与完整成绩字节在
同一事务提交，刷新页面后恢复。非HSCR块保持原始字节，尚未替代完整原版
CLRD/CATK/MUSC等owner及其规范化写入。原文件只读，不复制到浏览器资产。

score-save宿主检查覆盖60组表、180条实际记录、uint64上界、低分不入榜和
同分重载顺序。原版加载时同分插在已有项前，因此同分项重载会反转，检查
保留这一行为。原score.dat的51,600字节往返完全一致；追加浏览器HSCR后
其他块逐字节保留，原文件SHA256仍为44805e26…609441。

六条实际浏览器路径通过：四机体保存/刷新/回放、不保存录像时提交成绩、
成绩事务失败后重试。每条都检查实际HSCR名称/分数/分组及刷新后的完整
字节一致。score-failure路径实际中止事务，显示失败界面后通过真实鼠标
点击重试，成功后才回标题。六份实际68字节score.dat均通过原版6ca60解码
及74a3a编码的完整字节对照，证据为score-browser-files-native报告；这不是
完整原版规范化成绩写入器或原版文件系统的对照。

Reimu A浏览器报告另含隔离数据库的八项后端检查：初始默认、名称提交、
原生格式成绩重载、成绩事务中止时保留旧字节/名称、保留工作成绩以重试、
损坏成绩先精确保留备份再替换，以及录像事务中止/重试。修复IndexedDB
error先于abort且transaction.error为空时拒绝null的问题；错误现在具有
可显示的原因。只有事务完成后更新“已提交”的内存副本。

原版Result析构74470通过dirty字节决定写入；当前浏览器在对应正常退出
事件提交，完整dirty/stats owner与任务生命周期仍待恢复。新增score-header
原语对照真实744c2..74558，1,024组比较完整20字节和随机数seed/count，
包含计数回绕和非零分配填充。它按原版消耗两次next16、写入密钥/版本及
记录偏移，保留未赋值字节；末尾长度/加密在后续写入器完成。该原语尚未
接入浏览器全局随机数生命周期，不能将目前固定/保留的容器头声称为原版
写入过程等价。完整模式、通关/结尾、配置及其他剩余项仍在目标范围内。

### 规范化成绩写入器的连续原版对照

score-stat-chunks恢复747a4..74a3a：无条件写四条CLRD，筛选134个384字节
CATK槽并重写索引，筛选96个24字节槽的+12非零uint64字段，最后写MUSC。
24字节槽的玩法含义尚未确认，接口保留optionalRecords名称。检查使用32组
受控原始owner，比较5,230条输出记录和所有输入owner被原版修改后的完整
字节，覆盖空/满/稀疏选择、uint64最高位及填充保留。

score-canonical组合文件头、TH6K、60组HSCR表和上述统计块。新检查连续
执行原版744c2..74aa2，不在各原语边界截断或替换代码；24组场景的完整
加密文件合计1,149,024字节全部一致，同时比较TH6K/统计全局修改和共享
RNG状态。排名链由受控内存构造，默认/加载规则已有独立原版对照；此检查
不声明排名节点修改、统计输入来源、dirty析构门控或文件系统行为等价。

规范化写入器目前是明确输入的原语，尚未接入GameSave。生产仍使用前述
保留非HSCR原始块的组合，需先恢复统计owner加载与玩法更新及全局生命周期，
才能替换生产写入路径。现源码审计124份报告匹配、87份历史快照保留，199个
shared模块均有当前快照覆盖；完整游戏验收仍未完成，持续目标保持进行中。

### 统计数据默认值、加载及共享全局布局

score-stat-load恢复CATK加载6cc40、PSCR加载6ce20、Result的CLRD初始化/
加载74348..743f4、标题CATK初始化56042..560be和启动MUSC加载45776..457cd。
41组场景比较205份完整目标内存，包含只读原score.dat、空输入、重复项、
错误版本、越界项提前终止、已初始化/不完整的CATK首槽门控与数值上限。
CATK加载将+3c/+3e的uint16限制为9,999，将+e0..17f的40个uint32限制为
999,999,999；缺失槽保持旧值。标题仅在第一槽没有CATK标记时重建全部
134槽并读取文件。MUSC取最后一条匹配版本记录，不额外限制数据字段。

此前暂称optionalRecords的24字节记录已确认为PSCR。原版初始化4机体×
6关×4难度共96槽，却接受character<4、difficulty<5、stage<7，索引仍为
((character*6+stage)*4+difficulty)。因此存在槽别名和最多101槽的写入
范围；这些行为在完整内存对照中保留。并未将超出96槽的记录简单丢弃。

score-stats使用原全局4f1e8c..4ff164的单个53,976字节缓冲区及精确视图。
PSCR接受的写入范围与CATK首槽有重叠，会改变随后“首槽已初始化”的判断。
组合检查按真实启动音乐加载与55f9a..560be标题加载顺序连续执行原版，
16组比较启动后和标题后的整个全局范围，共32份完整内存一致；包含刻意
触发这一重叠的受控记录、零/随机/部分初始化状态及只读原文件。memset是
受控服务，未替换PSCR/CATK加载或它们之间的调用顺序。

这些统计加载owner尚未接入生产GameSave和玩法更新，Result状态9/17的
特殊加载门控、练习成绩更新、通关解锁及音乐更新/保存生命周期仍待恢复。
浏览器仍沿用已通过实际回归的HSCR保存路径。当前126份报告源码匹配、
87份历史快照保留，201个shared模块有当前快照覆盖；整作目标保持进行中。

### Result统计门控、练习最佳成绩与音乐解锁更新

ScoreStats.loadResult恢复7430c..74457：状态9和17跳过文件中的CATK/CLRD/
PSCR加载，其他状态按CATK、CLRD、PSCR顺序加载。状态17直接比较现有PSCR
最佳分与本次uint64分数，仅本次分数更高时替换；索引使用机体、当前关卡
减一及难度。288组组合运行连续原版代码，覆盖四机体、六关、四难度、
三种状态、空输入/只读原存档及无符号最高位边界，整个共享全局范围一致。
此处是数据加载/更新原语，尚未宣称练习模式入口或Result完整生命周期完成。

music-unlock恢复播放请求7bc80..7bcf4的MUSC更新前缀。owner+42c为9、
全局4f278c非零或路径为空时跳过；否则按原版data/bgm/th06_%d解析，曲号
1..32设置MUSC+12对应位。扩展名不是格式匹配条件，数值后缀亦可接受，
bgm2路径不匹配这个前缀。504组对照执行原版前缀及原版扫描包装函数，
其CRT导入使用实际Windows UCRT __stdio_common_vsscanf；比较整个MUSC。
包含空值、大小写、空白/符号、数值前缀、嵌入NUL、超界及超大整数。实测
UCRT通过饱和signed64累加器后写入%d的低32位，已据此修正直接回绕的假设。
该证据不包含请求后续缓存、音频解码/混音或浏览器保存接线。

新增Result方法后标题共享布局检查再次通过。当前128份报告源码匹配，
87份历史快照保留，202个shared模块有当前快照覆盖。仍需将这些统计owner
和更新服务接入生产玩法/保存生命周期，并继续全部模式、结尾及其他整作
验收；目标保持进行中。

### 规范化写入器与统计加载接入生产保存

前述“尚未接入GameSave”对应上一检查点。现在GameSave持有独立于排名表
的ScoreStats共享缓冲区：打开数据库时恢复启动MUSC，构造标题时按原顺序
加载CLRD/PSCR/CATK，正常Result状态9接入其加载门控。writeScores使用
encodeCanonicalScore写入TH6K、HSCR和规范化统计块，正常Result退出传入
实际environment.rng，原文件头初始化消耗其中两次next16。隔离后端检查
未提供玩法环境时使用独立受控RNG；不将它声明为原版启动种子来源。

浏览器标题/关卡/MSG的实际音乐播放请求先更新MUSC，回放播放标志阻止
这项更新。当前已接入口的普通菜单使用ownerState0，音乐室owner尚未恢复。
即使平台音频层缓存了同一曲目，也先执行解锁更新，保持原请求前缀顺序。

四机体录像保存/刷新/回放、普通不保存录像出口、保存失败后真实点击重试
六条浏览器路径通过。检查实际成绩中的四条CLRD、134条CATK、HSCR姓名/
分数及MUSC；标题与stage1曲目的位均置位，保存后刷新完整文件和解锁掩码
一致。普通单条HSCR文件为51,636字节，无HSCR的恢复文件为51,600字节。
后端原有八项事务中止/重试/损坏备份检查继续通过。六份实际成绩再次通过
原版6ca60解码与74a3a编码的完整字节对照，来源快照包含新的写入及加载图。

原score.dat始终只读，哈希仍为44805e26…609441。旧ScoreSave.snapshot
保留非HSCR的宿主组合仍供独立格式检查使用，生产提交已改为原版规范化
块顺序；未知块不再由这个生产写入器保留，符合已恢复的原版写入路径。
这并不代表完整统计行为完成：符卡/通关等玩法生产者尚待与存储owner接通，
完整dirty析构门控、全局字段绑定/任务顺序、启动随机数来源、分配器未赋值
头部填充字节及所有退出/其他模式保存路径仍未整体证明。整作目标继续进行。

### 符卡玩法生产者与CATK存储共享

createSpellRecord新增显式copy:false视图方式，默认复制行为保留。ScoreStats
为134个CATK槽创建固定记录对象，字段/数组直接引用同一共享缓冲区；标题
重新加载仍写入原缓冲区，不使这些视图失效。生产StageWorld的spellState
使用该记录Map，原有93/94操作码生产者因此直接修改随后写入成绩的字节。
同一次玩法跨关保留局内captures/extraCaptures；重新开局使用新的局内状态，
持久记录仍由独立ScoreStats持有。

spell-begin-native重新执行576组完整记录对照，交替使用复制记录与有非零
byteOffset的共享视图；符卡结束的896组原版对照也继续通过。新增宿主
spell-persistence检查让134个ID各经历两轮开始/结束、练习计数及规范化
保存/启动与标题重载，268组检查尝试/收取次数、键名、历史及练习数组；
每次回放标志开启时比较整个CATK池不变，重载后第二轮计数继续累计。
这是生产者/写入器组合证据，不冒充自然ECL或完整浏览器关卡验收。

浏览器隔离数据库后端检查扩展为十项：通过实际beginSpell/endSpell服务
更新共享记录，提交后新连接恢复两项计数；第二轮更新的事务中止时，磁盘
仍保留第一轮计数，工作内存保留第二轮，重试提交后刷新恢复累计值。测试
使用受控符卡请求，没有注入主游戏的Boss/玩家/HP或宣称自然收取成功。

回放浏览器检查同时修复刷新等待竞态：Page.reload后必须看到新的
performance.timeOrigin且新文档中的游戏初始化完成，避免误读旧页面的
title状态后立即操作已销毁的上下文。其余输入、逐点actor/RNG检查及保存
验证保持原义。剩余通关/解锁生产者、自然普通符卡到保存的浏览器验收、
完整模式与生命周期继续推进，整作目标尚未完成。

上述接线后的六条浏览器路径均完成，六份实际成绩文件再次通过原版编解码。
当前130份报告源码匹配、86份历史快照保留，202个shared模块有当前快照
覆盖；原score.dat哈希未变。

### CLRD进度、通关标记与Extra选择解锁

cleared-progress分别恢复3af27..3afe5关卡初始化前缀和2c9ef..2caa6结尾
初始化中的CLRD写入，4,800组比较完整96字节、关卡递增、已有通关标志及
受限标志。回放和符卡练习跳过进度写入，普通关卡练习并非该分支的跳过
条件；这一区别通过实际原版执行确认。进度前缀总会递增关卡，保护模式、
无续关且死亡次数<=5时更新第一表，第二表更新已完成关卡进度。结尾分支
在无续关且（非保护模式或死亡次数<=5）时将第一表置99，第二表总会置99。
两个分支的条件不同，未把它们合并成一个资格判断。

生产MSG跨关请求现先更新CLRD，再由openStage初始化下一关。结尾置99的
原语尚未接入实际结尾owner/提交生命周期，不能用当前占位结束界面冒充
完整通关和自然解锁。新增cleared-persistence宿主组合240组覆盖全部机体/
难度及保护、死亡、续关条件，经规范化文件、启动/标题重载后完整CLRD
一致，重复结算标志及解锁结果亦比较；它使用受控调用，不是自然通关证据。

cleared-unlocks恢复4818b全局Extra判断和4b958逐射击判断：只有四机体第一
表难度1..3的精确99有效。4,096种十二位组合全部运行原版，合计20,480个
比较块；Easy/Extra/第二表即使全为99也不参与。TitleScene现向难度、角色
和射击子流程传入实际解锁数据，标题从GameSave的CLRD恢复它们。

Reimu A浏览器回归新增cleared-unlocks受控存档分支：初始Extra锁定时
真实按下跳过到下一项；用实际通关标记原语生成灵梦B难度1的fixture，
经真实IndexedDB提交和页面刷新后，Extra可选、锁定角色不能选、只有B
射击可选。截图已视觉复查，Extra背景与B射击高亮正确。测试结束删除该
fixture后刷新，再执行原普通录像/成绩流程；不把这一fixture当作玩家
自然通关记录，也未宣称Extra游戏入口/关卡与结尾全部完成。

这一接线后的六条浏览器回归全部通过，六份实际成绩文件再次通过原版
编解码。当前133份报告源码匹配、86份历史快照保留，204个shared模块有
当前快照覆盖。原score.dat哈希未变。2c8d0初始化实际加载th06ED.dat中的
staff01/02/03.anm；后续须沿真实结尾/Staff入口恢复提交时机，不能仅在
占位结束按钮上调用通关标记来替代该生命周期。

### 剧情/Staff初始化与原始结尾脚本

2b959把2c8d0注册为同一结尾owner的初始化回调，更新回调为2bac0。
2c8d0先载入th06ED.dat和staff01/02/03.anm，再写CLRD、选择剧情.end，
并非先单独启动Staff场景再跳过剧情。ending-init恢复其2caa6..2ceaa
脚本选择与数据初始化：符合好结局条件时按机体选end00/01/10/11；Easy
或受限时选end00b/10b。加载成功写入脚本指针、速度和双时钟，释放旧脚本，
顺序请求结局/难度/保护模式或零死亡成就。加载失败返回-1、保留未赋值字段，
不继续请求后续成就。原版两角色坏结局均请求Achievement13，保持实测结果。

ending-init-native运行真实完整该段并返回，共960组，比较整个0x1280
owner（仅脚本指针归一化）、返回值及加载/释放/成就/提交/错误的有序请求。
覆盖机体/射击、五难度、受限标志、保护、死亡、已有脚本、加载失败；还包含
原版不选择脚本的第三角色字节分支。文件加载和成就接口为受控服务，尚不
包含资源/CLRD前缀、实际脚本更新或完整结尾生命周期。

ending-assets从只读原th06ED.dat提取六份剧情.end与staff00.end，写入
独立浏览器资产目录，并记录完整档案与七份文件SHA256。它使用已独立原版
对照的PKGL读取层，本报告不单独声明剧情执行或像素等价。脚本包含NUL分隔
参数与本地化键；不能按普通逐行文本或已有ECL/MSG格式执行。

ending-stream恢复2b6e0整数读取：当前token经atoi转换后越过终止NUL及
后续连续NUL，停在下一非零字节。1,018组执行原版helper及实际Windows
UCRT atoi，比较完整owner、返回整数、游标与未修改的脚本字节，覆盖七份
原始脚本token位置及空白/符号/后缀/溢出。此处atoi饱和signed32，与音乐
scanf先饱和signed64再存低32位不同，未复用后者的转换规则。测试追加
显式哨兵限定有效内存，不把截断文件的原版越界访问当作已验证行为。

已将原版分派表与七脚本行首命令对应写入tools/tmp/th06nc-ending-command-map.json，
共15种实际命令：2/3/F/M/R/V/a/b/c/m/r/s/v/w/z。它只是下一步定位依据，
并非这些命令已执行的证据。完整命令分派、文本/背景/Staff绘制、脚本更新
时序及其生产场景接线仍待恢复；本轮新增原语尚未替换浏览器占位结尾。
当前136份报告源码匹配、86份历史快照保留，206个shared模块有当前快照
覆盖，整作目标保持进行中。

### 结尾命令分派与脚本替换

ending-command恢复七份脚本实际用到的15种@命令，另包含原表中的0/1
淡出命令：a请求Staff ANM脚本/精灵，b加载背景，m/M播放/渐退音乐，s/c
更新速度/颜色，0..3设置淡入淡出模式与时长，v/V设置滚动位置/速度，
r/w设置两组等待计数，R清除16个VM脚本号，F切换脚本并刷新跳过资格，z
结束任务。函数包含相应命令后的CR/LF跳过，保留r/w让出更新与其他命令
继续解释的区别。F使用切换后的脚本和基址推进游标，未继续读取旧脚本。

ending-command-native直接执行原版2be75命令分派及各分支/尾部行推进，
770组比较完整0x1280 owner、游标、继续/让出/结束结果及有序服务请求。
覆盖七脚本的全部实际命令位置、背景/切换失败、零分母、负数/整数上限、
CRLF以及逐个CLRD资格位置。背景加载返回0才表示成功，已据原版分支校正。
F检查四机体两表中的难度0..3精确99，保留已有124c标志，不包含Extra列；
测试额外覆盖完全未通关及只在Extra列置99的情况。

此检查中ANM、背景、音乐、脚本切换是明确的受控服务；真实整数helper及
Windows UCRT atoi仍执行。其F切换stub明确将同一fixture脚本重绕，不将
它说成完整原版加载/缓存或跨文件生命周期对照。replaceEndingScript另
恢复完整2b7a0，原ending-init对照扩展为1,024组（原初始化960组加64组
替换），比较加载失败保留旧游标/时钟、成功重置及旧脚本释放顺序。

上述命令尚未接入外层完整2bac0更新：文本本地化/队列、等待/加速时序、
真实ANM与背景绘制及场景任务生命周期仍待恢复，因此生产占位结尾暂未
替换。原存档未改动，整作目标保持进行中。

### 结尾完整更新循环与绘制请求

前述“尚未接入外层更新”是上一检查点。ending-update现恢复2bac0循环：
126c/1238与1264/123c两组等待门控、确认键新按下跳过、允许跳过标志与
按住8位键时的五次逻辑更新上限、文本取出/发布时间、滚动及16个VM推进。
更新内部保留命令连续执行、文本先入队后逐行出队和r/w让出执行的区别。
保护模式下两个坏结局文本键04替换为05；字典缺失回退到键名，队列保留
中间空行，不因末尾换行多出一条空行。原deque分配布局由宿主数组表示。

ending-update-native执行真实完整原版2bac0。七份原始剧情/Staff脚本及
一份多行/空行受控脚本，各运行普通、周期确认与按住加速三模式，共24
场景、266,162次更新，逐次比较整个0x1280 owner的SHA256，并比较最终
队列及全部有序ANM/文字/背景/音乐/加载/释放请求。真实整数helper与F
脚本替换函数也在这条原版路径中执行；字典查找/行拆分、deque/string
存储、ANM/字体、背景和音频仍是明确受控服务，不将这些服务解释成原版
C++字符串库、字形/GPU/混音等价。

ending-draw恢复完整2c600绘制回调，720组比较完整owner与绘制请求，包含
主/备用背景句柄选择、1920宽度阈值对应1080/2160源高度、滚动截断坐标、
16个VM请求、四种黑白淡入淡出及计数边界。NaN/Inf坐标按原cvttss2si
返回INT_MIN。淡入淡出时钟在绘制时推进，未挪到update；整数乘255先按
32位溢出再有符号除法，保留该计算顺序。纹理查询和绘制传输是受控服务，
不声明实际像素一致。

ending-update-draw-native在上述24场景中，每次非终止更新后明确调用一次
真实原版绘制回调，再比较整个owner及绘制请求，同样266,162次更新通过。
此组合使用无背景句柄以隔离时钟/VM/淡入淡出；背景请求另由720组绘制检查
覆盖。该协调器未运行原版应用任务注册/析构链，不能代替真实结尾场景入口
与返回/提交生命周期验收。下一步仍需接上原ANM、背景、字体和浏览器场景。

### 浏览器普通结尾、Staff与Result提交接线

生产gameState10入口现创建EndingScene，准备实际Staff/text ANM、四种结尾
文字配色图集、所选剧情与Staff背景及17/18音乐。GameAssets按当前zh-CN
显示配置使用中文Staff纹理；当前背景走标准分辨率primary路径，4K自动
选择与完整原版缓存/加载所有权仍未整体证明。GameRenderer依据已恢复的
绘制请求使用源图偏移/高度滚动背景、绘制真实VM与淡入淡出。结尾键盘
确认使用256位、Ctrl使用8位；手动验收的每次结尾更新都伴随绘制，让
显示时钟按已对照顺序推进。

结尾返回0后卸载Staff ANM，准备不透明白色全局遮罩，转入Result姓名/
总结/录像选择流程，成绩仍在Result实际退出时提交。原版应用调度原语
ending-result-handoff-native运行79d7a分发表到Result注册，9组比较状态
10到请求7的分支、dirty=1、普通状态9/关卡练习状态17，以及更新/绘制
优先级13/16。构造器/分配/注册是受控服务；Native dirty位、任务删除、
缓存释放及全局所有权的完整浏览器等价仍待恢复，不能用此分支证明整链。

新增只在手动普通玩法可用的previewEnding调试入口，受控地把当前玩法
交给stage6结尾；没有把这个入口放进玩家菜单或把它当作自然通关。浏览器
验收先用实际标题选角色/射击/难度并运行600帧普通玩法，再经该入口执行
实际剧情/Staff脚本，逐次绘制、确认跳过、进入Result、选择不保存录像、
提交CLRD并刷新页面验证完整文件。Easy也使用这个明确的stage6受控fixture，
因此不声称验证了自然Easy在第五关结束的入口。

六份剧情文件的独立浏览器检查均通过：

| 剧情 | 显示更新数 | 发布文字行 | 成绩文件 |
| --- | ---: | ---: | ---: |
| end00 | 3,390 | 32 | 51,600字节 |
| end01 | 3,102 | 30 | 51,600字节 |
| end10 | 3,366 | 36 | 51,600字节 |
| end11 | 3,390 | 38 | 51,600字节 |
| end00b | 2,406 | 9 | 51,600字节 |
| end10b | 2,334 | 8 | 51,600字节 |

截图复查可见剧情背景、中文文本与Staff署名；GL无错误。fixture中的短局
分数不够入榜，故无新增HSCR，仍验证两张CLRD相应难度均为99以及刷新后
文件字节一致。四机体普通录像回放、Extra受控解锁、后端十项事务检查、
保存失败重试和不保存录像六条原回归再次通过。十二份实际浏览器成绩均
通过原版解码/重新编码，原score.dat哈希仍为44805e26…609441。

当前149份报告源码匹配、87份历史快照保留，211个shared模块有当前快照
覆盖。自然完整通关、全部模式/难度验收、原版完整任务/dirty/析构/缓存、
成就投递及字形/GPU/音频等价仍未完成，整作目标保持进行中。

### Extra真实入口与自然零残机路径验收

核对确认title-mode-update已有原版state14的stageIndex=6，TitleScene交接
时加一，确实启动stage7/difficulty4；无需再改写为另一条路由。新增Extra
浏览器检查仅预置对应机体普通难度1的CLRD解锁fixture，再经实际标题、
角色、射击、模式确认进入Extra。此后不写自机、HP、残机、敌机或Boss数据，
运行原第七关ECL/STD与玩法，验证300帧画面、暂停冻结与恢复，持有射击
自然耗尽残机后进入Result；Extra不提供续关，continuesUsed保持0。

四机体分别在玩法帧1,129/1,130/1,137/1,121到达自然零残机路径，随后实际
Result、总结、选择不保存录像、提交成绩与刷新恢复均通过。截图已复查：
Extra边框/背景与玩家可见，Result显示Extra成绩。实际HSCR是对应机体、
difficulty4、mode0、stage7的非零成绩；预置普通解锁标记保留，Extra列
没有伪造通关99。四份成绩各51,636字节，包含真正玩法产生的一条HSCR。

这证明早期Extra玩法及自然失败退出，不证明自然解锁、Boss/隐藏阶段或
Extra通关。还发现生产gameState7只在回放返回时被处理，普通Extra的
MSG11实际通关请求7仍会落到未接入分支。原应用previousState2/request7
分发表指向79e63，先等待/推进白色遮罩，再删除玩法任务、创建Result；
下一步须恢复这条通关交接，不能把本轮自然零残机入口当作过关入口替代。

十六份实际浏览器成绩重新通过原版解码与编码，额外检查四份Extra HSCR
分组/关卡。当前153份报告源码匹配、87份历史快照保留，211个shared模块
有当前快照覆盖；原score.dat哈希未变，整作目标继续进行。

### 结尾真实ANM适配与场景组合

ending-animations把16个VM视图直接绑定到0x1280 owner中，区分2760普通
脚本设置的坐标清零/字体初始化与2a20文字缓存脚本设置的字段保留，使用
真实Staff/text ANM程序，2980精灵绑定和69b0更新。Native检查覆盖全部10
个Staff脚本及8个文字脚本、三种已有状态，共54个绑定场景与6,480次更新，
比较完整VM字节；另执行实际精灵重绑定。文字缓存指针在该检查中明确指向
原text程序，实际缓存生产者/字体发布/GPU仍不在此证据内。资源文件也加入
源码快照，避免资源变化后仍错误判定报告当前有效。

EndingScene组合已恢复的CLRD结算、剧情选择、脚本替换、命令、更新、绘制
及ANM视图。主机检查使用七份实际脚本、原Staff/text程序和真实zh-CN
本地化，16组角色/射击/好坏结局/保护条件在334,134次更新后均到达脚本
结束和Staff音乐；请求有中文字行且存在可绘制VM。完整资源/本地化文件
哈希随报告保存。文字发布、背景和音频接口仍为受控回调，此检查不是实际
浏览器画面、原版完整场景或自然通关/返回/提交验收。

ending-textures从原归档准备42份剧情/Staff背景与动画纹理，包括常规、
4K和中文Staff变体，共277,241,416字节。每份都匹配既有独立原版DDS
哈希；使用单独ending-manifest，不改写既有游戏纹理清单。纹理的实际
高分辨率/语言选择、背景加载器、浏览器绘制及字体图集注册仍需接线。

另外确认2ceb0析构卸载三个Staff ANM、释放背景/文本与脚本/绘制任务，
设置不透明白色全局遮罩和gameState7；该处没有直接写成绩文件。下一步必须沿
原应用gameState7的后续数据对象/Result入口恢复最终提交，不能在脚本z
返回0时直接写档并回标题。生产占位结尾仍保留，整作目标继续进行。


### Extra 结束请求至 Result 的黑色渐隐交接（2026-11-15）

`gameplay-result-handoff.mjs` 接入原版应用上一状态 2 / 请求状态 7 分支（`79e63..79f2f`、`7a243`）。全局 fade 不存在或仍在其他非完成状态时等待；mode 0 请求黑色 30 帧 fade-out；mode 2 才删除玩法任务并注册 Result。普通 Result 初始 state 9，stage practice 为 17，dirty 字节为 1，更新／绘制优先级 13／16。浏览器当前接入普通 Result；stage practice Result owner 仍未实现。结尾路径也补齐 dirty=1。

`th06nc-gameplay-result-handoff-native-verified.json` 对照实际应用分支 280 组：完整 56 字节 fade、alpha 边界、空对象、各 mode、practice 与注册失败返回值，以及有序任务删除／Result 注册请求。任务调度、Result 构造和分配服务被控制，不能据此声称完整任务图或像素等价。

四个 `th06nc-extra-*-clear-handoff-browser-verified.json` 从真实标题入口进入 Extra，实际游玩、暂停／恢复后，通过明确的调试夹具执行真实 MSG11 结束生产者。黑色渐隐中世界继续更新 30 帧，随后停止玩法更新并进入 Result，检查 dirty=1、姓名／总结／不保存录像、Extra HSCR 写入和重载字节一致。四个自机均在 frame 884 停止玩法更新，成绩文件均 51636 字节。该夹具没有修改分数、残机或 Boss HP；它主动发出结束请求，**不构成自然击破 Extra 或隐藏阶段的验收**。该分支没有人为写 Extra CLRD=99。


本轮回归还通过灵梦 A 的 Extra 自然零残机路径（1129 帧）、`end00`／Staff／Result 路径（3390 帧）、普通玩法／录像播放／存档后端失败重试／Extra 解锁检查。四个结束交接夹具额外等待 Result fade-in 完成，检查 mode=0、alpha=0、dirty=1，并保存可见 Result 截图。实际浏览器成绩文件共 20 份全部通过原版 `6ca60` 解码和 `74a3a..74aa2` 重编码逐字节检查。源快照审计为 145 份当前、100 份历史报告、212 个共享模块，uncovered=[]；报告仅支持各自注明的范围。原游戏 `score.dat` SHA-256 仍为 `44805e2691e6d208290a9ecdbe3eec26d7d1a7ddb6e84ca21d2a502732609441`。整作 `completeGame=false`，目标保持 active。


### 挑战模式启动、初始 Rank 与录像回放（2026-11-15）

原版标题到新一轮玩法的 `4dbc0..4dc3c` 分支读取配置并设置 `lifeProtection`：挑战模式为真，固定 2 残机；Extra 或 stage practice 入口固定 2 残机／3 Bomb，普通标准入口使用配置残机／Bomb。实际玩法初始化 `3aa0f..3aaf6` 使挑战模式初始 Power 为 8，标准模式为 0，Extra 的分数 Extend 索引为 4，其他常规难度为 0。新共享模块 `gameplay-start-settings.mjs` 已接入生产 `startGame`，模式 1 不再进入 unsupported；stage／spell practice owner 仍未接通。

检查初始化时修复了原浏览器错误固定 Rank=0 的问题。原版表 `3084e0` 为 Easy 20、Normal／Hard／Lunatic 32、Extra 18；新一轮使用 `3aed7..3af10` 读表，录像每个关卡使用 `3b15d..3b171` 读表，普通跨关保留 Rank。生产入口和录像入口已采用对应值。该修复会改变以前使用错误初始 Rank 的弹幕和自然失败时序，旧报告按原 source hash 保留为历史，不能用旧时序宣称当前行为等价。完整动态 Rank 生命周期仍需进一步核对。

`th06nc-gameplay-start-settings-native-verified.json` 执行原版启动前缀：1152 组配置／模式／练习／难度／残机／Bomb，逐字段比较启动参数、实际 stock 复制、初始 Power 和 Extend 索引；另 160 组覆盖五难度、两处实际 Rank 初始化调用点及 16 种先前内存值。未声称完整玩法初始化、音乐清理或任务图等价。

四份 `th06nc-extra-*-challenge-clear-handoff-browser-verified.json` 均通过真实标题模式选择进入挑战 Extra，检查 Power 8／Rank 18、实际敌弹和中弹、暂停恢复、受控 MSG11 结束后的 Result、挑战 HSCR 分组、成绩和录像保存重载。四自机都在 frame 1334 自然中弹 3 次而残机保持 2，frame 1364 后进入 Result。真实保存的挑战录像由标题再次载入，在 frame 344／1334 的世界摘要、七类演员池、计数、Rank 和 RNG 全部与录制端一致。结束 MSG11 是明确的调试夹具，不写入录像，故只证明回放至这两个实际中弹检查点；不构成自然 Extra Boss／隐藏阶段击破或完整录像结束验收。四份录像与截图保存于 `artifacts/th06nc/extra-*-challenge-clear-handoff-browser/`。

同时修复录像启动的成绩分组：标题解析的挑战标志传入 `startGame`，最高分按挑战组读取，避免一律从标准模式组取最高分。


本轮补充完成挑战普通难度灵梦 A `end00`／Staff／Result（3390 帧）及挑战 Easy 魔理沙 A `end10b`／Staff／Result（2334 帧）的受控结束交接／CLRD 保存重载检查；正常玩法初始 Rank 分别 32／20，均从真实标题挑战选择启动。仍不代表自然通关。新 Rank 下四自机标准 Extra 自然零残机验收全部重跑通过，帧数依次 1103／1098／1098／1107；标准 Extra 四自机受控 MSG11 交接全部重跑通过，均 frame 884 停止世界更新。普通四自机存档录像播放回归也全部通过，各自自然结束于 frame 2193。灵梦 A 另回归存档后端失败重试和 Extra 解锁。

最终 14 份实际浏览器录像通过原版完整解码字节对照，26 份实际成绩通过原版解码／重编码完整字节对照。四份挑战录像均包含在这次原版文件检查中。浏览器 Extra 报告的 scope 文字已按自然零残机／受控结束交接／挑战录像复现分开说明，未重写执行时的 source hashes。原游戏成绩文件 SHA-256 保持 `44805e2691e6d208290a9ecdbe3eec26d7d1a7ddb6e84ca21d2a502732609441`。


### 关卡练习入口、Result 17 与 PSCR 回写（2026-11-15）

新增 `title-practice-entry.mjs`、`title-practice-update.mjs` 和 `title-practice-draw.mjs`，接入真实标题 mode 14 → practice stage 22 → final confirmation 24／25。练习关数读取对应自机／难度的 CLRD 第二组进度，上限 6，Easy 在达到 6 时限制为 5；支持环绕选择、返回模式页、重新进入、最终确认取消并保留关卡。关卡列表按原版位置／颜色／渐显和 `STAGE %d  %.9llu` 格式显示 PSCR 的 unsigned 64-bit best。生产标题使用共享存档里的 CLRD／PSCR 视图。

原版对照：mode 14（包含实际 `558c0` 练习入口 helper）448 场、stage 22 导航／取消／确认 448 场、final confirmation 24 标准／练习返回 448 场，均比较实际 helper 和完整 ANM 字节；共同 owner 新增练习状态对照，合计 864 场。练习列表 `54ca8..54f3f` 实际文本请求／坐标／颜色对照 768 场，含 Easy 关数上限和 uint64 最大分数；字体 formatter／cache／GPU 边界受控，不能据此宣称像素等价。

`practice-gameplay.mjs` 接入原版 `3afe5..3b00b`：第 1 关保留基础 Power，第 2 关 Power 64，其余关 Power 128。Result 17 的原版完整 dispatcher `6e43e..6e4db` 不经过普通姓名／HSCR／录像选择页，也不更新共同 Result ANM；它等待黑色遮罩完成后请求标题状态 1。练习分数通过已验证的 Result stat producer 更新现有 PSCR best，再进行 canonical commit。30 组初始 Power 以及 140 组完整 Result owner／fade／请求／返回值原版对照通过，Result 构造和任务图仍属独立未完成范围。

本次修正两处历史字段误名：MSG11 和复活 Bomb 重置读取的原版 `4f27b4` 是 stage practice，不是 replay playback（后者是 `4f278c`）。生产条件和原版夹具均改用 `practice`；296 场 MSG 分支与 1920 场自机生命周期对照重新通过。标题录像 helper 的 replay 字段本来对应 `4f278c`，保持其含义。

浏览器已通过四自机、标准／挑战第二／第三关练习、Easy 第五关练习，以及灵梦 A／魔理沙 A 第一关自然零残机失败的检查。非第一关完成请求由明确的 MSG11 夹具发出；它们不构成自然关卡击破。自然零残机两场未注入自机／HP／残机／分数，经黑色渐隐和 Result17 自动回标题，最大世界帧 2203。每份文件仅新增对应 PSCR（profile／difficulty／zero-based stage），没有 HSCR，也不出现普通姓名、结尾或录像保存页面；实际文件 51624 字节，重载后重新进入关卡列表／游戏 HUD 能读取保存的最高分。所有检查先通过真实进度 producer 种入 CLRD 第二组可选关数，不能称为自然练习解锁。对应 `th06nc-practice-*-browser-verified.json` 各自保留 scope；自然完整练习通关、完整取消回主菜单、成就和 Task/cache/audio/GPU 等价仍未完成。


练习保存失败路径另有真实 IndexedDB transaction abort 浏览器检查：Result17／dirty=1 和旧提交文件（51600 字节）保留，显示重试按钮，点击后成功写入 PSCR（51624 字节），重载、选关列表和 HUD 最高分检查通过。该场报告为 `th06nc-practice-reimu-a-stage2-standard-save-failure-browser-verified.json`。普通灵梦 A 录像／存档后端／Extra 解锁、Extra 自然零残机、挑战 Extra 保存录像／回放摘要和 `end00`／Staff／Result 回归均通过。

本轮累计实际文件验收：14 份录像通过原版解码完整字节对照，34 份成绩（含 8 份练习产物）通过原版解码／重编码完整字节对照。当前源快照审计为 156 份当前、110 份历史报告、217 个共享模块，uncovered=[]；保留各自 scope，不扩大为整作或 Native pixel 等价。原游戏 `score.dat` SHA-256 仍为 `44805e2691e6d208290a9ecdbe3eec26d7d1a7ddb6e84ca21d2a502732609441`。`completeGame=false`，目标保持 active。


### 完整取消选关、共享通关标志与首批自然完整流程（2026-11-15）

`title-selection-return.mjs` 接入选关取消 state10 的实际 frame==30 判定（`4b0d7..4b0f0`），重新绑定基础标题 ANM 后运行真实 warm helper 的逻辑，再走 state2 快速进入主菜单。原版 helper `4d370..4d67b` 的循环界限为 `0x167`，即 **359 次**；此前阅读时口述 355 已由完整 VM 字节对照纠正。在第 169 次请求背景 1；返回后按原版共同 owner 设置背景 6、清理 warm 标志并推进动画。6 组返回判定、15 组 warm helper／state2 前缀比较完整 VM／control／标量；共同 owner 扩为 1968 场、259776 次 VM 对照，覆盖 state10→0→2→3、warm/non-warm 和 entry-hold 分支。

`th06nc-title-cancel-standard-practice-browser-verified.json`／`th06nc-title-cancel-extra-browser-verified.json` 用实际浏览器键盘事件检查最终确认页逐层取消回主标题，恢复 Standard／Practice／Extra 对应主菜单项、保留内存难度／自机／射型／模式；Extra→Standard 正确恢复 Normal。标准／练习场还实际重新进入 Easy 魔理沙 B Challenge 并游玩 120 帧；取消期间成绩文件未写入。此处不代表磁盘配置或 Native resource/cache/task 逐字节等价。

修正 `4f27b3` 的共享含义：它既是 MSG task suspension，也被 Result `70c04..70c22` 读取为 cleared 标记。`game-clear-flag.mjs` 绑定同一个宿主字段；ending initializer 的实际 `2c914` 写 1 现在接到浏览器。16 场原版 producer／consumer 比较通过。此前普通结尾／Extra 完成后浏览器未同步 `cleared`，HSCR 错记普通关数；当前实际完成请求应写 stage byte 99（显示 C）。四自机 Standard／Challenge Extra 的受控结束、保存录像／前段回放检查均已重跑，检查 C 标记；没有人为给 Extra CLRD 写 99。自然零残机条目依旧使用实际关数。历史报告只支持其原 source hash，不能用旧 stage7 结束条目证明当前通关记录。

`stage-rng.mjs` 接通每关 initializer `3b171..3b189`：先保存当前 uint16 seed，再清零 uint32 RNG draw counter，原版 16 场对照通过。修复普通跨关累计 count 而录像各关重置 count 的差异；初始整局 seed producer 和完整 Native application task 顺序仍未证明。

自然六关流程首次在第三关 frame4490 触发旧 `enemy-draw.mjs` 的 3D guard。当前按实际 `67f0` 桥接逻辑：X／Y 旋转非零（含 NaN 分支）进入 `4dc0` world 路径，保持世界坐标；平面路径才加 gameplay offset 并按 Z rotation 选择 snap。渲染器接到已有三轴 world quad／游戏相机路径。原版完整 `38290..3868c` enemy draw 和实际 `67f0` 桥接 96 场，比较首敌完整字节及绘制请求；相机／渲染后端是受控边界，world quad 使用已有独立原版几何证据，仍不声称 Native pixel／depth／UV sampling 等价。

自然完整浏览器验收（全部为原版 Challenge，不修改 HP／残机／分数／Boss／结束状态，不种入解锁；仅正常射击和 Ctrl 对话跳过输入）：

- `th06nc-natural-run-reimu-a-difficulty1-challenge-browser-verified.json`：Normal 灵梦 A，实际跨越关卡 1..6、各 Boss／对话、自然结尾／Staff、姓名／总结、真实录像保存和 canonical 成绩／录像重载。六关录像记录帧为 11945、17329、21930、24365、25086、33909，合计 **134564**；结尾 2232 帧。最终分数 **12812130**，HSCR C，CLRD 第二组 99、第一组不写 99（Challenge 超过 5 次失误的原版限制）。实际录像 528 字节，成绩 51636 字节。文件中 20 个 CATK 的尝试次数从零变为 1，捕获均为零；这是实际符卡尝试到保存的证据，不构成自然捕获保存验收。
- `th06nc-natural-run-marisa-a-difficulty0-challenge-browser-verified.json`：Easy 魔理沙 A，实际 1..5 关后进入 ending。五关录像帧 11010、15327、19482、19456、24684，结尾 2256 帧；最终 **11115580** 分，HSCR C、CLRD 第二组 99；录像 460 字节，成绩 51636 字节。10 个 CATK 有实际尝试记录。保存了过渡完成后的可见 Result C／Staff／美铃阶段截图。
- `th06nc-practice-reimu-a-stage1-challenge-natural-clear-browser-verified.json`：真实第一关练习 Challenge，经实际 Boss／对话／MSG11 自然结束，最大世界帧 11954，随后 Result17／PSCR 保存重载和 best 读取；未注入结束请求。此前第一关 Standard 自然零残机证据与这条自然关卡完成路径明确分开。

两个整局自然录像只完成录制／编码／保存／重载，**尚未证明完整跨关 playback 的演员／RNG 对照**。其他自机／难度、Standard 和 Extra 的自然完整通关、隐藏阶段、Spell Practice、完整配置／Score／Music Room owners、成就持久化、Native task/cache/GPU/audio 及启动流程仍未完成。StageWorld 原有成就请求队列已核对，不会因没有传平台服务而抛错；这些请求尚未持久化，不能称为成就系统完成。


本轮最终文件／源快照检查：16 份实际录像经原版完整解码一致，37 份实际成绩经原版解码／重编码一致；162 份当前、113 份历史报告，220 个共享模块，uncovered=[]。原游戏 `score.dat` SHA-256 仍为 `44805e2691e6d208290a9ecdbe3eec26d7d1a7ddb6e84ca21d2a502732609441`。新增／修改 JS 入口语法检查通过。目标工具当前报告 **usageLimited**（未由本轮更改），完整整作目标保留，未标记 complete；本轮按用户手动继续请求完成上述推进，不能将其描述为已恢复自动续跑。后续关键验收包括六关自然录像的完整 playback 对照、其他难度／自机与 Standard／Extra 自然完成、Spell Practice 和剩余配置／菜单 owners。


### 自然通关录像的完整跨关回放（2026-11-17）

新增 `tools/th06nc-natural-playback-browser-check.mjs`，使用已由自然通关生成、并通过原版解码的原始录像，经过 GameSave 导入，再从真实标题录像文件页／关卡页启动。Normal 灵梦 A 顺序回放 1..6 关，最终分数 12812130；Easy 魔理沙 A 顺序回放 1..5 关，最终分数 11115580。两场都正常返回标题 owner20 的录像选关页，不进入成绩或结尾页面，最终分数与录像末关 header 一致，未写入 score.dat，输入录像字节保持一致。对应报告为 `th06nc-natural-playback-reimu-a-normal-browser-verified.json`、`th06nc-natural-playback-marisa-a-easy-browser-verified.json`。

这里证明完整关卡遍历、对话／场景交接和终点分数／返回状态，**未证明逐帧演员池／RNG 与录制端完全一致**。导入脚本将 Node Buffer 转为独立 Uint8Array，避免 Buffer.slice 的共享内存令测试侧原始文件缓冲被解码改写；产品运行时和磁盘原文件未因此改动。本轮没有修改游戏生产代码。目标工具已核实恢复为 active，整作目标保持原范围，completeGame=false。


2026-11-17 进一步重录六关自然流程，增加分关演员池／RNG 检查点，仍自然完成六关并保存原版格式录像。完整 raw actor-buffer 比较首次在 stage1/frame164 失败：分数、库存、Rank、RNG seed/count 及 player/enemy/bullet/laser/item/popup 六池一致，effects 池 hash 不同。完整 actual/expected 与 source hashes 位于 `artifacts/th06nc/natural-playback-reimu-a-normal-browser/first-mismatch.json`；命令日志位于 `tools/tmp/th06nc-natural-compare.log`。录制和回放当前使用不同绘制频率，缓存字节差异可能源于此，尚未证明因果；下一步必须对齐分关绘制时点后再比较，不能跳过 effects 池或将此失败视为状态一致。先前完整回放终点证据保持其原 input SHA/scope，未扩张为逐帧对照通过。本轮未改游戏生产代码。


### 自然录像完整对象池检查点对齐（2026-11-17）

记录器增加 `{stage,frame}` 绘制时序，调试入口 `advanceToFrame` 仍经过原有 replay dialogue chain restart，只推迟绘制到记录的逻辑帧。首次时序记录为空，原因是测试在刷新页面之后读取数组；改为刷新前保存后，实际捕获 1130 个绘制记录。对齐后，Normal 灵梦 A 六关回放 **108 个检查点全部通过**：player/enemy/effects/bullets/lasers/items/popups 七类完整 raw pool、分数／库存／Rank／RNG seed/count 及组合 SHA 一致。此前 stage1/frame164 的 effects-only 差异在相同时序下消失，保留 `first-mismatch.json` 作为旧失败证据。不能将其解释为每逻辑帧、原版 GPU 或原生完整任务图等价。

本次自然六关重录的关卡帧和最终分数保持不变；实际结尾输入流程为 2424 帧。回放经过真实录像菜单启动，完整返回 owner20；分数 12812130，未写入成绩，录像字节不变。16 份录像原版解码、37 份成绩原版解码／重编码再次通过。整作目标仍为 active，completeGame=false。


Hard 灵梦 B 进一步自然完成六关（13158、18388、23923、26650、25012、35892 帧），结尾／Staff 2304 帧，最终分数 24361670，实际成绩 51636／录像 528 字节并重载。对应完整回放的 **115 个** 分关检查点通过相同七池／计数／RNG／组合 SHA 比较，返回录像选关页且无成绩写入、录像未变。报告为 `th06nc-natural-run-reimu-b-difficulty2-challenge-browser-verified.json` 和 `th06nc-natural-playback-reimu-b-hard-browser-verified.json`。这是该自机／难度的 Challenge 路径证据，不能外推为全部组合通关。加入实际文件后原版编解码验收为 17 份录像和 38 份成绩。


Lunatic 魔理沙 B 自然 Challenge 六关录像帧为 12186、18244、24216、25590、24933、33848，结尾／Staff 2232 帧，最终分数 31379690，成绩 51636／录像 528 字节保存重载。完整回放 **112 个** 检查点的七池／计数／RNG／组合 SHA 全部一致，真实返回录像选关页，录像字节不变、无成绩写入。对应 `th06nc-natural-run-marisa-b-difficulty3-challenge-browser-verified.json`、`th06nc-natural-playback-marisa-b-lunatic-browser-verified.json`。18 份实际录像和 39 份实际成绩的原版编解码检查通过，仍不代表全部自机×难度组合或 Standard／Extra 自然通关完成。


Easy 魔理沙 A 重录补齐绘制时序和检查点，五关帧／分数／结尾保持一致；完整回放 **73 个** 检查点通过七池／计数／RNG／组合 SHA 比较。四条代表路径合计 **408 个** 检查点通过。新增 `tools/th06nc-natural-challenge-matrix-browser-check.mjs` 依次覆盖 4 自机×4 难度，自然录制和回放共用一个 CDP 端口，严格串行；只复用源快照匹配且检查点非空、录像 SHA 一致的报告，每次完成写入证据摘要及报告哈希。未完成全部 16 组合前 matrix 报告 passed=false；即使矩阵完成仍不等于整作完成。


### Challenge 全自机／难度自然通关矩阵（2026-11-17）

`th06nc-natural-challenge-matrix-browser-verified.json` 的 **16/16 组合全部通过**（灵梦 A/B、魔理沙 A/B × Easy/Normal/Hard/Lunatic）。每组经真实标题选项自然推进、ending／Staff／HSCR C／CLRD／实际录像保存和字节一致重载，再通过真实录像文件／选关菜单完整回放。共 **1611 个** 绘制时序对齐的检查点，比较七类完整 raw actor pools、计数／RNG 和组合 SHA；每场均自然返回录像选关页、最终分数一致、录像未改、无成绩写入。矩阵保存每份底层报告及其 SHA，原版文件校验扩展为 **30 份录像解码、51 份成绩解码／重编码**，全部通过。

此矩阵仅覆盖普通 Challenge；不声称逐逻辑帧原版应用等价、Standard／Extra 自然通关、Spell Practice、成就持久化、启动／配置／Score／Music Room 完整 owners 或 Native task/cache/GPU/audio 等价。完整整作目标保持 active，completeGame=false。后续 Spell Practice 反汇编定位：标题 state27 位于 `4c4cb..4cbcf`；state28..31 共用 `52370` updater。原始只读定位输出保存在 `tools/tmp/th06nc-spell-title-entry.txt`、`th06nc-spell-owner-body.txt`，这些定位不是实现／通过证据。


### Spell Practice 目录和查询基础（2026-11-17）

新增 `shared/th06nc/spell-practice-table.mjs`。原始 `th06IN.dat/spellpractice.msgpack` version6 实际目录为 **131 条**（ID 0..130）；CATK 仍有 134 槽，不将二者混淆。原版 `76b90..77540` 的完整资源解析／发布函数与 JS 对照通过，比较发布数量及每条初始化字段：uint8 ID／零基关卡、uint16 ECL 子程序、uint8 难度／组内序号／中 Boss 标记、最长 31 字节 UTF-8 名称键。资源 I/O、分配释放、memset/memcpy/memcmp、cookie 检查为受控服务；未把分配尾部／名称后未初始化字节当作有意义状态比较。对应 `th06nc-spell-practice-table-native-verified.json`，资源 SHA 为 `520198387b5a4401d94f0679ee51bca685a624c6734363614ddbe27ec722761a`。

继续对照实际查询函数：`466d0` 按 uint8 ID 查找（260 场）；`46900` 八行列表计数／滚动窗口（1716 场，含空关卡、越界滚动和整数边界）；`46850` 同关卡／组内序号任一难度有普通 attempts 就解锁（855 场）；`46740` 当前自机所有目录符卡均有普通 attempts 且对应 practiceCaptures 非零才视为关卡完成（270 场）。五组成绩模式含全空、仅尝试、全捕获、部分未尝试、限定自机捕获，另外测试无效自机。对应 `th06nc-spell-practice-query-native-verified.json`。目录 lazy initializer 是该查询夹具的受控服务，并由前一个完整 native loader 夹具独立核验。

此模块尚未接入标题 Spell Practice owner27..31，不能称为符卡练习菜单／启动／玩法／结果／保存完成。下一步继续资源和 ANM 初始化、菜单输入／绘制、实际符卡启动及结束后计数提交。


### Spell Practice 分层控制与 ANM 初始化（2026-11-17）

新增 `spell-practice-menu.mjs`，投影原版 `52370..532d9` 的 owner28 关卡／29 符卡组／30 难度／31 淡出后启动控制。3424 场实际原版函数对照通过：比较声明的 owner 字段、选关／自机／难度／练习标志／捕获前状态等启动 globals、声音队列、完整 fade 56 字节、音乐 globals 和 stop/release/fade 请求及同步展示服务请求。覆盖七关、首尾符卡组、输入等待、按住连发、相反方向同时按下、确认／取消组合、全锁／全尝试数据、通知／关卡完成提示、退出淡出、启动淡出和非零音乐句柄。Lazy catalog initializer 与 `4f150/4f1f0/4fdd0` 展示刷新为显式受控服务；不能用该控制夹具证明实际文本或动画内容。对应 `th06nc-spell-practice-menu-native-verified.json`。

`spell-practice-layout.mjs` 按 `4c781..4ca1a` 建立 base selection 22 VM 和新增 11 VM。实际加载 selection 与 `spellselect00.anm` 后，**33×288 字节**全部比较通过；单独 sprite VM `1a298` 使用 `1da0 + 2980`，其计时初值 -1、sprite flag 和零计数不同于普通 script initializer，已按原版对齐。原始 ANM 1456 字节及 DDS 4194452 字节从只读 PKGL 提取，并与独立 Python PKGL 哈希一致。对应 `th06nc-spell-practice-layout-native-verified.json`、`th06nc-spell-menu-assets-verified.json`。

`spell-practice-profile.mjs` 实现 `4f150` 角色立绘／标签刷新及 `4f1f0` 机体／预览刷新，保留 setter 未清的旧 VM 字节并使用既有 `initializeAnm`。四自机×三个方向×三个动画时点共 **36 场、每场 34 VM**完整字节及六个转换字段对照通过，包含已运行 15／40 帧后的重复刷新。对应 `th06nc-spell-practice-profile-native-verified.json`。

目前上述组件尚未接入 TitleScene；`4fdd0` 信息文本刷新、实际菜单绘制、owner27 后段初始化和完整 common tick、符卡游戏 initializer、结束／计数提交／返回仍需实现和验证。原普通 Challenge 矩阵范围保持原样，不将新的未接入模块解释为菜单浏览器验收通过。当前源快照审计 186 份当前／126 份历史报告，224 个共享模块，uncovered=[]；这只是模块源快照覆盖，不是整作完成证明。


### Spell Practice 关卡页信息文本（2026-11-17）

新增 `spell-practice-stage-info.mjs`，实现实际 `4fdd0..50ab2` 的 owner28 信息分支：标题、自机名、三列标题、七关标签／关卡名／Boss 名、取得／解锁／总数、关卡完成标志，以及原始 text.anm sprite、字号、颜色、浮点坐标和缩放。隐藏逻辑区分“任一符卡有尝试”和“本关非中 Boss 符卡有尝试”；只有中 Boss 记录时，关卡名可见而 Boss／总数仍可隐藏。未用目录下标替代符卡 ID。

`tools/th06nc-spell-info-native-capture.py` 执行实际完整 `4fdd0..52362`，先执行已核验的菜单 ANM 初始化，再调用实际目录查询／sprite setter／布局逻辑。受控服务为 localization map、C++ string／printf、memcpy／memset、cookie、lazy catalog load。默认 publication 为 no-op；`--native-font` 则执行实际 `7530` publisher，仅在 GPU 字体服务边界使用原始字形元数据独立计算度量，记录元数据和 advance 的 SHA。原版输出位于 `artifacts/th06nc/spell-info-native-cases.json`、`spell-info-native-font-cases.json`；每份 840 场，覆盖 owner28/29/30、七关、中英文、四自机及五组普通／练习成绩。最佳分数输入按原版 uint64 stride 写入大于 32 位的值，供后续符卡／难度页对照；采集本身不代表这两页 JS 已完成。

关卡页对上述两种 publication 各比较 **280 场、9240 个有序文本请求**及完整发布后 VM 字节；真实字体模式包含所有裁剪度量。成绩模式为空、全尝试／全取得、仅中 Boss 尝试、混合尝试／取得、已尝试但未取得，并核对七关完成标志。`th06nc-spell-practice-stage-info-verified.json` 与 `th06nc-spell-practice-stage-info-font-verified.json` 全部通过；无 GPU 像素或标题浏览器集成声明。

真实字体捕获证明 owner29/30 的部分信息合并路径会受实际文字宽度影响；下一步必须按该布局继续实现符卡／难度分支，不能用固定文本列表取代。TitleScene 接入、实际绘制、符卡初始化／自然结束／成绩提交仍未完成。整作目标保持 active，completeGame=false。


### Spell Practice 符卡／难度页及返回定位（2026-11-17）

新增 `spell-practice-card-info.mjs`，按实际 `50ab7..52362` 实现 owner29/30 信息刷新：八行分组窗口与下一组提示、按对应中 Boss／Boss 尝试记录显示名称、四难度（Extra 单项）符卡编号／名称、uint64 最高分、普通与练习尝试／取得统计。保留原版反复发布以度量编号＋名称、取得＋本篇组合宽度的步骤、Float32 运算顺序、组内间距缓存及超宽比例缩放。文字发布依赖真实同步 publisher 生成 VM 度量，不用固定 CSS 布局代替。

空 publication 对照 **560 场、26720 次有序文本请求**，真实 `7530` publisher／独立字形元数据对照 **560 场、24480 次请求**，每场全部相关 text VM 288 字节一致。两种字体路径的发布次数差异来自实际度量触发的合并分支。场景覆盖中英文、七关、四自机、首尾符卡组／滚动、五组混合成绩，最高分输入大于 32 位；输入 owner 间距缓存初值为 0，内部跨难度更新和复用参与比较。报告为 `th06nc-spell-practice-card-info-verified.json`、`th06nc-spell-practice-card-info-font-verified.json`。新公共 `spell-practice-info-text.mjs` 复用 sprite setter、发布与标题逻辑；关卡页两组 280 场原版比较同步重跑通过。

新增 `spell-practice-entry.mjs`，实现 state27 资源／VM 之后的 `4ca1a..4cb5f`：正常进入恢复配置关卡、清零菜单时钟／选项，返回练习时按原版符卡 ID 找回组号／难度／滚动位置，区分 45／30 帧淡入，按顺序调用角色／机体／信息刷新。**1370 场**实际原版对照通过，含全部目录 ID、目录外 ID、uint8 包装、无效配置关卡、淡入前 alpha。该路径恢复的是配置关卡 global `c21e5c`，并不提前修改游戏关卡 global `4f1e84`，已按原版验证。展示刷新在此夹具中为观测服务，其实际逻辑由独立组件夹具验证；不能据此宣称完整标题集成通过。报告为 `th06nc-spell-practice-entry-native-verified.json`。

后续绘制入口已定位为实际 `53500..54869`，其列表 helper 为 `532e0..534fc`，完整只读反汇编存于 `tools/tmp/th06nc-spell-menu-draw-body.txt`。绘制、owner common 接入、TitleScene／字体资源准备、实际符卡玩法及结束后提交仍需完成；整作目标保持 active。当前审计 191 当前／126 历史报告、228 个共享模块，uncovered=[]，仍仅为源快照审计。


### Spell Practice 绘制辅助与顶点透明度（2026-11-17）

新增 `spell-practice-draw-list.mjs`：`532e0` 复用选中／普通 VM 绘制行列表，保留行位置／颜色持久更新；`4e880` 临时平移和透明度调整仅作用于单次 draw，并恢复原 VM。实际函数 **300 场列表＋96 场淡入／平移**对照通过，比较原版 `2a80` 请求时的完整 VM 与调用后状态。包括无选择／越界选择、空列表、不同逐行进度、负滑动、透明度边界。报告 `th06nc-spell-practice-draw-list-native-verified.json`。

`spell-practice-draw-effects.mjs` 接通 `46d40` 脉冲透明度、`4ea50` 难度灰阶、`4e960` 行切换颜色／位移、`4f040` 列表底部上下透明度。原版 **750＋300＋504＋168 场**分别通过，含整数边界、负时钟、裁剪／非裁剪高度及缺少 sprite 绑定。此处观察 `2a80` 服务边界，不把 draw 请求等同于实际 GPU 输出。

实际 `2a80` 的上下顶点透明度在 byte 空间采用 `(baseAlpha * factor + 127) / 255` 向下取整。新增 `anm-vertex-alpha.mjs`，对照 `319d..31e7` **65536 个 byte 组合**，四顶点 alpha 全部一致。另执行实际 cropped／uncropped `2a80..3385` 的 8 场场景确认前两个顶点属于顶部、后两个属于底部及 RGB 保持；该方向场景禁用 pixel snapping，未执行 GPU。报告 `th06nc-anm-vertex-alpha-native-verified.json`。

`AnmRendererGl` 增加上下透明度参数及 shader 顶点插值，默认参数保留统一透明度。真实 WebGL2 编译／链接及 **16 quad、512 行** RGB 采样通过（黑底、线性插值误差不超过 1 byte）；对应 `th06nc-vertex-alpha-browser-verified.json`。实际标题完整取消／返回／再启动的 14 检查点浏览器回归通过。没有将此解释为原版完整 GPU pixel 等价。

完整 Spell menu 主绘制 `53500..54869`、选中行效果 `4eaf0..4f03c` 和 TitleScene／common owner 接入仍待完成，已有组件尚未开放用户菜单入口；实际符卡启动／自然结束／提交仍是剩余目标。只读反汇编保存于 `tools/tmp/th06nc-spell-menu-draw-body.txt`、`th06nc-spell-highlight-draw-body.txt`。渲染器源变更后旧浏览器报告按原哈希保留为历史证据，没有改写成当前版本；本轮审计 **163 当前／158 历史、231 模块、uncovered=[]**，仅证明各报告原有范围。整作目标保持 active、completeGame=false。

### Spell Practice 选中高亮与旋转裁剪分支（2026-11-17）

新增 `spell-practice-highlight.mjs`，实现实际 `4eaf0..4f038` 的选中行绘制：通知初期放大／上移／透明度、后续衰减摆动、切换时方向摆动、按原精灵尺寸计算旋转中心，清除临时 VM 的锚点位并保留原始 VM。`tools/th06nc-spell-practice-highlight-native-check.py` 执行完整函数，比较 **2307 场**调用 `36c0` 时的完整 288 字节 VM、snap=false 与调用后原始状态。覆盖 noticeClock -1..62、切换边界、三个方向、负缩放、不同 alpha 及未绑定／失效资源／缺失纹理。纹理可用性、cookie、f32 sin/cos 为受控服务；不声明原版 CRT 三角函数或 GPU 等价。

实际旋转入口 `36c0` 使用完整 sprite 的尺寸和 UV，忽略 VM 裁剪矩形；`anmQuad` 已按该分支处理，取消原先旋转裁剪报错。原版几何对照扩展为 **2860 场、478 场旋转，其中 224 场带裁剪字段**，全四顶点 XY/UV 字节一致；含八种锚点、正负缩放，整体覆盖 480／1080／1440 高度。新增旋转裁剪组合使用 480 高度，三角值双方提供相同 f32，未执行采样／混合／像素或 CRT 三角函数。报告 `th06nc-anm-quad-native-verified.json` 保留具体边界。

公共几何修改后的实际标题取消／返回／重新启动浏览器回归 **14 检查点**通过并进入游戏。原版 score.dat SHA256 仍为 `44805e2691e6d208290a9ecdbe3eec26d7d1a7ddb6e84ca21d2a502732609441`。源审计 **164 当前／159 历史报告、232 模块、uncovered=[]**；旧源快照证据不改写。Spell Practice 主绘制、TitleScene／common 接入、实际符卡启动／结束／提交继续待完成，整作目标保持 active。

### Spell Practice 主绘制与标题组件组合（2026-11-17）

新增 `spell-practice-draw.mjs`，实现完整实际 `53500..54869`：关卡页的时序滑入、复用选中／普通行精灵、关卡取得标记、三列表头；符卡组页八行窗口、底部下一行预览和独立上下透明度；难度页及 Extra 单项、实际 difficulty.anm 精灵绑定、符卡编号／名称／最高分／取得统计和动态取得标记。保留原版每次 draw 的有序请求和临时／持久 VM 字段更新。`tools/th06nc-spell-practice-draw-native-check.py` 执行整个函数，连同实际列表／淡入／高亮／切换／边界 helper、sprite setter、目录及记录查询，比较 **1120 场、53516 次绘制请求的完整 VM**及调用后保留状态，全部通过。输入文本 VM 来自已独立验证的实际字体捕获，覆盖中英文、七关、四机体、五种成绩、28／29／30／31 状态以及逐步入场和通知时钟。difficulty.anm 真实加载，不能以缺失精灵导致绑定跳过的场景冒充难度绘制验证。受控边界包括纹理可用性、cookie、目录 lazy init、双方相同的 f32 三角值以及最终 `2a80`／`36c0` 提交；不声明原版 CRT、GPU 像素或整张菜单等价。报告 `th06nc-spell-practice-draw-native-verified.json`。

新增 `SpellPracticePresentation`，将资源准备后的 VM 初始化、目录、共享 CATK 记录、角色／机体刷新、实际同步字体发布、entry／controller／main draw 组合为标题宿主组件。TitleScene 增加可选 spellServices 入口，使用宿主提供的目录／记录／配置／字体服务；state27 等待加载时钟后进入，28..31 执行实际控制器，生成独立 `startSpellPractice` 启动请求。返回主菜单后可重新进入并保留配置。公共 owner 扩展 27..31 支持，只在稳定 28..30 增加 pulse；实际 `4cd09..4d0ad` **2640 场、348480 个 VM 比较**通过。该公共夹具使用基础标题资源，未据此宣称资源替换／析构等价。

`tools/th06nc-spell-practice-presentation-check.mjs` 的 **8 场 CPU 组合流程**覆盖四机体×锁定／解锁成绩、七关切页、符卡滚动、难度／Extra 单项、左右切机体、取消回主菜单／再入、所选符卡启动请求，使用实际字体 metadata 生成裁剪和真实 ANM 几何；6092 次文本 publication、888460 次 draw 请求、377092 个可见 quad 均无异常。此处成绩为受控输入，没有物理浏览器按键或 GPU 绘制声明。现有实际标题取消／返回／再启动游戏浏览器回归 14 检查点同步通过，原 score.dat SHA 不变。

应用 boot 目前尚未提供 spellServices，入口仍待完整接线。实际外层标题 draw 在主绘制前后还调用 `4f3c0`、`4f5b0` 处理角色／机体预览；这两段尚未实现，因此不将上述主绘制／组件组合视为完整菜单验收。只读反汇编已保存为 `tools/tmp/th06nc-spell-profile-draw-annotated.txt`，主绘制常量版为 `th06nc-spell-menu-draw-annotated.txt`。接下来需补这两个 helper、应用字体／资源宿主以及符卡玩法初始化、自然结束、成绩提交与返回定位。源审计 **166 当前／159 历史、234 模块、uncovered=[]** 仅为快照审计。整作仍未完成，目标保持 active。

### Spell Practice 角色／机体预览及浏览器菜单绘制（2026-11-17）

新增 `spell-practice-profile-draw.mjs`，实现实际 `4f3c0`、`4f5b0` 以及嵌套 `4fc00`：贴近右屏幕边缘的机体图像、切换角色时两个角色名交叉淡入及位移、选中机体名的缩放／透明度、入场延迟及左右镜像装饰条。角色名／机体名复制完整临时 VM 后绘制，机体图像和装饰条的原版保留字段则持久更新。原版执行比较 **1080 场、5832 次完整 VM 绘制请求**及全部相关保留 VM，通过；覆盖四机体、state28／30、入场边界、切换时钟 0／1／5／10／11、三个方向、不同 ANM 更新阶段及 1920×1080／1280×720／640×480。最终提交、cookie、memset 和纹理可用性为受控边界，不声明 GPU／CRT 三角函数等价。报告 `th06nc-spell-profile-draw-native-verified.json`。

原版外层跳转表 `55800` 确认：state28 顺序是预览→主列表→角色／机体名；state29／30／31 是预览→角色／机体名→主列表。Presentation 已据此接线，TitleScene 与 GameRenderer 传递实际 framebuffer 宽高（当前应用为 **1926×1080**），避免预览沿用默认 1920 宽度。8 场 CPU 组合流程重跑通过，6092 次字体 publication、915396 次 draw 请求、404028 个可见 quad；其范围仍不包含实际游戏启动／结束／存档。

新增独立浏览器夹具 `tools/th06nc-spell-menu-browser-fixture.mjs` 及 `th06nc-spell-menu-browser-check.mjs`：使用实际 TitleScene、Presentation、GameAssets、FontTextureGl、GameRenderer、原始 ANM／DDS／字形／翻译资源，通过物理 CDP 按键验证锁定／解锁关卡页、四机体符卡／难度页、第四关超过八行的滚动列表、Extra 单难度及取消回主菜单，**12 个检查点**通过，无 GL 错误。显式加载菜单所需 `15_0x00E0FFFF_0x00000000_0x00010101_0x00040202_zh-CN` 字体，未用缺少 font cache 的旧裁剪度量冒充实际文本。截图保存在 `artifacts/th06nc/spell-menu-browser/`，已检查关卡、魔理沙 B 难度及滚动页，文本、取得标记、人物和镜像装饰均可见。此夹具使用受控 CATK 数据，不访问用户存档，不等同于应用 boot／游戏玩法或原版 GPU 像素验收；报告 `th06nc-spell-menu-browser-verified.json`。

公共 Renderer／TitleScene 修改后，实际游戏标题取消→返回→重新启动及 120 ticks 游戏回归 **14 检查点**通过。源审计 **168 当前／159 历史报告、235 模块、uncovered=[]**，旧源报告维持原哈希。应用仍需在 boot／return 中提供 Spell 服务及新增字体／资源，接通实际符卡玩法初始化、结束后成绩提交、返回定位和录像；不能将独立菜单绘制通过解释成完整 Spell Practice 或整作完成。目标继续 active、completeGame=false。

### Spell Practice 专用敌人生成与超时完成（2026-11-17）

新增 `spell-practice-spawn.mjs`，实现实际 timeline phase 的 `36260..363bd` 分支，并由 EnemyWorld 在 Spell 模式使用，绕过普通 ECL 时间轴。按 uint8 符卡 ID 查 131 行目录、读取有符号 subroutine，找到第一个空敌人槽，复制标准模板并在 `(192,-64,0)` 执行初始 ECL tick，之后设 item=-2（不随机掉落）、固定击破分 200000，保留初始 tick 的生命与动画结果。`spellEnemyStarted` 对应 `aa1e7f`，成功或满槽都设置；无有效 ID 时不设置，重复调用不生成第二个敌人。普通模式继续走原时间轴。

`tools/th06nc-spell-practice-spawn-native-check.py` 执行实际原版分支及完整初始 ECL，使用真实目录、每个子程序独立设置生命的合成脚本，比较 **810 场**全部敌人池 SHA、所选槽完整 0x10b0 字节、初始化标记和重复行为，包括全部 ID、uint8 包装、无效 ID、0／3／256 个占槽和预先初始化状态。memcpy、cookie、catalog lazy init 为受控服务，不把合成脚本对照当成真实符卡玩法验收。报告 `th06nc-spell-practice-spawn-native-verified.json`。

`tools/th06nc-spell-practice-world-check.mjs` 以实际七关 ECL／敌人／弹幕／激光／特效 ANM，在 StageWorld 中启动 **全部 131 张符卡各 240 ticks，共 31440 ticks**。执行真实自机／道具／敌人／弹幕／特效更新，使用灵梦 A、input0、禁用碰撞／伤害服务，未加载 STD／MSG／HUD／音画；每张均恰好发布一次正确 ID／key 的符卡介绍并增加一次对应难度 practiceAttempts，普通 timeline cursor 不运行（messageClock 仍可被真实 ECL 章节命令按 1800 增加）。报告 `th06nc-spell-practice-world-verified.json`，没有原版逐帧或自然通关声明。

`enemy-phase.mjs` 原有“符卡超时未实现”中断已按 `36f50..37160` 替换：非 suppress-cancel 超时照常增加失败计数、清除 spellActive、取消弹幕，然后仅在 Boss＋Spell 模式写 `spellFinished`（`aa1e8e`）。扩展的实际原版生命阈值／超时比较 **720 场、3600 个敌人状态**通过，含普通／Spell、Boss／非 Boss、阈值先转相、超时取消抑制和其他敌人重置；该夹具弹幕池为空。报告 `th06nc-enemy-phase-native-verified.json`。

上述 world 检查 `--timeout` 运行真实符卡 **0／70／130** 到实际脚本结束，分别 **1380／2460／9060 ticks，共12900 ticks**，未修改 HP 或计时器，仍以禁用碰撞／伤害服务隔离启动与超时逻辑；不是自然玩家通关，尚未接 Result／存档。报告 `th06nc-spell-practice-timeout-world-verified.json`。普通敌人世界原版回归同步通过 **8 场、15520 原版连续帧、1176 检查点、13837 个敌人状态比较**；实际应用标题取消后重新启动及120 ticks 游戏的 14 检查点浏览器回归也通过。原 score.dat SHA 保持不变。源审计 **172 当前／159 历史、236 模块、uncovered=[]**。

应用的实际 Spell 启动仍待准备正确初始全局／自机设置、STD 背景定位、成绩与录像及结束返回。已定位 `3b018..3b0cb` 复位启动标记并从按 ID 的缓存取得初始 Power（缺失回退128），`3b4b7` 调 `77550` 准备背景；这些不是将 Player Power 固定128和背景从零开始即可替代的路径，尚未完成对照。原版只读片段位于 `tools/tmp/th06nc-spell-game-init.txt` 等，后续需继续核对 `77550`／`77bb0` 以及缓存生产者 `777a0`。整作与 Spell 全流程仍未完成，目标保持 active。

### Spell Practice 背景快进与初始 Power（2026-11-17）

新增 `spell-practice-background.mjs`，实现实际 `77550..77732` 的启动背景准备：扫描 ECL timeline 的主 Boss 消息、中 Boss 消息及 item=-2 敌人标记选择目标时间；按目录 midboss 标志选分支。扫描 STD 时在**第一个 time=-1** 记录停止；非中 Boss 且没有 wait 指令时，如最后镜头关键帧位于目标后1800帧内，推进目标改为最后关键帧＋1。背景快进逐次执行实际 STD 更新，依次释放较早 wait，保留最后 wait。第六关 ID103 的目标因此为4573，不能错误使用主 Boss 消息时间3096或把 time=-1 的位置关键帧当成普通末尾时间。

`tools/th06nc-spell-background-native-check.py` 以七关实际 ECL／STD／背景 ANM 执行原版完整 `77550` 和 `77bb0`，对全部 **131 个 ID、973443 次背景更新**比较完整0x220 owner、mutable STD 文件／动画池 SHA、摄像方向、逐次雾调用及快进次数，全部通过。资源运输／分配、雾调用与 catalog lazy init 为受控服务；未执行 GPU 或完整玩法初始化。报告 `th06nc-spell-background-native-verified.json`。

按 ID 的 Power 表现已追溯到实际静态初始化器 `1780..188a`：固定九个键值，ID0／1为32，ID2..8为64；其余字节ID在 `3b018..3b0cb` 回退128。新增 `spell-practice-power.mjs`。原版初始化器在受控 allocation／map insertion／atexit 边界观察到全部九个键值，再以这些键值构造受控链式 bucket，执行真实 lookup 对 **259 个 ID／包装输入**比较通过。不是由本篇运行中动态生成的 Power 缓存，也没有对 C++ unordered_map 分配／扩容实现或完整启动全局作等价声明。报告 `th06nc-spell-practice-power-native-verified.json`。

StageWorld 已在实际 STD 初始化后、首帧敌人启动前执行 Spell 背景准备。全部131张符卡×240ticks 的 world 检查改为同时运行实际 STD／背景动画，并使用原版 Power 和初始 Rank；共31440玩法ticks通过，另有各自准备帧。0／70／130 的脚本结束检查在相同接入下再次通过12900ticks；碰撞／伤害仍是受控禁用，不能视为自然玩家清关。普通组合世界原版回归 **8 场、40000 连续帧、2712 检查点、46173 敌人状态**通过，实际标题取消→重新启动→120ticks游戏的14检查点浏览器回归通过。原 score.dat SHA不变。

当前审计 **175 当前／158 历史报告、238 模块、uncovered=[]**。后续需完成启动全局和实时库存的生命周期、应用 boot／return 资源与字体服务、实际 Spell handoff、结果展示／成绩提交／录像。`3b0cb` 的库存字段在后续核对中确认为实时库存，续关默认库存保持；详见后续启动／结果状态核验。只读反汇编另存 `tools/tmp/th06nc-spell-background-prepare.txt`、`th06nc-spell-power-initializer.txt`、`th06nc-spell-run-update.txt`。完整目标仍 active、completeGame=false。

### Spell Practice 启动库存、最高分和结果状态（2026-11-17）

新增 `spell-practice-run.mjs`。启动 `initializeSpellPracticeRun` 对应 `3b018..3b0d4`，复位专用敌人生成、run state／clock、Boss 缓存生命（初值1）、生存标志及完成标志，并设置按ID的初始Power，**将实时 lives／bombs 置零**。已结合 Player life／GameOver 原版字段核对：`4ff0f0/1` 是实时库存，`c21de0/1` 是续关默认库存；`3aa0f..3aa29` 是前者向后者复制，后续 `3b0cb` 仅清实时库存。前一轮将其称为默认库存的解释有误，现已修正。259个实际lookup用例现同时核对上述复位全局、不同初始实时库存及续关默认库存保持，通过；没有对完整任务／配置生命周期作扩大声明。

`advanceSpellPracticeRun` 实现实际 `3a42c..3a626`：在非回放活动帧，按所选ID／difficulty／profile更新 CATK uint64最高分；state0等待 Boss active 转1，state1缓存 Boss life／生存位，等待 Boss inactive 且 spellCounter=0后设120帧并转2，state2倒数后普通游戏发布取得／失败结果请求并转3；回放则请求30帧黑淡出并转4，state4等待 fade.mode2置gameState8。取得判断为缓存生命<=0或生存位，并非简单以超时作为失败。`spellFinished` 负责弹幕等结束行为，不是 state0→1 的门槛。结果绘制／用户选择另属ASCII结果owner。

`tools/th06nc-spell-practice-run-native-check.py` 执行完整原版分支，比较 **2560场**声明的全局、CATK完整记录字节、全56字节fade与结果发布字段（含取得位及ASCII时钟复位），覆盖五种state、倒数边界、空／存活／死亡Boss、生存位、Boss active、spellCounter、普通／回放及uint64高位分数。前置暂停／GameOver门槛为宿主输入，未宣称结果GPU绘制、存档或任务生命周期。报告 `th06nc-spell-practice-run-native-verified.json`。

131张符卡各240ticks的实际 ECL／STD world 组合检查已使用真实启动复位和完整134个共享CATK视图，逐帧执行结果状态，最高分必须等于实际最终score，仍通过31440ticks。`--timeout` 扩展到 **ID0／70／129／130**，运行到延迟完成后的实际结果请求，分别 **1500／2580／5400／9180ticks，共18660ticks**。ID129生存符真实取得，practiceCaptures与结果取得位一致，实际最高分2865520；其余三个超时失败，亦与记录一致。全过程未改HP／计时器，input0并禁用碰撞／伤害，不能据此声称自然玩家通关；结果UI／持久保存／录像仍未接通。

实际应用标题取消→再启动→120ticks游戏的14检查点浏览器回归通过，原score.dat SHA保持。当前源审计 **176当前／158历史、239模块、uncovered=[]**。应用还需接资源／字体与共享记录宿主、Spell启动handoff、一次失误结果入口、实际结果菜单和提交／重试／返回定位／录像。目标保持active，整作未完成。

### Spell Practice 结果菜单组件与原始结果画面（2026-11-17）

新增 `spell-practice-result-menu.mjs`，以原始 intext.anm／text.anm 和共享Pause底层VM处理器实现实际 `c230` update／`c950` draw：取得默认选择0“返回符卡选择”，失败默认选择2“重试”；三项按上／下边沿导航，R直接重试，Z执行所选项，X在这份原版菜单中不取消。菜单标题使用取得script775／失败776，背景分别774／777，并非普通Pause的773。选中／普通／录像不可用颜色、脉冲透明度和入场偏移均按实际draw计算，标签draw的颜色／位移为保留字段，标题临时复制后绘制。

保存录像仅在非回放且recording header可用时接收：10帧黑淡出后以显式宿主服务创建独立Result owner（standalone标志、state12），进入隐藏菜单state3；独立owner关闭后重新淡入10帧并发布菜单标签，创建失败则回state1。独立Result的真实构造／注册／读取文件未在此组件中冒充已完成。返回／重试先等20ticks，再黑淡出30帧；返回设置resumeSpell并请求gameState1，重试设置spellRestartRequested并请求gameState12。

`tools/th06nc-spell-result-menu-native-check.py` 在实际原版两函数中连续运行 **112组、9846帧**，逐帧比较完整0xda0 owner、56字节fade、声音队列、结果全局、独立录像owner请求及 **34630次有序VM绘制、342次文本发布**，全部通过。包括取得／失败、录像可用／不可用、回放标志、禁音／满队列、创建成功／失败／已有owner、独立owner关闭、R、确认重试和返回。受控边界为文字定位／绘制、独立Result分配／构造／任务注册、最终67f0提交；截图捕获未执行。报告 `th06nc-spell-result-menu-native-verified.json`。

独立浏览器夹具增加 `--result`：实际GameAssets／FontTextureGl／GameRenderer.pause和物理CDP按键验证 **16检查点**，覆盖成功／失败默认选择、录像选项、创建失败后的恢复、R重试及返回请求。使用原始图像与中文字体，已检查成功页截图；保存在 `artifacts/th06nc/spell-result-browser/`。底图为黑色，独立录像创建服务在该夹具中固定拒绝；没有实际录像列表、保存或结束后game task接线声明。报告 `th06nc-spell-result-browser-verified.json`。原符卡选择浏览器夹具的12检查点同步重跑通过，原score.dat SHA仍不变。

审计 **179当前／157历史、240模块、uncovered=[]**。组件目前尚未连到实际应用；下一步需在game.mjs中准备Spell目录／资源／字体、传共享CATK视图、按原版复位后启动StageWorld、从正常结束／一次失误进入结果、从结果打开实际standalone录像列表、提交成绩后重试／返回定位，并处理对应回放。完整音画／任务／缓存生命周期仍需验收，目标保持active。


### Spell Practice 实际应用接线与录像闭环

`runtimes/th06nc/game.mjs` 现在向 TitleScene 提供原始符卡表、共享 CATK 记录、字体发布和环境服务。标题读取 spellselect00/text 资源及缺失的 15 号浅青文字字体；符卡启动按表映射关卡/难度，先执行原版起始 Power/零残机/零炸弹初始化，再初始化录像元数据。StageWorld 接收同一符卡表并调用已验证的 STD 准备/独立敌人生成。非道中 Boss 选择第二首关卡音乐，并按需绑定六/七面动态效果资源。

实际失误和符卡结束请求进入 SpellPracticeResultMenu；保存录像使用独立 ResultNameScene state12/standalone 标志，关闭后恢复结果菜单并重新发布文字。重试创建新录制；返回选择恢复原卡片、滚动位置、难度和机体。成绩提交使用现有 canonical 编码器/IndexedDB，不调用会覆盖未提交 CATK 的普通 Result12 磁盘重载。mode3 录像自然结束返回文件列表 state18。

`tools/th06nc-spell-host-browser-check.mjs` 使用真实应用和物理浏览器按键。控制条件仅为用原版格式 CATK attempts 解锁 ID0；没有注入 HP、死亡、结果状态或通关事件。12 个检查点覆盖标题入口、实际关卡、自然失误、录像列表打开/关闭、实际编码保存、重试后第二次自然失误、原卡片恢复，以及保存录像的自然播放/返回。保存的 mode3 头和关卡起始元数据确认 ID0、Power32、残机0、炸弹0；回放不改写成绩文件。独立打开 IndexedDB 后确认 practiceAttempts=2、practiceCaptures=0，uint64 最佳成绩至少包含已观察结果分数。证据：`th06nc-spell-host-browser-verified.json`，原始截图在 `artifacts/th06nc/spell-host-browser/`。

这证明实际应用的失误/录像/重试/持久化路径已接通；成功收取路径、返回时提示生产者、结果界面期间原版任务与演员推进顺序、完整任务注册/析构以及原生 GPU/音频等价仍待验证。固定射击及一次横移的尝试仍自然失误，不算作收取验收。整作仍未完成，目标保持 active。


#### 补充：ID5 原始碰撞下收取与存档/录像验收

`tools/th06nc-spell-host-browser-check.mjs --capture` 进一步通过 12 个实际应用检查点。启动的是一面 Easy ID5（Power64）。控制条件为 CATK 的匹配名字/校验和/ordinary attempts=1 解锁；只读 `th06ncGame.hazards()` 返回现有弹幕位置/速度/尺寸和自机速度。测试每四帧根据线性预测选择方向、低速和射击输入，没有修改 HP、计时、碰撞、无敌或结果状态。实际收取后在第1561帧进入 Success 结果，显示分数783430；这包含真实击破与120帧结果等待。

结果菜单中实际打开、取消、再次打开并保存 mode3 录像；然后重新挑战并自然失误，返回原卡片 order2 / difficulty0。独立重开 IndexedDB 确认 ordinary attempts=1、practiceAttempts=2、practiceCaptures=1、uint64最佳成绩783430。保存录像从实际标题文件列表启动，自然结束回到同一列表，最终分数仍783430，成绩文件字节未变化。证据 `th06nc-spell-host-capture-browser-verified.json`；Success截图 `artifacts/th06nc/spell-host-capture-browser/spell-captured.png` 已人工查看。

此前 ID0 解锁种子仅设 attempts，第一次真实 ECL 会因名字校验和不同按原版清零 ordinary attempts。测试现已按资源表设置匹配名字与校验和，并断言 ordinary attempts=1 跨两次练习/保存保留。这是测试种子修正，不是游戏校验逻辑变更。此前关于成功收取路径未验收的描述由本段 ID5 有界验收补充；其他卡片、原生任务/GPU/音频等价、结果画面期间演员推进以及返回提示生产者仍未完成。原版 score.dat SHA256仍为44805e2691e6d208290a9ecdbe3eec26d7d1a7ddb6e84ca21d2a502732609441。


### Spell 返回提示与结果界面的原版任务门禁

新增 `shared/th06nc/spell-practice-return.mjs`，对应标题初始化 55a30..55c4e 的提示生产过程。它先消费 titleLaunchPending，再要求非启动入口、resumeSpell、当前机体/符卡与进入挑战时记录一致；只在进入前未收取、返回后 practiceCaptures 非零时产生新收取提示。全关完成还要求进入前未全收取，并执行原版 46740 对该关全部卡片/当前机体的完成查询。应用启动现在保存 spellWasCaptured/spellStageWasComplete/lastSpellId/lastSpellProfile 等全局快照，重试保留同一快照；返回标题消费一次，并将请求传给已有标题绘制/计时逻辑。

`tools/th06nc-spell-return-native-check.py` 实际执行上述原版代码、表遍历和 46740；仅控制表延迟初始化与 title-owner memset，比较完整清空后的0x1a728字节对象和相关全局值。2244例通过，覆盖680次新收取、655次全关完成请求，以及已收取/已完成/机体或ID不符/非resume/启动/无待处理请求等情况。浏览器 `--capture` 检查返回后的noticeClock>0；`--known-capture` 控制预先收取一次，重打后不出现新收取提示；`--complete` 为其余一面符卡设置合法CATK收取种子，在真实ID5收取、重试/失误后返回卡片时保留completePending，退到关卡选择才触发completeClock。所有种子条件均明确记录，不将控制种子视为自然解锁验收。

任务门禁已找到原版依据：ASCII更新90d0优先级1，独立Result任务优先级3，游戏任务3a210优先级4。游戏任务在暂停状态1/2、GameOver、spellResultVisible或非游戏状态时返回3；真实任务调度3be80立即停止后续更新。因此玩家7、敌人9、效果10、弹幕/道具11和后续消息任务应冻结。`tools/th06nc-spell-task-gate-native-check.py` 使用控制回调的合成链表，执行真实游戏任务前段/门禁/尾声与调度器：96组通过，92组阻止战斗回调；活动玩法门禁后的正文、回调实体、视口/时间/渲染服务受控，不能据此声称完整任务分配/注册/析构等价。

应用此前在录像列表期间漏掉了ASCII Spell结果owner state3的更新，现在仍推进其头部/背景ANM及clock。浏览器在列表中推进20帧，确认隐藏clock恰好+20，而全部七个演员池、计数器和RNG的摘要保持不变。原版6a36a还要求失败结果隐藏state1/2死亡/重生自机；`drawPlayer`默认从environment.spellResultVisible取该标志，128例完整owner/2800次请求原版对照通过，浏览器分别检查失败自机请求0、成功自机请求1。

新增 `result-entry-fade.mjs` 对应73d75..73dcf：独立录像窗口淡入10帧，普通姓名登记30帧；保留已有颜色、当前alpha和其他未写字段。此前通用ResultNameScene构造器固定黑色30帧，现已修正并明确standalone初始化。1512例完整56字节原版淡入比较通过，包含空指针、状态/模式门禁和高位颜色字节；Practice17使用独立入口，排除。普通姓名输入96场景/2784帧和完整结果/录像列表64场景/25376帧回归通过。完整原版任务/缓存/字体/GPU/音频以及整作所有模式仍未完成，目标继续active。


本轮最终应用快照的浏览器回归：ID0失误13检查点、ID5首次收取13检查点、ID5已收取13检查点、全一面收取提示14检查点，分别保存在 `th06nc-spell-host[-capture|-known-capture|-complete]-browser-verified.json`。均确认独立录像窗口淡入长度10、隐藏结果clock+20与完整战斗摘要冻结；失败自机请求0、成功自机请求1。全收取关卡选择图和失败结果图已检查。普通结尾/Staff/Result/拒绝录像/CLRD提交/重载回归通过3390帧、32段文字；它使用已披露previewEnding受控交接，并不替代Standard自然通关。当前所有相关Native和浏览器报告仅支持其声明范围；旧源哈希报告继续保留为历史证据。


### Music Room 原始曲目、独立菜单与实际应用接线

本轮从 `th06MD.dat/musiccmt.txt` 读取原始18曲目录：文件982字节，SHA256 `b30076a2732e9460a9993c01182b30fb47105c6bfc18c580968b6783c43472c9`；归档SHA256 `9ceefcc3ad19625078eda0ada6402c4888068ba47fd4f84e63e72e215b8d30d3`。`tools/th06nc-music-room-prepare.mjs` 可重新从只读原归档抽取并检查Native证据；`th06nc-game-texture-prepare.mjs` 现包含原始 music/music00 DDS，其哈希继续与已有Native DDS证据核对。

新增 music-room-table/state/update/initialize/description/draw/scene 组件。58b50曲目解析按原始字节写入0x1080分配，每项0x84字节，标题键0、说明键0x22、路径0x44。没有额外写入终止符，保留原始目标字节；2010个Native完整分配/返回数量比较通过，涵盖原文件全部前缀、CR/LF组合、截断项、32项和有界字段覆盖。

57f30菜单控制与584a0外层计时在2934组Native完整0x3d18对象、56字节fade、退出全局和18012请求比较中通过。上/下只接受边沿，两个方向同时按下按原版顺序处理，十行窗口与首尾换页保留。确认一个未在游戏内播放的有效曲目时，第一次只显示MD_LOCKED_DESC；再次确认同曲即可播放并显示说明；移动光标清除这次确认记忆。它并不禁止播放未解锁曲目。X开始30帧退出；返回条件是unsigned exitClock>=30，独立于fade是否已达到mode2。此项只控制ANM、说明/音频服务和UCRT扫描边界，不能算原生可听输出或画面证明。已有music-unlock原版回归也通过；应用播放音乐室曲目传ownerState9，因此不会修改MUSC解锁位。

原始资源 music.anm(slot69/base7d5)、music00.anm(46/100)、music01.anm(47/101)、music02.anm(48/111) 及IN text/anASCII已连接。58cc0初始化比较24组完整对象/fade/480请求，实际运行六个背景/标题ANM和原始曲目解析；控制资源加载、路径扫描、本地化、字体度量、说明和平台成就服务。59490说明发布尾部比较42组完整对象/232字体请求，涵盖中/日/英、空行、CRLF和超过16行截断，包含原版pure VM reset的visible和clock=-1字段。该尾部的getline向量、本地化和栅格度量仍是供应输入。

58630绘制比较756场景/20088顺序VM请求，完整保留对象和ASCII队列逐字节匹配，数字使用实际UCRT格式化。覆盖背景0/2/4/3层及最后1层、前后十行窗口、逐行三帧延迟/18帧三次方入场、正在播放白色标记、选中闪烁、编号/箭头与ASCII缓存容量边界。最终GPU提交受控，不能称原生像素等价。

标题state21在frame>=50交接Music Room(gameState9)，没有另加fade完成门禁；与Score/Credits相邻原版交接分支共72例检查通过。TitleScene与common owner现支持21，共2736组公共推进原版检查通过。实际应用异步准备原始18首默认bgm、音乐室ANM/字体和曲目表，然后运行独立MusicRoomScene，退出后重建标题。

`tools/th06nc-music-room-browser-check.mjs` 通过11个物理按键检查点：从实际标题进入、18首原始解码音乐、首次警告/二次播放、原始中文说明、导航不改说明、首尾翻页/十行滚动、长按不自动重复、精确30逻辑帧退出、标题音乐恢复。首次进入只解锁标题曲；在音乐室播放第二曲后MUSC仍为1且成绩文件字节未变。独立原版格式MUSC127控制种子/页面重载后，验证七首已解锁、直接播放及Achievement22 award/commit请求，并再次检查无成绩写入。平台成就持久化尚未实现，不把请求当作完成。入口、剧透警告截图已查看，原始画面与中文文字正常。证据 `th06nc-music-room-browser-verified.json`，截图 `artifacts/th06nc/music-room-browser/`。

当前覆盖默认bgm音乐室；bgm2音轨切换/配置owner、完整异步请求/缓存/解码器/混音器、原生任务/资源生命周期和GPU/字体像素等价仍未完成。Score、Options及其他整作未完成项继续推进，completeGame=false，目标保持active。


### Score 标题入口、排行、符卡记录与隐藏解锁

标题state12现在按原版frame>=50交接gameState6，载入原始Result/Difficulty/Text/ASCII资源，创建独立ScoreScene。沿用完整0xbb48 ResultState，普通游戏Result的资格检查和姓名录入不参与本入口。读取已有HSCR表及原版CATK/CLRD/PSCR数据；正常浏览没有成绩写入，只有原版dirty字节置位后的退出才提交规范成绩文件。common title推进扩大到state12，2832组/373824个VM原版比较通过。

`score-menu-update.mjs` 实现根菜单state0/1，原始6e3a0整函数2016组完整对象/fade/声音比较通过。七项含五难度、符卡记录、返回；X只选择返回项，Z确认后38主VM与背景执行退出中断并黑色30帧淡出。入场clock20从state0落入state1，同帧仍处理输入。原版脉冲alpha和Up/Down顺序均保留。前131个符卡ID无条件列出，131..133仅在普通attempts>0时加入。

`score-rank-update.mjs` 对照原版1440组，覆盖五难度、四组角色/Standard/Challenge、tick20双侧标签发布、tick30后左右导航、左优先、重复键、X返回和保留组选择；Lunatic额外生产者单独验证。`score-spell-update.mjs` 对照648组，涵盖空/一/十/十一/131/134条、末页、tick20延迟名称发布、未知名称、本地化回退、tick30后翻页及保留页码。两项均执行原版完整6e3a0和真实ANM/公共时间尾；C++本地化及glyph度量为供应服务，不能视为原生字体证明。

`score-secret-unlock.mjs` 对照真实6e020/6e190共7360组，比较完整Result对象、96字节CLRD和声音队列。Lunatic页输入classiclager，以八个物理字母键的上升沿推进；错误输入按c前缀重启。隐藏手柄组合以独立原始位输入复刻并测试，但浏览器尚未提供原生手柄输入owner，不能称手柄应用验收。成功只把四profile中两模式/五难度完成字节置99，保留记录头/尾，排队声音28并置dirty9e99；普通按键不触发保存。

共同`result-replay-draw.mjs`扩展Score根/排行页，1872场景原版全Result/ASCII对象、顺序VM与UCRT格式化比较通过。`score-spell-draw.mjs`实现view8的十行记录，288场景比较涵盖隐藏/入场、首末页、未尝试/已尝试/已收取颜色、名称偏移、编号缩放、原始难度sprite和捕获率。名称与编号的float32位置、临时ASCII缩放恢复、前后景请求均比较；不宣称GPU像素等价。

`tools/th06nc-score-menu-browser-check.mjs`通过11检查点，全部使用实际物理按键：从标题进入、排行模式/角色首尾环绕和记忆、131条符卡第一页与第十四页/页码记忆、正常浏览字节不变、精确30逻辑帧退出、Lunatic隐藏键序列、CLRD提交后页面重载仍全部99。解锁Extra后标题会导航经过Extra项，测试按实际选择导航到Score。实际原始ANM/DDS、中文标签、ASCII、普通排行与符卡页截图已查看。报告`th06nc-score-menu-browser-verified.json`，截图`artifacts/th06nc/score-menu-browser/`。Music Room随后回归11检查点通过。Options/config、自然Standard/Extra整作通关、原生任务/资源生命周期与音画/字体等价仍未完成；目标保持active。


### Options / 配置原版定位与当前实现边界

本轮纠正早先handoff的命名：标题state23/gameState11的原版生产者是13510，其初始化14510读取data/credit.json及data/title/credit.png，属于Credits；并非Options。`title-menu-handoff.mjs`现返回openCredits，72个原版交接检查已重新通过。真正Options在标题state4(490d2)，显示设置子页state7调用4dc90，按键设置子页state6在49acc..4aa92。Credits实际应用入口仍待接入，没有把命名修正当作Credits完成。

`config-file.mjs`按7b92b..7b9e2的原始判定接收44字节th06.cfg：版本102，字节16<5、17<4、18/19<=9、20<=1、21<5、22/23/24<=1。十个按键字节和未验证尾部不擅自归一化。接收时复制原始44字节并清byte40，运行时十字节按键owner取输入0..9。7bad0恢复默认保留确认/取消互换byte22、名称32..39和byte40，按键取当前runtime十字节，不从文件猜默认键。实际原版3901个长度/版本/字段/尾部用例及256组重置逐字节比较通过。

th06.env是独立12字节记录，7b9f4..7ba5d要求版本102、byte4<3、bytes5/6/7<5、byte8<=1；接受后保留全部12字节。3092个Native长度和逐字段枚举用例通过。此报告只覆盖配置有效性/接收和重置，不覆盖文件I/O、启动顺序和浏览器持久化。原始文件保持只读。

`title-options-update.mjs`复刻state4导航、九项主选项/五组值的原始menu-item presentation，32帧后左右边沿/重复、X选择返回、左右+X输入顺序、音量0..9边界、残机/炸弹值环绕、曲库切换、恢复默认、返回标题及显示/按键子菜单交接。2592组实际490d2..49acc原版检查通过：132个已初始化VM逐字节比较，共342144个VM；选项状态/时钟/配置44字节、声音与有序外部请求匹配。原始navigation/menu-item helper及sprite绑定、config reset实际执行；音乐/音量应用/文件写服务受控。返回主菜单的10帧门禁在inputDelay(1687c)，而不是common inputCooldown(1686c)。目前尚未接入TitleScene，state6/7主体、实际配置消费/持久化、绘制与浏览器验收仍需继续。

后续原版入口：Options state4=490d2..49acc；按键state6=49acc..4aa92；显示state7=4dc90..4e87c；配置loader=7b5d0，cfg reset=7bad0，cfg writer=7ba70；环境记录在c21dfc，44字节cfg在c21da4，运行时十字节按键在a6ec50。初步反汇编留在tools/tmp/th06nc-options-*，不能将这些未验收文本当成实现证明。修正handoff命名后实际Score浏览器11检查点重新通过。


### Options 三页实际接线、公共入场与配置消费

`title-display-options.mjs`实现state7的完整4dc90..4e87c。按原始[1,0,2]顺序切模式，mode1跳过尺寸项；三模式各自保留尺寸值，mode0跳过自动尺寸0。绘制五行根项、三模式、五尺寸条件可见性及二值显示标志；32帧后接受左右/X/Z输入。返回时只比较进入时快照的当前模式、当前生效尺寸、显示标志，真正变化才发平台重建和环境写入请求；不因非当前模式尺寸改变而误重建。2880组原版检查逐字节比较132已初始化VM、配置12字节、状态/时钟/声音与有序平台请求，共380160个VM。平台显示flag/模式重建和文件写API受控，不能据此证明原生窗口/垂直同步生效。

`title-key-options.mjs`实现state6的49acc..4aa92，实际配置的是控制器按钮，不修改Z/X等固定键盘输入。原始候选码为[12,13,14,15,8,9,16,17,6,7,4,5]，静态默认[12,13,9,14,4]。原始Xbox/PS/NS图标资源slot65/base787现已准备；三资源的DDS均按既有独立Native哈希验证，game纹理清单73项。读取独立18字节按钮owner，优先第一个候选按下值；只有按钮索引与全局previous不同且选中五个动作之一时重新分配。原始4d310交换规则对第1/3动作保留例外；负绑定隐藏图标，确认/取消固定按钮与动作预览避免重复。byte22控制固定确认/取消互换，恢复普通配置时保留它，恢复控制器配置时清零它。返回原生按钮码写入44字节cfg前十字节及运行时十字节owner。3840组/506880个VM对照通过，包含未分配、重复动作、按钮优先/上次值、互换动画、默认、提交。Xbox图标绑定、navigation及4d310实际运行；输入API/设备查询供应，不能称实际物理手柄证明。

新增`title-options-entry.mjs`对照4cbf4..4cd1a：进入根Options首先清除九组中断，再逐帧发原始九组入场；返回主菜单的10帧inputDelay结束时释放背景51..69中断。594组/78408个VM比较通过。`advanceTitleOwnerCommon`扩大state4/6/7，并按原版修正logo在Options组进入/离开时的中断3/2、首次frame1延迟、Options背景30帧请求3和返回主菜单6/2组合。3264组/430848个VM比较通过。旧Common fixture的重复before快照改为单份同值baseline，保留全部场景，避免Node单字符串超过512MB；未减少验收范围。

TitleScene现接入三页、原始图标切换、0x80ffffff非选中色、公共入场和原始背景推进。GameSave使用独立IndexedDB键gameConfig/environmentConfig存44/12字节，启动按Native规则接受或恢复默认，运行时按钮取接受cfg的前十字节；Options退出分别提交cfg/env，显示页发生实际生效配置变化时先提交env。残机/炸弹传给既有gameplayStartSettings，Challenge/Extra/practice原始固定库存规则仍由该模块处理。音乐/音效音量消费配置18/19，原曲/改编曲配置20选择bgm/bgm2并实际解码重启；MUSC必须先处理原始incoming路径再替换transport路径，原始7bcf4..7bd7e共104个前缀/复制/UTF8路径用例通过。显式bgm2路径不会被错误改回bgm。

`tools/th06nc-options-browser-check.mjs`通过10检查点：真实物理键进入Options，改变残机/炸弹/音量，实际bgm2/bgm标题曲重启，显示子页切到mode0/尺寸4、请求标志改变和1280px maxWidth适配，控制器图标/确认取消互换，供应标准浏览器手柄的按钮2后真实配置生产者分配为原始按钮14，返回提交cfg/env，完整页面重载保留原始44/12字节及runtime绑定；随后正常菜单确认进入Standard并实际起始lives1/bombs0。浏览设置不改变score.dat。截图`artifacts/th06nc/options-browser/`，报告`th06nc-options-browser-verified.json`。已查看根菜单与控制器图标页面；这些画面尚未经过原生像素比较。

浏览器窗口适配将原生尺寸选项映射为页面maxWidth，并在非窗口模式申请浏览器Fullscreen；失败保留在report.display.fullscreenError，不能把请求当作原生exclusive fullscreen完成。显示flag目前只记录请求，浏览器/native垂直同步、完整窗口尺寸裁剪/设备重建仍未验收；原始键盘/物理手柄完整输入映射、配置姓名字段与原版任务/资源生命周期、音画/字体等价继续待办。默认与重置原生cfg的byte22实际是确认/取消互换，先前“display selector”注释已纠正。Credits实际入口、Boot和自然Standard/Extra整作验收仍未完成，目标active，completeGame=false。

本轮最终源码回归：Options10、Score11、Music Room11、标题取消14、符卡自然收取13检查点均通过；符卡仍保持战斗池/计数/RNG冻结、录像保存/返回等既有范围。原游戏score.dat SHA256仍为44805e2691e6d208290a9ecdbe3eec26d7d1a7ddb6e84ca21d2a502732609441，th06.cfg仍为2736fe712f0e49ca25b6dc2944c3e804b976dc484ab91dfb7dffc7882ceaacbc，只读未改。下一步物理手柄输入生产者12be0/12b40、映射消费与显示平台行为，随后Credits与剩余整作验收。


### 完整键盘输入、控制器包与配置映射实际消费

新增`input-sample.mjs`，键盘前缀12d69..13019按原版读取扫描索引并合成完整位，不再按网页phase丢弃额外输入位。Z/J=8101、X/K=202、Enter=100、LShift/Space/L=4、LCtrl/分号=8、R=4000，W/A/S/D与小键盘方向/斜向保留原始位（S=1020、Esc=600）。2166组Native键盘读取/完整mask比较通过，含每键四种原始字节、组合及2048个确定性混合输入。布局表/物理键盘API为供应边界；不能把固定浏览器KeyboardEvent.code适配当作所有系统布局证明。

127d0控制器合成通过6012组原版检查：返回完整mask、uint16共用射击/低速计时、raw secret bitfield全部匹配。配置前五个int16映射shot/bomb/focus/skip/pause，负码不映射；固定确认/取消取决byte22，并保留配置动作与固定菜单键冲突时的抑制规则。射击/低速共键时按住第8tick才产生focus，最多记16（已有超范围uint16保留原版比较），松开按原版8阶衰减。触发器原始byte>=30视为按下；左摇杆半径平方float32必须严格>100000000才给方向。正常gameState2且非暂停/失败/符卡结果时方向锥额外0.30543264746665955；其他状态使用原始45度边界。CRT atan2供应双方相同float32角度，不声称libm等价。控制器断开保留原版focusClock/raw secret全局，仅返回键盘mask。

实际平台分支a9fd0返回26字节（16个数字键、两trigger byte、四个int16摇杆轴）。`browser-controller.mjs`现构造完整26字节及18字节阈值按钮view。继续追踪原始XInput提取adc0c..add6a后纠正了早期推断：Start=code4、Back=5、L3/R3=6/7；不是Start/Back=6/7。原始控制器配置默认Pause=4，因此网页现在使用Start暂停。隐藏解锁前两键码6+7实际为两摇杆按下。候选列表12/13/14/15为face，8/9为shoulder，16/17为trigger。16727个原版完整26字节比较通过，覆盖16384个数字按钮组合、trigger临界值及正负int16轴；浏览器轴fixture明示按正32767/负32768归一化，不能外推所有浏览器驱动归一化完全一致。

Game.sample现在每逻辑tick调用真实键盘合成+控制器包合成，Options按钮扫描仍读取独立18字节view。新局从保存cfg消费映射；暂停以完整采样mask的400上升沿打开，不再在keydown回调另开一次。异步符卡结果/失败交接沿用最近采样mask，避免额外调用sample推进共键计时。ScoreScene现收到同一输入生产者的raw secret位，原始按键和手柄解锁分支均可从实际应用到达。输入report只读暴露mask/focusClock/secretMask/connected；manual显式mask仍是既有受控测试入口，未替换正常物理采样。

`tools/th06nc-input-browser-check.mjs`通过17检查点，重跑完整Options编辑/保存/重载及Standard实际库存后，供应标准浏览器控制器：A按保存配置只产生cancel/skip而不射击，West按真实重复分配交换结果产生8101并创建真实自机弹；摇杆0.2在死区无位移，0.4产生右移及实际位置变化，Start按保存Pause映射打开暂停、B按已保存confirm/cancel互换恢复。物理J/K/L/分号/W/小键盘9/R输入mask全部检查；重载后从标题进入Lunatic Score，L3+R3、North、West、双shoulder序列实际置CLRD99和dirty。测试修正了按键重新分配同时交换Skip的真实结果，并未强令预期配置。受控navigator.getGamepads输入不等于物理手柄硬件验收。

新版全键盘还意味着在Lunatic输入classiclager时A会按原版横向切排行并重置页clock；Score浏览器验证据此等待原始30帧门禁后返回，没有绕过真实输入。最终Score11、Music Room11、标题取消14、符卡自然收取13检查点回归通过。目标保持active；真实设备/驱动、完整键盘布局/API前缀、display平台/vsync、Credits及剩余自然整作/原生生命周期与像素音频验收仍未完成。


### Credits 制作名单与 Quit 完整入口（2026-11-17）

标题第7项现在实际进入Credits，state23/gameState11；先前openOptions名称只描述旧占位交接，已更正。原始TL归档credit.json保留14页（含空字符串/空页），44个文本VM按每页22行、一次两页呈现。credit.dds为1920×1080 BC7，SHA256 e5c22bfa03adc24fc990c6801637854ec5669eb49f8d2bd1e2d39440fd61bfe2；credit_4k.dds也只读提取并记录哈希，但原生质量选择尚未等价验证。原始JSON解析/C++ vector构造为供应边界，不声称原生解析器完成。

credits-state/update/draw/scene实现完整0x31c8 owner：原始14ac1..14c8c初始化尾段16组、13790..13bee更新3045组通过全owner/fade56字节/有序字体请求/声音/返回值比较，状态摘要765092492ea7364cc44823fa0a487dd0a1e45596cc6aedc09f044e322a5fc4ef。包括8帧入场、左右edge优先级、两页环绕、五帧滑动、44行揭示、72帧脉冲、X触发30帧退出及退出期间冻结其他时钟。13bf0绘制2916场景/131220请求通过全retained owner、ASCII owner和有序VM/背景请求；摘要d6f370e539b8f5ad915c8500d213cb702c19827932b423a36f9cc61a0741ea8a。f32缩放/立方滑动/行揭示透明度、旧新页脚、页码宽度/奇数末页空位由原始UCRT格式化对照，绘后恢复原始VM状态；背景78a0只观察调用，GPU像素/后台缓存和任务生命周期未建立。

字体原始primary=0xfffffe为无语言后缀的英文缓存。font-publish已按原版处理这个sentinel；完整原生7530字体发布360组通过（270绘制、90缺失），使用受控7d2c0度量/字体服务，不能外推GPU/实际字体栅格一致。网页载入实际英文atlas，保留原始颜色[0xfffffe,0,0x10101,0x40202]。

Credits实际浏览器8检查点通过：物理键标题进入、14页44VM、英文首屏、slide0/2/5、中间页、末页/空右页、按住仅翻一次、30tick退出、重开归零、标题音乐连续和score文件不变。截图artifacts/th06nc/credits-browser/first.png已查看，布局可读；像素未与原生画面比较。

Quit标题第9项及物理Q均进入owner5；原始4c198..4c1c7须clock>=50且存在fade.mode2才写desiredGameState4并结束标题任务。handoff原生216组通过，含无fade及mode0/1/2/3、临界帧和原有Score/Music/Credits分支；公共标题推进扩到state5/23后3456组/456192个VM通过，摘要0ece1d4ca313afbd6b530dfa2add982c90a6338ef8c974fc0a6562a86fc0ae58。网页退出提交44/12字节cfg/env、停止声音和音乐、冻结逻辑更新，并显示返回标题按钮；保留浏览器标签页属于平台适配，不代表原生进程/任务/资源销毁完成。实际浏览器7检查点通过两入口、49/50帧门禁、各配置独立提交、score不变、120tick冻结及重新进入标题。

本轮最终源码回归：Credits8、标题取消14、符卡自然收取13检查点通过。此前Score11、输入17也在Credits接线后通过，Quit后的当前源码范围以各报告哈希为准。原版score.dat/th06.cfg只读；目标保持active、completeGame=false，继续原始boot/splash、自然Standard/Extra全通、显示/设备输入边界、cfg姓名字段和原生任务/资源/字体/GPU/音频生命周期验收。


### 配置姓名原版读写与网页持久化（2026-11-19）

config-name.mjs对照原始7bb80读取和7bc00..7bc2b写入前缀：2048组全44字节配置/9字节姓名比较通过。读取限制8字节，ASCII32..126外字符显示为空格，遇NUL后剩余填空格，byte8终止；写入先清cfg32..40九字节，再strncpy8，不过滤原始姓名字节。CRT memset/strncpy为明确供应服务，未验证原生文件分配/排队/线程。原始binary和磁盘cfg保持只读。

GameSave现在优先从有效44字节cfg读取姓名；旧lastName-only存档在内存配置中迁移，后续配置写入可持久化。姓名提交将姓名字段和完整44字节配置放入同一IndexedDB事务，成功后发布内存结果，不再只写独立字符串。浏览器9检查通过cfg优先、NUL显示过滤、8字节截断及byte40 NUL、邻接字段保留、全配置重载、旧存档迁移及score不变。启动原版state0/1/2与4d370已定位，冷启动资源/首次过场尚未接入，目标继续active。

配置姓名接线后最终回归：Quit7、符卡自然收取/录像/返回13检查点通过；原始score.dat与th06.cfg SHA256保持未变。


### 冷启动标题初始化分支与主菜单交接

扩展title-selection-return中的原始4d370..4d67b helper，startupOverlay非零时保留过场VM，设置state2/frame0、inputCooldown60、背景counter170，清warmReturn/mainFastEntry，保留其余原始标量。原有返回标题的359帧预推进维持原行为。4801b..48174交接现按mainFastEntry选择背景51..69中断6/2，按startupOverlay或fast决定十项菜单中断28与entryHold，并保留cold的warmReturn=false。

原生对照扩大为30个cold/warm场景，检查完整132个VM、40字节背景control、counter与相关标量，两个阶段共7920个VM比较通过，另有6组返回判定。标题返回实际浏览器14检查点通过。该轮验证入口helper及确认后的状态交接；首次确认的30帧输入门禁、异步启动等待、cold绘制及应用冷启动接线继续待办。


### 冷启动标题实际接线与确认门禁

正常网页boot现在通过coldStartup进入原始state2过场。returnToTitle的普通调用继续原有返回行为。TitleScene的state2使用原始47f6a..47fa2门禁，frame>=30且held&1f00非零并与previous&1f00整体不同才进入，mainFastEntry绕过等待。12288组原版门禁比较通过。冷启动确认前缀恢复背景透明度，按剩余counter处理三层，活动fade按760c0从当前alpha以8帧淡入，保存24帧缩放起点。冷/暖初始化和交接扩到120组，含fade mode0/1/2/3的完整56字节比较，共31680个VM比较通过。46e50的24帧缩放独立600组原版float32对照通过，实际公共更新按原序在菜单VM之后执行。

新增cold-title-browser检查，正常页面进入state2，frame29按确认及frame30继续按住均保留过场，空闲220帧仍等待确认，物理Z进入state3/frame1，等待入场后再次物理Z进入难度菜单，6检查点通过。已查看prompt截图，使用原始标题资源与背景。现有浏览器工具在360帧预热后若state2则显式确认，以经过正常首次入口。标题取消14、Quit7、Credits8、符卡自然收取/录像/返回13回归通过。原始启动worker/资源调度、独立splash、平台/GPU像素全等价仍待验证。


### Standard Easy灵梦A自然续关全通

新增standard-natural-browser-check，从实际Options把初始残机调到最大4，原有炸弹3，正常标题选择Standard/Easy/灵梦A。控制脚本只提交方向/低速/射击/Bomb/跳过和真实菜单输入，读取只读hazards的子弹/激光/道具几何来操作；运行时未赋值敌人HP、存活库存、分数或完成标记。自然通过stage1..5、原始MSG结束请求、结局和Staff，使用2次正常续关，共2352个结局帧，最终score.dat51636字节保存/页面重载一致。续关后的结果state11禁止保存录像、确认返回标题、无录像文件均检查通过。HSCR保留Standard模式stage99，primary CLRD未标记99，secondary CLRD99符合原始受限通关规则。

本次自动操作曾在二面和四面耗尽库存，补充激光/道具观察、原始deathbomb输入与实际Options/续关路径后完成自然通关。该结果为续关完成范围，一命全通和其他角色/难度继续待验。报告th06nc-natural-run-reimu-a-difficulty0-standard-browser-verified.json记录完整源码快照，不把早先失败尝试计作通过。后续修正冷/暖标题helper必须清零遗留缩放起点和计时，原生240场景验证包含先前计时17的状态，63360个VM比较通过；Easy通关报告的历史源码边界按source-current-audit保留。


### Extra Challenge自然全通及完整录像

extra-natural-browser-check使用原始格式Normal-clear解锁存档作为前置，再实际选择Extra/灵梦A/Challenge。全程按住射击/Ctrl，未调用MSG11完成预览或改写战斗对象，原始ECL/STD/MSG自然推进至Extra Boss结束、黑色退出过渡和实际Result，HSCR的Challenge/Extra条目stage99。最终score.dat51636字节、完整录像188字节保存并页面重载一致。Challenge中累计实际miss超过120，按原始生命保护规则保留存活；Standard Extra和自然解锁仍需独立验收。

扩展natural-playback工具--extra，导入该自然录像，经实际标题文件/关卡列表选择stage7，使用记录的绘制帧序列回放到自然返回关卡列表。26个检查点匹配全部七类原始对象池、玩法计数与RNG，最终score11800090一致，录像字节不变且未写score文件。报告th06nc-extra-natural-reimu-a-challenge-browser-verified.json和th06nc-natural-playback-reimu-a-extra-browser-verified.json。

Normal魔理沙B自然测试达到五面，耗尽三次正常续关进入GameOver/成绩，尚未通关。该失败日志保留在tools/tmp/th06nc-standard-normal-marisa-b.log，未生成通过报告。自动操作改进预测避让、Boss接触范围与Power道具优先级后，继续验证Standard Normal角色。标题/系统迁移整体completeGame仍为false。


### Standard Normal自然全通与原版标题窗口观察

Normal灵梦A的自动输入改为每2帧观察一次普通子弹/激光/Boss接触范围和Power道具，并保留正常deathbomb与续关输入。自然完成stage1..6、原始结局和Staff，使用2次正常续关，结局2352帧、score.dat51636字节，受限CLRD/HSCR、录像禁止、返回标题及页面重载检查通过。Normal魔理沙B先前达到五面，灵梦A先前达到六面后失败，均未冒充通过；通过报告为th06nc-natural-run-reimu-a-difficulty1-standard-browser-verified.json。工具明确记录输入策略源码和实际推进帧数，避免把deathbomb期间2帧输入计作6帧。原有成绩/录像Codec复核新增自然Standard Easy与Extra文件后分别53/31文件通过，后续Normal文件也将加入。

按computer-use技能在artifacts/th06nc/native-observation-20261119隔离目录运行原版副本，数据归档以目录junction只读使用，cfg/env/score与EXE/DLL使用本地副本。实际观察冷启动等待画面、Z进入主菜单和Q淡出退出，原版目录score.dat/th06.cfg SHA256继续保持原值。原版English图形与网页中文/默认低分辨率资源的完整像素/语言/质量选择尚需继续对照。

修复GameRenderer.title底色，原始5498f..54999在背景VM分支先请求白色全屏矩形，再执行5499e后的背景绘制。网页此前使用默认黑底，导致半透明背景变灰。现背景启用时清白底，选择页/其他背景分支保留各自绘制。冷启动6、标题取消14、Quit7检查点通过，prompt截图背景抽样接近白色（253,248,246等），已重新查看。该修复不声称完整GPU像素等价。


### 原始语言资源解析、中文贴图与异步持久化边界

新增localized-asset.mjs，对照原始387a0归档文件读取器的名称选择部分。先按最后的斜杠或反斜杠取basename，在最后一个点之前插入下划线加语言（无扩展名则尾部追加），先遍历所有16个归档的本地化名称，再遍历所有16个归档的基础名称；第17槽不参与，重复名取首项。bypass保留完整路径，交给独立文件服务。2496组原版对照通过，覆盖13组语言值、混合分隔符、Unicode、点文件、多扩展名、无扩展名、本地化优先于早先归档基础名、重复项和文件服务分支。实际字符串名称比较/查找循环执行，C++ string与CRT字节操作/实际解包为控制服务，scope按报告明确记录。

localized-textures-prepare按原版DDS独立哈希准备31张中文资源，170个已准备纹理名称写入localized-manifest.json；本地化与基础图尺寸全一致。GameAssets使用同一解析模块选中文贴图，字体语言继续zh-CN。标题截图现显示原版中文“东方红魔乡/新典”资源，标题/选项/其他界面的语言资源按真实可用文件回退。冷启动6、输入/Options17、Score11、Credits8、符卡自然收取13检查点通过。后来修复同名纹理并发上传与失败重试，独立WebGL2上下文4检查点验证并发仅建一张GPU纹理、双消费者一起失败且不分配、重试共享新纹理、manifest失败清除缓存后恢复。原生缓存/设备/任务生命周期不由此建立。

配置写入使用独立串行队列，姓名提交成功后只发布cfg32..40九字节，避免旧44字节快照覆盖提交期间的新Options字段。新GameSave实例下姓名FIRST、配置音量8、姓名SECOND重叠提交后RAM和重载均保留SECOND/8；真正abort事务保持旧姓名，随后RECOVER成功。配置姓名浏览器从9项扩到13项，输入/Options17和符卡自然收取13回归通过。失败重试操作仅在测试独立IndexedDB库，原始文件只读。

Extra前置现使用真实物理键进入Lunatic Score并输入classiclager，按原始确认/保存路径解锁，再从标题实际选择Extra Challenge。自然完整战斗、结果、录像/成绩、完整回放26检查点通过，不再使用人工Normal-clear存档前置。该口令是原版功能，尚不声称通过无续关Standard成绩获得解锁。其余三组机体和射击组合正依次自然验证。


### 2026-11-19: title configuration publication and Extra acceptance

Original title decision owners publish difficulty to cfg byte21 and mode as a word at byte23 (clearing byte24); byte24 is not a persisted practice-stage selection. Character/shot globals remain session state. TitleScene now publishes the same fields and retains character/shot across title reconstruction, while fresh application boot resets those session globals. Full44-byte configuration comparison passes1152 native cases. Actual physical-key browser coverage passes7 checkpoints through Lunatic/MarisaB/Challenge selection, cancellation, Credits return, ordinary Quit configuration commit and fresh reload. Input17, spell13 and cancellation14 regressions pass.

All four Extra Challenge profiles now use the actual physical classiclager secret/Score-save/title unlock path, then naturally execute stage7 ECL/STD/MSG/Boss/result with ordinary held shot/Ctrl inputs. They save/reload original-format score and188-byte replay, then launch the complete saved replay from the actual title. ReimuA/B and MarisaA/B match26/26/24/25 checkpoints respectively (101 total), comparing seven complete raw actor pools, counters and RNG at recorded draw cadence, exact final score and natural stage-list return. The matrix passed on the title-configuration source snapshot; later runtime integration changes retain that report as historical evidence. This proves neither a Standard Extra clear nor an earned no-continue normal-clear unlock. Updated actual-file native checks pass57 score files (decode/re-encode) and34 replay files (decode); full native filesystem/task ownership is excluded.


### 2026-11-19: local achievement platform boundary

Added GameAchievements as a local IndexedDB replacement for the native platform award/StoreStats service. It preserves separate award/commit calls, merges independent writers in one read/write transaction, publishes unlocked keys only after transaction completion, retains pending keys on abort, retries without poisoning the queue and reloads independently. No Steam/network calls or native platform equivalence are claimed. Fourteen actual-browser checks pass, including unchanged score/config bytes and transaction abort/recovery.

Runtime now supplies the service to StageWorld (message progress and deathbomb), EndingScene and score-name completion, and consumes MusicRoom's ordered initialization requests. Actual MusicRoom7-unlocked fixture verifies Achievement22 persists in an independent GameSave; existing11 physical-key checkpoints pass. Controlled ending/Staff/Result flow verifies script/profile/difficulty/Challenge achievement publication and passes3390 frames,32 text lines plus score/reload. Spell ID5 natural capture/replay/retry regression passes13 checkpoints after initial service integration. Two formerly missing producers are now decoded: title post-fade ordinary launch (launchFrom14) awards01; end of gameplay initialization scans all134 CATK uint16 attempts at+3c, awarding23 only when every slot is nonzero. This includes three slots outside the131-entry practice catalog and does not use captures or practice attempts. Original executable comparisons pass32 title cases and405 CATK-loop cases; actual initializer and natural Extra checks are being run. Remaining natural all-card encounter/secret Extra acceptance and external platform integration are unproven.


The actual initializer fixture passes5 checks through physical title-to-game launch, canonical score seeds and independent achievement reload: first133 encountered slots do not award23; all134 with zero captures do. Extra Challenge ReimuA subsequently passes the full natural clear/save/reload with local01/08/21 retained, and title-launched complete playback matches26 raw-pool/counter/RNG checkpoints, final11800090 and naturally returns without writing local achievements or score. The source guard rejected an earlier playback attempt because the recorder and playback harness listed different snapshot dependencies; the unified source lists and fresh record/playback pass. No rejected run was published as a pass.


### 2026-11-19: music request recovery and alternate-title cache regression

GameAudio now coalesces concurrent requests for the music metadata and for an identical track into one read/decode operation. Failed metadata or real audio decoding clears the in-flight entry and permits retry. Five checks use actual original prepared Ogg bytes and a separate real AudioContext, verifying one read/decode for three consumers, invalid-audio rejection for both consumers, retry, metadata failure/retry and unchanged source/handle on repeated active-track play. This is browser resource management, not native PCM decoder/mixer/cache equivalence.

A physical Options-to-stage regression reproduced an existing crash: alternate music enabled, Stage1 Pause confirmed restart, then Pause confirmed title return threw music-not-prepared for bgm2/th06_01.opus. Stage preparation retained only the default title track when evicting other buffers. Both default and alternate title tracks are now retained. The same physical flow passes4 checkpoints after the fix. MusicRoom11 and audio-cache5 regressions pass; input17, title-config7 and spell natural-capture13 passed after the request coalescing change. Original native queue408/fade1680/loop39 cases pass unchanged. Refreshed native actual-file checks pass57 scores and34 replays. Original source score.dat and th06.cfg hashes remain unchanged.


Standard Extra acceptance attempts use the actual classiclager unlock path and ordinary shot/focus/directional/Bomb masks, with read-only actor observations. The initial MarisaB run exhausted stocks before clear. ReimuA with the existing Standard bot reached frame20093 and score14042500 but naturally exhausted stocks; failed-attempt-proactive-bombs.json retains its final owner report and hazards. A deathbomb-only variant reached the final Boss and frame24044 with full Power but later GameOver; no pass report was written. Further input-policy work is isolated in tools/th06nc-extra-bot.mjs; production gameplay, collision, stocks, damage and script progression are unchanged. The current alternate-speed policy is still under acceptance; Standard Extra is not yet claimed complete.


### 2026-11-19: correct production player movement rectangle

Standard Extra observation exposed a production adapter error: the native moving-player helper was verified with supplied bounds, but Runtime.openStage passed the full384x448 field. Actual new-run initializer3aa49..3aa71 writes the four float32 values8,16,368,416 at game-owner+d280; therefore reachable positions are x8..376 and y16..432. Added gameplayPlayerBounds from that native initializer and use it in the production StageWorld service. No change to bullet collision, damage, stocks or scripts.

The existing start-settings native verifier now compares these complete16 rectangle bytes in every1152 input case, alongside the existing stock/Power/extend settings and160 initial-Rank cases. A physical-browser test holds each direction120 ticks and restarts via actual Pause/R between bounds: x8/376, y16/432 and unchanged positions after key release pass4 checks with no deaths. The actual ID5 Spell natural capture/result/replay/retry/storage regression passes13 checkpoints on the corrected production bounds. Prior natural runs/replays remain historical source-snapshot evidence; those recorded with full-field bounds do not establish current/native movement equivalence. Current Standard Extra acceptance is rerunning with the corrected bounds and ordinary observed inputs; no natural-clear pass is claimed yet.


Native startup clock and new-run CATK lifecycle investigation: boot7a7fe..7a812 callsb0370/GetNowCount with argument0, publishes low16 bits to global RNG seed and clears its uint32 counter. This exact boundary passes264 clock values, including wrap/error values. New-run3aaf6..3abcd rebuilds all134 CATK defaults, consuming192 next16 values per384-byte record (25728 total), overwrites semantic header/zero counters/score arrays, then actual3ad68 invokes the existing6cc40 CATK loader and3ae2a invokes6ce20 PSCR loading. Eight prototype scenes compare1072 complete records and final RNG seed/count against the executable. These probes are not yet connected to production; fixed startup seed/per-run RNG recreation and missing new-run stat reset remain work items. The bounded natural Extra attempt with the fixed bounds reached54664 then GameOver; a target-alignment variant reached54957 then natural un-cleared result. Neither wrote a passing clear report.


### 2026-11-19: production boot/shared RNG and new-run stat reset

Connected boot clock sampling (low16 seed, count0) to a session NativeRng. New games and restarts use that shared generator rather than recreating0xbeef; canonical menu saves also use it. Browser Date.now supplies the clock boundary (its epoch differs from Windows GetNowCount). New-run ScoreStats.loadRun rebuilds native CATK defaults, reloads committed CATK, then PSCR in the actual native order. This prevents abandoned unsaved spell counters leaking into a fresh run and preserves the accepted PSCR/CATK overlap behavior. Six composed original-executable cases compare the whole shared d2d8-byte stat span, including original read-only score.dat, saturation/scan-stop and alias cases. Boot264 and full-default1072-record native comparisons pass.

Browser acceptance fixtures control only the platform boot clock before page initialization. Clock9909 followed by the native25728 default-record draws produces first-stage0xbeef, retaining the prior deterministic first-run conditions without changing actor state. The first capture attempt using clock0xbeef correctly received a different stage seed and missed; that failed run was not published. ID5 natural capture/result/save/retry and complete saved playback pass13 checkpoints with the corrected clock fixture. Actual physical edge/Pause-R tests additionally verify four shared-RNG restart continuations and stage counter reset. Historical Normal ReimuA Challenge replay still matches108 seven-pool/counter/RNG checkpoints and exact12812130 on the updated runtime, without score or achievement writes.

Before this later RNG/stat integration, all16 ordinary Challenge historical recordings passed current-bounds complete playback,1611 checkpoints, unchanged final scores and no score/replay/achievement writes. The ordinary revalidation matrix retains recording and playback source hashes separately; --revalidate-source bypasses only the source-equality prerequisite, retaining all actual actor/counter/RNG comparisons and recording each changed dependency. The matrix is historical after the subsequent RNG/stat integration; a new successful playback is not described as a fresh recording.

### 2026-11-19: first natural Standard Extra clear

A read-only short-horizon beam planner sends ordinary direction/focus/shot/Bomb masks, reconsidering turns every two ticks. Under the actual physical classiclager unlock/save/title path, ReimuA Standard Extra naturally completed all original ECL/STD/MSG/Boss progression in76517 frames, score29962330, three deaths, one remaining extra life/one Bomb and zero continues. No actor/HP/collision/stock/score/end-state injections are used. Actual Result/name,154724-byte complete replay,51636-byte score and independent reload pass, with local01/08/20/21 retained. Thirty-two raw seven-pool/counter/RNG checkpoints and38234 draw events were recorded; complete title-launched playback is running. Earned normal-clear unlock and natural secret Extra route remain unproven.

Actual-file native score decode/re-encode now passes58 files. The larger movement-heavy replay exposed a verifier instruction-budget issue: the native decoder had stopped before its boundary at the old fixed million instructions. The verifier now scales the bound with file size and asserts the actual final native RIP before comparing normalized bytes. All35 replay files, including the154724-byte Standard Extra recording, pass complete native decoding. No production replay codec change was needed.


### 2026-11-19: complete Standard Normal replay and earned save

The ReimuA Standard Extra recording above passed all32 complete title-launched playback checkpoints with identical final29962330, natural return, unchanged replay and no score/achievement writes. Its acceptance scope does not establish the hidden Extra route.

ReimuA Normal Standard now naturally clears all six stages without continues, two deaths, original ending/Staff and actual Result/save/reload. Stage frames are11238/18088/22046/25721/25242/34746, followed by3336 ending frames. The166668-byte replay completes through all six stages with110 actor-pool/counter/RNG checkpoints, final score20720220 and natural return to the title replay stage list; no score/achievement writes. All raw checkpoint pools are retained as hashed gzip sidecars alongside the natural-run report.

Replay dialogue chain restarts can perform more world updates per displayed draw. Initial strict raw comparisons exposed17 bytes of stale last-drawn VM position in three inactive effect slots. Actual original draw/spawn code proves inactive positions are retained and all21 effect types republish them on reuse. A later item-only mismatch was investigated through actual original spawn/ANM tick/draw: seven inactive cache pairs and21 type/drop-mode reuse cases converge. Comparison copies therefore exclude only the proven inactive effect position and inactive item draw/sprite caches. Active state, item physics, all other pool bytes and all counters/RNG remain exact. Original raw snapshots and every permitted difference are retained; gameplay is unchanged. See th06nc-effect-render-residue-native-verified.json, th06nc-item-render-residue-native-verified.json and tools/th06nc-pool-comparison.mjs.

Actual original-format corpus verification now passes58 score files and36 replay files, including the Normal Standard166668-byte recording; complete native decoder termination is asserted. Browser boot seed/shared RNG checks pass five boundary scenarios.

Extra capture-gate investigation found a production integration error: message opcode14 writes native a6eb90 (timeline resume request), while boss-spawn inhibition is separate native a6ec14. Earlier message progress fixture mislabeled the former as suppressSpawn; isolated byte comparison passed but composed high-capture progression incorrectly skipped the hidden enemy. The prior high-capture CPU report is historical evidence of that incorrect composition, not hidden-route acceptance. Correction and renewed native/composed acceptance follow below; low-capture is the ordinary ending route, not the additional-card route.


The exact score.dat from the no-continue Normal run passes six physical-browser checks: isolated IndexedDB import, fresh reload, only the earned ReimuA character/shot available, real Standard Extra launch at Power0/lives2 and byte-unchanged score. No fabricated unlock or secret code is used in that earned-unlock fixture.

Corrected message opcode14 to publish timelineResumeRequested independently of suppressSpawn. Timeline controller consumes that request only if an opcode13 checkpoint exists; initializer now scans nonnegative-time instructions for the first marker as actual3b48a..3b4a7 does. Shipped Extra has an opcode14 timeline marker, not opcode13, so the request remains pending and the independent inactive-Boss flag permits the next enemy. Eight native flag/checkpoint cases,296 full message branch cases and14610 timeline event/frame cases with both Boss inhibition values pass. The composed full-power/no-collision world now reaches all16 spell IDs118..133 and normal completion at48099, with special frame at39150 and Achievement24; the low-capture eight-Bomb fixture reaches only118..130 and ordinary completion at47263 without gate/24. Neither fixture changes boss HP, capture counters, timers or progression. These are controlled CPU proofs, not natural hidden-route clears or browser GPU/audio acceptance.


The corrected current runtime replays the earlier natural Standard Extra recording through all32 checkpoints/final29962330 and natural title return, with unchanged file/no score or achievement writes. This is explicit source revalidation, preserving historical recording hashes.

The full application hidden-route browser fixture now passes: actual physical classiclager and title Standard Extra launch; first world tick sets Power128 and replaces only player body/bullet/laser collision callbacks in the isolated test. Ordinary input13, original shots/damage/HP/timers and all ECL/STD/MSG naturally reach the high-capture gate at38849, then cards131/132/133, hidden final dialogue and Result. Original ANM/DDS/Chinese text/WebGL and music preparation complete without browser/GL errors; screenshots of all three hidden cards are retained and card133 was visually inspected. Name/result, decline replay, canonical51636-byte score, Achievement24 and independent page reload pass. No capture-counter/boss/HP/script/end-state injection; this is controlled browser branch acceptance, not a natural player clear or valid recorded replay. Report: th06nc-extra-hidden-fixture-reimu-a-browser-verified.json.

Source snapshot audit now covers274 shared modules with196 current and215 historical reports, no uncovered modules; this is coverage only. Original score.dat and th06.cfg hashes remain unchanged. Hard ReimuB Standard zero-continue natural acceptance with raw checkpoint archives is running next.


### 2026-11-19: Standard Hard ReimuB natural acceptance

The first Hard ReimuB run naturally completed all six stages but its acceptance tool rejected end01.end because its old assertion hardcoded shot A for every profile. That run wrote no passing report. The tool now asserts the exact native character/shot good-ending name, or the bad-ending name for Easy/continued runs; production ending code did not change. A complete repeat passes six stages, real end01/Staff3048 frames, actual Result/name, canonical save and independent score/replay reload: final30705070, two deaths, zero continues, four remaining lives/one Bomb. Stage frames12045/18388/24998/28541/24856/35946, replay211764 bytes, score51636 bytes. Raw hashed compressed actor-pool checkpoints are retained. Complete title-launched playback is underway; no playback pass is claimed yet.

Native actual-file corpus now passes60 scores and37 replays, including this Hard recording, with complete native decoder termination. Standard remaining acceptance is queued sequentially on9499: Hard complete replay/earned unlock, Lunatic MarisaB recording/replay/earned unlock, Easy MarisaA recording/replay and current Normal replay. Independently,20 historical ordinary/Extra Challenge replays are being revalidated on two isolated browser ports9500/9501 with unique profiles/artifacts; shared production sources stay unchanged. Each child retains strict raw-pool/counter/RNG/final score and source-snapshot checks; any failure stops new jobs and retains its log. The aggregation report is written only after all20 checks actually pass.


Hard ReimuB complete title-launched playback now passes116 actor-pool/counter/RNG checkpoints, exact final30705070, natural replay stage-list return, unchanged replay and no score/achievement writes. The exact naturally earned Hard score passes six physical-browser unlock/reload checks: only ReimuB is available, locked character/shot attempts stay on that earned choice, and Standard Extra starts at stage7/Power0/lives2 without score changes. The earned verifier also checks actual difficulty/ending/name/stage achievements and that no-miss Achievement19 agrees with the final recorded death count.

All20 historical natural Challenge recordings now pass complete current-runtime revalidation: ordinary4profiles x4difficulties1611 checkpoints plus four Extra101, total1712. Every recording retains its old source hashes; current playback source hashes, every changed dependency, final score and unchanged file/no score or achievement writes are verified. Both20-run and16-run aggregation reports pass against current files. This establishes current replay acceptance, not fresh recordings or native every-frame/GPU/task equivalence. The refreshed source audit has225 current/191 historical reports across274 shared modules, none uncovered. Lunatic MarisaB Standard natural recording is underway.


### 2026-11-20: Standard Lunatic MarisaB and second-character hidden branch

MarisaB Standard Lunatic naturally passes all six stages without continues, real end11.end/Staff3336, Result/name and independent score/replay reload. Final45682410, four deaths, three remaining lives/three Bombs. Stage frames10785/18390/24996/28535/25011/35948, complete replay247488 bytes, score51636 bytes; raw actor-pool checkpoint archives retained. Local difficulty12/ending17/name21 and stage achievements persist. Complete playback and exact earned Extra unlock are running/queued, so no playback pass is claimed yet.

A second full-application hidden Extra fixture uses MarisaB and the same explicit first-world-tick Power128/no-player-collision condition, covering the other character's dialogue/portrait/resource path and actual laser shot damage. All IDs118..133, gate38842, hidden final dialogue/Result, canonical51636-byte score and Achievement24 reload pass with no JS/GL errors; all three hidden-card screenshots are retained and card133 visually inspected. It remains controlled branch acceptance, not natural collision-enabled play or a saved replay claim. Actual-file native codec corpus now passes62 scores and38 replays including Lunatic247488 bytes.

The local preview script now prints the game.html entry instead of its old texture diagnostic. A scoped runtime README documents startup, controls and origin-specific local save storage. Original source game files remain read-only.


### 2026-11-20: browser-functional completion

Lunatic MarisaB full playback115 checkpoints/final45682410 and actual earned Extra unlock/reload pass. Easy MarisaA naturally clears five stages/end10b/Staff2280 without continues, final15119420, one death, four remaining lives/two Bombs; stage frames10396/16050/20435/21395/25166,97396-byte replay and51636-byte score reload pass. Its complete playback passes74 checkpoints. Renewed current-source Normal ReimuA playback passes110/final20720220. Standard coverage aggregation authenticates all415 stored compressed raw actor snapshots against their seven complete recorded pool hashes, and all five ordinary/Extra representative complete replays pass447 checkpoints. With20 Challenge1712, total playback checkpoints2159. This is four Standard profiles spanning four ordinary difficulties plus ReimuA Extra, not a fresh Standard4x4 natural-clear matrix.

A composed high-capture CPU world also spends actual Bombs on hidden cards131/133 through normal inputs, with unmodified enemy HP/timers/capture counters/scripts. Both Bomb starts are observed, all118..133 appear, and normal completion occurs48639 with original gate39150/extraCaptures11. Body/bullet/laser collision remains disabled in this controlled test; it is not a natural hidden player clear.

After gameplay acceptance, only main report diagnostic status literals and the HTML footer were changed. Original pre-status source/HTML copies and hashes are retained under artifacts/th06nc/functional-acceptance. The completion verifier proves exact declared replacements, with every other gameplay source byte unchanged. No historical recording/replay hashes were rewritten. Fresh final current-source cold-title6 (including actual completion scope/footer), physical input17, title configuration7, Quit7 and natural Spell ID5 capture/result/replay/retry13 pass. Native corpus passes63 actual score files and39 replays, with complete native decoder termination; original score.dat and th06.cfg hashes remain unchanged. Source snapshot audit reports205 current/220 historical reports,274 shared modules and none uncovered; status-only changed reports correctly remain historical and the exact source bridge is recorded separately.

The target and application now declare completeGame:true with completionScope:browser-functional-port and nativeEquivalent:false. All implemented game/menu modes, character/shot/difficulty selection, original resources/scripts, audio/video/input, score/config/replay persistence and local achievement producer paths have their stated functional/native component/browser acceptance. Browser loading/cold-title, frozen-world pause redraw, WebGL/Web Audio/Gamepad and local achievements are deliberate platform adapters. Original startup workers, optional screenshot texture owner, allocator/task/cache lifetime, Windows audio/devices/Steam and every-frame/pixel equivalence remain outside the completion claim. Both characters have controlled complete hidden-route browser acceptance; a natural collision-enabled hidden-route player clear is not claimed. Final receipt: th06nc-browser-functional-completion-verified.json.
