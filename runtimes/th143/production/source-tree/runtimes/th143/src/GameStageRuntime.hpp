#pragma once
#include "GameOwnerRuntime.hpp"
#include "StageFrame.hpp"
namespace th143 {
struct GameStageServices {
    virtual ~GameStageServices()=default;
    virtual bool read_game_stage_file(const std::string&,std::vector<u8>&)=0;
    virtual bool game_stage_warp(StageState&){return false;}
};
// The background Stage owner shares gameplay resources/Scheduler; STD storage
// and primitive VMs remain owned here. Presentation uses StageDraw separately.
class GameStageRuntime final:private StageInitHost,private StageAnimationMemory,private StageFrameServices {
public:
    static constexpr u32 self=0x6c010000;
    GameStageRuntime(GameFrameRuntime& f,AnmWorld& a,GameOwnerServices& s,GameStageServices& io)
        :frames(f),animations(a),services(s),files(io){}
    StageState state;
    StageInitGlobals loading;
    StageScriptGlobals script;
    std::array<u8,0x12c> camera{};
    std::vector<GameOwnerRuntime::Storage> storage;
    bool created=false,failed=false;
    bool create(const std::string&,u32& result);
    bool activate();
    i32 update();
    bool read(u32,void*,u32);
    bool write(u32,const void*,u32);
private:
    GameFrameRuntime& frames;AnmWorld& animations;GameOwnerServices& services;GameStageServices& files;
    AnmView mapped(u32,u32);
    bool read_stage_memory(u32 p,void* out,u32 n)override{return read(p,out,n);}
    bool write_stage_memory(u32 p,const void* in,u32 n)override{return write(p,in,n);}
    bool allocate_stage_storage(u32,bool,u32&)override;
    bool read_stage_file(const std::string&,u32&,u32&)override;
    bool request_stage_animation(u32 slot,const std::string& name,u32& token)override{return services.request_game_resource(slot,name.c_str(),token);}
    bool register_stage_callback(u32,i32,bool,u32,u32&)override;
    bool read_stage_animation_memory(u32 p,void* out,u32 n)override{return read(p,out,n);}
    bool write_stage_animation_memory(u32 p,const void* in,u32 n)override{return write(p,in,n);}
    AnmView stage_animation_storage(u32 p)override{return mapped(p,AnmView::bytes);}
    AnmView stage_animation_template(u32,i32)override;
    bool set_stage_animation_rate(float value,float& previous)override{previous=animations.rate;animations.rate=value;return true;}
    bool update_stage_warp(StageState& s)override{return files.game_stage_warp(s);}
};
}
