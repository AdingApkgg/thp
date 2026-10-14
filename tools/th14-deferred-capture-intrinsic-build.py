"""Private v2 intrinsic AnmManager queue; never mutates production or v1."""
import hashlib,json,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];V1=ROOT/'artifacts/th14/deferred-capture-integration-oct14';OUT=ROOT/'artifacts/th14/deferred-capture-intrinsic-oct14';sha=lambda b:hashlib.sha256(b).hexdigest()
v1=json.loads((V1/'integration-inputs.json').read_bytes());complete=json.loads((V1/'integration-complete.json').read_bytes())
assert sha((ROOT/'docs/porting/th14-deferred-capture-bridge-verified-oct14.json').read_bytes())==complete['reportSha256']
assert sha((V1/'integration.patch').read_bytes())==complete['patchSha256']==v1['patchSha256']
OUT.mkdir(parents=True,exist_ok=True);assert not(OUT/'intrinsic-complete.json').exists(),'Completed intrinsic prototype is immutable'
for path in (V1/'source').rglob('*'):
    if not path.is_file() or path.name=='DeferredCaptureBindingTh14.hpp':continue
    relative=path.relative_to(V1/'source');target=OUT/'source'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
def edit(relative,changes):
    path=OUT/'source'/relative;source=path.read_text(encoding='utf8')
    for before,after in changes:
        assert source.count(before)==1,(relative,before);source=source.replace(before,after)
    path.write_text(source,encoding='utf8')
edit('cpp/game/AnmManager.hpp',[
 ('#include "PortTitle.hpp"','#include "PortTitle.hpp"\n#if PORT_TITLE == 14\n#include "DeferredCaptureQueueTh14.hpp"\n#endif'),
 ('    u32 next_id=0,spawn_depth=0;\n};','''    u32 next_id=0,spawn_depth=0;
#if PORT_TITLE == 14
public:
    // Native capture records belong to this manager, not to a menu, a
    // staged resource job, or a GPU completion counter. VM clear preserves it.
    DeferredCaptureQueueTh14 deferred_captures;
    i32 first_deferred_capture_file_index()const noexcept{return deferred_captures.first_file_index();}
    // Headless has no copy target. This explicitly retires request records,
    // never simulates Native GPU completion or a hardware/resource fence.
    void retire_deferred_captures_without_target(){deferred_captures.consume([](const auto&){});}
#endif
};'''),
])
edit('cpp/game/PauseMenu.hpp',[('#if PORT_TITLE == 14\n#include "DeferredCaptureBindingTh14.hpp"\n#endif\n','')])
edit('cpp/game/PauseEnd.cpp',[
 (' auto* queue=th14_capture_queue(animations);\n if(!queue){error="TH14 deferred capture queue is not bound";return false;}',' auto& queue=animations.deferred_captures;'),
 (' queue->enqueue(request);return true;',' queue.enqueue(request);return true;'),
])
edit('cpp/sdl/ApplicationCaptureTh14.hpp',[('#include "../game/DeferredCaptureBindingTh14.hpp"','#include "../game/AnmManager.hpp"')])
edit('cpp/sdl/Application.cpp',[
 ('''#if PORT_TITLE == 14
    DeferredCaptureQueueTh14 deferred_captures;
    DeferredCaptureBindingTh14 deferred_capture_binding{session.animations,deferred_captures};
#endif
''',''),
 ('th14_consume_deferred_captures(deferred_captures,session,graphics,renderer);','th14_consume_deferred_captures(session.animations.deferred_captures,session,graphics,renderer);'),
])
changed=[*v1['modifiedExistingFiles'],'cpp/game/AnmManager.hpp'];bindings=v1['sourceBindings'];patch=[]
for relative in changed:
    before_path=V1/'before'/relative if relative in v1['modifiedExistingFiles'] else V1/'source'/relative
    before_bytes=before_path.read_bytes();assert sha(before_bytes)==bindings[relative]['sha256']
    target=OUT/'before'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(before_bytes)
    before=before_bytes.decode('utf8').splitlines(True);after=(OUT/'source'/relative).read_text(encoding='utf8').splitlines(True)
    patch.extend(difflib.unified_diff(before,after,fromfile='a/'+relative,tofile='b/'+relative))
for relative in ['cpp/game/DeferredCaptureQueueTh14.hpp','cpp/sdl/ApplicationCaptureTh14.hpp']:
    patch.extend(difflib.unified_diff([],(OUT/'source'/relative).read_text(encoding='utf8').splitlines(True),fromfile='/dev/null',tofile='b/'+relative))
(OUT/'intrinsic.patch').write_text(''.join(patch),encoding='utf8')
assert not(OUT/'source/cpp/game/DeferredCaptureBindingTh14.hpp').exists()
for relative in ['cpp/game/PauseMenu.hpp','cpp/game/PauseEnd.cpp','cpp/sdl/Application.cpp','cpp/sdl/ApplicationCaptureTh14.hpp']:
    data=(OUT/'source'/relative).read_bytes();assert b'th14_capture_queue' not in data and b'th14_capture_bindings' not in data and b'DeferredCaptureBindingTh14' not in data
report=dict(privateIntrinsicPrepared=True,productionChanged=False,completeGame=False,nativeEquivalent=False,sourceBindings=bindings,modifiedExistingFiles=changed,
 sourceFiles={p.relative_to(OUT/'source').as_posix():{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in (OUT/'source').rglob('*') if p.is_file()},
 v1CompletionSha256=sha((V1/'integration-complete.json').read_bytes()),v1PatchSha256=v1['patchSha256'],patchSha256=sha((OUT/'intrinsic.patch').read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),
 scope='Private v2 explicit AnmManager-owned queue appended after existing fields under PORT_TITLE14. No static capture map or registration scope remains. Existing manager field offsets remain; full production rebuild is still required for enclosing GameSession layout. VM clear does not reset records. Actual text52 caller identity remains scoped, normal/death completion classification retained, postDraw consumes the same manager queue, and headless request retirement is explicit without a GPU target. No ROOT/loading prototype or production edits.')
(OUT/'intrinsic-inputs.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'privateIntrinsicPrepared':True,'modifiedExistingFiles':changed,'patchSha256':report['patchSha256']}))
