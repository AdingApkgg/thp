"""Prepare a source/evidence-only GitHub commit after the current replay audit."""
from pathlib import Path
import ast
import hashlib
import json
import os
import subprocess

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/option-refresh-oracle-nov13'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
q = load(H / 'current-replay/qualified.json')
v = load(H / 'current-replay/shot-vm303-qualified.json')
b = load(H / 'browser/build.json')
component = load(H / 'qualified.json')
assert q['allChildrenWorkersHostsGpuAndClockRetired']
assert q['cppCallbacks'] == 35000 and q['nativeSlotSnapshotPairs'] == 123
assert not q['rawDifferenceCounts']['state32'] and not q['rawDifferenceCounts']['hud2']
assert not q['rawDifferenceCounts']['cursor4'] and not q['slotDifferenceCounts']
assert v['differentWords'] == 0
assert b['unitsRecompiled'] == 1 and b['objectsVerifiedReused'] == 145
for name, digest in b['sourceBindings'].items():
    assert sha(R / name) == digest, name
summary = dict(
    schema='thp/th14-option-current-regression/1',
    sourceBase='b8e36ef27d96238352f5edaf9b368ca23394ceb3',
    localSourceChanges=q['localSourceChanges'],
    componentSelections=6, componentSteps=90, componentComparedWords=183060,
    componentDifferentWords=0, otherTitleObjectPairs=3,
    replayCallbacks=q['cppCallbacks'], nativeSlotSnapshotPairs=q['nativeSlotSnapshotPairs'],
    selected32Hud2Cursor4Exact=True, rawStrict113Exact=q['rawStrict113AllWordsExact'],
    rawStrict113Prefix=q['rawStrict113Prefix'],
    rawDifferenceCounts=q['rawDifferenceCounts'], firstRawDifferences=q['firstRawDifferences'],
    slotCompared=q['slotCompared'], slotDifferenceCounts=q['slotDifferenceCounts'],
    vm303CapturedPairs=v['capturedVmPairs'], vm303MeasuredWords=v['comparedWords'],
    vm303DifferentWords=v['differentWords'], unmeasuredNativeLinkWords=v['unmeasuredNativeLinkWords'],
    complete303PerVmAccepted=v['complete303WordsPerVmAccepted'],
    browserUnitsRecompiled=1, browserObjectsVerifiedReused=145,
    browserWasmSha256=b['sha256'], browserLoaderSha256=b['loaderSha256'],
    allOwnedResourcesRetired=True, silent=True, newOriginalRuns=0,
    executedDriverExitCode=1, executedCaptureCompleteFlag=False,
    independentlyQualifiedPredeclaredCaptureScope=True,
    failedReportAndExitCodePreserved=True, laterRuntimeV2NotRerun=True,
    referenceRowsNotSuppliedToEngine=True, noPerFileReadinessSchedule=True,
    browserUiAccepted=False, deployed=False, completeGame=False,
    evidenceBindings={p.relative_to(R).as_posix():sha(p) for p in [
        H / 'qualified.json', H / 'current-replay/qualified.json',
        H / 'current-replay/shot-vm303-qualified.json', H / 'browser/build.json',
        H / 'current-replay/cpp-terminal-receipt.json',
        H / 'current-replay/capture-boundary-qualified.json', Path(__file__)]})
p = R / 'docs/porting/th14-option-current-regression-nov13.json'
assert not p.exists()
p.write_text(json.dumps(summary, indent=2) + '\n')
camera = ('全部 113 字也相同' if q['rawStrict113AllWordsExact'] else
          f"113 字严格前缀为 {q['rawStrict113Prefix']:,}；相机缓存差异仍保留")
paragraph = (
    '\n## 当前源码的有限录像回归\n\n'
    '使用包含本处初始化修正的当前源码，实际 Application／WASI 工作线程／ANGLE GLES '
    '完成一次 35,000 回调前缀。复用已结束的低暂停原版记录，原版只带声明的六字节入口观察器；'
    '本次未启动新的原版游戏。执行端不读取参考行，不补 RNG／年龄／完成帧。'
    'selected32、HUD 两字和录像游标四字全部相同，123 个输入点的活动弹槽及所测弹／VM／几何字段零差异；'
    f'{camera}。进一步比较 {v["capturedVmPairs"]:,} 个已捕获 VM，'
    f'{v["comparedWords"]:,} 个实测规范字零差异，另有 '
    f'{v["unmeasuredNativeLinkWords"]:,} 个未捕获链接保持未知。'
    '三个历史弹数位置在当前此病例中已一致，不能推广为全部调度／所有模式通过。\n\n'
    '观测脚本 v1 沿用了旧 16,400 回调验收范围，仍期待 68 个弹槽点和两个完整快照，'
    '因实际采齐 123 个点和四个快照而返回 1。原始退出码与 captureComplete=false 均保留；'
    '另按执行前的夹具目标数组和构建记录核验全部覆盖，再独立进行上述差异比较。'
    '没有修改原始报告、缩减字段或重跑录像。后续 v2 脚本改用原先完整范围，未重新执行游戏。\n\n'
    '浏览器运行包已重建，仅重编 PlayerFrame，核验复用其余 145 个对象；'
    '尚未部署，线上仍为 b8e36ef2。当前回归使用既有本地音频输入，'
    '不作为线上 Vorbis 播放或最终 PCM 验收。全部线程、GPU、文件、异步服务与计时请求已回收。'
    '[当前回归与构建绑定](th14-option-current-regression-nov13.json)。\n')
