"""Seal browser startup evidence as metadata; screenshots and Wasm stay private."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/browser-ordinary-gles-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest();bindings={}
def seal(path):
    raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
def read(name):return json.loads(seal(H/name))
build=read('async-build-retry1/build.json');transport=read('async-clean-transport.json');syntax=read('shared-application-syntax/report.json')
assert build['compiledUnits']==1 and build['reusedObjectCount']==145 and build['gameCoreObjectsReused']==141
assert build['backend']=='gles'and build['frameAndWorkerCallbacksSerialized']and not build['backgroundArchiveIntegration']
assert transport['verifiedTransport']and transport['routes']==135 and len(transport['requests'])==28
assert syntax['passed']and len(syntax['rows'])==5
failure=read('loop-audit-dom.json');start=read('async-startup-dom.json');normal=read('async-normal-stage1-dom.json');pause=read('async-pause-dom.json')
assert failure['loop']['callbacks']==2 and failure['loop']['lastReturn']==0 and failure['phase']==6
assert any('native-return n=2 result=1'in line for line in failure['nativeOutput'])
assert start['phase']==0 and normal['phase']==1 and pause['phase']==2
assert start['gameTicks']>failure['gameTicks']and normal['gameFrame']>=1204 and pause['gameFrame']==1327
for row in [start,normal,pause]:assert row['error']==''and row['asyncCallbacks']['failure']==''and not row['hidden']
for name in ['clean-startup-dom.txt','async-quit-dom.txt','clean-quit-dom.txt']:
    text=seal(H/name).decode();assert 'th14-startup-probe'not in text
for name in ['async-startup.jpg','async-normal-stage1.jpg','async-pause.jpg','async-returned-title.jpg','async-quit.jpg','clean-startup.jpg','clean-quit.jpg','clean-config-before.jpg','clean-config-changed95.jpg','clean-config-readback95.jpg']:
    seal(H/name)
for name in ['runtimes/th12/th12_web/cpp/sdl/Application.cpp','runtimes/th12/th12_web/sdl-runtime/shell.mjs',
             'runtimes/th12/portable/sdl/Th14AsyncCallbacks.hpp','runtimes/th12/portable/sdl/Th14AsyncRuntime.mjs','tools/th14-test-async-runtime-nov05.mjs']:
    seal(R/name)
test=subprocess.run(['C:/nvm4w/nodejs/node.exe',str(R/'tools/th14-test-async-runtime-nov05.mjs')],capture_output=True,check=True)
test_report=json.loads(test.stdout);assert test_report['passed']and test_report['peakConcurrentWasmCalls']==1
(H/'async-runtime-test.json').write_bytes(test.stdout);seal(H/'async-runtime-test.json')
out=dict(schema='th14/gles-async-startup-evidence/1',wasmSha256=build['wasmSha256'],backend='gles',
    compiledApplicationUnits=1,reusedObjects=145,reusedGameplayObjects=141,asyncCallbackTest=test_report,sharedSyntax=syntax['rows'],
    transport=dict(routes=135,httpChecks=28,quietByDefault=True),
    oldFailure=dict(nativeFinalReturn=1,rawRafReturn=0,callbacks=2,ticks=4,phase=6,retained=True),
    withOutputProbe=dict(title=start,normalFirstStage=normal,pause=pause,normalKeysUsed=True,normalMenuQuitReturnedToLauncher=True),
    withoutOutputProbe=dict(actualStartupObserved=True,autoDemoRendered=True,normalOptionMenuRendered=True),
    finiteConfigPersistence=dict(beforeBgmPercent=100,changedBgmPercent=95,afterNormalQuitAndFullPageReloadBgmPercent=95,
        newRuntimeCreated=True,visibleReadbackAccepted=True,allSaveFilesByteEqualityAccepted=False,offlineAccepted=False),
    previewSoundOutputZero=True,originalWholeGamePixelsOrPcmAccepted=False,ordinaryIndependentTimingAccepted=False,
    completeBrowserAcceptance=False,completeGame=False,imagesAssetsRawObservationsAndBinariesIncluded=False,
    evidencePathsAndHashes=bindings,toolSha256=SHA(Path(__file__).read_bytes()))
target=R/'docs/porting/th14-gles-async-startup-nov05.json';target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(prepared=True,path=target.relative_to(R).as_posix(),bytes=target.stat().st_size,completeGame=False)))
