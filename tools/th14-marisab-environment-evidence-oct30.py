"""Audit the real KMK playback boundary and crossed Application environments.

Warm and ordinary initializations are different. Report all 32 field failures;
alignment of unique positive stage clocks is diagnostic, never a whole-mode pass.
"""
from pathlib import Path
import argparse,collections,hashlib,io,json,struct,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
def verify(home):
 bindings={}
 def read(path):
  raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]={'bytes':len(raw),'sha256':SHA(raw)};return raw
 def load(path):return json.loads(read(path))
 native_home=ROOT/'artifacts/th14/retail-marisab-normal-kmk-callback-hardware-oct26'
 original=load(native_home/'report.json');assert original['callbacks']==19496 and original['childExited']and not original['error']and original['observedForcedReplayEndMenu']
 assert original['caseInitialization']['attractBitClearOnly']and not original['ordinaryMenuReplayInitialization']
 assert original['instructionBytesPatched']==original['rngOrCounterWrites']==0
 source_sha='28d9d29a34cf1dd0e67d67a82c1f0a5f7c508543271e0f1b1e4cbed527ff7353';assert original['sourceFullReplaySha256']==source_sha
 terminal=original['terminalMenuSamples'][-1];assert (terminal['stage'],terminal['controlFrame'],terminal['score'],terminal['lives'])==(2,10142,3270751,0xffffffff)
 initial=load(native_home/'untouched-first-player.json');assert initial['actualInitialTimeGetTimeInput']==433399386 and initial['actualOriginalSecurityCookie']==1759244761
 warm=load(home/'verified.json');assert warm['verifiedFiniteEvidence']and warm['callbacks']==19496 and warm['allSelected32Equal']and warm['allCamera25Equal']and warm['allHud2Equal']and warm['allVm303AndRegistryOrderEqual']and warm['allCapturedCombatWordsEqual']
 assert warm['vm303Rows']==52 and warm['combatCheckpoints']==212 and warm['orderedPublications']==1770
 for name,row in warm['bindings'].items():assert SHA(read(ROOT/name))==row['sha256'],name
 build=load(home/'application-observer-v2/build.json');assert build['readOnlyBeforePlayerObserver']and build['observerRowsBound']==32768 and len(build['coreObjects'])==141 and len(build['reusedDeviceObjects'])==4
 assert SHA(read(home/'application-observer-v2/application.wasm'))==build['wasmSha256']
 for name,row in build['sourceBindings'].items():assert SHA(read(ROOT/name))==row['sha256'],name
 for row in build['coreObjects']:assert SHA(read(Path(row['path'])))==row['sha256']
 for row in build['reusedDeviceObjects']:assert SHA(read(ROOT/row['path']))==row['sha256']
 core=load(ROOT/'artifacts/th14/replay-construction-oct30/core-build/observer-build.json');assert core['objectBindings']==build['coreObjects']
 tree_raw=subprocess.check_output(['git','-C',str(ROOT/'tools/tmp/github-source-release'),'archive','--format=tar','57a544191704e0ce64cd46de85fe648a3e152097','runtimes/th12/th12_web/cpp/game'])
 with tarfile.open(fileobj=io.BytesIO(tree_raw))as tree:
  for name,digest in core['sourceHashes'].items():assert SHA(tree.extractfile('runtimes/th12/'+name).read())==digest==build['coreSourceHashes'][name]
 original_rows=list(struct.iter_unpack('<32I',read(native_home/'selected-state.u32')));index=collections.defaultdict(list)
 for ordinal,row in enumerate(original_rows,1):index[(row[30],row[0])].append((ordinal,row))
 def compare(rows):
  counts=collections.Counter();first={};paired=0;excluded=collections.Counter()
  for ordinal,row in enumerate(rows):
   key=(row[30],row[0]);target=index[key]
   if row[0]==0:excluded['frozenClockZero']+=1;continue
   if len(target)!=1:excluded['missingOrAmbiguousOriginalClock']+=1;continue
   paired+=1;native_callback,expected=target[0]
   for field,(actual,wanted)in enumerate(zip(row[:32],expected)):
    if actual!=wanted:
     counts[field]+=1;first.setdefault(field,dict(appObservation=ordinal,stage=key[0],battleFrame=key[1],appTick=row[32],nativeCallback=native_callback,field=field,actual=actual,expected=wanted,scratchWord=row[33]))
  extra=[v for k,v in first.items()if k not in (21,22)]
  return dict(actualBeforePlayerRows=len(rows),uniquePositiveClockPairs=paired,unpairedRows=dict(excluded),all32DifferenceCounts={str(k):v for k,v in sorted(counts.items())},firstDifferencePerField={str(k):v for k,v in first.items()},firstAdditionalDifferenceBeyondScriptRng=min(extra,key=lambda x:(x['appTick'],x['field']))if extra else None,strictAll32Equal=not counts,wholeOrdinaryNativeComparisonAccepted=False)
 def run(name):
  folder=home/name;d=load(folder/'report.json');assert d['completed']and not d['error']and d['actualProductionApplicationAndDevices']and d['physicalAudioDevicesOpened']==0 and not d['browserAcceptance']
  assert d['wasmSha256']==build['wasmSha256']and d['buildReportSha256']==SHA(read(home/'application-observer-v2/build.json'))
  assert d['toolSha256']==SHA(read(folder/'run-tool.py'))
  assert d['initialSave']==d['finalSave']=={'replay/th14_01.rpy':{'bytes':77283,'sha256':source_sha}}
  assert SHA(read(folder/'save/replay/th14_01.rpy'))==source_sha
  meta=d['beforePlayerObservation'];raw=read(folder/'player-observations.u32');assert SHA(raw)==meta['sha256']and len(raw)==meta['rows']*34*4 and meta['rows']<=32768 and meta['readOnly']and not meta['gameplayStateOrHostInputsReplaced']
  rows=list(struct.iter_unpack('<34I',raw));assert rows[0][0]==1 and rows[0][30]==1
  for capture in d['captures']:assert SHA(read(folder/capture['file']))==capture['sha256']
  process=load(home/(name+'-process-end.json'));assert process['exitCode']==0
  return d,compare(rows)
 old=load(ROOT/'artifacts/th14/replay-construction-oct30/ordinary-full/report.json');assert not old['completed']and 'Declared state was not reached'in old['error']
 old_end=next(row for row in old['rows']if row['state'][:2]==[2,2]);assert old_end['state'][6]==10142 and old_end['state'][9]==3285179
 control=load(home/'observer-v2-noninvasiveness-control.json');assert control['readOnlyAdapterPreservedCommonPrefix']and control['commonScenarioActions']==13 and control['fullImageAndLiveVmHashesUnchanged']
 control_run=load(home/'application-observer-v2-control/report.json')
 for actual,prior in zip(control_run['actions'],old['actions'][:13]):assert actual['state']==prior['state']and actual['atFrame']==prior['atFrame']and actual['endFrame']==prior['endFrame']
 for key in ['sha256','referenceState','liveAnimations']:assert control_run['captures'][0][key]==old['captures'][0][key]
 ordinary,ordinary_difference=run('application-native-environment-terminal');assert ordinary['frames']==20053 and len(ordinary['checks'])==18
 end,stable=ordinary['actions'][-2:];assert end['state'][:2]==stable['state'][:2]==[2,2]and stable['endFrame']-end['endFrame']==60
 assert end['state'][6]==stable['state'][6]==10142 and end['state'][9]==stable['state'][9]==3270751 and stable['state'][7]==0xffffffff
 assert ordinary['declaredInitialGameTicks']==433399386 and ordinary['captures'][0]['referenceState'][1]==1759244761
 assert set(ordinary_difference['all32DifferenceCounts'])=={'21','22'}and ordinary_difference['uniquePositiveClockPairs']==19254
 crossings=[]
 for name,ticks,cookie in [('application-cross-old-clock-native-cookie',479352152,1759244761),('application-cross-native-clock-old-cookie',433399386,3067924159)]:
  d,difference=run(name);assert d['frames']==15551 and len(d['checks'])==21 and d['actions'][-1]['state'][:2]==[1,2]and d['actions'][-1]['state'][6]==5700
  assert d['declaredInitialGameTicks']==ticks and d['captures'][0]['referenceState'][1]==cookie
  crossings.append(dict(name=name,initialGameTicks=ticks,processCookie=cookie,frames=d['frames'],endScoreUnits=d['actions'][-1]['state'][9],**difference))
 assert set(crossings[0]['all32DifferenceCounts'])=={'21','22'}and crossings[0]['firstAdditionalDifferenceBeyondScriptRng']is None
 assert crossings[1]['firstAdditionalDifferenceBeyondScriptRng']is not None
 return dict(verifiedFiniteEnvironmentAudit=True,coreCommit='57a544191704e0ce64cd46de85fe648a3e152097',sourceReplaySha256=source_sha,warmOriginalCallbacks=19496,warmCurrentStrictAll32CameraHudVmCombatPassed=True,warmVm303Rows=52,warmCombatCheckpoints=212,warmOrderedPublications=1770,originalWarmTerminalStage=2,originalWarmTerminalBattleFrame=10142,originalWarmTerminalScoreUnits=3270751,sourceSixStageHeadersDoNotProveSixStagePlayback=True,oldFullScenarioFailurePreserved=True,oldOrdinaryEnvironmentEndScoreUnits=3285179,ordinaryDeclaredOriginalEnvironmentFrames=20053,ordinaryDeclaredOriginalEnvironmentAssertions=18,ordinaryNaturalEndStage=2,ordinaryNaturalEndBattleFrame=10142,ordinaryNaturalEndScoreUnits=3270751,ordinaryStableTerminalFrames=60,ordinaryVersusWarmDiagnostic=ordinary_difference,crossedEnvironments=crossings,cookieEffectSeparatedFromInitialClockInThisCppWindow=True,readOnlyCommonPrefixControlPassed=True,verifiedCoreObjectsReused=141,verifiedDeviceObjectsReused=4,adapterCompiledObjects=1,originalGameRngHealthInputOrCookieWritten=False,allSelectedOrdinary32Equal=False,ordinaryOriginalGuiAccepted=False,originalWholePixelsOrPcmCompared=False,allSixStagesAccepted=False,modeInventoryChanged=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--home',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check',action='store_true');args=parser.parse_args();home=args.home.resolve();out=args.output.resolve();assert home.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT/'artifacts/th14')
 proof=verify(home)
 if args.check:assert json.loads(out.read_bytes())==proof
 else:out.write_text(json.dumps(proof,indent=2)+'\n')
 print(json.dumps({k:proof[k]for k in ['verifiedFiniteEnvironmentAudit','warmOriginalCallbacks','ordinaryDeclaredOriginalEnvironmentFrames','ordinaryNaturalEndScoreUnits','cookieEffectSeparatedFromInitialClockInThisCppWindow','ordinaryOriginalGuiAccepted','completeGame']}))
if __name__=='__main__':main()