doc = R / 'docs/porting/TH14_OPTION_INITIAL_STATE_NOV13.md'
text = doc.read_text(encoding='utf8')
assert '## 当前源码的有限录像回归' not in text
old_status = '本处修正目前仅在本地通过，尚未重建浏览器运行包或部署；线上核心仍为 `b8e36ef2`。'
assert text.count(old_status) == 1
text = text.replace(old_status, '本处修正已重建浏览器运行包，尚未部署；线上核心仍为 `b8e36ef2`。')
temp = doc.with_suffix('.option-current.tmp')
temp.write_text(text + paragraph, encoding='utf8')
os.replace(temp, doc)
remaining = R / 'docs/porting/TH14_REMAINING_ACCEPTANCE.md'
text = remaining.read_text(encoding='utf8')
assert 'TH14_OPTION_INITIAL_STATE_NOV13.md' not in text
at = text.index('\n') + 1
entry = ('\n2026-11-13：[Player 历史坐标与僚机初值](TH14_OPTION_INITIAL_STATE_NOV13.md)：'
         '实际原版六自机／九十步／183,060 字零差异；当前源码静音 35,000 回调的 '
         'selected32／HUD／游标、123 个弹槽采样和已测 VM 字一致，历史三处弹数在本病例一致；'
         + camera + '。浏览器仅重编一单元、复用 145，尚未部署。'
         '物理加载 RNG、全模式／普通存档／像素／PCM／浏览器验收继续。\n\n')
temp = remaining.with_suffix('.option-current.tmp')
temp.write_text(text[:at] + entry + text[at:].lstrip('\r\n'), encoding='utf8')
os.replace(temp, remaining)
tool_names = [
    'th14-option-refresh-native-nov13.py', 'th14-build-option-refresh-oracle-nov13.py',
    'th14-run-option-refresh-oracle-nov13.mjs', 'th14-build-option-initial-state-candidate-nov13.py',
    'th14-run-option-initial-state-candidate-nov13.mjs', 'th14-audit-retained-shot-count-inputs-nov13.py',
    'th14-option-initial-state-other-title-controls-nov13.py', 'th14-qualify-option-initial-state-nov13.py',
    'th14-build-option-current-replay-nov13.py', 'th14-run-option-current-replay-nov13.mjs',
    'th14-prepare-option-current-replay-audits-nov13.py', 'th14-audit-option-current-replay-nov13.py',
    'th14-audit-option-current-replay-vm303-nov13.py', 'th14-build-option-browser-nov13.py',
    'th14-qualify-option-capture-boundary-nov13.py',
    'th14-audit-option-current-replay-boundary-nov13.py',
    'th14-run-option-current-replay-v2-nov13.mjs',
    'th14-prepare-option-publication-nov13.py']
paths = ['runtimes/th12/th12_web/cpp/game/PlayerFrame.cpp',
         *['tools/' + n for n in tool_names],
         'docs/porting/TH14_OPTION_INITIAL_STATE_NOV13.md',
         'docs/porting/th14-option-initial-state-nov13.json',
         'docs/porting/th14-option-current-regression-nov13.json',
         'docs/porting/TH14_REMAINING_ACCEPTANCE.md']
files = []
for name in paths:
    raw = (R / name).read_bytes()
    raw.decode('utf8')
    assert len(raw) < 600000
    if name.endswith('.py'):
        ast.parse(raw)
    files.append(dict(path=name, bytes=len(raw), sha256=sha(R / name)))
gh = 'C:/Program Files/GitHub CLI/gh.exe'
head = json.loads(subprocess.check_output([gh, 'api', 'repos/AdingApkgg/thp/commits/main'], timeout=30))
assert head['sha'] == '61622c82bbb37406ed4fc0ad7634b85dd29e3931'
plan = dict(previousHead=head['sha'], publicEvidenceAuthorized=True,
            rawAssetsOrObservationsIncluded=False, files=files,
            commitMessage='Initialize TH14 Player history and inactive option coordinates\n\n'
            'Match actual retail initialization through six option/stage-reset sequences. '
            'Current 35k callback replay selected state and measured shot fields match; '
            'keep camera, physical loading and whole-game acceptance open.')
(H / 'release-reviewed-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
(H / 'publish-release-reviewed.py').write_bytes((R /
    'artifacts/th14/player-initialization-oracle-nov13/publish-release-reviewed.py').read_bytes())
print(json.dumps(dict(files=len(files), bytes=sum(f['bytes'] for f in files),
                      parent=head['sha'], browserWasmSha256=b['sha256'])))
