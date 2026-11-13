"""Rebuild the one production host provider; retain immutable prior bindings."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/alpha-range-current-nov13'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
q=load(O/'qualified.json');changed='runtimes/th12/portable/sdl/Renderer.cpp';assert sha(R/changed)==q['sourceSha256']
old=load(R/'artifacts/th14/compositor-filter-nov13/current-provider-bindings.json')
for n,h in {**old['sourceBindings'],**old['objectBindings']}.items():
 if n==changed:assert sha(O/'Renderer.before.cpp')==h
 else:assert sha(R/n)==h,n
provider=load(R/'artifacts/th14/option-refresh-oracle-nov13/candidate-providers/build.json')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==provider['compilerSha256']
flags=provider['flags']+['-D__EMSCRIPTEN__=1','-I'+str(R/'runtimes/th12/th12_web/cpp/sdl'),'-I'+str(R/'runtimes/th12/portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
assert '-fno-access-control'not in flags
obj=O/'Renderer.cpp.o';assert not obj.exists()
with(O/'normal-renderer-build.log').open('wb')as f:p=subprocess.run([str(cc),*flags,'-c',str(R/changed),'-o',str(obj)],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
assert p.returncode==0,(O/'normal-renderer-build.log').read_text(errors='replace')[-3000:]
sources=dict(old['sourceBindings']);sources[changed]=sha(R/changed)
game=dict(old['objectBindings']);hosts={}
prior=load(R/'artifacts/th14/current-vorbis-no1-startup-nov13/component-v2/build.json')
for n,h in prior['objectBindings'].items():
 if Path(n).name in ['AudioDevice.cpp.o','GraphicsDevice.cpp.o','FontDevice.cpp.o']:
  assert sha(R/n)==h,n
  hosts[n]=h
assert len(game)==141 and len(hosts)==3
hosts[obj.relative_to(R).as_posix()]=sha(obj)
j=dict(sourceBindings=sources,objectBindings=game,hostObjectBindings=hosts,
       normalRecompiledHostUnits=1,normalGameObjectsVerifiedReused=141,normalOtherHostObjectsVerifiedReused=3,
       layoutChanged=False,rootIntegrated=True,published=False,deployed=False,completeGame=False)
(O/'current-provider-bindings.json').write_text(json.dumps(j,indent=2)+'\n')
(O/'terminal-receipt.json').write_text(json.dumps(dict(gpuSession=85097,gpuPid=16108,gpuExitCode=1,reaped=True,
    alphaCompletedBeforeUnrelatedMissingClearReference=True,allMeasuredGpuAndPlatformResourcesRetired=True,
    guardSession=99079,guardExitCode=0,guardReaped=True,normalHostBuildExitCode=0),indent=2)+'\n')
print(json.dumps(dict(normalHostRecompiled=1,verifiedReused=144,layoutChanged=False,completeGame=False)))
