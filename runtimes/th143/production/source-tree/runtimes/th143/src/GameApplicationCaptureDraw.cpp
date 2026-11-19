#include "GameApplicationCaptureDraw.hpp"
namespace th143 {
bool finish_capture_application_draw(GameRenderRuntime& render,GameRenderDevice& device,GameAuxRuntime& aux,AnmView menu){
    if(!render.flush())return false;auto app=AnmView{render.application.data()};for(u32 at:{0x6b0u,0x6b4u,0x458u,0x45cu})app.put(at,0);const u32 token=device.game_device_token();
    for(u32 i=0;i<2;++i)if(aux.independent.signals&(1u<<i)){
        const u32 vm_token=aux.independent.animations[i];AnmView vm{nullptr};for(auto& s:aux.storage)if(vm_token>=s.token&&std::uint64_t(vm_token)+AnmView::bytes<=std::uint64_t(s.token)+s.bytes.size()){vm={s.bytes.data()+vm_token-s.token};break;}
        if(!vm.data||!device.application_render_target(token,0,aux.independent.surface)||!device.render_state(15,0))return false;
        vm.put(0x534,0xffffffff);if(!render.draw_player_visual(vm_token,vm)||!render.flush()||!device.render_state(15,1)||!device.application_render_target(token,0,app.get(0x1b4)))return false;
        if(i==0)aux.independent.signals=(aux.independent.signals&~1u)|4u;else aux.independent.signals&=~2u;
    }
    if(!menu.data||!(menu.get(0x91bc)&1u))return true;
    if(!device.application_render_target(token,0,app.get(0x1ac))||!device.render_state(15,0))return false;
    for(u32 at:{0x404u,0x9d0u}){auto vm=menu.sub(at);vm.put(0x534,0xffffffff);if(!render.draw_player_visual(0x6b020000+at,vm))return false;}
    if(!render.flush()||!device.render_state(15,1)||!device.application_render_target(token,0,app.get(0x1b4)))return false;menu.put(0x91bc,menu.get(0x91bc)&~1u);return true;
}
bool GameCaptureApplicationDraw::dispatch(i32& result){if(!composition.reset_batches())return false;base.trace.clear();base.failed_entry=0;return scheduler.dispatch(true,*this,result);}
bool GameCaptureApplicationDraw::invoke(u32 entry,u32 owner,u32& result){
    base.trace.insert(base.trace.end(),{entry,owner});result=1;bool ok=false;auto& frame=base.frame;auto& globals=base.globals;
    if(owner==0x72000000)ok=animations.draw_pool_callback(entry);
    else if(owner!=0x4e47d0)ok=services.application_owner_draw(entry,owner,result);
    else if(entry==0x445b60){auto app=AnmView{render.application.data()};frame.device=app.get(8);frame.width=world.width;frame.height=world.height;frame.render_target=app.get(0x1ac);frame.clear_color=app.get(0xa30);frame.first_origin=world.viewport.first_origin;std::memcpy(frame.stage_viewport.data(),app.data+0x694,16);ok=composition.begin_frame(frame,false);globals.scale=world.viewport.scale;globals.logical_width=frame.logical_width;globals.logical_height=frame.logical_height;}
    else if(entry==0x446290)ok=finish_capture_application_draw(render,device,auxiliary,menu);
    else if(entry==0x445e20||entry==0x445d10||entry==0x445fc0||entry==0x445ec0||entry==0x446110||entry==0x446060||entry==0x446240||entry==0x4461e0){ok=composition.draw(ApplicationCompositionPass(entry),globals);frame.logical_width=globals.logical_width;frame.logical_height=globals.logical_height;}
    if(!ok)base.failed_entry=entry;return ok;
}
}
