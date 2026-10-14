# TH14 屏幕相机参数修正（2026-10-15）

TH14 的 `SceneCamera::screen()` 已改用相机自身的 FOV，并把视口起点计入中心。原版 `4465e0` 将 30° FOV 复制到四个相机，`446920` 直接跳到同一重置函数；此前移植固定使用 18°，且中心缺少视口起点。距离分子保留原版 `height >> 1`，中心则保留浮点半尺寸，近／远裁剪面仍为 1／10000。

修改仅在 `PORT_TITLE == 14` 分支。其他作品的屏幕函数分支及非屏幕函数保持原字节，数学库和 compositor 未修改，也没有再次给顶点增加视口偏移。普通 `ScreenColor`／`ScreenColorUv` 路径绕过这些矩阵；矩阵投影路径使用已经完成原点转换的坐标。

实际比较直接调用修改前后的真实生产 `SceneCamera::screen()`，观察数学函数参数后继续执行真实数学函数。四个相机共比较 52 个参数字和 128 个矩阵字：修改前分别有 20／26 个差异，修改后全部一致。[生产函数比较](th14-startup-camera-screen-correction-observed-oct14.json)的输入来自本轮原码启动观察；D3DX 分派及 FPU 是明确声明的受控配置，并非实测原生 CPU 或整作图像验收。[同输入数学记录](th14-startup-camera-same-input-math-observed-oct14.json)另证实这些参数下数学运算本身一致。

新版 SDL 已构建为 1,890,843 字节，SHA-256 `3083772c3d52e981dfd5dacd37960d9bf35ffc7acf441f247422981a3b0eb7ea`。267 份游戏核心文件只改变相机；141 个 engine 对象、146 个 SDL 对象也各只改变相机对象，导入／导出接口差异为零。无入口 engine 链接文件仍逐字相同，因此不将这一链接结果当作相机行为执行证明；上面的专用真实函数比较和新版 SDL 是分别记录的证据。[构建独审](th14-screen-camera-production-build-observed-oct15.json)。

127 文件新版预览已在原 `http://localhost:8208/` 地址实际启动，显示标题及 Normal Demo Play。游戏 iframe 与外层页面均显示“本机测试静音”，捕获的警告／错误为零。初次沙箱服务不可达及错误标签页的失败如实保留，随后复用已授权的同一回环服务并新建测试标签页，原游戏页未刷新。按键后的图片仍显示 Demo，未据此认定普通新游戏菜单流程通过。[浏览器观察](th14-screen-camera-browser-observed-oct15.json)。

随后新增 960×720、1280×960 两个分辨率对照。每组重新映射原 EXE 与固定 D3DX，仅输入配置字 16／20，真实执行 Supervisor 构造、尺寸计算和四相机重置；八次 D3DX 数学调用都完成原返回，矩阵有限，随机数区域未改变。生产 `SceneCamera::screen()` 的同输入比较各得到 52 个参数字、128 个矩阵字零差，共 104／256 字。此对照仍使用明确声明的 FPCW／MXCSR 与模拟执行环境，不证明这两个分辨率的浏览器画面、原生 CPU 或完整冷启动。[分辨率对照收据](th14-screen-camera-resolutions-observed-oct15.json)。

此前加载生命周期、整局回放及像素记录保留原版本范围，不能自动继承为本次相机修正的整局通过。当前仍为 `completeGame=false`、`nativeEquivalent=false`。
