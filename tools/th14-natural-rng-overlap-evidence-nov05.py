"""Public metadata for the actual original overlap, retained failure and diagnostic."""
from pathlib import Path
import argparse
import hashlib
import json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-native-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()
PUBLIC = R / 'docs/porting/th14-natural-rng-overlap-nov05.json'
DOC = R / 'docs/porting/TH14_NATURAL_RNG_OVERLAP_NOV05.md'


def main(check):
    bindings = {}

    def raw(path):
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    native = load(H / 'prefix-slots-v2/native/report.json')
    ended = load(H / 'prefix-slots-v2/process-end.json')
    preflight = load(H / 'preflight-slots-v2/verified.json')
    race = load(H / 'natural-overlap.json')
    slots = load(H / 'slot-audit.json')
    pair = load(H / 'original-pair.json')
    failure = load(H / 'comparison-off/result.json')
    failed_model = load(H / 'comparison-off/model/report.json')
    assert native['callbacks'] == 35000 and native['childExited']
    assert not native['error'] and not native['debugErrors'] and ended['guardStop'] is None
    assert preflight['verifiedNativePreflight'] and preflight['nativeShotSnapshotsVerified']
    assert preflight['observerSha256'] == native['sourceSha256']
    assert race['verifiedNaturalSeedReadSpansReplayStore']
    assert race['globalSnapshotMismatchCounts'] == {'mix32':1}
    assert race['workerScriptStoreValueRecoveredFromAx']
    assert race['laterWorkerMemorySnapshotAlreadyContainsMainStore']
    assert failure['strictDriverExitCode'] == failure['rawVerifierExitCode'] == 1
    assert failed_model['differenceCounts'] == {'21':4256,'22':344,'26':2}
    assert slots['allComparedFieldsEqual'] and slots['snapshotPairs'] == 55
    assert slots['geometryVms'] == 3117 and slots['comparedFields']['quadWords'] == 37404
    assert slots['vmAvailability'] == {'bothPresent':3117,'bothAbsent':26}
    assert slots['extraNativeSnapshotsNotAccepted'] == 4 and not slots['uncomparedGeometry']
    assert pair['actualOriginalSnapshotsCompared'] and pair['allNativeRetirementCausesAccepted']
    assert pair['pairedStageFrames'] == 59 and len(pair['observedDifferentRetirementPairs']) == 6
    assert not pair['uncovered']
    for report in [race, slots, pair]:
        for name, row in report['evidenceBindings'].items():
            data = raw(R / name)
            assert len(data) == row['bytes'] and SHA(data) == row['sha256']
    assert race['verifierSha256'] == SHA(raw(R / 'tools/th14-natural-rng-overlap-nov05.py'))
    assert slots['toolSha256'] == SHA(raw(R / 'tools/th14-audit-original-nine-shot-slots-nov05.py'))
    runs = []
    for case in ['off','on']:
        home = H / ('overlap-'+case)
        result = load(home / 'result.json')
        expanded = load(home / 'expanded-verified.json')
        assert result['strictDriverExitCode'] == result['rawVerifierExitCode'] == 0
        assert result['finiteLogicalOrderDiagnostic'] and not result['exactNativeScheduleAccepted']
        assert expanded['verifiedExpandedFiniteComparison']
        assert expanded['actualOriginalInstructionAccesses'] == 66 and expanded['pairedNext32Calls'] == 33
        assert expanded['extraPortableRowsNotAccepted'] == 24
        assert expanded['vm303Rows'] == 753 and expanded['combatCheckpoints'] == 354
        assert expanded['verifierSha256'] == SHA(raw(R / 'tools/th14-verify-original-nine-shot-native-nov05.py'))
        runs.append({key: expanded[key] for key in ['case','callbacks','all32StateFieldsEqual',
            'comparedCameraWords','all75CameraWordsEqual','all4CursorFieldsEqual','all2HudFieldsEqual',
            'actualOriginalInstructionAccesses','pairedNext32Calls','extraPortableRowsNotAccepted',
            'vm303Rows','combatCheckpoints','orderedPublications']})
    for name in ['selected-state.u32','full-camera.u32','replay-cursor.u32','portable-hud.u32']:
        assert raw(H / 'overlap-off/model' / name) == raw(H / 'overlap-on/model' / name)
    for name in ['th14-original-nine-shot-native-nov05.py','th14-original-nine-shot-read-evidence-nov05.py',
                 'th14-compare-original-nine-shot-native-nov05.py','th14-original-shot-pair-nov05.py',
                 'th14-compare-natural-rng-overlap-nov05.py']:
        raw(R / 'tools' / name)
    result = dict(schema='th14/natural-rng-overlap-public/1',
        verifiedOneActualOriginalSeedOverlap=True, nativeCallbacks=35000,
        nativeDebugExceptions=0, nativeShotSnapshots=59, preflightCallbacks=1200,
        nativeThreadScheduleExplicitlyControlled=False, additionalGameMemoryWrites=0,
        originalAttractFlagClearWrites=1, instructionBytesPatched=0, quiet=True,
        overlap=dict(stage=3, precedingPlayerCallbacks=30744,
            mainLoadPc='0x403336', mainStorePc='0x403373', workerScriptStorePc='0x456123',
            mainOldSeedReadRetainedByInstruction=True, workerReplacementRecoveredFromAx=True,
            laterWorkerMemoryAlreadyContainsMainStore=True,
            globalSnapshotMismatchCounts={'mix32':1}, mainStaleStoreWins=True,
            nextReadLoadsThatMainStore=True, accessEvents=66, pairedNext32Calls=33,
            exactCrossThreadExecutionTimesRecovered=False),
        retainedAtomicDeliveryFailure=dict(strictDriverExitCode=1,rawVerifierExitCode=1,
            firstDifferenceCallback=30745,stage=3,stageFrame=0,word=21,
            differenceCounts=failed_model['differenceCounts'], failureDiscarded=False),
        logicalDeliveryRuns=runs, readonlyProbeTransparentForCapturedState=True,
        actualOriginalSlotComparison={key:slots[key] for key in ['snapshotPairs','comparedFields',
            'geometryVms','vmAvailability','extraNativeSnapshotsNotAccepted',
            'completeVmMemoryCompared','quadExecutionIsComponentReconstruction']},
        actualOriginalPair=dict(pairedStageFrames=59, countDifferenceFrames=6,
            differingRetirementPairs=pair['observedDifferentRetirementPairs'],
            allComparedRetirementPairsExplained=True, noPortableVmValuesUsed=True,
            bootInputsAndSchedulesNotControlled=True, wholeOriginalGpuPixelsCompared=False),
        productionChanged=False, logicalOrderDiagnosticOnly=True,
        counterClearAndGlobalsCopyAtExactNativeMainInstructionAccepted=False,
        independentTimingAccepted=False, ordinaryOriginalGuiAccepted=False,
        oldHistoricalAVmGeometryRecovered=False, oldNineDifferencesClosed=False,
        strictNaturalModePassCountIncreased=False, completeGame=False, nativeEquivalent=False,
        rawAssetsOrObservationContentsUploaded=False, evidenceBindings=bindings,
        toolSha256=SHA(Path(__file__).read_bytes()))
    table = '\n'.join(f"| {row['stage']} / {row['stageFrame']} | {row['slots'][0]} / {row['slots'][1]} | {'A' if row['retired'][0] else 'B'} |"
                      for row in pair['observedDifferentRetirementPairs'])
    doc = '''# TH14 原版自然 RNG 交错与逐槽验证（2026-11-05）

新原版 35,000 回调实际捕获到一次旧种子读取跨过录像种子恢复的交错。读取时全局内存已经被工作线程改写，但主线程寄存器仍保留旧输入；主线程随后按旧输入写回并覆盖恢复值。按这条数据流交付初始化的有限诊断复算通过全部既有检查，同时保留原先整体交付的失败。另以两份原版实际 VM 快照直接复现六处旋转／退场差异。这推进了原版证据链，不是独立调度或整作 1:1 完成。

## 新原版观察与保留失败

沿用旧 A 的 player/pump 硬件观察配置，增加预定窗口的只读弹槽／动画快照。原始 EXE 和完整录像不变，测试隐藏、静音，资源复用。16 个完整上下文安装组件通过；原有 29 个句柄查找组件复用。1,200 回调前检的状态、相机、游标、HUD、230 行 VM、3 个战斗检查点及两份弹槽快照核验通过。之后独立完成 35,000 回调，零采集错误／调试异常，留存 59 个实际弹槽快照；未加入控制线程执行顺序的暂停／恢复，也未增加游戏内存写入。

原有比较时钟直接运行时，严格 driver 与原始核验均返回 1。首差在第 30,745 个 Player 观察、三面帧 0、脚本种子字；完整差异为脚本种子 4,256 处、脚本调用数 344 处、活动弹数 2 处。相机和 HUD 仍一致；动画及战斗检查失败保留。没有把失败输出标成通过。

## 寄存器与内存对应不同代次

三面第 30,744 次 Player 后，实际 `next32` 在 `0x403336` 已读取旧输入，工作线程的 `0x456123` 把录像种子写到同一脚本 RNG，主线程 `0x403373` 随后按自己保留的旧输入写回。工作线程的 AX 仍等于录像种子；主线程第一次 mix 的全局快照已是这个新值，与 AX 解码出的旧输入不同。更晚收到的工作线程断点快照却已经包含主线程的写回值，不能用该快照代替工作线程自己的写入值。后续计数清零／全局复制样本及下次实际读取均保留主线程的写回值。

全部 66 个原版指令访问、33 对 `next32` 算术对应通过，包含这一处 `mix32` 全局快照冲突，没有丢弃额外两条访问来沿用旧记录的 64 条。原版代码字节、寄存器恢复规则和真实全局样本分别核验；调试事件接收顺序不是完整跨线程执行时刻。

## 有限逻辑顺序诊断

已有观察 API 可在脚本 RNG 保留输入后、写回前交付初始化。新诊断只根据上述绑定证据安装这一窗口，输入是阶段／回调／宿主时刻，种子仍由原始录像及实际 C++ RNG 计算；不覆盖 RNG、残机、计数或逐帧状态。

关闭／开启只读逐槽观察各执行 35,000 回调，严格 driver 和独立原始文件核验均通过。32 项状态、2,624,925 相机数据项、4 项游标、2 项 HUD、66 次实际 RNG 指令值／次序／计数、753 行 VM 的选定 303 字段、354 个战斗检查点和初始 3,275 项发布顺序一致。24 条额外模型访问单列未验收；不按种子或 VM flags 挑选匹配。四份状态／相机／游标／HUD 输出在观察开关间逐字节相同。

这个窗口把 Initialize 的恢复工作作为整体放在保留输入之后。游戏计数清零和全局复制并未据此放到原版各自精确的主线程指令位置；因此只能接受所列有限结果，不能写成已恢复全部真实并发交错或普通浏览器独立调度。原整体交付失败不删除，正式玩法与严格模式通过数不变。

## 原版实际逐槽与六处退场变化

55 对新原版／模型快照按槽与句柄直接核对：3,143 次活动弹字段一致，3,117 个存在动画的选定字段及原版指令重建的 37,404 四角坐标字逐位相同；26 次两端动画已不存在也保留一致。另四份原版快照未配对，不计入通过；未比较完整 VM 内存或 GPU 帧缓冲。

再直接比较新旧两份实际原版快照，共 59 个关卡／帧配对，六处活动弹数不同。使用唯一出生帧／完整规格／运动键匹配对应子弹，原版 VM 字节经原版 `0x479560` 计算的可见性准确预测实际退场变化；六对各自只换旋转角的控制都反转可见性，并逐位重现另一端完整四角。该比较未使用可移植 VM 值。

| 关卡 / 退场差异帧 | A / B 弹槽 | 先退场的一端 |
| --- | --- | --- |
''' + table + '''

两份原版启动输入和观察配置不同，不能据此证明普通 GUI 的非确定性。这里的六处新原版差异与此前[九处旧记录模型定位](TH14_ORIGINAL_NINE_SHOT_MODEL_NOV05.md)分别列示；旧 A 历史 VM 几何依然缺失，不补造或强称恢复。

## 复核与剩余范围

`tools/th14-original-nine-shot-native-nov05.py` 准备、短前检并运行有界静音原版；`tools/th14-original-nine-shot-read-evidence-nov05.py` 校验真实 RNG 指令；`tools/th14-natural-rng-overlap-nov05.py` 核验交错数据流。原失败在 `comparison-off`，新逻辑诊断由 `tools/th14-compare-natural-rng-overlap-nov05.py` 生成，额外相机／游标／全部 RNG 配对由 `tools/th14-verify-original-nine-shot-native-nov05.py` 重算。实际逐槽和原版间比较分别用 `tools/th14-audit-original-nine-shot-slots-nov05.py`、`tools/th14-original-shot-pair-nov05.py`。

原始资产、种子／cookie、内存／寄存器、录像、图片、PCM 和二进制留本地。[公开元数据](th14-natural-rng-overlap-nov05.json)只包含计数、差异、地址、标识、路径和哈希，可用 `python tools/th14-natural-rng-overlap-evidence-nov05.py --check` 复核。后续继续原版指令交付、独立时序、全模式及普通流程、浏览器侧栏／保存／离线和整局像素／PCM；整作 1:1 未完成。
'''
    data = (json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode()
    if check:
        assert PUBLIC.read_bytes() == data and DOC.read_bytes() == doc.encode()
    else:
        assert not PUBLIC.exists() and not DOC.exists()
        PUBLIC.write_bytes(data)
        DOC.write_bytes(doc.encode())
    print(json.dumps(dict(verifiedActualNativeOverlap=True, nativeCallbacks=35000,
        registerAccesses=66, pairedShotSnapshots=55, originalRetirementPairs=6,
        publicBytes=len(data), rawContentsPublished=False, completeGame=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    main(parser.parse_args().check)
