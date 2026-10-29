"""Extend a frozen coverage inventory with one explicit native run, without rescanning old artifacts."""
from pathlib import Path
import argparse,array,hashlib,json,subprocess

R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/mode-coverage-oct29'
BASE='babc4e04e4b37f98cbf89d5117065e084fbd8b26';SHA=lambda b:hashlib.sha256(b).hexdigest()

def results():
    names=['docs/porting/th14-mode-acceptance-inventory-oct25.json','docs/porting/TH14_MODE_ACCEPTANCE_OCT25.md']
    sources={name:subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),'show',BASE+':'+name])for name in names}
    baseline=json.loads(sources[names[0]]);report=json.loads(sources[names[0]])
    native=H/'marisaa-easy-toho-native';original_raw=(native/'report.json').read_bytes();original=json.loads(original_raw)
    initial_raw=(native/'untouched-first-player.json').read_bytes();initial=json.loads(initial_raw)
    raw=(native/'selected-state.u32').read_bytes();words=array.array('I',raw)
    assert initial['words'][27:31]==[1,0,0,1]and len(raw)==80324*128 and SHA(raw)==original['selectedSha256']
    stages=sorted(set(words[30::32]));assert stages==[1,2,3,4,5]
    assert original['childExited']and original['observedForcedReplayEndMenu']and not original['error']
    assert original['hardwareBreakpointsOnly']and original['instructionBytesPatched']==original['rngOrCounterWrites']==0
    assert original['gameStateWordWrites']==1 and original['caseInitialization']['attractBitClearOnly']
    assert original['sourceFullReplaySha256']=='b1d9e367e7e5e29e0d7bd08fe493062164171d5d88c52f954b8565fcd2e81a2d'
    model=H/'marisaa-easy-toho-prefix30000-warm-flag/report.json';model_raw=model.read_bytes();compared=json.loads(model_raw)
    assert compared['callbacks']==30000 and compared['diagnosticPrefixOnly']and compared['allRaw32ByteIdentical']
    assert raw[:30000*128]==(model.parent/'selected-state.u32').read_bytes()
    failed=H/'marisaa-easy-toho-prefix48000-warm-flag/report.json';failed_raw=failed.read_bytes();failure=json.loads(failed_raw)
    assert failure['callbacks']==48000 and not failure['allRaw32ByteIdentical']and failure['firstDifference']['index']==30990
    case=next(row for row in report['cases']if row['key']=='marisaa-easy')
    record=dict(path=native.relative_to(R).as_posix(),reportSha256=SHA(original_raw),initialSnapshotSha256=SHA(initial_raw),
        selectedSha256=SHA(raw),callbacks=80324,stagesObserved=stages,naturalReplayEndObserved=True,clearCompletionNotAsserted=True,
        intactOriginalReplayDeclared=True,instructionBytesPatched=0,rngOrCounterWrites=0,replaySha256=original['sourceFullReplaySha256'],
        selected32ComparisonReports=[],preferredComparisonPath=None,
        partialSelected32ComparisonReports=[dict(path=model.relative_to(R).as_posix(),reportSha256=SHA(model_raw),callbacks=30000,
            wasmSha256=compared['wasmSha256'],scope='Explicit30000-callback selected32 prefix; separately recomputed camera/HUD/VM/combat/publication fields. Longer48000 prefix strictly fails; no full-run acceptance.')],
        retainedLongerStrictFailures=[dict(path=failed.relative_to(R).as_posix(),reportSha256=SHA(failed_raw),callbacks=48000,firstDifference=failure['firstDifference'])])
    assert all(row['path']!=record['path']for row in case['retainedNaturalRuns'])
    case['retainedNaturalRuns'].insert(0,record);case['allStageEntriesObserved']=False;case['wholeModeEquivalent']=False
    for row,old in zip(report['cases'],baseline['cases']):
        if row['key']!='marisaa-easy':assert row==old
    for path,digest in [(native/'report.json',SHA(original_raw)),(model,SHA(model_raw)),(failed,SHA(failed_raw))]:
        report['reportBindings'][path.relative_to(R).as_posix()]=digest
    report.update(schema='th14/mode-acceptance-inventory/3',date='2026-10-29',toolSha256=SHA(Path(__file__).read_bytes()),
        explicitExtension=dict(baseSourceCommit=BASE,baseInventorySha256=SHA(sources[names[0]]),
            originalInventoryToolSha256=baseline['toolSha256'],updatedModeOnly='marisaa-easy',otherModesFrozenUnchanged=True,
            oldObservedStages=[1,2,3],newObservedStages=stages,missingStageEntries=[6],fullCapturedRunCompared=False,
            longerStrictFailureRetained=True,completeGame=False))
    assert report['pairsWithNaturalNativeRun']==sum(row['nativeCapturedRunAvailable']for row in report['cases'])==30
    assert report['pairsWithAllStageEntriesObserved']==sum(row['allStageEntriesObserved']for row in report['cases'])==25
    markdown=sources[names[1]].decode('utf8');markdown=markdown.replace('2026-10-26','2026-10-29',1)
    old='| 魔理沙 A | 已观察关卡 1/2/3；需绑定对照 |';assert markdown.count(old)==1
    markdown=markdown.replace(old,'| 魔理沙 A | 已观察关卡 1/2/3/4/5；30000 回调有限对照通过；48000 回调严格失败 |',1)
    marker='| 自机 | Easy | Normal | Hard | Lunatic | Extra |'
    note='2026-10-29 仅增补魔理沙 A Easy：新原始输入在 80,324 回调、五面自然提前结束，六面入口仍缺失；前 30,000 回调的有限对照通过，延长至 48,000 回调仍在三面换关 RNG 严格失败。其余模式保留冻结清单，未重新扫描全部历史产物。详见 [暖启动标志及后续失败](TH14_WARM_REPLAY_FLAGS_OCT29.md)。\n\n'
    markdown=markdown.replace(marker,note+marker,1)
    inventory=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if b'\r\n'in sources[names[0]]:inventory=inventory.replace('\n','\r\n')
    return {names[0]:inventory.encode(),names[1]:markdown.encode()}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for name,raw in results().items():
        if args.check:assert (R/name).read_bytes()==raw
        else:(R/name).write_bytes(raw)
    print(json.dumps(dict(extendedMode='marisaa-easy',observedStages=[1,2,3,4,5],missingStages=[6],naturalModePairs=30,allStageEntryModePairs=25,wholeModeEquivalent=False)))
if __name__=='__main__':main()
