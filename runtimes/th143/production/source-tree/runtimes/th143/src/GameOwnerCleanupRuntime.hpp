#pragma once
#include "GameOwnerRuntime.hpp"
#include "AnmResourceWorld.hpp"
#include "SceneCleanup.hpp"
#include "PoolCleanup.hpp"
#include "SupportOwnerCleanup.hpp"
#include "LaserCleanup.hpp"

namespace th143 {
struct GameOwnerCleanupServices {
    virtual ~GameOwnerCleanupServices()=default;
    virtual bool release_owner_storage(u32 token,bool array)=0;
    virtual bool destroy_equipment_option(AnmView owner,u32 offset)=0;
    virtual bool destroy_owned_laser(u32 token)=0;
};
// Cleanup uses the same owner arrays and Scheduler as gameplay. Released
// arrays remain readable for diagnostics; created bits record live ownership.
// Option and beam virtual destructors are explicit session services.
class GameOwnerCleanupRuntime final:private SchedulerHost,private SceneCleanupHost,
    private PoolCleanupHost,private SupportOwnerCleanupHost,private GameManagerMemory,
    private LaserCleanupMemory {
public:
    GameOwnerCleanupRuntime(GameOwnerRuntime& o,GameFrameRuntime& f,AnmResourceWorld& a,GameOwnerCleanupServices& s):owners(o),frames(f),animations(a),services(s){}
    bool recording(u32& owner);
    bool player(u32 flags,u32& owner,u32& saved_shots);
    bool equipment(u32& owner);
    bool bullets(u32& owner);
    bool items(u32& owner);
    bool lasers(u32& owner);
    bool scores(u32& owner);
    bool read_retained(u32,void*,u32);
private:
    GameOwnerRuntime& owners;GameFrameRuntime& frames;AnmResourceWorld& animations;GameOwnerCleanupServices& services;
    bool write_retained(u32,const void*,u32);
    bool remove(u32 p){return !p||frames.scheduler.remove(p,*this);}
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 p)override{return services.release_owner_storage(p,false);}
    bool remove_callback(u32 p)override{return remove(p);}
    bool deactivate_callback(u32 p)override;
    bool release_storage(u32 p,bool a)override{return services.release_owner_storage(p,a);}
    bool destroy_scene_choice(u32)override{return false;}
    bool destroy_message(u32)override{return false;}
    bool unload_message_resource()override{return false;}
    bool remove_pool_callback(u32 p)override{return remove(p);}
    bool release_pool_array(u32 p)override{return services.release_owner_storage(p,true);}
    bool remove_support_callback(u32 p)override{return remove(p);}
    bool destroy_support_option(AnmView v,u32 at)override{return services.destroy_equipment_option(v,at);}
    bool release_support_option(u32 p)override{return services.release_owner_storage(p,true);}
    bool read_manager_memory(u32 p,void* b,u32 n)override{return read_retained(p,b,n);}
    bool write_manager_memory(u32 p,const void* b,u32 n)override{return write_retained(p,b,n);}
    bool release_manager_storage(u32 p)override{return services.release_owner_storage(p,false);}
    bool remove_manager_callback(u32 p)override{return remove(p);}
    bool read_enemy_memory(u32 p,void* b,u32 n)override{return read_retained(p,b,n)||animations.read(p,b,n);}
    bool write_enemy_memory(u32 p,const void* b,u32 n)override{return write_retained(p,b,n)||animations.write(p,b,n);}
    bool release_enemy_storage(u32 p,bool a)override{return services.release_owner_storage(p,a);}
    bool find_enemy_visual(u32 h,u32& p)override{return animations.find_enemy_visual(h,p);}
    bool remove_laser_callback(u32 p)override{return remove(p);}
    bool destroy_laser(u32 p)override{return services.destroy_owned_laser(p);}
};
}
