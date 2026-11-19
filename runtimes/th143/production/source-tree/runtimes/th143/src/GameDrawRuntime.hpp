#pragma once
#include "GameRenderRuntime.hpp"
#include "ObjectDraw.hpp"
#include "HudDraw.hpp"
#include "CheatDraw.hpp"
namespace th143 {
struct GameDrawOwners {
    AnmView root,ascii,hud,enemy,special,cheat,menu,save,timing,background;
    PlayerEquipmentFrameHost* equipment=nullptr;
    PlayerDrawHost* player=nullptr;
};
struct GameDrawGlobals {u32 game_flags=0,application_state=0;HudDrawGlobals hud;};
struct GameDrawServices {
    virtual ~GameDrawServices()=default;
    virtual bool draw_laser_virtual(u32,u32){return false;}
    virtual bool draw_menu_page(u32,AnmView){return false;}
};
// Shared gameplay drawing: actual registered owner bodies, actual CPU renderer
// and ASCII side effects. The application owns every passed owner and resource.
// Unsupported virtual subclasses/menu subpages fail at explicit boundaries.
class GameDrawRuntime final:public SchedulerHost,public PlayerEquipmentFrameHost,private AnmRenderMemory,private AnmTransformHost,private CheatDrawHost {
public:
    GameDrawRuntime(GameOwnerRuntime& o,GameStageRuntime& s,AnmResourceWorld& w,GameRenderRuntime& r,GameRenderDevice& d,GameDrawServices& p):owners(o),stage(s),world(w),render(r),device(d),platform(p){}
    GameDrawOwners bindings;GameDrawGlobals globals;u32 failed_entry=0;
    bool invoke(u32 entry,u32 owner,u32& result)override;
    bool release_callback(u32)override{return false;}
    bool timer_rate(u32 p,float& rate)override{return world.timer_rate(p,rate);}
    bool update_equipment_option(u32 p)override{return bindings.equipment&&bindings.equipment->update_equipment_option(p);}
    bool draw_equipment_option(u32 p)override;
    bool equipment_option_busy(u32 p,bool& v)override{return bindings.equipment&&bindings.equipment->equipment_option_busy(p,v);}
    bool equipment_option_count(u32 p,u32& v)override{return bindings.equipment&&bindings.equipment->equipment_option_count(p,v);}
    bool equipment_empty_sound(u32 p)override{return bindings.equipment&&bindings.equipment->equipment_empty_sound(p);}
private:
    static constexpr u32 manager=0x72000000,app_self=0x4e47d0;
    GameOwnerRuntime& owners;GameStageRuntime& stage;AnmResourceWorld& world;GameRenderRuntime& render;GameRenderDevice& device;GameDrawServices& platform;
    bool body(u32,u32);
    bool depth_write(u32);
    bool score();bool special();bool menu();bool input();bool timing();bool lasers();
    bool text(const std::array<float,3>& p,const char* f,double v,bool interface_layer=false);
    bool read_render_memory(u32,void*,u32)override;
    bool write_render_memory(u32,const void*,u32)override;
    AnmView transform_parent(u32)override;
    bool cheat_draw_format(const std::array<float,3>& p,const char* f,double v)override{return text(p,f,v);}
    bool cheat_draw_number(const std::array<float,3>& p,i32 v)override{return queue_ascii_text(bindings.ascii,p,format_ascii_number(u32(v)),world.viewport);}
};
// Construct this adapter before cold factories. Updates keep their existing
// services; draw dispatch uses the same GameFrameRuntime/Scheduler and owners.
class GameDrawFrameServices final:public GameFrameServices {
public:
    explicit GameDrawFrameServices(GameFrameServices& updates):updates(updates){}
    GameDrawRuntime* drawing=nullptr;bool in_draw=false;std::vector<u32> trace;
    bool dispatch(GameFrameRuntime& frames,i32& result){if(!drawing||in_draw)return false;in_draw=true;trace.clear();drawing->failed_entry=0;auto* equipment=frames.equipment_host;frames.equipment_host=drawing;const bool ok=frames.dispatch(true,result);frames.equipment_host=equipment;in_draw=false;return ok;}
    bool frame_input(GameInputFrame& g)override{return updates.frame_input(g);}
    bool before_game_callback(u32 e,u32 o)override{if(in_draw){trace.insert(trace.end(),{e,o});return true;}return updates.before_game_callback(e,o);}
    bool after_game_callback(u32 e,u32 o,u32 r)override{return in_draw||updates.after_game_callback(e,o,r);}
    bool other_game_callback(u32 e,u32 o,u32& r)override{if(in_draw||e==0x40b590)return drawing&&drawing->invoke(e,o,r);return updates.other_game_callback(e,o,r);}
    bool release_game_callback(u32 p)override{return updates.release_game_callback(p);}
private:GameFrameServices& updates;
};
}
