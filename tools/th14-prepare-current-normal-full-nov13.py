"""One current-source full Normal run, reusing the terminal retail reference."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/current-normal-full-nov13';assert not H.exists();H.mkdir();O=H/'component';O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
providers=load(R/'artifacts/th14/alpha-range-current-nov13/current-provider-bindings.json')
objects={**providers['objectBindings'],**providers['hostObjectBindings']};assert len(objects)==145
for n,h in {**providers['sourceBindings'],**objects}.items():assert sha(R/n)==h,n
parent=R/'artifacts/th14/promoted-normal-campaign-nov08/full-application'
for n in ['fixture.cpp','Th14WarmAttractCase.hpp']:(O/n).write_bytes((parent/n).read_bytes())
fixture=O/'fixture.cpp'
fixture.write_text(fixture.read_text()+'\nAPI(async_deliver_owned) void async_deliver_owned(u32 callback,u32 data){th14_async_invoke(callback,data);}\n',encoding='utf8',newline='\n')
meta=load(R/'artifacts/th14/option-refresh-oracle-nov13/candidate-providers/build.json')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==meta['compilerSha256']
flags=['-I'+str(R/'runtimes/th12/th12_web/cpp/game')if x.startswith('-I')else x for x in meta['flags']]
flags+=['-I'+str(R/'runtimes/th12/th12_web/cpp/sdl'),'-I'+str(R/'runtimes/th12/portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
cmd=[str(cc),*flags,'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--export-table','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(O/'fixture.cpp'),*[str(R/n)for n in objects],'-o',str(O/'candidate.wasm')]
(O/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with(O/'compile.log').open('wb')as f:q=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
assert q.returncode==0,(O/'compile.log').read_text(errors='replace')[-3000:]
bindings=dict(providers['sourceBindings'])
for p in [O/'fixture.cpp',O/'Th14WarmAttractCase.hpp',Path(__file__)]:bindings[p.relative_to(R).as_posix()]=sha(p)
j=dict(compiled=True,actualColdApplicationInitializeTickAndDraw=True,noDeclaredPerFileReadinessSchedule=True,outputs={'candidate':{'wasmSha256':sha(O/'candidate.wasm')}},fixtureSha256=sha(O/'fixture.cpp'),sourceBindingsByMode={'candidate':bindings},objectBindings=objects,normalProductionProviders=145,fixtureOnlyRelaxedAccess=True,completeGame=False)
(O/'build.json').write_text(json.dumps(j,indent=2)+'\n')
driver=(R/'tools/th14-run-late-ascii-normal-nov08.mjs').read_text()
for a,b in {
 "artifacts/th14/startup-late-ascii-read-nov08/normal-regression":"artifacts/th14/current-normal-full-nov13",
 "artifacts/th14/startup-late-ascii-read-nov08/cpu-application":"artifacts/th14/current-normal-full-nov13/component",
 "./th14-full-application-recording-platform-texture-units-v2-nov07.mjs":"./th14-full-application-recording-platform-uniform2-nov13.mjs",
 "tools/th14-full-application-recording-platform-texture-units-v2-nov07.mjs":"tools/th14-full-application-recording-platform-uniform2-nov13.mjs",
 }.items():assert a in driver;driver=driver.replace(a,b)
# Keep mandatory raw113-word + ordinal rows. Avoid redundant JSON per-frame
# state/timing growth; the existing binary frame-dispatch trace is retained.
a='frameTimes.push([frames,now-began,after-now,delta*1000]);collect();';assert driver.count(a)==1;driver=driver.replace(a,'collect();')
a='if(!lastState||current.some((v,i)=>v!==lastState[i]))states.push';assert driver.count(a)==1;driver=driver.replace(a,'if(!lastState||[4,5,6,7,8,9,10,12,13,14].some(i=>current[i]!==lastState[i]))states.push')
a="const runtime=resolve(root,'artifacts/th14/stable-stage-close-nov07/runtime-ready');";assert driver.count(a)==1
driver=driver.replace(a,a+"\nconst music=load(resolve(root,'artifacts/th14/published-vorbis-cache-nov13/prepared.json'));assert(music.passed&&music.tracks===18);const musicDirectory=resolve(root,music.musicDirectory);for(const [n,h]of Object.entries(music.sha256))assert.equal(sha(read(resolve(musicDirectory,n))),h,n);")
driver=driver.replace("'/music':resolve(runtime,'music')","'/music':musicDirectory")
driver=driver.replace('await Promise.all(pools.map(p=>p.shutdown()));clock.close();','await Promise.all(pools.map(p=>p.shutdown()));await platform.closeServices();clock.close();')
driver=driver.replace('productionCodeChanged:false','productionCodeChanged:false,sourceIncludesUnpublishedSceneFilterAndAlphaRange:true,publishedVorbis18HashesVerified:true,frameTimesJsonOmittedBinaryDispatchRetained:true')
assert driver.count('new WebAssembly.Memory({initial:1024')==1
p=R/'tools/th14-run-current-normal-full-nov13.mjs';assert not p.exists();p.write_text(driver,encoding='utf8',newline='\n')
native=R/'artifacts/th14/player-entry-end-menu-nov06/campaign'
proof=load(native/'verified.json');assert proof['callbacks']==122005 and proof['nativeStableForcedReplayEndVerified']
plan=dict(onePredeclaredRun=True,normalGameProviders=145,recompiledProviderUnits=0,referenceCallbacks=122005,maximumCallbacks=150000,maximumSeconds=2700,maximumFrames=180000,expectedStableEndStage=6,reference='artifacts/th14/player-entry-end-menu-nov06/campaign',newNativeGameStarted=False,referenceHasSixByteObserver=True,firstPlayerAttractFlagClearedInBothFixtures=True,ordinaryPlayAccepted=False,hardwareGraphics=False,actualPthreadApplication=True,originalScoreAndPlaybackDataNotFedBack=True,publishedVorbisHashesRequired=18,quiet=True,sourceFrozenForRun=True,driverSha256=sha(p),moduleSha256=sha(O/'candidate.wasm'),completeGame=False)
(H/'prepared.json').write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(plan))
