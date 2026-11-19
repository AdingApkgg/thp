#pragma once
#include "GameFrameRuntime.hpp"
#include "PlayerInit.hpp"
#include "LogicalRegionStorageV148.hpp"

namespace th143 {
struct GameOwnerServices {
    virtual ~GameOwnerServices()=default;
    // The session reserves these logical addresses; C++ owns their storage.
    virtual bool reserve_game_owner(u32 token,u32 bytes)=0;
    virtual bool allocate_game_storage(u32 bytes,u32& token)=0;
    virtual bool release_game_storage(u32 token)=0;
    virtual bool request_game_resource(u32 slot,const char* name,u32& token)=0;
    virtual bool read_player_shots(std::vector<u8>&)=0;
    virtual u8 game_allocation_fill()const{return 0;}
};
// Cold factories used by432440. All callbacks belong to the application's
// actual Scheduler and remain disabled until RootStartup enables them.
// Reinitialization, replay-file mode and failure destructors are separate work;
// an unsupported/failed operation latches failure instead of faking success.
class GameOwnerRuntime final:private PlayerInitHost,private PlayerEquipmentHost,private GameInputServices {
public:
    static constexpr u32 player_self=0x6a000000,shots_self=0x6a100000;
    static constexpr u32 equipment_self=0x6b001000,input_self=0x6e000000,laser_self=0x6c000000;
    GameOwnerRuntime(GameFrameRuntime&,AnmWorld&,GameOwnerServices&);
    PlayerState player;
    PlayerShotData shots;
    PlayerPower power;
    PlayerEquipmentState equipment;
    GameInputRuntime input;
    BulletPool bullets;
    ItemPool items;
    ScorePopups scores;
    std::array<u8,0x600> lasers{};
    struct Storage{u32 token;std::vector<u8> bytes;};
    LogicalRegionStorageV148 storage;
    u32 created=0;
    bool failed=false;
    // Entry is the actual factory address; mode is only meaningful for454740.
    bool create(u32 entry,u32 mode,GameManagerInitGlobals&,u32& result);
    bool read(u32 token,void*,u32 bytes);
    bool write(u32 token,const void*,u32 bytes);
private:
    GameFrameRuntime& frames;
    AnmWorld& animations;
    GameOwnerServices& services;
    AnmView mapped(u32,u32);
    bool reserve(u32 bit,u32 token,u8*,u32 bytes);
    bool allocate(u32,u32&);
    bool callback(u32 entry,i32 priority,bool draw,u32 owner,u32& token);
    bool pair(u32 owner,AnmView,u32 update,i32 update_priority,u32 draw,i32 draw_priority);
    bool bind_initial_visual(PlayerState&)override;
    bool equipment_read(u32 p,u32& v)override{return read(p,&v,4);}
    bool equipment_write(u32 p,u32 v)override{return write(p,&v,4);}
    bool equipment_allocate(u32 n,u32& p,AnmView& v)override;
    bool equipment_register(u32 e,i32 p,bool d,u32 o,u32& t)override{return callback(e,p,d,o,t);}
    bool read_manager_memory(u32 p,void* v,u32 n)override{return read(p,v,n);}
    bool write_manager_memory(u32 p,const void* v,u32 n)override{return write(p,v,n);}
    bool release_manager_storage(u32 p)override{return services.release_game_storage(p);}
    bool remove_manager_callback(u32)override{return false;}
    bool allocate_manager_storage(u32 n,u32& p)override{return allocate(n,p);}
    bool allocate_scene_history(u32 n,u32& p)override{return allocate(n,p);}
    bool register_manager_callback(u32 e,i32 p,bool d,u32 o,u32& t)override{return callback(e,p,d,o,t);}
};
}
