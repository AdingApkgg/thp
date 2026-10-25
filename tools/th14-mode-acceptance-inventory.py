"""Inventory retained Native stage coverage without declaring mode equivalence."""
import array
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
NAMES=['reimua','reimub','marisaa','marisab','sakuyaa','sakuyab']
DISPLAY=['灵梦 A','灵梦 B','魔理沙 A','魔理沙 B','咲夜 A','咲夜 B']
DIFFICULTIES=['Easy','Normal','Hard','Lunatic','Extra']
GATES={
    'camera':('camera-report.json','allCameraWordsEqual','相机'),
    'hud':('hud-report.json','allHudWordsEqual','HUD'),
    'animation':('live-report.json','allLiveValuesEqual','动画'),
    'combat':('combat-snapshots.json','allCapturedCombatWordsEqual','战斗对象'),
}


def additional_gates(path,comparison,bindings):
    results={}
    for name,(filename,field,_)in GATES.items():
        source=path.parent/filename
        if not source.exists():results[name]=None;continue
        raw=source.read_bytes();d=json.loads(raw)
        if 'callbacks'in d:assert d['callbacks']==comparison['callbacks'],str(source)
        if d.get('wasmSha256'):assert d['wasmSha256']==comparison['wasmSha256'],str(source)
        assert isinstance(d.get(field),bool),str(source)
        bindings[source.relative_to(ROOT).as_posix()]=SHA(raw)
        results[name]=d[field]
    return results

