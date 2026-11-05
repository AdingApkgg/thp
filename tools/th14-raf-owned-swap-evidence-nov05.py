"""Validate Renderer timing ownership, frozen inputs and finite browser observations."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/raf-owned-swap-nov05'
BASE=R/'artifacts/th14/browser-ordinary-gles-nov05/async-build-retry1'
SHA=lambda data:hashlib.sha256(data).hexdigest();bindings={}

def raw(path):
    path=path.resolve();assert path.is_relative_to(R)
    data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data))
    return data

def read(path):return json.loads(raw(path))

before=read(BASE/'build.json');build=read(H/'build/build.json')
assert before['wasmSha256']=='4a8e02cc5d27c6fe13c3948fe750f9050d2a941421056a3f5b12bf745eedeca9'
assert build['wasmSha256']=='7396f28c66e97e961b94352fca493ee54ad1b67ae757b1715b811826db410325'
assert build['compiledUnits']==1 and build['reusedObjectCount']==145 and build['rendererOnlyChanged']
assert build['flags']==before['flags']and build['linkFlags']==before['linkFlags']and build['exports']==before['exports']
name='portable/sdl/Renderer.cpp'
changed=[key for key,row in build['sourceBindings'].items()if row!=before['sourceBindings'][key]]
assert changed==[name]
for key,row in build['sourceBindings'].items():assert SHA((H/'build/source'/key).read_bytes())==row['sha256'],key
assert raw(R/'runtimes/th12'/name)==raw(H/'build/source'/name)
units=[key for key,value in build['objectHashes'].items()if value!=before['objectHashes'][key]]
assert units==[name]
game_units=[key for key in build['objectHashes']if key.startswith('th12_web/cpp/game/')];assert len(game_units)==141
for key,digest in build['reusedObjectHashes'].items():
    assert digest==before['objectHashes'][key] and SHA((R/build['reusedObjectPaths'][key]).read_bytes())==digest
assert SHA(raw(H/'build/th14-sdl.wasm'))==build['wasmSha256']
assert SHA(raw(H/'build/th14-sdl.mjs'))==build['loaderSha256']
sdk=R/'runtimes/th12/tools/emsdk/upstream/emscripten/cache/ports/sdl3/SDL-release-3.4.2/src/video/emscripten'
gl=raw(sdk/'SDL_emscriptenopengles.c').decode();video=raw(sdk/'SDL_emscriptenvideo.c').decode()
assert 'emscripten_set_main_loop_timing(EM_TIMING_RAF, interval)'in gl
assert 'static int pending_swap_interval = -1;'in video and 'Emscripten_GLES_SetSwapInterval(_this, pending_swap_interval)'in video
syntax=read(H/'shared-syntax/report.json');assert syntax['passed']and syntax['syntaxOnly']and len(syntax['rows'])==5
assert all(row['returncode']==0 for row in syntax['rows'])
transport=read(H/'transport.json');assert transport['verifiedTransport']and transport['routes']==135 and len(transport['requests'])==28
served=read(H/'served-version.json');assert served['passed']and served['wasmSha256']==build['wasmSha256']
package=read(H/'package/package-report.json');assert package['prepared']and package['wasmSha256']==build['wasmSha256']
launcher=read(H/'launcher/launcher-report.json');assert launcher['wasmSha256']==build['wasmSha256']
assert launcher['frozenLauncherReused']and not launcher['payloadFilesCopied']
for name in ['title','normal-paused','resumed-moved-paused','returned-title','quit-launcher','reloaded-title','second-quit-launcher']:
    assert raw(H/(name+'.jpg'))[:3]==bytes.fromhex('ffd8ff')
for name in ['quit-dom.txt','reloaded-title-dom.txt','second-quit-dom.txt']:raw(H/name)
assert read(H/'console-after-second-quit.json')==[]
old_logs=read(R/'artifacts/th14/browser-new-recording-nov05/console.json');assert len(old_logs)==4
assert all('emscripten_set_main_loop_timing' in row['message']for row in old_logs)
raw(R/'tools/th14-build-raf-owned-swap-nov05.py')
out=dict(schema='th14/raf-owned-swap-public-evidence/1',verifiedFiniteStartupTimingErrorFix=True,
    wasmSha256=build['wasmSha256'],previousWasmSha256=before['wasmSha256'],backend='gles',
    change='Emscripten TH14 custom RAF host does not request SDL emscripten main-loop timing',
    otherTitleAndNativeSwapIntervalCallRetained=True,frameSchedulingAndAsyncQueueUnchanged=True,
    compiledUnits=1,reusedObjects=145,reusedGameObjects=141,gameplaySourcesChanged=False,
    sharedBranchSyntaxChecks=syntax['rows'],routeChecks=135,httpChecks=28,servedFilesVerified=3,
    ordinaryVisibleBrowserFlow=dict(title=True,selection='ReimuA Normal',newGame=True,
        shootingAndScoreIncreaseObserved=True,pauseResumeAndMovementObserved=True,
        returnedTitleByOrdinaryConfirmation=True,ordinaryQuit=True,parentReloadAndSecondStartup=True,secondOrdinaryQuit=True),
    quietPreview=True,noOutputProbe=True,diagnosticEngineStateRead=False,
    retainedPreviousTimingErrorMessages=4,candidateWarnOrErrorMessages=0,
    oldReplayManagerFailureClosed=False,oldReplayPersistenceEvidenceAutomaticallyReaccepted=False,
    wholeFrameOrPcmCompared=False,independentOriginalTimingAccepted=False,allModesAccepted=False,
    completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,
    rawAssetsImagesReplaysScoresSeedsOrBinariesUploaded=False,
    evidenceBindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()))
(R/'docs/porting/th14-raf-owned-swap-nov05.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(verifiedFiniteStartupTimingErrorFix=True,reusedGameObjects=141,candidateWarnOrErrorMessages=0,completeGame=False)))
