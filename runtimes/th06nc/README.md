# TH06nc 浏览器移植

浏览器功能版已通过 [完成验收](../../docs/porting/th06nc-browser-functional-completion-verified.json)。具体测试组合和原版平台等价性的验证限制一并保留。

在工作区根目录运行：

```powershell
py -3 tools/th06nc-preview.py
```

打开 [游戏入口](http://127.0.0.1:8268/runtimes/th06nc/game.html)。已有本机服务时直接使用该链接。资源使用本目录下已经准备好的 `artifacts`；原版目录保持只读。

方向键移动，Z 射击／确认，Shift 低速，X 使用 Bomb／取消，Ctrl 快进对话，Esc 暂停。暂停菜单提供继续、重开和返回标题。首次按键会启用浏览器音频。

成绩、录像、配置和本地成就保存在当前浏览器的 IndexedDB。固定使用上述地址可以继续使用同一份存档；域名、端口和浏览器分别对应独立的存档空间。

普通、Challenge、关卡练习、符卡练习、Extra、录像、成绩、音乐室、制作名单和选项的实现与验收范围见 [目标状态](target.json) 和 [验证记录](../../docs/porting/TH06NC_FORMATS.md)。Windows 图形／音频设备、Steam 成就和原版线程资源生命周期与浏览器适配层分别记录，不作为已经获得原版逐像素等价的声明。
