#pragma once
#include "BulletMotion.hpp"
#include "AnmSignal.hpp"
namespace th143 {
struct BulletCancelGlobals {
    u32 cancelled=0,item_counter=0,special_flags=0;
    Rng gameplay_rng;
};
struct BulletCancelHost:AnmSignalHost {
    virtual bool cancel_read(u32,void*,u32)=0;
    virtual bool cancel_write(u32,const void*,u32)=0;
    virtual bool cancel_bullet_view(u32, BulletView&)=0;
    virtual bool cancel_sound(u32 id,float x)=0;
    virtual bool cancel_item(i32 type,const std::array<float,3>&,float angle,float speed)=0;
    virtual bool cancel_enemy_circle(const std::array<float,3>&,float radius,i32 kind)=0;
};
bool bullet_cancel_item(const std::array<float,3>&,i32 kind,BulletCancelGlobals&,BulletCancelHost&); //4172e0
bool cancel_bullet(BulletView,i32 kind,u32 resource,const float& elapsed,BulletCancelGlobals&,AnmWorld&,BulletCancelHost&); //4170a0
//417440 includes delayed bullets;417540 excludes +24!=0. Traversal cursors
//live at manager9bf6c0/c4 and are reread after callbacks, as in the original.
bool cancel_bullets_circle(u32 manager,const std::array<float,3>&,float radius,i32 kind,bool include_delayed,const float& elapsed,BulletCancelGlobals&,AnmWorld&,BulletCancelHost&);
}
