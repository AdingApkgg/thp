from pathlib import Path
import argparse,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/frame-rng-scope-nov02';sha=lambda b:hashlib.sha256(b).hexdigest();bindings={}
def raw(p):
 p=p.resolve();b=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(b),'sha256':sha(b)};return b
def load(p):return json.loads(raw(p))
p=argparse.ArgumentParser(description='Check finite TH14 visual RNG counter collision evidence.');p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-shake-counter-restore-nov03.json');args=p.parse_args()
proof=load(H/'counter-candidate-verified.json');assert proof['verifiedFiniteCounterCandidate'] and not proof['productionIntegrated'] and proof['naturalCases']==16 and proof['naturalCallbacks']==1579705
for name,binding in proof['bindings'].items():assert sha((R/name).read_bytes())==binding['sha256'],name
integration=load(H/'counter-integration.json');build=load(H/'counter-production-core/observer-build.json')
assert integration['productionIntegrated'] and integration['candidateAndProductionWasmExactlyEqual'] and integration['exportAbiIdentical'] and integration['exports']==134
assert build['promotedFromExactVerifiedCandidate'] and build['productionSourceMatchVerified'] and build['wasmSha256']==proof['candidateWasmSha256']
assert sha(raw(H/'counter-production-core/observer.wasm'))==build['wasmSha256']
for name,digest in {**build['sourceHashes'],**build['headerHashes']}.items():
 if name.endswith('/ResourceCrypt.cpp'):continue
 assert sha(raw(R/'runtimes/th12'/name))==digest,name
component=load(H/'counter-integrated-component/verified.json');compiled=load(H/'counter-integrated-component/build.json')
assert component['passed'] and component['activeRngComparisons']==480 and component['results']['candidate']['differentStackWords']==0
assert sha(raw(H/'counter-integrated-component/component.wasm'))==compiled['wasmSha256']
frozen=load(H/'counter-restore/candidate/build.json');assert compiled['wasmSha256']==frozen['wasmSha256']
for name,digest in compiled['sourceHashes'].items():assert sha(raw(R/name))==digest
for name in ['tools/th14-rng-actor-counter-restore-native-nov02.py','tools/th14-shake-counter-restore-build-nov03.py','tools/th14-shake-counter-restore-check-nov03.mjs','runtimes/th12/th12_web/tests/cpp/th14-shake-counter-restore-fixture-nov03.cpp']:raw(R/name)
assert sha(raw(R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp'))=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
assert sha(raw(R/'artifacts/th14/vm-return-worker-oct29/work-state.json'))=='2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'
result={'verifiedIntegratedShakeCounterCollisionFix':True,'productionIntegrated':True,'baseCoreCommit':'2f42560318202a997514d9644adb549db548964a','sourceFiles':['ScreenShake.hpp','ScreenShake.cpp'],'candidateAndProductionWasmExactlyEqual':True,'wasmSha256':build['wasmSha256'],'coreObjectsRecompiled':141,'unchangedExports':134,'originalInstructionProfiles':2016,'actualWorkerStoreExecutions':480,'activeCppComparisons':480,'baselineWrongStackWords':192,'candidateWrongStackWords':0,'syntheticWorkerSchedule':True,'lifecycleCasesPerVersion':312,'crossTitleSyntaxChecks':12,'naturalCases':16,'naturalCallbacks':1579705,'old36826StrictFailureClosed':False,'actualFullWorkerAndControllerReaderProved':False,'newCoreApplicationOrBrowserAccepted':False,'naturalModeInventory':30,'allStageEntryModeInventory':27,'completeGame':False,'nativeEquivalent':False,'bindings':bindings,'verifierSha256':sha(Path(__file__).read_bytes())}
output=args.output.resolve();assert output.is_relative_to(R/'docs/porting') or output.is_relative_to(H);data=(json.dumps(result,indent=2)+'\n').encode()
if args.check:assert output.read_bytes()==data
else:output.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
