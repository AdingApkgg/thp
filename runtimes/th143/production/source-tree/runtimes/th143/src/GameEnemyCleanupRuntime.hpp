#pragma once
#include "GameEnemyStartup.hpp"
namespace th143 {
struct GameEnemyCleanupServices {
    virtual ~GameEnemyCleanupServices()=default;
    // Identities belong to the session's declared script allocator, established
    // when EclOwner creates the secondary VM and its list node.
    virtual bool enemy_thread_identity(const Vm&,u32& vm,u32& node)=0;
    virtual bool release_enemy_cleanup_storage(u32,bool array)=0;
    virtual bool read_enemy_cleanup_memory(u32,void*,u32)=0;
    virtual bool write_enemy_cleanup_memory(u32,const void*,u32)=0;
    virtual u8 enemy_cleanup_allocation_fill()const{return 0;}
};
// Live actor reset for retained EnemyManager/ECL resources during a retry.
// Old typed actors and guest ownership links remain available after release.
class GameEnemyCleanupRuntime final:private EnemyCleanupMemory {
public:
    GameEnemyCleanupRuntime(GameEnemyRuntime& o,EnemyScripts& s,AnmResourceWorld& a,Scheduler& q,GameEnemyCleanupServices& h):owner(o),scripts(s),animations(a),scheduler(q),services(h){}
    bool reset();
    bool read_retained(u32,void*,u32);
    std::vector<std::unique_ptr<EnemyScripts::Actor>> retired;
private:
    struct Header {EnemyScripts::Actor* actor;u32 vtable;std::array<u32,4> links;};
    struct Node {u32 token;std::array<u32,4> data;};
    GameEnemyRuntime& owner;EnemyScripts& scripts;AnmResourceWorld& animations;Scheduler& scheduler;GameEnemyCleanupServices& services;
    std::vector<Header> headers;std::vector<Node> nodes;
    bool map(u32,void*,u32,bool write);
    bool read_enemy_memory(u32 p,void* b,u32 n)override{return read_retained(p,b,n);}
    bool write_enemy_memory(u32 p,const void* b,u32 n)override;
    bool release_enemy_storage(u32 p,bool a)override{return services.release_enemy_cleanup_storage(p,a);}
    bool find_enemy_visual(u32 h,u32& p)override{return animations.find_enemy_visual(h,p);}
};
}
