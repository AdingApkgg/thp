# TH14 生产 Application 的离屏流程验证 · 2026-10-26

新增可重复执行的生产 C++ Application 集成入口。实际执行 `Application.cpp`、图形、字体、音频设备及生产渲染器，链接 141 个已冻结游戏对象；平台提供声明的时钟、异步回调队列、只读资源、私有保存目录和不播放的音频队列。无浏览器、DOM、真实窗口、物理输入或音频设备。Application 和渲染器源码均未修改。

第一段普通输入场景执行 1,286 帧：冷启动至主菜单，选择咲夜 B Easy，进入一面，暂停／恢复，保存录像，输入名字 A，返回标题，打开录像菜单，读回并播放刚保存的录像至结束菜单。第二个新进程只接收第一段实际写出的文件，执行 722 帧，重新启动、扫描录像并回放至结束菜单。两段共 239 项状态断言和 18 幅实际渲染缓冲留存；不是原版图像比较。首次按取消键早于保存列表的输入等待时间，脚本明确检查其仍停留在列表，不把这幅图标成返回标题。

本页保留该次冻结 GLES 构建的证据。后续[实际 C++ WebGPU 接入](TH14_CPP_WEBGPU_OCT26.md)使用新构建及声明相同元数据时钟的成对场景，另行验证两个后端的全部 18 幅缓冲、PCM 和文件一致；不让旧证据自动继承新源码。

实际写出 `scoreth14.dat` 21,635 字节、`th14.cfg` 92 字节及 `replay/th14_01.rpy` 358 字节。新进程读回后三个文件逐字节不变。录像包含 127 个空闲玩法输入、一个六字节终止标记及五个 FPS 样本。原版 x86 `4028e0` 双遍解密及 `465840` 解压实际文件；原版 `456de0` 加载全部 149,076 字节分数记录，`456f60` 写回的完整文件也逐字节一致。CRT 分配、释放、复制和清零属于声明的组件边界；没有启动、驱动或修改正在运行的原版进程。

[范围和哈希报告](th14-native-application-verified-oct26.json)由[独立检查器](../../tools/th14-native-application-evidence-check-oct26.py)复算场景输入、逐项状态断言、资源／源文件绑定、原始缓冲哈希、文件字节和原版 codec 结果。组件 Wasm 为 `03ee28ed03ad847f7e7146c11deec1214de9ab5ecf8c349df1c8d187b0860aab`。当前编译的 Application／设备／渲染源码与项目头文件绑定在构建报告中，复用游戏对象保留其原始冻结构建的来源，不宣称工作区每个当前源文件都重新编译。

```powershell
python tools/th14-build-native-application.py `
  --core-build PATH_TO_RETAINED_CORE_BUILD_JSON `
  --output artifacts/th14/NEW/build
python tools/th14-native-application.py `
  --build artifacts/th14/NEW/build `
  --output artifacts/th14/NEW/workflow `
  --scenario runtimes/th12/th12_web/tests/fixtures/th14-native-application-save-replay.json `
  --archive PATH_TO_OWN_TH14_DAT --fonts PATH_TO_GENERATED_FONTS `
  --music PATH_TO_GENERATED_MUSIC --angle-directory PATH_TO_ANGLE_DLLS `
  --wasmtime-site PATH_TO_LOCAL_WASMTIME_PACKAGE
python tools/th14-native-application.py `
  --build artifacts/th14/NEW/build `
  --output artifacts/th14/NEW/reload `
  --scenario runtimes/th12/th12_web/tests/fixtures/th14-native-application-reload-replay.json `
  --initial-save artifacts/th14/NEW/workflow/save `
  --archive PATH_TO_OWN_TH14_DAT --fonts PATH_TO_GENERATED_FONTS `
  --music PATH_TO_GENERATED_MUSIC --angle-directory PATH_TO_ANGLE_DLLS `
  --wasmtime-site PATH_TO_LOCAL_WASMTIME_PACKAGE
python tools/th14-native-application-files.py `
  --save artifacts/th14/NEW/workflow/save --output artifacts/th14/NEW/native-files
```

依赖是本地 WASI SDK、SDL3/GLES 头文件、Windows ANGLE、Wasmtime；原版文件检查另用 Unicorn 和本机原版 EXE。工具不安装依赖，不操作浏览器或其他应用。输出必须放入新的私有 `artifacts/th14` 目录，单次最多 12,000 帧、900 秒，至少保留 100 GiB 磁盘空间，观察文件预算 2 GiB。文件检查场景明确针对本次 127 帧咲夜 B Easy 录像，不能当作任意录像的通用验收器。

这是独立平台组件中的生产 Application 衔接证据，尚未对照原版普通冷启动菜单，也没有证明物理输入、原版完整录像播放、完整六面玩法、续关、整幅图像、音频设备、浏览器 IndexedDB、刷新或当前发布模块的普通浏览器流程。`browserAcceptance=false`、`completeGame=false`、`nativeEquivalent=false`。游戏资源、原始图像、存档、录像、DLL、对象文件和 Wasm 均不随源码发布。
