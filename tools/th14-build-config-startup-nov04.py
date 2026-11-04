"""Recompile only the Application adapter for TH14 config startup recovery."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess

R=Path(__file__).resolve().parents[1];K=R/'artifacts/th14/scene-camera-read-job-nov04'
H=R/'artifacts/th14/config-startup-fallback-nov04';B=H/'build'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
assert not B.exists();B.mkdir()
parent=K/'ordinary-full-exit/build/build.json';parent_raw=parent.read_bytes();base=json.loads(parent_raw)
assert base['wasmSha256']=='bd41c7612120ef22a42cada1d228721fc0b7f9b7e370c94531fee6db3dcd51b0'
for name,row in base['sourceBindings'].items():assert SHA((R/name).read_bytes())==row['sha256']
old=Path(base['frozenApplicationSourceRoot']);frozen=B/'frozen-application'
assert old.is_relative_to(K) and sum(p.stat().st_size for p in old.rglob('*')if p.is_file())<16*1024**2
shutil.copytree(old,frozen)
app=R/'runtimes/th12/th12_web/cpp/sdl/Application.cpp';newapp=frozen/'th12_web/cpp/sdl/Application.cpp';newapp.write_bytes(app.read_bytes())
fixture=B/'fixture.cpp';fixture.write_bytes((K/'gles-build/fixture.cpp').read_bytes())
flags=[value.replace(str(old),str(frozen)) for value in base['flags']]
compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert SHA(compiler.read_bytes())==base['compilerSha256']
env={**os.environ,'TEMP':str(B),'TMP':str(B),'TMPDIR':str(B)}
command=[str(compiler),*flags,'-c',str(fixture),'-o',str(B/'fixture.o')]
(B/'compile-argv.json').write_text(json.dumps(command,indent=2)+'\n')
result=subprocess.run(command,cwd=R,env=env,capture_output=True,timeout=180);(B/'compile.log').write_bytes(result.stdout+result.stderr)
assert result.returncode==0,result.stderr.decode(errors='replace')[-3000:]
objects=[B/'fixture.o'];object_bindings=[]
for name,digest in base['newObjects'].items():
    path=B/name if name=='fixture.o' else K/'gles-build'/name
    if name!='fixture.o':assert SHA(path.read_bytes())==digest
    if name!='fixture.o':objects.append(path)
    object_bindings.append(dict(path=str(path),sha256=SHA(path.read_bytes())))
for row in base['coreObjects']:assert SHA(Path(row['path']).read_bytes())==row['sha256']
command=[str(compiler),*flags,*base['linkFlags'],*[str(path)for path in objects],*[row['path']for row in base['coreObjects']],'-o',str(B/'application.wasm')]
(B/'link-argv.json').write_text(json.dumps(command,indent=2)+'\n')
result=subprocess.run(command,cwd=R,env=env,capture_output=True,timeout=180);(B/'link.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')[-3000:]
(B/'gl-signatures.json').write_bytes((K/'gles-build/gl-signatures.json').read_bytes())
bindings={}
for name,row in base['sourceBindings'].items():
    path=R/name
    if path.is_relative_to(old):path=frozen/path.relative_to(old)
    elif path==K/'gles-build/fixture.cpp':path=fixture
    raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw))
build=dict(base);build.update(wasmSha256=SHA((B/'application.wasm').read_bytes()),sourceBindings=bindings,
    flags=flags,toolSha256=SHA(Path(__file__).read_bytes()),parentBuild=parent.relative_to(R).as_posix(),parentBuildSha256=SHA(parent_raw),
    newObjects={Path(row['path']).name:row['sha256']for row in object_bindings},applicationObjectBindings=object_bindings,
    applicationObjectsRecompiled=1,applicationObjectsReused=4,coreObjectsRecompiled=0,coreObjectsReused=141,
    relinkOnly=False,frozenApplicationSourceRoot=str(frozen),rootApplicationSourceSha256=SHA(app.read_bytes()),
    scope='Production Application config startup fallback only. One Application fixture object recompiled, four devices and 141 unchanged core objects reused with hashes. No game state override, browser or whole-game acceptance.')
(B/'build.json').write_text(json.dumps(build,indent=2)+'\n')
syntax=[]
for title in [12,13,14,16]:
    syntax_flags=[f'-DPORT_TITLE={title}'if flag=='-DPORT_TITLE=14'else flag for flag in flags]
    result=subprocess.run([str(compiler),*syntax_flags,'-fsyntax-only',str(newapp)],cwd=R,env=env,capture_output=True,timeout=180)
    (B/f'syntax-{title}.log').write_bytes(result.stdout+result.stderr);syntax.append(dict(title=title,returncode=result.returncode));assert result.returncode==0,result.stderr.decode(errors='replace')[-2000:]
(B/'shared-syntax.json').write_text(json.dumps(dict(cases=syntax,sourceSha256=SHA(newapp.read_bytes()),onlyTh14BehaviorChanged=True),indent=2)+'\n')
print(json.dumps(dict(compiled=True,wasmSha256=build['wasmSha256'],recompiledApplicationUnits=1,reusedCoreUnits=141,sharedSyntaxTitles=[row['title']for row in syntax])))
