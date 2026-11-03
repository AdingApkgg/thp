"""Bind WebGPU startup error tests, a rebuilt loader and actual browser observations."""
from pathlib import Path
import argparse,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest()
base=R/'artifacts/th14/shake-counter-browser-nov03';home=R/'artifacts/th14/webgpu-error-bridge-build-reuse-nov03';build_raw=(home/'build.json').read_bytes();build=json.loads(build_raw);old=json.loads((base/'build.json').read_bytes())
assert build['compiled'] and build['compiledUnits']==0 and build['reusedObjectCount']==146 and build['reusedArchiveWorker'] and build['objectHashes']==old['objectHashes']
assert build['wasmSha256']==old['wasmSha256']==sha((home/'th14-sdl.wasm').read_bytes()) and build['loaderSha256']==sha((home/'th14-sdl.mjs').read_bytes()) and build['loaderSha256']!=old['loaderSha256']
for name in ['portable/sdl/Th14WebGpuLibrary.js','portable/sdl/Th14WebGpuRuntime.mjs']:
 assert sha((R/'runtimes/th12'/name).read_bytes())==build['sourceBindings'][name]['sha256']==sha((home/'source'/name).read_bytes())
for name,row in build['sourceBindings'].items():
 if Path(name).suffix in ('.cpp','.hpp','.h','.inc'):assert row['sha256']==old['sourceBindings'][name]['sha256']
test=subprocess.run(['C:/nvm4w/nodejs/node.exe',str(R/'tools/th14-webgpu-open-error-check-nov03.mjs')],cwd=R,capture_output=True,check=True,timeout=30);component=json.loads(test.stdout);assert all(component[x] for x in ['concurrentOpenCreatesOnce','queuedWorkRejected','failedBridgeReturnsZero','failedCloseIsSafe','successfulInitializationUnaffected'])
observations=[]
for folder,fixed in [('headless-browser-game-nov03',False),('headless-browser-bridge-final-nov03',True)]:
 h=R/'artifacts/th14'/folder;raw=(h/'observation.json').read_bytes();d=json.loads(raw);text=d['dom']['bodyText'];events=d['debugLogEvents'];exceptions=[x for x in events if x['method']=='Runtime.exceptionThrown'];shot=(h/'page.png').read_bytes();assert shot.startswith(b'\x89PNG\r\n\x1a\n') and d['mutedByBrowserAndLocalAudioPolicy'] and d['freshIsolatedProfile'] and d['originalWasmVerified'] and not d['completeGame']
 assert [x['text'] for x in d['launcherMouseActions']]==['关闭','启动游戏']
 if fixed:
  assert 'WebGPU initialization failed' in text and 'first-frame-timeout' not in text and 'launch 操作超时' not in text and not exceptions
 else:
  assert 'first-frame-timeout' in text and 'launch 操作超时' in text and len(exceptions)==1 and 'No WebGPU adapter' in exceptions[0]['params']['exceptionDetails']['exception']['description']
 observations.append(dict(fixed=fixed,observationSha256=sha(raw),screenshotSha256=sha(shot),unhandledRuntimeExceptions=len(exceptions),firstFrameTimeoutVisible='first-frame-timeout' in text,launchTimeoutVisible='launch 操作超时' in text,initializationFailureVisible='WebGPU initialization failed' in text,profileBytes=d['profileBytes']))
result=dict(verifiedWebGpuStartupFailureReturn=True,component=component,browserObservations=observations,buildSha256=sha(build_raw),wasmSha256=build['wasmSha256'],loaderSha256=build['loaderSha256'],gameplayObjectsReusedWithoutChange=146,archiveWorkerReused=True,headlessGpuAdapterUnavailable=True,ordinaryChromeGameplayAccepted=False,wholeGameAccepted=False,completeGame=False,nativeEquivalent=False,toolSha256=sha(Path(__file__).read_bytes()),scope='Failure handling only: a missing WebGPU adapter returns initialization failure to the launcher instead of leaving an unhandled async rejection and later launch/first-frame timeouts. Fresh muted headless Chrome observations and component success/failure controls are bound to the relinked loader. This is not a successful gameplay, ordinary-GUI, pixel, audio or complete-game acceptance.')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-webgpu-open-error-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(R/'artifacts/th14');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
