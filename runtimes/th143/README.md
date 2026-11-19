# TH143 弾幕アマノジャク · V154

生产入口：https://wth.saop.cc/th143/ 。独立 C++/Wasm 核心，WebGL、浏览器本地文件存储及 WebAudio 前端。与 TH14、TH06nc 的代码和存档空间分开。

## 源码与构建

`production/source-tree` 保存当前558个编译单元的1193个精确逻辑源码依赖，已解析开发工作区冻结覆盖；不依赖正在变动的其他游戏目录。`production/source-manifest.json` 提供全部文件SHA-256。文件名中的 fixture 是历史命名，当前编译的是实际运行游戏的导出宿主。

安装 WASI SDK34，并设置 `WASI_SDK_PATH` 指向SDK目录，然后运行：

```sh
python runtimes/th143/production/build.py /absolute/output/directory
```

需要 Python3；脚本校验全部输入并编译、链接独立 `play.wasm`。构建目录不是发布资源目录。采用的验收Wasm SHA256：`d4d5407fb0b7b06cf0052efbe845f9abf303838d39e71a21bc5cc57ae3ee7cbd`。跨路径或工具链生成文件身份以实际构建记录为准。

`production/web` 包含73个前端模块与入口HTML；`host/th143/runtime-manifest.json` 定义自托管发布包身份。游戏资源、预编译Wasm、原版可执行文件、开发观察数据、QA页面和个人存档不上传Git。完整已验收资源包在生产站单独部署；本地需要对应的 `build.json`、`blobs/` 和许可字体，保持与清单一致。部署目录为站点的 `th143/`，必须保留相对路径；Wasm和mjs应使用正确MIME，建议与现有站点一致提供COOP/COEP。

## 行为验收范围

已完成十天75场自然进度保存、81组合初始化与主使用结束、适用主副道具代表边界；菜单、设置、真实保存/回放、音画与生命周期证据按具体版本保留。自然75链使用普通键盘输入、原版动作参考及网页Pause辅助，不是连续实时通关。未声称逐像素/75场原生整进程同步、物理手柄或扬声器听感验证。

V152修复失败菜单放弃/说明崩溃；V153修复批量文件同步入队异常后的部分提交及异步输入快照；V154修复失败录像自然死亡时拒绝结束入口的问题。真实失败录像保存/命名/取消、换装取消/重试、同录像重复结束、通关录像结束、结算说明正文/返回/重开/Quit均有实际操作回归。旧V151整体完成结论因实际反例撤回，V154重新逐项验收。

键盘：Z/Enter确认和射击，X道具，方向键移动，Shift低速，Esc返回。声音由用户开启；配置和成绩在正常Quit/离页时保存于当前浏览器。正式生产部署结果另见 `docs/porting/th143-production-release-nov20.json`。
