"""Link actual compositor and Application probes against normal candidate providers."""
from pathlib import Path
import hashlib, json, os, subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-mode-entry-nov12'
core=json.loads((H/'candidate/build.json').read_bytes());S=Path(core['sourceRoot'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in core['sourceBindings'].items():assert sha(S/name)==digest,name
objects={row['object']:row['objectSha256'] for row in core['objects']}
for name,digest in objects.items():assert sha(R/name)==digest,name
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256']
def link(out,fixture,providers,flags):
    with (out/'link.log').open('wb') as log:
        subprocess.run([str(cc),*flags,'-fno-access-control','-mexec-model=reactor',
            '-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined',
            '-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',
            str(fixture),*[str(R/name) for name in providers],'-o',str(out/'candidate.wasm')],cwd=R,
            stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240,
            env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)})
    bindings={(S/name).relative_to(R).as_posix():digest for name,digest in core['sourceBindings'].items()}
    bindings[fixture.relative_to(R).as_posix()]=sha(fixture)
    result=dict(sourceBindings=bindings,objectBindings=providers,fixtureSha256=sha(fixture),
                wasmSha256=sha(out/'candidate.wasm'),fixtureOnlyRelaxedAccess=True,
                sourceRoot=str(S),completeGame=False)
    (out/'build.json').write_text(json.dumps(result,indent=2)+'\n');return result
C=H/'context-component';C.mkdir(exist_ok=False)
fixture=C/'fixture.cpp';fixture.write_bytes((R/'tools/th14-display-context-component-nov12.cpp').read_bytes())
link(C,fixture,objects,core['flags'])
A=H/'application/component';A.mkdir(parents=True,exist_ok=False)
rt=S/'runtimes/th12';flags=core['flags']+['-I'+str(rt/'th12_web/cpp/sdl'),'-I'+str(rt/'portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
providers=dict(objects)
for name in ['th12_web/cpp/sdl/AudioDevice.cpp','th12_web/cpp/sdl/FontDevice.cpp','th12_web/cpp/sdl/GraphicsDevice.cpp','portable/sdl/Renderer.cpp']:
    source=rt/name;obj=A/(source.name+'.o')
    with (A/(source.name+'.log')).open('wb') as log:
        subprocess.run([str(cc),*flags,'-c',str(source),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,
            env={**os.environ,'TEMP':str(A),'TMP':str(A),'TMPDIR':str(A)})
    providers[obj.relative_to(R).as_posix()]=sha(obj)
B=R/'artifacts/th14/current-title-quit-nov12/component'
fixture=A/'fixture.cpp';source=(B/'fixture.cpp').read_text(encoding='utf8')
source+='''
API(display_state) const u32* display_state(){
 static u32 w[37];if(!current)return nullptr;
 auto& a=*current;auto& s=a.session;const auto& cfg=s.persistent_config();
 auto* screen=a.graphics.pixels(a.graphics.screen);auto* depth=a.graphics.pixels(a.graphics.depth);
 u32* p=w;*p++=cfg.bytes[0x1f];*p++=cfg.render_width();*p++=cfg.render_height();
 for(auto* image:{screen,depth}){*p++=image?image->width:0;*p++=image?image->height:0;*p++=image?image->pitch:0;}
 *p++=a.renderer.render_width;*p++=a.renderer.render_height;
 const auto& space=s.animations.render_space;
 for(float value:{space.scale,space.play_origin.x,space.play_origin.y,space.scaled_origin.x,space.scaled_origin.y})*p++=float_bits(value);
 for(const auto* camera:{&s.compositor.full_camera,&s.compositor.play_camera,&s.compositor.scaled_play_camera,&s.compositor.world_camera}){
  *p++=camera->viewport.x;*p++=camera->viewport.y;*p++=camera->viewport.width;*p++=camera->viewport.height;
 }
 for(const auto& copy:s.compositor.copies)*p++=u32(copy.script_index);
 *p++=u32(p-w)+1;return w;
}
'''
fixture.write_text(source,encoding='utf8',newline='\n');(A/'Th14WarmAttractCase.hpp').write_bytes((B/'Th14WarmAttractCase.hpp').read_bytes())
j=link(A,fixture,providers,flags)
j.update(actualColdApplicationInitializeTickAndDraw=True,ordinaryKeyboardInputExport=True,
         exitSaveUsesProductionMethodAfterFinishedOnly=True,normalProviders=145,
         sourceBindingsByMode={'candidate':j['sourceBindings']},fixturePath=fixture.relative_to(R).as_posix())
j['sourceBindings'][(A/'Th14WarmAttractCase.hpp').relative_to(R).as_posix()]=sha(A/'Th14WarmAttractCase.hpp')
j['sourceBindings']['runtimes/th12/th12_web/tests/cpp/th14-native-title-live-observer.hpp']=sha(R/'runtimes/th12/th12_web/tests/cpp/th14-native-title-live-observer.hpp')
(A/'build.json').write_text(json.dumps(j,indent=2)+'\n')
print(json.dumps(dict(contextWasmSha256=sha(C/'candidate.wasm'),applicationWasmSha256=j['wasmSha256'],normalProviders=145,canonicalEngineChanged=False)))
