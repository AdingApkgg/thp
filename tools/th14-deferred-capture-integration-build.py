"""Build reviewable private TH14 menu/application capture wiring snapshots.

This tool never edits production or another agent's loading prototype. It
freezes all original game headers for type/layout checks, then changes only
PauseMenu.hpp/.cpp, PauseEnd.cpp and Application.cpp in its own tree.
"""
import hashlib,json,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RT=ROOT/'runtimes/th12/th12_web'
OUT=ROOT/'artifacts/th14/deferred-capture-integration-oct14';sha=lambda b:hashlib.sha256(b).hexdigest()
OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'integration-complete.json').exists(),'Completed integration is immutable'
bindings={}
for file in sorted((RT/'cpp').rglob('*')):
    if not file.is_file() or file.suffix not in ('.cpp','.hpp','.h','.inc'):continue
    relative=file.relative_to(RT);data=file.read_bytes();bindings[relative.as_posix()]={'bytes':len(data),'sha256':sha(data)}
    target=OUT/'source'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    before=OUT/'before'/relative
    if relative.as_posix() in ['cpp/game/PauseMenu.hpp','cpp/game/PauseMenu.cpp','cpp/game/PauseEnd.cpp','cpp/sdl/Application.cpp']:
        before.parent.mkdir(parents=True,exist_ok=True);before.write_bytes(data)
queue=(ROOT/'artifacts/th14/deferred-capture-prototype-oct14/DeferredCaptureQueueTh14.hpp').read_bytes()
(OUT/'source/cpp/game/DeferredCaptureQueueTh14.hpp').write_bytes(queue)
bridge='''#pragma once
#include "DeferredCaptureQueueTh14.hpp"
#include <unordered_map>
namespace th11 {
class AnmManager;
// Private scope-limited bridge. Production should put the queue explicitly
// on AnmManager/session ownership; this registry is not a completed design.
inline auto& th14_capture_bindings(){static std::unordered_map<AnmManager*,DeferredCaptureQueueTh14*> bindings;return bindings;}
inline DeferredCaptureQueueTh14* th14_capture_queue(AnmManager& manager){auto& map=th14_capture_bindings();auto it=map.find(&manager);return it==map.end()?nullptr:it->second;}
struct DeferredCaptureBindingTh14 {
 AnmManager& manager;DeferredCaptureQueueTh14& queue;
 DeferredCaptureBindingTh14(AnmManager& a,DeferredCaptureQueueTh14& q):manager(a),queue(q){th14_capture_bindings()[&manager]=&queue;}
 ~DeferredCaptureBindingTh14(){auto& map=th14_capture_bindings();auto it=map.find(&manager);if(it!=map.end()&&it->second==&queue)map.erase(it);}
 DeferredCaptureBindingTh14(const DeferredCaptureBindingTh14&)=delete;
 DeferredCaptureBindingTh14& operator=(const DeferredCaptureBindingTh14&)=delete;
};
}
'''
(OUT/'source/cpp/game/DeferredCaptureBindingTh14.hpp').write_text(bridge,encoding='utf8')
app_helper='''#pragma once
#include "../game/DeferredCaptureBindingTh14.hpp"
namespace th11::sdl {
struct ImmediateCaptureSourceTh14 {bool text_intermediate=false;i32 rectangle[4]{};};
template<class Session> ImmediateCaptureSourceTh14 th14_immediate_capture_source(const Session& session){
 // Native448bf0 tests GUI+194 after both448d80 Pause and449d30 death.
 // It does not test the public session phase. Normal Pause remains unchanged.
 const bool dialogue=session.battle&&session.battle->dialogue&&session.battle->dialogue->active;
 return {dialogue,{dialogue?128:32,16,dialogue?512:416,464}};
}
template<class Session> AnmResource* th14_deferred_capture_target(Session& session,const DeferredCaptureRequestTh14& request){
 // Both actual44be40 callers use text52 from Supervisor+71c/slot0.
 // Do not invent a generic owner map for normalized player/ANM file tags.
 if(request.file_index!=0||request.texture_index<0)return nullptr;
 auto& text=session.resources.core.text;
 return u32(request.texture_index)<text.textures.size()?&text:nullptr;
}
template<class Session,class Graphics,class Render>
void th14_consume_deferred_captures(DeferredCaptureQueueTh14& queue,Session& session,Graphics& graphics,Render& renderer){
 queue.consume([&](const auto& request){
  auto* resource=th14_deferred_capture_target(session,request);if(!resource)return;
  const u32 target=graphics.texture(*resource,u32(request.texture_index));if(!target)return;
  i32 from[4]={request.source[0],request.source[1],request.source[0]+request.source[2],request.source[1]+request.source[3]};
  i32 to[4]={request.destination[0],request.destination[1],request.destination[0]+request.destination[2],request.destination[1]+request.destination[3]};
  renderer.flush();
  // Return values do not keep a request alive. This is request retirement,
  // not successful GPU completion or a resource-lifetime fence.
  graphics.backend.resample(Graphics::screen,from,target,to,nullptr,0,0);
  graphics.changed(target);renderer.invalidate();
 });
}
}
'''
(OUT/'source/cpp/sdl/ApplicationCaptureTh14.hpp').write_text(app_helper,encoding='utf8')
def edit(relative,changes):
    path=OUT/'source'/relative;source=path.read_text(encoding='utf8')
    for before,after in changes:
        assert source.count(before)==1,(relative,before,source.count(before));source=source.replace(before,after)
    path.write_text(source,encoding='utf8')
