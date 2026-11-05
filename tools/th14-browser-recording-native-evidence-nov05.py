"""Publishable metadata for one browser-authored replay's original playback.

Reads retained local evidence only. Never embeds replay, memory, register,
cookie, seed, image, PCM, score-file, archive or binary contents.
"""
from pathlib import Path
import argparse
import hashlib
import json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/browser-recording-native-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()
PUBLIC = R / 'docs/porting/th14-browser-recording-native-nov05.json'
DOC = R / 'docs/porting/TH14_BROWSER_RECORDING_NATIVE_NOV05.md'


def main(check):
    bindings = {}

    def read(name):
        path = R / name
        data = path.read_bytes()
        bindings[name] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(name):
        return json.loads(read(name))

    stem = 'artifacts/th14/browser-recording-native-nov05/'
    prep = load(stem + 'observer/prepared.json')
    preflight = load(stem + 'preflight/verified.json')
    full = load(stem + 'natural/verified.json')
    native = load(stem + 'natural/native/report.json')
    manifest_path = 'artifacts/th14/native-campaign-assets/57d84a5cbe82-ec04b9bea043/manifest.json'
    manifest = load(manifest_path)
    assert full['verifiedOneBrowserRecordingOriginalPlayback']
    assert preflight['verifiedNativePreflight']
    assert SHA(read(stem + 'natural/native/observer-source.py')) == prep['observerSha256'] == full['observerSha256']
    assert bindings[stem + 'natural/native/report.json']['sha256'] == full['nativeReportSha256']
    assert bindings[manifest_path]['sha256'] == prep['assetManifestSha256']
    assert manifest['passed'] and manifest['allOrdinalDecodedBytesVerified']
    assert manifest['originalFilesNeverHardlinked'] and manifest['noArchiveExtractionPerformed']
    assert manifest['unchangedEntries'] == 226 and manifest['changedEntries'] == ['demo0.rpy']
    assert not full['actualDeclaredInputExhaustionBranchObserved']
    assert not full['actualAllFfffMarkerBranchObserved']
    assert native['callbacks'] == 1293 and native['observedForcedReplayEndMenu']
    assert native['childExited'] and not native['error'] and not native['debugErrors']
    assert prep['criticalMutationCallAstUnchanged'] and prep['additionalGameMemoryWrites'] == 0
    read('artifacts/th14/browser-new-recording-nov05/saved-slot02.rpy')
    assert bindings['artifacts/th14/browser-new-recording-nov05/saved-slot02.rpy']['bytes'] == 1240
    assert bindings['artifacts/th14/browser-new-recording-nov05/saved-slot02.rpy']['sha256'] == full['replaySha256']
    for name in ['tools/th14-browser-recording-native-assets-nov05.mjs',
                 'tools/th14-prepare-browser-recording-native-nov05.py',
                 'tools/th14-run-browser-recording-native-nov05.py',
                 'tools/th14-check-browser-recording-preflight-nov05.py',
                 'tools/th14-check-browser-recording-natural-nov05.py',
                 'docs/porting/th14-browser-new-recording-nov05.json',
                 stem + 'preflight/raw-verified.json', stem + 'natural/raw-verified.json',
                 stem + 'natural/comparison/model/report.json',
                 stem + 'natural/comparison/model/full-camera-report.json',
                 stem + 'natural/comparison/model/replay-cursor-report.json',
                 stem + 'natural/comparison/model/hud-report.json',
                 stem + 'natural/process-end.json']:
        read(name)
    evidence = dict(
        schema='th14/browser-recording-native/1',
        verifiedOneBrowserRecordingOriginalPlayback=True,
        browserReplayBytes=1240, replaySha256=full['replaySha256'],
        selection=dict(character='Reimu', subtype='B', difficulty='Normal', stage=1),
        preflight=dict(callbacks=1200, all32StateFieldsEqual=True,
                       comparedCameraWords=89925, vm303Rows=preflight['vm303Rows'],
                       combatCheckpoints=preflight['combatCheckpoints']),
        naturalPlayback={key: full[key] for key in [
            'declaredFrames', 'callbacks', 'originalStableMenuSamples',
            'all32StateFieldsEqual', 'all75CameraWordsEqual', 'comparedCameraWords',
            'all4CursorFieldsEqual', 'all2HudFieldsEqual', 'vm303Rows',
            'combatCheckpoints', 'orderedPublications', 'selectedVisibleTerminalFields',
            'originalInternalLifeCountMinusOne', 'originalLifeState',
            'originalCursorAtMenu', 'declaredRangeExhaustedAtMenu',
            'actualDeclaredInputExhaustionBranchObserved', 'actualAllFfffMarkerBranchObserved',
            'originalObservedStableReplayEnd', 'modelStableMenuAfter90Ticks']},
        assets=dict(changedEntries=['demo0.rpy'], unchangedEntries=226,
                    allOrdinalDecodedBytesVerified=True, noArchiveExtractionPerformed=True,
                    sharedGeneratedBytes=manifest['sharedGeneratedBytes'],
                    smallCopiedBytes=manifest['smallCopiedBytes'],
                    generatedArchiveBytes=manifest['generatedArchiveBytes']),
        observer=dict(terminalPausePredicateUnchanged=True,
                      readOnlyProbeWhilePaused=True, additionalGameMemoryWrites=0,
                      additionalSuspendOrResumeCalls=0, criticalMutationCallAstUnchanged=True,
                      originalAttractFlagClearWrites=1, rngCounterHealthInputWrites=0,
                      hardwareInstructionWatchesUnchanged=True, instructionBytesPatched=0,
                      nativeDebugExceptions=0, quiet=True),
        privateAttractHarness=True, ordinaryOriginalGuiReplayMenuAccepted=False,
        observedHostClockScheduleSupplied=True, independentTimingAccepted=False,
        originalGpuPixelsOrPcmCompared=False, allModesAccepted=False,
        fullBrowserSaveReplayAcceptance=False, sidebarFailureClosed=False,
        oldNineShotDifferencesClosed=False, productionSourcesChanged=False,
        completeGame=False, nativeEquivalent=False,
        rawAssetsOrObservationsUploaded=False, evidenceBindings=bindings,
        toolSha256=SHA(Path(__file__).read_bytes()))
    doc = '''# TH14 浏览器新录像的原版自然回放（2026-11-05）

浏览器通过普通 Game Over → Save 保存的完整 No.02「B」录像，现已在原版 Windows EXE 中自然进入稳定 Replay End。独立 C++/Wasm 对该原版运行的完整 1,293 次 Player 回调严格复算通过。这补上该文件从实际浏览器录制到实际原版回放的验证；不是整作 1:1 完成，也不是普通原版 GUI 回放入口的验收。

输入是先前[普通浏览器新保存](TH14_BROWSER_NEW_RECORDING_NOV05.md)的灵梦 B Normal 一面录像，完整 1,240 字节原样保留。私人测试包只替换 `demo0.rpy`，其余 226 个条目按原始顺序逐项解码核对；没有修改录像输入、头部或 FPS。复用 237,406,884 字节既有生成资源，仅复制 15,843,936 字节小文件，重建归档 90,744,064 字节；未重新解包整套资源。原始游戏文件没有硬链接或改动。

## 实测结果

| 范围 | 结果 |
| --- | --- |
| 启动前检 | 1,200 回调；32 项状态、89,925 相机数据项、游标／HUD、175 行 VM、3 个战斗检查点一致 |
| 原版自然结束 | 1,293 次 Player 回调，3 份实际稳定结束菜单样本；采集错误／调试异常均为零 |
| 独立模型完整复算 | 32 项状态、96,900 相机数据项、4 项游标、2 项 HUD 一致 |
| 动画与战斗 | 176 行 VM 的选定 303 字段、3 个战斗检查点、初始 1,091 项发布顺序一致 |
| 模型菜单 | 实际进入结束菜单，再推进 90 tick 保持稳定；终局 HUD 两字为 424／424 |
| 两端选定终局显示 | 分数 4,240；残机 0、碎片 0/3；Bomb 3、碎片 0/8；火力 1.00；最大得点 10,010；擦弹 11 |

声明帧数为 1,294，实测回调为 1,293，两者没有混用。原版结束时内部残机为 -1、Player life state 为 2；界面零残机与此前浏览器现场一致。菜单时录像游标 1,293 尚小于声明 1,294，未观察到输入范围耗尽分支或全 FFFF 标记分支，不能把这次自然 Game Over 结束写成已验证 EOF 分支。

## 观察方式与边界

沿用原有私人 attract 回放初始化，在首个 Player 边界只清一次 attract 标志；没有增加 RNG、计数、残机或输入写入。硬件指令观察点和异常保护不变。只读终局探测增加在已暂停的调试事件处执行，因为固定 Supervisor/pump 观察点在 Player 停止后仍触发事件，旧的等待超时分支不能可靠运行。原有完整菜单判定未放宽；只有读到实际菜单才留样，重复三次稳定样本后才终止观察。测试全程静音，不接触浏览器。

复算沿用冻结的严格 driver 和原始字节核验器，另逐回调检查全部 75 相机数据项及 4 游标字段。模型提供了原版观测到的宿主时序和启动环境，不能据此认定独立浏览器调度或普通原版 GUI 已通过。浏览器文件来自较早 GLES 候选，本次不把该旧版本的浏览器流程结果自动迁移到当前候选。

当前正式玩法源码未改。此前九处旧自机弹差异、普通启动／所有保存分支、全模式、侧栏故障、离线、原版整局 GPU 像素和 PCM 仍开放。原始录像、资产、种子、cookie、内存、寄存器、图片、音频和二进制留本地；公开内容只有源码与计数／差异／路径／哈希元数据。

## 本地复核

`tools/th14-browser-recording-native-assets-nov05.mjs`、`tools/th14-prepare-browser-recording-native-nov05.py` 和 `tools/th14-run-browser-recording-native-nov05.py` 依次准备哈希绑定输入与有界静音原版运行。已有输出目录拒绝覆盖。先运行 `tools/th14-check-browser-recording-preflight-nov05.py`，通过后运行独立 natural case，再运行 `tools/th14-check-browser-recording-natural-nov05.py`。默认保留至少 100 GiB 空闲余量，观察文件上限 512 MiB；不会自动重复采集。

公开元数据为 [th14-browser-recording-native-nov05.json](th14-browser-recording-native-nov05.json)，可用 `python tools/th14-browser-recording-native-evidence-nov05.py --check` 校验本地封存的绑定与报告。
'''
    data = (json.dumps(evidence, ensure_ascii=False, indent=2) + '\n').encode()
    if check:
        assert PUBLIC.read_bytes() == data and DOC.read_bytes() == doc.encode()
    else:
        assert not PUBLIC.exists() and not DOC.exists()
        PUBLIC.write_bytes(data)
        DOC.write_bytes(doc.encode())
    print(json.dumps(dict(verifiedOneReplayCase=True, callbacks=1293,
                          publicBindings=len(bindings), publicBytes=len(data),
                          rawContentsPublished=False, completeGame=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    main(parser.parse_args().check)
