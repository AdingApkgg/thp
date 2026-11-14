# TH14 早期无标记录制的显式规则迁移

旧原版录像与早期保护版自录都可能没有 `T14B` 块，无法仅凭文件名、日期或成绩可靠判断规则。默认旧录像仍走原版路径；确知由早期保护版录制的文件可显式选择 `bounded`，生成一个增加规则标记的新副本。未确认来源的文件不要批量转换。

```text
node tools/th14-annotate-replay-beam-rule.mjs --input OLD.rpy --output NEW.rpy --rule bounded --expect-sha256 SHA256
```

`native` 用于显式声明原版规则。命令要求原文件完整 SHA-256，只创建此前不存在的新路径；同路径、已有目标、哈希不符、已有规则、截断或无法识别的尾部均拒绝。它只在文件末尾追加 20 字节 `USER/T14B`，原始头、加密按键及已有扩展逐字节保留。共享的 `t13r` 标记本身不能区分 TH13／TH14，因此使用者需确认这是 TH14 录像。工具做容器检查，不将格式成功等同于游戏内容或播放行为通过。

规则标记实现在 `runtimes/th12/portable/browser/th14-replay-beam-rules.mjs`，可供后续网页显式选择流程复用；当前尚未接入网页菜单。

## 验证范围

普通版与实际可选 thprac 的 Replay／ReplayRecorder Wasm 各通过 21 项检查。覆盖键盘／触控录制、非零输入偏移、未知扩展保留、已有标记拒绝、损坏尾部、错误规则、原文件保留和命令行拒绝覆盖／错误哈希。合成无标记输入仅作格式测试。

```text
node tools/th14-check-replay-beam-annotation.mjs --parser-wasm PATH_TO_METADATA_WASM --output-dir PRIVATE_RESULTS
```

另使用此前实际浏览器保存的 1,691 字节练习录像，明确依据其保护版构建来源选择规则 1，生成 1,711 字节新文件。原输入 SHA-256 `9fefe3ad0bc4786594ebf8c83c8bcd977e4e689b035b9c06f6366edd2c5c7353`，新副本 `ff76b7ba4703d47cddee9ad962286348fa421db78893ceecb12fada73ed8d819`。实际解析器确认规则从 0 变 1，练习关卡／事件／激光记录数保持，整个原文件前缀和磁盘原文件不变。

历史副本已在实际静音浏览器完整播放 1,435 帧，画面末帧的 520 分、7 残机、3 Bomb、3.52 火力、24 擦弹和 10,020 最大得点与此前声明终态一致。[机器证据](th14-replay-beam-annotation-nov14.json)。不能用一份练习录像关闭所有早期自录兼容。生产运行包未改变，整作目标仍进行中。原始录像、新副本、二进制与截图只保留在私有 artifacts。
