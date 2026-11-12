"""Apply the observed retail @R resize/UV rule only to the isolated candidate."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-mode-entry-nov12';P=json.loads((H/'prepared.json').read_bytes());S=Path(P['sourceRoot'])
name='runtimes/th12/th12_web/cpp/sdl/GraphicsDevice.cpp';p=S/name;before=p.read_text(encoding='utf8')
old='    const auto& source=file.textures[index];Texture texture;'
new='''#if PORT_TITLE == 14
    auto& source=file.textures[index];
    if(source.kind==AnmTexture::Kind::RenderTarget){
        // Retail47d4b1..47d4dc replaces the chunk dimensions before
        //47d9e0 derives sprite UVs from the resulting surface descriptor.
        const auto& display=textures.at(screen).image;
        if(source.width!=display.width||source.height!=display.height){
            source.width=u16(display.width);source.height=u16(display.height);
            for(auto& sprite:file.sprites)if(sprite.texture==index){
                sprite.u0=float(double(sprite.x)/source.width);sprite.v0=float(double(sprite.y)/source.height);
                const float right=float(double(sprite.x)+sprite.width),bottom=float(double(sprite.y)+sprite.height);
                sprite.u1=float(double(right)/source.width);sprite.v1=float(double(bottom)/source.height);
            }
        }
    }
#else
    const auto& source=file.textures[index];
#endif
    Texture texture;'''
assert before.count(old)==1
(H/'GraphicsDevice-before-target-fix.cpp').write_bytes(p.read_bytes());p.write_text(before.replace(old,new),encoding='utf8',newline='\n')
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();P['sourceBindings'][name]=sha(p);next(x for x in P['changes'] if x['path']==name)['afterSha256']=sha(p)
(H/'prepared-before-target-fix.json').write_bytes((H/'prepared.json').read_bytes());(H/'prepared.json').write_text(json.dumps(P,indent=2)+'\n')
core=json.loads((H/'candidate/build.json').read_bytes());core['sourceBindings']=P['sourceBindings'];(H/'candidate/build.json').write_text(json.dumps(core,indent=2)+'\n')
A=H/'application/component';j=json.loads((A/'build.json').read_bytes());(A/'build-before-target-fix.json').write_bytes((A/'build.json').read_bytes())
rt=S/'runtimes/th12';flags=core['flags']+['-I'+str(rt/'th12_web/cpp/sdl'),'-I'+str(rt/'portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';obj=A/'GraphicsDevice.cpp.o';os.replace(obj,A/'GraphicsDevice-before-target-fix.cpp.o')
with (A/'GraphicsDevice-target-fix.log').open('wb') as log:subprocess.run([str(cc),*flags,'-c',str(p),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
j['objectBindings'][obj.relative_to(R).as_posix()]=sha(obj)
fixture=A/'fixture.cpp';(A/'fixture-before-target-observer.cpp').write_bytes(fixture.read_bytes());source=fixture.read_text(encoding='utf8')
source+='''
API(display_target_words) const u32* display_target_words(){
 static std::vector<u32> out;out.clear();auto& file=current->session.resources.core.text;
 for(u32 i=0;i<file.sprites.size();++i){const auto& s=file.sprites[i];const auto& t=file.textures[s.texture];
  if(t.kind!=AnmTexture::Kind::RenderTarget)continue;
  out.push_back(i);out.push_back(s.texture);
  for(float value:{s.x,s.y,float(s.x+s.width),float(s.y+s.height),float(t.height),float(t.width),s.u0,s.v0,s.u1,s.v1,s.height,s.width,1.f,1.f})out.push_back(float_bits(value));
 }
 return out.data();
}
API(display_target_count) u32 display_target_count(){u32 count=0;auto& f=current->session.resources.core.text;for(const auto& s:f.sprites)if(f.textures[s.texture].kind==AnmTexture::Kind::RenderTarget)++count;return count;}
'''
fixture.write_text(source,encoding='utf8',newline='\n')
os.replace(A/'candidate.wasm',A/'candidate-before-target-fix.wasm')
with (A/'link-target-fix.log').open('wb') as log:subprocess.run([str(cc),*flags,'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(R/n) for n in j['objectBindings']],'-o',str(A/'candidate.wasm')],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240,env={**os.environ,'TEMP':str(A),'TMP':str(A),'TMPDIR':str(A)})
bindings={(S/n).relative_to(R).as_posix():d for n,d in P['sourceBindings'].items()}
for n in ['fixture.cpp','Th14WarmAttractCase.hpp']:bindings[(A/n).relative_to(R).as_posix()]=sha(A/n)
bindings['runtimes/th12/th12_web/tests/cpp/th14-native-title-live-observer.hpp']=sha(R/'runtimes/th12/th12_web/tests/cpp/th14-native-title-live-observer.hpp')
j.update(sourceBindings=bindings,sourceBindingsByMode={'candidate':bindings},fixtureSha256=sha(fixture),wasmSha256=sha(A/'candidate.wasm'),observedNativeRenderTargetResizeAndUvApplied=True)
(A/'build.json').write_text(json.dumps(j,indent=2)+'\n')
driver=R/'tools/th14-run-display-mode-title-quit-nov12.mjs';old=driver.read_text(encoding='utf8');(H/'driver-before-target-fix.mjs').write_text(old,encoding='utf8')
old=old.replace('`run-mode${mode}`','`run-v2-mode${mode}`')
old=old.replace(' const pixels=platform.readBGRA();', '''
 const targetCount=c.display_target_count();assert.equal(targetCount,10);
 const targetWords=Array.from(new Uint32Array(memory.buffer,c.display_target_words(),targetCount*16));
 const targetNative=load(resolve(root,'artifacts/th14/display-mode-entry-nov12/targets-native-v2/native.json')).rows.find(r=>r.name==='text.anm'&&r.renderWidth===width);
 const targetRows=targetNative.sprites.filter(s=>s.texture>=2);
 assert.equal(targetRows.length,targetCount);
 for(let i=0;i<targetCount;i++)assert.deepEqual(targetWords.slice(i*16,i*16+16),[targetRows[i].index,targetRows[i].texture,...targetRows[i].words.slice(3,17)]);
 put('targets.json',{targetCount,words:targetWords,comparedNativeWords:targetCount*14,rawSpriteIdentityPreserved:true});
 const pixels=platform.readBGRA();''')
tmp=driver.with_suffix('.tmp');tmp.write_text(old,encoding='utf8',newline='\n');os.replace(tmp,driver)
print(json.dumps(dict(normalProviders=145,hostUnitsRecompiled=1,wasmSha256=j['wasmSha256'],canonicalEngineChanged=False)))