def main():
    captures={};bindings={}
    for home in (ROOT/'artifacts/th14').iterdir():
        if not home.is_dir()or not home.name.startswith('retail-'):continue
        report=home/'report.json';initial=home/'untouched-first-player.json';raw_path=home/'selected-state.u32'
        if not all(p.exists()for p in (report,initial,raw_path)):continue
        try:
            raw_report=report.read_bytes();d=json.loads(raw_report);selection=json.loads(initial.read_bytes())['words'][27:31]
        except(KeyError,ValueError,OSError):continue
        if len(selection)!=4 or selection[3]not in (1,7)or not d.get('observedForcedReplayEndMenu')or d.get('error')or not d.get('callbacks'):continue
        c,s,diff,first=selection
        if c not in range(3)or s not in range(2)or diff not in range(5)or first!=(7 if diff==4 else 1):continue
        raw=raw_path.read_bytes()
        if len(raw)!=d['callbacks']*128:continue
        words=array.array('I',raw);stages=sorted(set(words[30::32]));assert len(stages)<=7
        record=dict(path=home.relative_to(ROOT).as_posix(),reportSha256=SHA(raw_report),initialSnapshotSha256=SHA(initial.read_bytes()),selectedSha256=SHA(raw),callbacks=d['callbacks'],stagesObserved=stages,naturalReplayEndObserved=True,clearCompletionNotAsserted=True,intactOriginalReplayDeclared=d.get('intactOriginalReplay'),instructionBytesPatched=d.get('instructionBytesPatched'),rngOrCounterWrites=d.get('rngOrCounterWrites'),replaySha256=d.get('sourceFullReplaySha256'))
        captures.setdefault((c,s,diff),[]).append(record);bindings[report.relative_to(ROOT).as_posix()]=SHA(raw_report)
    comparisons={};partial_comparisons={}
    for directory in ['damage-area-snap-oct25','player-aim-oct25','boss-name-input-oct25','vm-interrupt-cache-oct25','stage-item-retirement-oct25']:
        home=ROOT/'artifacts/th14'/directory
        if not home.exists():continue
        for path in home.rglob('report.json'):
            try:raw=path.read_bytes();d=json.loads(raw)
            except(ValueError,OSError):continue
            digest=d.get('nativeSelectedSha256')
            if digest and d.get('allRaw32ByteIdentical')and d.get('callbacks')and not d.get('diagnosticPrefixOnly'):
                gates=additional_gates(path,d,bindings)
                comparisons.setdefault(digest,[]).append(dict(path=path.relative_to(ROOT).as_posix(),reportSha256=SHA(raw),callbacks=d['callbacks'],wasmSha256=d.get('wasmSha256'),additionalObservedGateResults=gates,reportedAdditionalGateFailures=[name for name,value in gates.items()if value is False],scope='Reported full captured-run selected32 equality only; additional failures remain explicit. Each version and field scope requires its own verification.'))
            if d.get('nativeInitialSnapshotSha256')and d.get('allRaw32ByteIdentical')and d.get('diagnosticPrefixOnly'):
                partial_comparisons.setdefault(d['nativeInitialSnapshotSha256'],[]).append(dict(path=path.relative_to(ROOT).as_posix(),reportSha256=SHA(raw),callbacks=d['callbacks'],wasmSha256=d.get('wasmSha256'),scope='Reported selected32 prefix equality only, not a full captured-run pass.'))
    rows=[]
    for shot in range(6):
        for diff in range(5):
            records=captures.get((shot//2,shot%2,diff),[]);expected=[7]if diff==4 else list(range(1,7))
            for record in records:
                record['selected32ComparisonReports']=comparisons.get(record['selectedSha256'],[])
                record['selected32ComparisonReports'].sort(key=lambda r:(all(v is True for v in r['additionalObservedGateResults'].values()),sum(v is not None for v in r['additionalObservedGateResults'].values()),-len(r['reportedAdditionalGateFailures']),r['path']),reverse=True)
                record['preferredComparisonPath']=record['selected32ComparisonReports'][0]['path']if record['selected32ComparisonReports']else None
                record['partialSelected32ComparisonReports']=partial_comparisons.get(record['initialSnapshotSha256'],[])
            records.sort(key=lambda r:(len(r['stagesObserved']),bool(r['selected32ComparisonReports']),max((p['callbacks']for p in r['partialSelected32ComparisonReports']),default=0),r['callbacks']),reverse=True)
            best=records[0]if records else None
            rows.append(dict(key=NAMES[shot]+'-'+DIFFICULTIES[diff].lower(),character=shot//2,subtype=shot%2,difficulty=diff,expectedStages=expected,nativeCapturedRunAvailable=bool(best),allStageEntriesObserved=bool(best and best['stagesObserved']==expected),retainedNaturalRuns=records,wholeModeEquivalent=False))
    report=dict(schema='th14/mode-acceptance-inventory/2',date='2026-10-26',cases=rows,modePairs=30,pairsWithNaturalNativeRun=sum(r['nativeCapturedRunAvailable']for r in rows),pairsWithAllStageEntriesObserved=sum(r['allStageEntriesObserved']for r in rows),preferredCaptureRule='Prefer more observed stages, then a reported full selected32 comparison, then the longest compared prefix; loading callback count breaks remaining ties.',scope='An inventory of retained actual stage entries and separately scoped reported selected32 comparisons, with additional observed gate failures. Missing gates are null, never passed. Neither replay end nor observing all stage entries proves a clear, all objects, ordinary menu initialization, pixels, PCM, persistence or mode equivalence.',reportBindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()),completeGame=False,nativeEquivalent=False)
    output=ROOT/'docs/porting/th14-mode-acceptance-inventory-oct25.json';output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    lines=['# TH14 模式验收清单 · 2026-10-26','','本表依据本机已保留的原版记录生成。自然录像结束、进入全部关卡、通关和完整模式等价分别判断；本表不把前三者自动视为 1:1。所选 32 字相同的记录也可能存在其他字段差异，以下单独列出；缺少门槛报告不算通过。','', '| 自机 | Easy | Normal | Hard | Lunatic | Extra |','| --- | --- | --- | --- | --- | --- |']
    for shot,name in enumerate(DISPLAY):
        cells=[]
        for row in rows[shot*5:shot*5+5]:
            if not row['nativeCapturedRunAvailable']:cells.append('缺完整原版记录');continue
            best=row['retainedNaturalRuns'][0];stages='/'.join(map(str,best['stagesObserved']));compared=bool(best['selected32ComparisonReports']);partial=max((r['callbacks']for r in best['partialSelected32ComparisonReports']),default=0)
            suffix='；有所选状态对照'if compared else'；部分所选状态对照（'+str(partial)+' 回调）'if partial else'；需绑定对照'
            failures=set(best['selected32ComparisonReports'][0]['reportedAdditionalGateFailures'])if compared else set()
            if failures:suffix+='；另有'+'／'.join(GATES[name][2]for name in GATES if name in failures)+'差异'
            cells.append('已观察关卡 '+stages+suffix)
        lines.append('| '+name+' | '+' | '.join(cells)+' |')
    lines+=['',f"已有 {report['pairsWithNaturalNativeRun']} 个组合的自然结束记录，{report['pairsWithAllStageEntriesObserved']} 个组合观察到全部目标关卡入口。部分记录在二、三或五面结束，不能算完整六面覆盖。表中优先展示额外门槛齐全且通过的已有对照，各历史版本及失败报告均保留在结构化清单中。对照只按记录的输入、构建和所选字段生效，旧版结果不自动继承至当前源码。",'', '当前最先补齐尚缺原版记录的模式及提前结束的标准流程；正在进行的采集未结束时不会写成通过。详细路径、版本与哈希见 [结构化清单](th14-mode-acceptance-inventory-oct25.json)。生产图像、音频和浏览器范围继续按 [剩余验收清单](TH14_REMAINING_ACCEPTANCE.md) 独立验收。','']
    (ROOT/'docs/porting/TH14_MODE_ACCEPTANCE_OCT25.md').write_text('\n'.join(lines),encoding='utf8')
    print(json.dumps({k:report[k]for k in ['modePairs','pairsWithNaturalNativeRun','pairsWithAllStageEntriesObserved']}))

if __name__=='__main__':main()
