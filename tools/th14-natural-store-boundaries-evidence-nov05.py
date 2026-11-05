"""Public metadata for separate original-bound worker store acknowledgements."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/natural-store-boundaries-nov05'
OLD=R/'artifacts/th14/original-nine-shot-native-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest()
PUBLIC=R/'docs/porting/th14-native-store-boundaries-nov05.json'
DOC=R/'docs/porting/TH14_NATIVE_STORE_BOUNDARIES_NOV05.md'


def main(check):
    bindings={}
    def raw(path):
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    boundary=load(H/'native-boundaries.json');build=load(H/'build-retry1/observer-build.json')
    assert boundary['verifiedNativeAcknowledgementEdges']and boundary['logicalAcknowledgementBoundariesOnly']
    assert build['engineObjectsReusedForThisLink']==141 and build['engineSourcesRecompiledForThisLink']==0
    assert SHA(raw(H/'build-retry1/observer.wasm'))==build['wasmSha256']
    fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-natural-store-scheduler-nov05.cpp'
    assert SHA(raw(fixture))==build['observerSourceSha256']
    finish=fixture.read_text(encoding='utf8').split('API(natural_store_finish)',1)[1]
    assert 'e.finished=true' in finish and 'e.observation.reset()'in finish
    assert 'before_rng_boundary='not in finish and 'before_initial_update='not in finish
    for path,row in boundary['evidenceBindings'].items():
        data=raw(R/path);assert len(data)==row['bytes']and SHA(data)==row['sha256']
    n=OLD/'prefix-slots-v2/native'
    stores=[json.loads(line)for line in raw(n/'replay-rng-store-events.jsonl').splitlines()if json.loads(line)['stage']==3]
    access=[json.loads(line)for line in raw(n/'script-rng-access-events.jsonl').splitlines()]
    words=lambda row:struct.unpack('<4I',bytes.fromhex(row.get('rngHex',row.get('rngHexAtObservation'))))
    expected=[words(stores[0]),words(access[0]),words(stores[2]),words(stores[3])]
    runs=[]
    for case in ['off','on','negative']:
        home=H/case;result=load(home/'result.json');report=load(home/'model/natural-store-report.json')
        data=raw(home/'model/natural-store-observations.u32');assert len(data)==4*12*4
        observations=list(struct.iter_unpack('<12I',data));assert [row[0]for row in observations]==[0,1,2,3]
        assert all(row[1:3]==(30744,3)for row in observations)
        differences=[dict(point=i,word=j)for i,row in enumerate(observations)for j in range(4)if row[3+j]!=expected[i][j]]
        assert differences==report['differences']
        offsets=[(row[8]|row[9]<<32)-boundary['storeReceiptNs'][i]for i,row in enumerate(observations)]
        assert len(set(offsets))==1
        assert report['activeEffectsRestored']and report['lateInstalledAuditorPreserved']
        if case=='negative':
            assert result['strictDriverExitCode']==result['rawVerifierExitCode']==1
            assert differences==[dict(point=2,word=0),dict(point=3,word=0)]
            model=load(home/'model/report.json');assert model['differenceCounts']=={'21':4256,'22':338}
            script=[row for row in struct.iter_unpack('<16I',raw(home/'model/rng-register-audit.u32'))if row[3]==0]
            assert script[0][4]!=access[0]['valueRetainedByTrappedInstruction']
            negative=dict(deliberateBeforeReadVariant=True,strictDriverExitCode=1,rawVerifierExitCode=1,
                perStoreDifferences=differences,stateDifferenceCounts=model['differenceCounts'],
                firstActualRngReadAlreadyDiffers=True,negativeAcceptedAsGameplay=False)
        else:
            assert result['strictDriverExitCode']==result['rawVerifierExitCode']==0 and not differences
            expanded=load(home/'expanded-verified.json')
            assert expanded['verifiedExpandedFiniteComparison']and expanded['perStoreAcknowledgementDiagnostic']
            assert expanded['actualOriginalInstructionAccesses']==66 and expanded['pairedNext32Calls']==33
            assert expanded['extraPortableRowsNotAccepted']==24
            assert expanded['verifierSha256']==SHA(raw(R/'tools/th14-verify-natural-store-boundaries-nov05.py'))
            runs.append({key:expanded[key]for key in ['case','callbacks','comparedCameraWords','vm303Rows',
                'combatCheckpoints','orderedPublications','actualOriginalInstructionAccesses','extraPortableRowsNotAccepted']})
    for name in ['selected-state.u32','full-camera.u32','replay-cursor.u32','portable-hud.u32']:
        assert raw(H/'off/model'/name)==raw(H/'on/model'/name)
    before=raw(H/'off/driver.mjs');negative_source=raw(H/'negative/driver.mjs')
    assert before.count(b'...naturalBoundaryTimes,0')==1
    assert before.replace(b'...naturalBoundaryTimes,0',b'...naturalBoundaryTimes,1')==negative_source
    slots=load(H/'slot-audit.json');assert slots['allComparedFieldsEqual']and not slots['uncomparedGeometry']
    assert slots['snapshotPairs']==55 and slots['geometryVms']==3117 and slots['comparedFields']['quadWords']==37404
    assert slots['vmAvailability']=={'bothPresent':3117,'bothAbsent':26}
    for path,row in slots['evidenceBindings'].items():
        data=raw(R/path);assert len(data)==row['bytes']and SHA(data)==row['sha256']
    for name in ['th14-natural-store-boundaries-nov05.py','th14-build-natural-store-scheduler-nov05.py',
                 'th14-compare-natural-store-boundaries-nov05.py']:
        raw(R/'tools'/name)
    assert (H/'verification-v1/verifier.py').exists()
    output=dict(schema='th14/native-store-boundaries-public/1',verifiedFinitePerStoreAcknowledgement=True,
        nativeTraceReused=True,newOriginalProcessesLaunched=0,engineObjectsReused=141,productionChanged=False,
        acknowledgements=boundary['acknowledgementEdges'],ownerStage=2,objectIndex=6,
        firstPrimitive=0,firstAnimation=8,nextPrimitive=1,nextAnimation=9,callback=30744,
        realReplayRngRestoreJobUsed=True,realStageSnapshotCopyUsed=True,
        observedStoreStatesCompared=4,observedRngWordsCompared=16,all16WordsEqual=True,
        counterClearAndSnapshotNotDeliveredWithScriptSeed=True,
        effectsAndScopeRetired=True,lateAuditorCallbackChainPreservedByTransparentGuard=True,
        positiveRuns=runs,readonlyProbeTransparentForCapturedState=True,negative=negative,
        actualNativeSlots={key:slots[key]for key in ['snapshotPairs','comparedFields','geometryVms','vmAvailability',
            'extraNativeSnapshotsNotAccepted','completeVmMemoryCompared','quadExecutionIsComponentReconstruction']},
        earlierVerifierSourceAndReportsRetained=True,nativeRngOrVmValuesSuppliedToEngine=False,
        logicalAcknowledgementBoundariesOnly=True,exactMainInstructionAtEarlierWorkerStoreAccepted=False,
        crossThreadExecutionTimesRecovered=False,independentTimingAccepted=False,
        ordinaryOriginalGuiAccepted=False,oldNineHistoricalDifferencesClosed=False,
        wholePixelsOrPcmCompared=False,strictNaturalModePassCountIncreased=False,
        completeGame=False,nativeEquivalent=False,rawObservationContentsUploaded=False,
        evidenceBindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()))
    doc='''# TH14 原版约束的分步恢复交付（2026-11-05）

沿用上一轮原版自然交错记录，把录像恢复拆成真实 `ReplayRngRestoreJobTh14` 的三次存储和独立全局复制。新诊断不再把计数清零／全局复制一起提前到脚本种子读取后。两个 35,000 回调复算通过全部原有检查，四组共 16 个 RNG 状态字与原版分别一致；故意把脚本种子恢复移到读取前的负例被严格拒绝。正式玩法未改，独立调度和整作 1:1 未完成。

## 原版约束与新交付

输入复用[原版自然 RNG 交错](TH14_NATURAL_RNG_OVERLAP_NOV05.md)的完整封存记录，没有再启动原版或复制资源。三面第 30,744 个 Player 之后，当前对象属于原二面背景、对象 6；原版实际 VM 数组和 primitive 对应如下。

| 工作线程动作 | 交付所用的主线程确认边界 |
| --- | --- |
| 玩法种子写入 | primitive 0／animation 8 的 VM 调用前 |
| 脚本种子写入 | 同一 VM 第一次脚本 RNG 已保留输入后 |
| 玩法调用数清零 | 同一 VM 返回后 |
| 录像全局复制 | primitive 1／animation 9 的下一 VM 调用前 |

原版工作线程上下文中的主线程 PC 分别为 `0x40f2a2`、`0x403376`、`0x40f2a7`、`0x40f2a2`，且都有对应待处理的硬件命中。原版数组／primitive 索引、已观察 VM 调用身份和下一调用的 ECX 指针分别核对。第一次数值读取与脚本种子写入之间的数据流继续由真实寄存器恢复验证，不能拿较晚的全局快照代替指令保留值。

这些是基于已停住上下文的逻辑确认边界，不声称调试事件接收时刻就是完整跨线程执行时间，也不把较早每次工作线程存储唯一定位到主线程某一条精确指令。旧记录缺失的历史 VM 几何没有补造。

新增 C++ 仅为观察宿主：资源 effects 按确认边界分别解除每一步等待，实际种子仍从完整录像读取，存储由生产恢复 job 执行，全局复制仍由真实 GameSession 执行。没有向 RNG 或 VM 提供原版结果。宿主结束后释放观察 scope、恢复原资源 effects；回调保留透明守卫，避免覆盖之后安装的只读审计链。141 个哈希绑定玩法对象全部复用，没有重编正式玩法。

## 实际通过范围

关闭／开启只读弹槽观察各执行 35,000 回调，原严格 driver 与独立原始文件核验都通过。32 项状态、2,624,925 相机数据项、4 项游标、2 项 HUD、66 次实际 RNG 访问、753 行 VM 的选定 303 字段、354 个战斗检查点、初始 3,275 项发布顺序一致。24 条额外模型访问仍单列未验收。四份状态／相机／游标／HUD 输出在观察开关之间逐字节相同。

恢复 job 的前三个存储检查点与实际全局复制之后另各记录一次状态，四组共 16 个 RNG 字分别与原版对应样本一致；所有时刻均是同一个坐标变换下的原始记录边界。脚本种子存储对应第一条 mix 的全局样本及工作线程 AX，不使用已经被主线程写回覆盖的晚到内存。

55 对实际原版／模型快照继续按槽与句柄核对：3,143 次活动弹字段、3,117 个存在动画的选定字段，以及原版指令重建的 37,404 四角坐标字一致；26 次两端动画已不存在也保留一致。四份额外原版快照未配对，未计通过。未比较完整 VM 内存或 GPU 帧缓冲。

## 负例与剩余范围

负例只把“保留输入后恢复”改成“读取前恢复”，其他输入和时刻保持相同；恢复动作仍经真实 job 执行。它在第一条实际 RNG 读取就不同，严格 driver 和原始核验均返回 1，完整状态中留下 4,256 个脚本种子差和 338 个调用数差，后两组存储状态的种子也不同。负例没有作为玩法通过或被丢弃。

该结果验证真实分步恢复代码在明确原版约束下的行为，未增加普通严格模式通过数。原版独立调度、全部模式／普通 GUI 流程、浏览器侧栏／所有保存分支／离线和整局原版像素／PCM仍继续；整作 1:1 未完成。

## 本地复核

`tools/th14-natural-store-boundaries-nov05.py` 核验封存的原版上下文；`tools/th14-build-natural-store-scheduler-nov05.py` 复用 141 对象链接观察宿主；`tools/th14-compare-natural-store-boundaries-nov05.py` 运行 off／on／negative；`tools/th14-verify-natural-store-boundaries-nov05.py` 复用全部相机、游标、RNG 与实际弹槽／几何核验。初版核验器的路径还原检查拒绝了一次泛化替换，旧来源和报告留档后修成完整路径替换，未改变比较门槛或重跑已通过的模型。

[公开索引](th14-native-store-boundaries-nov05.json)只含源码、计数、差异、身份、路径与哈希。原始种子／cookie、内存／寄存器、资源、录像、图片、PCM 和二进制留本地。可用 `python tools/th14-natural-store-boundaries-evidence-nov05.py --check` 复核。所有测试保持静音。
'''
    data=(json.dumps(output,ensure_ascii=False,indent=2)+'\n').encode()
    if check:assert PUBLIC.read_bytes()==data and DOC.read_bytes()==doc.encode()
    else:
        assert not PUBLIC.exists()and not DOC.exists();PUBLIC.write_bytes(data);DOC.write_bytes(doc.encode())
    print(json.dumps(dict(verifiedPerStoreAcknowledgements=True,runs=2,callbacksPerRun=35000,
        observedRngStates=4,negativeRejected=True,nativeSlotPairs=55,publicBytes=len(data),completeGame=False)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    main(parser.parse_args().check)
