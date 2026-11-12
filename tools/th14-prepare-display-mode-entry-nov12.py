"""Prepare an isolated display-mode candidate; canonical engine is untouched."""
from pathlib import Path
import difflib, hashlib, json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/display-mode-entry-nov12'
S = H / 'source'
S.mkdir(exist_ok=False)
base_path = R / 'artifacts/th14/camera-roles-nov12-v3/current-provider-bindings.json'
base = json.loads(base_path.read_bytes())
sha = lambda data: hashlib.sha256(data).hexdigest()
for name, digest in base['sourceBindings'].items():
    raw = (R / name).read_bytes()
    assert sha(raw) == digest, name
    out = S / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
changes = []

def edit(name, replacements):
    path = S / name
    before = path.read_text(encoding='utf8')
    after = before
    for old, new, count in replacements:
        assert after.count(old) == count, (name, old, after.count(old))
        after = after.replace(old, new)
    assert after != before
    path.write_text(after, encoding='utf8', newline='')
    changes.append(dict(path=name, beforeSha256=sha((R/name).read_bytes()),
                        afterSha256=sha(path.read_bytes())))
    (H / (path.name + '.diff')).write_text(''.join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True), fromfile=name, tofile=name)), encoding='utf8')

game = 'runtimes/th12/th12_web/cpp/game/'
sdl = 'runtimes/th12/th12_web/cpp/sdl/'
edit(game+'GameConfig.hpp', [(
    '    bool auto_focus()const noexcept{return bytes[volume_offset+2]!=0;}',
    '''    bool auto_focus()const noexcept{return bytes[volume_offset+2]!=0;}
#if PORT_TITLE == 14
    // Retail46af64 selects the mode;46ae40 supplies the internal pixel size.
    u32 render_width()const noexcept{
        const u32 mode=bytes[0x1f];
        return mode==1||mode==4?960:mode==2||mode==5?1280:640;
    }
    u32 render_height()const noexcept{return render_width()*3/4;}
#endif''', 1)])
edit(game+'GameSession.hpp', [(
    '    bool update(const GameSessionInput& input);',
    '''    bool initialize_compositor(){
#if PORT_TITLE == 14
        const auto& display=persistent_config();
        return compositor.initialize(resources.core.text,display.render_width(),display.render_height());
#else
        return compositor.initialize(resources.core.text);
#endif
    }
    void reset_compositor_cameras(bool restricted){
#if PORT_TITLE == 14
        const auto& display=persistent_config();
        compositor.reset_cameras(restricted,display.render_width(),display.render_height());
#else
        compositor.reset_cameras(restricted);
#endif
    }
    bool update(const GameSessionInput& input);''', 1)])
edit(game+'GameSession.cpp', [
    ('compositor.initialize(resources.core.text)', 'initialize_compositor()', 4),
    ('compositor.reset_cameras(false)', 'reset_compositor_cameras(false)', 4)])
edit(sdl+'GraphicsDevice.hpp', [(
    '    bool initialize();',
    '''#if PORT_TITLE == 14
    bool initialize(u32 width=640,u32 height=480);
#else
    bool initialize();
#endif''', 1)])
edit(sdl+'GraphicsDevice.cpp', [(
    'bool GraphicsDevice::initialize(){',
    '''#if PORT_TITLE == 14
bool GraphicsDevice::initialize(u32 width,u32 height){
#else
bool GraphicsDevice::initialize(){
    constexpr u32 width=640,height=480;
#endif''', 1),
    ('image.width=640;image.height=480;image.pitch=640*',
     'image.width=width;image.height=height;image.pitch=width*', 1),
    ('if(!backend.initialize()){error=backend.error();return false;}SDL_SetWindowTitle',
     '''if(!backend.initialize()){error=backend.error();return false;}
#if PORT_TITLE == 14
    if(width!=640||height!=480)SDL_SetWindowSize(backend.native_window(),int(width),int(height));
#endif
    SDL_SetWindowTitle''', 1)])
app = (S / (sdl+'Application.cpp')).read_text(encoding='utf8')
start = app.index('        mkdir("/save",0777);mkdir("/save/replay",0777);')
end = app.index('        audio.music_volume=session.config.music_volume();', start)
block = app[start:end]
# Keep non-TH14 score/config initialization in its previous position.
config_start = block.index('        if(SDL_GetPathInfo(config_path,nullptr)){')
config = block[config_start:]
edit(sdl+'Application.cpp', [
    ('        if(!graphics.initialize()){error=graphics.error;return false;}',
     '''#if PORT_TITLE == 14
        mkdir("/save",0777);mkdir("/save/replay",0777);
'''+config+'''        if(!graphics.initialize(session.config.render_width(),session.config.render_height())){error=graphics.error;return false;}
#else
        if(!graphics.initialize()){error=graphics.error;return false;}
#endif''', 1),
    (block, '#if PORT_TITLE != 14\n'+block+'#endif\n', 1),
    ('session.compositor.initialize(session.resources.core.text)', 'session.initialize_compositor()', 1),
    ('app.session.compositor.initialize(app.session.resources.core.text)', 'app.session.initialize_compositor()', 1),
    ('session.compositor.initialize(*job.resource)', 'session.initialize_compositor()', 1),
    ('session.compositor.reset_cameras(false)', 'session.reset_compositor_cameras(false)', 3),
    ('        renderer.viewport={0,0,640,480,0,1};',
     '''#if PORT_TITLE == 14
        renderer.viewport={0,0,session.config.render_width(),session.config.render_height(),0,1};
#else
        renderer.viewport={0,0,640,480,0,1};
#endif''', 1)])
edit('runtimes/th12/portable/sdl/Renderer.cpp', [(
    'glBlitFramebuffer(0,0,s.width,s.height,0,480,640,0,GL_COLOR_BUFFER_BIT,GL_NEAREST);',
    '''
#if defined(PORT_TITLE) && PORT_TITLE == 14
glBlitFramebuffer(0,0,s.width,s.height,0,s.height,s.width,0,GL_COLOR_BUFFER_BIT,GL_NEAREST);
#else
glBlitFramebuffer(0,0,s.width,s.height,0,480,640,0,GL_COLOR_BUFFER_BIT,GL_NEAREST);
#endif
''', 1)])
bindings = {name: sha((S/name).read_bytes()) for name in base['sourceBindings']}
report = dict(schema='thp/th14-display-mode-candidate/1', sourceRoot=str(S), changes=changes,
              sourceBindings=bindings, baseManifestSha256=sha(base_path.read_bytes()),
              canonicalEngineChanged=False, deployed=False, completeGame=False)
(H/'prepared.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(dict(changedFiles=len(changes), sourceBindings=len(bindings), canonicalEngineChanged=False)))
