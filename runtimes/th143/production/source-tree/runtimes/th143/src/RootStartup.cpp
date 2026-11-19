#include "RootStartup.hpp"

namespace th143 {
namespace {
bool callbacks(RootStartupHost& h,u32 global,bool required,u32 first=8){
    u32 owner;if(!h.startup_read(global,owner)||!owner)return false;
    for(u32 at:{first,first+4}){
        u32 callback;if(!h.startup_read(owner+at,callback))return false;
        if(!callback){if(required)return false;continue;}
        u32 flags;if(!h.startup_read(callback+4,flags)||!h.startup_write(callback+4,flags|2))return false;
    }return true;
}
bool owner_service(RootStartupHost& h,RootStartupService service,u32 global){
    u32 owner;return h.startup_read(global,owner)&&owner&&h.startup_service(service,owner);
}
bool ascii_signal(RootStartupHost& h,u32 offset,bool clear){
    u32 owner,handle;return h.startup_read(0x4e69f8,owner)&&owner&&h.startup_read(owner+offset,handle)&&
        h.startup_signal(handle,1)&&(!clear||h.startup_write(owner+offset,0));
}
bool music(RootStartupHost& h){
    u32 owner,track;return h.startup_read(0x4e6bac,owner)&&owner&&h.startup_read(owner+0x18,track)&&h.startup_music(0,track);
}
}
RootStartupResult start_root(RootState& root,RootStartupGlobals& g,RootStartupHost& h){
    using S=RootStartupService;using R=RootStartupResult;auto r=root.view();const u32 time=r.get(0x14);
    if(time&&!(time==30&&(r.get(0x80)&0x800)))return R::continue_frame;
    if(!time){
        if(!h.startup_clock(g.statistics_time)||!h.startup_service(S::hud_begin))return R::unsupported;
        if(r.get(0x80)&8){
            if(!h.startup_service(S::stop_worker,0x4e515c))return R::unsupported;
            g.application_state=((~(g.config>>13))&1)|2;return R::return_one;
        }
        if(!h.startup_service(S::stage_activate))return R::unsupported;
        u32 previous;if(!h.startup_read(0x4e69fc,previous))return R::unsupported;
        if(previous){
            if(!h.startup_service(S::replay_prepare)||!h.startup_service(S::replay_transition))return R::unsupported;
            r.put(0x80,r.get(0x80)|0x800);
            u32 hud,handle;if(!h.startup_read(0x4e6a54,hud)||!hud||!h.startup_read(hud+0xcc,handle)||!h.startup_signal(handle,1))return R::unsupported;
            return R::continue_frame;
        }
    }
    r.put(0x80,r.get(0x80)&~0x800u);
    if(!h.startup_service(S::bullets_reset)||!h.startup_service(S::player_reset)||
       !owner_service(h,S::items_reset,0x4e6b64)||!owner_service(h,S::enemies_reset,0x4e6a48)||
       !h.startup_service(S::lasers_reset))return R::unsupported;
    g.frames=g.scene_frames=0;
    if(!h.startup_service(S::statistics_begin))return R::unsupported;
    if(!time&&(!callbacks(h,0x4e6b68,true)||!h.startup_service(S::equipment_activate)))return R::unsupported;
    if(!h.startup_spawn_main({})||!h.startup_service(S::hud_initialize))return R::unsupported;
    for(auto entry:{std::array<u32,3>{0x4e6b84,0,8},{0x4e6b88,1,8},{0x4e6a08,0,8},
        {0x4e6a48,0,8},{0x4e6b64,0,8},{0x4e6b6c,0,8},{0x4e6a40,1,8},
        {0x4daef4,0,12},{0x4e6ba4,1,8},{0x4e6a0c,0,8}})
        if(!callbacks(h,entry[0],entry[1]!=0,entry[2]))return R::unsupported;
    if(!time){
        if((g.game_flags&0x60)!=0x40&&(g.game_flags&0x200)&&!music(h))return R::unsupported;
        if(!ascii_signal(h,0x191e8,false)||!ascii_signal(h,0x191ec,true))return R::unsupported;
        u32 handle;if(!h.startup_read(0x4e49a0,handle)||!h.startup_signal(handle,1)||!h.startup_write(0x4e49a0,0))return R::unsupported;
    }else{
        if(!h.startup_service(S::music_clear)||!music(h)||!ascii_signal(h,0x191ec,true))return R::unsupported;
        const u32 flags=r.get(0x20);if(!(flags&1)){r.put(0x1c,0x4e40b0);r.put(0x20,flags|1);}
        r.put(0x14,0);r.put(0x18,0);r.put(0x10,0xffffffff);
    }
    return R::continue_frame;
}
}
