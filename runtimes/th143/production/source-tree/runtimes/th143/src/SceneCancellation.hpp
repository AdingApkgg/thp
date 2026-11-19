#pragma once
#include "BulletCancel.hpp"
#include "BulletPool.hpp"
#include "EnemyCancel.hpp"
#include "EnemyDeath.hpp"
#include <vector>
namespace th143 {
struct SceneCancellationServices:EnemyDeathHost,AnmSignalHost {
    // Session ECL services may use a current-actor binding. Bracket death so
    // its optional phase script runs against this actor and restores callers.
    virtual bool begin_cancelled_actor(ActorState&,EclOwner&){return true;}
    virtual bool end_cancelled_actor(){return true;}
};
// Session adapter joining live bullet/item pools and bound enemy script
// owners. Bind actors in intrusive-list order and refresh after list changes;
// bindings retain references owned by the scene, without copying actor state.
class SceneCancellation final:private BulletCancelHost,private EnemyCancelHost {
public:
    struct Actor {u32 token;ActorState* state;EclOwner* script;u32 callback;};
    static constexpr u32 enemy_manager=0x6d000000;
    SceneCancellation(AnmWorld& world,BulletPool& bullets,ItemPool& items,Rng& rng,SceneCancellationServices& services):world(world),bullets(bullets),items(items),rng(rng),services(services){}
    bool bind_actors(const std::vector<Actor>&);
    bool circle(const std::array<float,3>&,float radius,i32 kind,bool include_delayed,u32 special_flags);
    bool single(u32 bullet,i32 kind,u32 special_flags);
    bool item(const std::array<float,3>&,i32 kind,u32 special_flags);
private:
    AnmWorld& world;BulletPool& bullets;ItemPool& items;Rng& rng;SceneCancellationServices& services;
    std::vector<Actor> actors;
    BulletCancelGlobals* active=nullptr;
    Actor* actor(u32 token);
    void publish();void refresh();
    bool cancel_read(u32,void*,u32)override;
    bool cancel_write(u32,const void*,u32)override;
    bool cancel_bullet_view(u32,BulletView&)override;
    bool animation_signal_callback(u32,AnmView,i32)override;
    bool cancel_sound(u32,float)override;
    bool cancel_item(i32,const std::array<float,3>&,float,float)override;
    bool cancel_enemy_circle(const std::array<float,3>&,float,i32)override;
    bool enemy_cancel_read(u32,void*,u32)override;
    bool enemy_cancel_write(u32,const void*,u32)override;
    bool enemy_cancel_death(u32,i32&)override;
};
}
