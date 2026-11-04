"""Recompile the Application adapters against the new renderer; reuse 141 core units."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
R=Path(__file__).resolve().parents[1];G=R/'artifacts/th14/gles-clip-portable-nov04';P=R/'artifacts/th14/config-startup-fallback-nov04/build';D=G/'application-build-v2-nov05';assert not D.exists();D.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();parent_raw=(P/'build.json').read_bytes();parent=json.loads(parent_raw)
assert sha((P/'application.wasm').read_bytes())==parent['wasmSha256'] and parent['wasmSha256']=='33430a93a78845cff708088106f16018b8e23515f804fb5e33e731cc36174f7d'
for name,row in parent['sourceBindings'].items():assert sha((R/name).read_bytes())==row['sha256'],name
for row in parent['coreObjects']+parent['applicationObjectBindings']:assert sha(Path(row['path']).read_bytes())==row['sha256']
old=Path(parent['frozenApplicationSourceRoot']);frozen=D/'frozen-application';assert old.is_relative_to(R/'artifacts/th14') and sum(p.stat().st_size for p in old.rglob('*')if p.is_file())<16*1024**2
shutil.copytree(old,frozen);changed=['Renderer.cpp','Renderer.hpp','Shaders.hpp','Th14RenderMath.hpp'];production={}
for name in changed:
    source=R/'runtimes/th12/portable/sdl'/name;raw=source.read_bytes();(frozen/'portable/sdl'/name).write_bytes(raw);production[source.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw))
(D/'fixture.cpp').write_bytes((P/'fixture.cpp').read_bytes());flags=[v.replace(str(old),str(frozen))for v in parent['flags']];compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(compiler.read_bytes())==parent['compilerSha256'];env={**os.environ,'TMP':str(D),'TEMP':str(D),'TMPDIR':str(D)}
units=[D/'fixture.cpp',*[frozen/'th12_web/cpp/sdl'/name for name in ['AudioDevice.cpp','FontDevice.cpp','GraphicsDevice.cpp']],frozen/'portable/sdl/Renderer.cpp'];objects=[]
for source in units:
    obj=D/(source.stem+'.o');command=[str(compiler),*flags,'-c',str(source),'-o',str(obj)];(D/(source.stem+'-argv.json')).write_text(json.dumps(command,indent=2)+'\n')
    p=subprocess.run(command,cwd=R,env=env,capture_output=True,timeout=180);(D/(source.stem+'.compile.log')).write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr.decode(errors='replace');objects.append(obj);print('compiled '+source.name,flush=True)
command=[str(compiler),*flags,*parent['linkFlags'],*[str(o)for o in objects],*[row['path']for row in parent['coreObjects']],'-o',str(D/'application.wasm')];(D/'link-argv.json').write_text(json.dumps(command,indent=2)+'\n')
p=subprocess.run(command,cwd=R,env=env,capture_output=True,timeout=180);(D/'link.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr.decode(errors='replace')
bindings={}
for name,row in parent['sourceBindings'].items():
    path=R/name
    if path.is_relative_to(old):path=frozen/path.relative_to(old)
    elif path==P/'fixture.cpp':path=D/'fixture.cpp'
    raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw))
bindings.update(production);(D/'gl-signatures.json').write_bytes((G/'production-build-nov05/gl-signatures.json').read_bytes())
build=dict(parent);build.update(flags=flags,toolSha256=sha(Path(__file__).read_bytes()),parentBuild=P.relative_to(R).as_posix()+'/build.json',parentBuildSha256=sha(parent_raw),sourceBindings=bindings,frozenApplicationSourceRoot=str(frozen),
    glSignaturesSha256=sha((D/'gl-signatures.json').read_bytes()),wasmSha256=sha((D/'application.wasm').read_bytes()),newObjects={p.name:sha(p.read_bytes())for p in objects},applicationObjectBindings=[dict(path=str(p),sha256=sha(p.read_bytes()))for p in objects],
    applicationObjectsRecompiled=5,applicationObjectsReused=0,coreObjectsRecompiled=0,coreObjectsReused=141,rendererProductionSourceFiles=production,scope='Current production Application adapters and renderer, five freshly compiled units. All 141 unchanged gameplay core objects reused with hashes from the accepted Application parent. Quiet standalone platform boundary, no original whole-game or browser acceptance.')
(D/'build.json').write_text(json.dumps(build,indent=2)+'\n');print(json.dumps(dict(compiled=True,wasmSha256=build['wasmSha256'],recompiledApplicationUnits=5,reusedCoreUnits=141)))