edit('cpp/game/PauseMenu.hpp',[
 ('#include "AsciiText.hpp"','#include "AsciiText.hpp"\n#if PORT_TITLE == 14\n#include "DeferredCaptureBindingTh14.hpp"\n#endif'),
 ('    bool create_backdrop();','    #if PORT_TITLE == 14\n    bool create_backdrop(bool immediate_capture=true);\n    #else\n    bool create_backdrop();\n    #endif'),
 ('    void manual_choices();','    bool create_deferred_backdrop_th14();\n    void manual_choices();'),
])
edit('cpp/game/PauseMenu.cpp',[
 ('bool PauseMenu::create_backdrop(){','#if PORT_TITLE == 14\nbool PauseMenu::create_backdrop(bool immediate_capture){\n#else\nbool PauseMenu::create_backdrop(){\n#endif'),
 ('background_animation=vm->id;capture_requested=true;return true;','background_animation=vm->id;\n#if PORT_TITLE == 14\n    capture_requested=immediate_capture;\n#else\n    capture_requested=true;\n#endif\n    return true;'),
])
deferred_method='''#if PORT_TITLE == 14
bool PauseMenu::create_deferred_backdrop_th14(){
 auto* queue=th14_capture_queue(animations);
 if(!queue){error="TH14 deferred capture queue is not bound";return false;}
 if(!create_backdrop(false))return false;
 auto* vm=animations.find(background_animation);
 if(!vm||vm->resource!=&text||!vm->sprite){error="TH14 deferred text52 sprite missing";return false;}
 const auto& sprite=*vm->sprite;
 DeferredCaptureRequestTh14 request;
 request.file_index=i32(vm->file_index);request.texture_index=i32(sprite.texture);
 request.source={32,16,384,448};
 request.destination={i32(sprite.x),i32(sprite.y),i32(sprite.width),i32(sprite.height)};
 queue->enqueue(request);return true;
}
#endif
'''
edit('cpp/game/PauseEnd.cpp',[
 ('void PauseMenu::visible(bool value){',deferred_method+'void PauseMenu::visible(bool value){'),
 ('    if(!create_backdrop())return false;\n    if constexpr(kPortTitle==14){','''#if PORT_TITLE == 14
    //449d30 death uses448bf0 ImmediatePause, in all run flag branches.
    //449f20 completion queues only flags0/normal Extra at entry. Completed
    //StagePractice waits for31's80-frame handler; SpellPractice has no copy.
    if(!completed){if(!create_backdrop())return false;}
    else if(!practice){if(!create_deferred_backdrop_th14())return false;}
#else
    if(!create_backdrop())return false;
#endif
    if constexpr(kPortTitle==14){'''),
 ('    case 13:case 21:\n        if(timer.current<10)break;','''    case 13:case 21:
#if PORT_TITLE == 14
        if(practice&&completed&&spell_practice_id<0){
            if(timer.current<80)break;
            if(!create_deferred_backdrop_th14())return;
        }else
#endif
        if(timer.current<10)break;'''),
])
edit('cpp/sdl/Application.cpp',[
 ('#include "PauseCaptureTh14.hpp"','#include "PauseCaptureTh14.hpp"\n#include "ApplicationCaptureTh14.hpp"'),
 ('    FrameStatistics frame_statistics;','''#if PORT_TITLE == 14
    DeferredCaptureQueueTh14 deferred_captures;
    DeferredCaptureBindingTh14 deferred_capture_binding{session.animations,deferred_captures};
#endif
    FrameStatistics frame_statistics;'''),
 ('const auto capture=th14_pause_capture_source(session);','const auto capture=th14_immediate_capture_source(session);'),
 ('        graphics.present();','''#if PORT_TITLE == 14
        // Actual draw commands must finish submission before4690d0 retirement.
        th14_consume_deferred_captures(deferred_captures,session,graphics,renderer);
#endif
        graphics.present();'''),
])
changed=['cpp/game/PauseMenu.hpp','cpp/game/PauseMenu.cpp','cpp/game/PauseEnd.cpp','cpp/sdl/Application.cpp']
patch=[]
for name in changed:
    before=(OUT/'before'/name).read_text(encoding='utf8').splitlines(True)
    after=(OUT/'source'/name).read_text(encoding='utf8').splitlines(True)
    patch.extend(difflib.unified_diff(before,after,fromfile='a/'+name,tofile='b/'+name))
