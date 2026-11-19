#include "GameApplicationDraw.hpp"
namespace th143 {
bool GameApplicationDraw::register_callbacks(){
    if(registered)return false;
    for(auto row:{std::array<u32,2>{0x445b60,1},{0x445e20,14},{0x445d10,15},{0x445fc0,24},{0x445ec0,25},{0x446110,41},{0x446060,42},{0x446240,53},{0x4461e0,54},{0x446290,82}}){
        u32 p,result;if(!storage.allocate_game_storage(40,p)||!p||!scheduler.create(p,row[0],storage.game_allocation_fill()))return false;auto callback=scheduler.at(p);callback.put(4,callback.get(4)|2u);callback.put(0x24,0x4e47d0);if(!scheduler.add(p,i32(row[1]),true,*this,result))return false;
    }
    auto app=AnmView{render.application.data()};u32 back=app.get(0x1b4);if(!targets.target_backbuffer(app.get(8),back))return false;app.put(0x1b4,back);registered=true;return true;
}
bool GameApplicationDraw::dispatch(i32& result){if(!registered||!composition.reset_batches())return false;trace.clear();failed_entry=0;return scheduler.dispatch(true,*this,result);}
bool GameApplicationDraw::invoke(u32 entry,u32 owner,u32& result){
    trace.insert(trace.end(),{entry,owner});result=1;bool ok=false;
    if(owner!=0x4e47d0)ok=services.application_owner_draw(entry,owner,result);
    else if(entry==0x445b60){auto app=AnmView{render.application.data()};frame.device=app.get(8);frame.width=world.width;frame.height=world.height;frame.render_target=app.get(0x1ac);frame.clear_color=app.get(0xa30);frame.first_origin=world.viewport.first_origin;std::memcpy(frame.stage_viewport.data(),app.data+0x694,16);ok=composition.begin_frame(frame,false);globals.scale=world.viewport.scale;globals.logical_width=frame.logical_width;globals.logical_height=frame.logical_height;}
    else if(entry==0x446290){
        //4116e0's no-pending-capture branch. Active captures and menu4481d0
        // require their own real draw adapters before this path can run them.
        ok=render.flush();if(ok){auto app=AnmView{render.application.data()};for(u32 offset:{0x6b0u,0x6b4u,0x458u,0x45cu})app.put(offset,0);ok=!(independent_signals&3u)&&!menu_owner;}
    }else if(entry==0x445e20||entry==0x445d10||entry==0x445fc0||entry==0x445ec0||entry==0x446110||entry==0x446060||entry==0x446240||entry==0x4461e0){ok=composition.draw(ApplicationCompositionPass(entry),globals);frame.logical_width=globals.logical_width;frame.logical_height=globals.logical_height;}
    if(!ok)failed_entry=entry;return ok;
}
}
