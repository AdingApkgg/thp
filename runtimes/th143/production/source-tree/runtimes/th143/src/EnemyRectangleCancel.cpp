#include "EnemyRectangleCancel.hpp"
#include "ShotRectangleGeometry.hpp"
#include "ShotGeometry.hpp"
namespace th143 {
bool cancel_enemy_rectangle(u32 manager,const std::array<float,3>& p,const std::array<float,3>& size,float angle,i32 kind,BulletCancelGlobals& g,BulletCancelHost& services,EnemyCancelHost& host){
    auto read=[&](u32 at,u32& value){return host.enemy_cancel_read(at,&value,4);};
    auto write=[&](u32 at,u32 value){return host.enemy_cancel_write(at,&value,4);};
    auto floating=[&](u32 at,float& value){return host.enemy_cancel_read(at,&value,4);};
    u32 node;if(!read(manager+0xd0,node))return false;u32 budget=100000;
    while(node){
        if(!budget--)return false;u32 actor,next,flags;
        if(!read(node+4,next)||!read(node,actor)||!read(actor+0x52f0,flags))return false;
        if(!(flags&0x2000000)&&(flags&0x800)){
            std::array<float,3> center;if(!host.enemy_cancel_read(actor+0x1234,center.data(),12))return false;
            float width;if(!floating(actor+0x1308,width))return false;bool contact;
            if(flags&0x1000){
                float height,actor_angle;if(!floating(actor+0x130c,height)||!floating(actor+0x1310,actor_angle))return false;
                contact=shot_rectangle_rectangle(center[0],center[1],width,height,actor_angle,p[0],p[1],size[0],size[1],angle);
            }else contact=shot_rectangle_circle(p[0],p[1],size[1],size[0],angle,center[0],center[1],width);
            if(contact){
                if(!services.cancel_sound(71,center[0])||!bullet_cancel_item(center,kind,g,services))return false;
                u32 script;if(!read(actor+0x53a8,script)||!host.enemy_cancel_write(actor+0x1510,center.data(),12))return false;
                i32 result;if(!host.enemy_cancel_death(script,result))return false;
                if(result){if(!read(actor+0x52f0,flags)||!write(actor+0x52f0,flags|0x2000000))return false;}
            }
        }node=next;
    }return true;
}
}
