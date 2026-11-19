#include "GameMenuApplicationDraw.hpp"
namespace th143 {
bool GameMenuApplicationDraw::dispatch(i32& result){if(!composition.reset_batches())return false;base.trace.clear();base.failed_entry=0;return scheduler.dispatch(true,*this,result);}
bool GameMenuApplicationDraw::invoke(u32 entry,u32 owner,u32& result){
    base.trace.insert(base.trace.end(),{entry,owner});result=1;bool ok=false;auto& frame=base.frame;auto& globals=base.globals;
    if(owner==0x72000000)ok=menu.draw_pool_callback(entry);
    else if(owner!=0x4e47d0)ok=services.application_owner_draw(entry,owner,result);
    else if(entry==0x445b60){auto app=AnmView{render.application.data()};frame.device=app.get(8);frame.width=world.width;frame.height=world.height;frame.render_target=app.get(0x1ac);frame.clear_color=app.get(0xa30);frame.first_origin=world.viewport.first_origin;std::memcpy(frame.stage_viewport.data(),app.data+0x694,16);ok=composition.begin_frame(frame,false);globals.scale=world.viewport.scale;globals.logical_width=frame.logical_width;globals.logical_height=frame.logical_height;}
    else if(entry==0x446290){ok=render.flush();if(ok){auto app=AnmView{render.application.data()};for(u32 offset:{0x6b0u,0x6b4u,0x458u,0x45cu})app.put(offset,0);ok=!(base.independent_signals&3u)&&!base.menu_owner;}}
    else if(entry==0x445e20||entry==0x445d10||entry==0x445fc0||entry==0x445ec0||entry==0x446110||entry==0x446060||entry==0x446240||entry==0x4461e0){ok=composition.draw(ApplicationCompositionPass(entry),globals);frame.logical_width=globals.logical_width;frame.logical_height=globals.logical_height;}
    if(!ok)base.failed_entry=entry;return ok;
}
}
