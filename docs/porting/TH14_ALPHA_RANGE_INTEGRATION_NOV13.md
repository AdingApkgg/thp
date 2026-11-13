# TH14 协作者 alpha 阈值优化的独立整合 · 2026-11-13

从 Goan114 的[19170e47](https://github.com/Ritosa2333/eagler-touhou/commit/19170e47016e10d61d5e69556989b68b5cdea8e3)单独接回 alpha 阈值比较。该提交还包含延迟颜色清屏；本次没有接回这一部分，也没有改动清屏、批次、几何或模拟更新顺序。

旧 shader 根据测得的 RGBA8 边界重建字节 alpha，再与参考字节比较。新 TH14/version10 shader 在 CPU 端取参考字节对应的两个边界，通过 `alphaRange` 直接比较，保留相同边界归属。其他版本和其他作品保留原表达式；无纹理绘制解绑修复保留。没有测量本轮修改的帧率提升，不将减少 shader 工作量等同于已测性能收益。

使用当前 Renderer 及正常权限构建的独立候选，在实际 ANGLE/D3D11 离屏 GLES 执行8,192组原版 D3D9像素对照：两种操作、八种比较、全部256个参考值，普通／低alpha两套输入。8,388,608像素零差异，两个完整像素流聚合哈希与保留原版相同。该范围不覆盖所有纹理／混合输入或整帧，也不证明最终游戏画面或物理加载时间线。

执行驱动复用了包含清屏检查的旧工具，在alpha完成后查找错误的 `v4-baseline/gpu/clears.bgra` 而退出1。失败报告、执行驱动和退出码保留；它没有执行本轮清屏检查。独立资格检查重新核验8192计数、原版文件／清单哈希、候选模块身份、两个实际像素流聚合哈希及设备回收，接受已完成的alpha部分，未将整个失败命令改写为成功。后续工具改为只执行alpha，未重跑游戏或GPU测试。

首次收紧条件编译时，TH12对象仍相差12字节：非TH14路径把原 `float alpha` 变成额外作用域内的 `const float alpha`。该候选被拒收。v2完整恢复原非TH14表达式及作用域，TH12／13／16三对正常权限对象逐字节相等；v2的TH14完整测试模块与刚才通过8192组对照的模块逐字节相等，因此不重复GPU测试。

本地Root原子合入 `runtimes/th12/portable/sdl/Renderer.cpp`，SHA256 `851eb78ae64600ddbec096c15bcb79e930c4a04d64b9395642507e4281d49780`。实际正常权限宿主Renderer重编成功，141个游戏和其余三个宿主对象逐项核验复用，布局不变。新绑定位于 `artifacts/th14/alpha-range-current-nov13/current-provider-bindings.json`；旧绑定与旧结果保持原样，不冒充对应新源码。

本轮测试静音，GPU／平台已测对象均回收。没有复制游戏资产或运行完整录像。此处记录源码整合，运行包部署另行记录；加载24次RNG、相机缓存、实际完整画面、全部自机难度、普通流程、最终音频与浏览器等验收继续开放，`completeGame=false`。

本地证据根目录：`artifacts/th14/alpha-range-current-nov13/`。工具：`tools/th14-prepare-alpha-range-nov13.py`、`tools/th14-run-alpha-range-current-nov13.mjs`、`tools/th14-qualify-alpha-range-nov13.py`、`tools/th14-bind-alpha-range-providers-nov13.py`。原始像素、资产与二进制不加入公开Git。
