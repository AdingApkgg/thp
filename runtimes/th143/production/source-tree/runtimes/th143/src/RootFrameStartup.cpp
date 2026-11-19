#include "RootFrameStartup.hpp"

namespace th143 {
i32 root_frame_with_startup(RootState& root,AnmView hud,RootFrameGlobals& g,
                            RootStartupGlobals& startup,RootFrameHost& live,RootStartupHost& host){
    struct Adapter:RootFrameHost {
        RootStartupGlobals& state;RootFrameHost& live;RootStartupHost& host;
        RootStartupResult result=RootStartupResult::continue_frame;
        Adapter(RootStartupGlobals& s,RootFrameHost& l,RootStartupHost& h):state(s),live(l),host(h){}
        bool start_or_restart(RootState& root,RootFrameGlobals& g)override{
            state.config=g.config;state.application_state=g.application_state;state.game_flags=g.game_flags;
            state.frames=g.frames;state.scene_frames=g.scene_frames;
            result=start_root(root,state,host);
            g.config=state.config;g.application_state=state.application_state;g.game_flags=state.game_flags;
            g.frames=state.frames;g.scene_frames=state.scene_frames;
            if(result!=RootStartupResult::continue_frame)return false;
            u32 previous,flags=0;
            if(!host.startup_read(0x4e69fc,previous)||(previous&&!host.startup_read(previous+0x4224,flags)))return false;
            g.previous_dialog=previous!=0;g.previous_dialog_flags=flags;return true;
        }
        bool timer_rate(u32 token,float& rate)override{return live.timer_rate(token,rate);}
        u32 global_rate_token()const override{return live.global_rate_token();}
        bool notice(u32 kind,u32 duration,u32 message)override{return live.notice(kind,duration,message);}
        bool replay_exit()override{return live.replay_exit();}
        bool erase_previous_dialog()override{return live.erase_previous_dialog();}
        bool animate_backgrounds()override{return live.animate_backgrounds();}
    }adapter(startup,live,host);
    const i32 result=root_frame(root,hud,g,adapter);
    return adapter.result==RootStartupResult::return_one?1:result;
}
}
