"""Private narrow helper candidate; preserve Native/before capture receipts."""
import hashlib,json,os,shutil,subprocess,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/th14/deferred-capture-pixels-oct14';OUT=ROOT/'artifacts/th14/deferred-capture-success-dirty-oct14';SHA=lambda b:hashlib.sha256(b).hexdigest()
assert not (OUT/'webgl-build.json').exists(),'Completed build immutable';OUT.mkdir(parents=True,exist_ok=True);PRIVATE=OUT/'private';shutil.copytree(BASE/'private',PRIVATE,dirs_exist_ok=True)
baseline=json.loads((BASE/'webgl-build.json').read_bytes());path=PRIVATE/'cpp/sdl/ApplicationCaptureTh14.hpp';before=path.read_bytes();assert SHA(before)==baseline['captureConsumerSha256']
needle=b'  graphics.backend.resample(Graphics::screen,from,target,to,nullptr,0,0);\n  graphics.changed(target);renderer.invalidate();'
replacement=b'  if(graphics.backend.resample(Graphics::screen,from,target,to,nullptr,0,0))graphics.changed(target);\n  // Material-cache invalidation is separate from the successful target write.\n  renderer.invalidate();'
newline=b'\r\n' if b'\r\n' in before else b'\n';needle=needle.replace(b'\n',newline);replacement=replacement.replace(b'\n',newline)
assert before.count(needle)==1;after=before.replace(needle,replacement);path.write_bytes(after)
(OUT/'ApplicationCaptureTh14.before.hpp').write_bytes(before);(OUT/'ApplicationCaptureTh14.candidate.hpp').write_bytes(after)
patch=''.join(difflib.unified_diff(before.decode().replace('\r\n','\n').splitlines(True),after.decode().replace('\r\n','\n').splitlines(True),fromfile='a/runtimes/th12/th12_web/cpp/sdl/ApplicationCaptureTh14.hpp',tofile='b/runtimes/th12/th12_web/cpp/sdl/ApplicationCaptureTh14.hpp'))
(OUT/'success-dirty.patch').write_bytes(patch.encode())
bindings=[]
for row in baseline['bindings']:
    b=(PRIVATE/Path(row['snapshot']).relative_to('private')).read_bytes();assert SHA(b)==row['sha256'] or row['snapshot']=='private/cpp/sdl/ApplicationCaptureTh14.hpp';bindings.append(dict(row,sha256=SHA(b),beforeSha256=row['sha256']))
assert (PRIVATE/'fixture.cpp').read_bytes()==(BASE/'private/fixture.cpp').read_bytes()
sdk=ROOT/'runtimes/th12/tools/emsdk';python='C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe';flags=[f if not f.startswith('-I') else '-I'+str(PRIVATE) for f in baseline['flags']];env=dict(os.environ,EM_CONFIG=str(sdk/'.emscripten'),EMSDK=str(sdk),TEMP=str(OUT),TMP=str(OUT),TMPDIR=str(OUT))
p=subprocess.run([python,str(sdk/'upstream/emscripten/emcc.py'),*flags,str(PRIVATE/'fixture.cpp'),str(PRIVATE/'portable/sdl/Renderer.cpp'),'-o',str(OUT/'capture.mjs')],cwd=ROOT,env=env,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);(OUT/'webgl-build.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr.decode(errors='replace')
state=['runtimes/th12/th12_web/cpp/game/AnmRenderer.cpp','runtimes/th12/th12_web/cpp/game/AnmRenderer.hpp','runtimes/th12/th12_web/cpp/sdl/GraphicsDevice.hpp']
for name in state:
    p=ROOT/name;q=OUT/'state-source'/Path(name).name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
report=dict(privateBuilt=True,productionChanged=False,completeGame=False,nativeEquivalent=False,bindings=bindings,fixtureSha256=baseline['fixtureSha256'],wasmSha256=SHA((OUT/'capture.wasm').read_bytes()),loaderSha256=SHA((OUT/'capture.mjs').read_bytes()),flags=flags,toolSha256=SHA(Path(__file__).read_bytes()),captureConsumerSha256=SHA(after),beforeConsumerSha256=SHA(before),baselineBuildSha256=SHA((BASE/'webgl-build.json').read_bytes()),baselinePixelReportSha256=SHA((ROOT/'docs/porting/th14-deferred-capture-pixels-observed-oct14.json').read_bytes()),patchSha256=SHA(patch.encode()),stateBindings=[{'path':name,'snapshot':'state-source/'+Path(name).name,'sha256':SHA((ROOT/name).read_bytes())} for name in state],scope='Private single helper candidate: successful bool backend copy alone increments target revision, request still retires for all results. ANM material-cache invalidation remains unconditional after a non-null-target backend attempt; it is a distinct port-state/cache operation, not NativeAddDirtyRect. All Renderer/ResampleShader and fixture sources/flags equal baseline. Eight actualWebGL full buffers and same3 explicit null/controlledfalse controls will be compared independently; no production edit.')
(OUT/'webgl-build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'privateBuilt':True,'wasmSha256':report['wasmSha256'],'patchSha256':report['patchSha256']}))
