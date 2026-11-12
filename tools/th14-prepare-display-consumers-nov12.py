"""Isolate two measured TH14 display-size consumers; leave other titles unchanged."""
from pathlib import Path
import difflib, hashlib, json
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/display-consumers-nov12';H.mkdir(exist_ok=False)
S=H/'source';base_path=R/'artifacts/th14/display-mode-entry-nov12/current-provider-bindings.json'
base=json.loads(base_path.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
for name,digest in base['sourceBindings'].items():
    raw=(R/name).read_bytes();assert sha(raw)==digest,name
    out=S/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
changes=[]
def edit(name,old,new):
    p=S/name;before=p.read_text(encoding='utf8');assert before.count(old)==1,name
    after=before.replace(old,new);p.write_text(after,encoding='utf8',newline='')
    changes.append(dict(path=name,beforeSha256=sha((R/name).read_bytes()),afterSha256=sha(p.read_bytes())))
    (H/(p.name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=name,tofile=name)),encoding='utf8')
g='runtimes/th12/th12_web/cpp/game/'
edit(g+'ScreenFade.cpp', '''    // TH14 Stage type2/3 uses 46ca40: full virtual-window vertices, retaining
    // the active viewport. The compositor clips it to the current target.
    if(kPortTitle==14&&(type==2||type==3))renderer.solid_rectangle(0,0,640,480,(u32(alpha)<<24)|color);
    else if(type==5||(kPortTitle==14&&type==0)){renderer.set_viewport({0,0,640,480,0,1});renderer.solid_rectangle(0,0,640,480,(u32(alpha)<<24)|color);}
    else renderer.solid_rectangle(32,16,416,464,(u32(alpha)<<24)|color);''', '''#if PORT_TITLE == 14
    // Retail46c8d0 and46ca40 read the current internal display dimensions.
    // Type2/3 retain the active viewport; type0/5 first select the full window.
    if(type==0||type==2||type==3||type==5){
        if(type==0||type==5)renderer.set_viewport({0,0,renderer.render_width,renderer.render_height,0,1});
        renderer.solid_rectangle(0,0,float(renderer.render_width),float(renderer.render_height),(u32(alpha)<<24)|color);
    }else renderer.solid_rectangle(32,16,416,464,(u32(alpha)<<24)|color);
#else
    if(type==5){renderer.set_viewport({0,0,640,480,0,1});renderer.solid_rectangle(0,0,640,480,(u32(alpha)<<24)|color);}
    else renderer.solid_rectangle(32,16,416,464,(u32(alpha)<<24)|color);
#endif''')
edit(g+'ScreenDeformation.cpp', 'const float u=float(double(px)/640),v=float(double(py)/480);',
     'const float u=kPortTitle==14?px/(manager.render_space.scale*640.f):float(double(px)/640),v=kPortTitle==14?py/(manager.render_space.scale*480.f):float(double(py)/480);')
edit(g+'ScreenDeformation.cpp', 'e.current.position.x+(kPortTitle==16?manager.render_space.play_origin.x:320.f)',
     'e.current.position.x+(kPortTitle==16?manager.render_space.play_origin.x:(manager.render_space.scale*640.f)*.5f)')
edit(g+'ScreenDeformation.cpp', 'v.uv={p.x/640.f,p.y/480.f};',
     '// Retail4245d5/4245ed divide by the current display width/height.\n        v.uv={p.x/(kPortTitle==14?manager.render_space.scale*640.f:640.f),p.y/(kPortTitle==14?manager.render_space.scale*480.f:480.f)};')
# Consolidate multiple replacements of one translation unit into one final binding.
changes={row['path']:dict(path=row['path'],beforeSha256=sha((R/row['path']).read_bytes()),afterSha256=sha((S/row['path']).read_bytes())) for row in changes}
for name in changes:
    a=(R/name).read_text(encoding='utf8');b=(S/name).read_text(encoding='utf8')
    (H/(Path(name).name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=name,tofile=name)),encoding='utf8')
report=dict(schema='thp/th14-display-consumers-candidate/1',sourceRoot=str(S),changes=list(changes.values()),
    sourceBindings={n:sha((S/n).read_bytes()) for n in base['sourceBindings']},baseManifest=str(base_path.relative_to(R)),
    baseManifestSha256=sha(base_path.read_bytes()),canonicalEngineChanged=False,completeGame=False)
(H/'prepared.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(changedFiles=len(changes),sourceBindings=len(report['sourceBindings']),canonicalEngineChanged=False)))
