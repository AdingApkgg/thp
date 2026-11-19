#pragma once
#include "BulletCancel.hpp"
namespace th143 {
struct EnemyCancelHost {
    virtual ~EnemyCancelHost()=default;
    virtual bool enemy_cancel_read(u32,void*,u32)=0;
    virtual bool enemy_cancel_write(u32,const void*,u32)=0;
    //4215f0 receives actor53a8. The session resolves the actual script owner
    // and supplies EnemyDeath; a nonzero result marks the actor retired.
    virtual bool enemy_cancel_death(u32 script_owner,i32& result)=0;
};
//41fe20. Cancels actors marked800;2000000 means already retired and1000
// selects the rotated rectangle. Node next is captured before any callback.
bool cancel_enemy_circle(u32 manager,const std::array<float,3>&,float radius,i32 kind,BulletCancelGlobals&,BulletCancelHost&,EnemyCancelHost&);
}
