"""Complete the isolated mode candidate's native reset/Begin context writes."""
from pathlib import Path
import difflib, hashlib, json, os, subprocess

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/display-mode-entry-nov12'
P = json.loads((H/'prepared.json').read_bytes())
S = Path(P['sourceRoot'])
name = 'runtimes/th12/th12_web/cpp/game/SceneCompositor.cpp'
p = S/name
before = p.read_text(encoding='utf8')
after = before
changes = [(
    '        const float scale=float(width)/640.f;',
    '''        const float scale=float(width)/640.f;
#if PORT_TITLE == 14
        manager.render_space.scale=scale;
#endif'''), (
    '        full_camera.screen();play_camera.screen();scaled_play_camera.screen();world_camera.screen();return;',
    '''        full_camera.screen();play_camera.screen();scaled_play_camera.screen();world_camera.screen();
#if PORT_TITLE == 14
        // Retail4468eb..44690e follows the four screen-camera calculations.
        manager.render_space.scaled_origin={float(i32(width)/2),float(i32(float(scale*16.f)))};
#endif
        return;'''), (
    '        renderer.offset={};renderer.tint_enabled=false;renderer.tint=0x80808080;',
    '''#if PORT_TITLE == 14
        // Retail446c72..446cb1 writes play origin after target/clear only
        // when the intermediate render target exists. Reset retains it.
        if(resource)manager.render_space.play_origin={float(i32(world_camera.render_width)/2),float((i32(world_camera.render_height)-448)/2)};
#endif
        renderer.offset={};renderer.tint_enabled=false;renderer.tint=0x80808080;''')]
for old, new in changes:
    assert after.count(old) == 1
    after = after.replace(old, new)
(H/'SceneCompositor-context-before.cpp').write_bytes(p.read_bytes())
p.write_text(after, encoding='utf8', newline='')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
(H/'SceneCompositor.cpp.diff').write_text(''.join(difflib.unified_diff(
    before.splitlines(True),after.splitlines(True),fromfile=name,tofile=name)),encoding='utf8')
P['changes'].append(dict(path=name,beforeSha256=sha(R/name),afterSha256=sha(p)))
P['sourceBindings'][name]=sha(p)
(H/'prepared-v1.json').write_bytes((H/'prepared.json').read_bytes())
(H/'prepared.json').write_text(json.dumps(P,indent=2)+'\n')
B=H/'candidate';j=json.loads((B/'build.json').read_bytes())
(B/'build-v1.json').write_bytes((B/'build.json').read_bytes())
row=next(x for x in j['objects'] if x['source']==name)
old=B/'SceneCompositor.cpp.o'
os.replace(old,B/'SceneCompositor-v1.cpp.o')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
with (B/'SceneCompositor-v2.log').open('wb') as log:
    subprocess.run([str(cc),*j['flags'],'-c',str(p),'-o',str(old)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
row['sourceSha256']=sha(p);row['objectSha256']=sha(old)
j['sourceBindings']=P['sourceBindings'];j['secondPassOnlySceneCompositorRecompiled']=True
for obj in j['objects']:assert sha(R/obj['object'])==obj['objectSha256']
(B/'build.json').write_text(json.dumps(j,indent=2)+'\n')
print(json.dumps(dict(files=len(P['changes']),normalProviders=141,updatedUnits=1,canonicalEngineChanged=False)))
