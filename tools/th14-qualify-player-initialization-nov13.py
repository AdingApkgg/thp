"""Bind the Player initialization fix, rejected baselines and actual entry scope."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/player-initialization-oracle-nov13';bindings={}
def raw(path):
 p=path if path.is_absolute()else R/path;b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return b
def load(p):return json.loads(raw(p))
sha=lambda p:hashlib.sha256(raw(p)).hexdigest()
def main():
 edits=load(H/'candidate-edits.json');changed={r['path']:r for r in edits['files']}
 assert set(changed)=={'runtimes/th12/th12_web/cpp/game/Timer.hpp','runtimes/th12/th12_web/cpp/game/PlayerFrame.cpp'}
 for name,row in changed.items():assert sha(R/name)==row['afterSha256']and sha(H/'baseline-source'/Path(name).name)==row['beforeSha256']
 native=load(H/'native.json');assert native['actualFullConstructor']and native['actualFullInitialize']and len(native['rows'])==6
 for n in native['rows']:
  assert n['constructorZeroedAllBytes']and not n['constructorRngWrites']and not n['rngWrites']
  assert [(c['kind'],c.get('priority'))for c in n['calls']]==[('cached-ANM9',None),('main',18),('draw',28)]
  assert all(c['flags']&2==0 for c in n['calls'][1:])
 baseline=load(H/'mapped-result.json');candidate=load(H/'candidate-result.json')
 assert not baseline['passed']and candidate['passed']and candidate['words']==3024
 assert all([d['field']for d in r['differences']]==['transition.previous','transition.ratePresent','transition.flags']for r in baseline['rows'])
 assert all(not r['differences']for r in candidate['rows'])
 rejected=load(H/'result.json');assert not rejected['passed']
 assert sum(len(r['differences'])for r in rejected['rows'])==501
 timer=load(H/'timer-oracle/result.json');assert timer['passed']and timer['nativeCases']==240
 assert timer['results']['baseline']['failedCases']==64 and timer['results']['baseline']['liveRateFailedCases']==0
 assert timer['results']['candidate']['failedCases']==0 and timer['results']['candidate']['cases']==960
 controls=load(H/'other-title-controls-v2/result.json');assert controls['passed']and len(controls['pairs'])==6
 for p,d in controls['objectBindings'].items():assert sha(R/p)==d
 core=load(H/'candidate-providers/build.json');assert core['normalEngineAccessControl']and core['gameUnitsCompiled']==141 and core['gameObjectsReused']==0
 for p,d in core['sourceBindings'].items():assert sha(R/p)==sha(R/core['sourceSnapshotRoot']/p)==d
 for row in core['currentProviders']:assert sha(R/row['object'])==row['objectSha256']
 browser=load(H/'browser/build.json');assert browser['units']==146
 assert browser['sourceBindings']==core['sourceBindings']
 assert sha(H/'browser/th14-sdl.wasm')==browser['sha256']
 for p,d in browser['objects'].items():assert sha(H/'browser'/p)==d
 for name in ['loading-flags4','loading-legacy']:
  r=load(H/name/'result.json');assert r['passed']and not r['physicalSchedulingAccepted']and r['graphicsOrAudioDevicesOpened']==0
 run=H/'application/start-mode3';report=load(run/'report.json');plan=load(run/'plan.json');platform=load(run/'platform.json');player=load(run/'first-player.json');app=load(H/'application/component/build.json')
 assert report['terminal']and report['closed']and report['quiet']and report['errors']==[]and report['exception']is None
 assert report['stage']=='first-player'and report['frames']==player['frames']==540
 assert app['freshNormalGameUnits']==141 and app['freshNormalHostUnits']==4 and app['normalProviders']==145
 assert sha(H/'application/component/candidate.wasm')==app['wasmSha256']==report['wasmSha256']
 assert sha(run/'run-host.mjs')==report['driverSha256']
 assert sha(run/'first-player.bgra')==player['pixelSha256']and player['pixelBytes']==640*480*4
 assert player['ordinaryGameStart']and player['playerCallbacks']==1 and not player['replay']and not player['demo']
 assert all(w['returned']and w['error']is None for w in report['workers'])and all(w['closed']and w['exitCode']==0 for w in report['physicalWorkers'])
 assert not report['processClockResolution']['active']
 assert all(platform[k]==0 for k in ['pendingTimers','openFiles','window','context','stream'])
 assert all(v==0 for v in platform['liveObjects'].values())and all(v==0 for v in platform['actualNativeGles']['liveObjects'].values())
 assert not platform['productionDelivery']['workers']
 assert sha(R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp')=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
 for p in [R/'tools/th14-player-initialization-oracle-nov13.py',R/'tools/th14-run-player-initialization-mapped-nov13.mjs',R/'tools/th14-run-player-initialization-candidate-nov13.mjs',R/'tools/th14-null-rate-timer-oracle-nov13.py',R/'tools/th14-run-null-rate-timer-oracle-nov13.mjs',R/'tools/th14-null-rate-other-title-controls-v2-nov13.py',Path(__file__)]:raw(p)
 out=dict(schema='thp/th14-player-initialization/1',terminal=True,gameSourceBase='84b8741af5b7ca617cc4046fe697d3cbfebbf4ad',
          changedGameFiles=edits['files'],nativeWholePlayerConstructorAndInitializeSelections=6,
          nativeConstructorClearsAllBytes=True,nativeInitializeRngWrites=0,
          translatedShtHeaderSchema=True,rawHeaderLayoutMiscomparisonRejected=True,retainedInitialMiscomparisonWords=501,
          baselineMappedDifferences=18,candidateMappedWords=3024,candidateMappedDifferences=0,
          nullableTimerTickNativeCases=240,nullableTimerTickComparisons=960,nullableTimerTickWords=4800,
          oldNullableTickFailures=64,nonnullTickFailures=0,timerAdvanceChangedOrAccepted=False,
          normalSdkGameUnitsFresh=141,normalBrowserUnitsFresh=146,otherTitleObjectPairsEqual=6,
          loadingRegressionFrames=2093,loadingRegressionWords=2928024,loadingRegressionDifferences=0,
          ordinaryReimuBNormalFirstPlayer=dict(frames=540,callbacks=1,quiet=True,allResourcesRetired=True,
              actualApplicationWasmSha256=app['wasmSha256'],rng=player['scriptAndGameplayRngAfterFrame'],
              originalSameRunNativePairAccepted=False,audioInput='prior FLAC',newVorbisPlaybackAccepted=False),
          browserWasmSha256=browser['sha256'],browserLoaderSha256=sha(H/'browser/th14-sdl.mjs'),
          actualProductionDeliveryWorkersExercised=0,loading24CallDifferenceClosed=False,
          fullReplayRuns=0,wholeFrameOrFinalPcmAccepted=False,browserUiAccepted=False,completeGame=False,bindings=bindings)
 p=H/'qualified.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({k:v for k,v in out.items()if k not in ['bindings','changedGameFiles']}))
if __name__=='__main__':main()
