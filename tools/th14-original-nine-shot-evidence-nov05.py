"""Produce public count/identity/hash metadata for the nine-shot model audit."""
from pathlib import Path
import argparse
import hashlib
import json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-model-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()
PUBLIC = R / 'docs/porting/th14-original-nine-shot-model-nov05.json'
DOC = R / 'docs/porting/TH14_ORIGINAL_NINE_SHOT_MODEL_NOV05.md'


def main(check):
    bindings = {}

    def load(path):
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return json.loads(data)

    audit = load(H / 'model-audit.json')
    component = load(H / 'retail-component.json')
    prepared = load(H / 'component/prepared.json')
    assert audit['verifiedModelExplanation'] and len(audit['events']) == 9
    assert audit['matchedOldCountDifferenceFrames'] == 9
    assert not audit['originalNineDifferencesClosed'] and not audit['oldOriginalAVmGeometryMeasured']
    assert component['passed'] and len(component['cases']) == 45
    assert component['rotationOnlyControls'] == 18
    assert sum(row['rotationSwapped'] for row in component['cases']) == 18
    assert all(row['quadBitIdentical'] and row['quadMaxAbsError'] == 0 for row in component['cases'])
    assert all(row['retired'] == row['expectedRetirement'] == row['releaseCalled'] for row in component['cases'])
    assert prepared['exactReversalRestoresParent'] and prepared['retailInstructionExecutionUnchanged']
    assert SHA((H / 'component/oracle.py').read_bytes()) == prepared['oracleSha256'] == component['toolSha256']
    assert any(max(row['familyBirthMultiplicity']) > 1 for row in audit['events'])
    for report in [audit, component]:
        for name, row in report['evidenceBindings'].items():
            data = (R / name).read_bytes()
            assert len(data) == row['bytes'] and SHA(data) == row['sha256'], name
            bindings[name] = row
    runs = []
    for case in ['off', 'on']:
        result = load(H / 'retry1' / case / 'result.json')
        assert result['driverExitCode'] == result['rawVerifierExitCode'] == 0
        assert result['allExistingPayloadsByteIdentical'] and result['payloadFiles'] == 359
        runs.append({key: result[key] for key in ['case', 'callbacks', 'snapshots', 'outputBytes',
            'payloadFiles', 'allExistingPayloadsByteIdentical', 'driverSha256', 'buildSha256']})
    initial = load(H / 'off/result.json')
    assert initial['driverExitCode'] == 1
    assert b'New TH14 artifact directory required' in (H / 'off/driver.log').read_bytes()
    for name in ['th14-original-nine-shot-model-nov05.py', 'th14-original-nine-shot-audit-nov05.py',
                 'th14-original-nine-shot-component-nov05.py']:
        path = R / 'tools' / name
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
    result = dict(schema='th14/original-nine-shot-model-public/1',
                  verifiedModelExplanation=True, runs=runs, snapshotPairs=55, slotsPerSnapshot=256,
                  matchedOldOriginalCountDifferenceFrames=9, events=audit['events'],
                  bothModelSelectedStatesExactlyMatchTheirRetainedOriginal=True,
                  retailComponent=dict(cases=45, unswappedCases=27, rotationOnlyControls=18,
                      all45QuadCoordinateWordsBitIdentical=True, quadCoordinateWords=45*12,
                      all18RotationOnlyControlsReverseRetirement=True,
                      wholeRetailShotUpdateExecuted=True, retailQuadExecuted=True,
                      originalGameplayCapture=False, instructionBindings=component['instructionBindings'],
                      controlledSinks=component['sinks']),
                  retainedPreparationFailure=dict(firstDriverRelocationExitCode=1,
                      wrongArtifactRootRejected=True, originalFailedOutputRetained=True,
                      invalidFamilyOnlyUniquenessAssumptionRejected=True,
                      fullBirthFamilyAndMotionIdentityUsed=True),
                  oldOriginalAVmGeometryMeasured=False, ordinaryOriginalGuiAccepted=False,
                  observedHostTimingInputsUsed=True, independentSchedulingAccepted=False,
                  oldNineDifferencesClosed=False, currentStrictModePassCountIncreased=False,
                  productionChanged=False, newOriginalProcessLaunched=False,
                  originalWholeGpuOrPcmCompared=False, completeGame=False, nativeEquivalent=False,
                  rawStatesAssetsSeedsCookiesImagesOrBinariesUploaded=False,
                  evidenceBindings=bindings, toolSha256=SHA(Path(__file__).read_bytes()))
    table = '\n'.join(f"| {row['stage']} / {row['stageFrame']} | {row['slots'][0]} / {row['slots'][1]} | {row['countA']} / {row['countB']} | {'A' if row['retired'][0] else 'B'} |"
                      for row in audit['events'])
    doc = '''# TH14 九处旧弹数差异的模型逐槽定位（2026-11-05）

两份旧原版记录各自对应的模型复算中，九处弹数差异现在全部定位到具体弹槽：动画旋转改变四角越过上边界的时刻，使已经命中的子弹相差一帧退场。45 个原版单弹更新／四角计算组件用例通过，其中 18 个只交换旋转角的控制全部反转退场结果。该结论覆盖两条重现原版选定状态的模型轨迹，不补造旧原版未采集的 VM 几何，也没有关闭独立时序或原版整体等价门槛。

## 覆盖九处实际记录差异

原来的[原版记录对照](TH14_STARTUP_TIMING_SENSITIVITY_NOV05.md)有 34,429 个唯一关卡／帧配对，脚本 RNG 两字段不同，活动自机弹计数恰有九处不同。A 为旧 player/pump 轮换观察记录，B 为固定 Supervisor/pump 观察记录；启动时间、cookie 和观察配置不同。两份记录不是控制所有输入的普通 GUI 对照。

本次复用原有严格 A driver、既有只读观察 Wasm 和 141 个哈希绑定玩法对象。关闭／开启逐槽观察各执行 35,000 回调，原有严格比较和独立原始文件核验均通过；所有 359 份既有二进制状态、采样 VM、战斗对象输出都与此前 A 通过结果逐字节相同。没有改写原版数值、放宽断言或挑选新时钟。新 A 留存 55 个逐槽快照，与已有 B 模型快照配对；两条完整 32 字状态轨迹各自与对应旧原版完全相同。

| 关卡 / 差异帧 | A / B 弹槽 | A / B 活动弹数 | 先退场的一端 |
| --- | --- | --- | --- |
''' + table + '''

每个差异帧的前一帧，都找到一对唯一的完整出生帧／弹种族／运动字段匹配。两端均为已命中状态 2，动画都存在，文件 9／脚本 6、sprite 29、绘制模式 1 相同；位置、尺寸和缩放相同，旋转角与浮点寄存器 0 不同。旋转等于弹角度加该寄存器，直接决定四角是否已经全部越过上边界。各差异帧恰有这一对的退场结果不同；较晚的一发在下一次 Player 更新也退场。

仅出生帧／弹种族不足以唯一匹配，多发子弹会共享这个分组。本次保留实际分组复数，使用完整运动字段确认边界内唯一性，没有凭同槽号或弹种猜测身份。

## 原版指令组件

沿用哈希冻结的单弹组件，执行原版 `0x4510b0` 完整更新和 `0x479560` 四角计算。控制边界只有 ANM 查找、释放和安全 cookie 返回，输入明确来自模型快照，不是原版实际玩法抓帧。九对差异前输入各运行两端原样和只交换旋转角的控制，再对每个较晚退场端运行下一帧，共 45 例。

27 例原样输入、18 例旋转交换输入的全部 540 个四角坐标字都逐位相同；18 个只换旋转角的控制均反转退场，释放调用与退场完全一致。因此在这些明确输入下，移植的出屏／释放决定与原版指令一致，不能靠修补计数或固定随机值处理旧差异。

最初迁移 driver 时未调整其相对仓库根路径，被目录保护立即拒绝，失败输出保留；修正工具路径后才运行。初始审计中的“出生族必为单发”假定也被真实复数分组拒绝；完整运动键唯一性通过后才计入上述结论。正式游戏没有因此改动。

## 仍缺什么

这把此前仅针对两个合成时刻变化的[寿命定位](TH14_SHOT_LIFETIME_NOV05.md)扩展到了九处旧原版计数差异对应的模型机制。旧 A 原版没有这些帧的逐槽 VM／几何，不能把模型的角度当成当时原版直接读数。后续应补不同实际观察配置下的原版有界逐槽／随机消耗证据，继续核对完成和读取顺序；不需要再重跑相同的模型轨迹来累计通过数。

原版完整模式覆盖、独立调度、普通原版 GUI、浏览器侧栏故障、全部保存分支、离线和整局 GPU 像素／PCM 继续。整作 1:1 未完成，严格模式通过数未增加。原始状态、随机值、录像、资源和二进制留本地；[公开元数据](th14-original-nine-shot-model-nov05.json)只有计数／差异／标识／路径／哈希。

复核入口为 `tools/th14-original-nine-shot-model-nov05.py`、`tools/th14-original-nine-shot-audit-nov05.py`、`tools/th14-original-nine-shot-component-nov05.py`。已有采集目录拒绝覆盖；封存结果可用 `python tools/th14-original-nine-shot-evidence-nov05.py --check` 核对。测试全程静音，没有启动新的原版进程或复制大资源。
'''
    data = (json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode()
    if check:
        assert PUBLIC.read_bytes() == data and DOC.read_bytes() == doc.encode()
    else:
        assert not PUBLIC.exists() and not DOC.exists()
        PUBLIC.write_bytes(data)
        DOC.write_bytes(doc.encode())
    print(json.dumps(dict(verifiedModelExplanation=True, countDifferenceFrames=9,
                         retailCases=45, rotationOnlyControls=18, publicBytes=len(data),
                         oldNineDifferencesClosed=False, completeGame=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    main(parser.parse_args().check)
