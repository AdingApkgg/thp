"""Check finite cancellation component bindings; publish counts and hashes only."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/stage-wait-cancel-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest()

def verify():
 bindings={}
 def raw(path):
  data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
 def read(path):return json.loads(raw(path))
 source=R/'runtimes/th12/th12_web/cpp/game/GameSessionResources.cpp'
 app=R/'runtimes/th12/th12_web/cpp/sdl/Application.cpp'
 records={}
 for name in ['component','root-fixed']:
  home=H/name;build=read(home/'build.json');run=read(home/'verified.json')
  assert run['passed'] and SHA(raw(home/'build.json'))==run['buildSha256']
  for kind in ['before','after']:
   assert SHA(raw(home/kind/'component.wasm'))==build['builds'][kind]['wasmSha256']
   assert SHA(raw(home/kind/'fixture.cpp'))==build['builds'][kind]['fixtureSha256']
  assert run['results']['before']['failures']==7 and run['results']['before']['hostCancellations']==0
  assert run['results']['before']['waitStillActive'] and run['results']['before']['pendingUploadReferences']==1
  assert run['results']['after']['failures']==0 and run['results']['after']['checks']==35
  assert run['results']['after']['hostCancellations']==run['results']['after']['releases']==3
  assert not run['results']['after']['waitStillActive'] and run['results']['after']['pendingUploadReferences']==0
  assert not run['ordinaryApplicationExecuted'] and not run['completeGame']
  records[name]=dict(build=build,run=run)
 fixed=records['root-fixed']['build'];initial=records['component']['build']
 assert fixed['rootAlreadyContainsFix'] and not initial['rootAlreadyContainsFix']
 assert fixed['ownerSourceSha256']==SHA(raw(source))
 assert fixed['applicationSourceSha256']==initial['applicationSourceSha256']==SHA(raw(app))
 assert fixed['headerHashes']==initial['headerHashes']
 for name,digest in fixed['headerHashes'].items():assert SHA((R/name).read_bytes())==digest
 for name in ['th14-stage-wait-cancel-check-nov05.py','th14-stage-wait-cancel-run-nov05.mjs']:
  data=raw(R/'tools'/name)
  if name.endswith('.py'):assert SHA(data)==fixed['toolSha256']
  else:assert SHA(data)==records['root-fixed']['run']['toolSha256']
 failed=read(H/'checker-initial/failure.json');raw(H/'checker-initial/checker.mjs')
 assert failed['actualAfterChecks']==35 and failed['incorrectExpectedAfterChecks']==38
 return dict(schema='th14/stage-wait-cancel-public-evidence/1',
  productionSourceFix=True,productionHostWaitNowCancelledAtZeroRequestedPhaseMask=True,
  actualOwnerBeginAndCancellationMethodsCompiled=True,actualSdlAdapterCancelBodyCompiled=True,
  realWaitGenerationAndUploadQueueHelpers=True,
  declaredRecordingDependencies=['decode callback','graphics release callback'],
  before=dict(failedChecks=7,totalChecks=26,hostCancellations=0,waitStillActive=True,pendingUploadHelperReferences=1),
  after=dict(failedChecks=0,totalChecks=35,hostCancellations=3,waitStillActive=False,pendingUploadHelperReferences=0),
  staleBeforeDispatchRejected=True,staleAfterDispatchRejected=True,newGenerationProtected=True,repeatedCancelIsNoOp=True,
  uploadControlScope='Unit directly enqueues a helper reference before cancellation; not an observed ordinary GPU request.',
  firstCheckerAssertionCountFailureRetained=True,correctedExtraRecordingChecks=9,
  ownerSourceSha256=fixed['ownerSourceSha256'],applicationSourceSha256=fixed['applicationSourceSha256'],
  conservativeHeaderInventoryCount=len(fixed['headerHashes']),headerInventorySha256=SHA(json.dumps(fixed['headerHashes'],sort_keys=True).encode()),
  ordinaryApplicationExecuted=False,previewWasmReplaced=False,fullGameplayRegressionRun=False,
  independentReadinessIntegrated=False,fourthReplayGlobalsDeliveryTested=False,
  ordinaryApplicationLifetimeFullyAccepted=False,modePassCountsChanged=False,
  gameAssetsCopied=False,originalProcessBrowserOrAudioStarted=False,completeGame=False,nativeEquivalent=False,
  evidenceBindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
 result=verify();target=R/'docs/porting/th14-stage-wait-cancel-nov05.json'
 if a.check:assert json.loads(target.read_bytes())==result
 else:target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(dict(passed=True,checks=35,oldFailuresRetained=7,ordinaryApplicationExecuted=False,completeGame=False)))