for name in ['cpp/game/DeferredCaptureQueueTh14.hpp','cpp/game/DeferredCaptureBindingTh14.hpp','cpp/sdl/ApplicationCaptureTh14.hpp']:
    after=(OUT/'source'/name).read_text(encoding='utf8').splitlines(True)
    patch.extend(difflib.unified_diff([],after,fromfile='/dev/null',tofile='b/'+name))
(OUT/'integration.patch').write_text(''.join(patch),encoding='utf8')
report=dict(privateIntegrationPrepared=True,productionChanged=False,completeGame=False,nativeEquivalent=False,modifiedExistingFiles=changed,
 rootPrototypeQueueSha256=sha(queue),sourceBindings=bindings,
 newPrivateFiles={p.relative_to(OUT/'source').as_posix():{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in (OUT/'source').rglob('*') if p.is_file() and(p.relative_to(OUT/'source').as_posix() in changed or p.name in ['DeferredCaptureQueueTh14.hpp','DeferredCaptureBindingTh14.hpp','ApplicationCaptureTh14.hpp'])},
 patchSha256=sha((OUT/'integration.patch').read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),
 scope='Private scoped integration prototype only. No GameSession or AnmManager changes. Application owns the queue and a declared per-manager static binding bridge for its lifetime; production must replace that bridge with explicit manager/session ownership. Real actual text52 caller resource/texture identity is used; no generic file-index owner mapping or boot-upload queue substitution. Native request retirement is not GPU success. Immediate source phase contract is newly widened and needs separate code-level evidence; no pixel equality claim.')
(OUT/'integration-inputs.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'privateIntegrationPrepared':True,'modifiedExistingFiles':changed,'patchSha256':report['patchSha256']}))
