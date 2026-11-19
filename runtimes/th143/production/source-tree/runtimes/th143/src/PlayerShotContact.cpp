#include "PlayerShotContact.hpp"
#include "ShotGeometry.hpp"
#include "ShotRectangleGeometry.hpp"
namespace th143 {
namespace {
bool overlap(PlayerState& p,u32 at,const PlayerShotImpactQuery& q){
    const float x=p.floating(at+0x2c),y=p.floating(at+0x30);
    if(p.get(at+0x10)&2){
        if(q.rectangle)return shot_rectangle_circle(q.position[0],q.position[1],q.size[0],q.size[1],q.angle,x,y,p.floating(at+0x14));
        const float dx=x-q.position[0],dy=y-q.position[1],radius=p.floating(at+0x14)+q.radius;
        return !(dx*dx+dy*dy>radius*radius);
    }
    if(q.rectangle)return shot_rectangle_rectangle(x,y,p.floating(at+0x24),p.floating(at+0x28),p.floating(at+0x1c),q.position[0],q.position[1],q.size[0],q.size[1],q.angle);
    return shot_rectangle_circle(x,y,p.floating(at+0x24),p.floating(at+0x28),p.floating(at+0x1c),q.position[0],q.position[1],q.radius);
}
}
bool contact_player_shots(PlayerState& p,PlayerShotData& sht,const PlayerShootingConfig& config,PlayerShotContactGlobals& g,const PlayerShotImpactQuery& q,const PlayerShotContactOptions& options,PlayerShotContactHost& host,PlayerShotContactResult& out){
    out.damage=0;if(p.get(0x690)==p.get(0x68c))return true;
    i32 extra=0;if(g.cheat_active&&!host.cheat_damage(q,extra))return false;u32 damage=u32(extra);
    if(options.hit_flag)out.hit_flag=extra>0?1:0;
    for(u32 i=0;i<256;++i){const u32 at=0xde18+i*0xa4;if(!(p.get(at+0x10)&1))continue;
        const i32 current=signed_word(p.get(at+0x74)),period=signed_word(p.get(at+0x90));bool due=false;
        if(p.get(at+0x74)!=p.get(at+0x70)){
            if(!period||(current==i32(0x80000000u)&&period==-1))return false;
            due=current%period==0;
        }
        if(!due&&period>1)continue;if(!overlap(p,at,q))continue;
        if(q.id){if(p.get(at+0x94)==q.id)continue;p.put(at+0x94,q.id);}
        if(options.hit_flag&&(p.get(at+0x10)&4))out.hit_flag=1;
        i32 value=signed_word(p.get(at+0x84));if(const u32 callback=p.get(at+0xa0)){
            p.put(at+0x9c,q.owner);
            if(callback==0x4518e0){if(!impact_player_shot(p,sht,at,config,q,host,value))return false;}
            else if(!host.area_callback(callback,p,at,q,value))return false;
        }
        p.put(at+0x88,p.get(at+0x88)+p.get(at+0x84));damage+=u32(value);
        if(options.last_position)for(u32 j=0;j<3;++j)out.last_position[j]=p.floating(at+0x2c+j*4);
        const i32 limit=signed_word(p.get(at+0x8c));if(limit<9999999&&limit<=signed_word(p.get(at+0x88))){p.put(at+0x10,p.get(at+0x10)&~1u);p.put(at+0x84,0);}
    }
    if(sht.data.size()<0x2c)return false;const i32 cap=signed_word(sht.get(0x28));if(signed_word(damage)>cap)damage=u32(cap);
    out.damage=signed_word(damage);if(damage){const i32 increment=(signed_word(damage)/10+10)/10;const u32 score=g.score+u32(increment);g.score=score>=1000000000?999999999:score;}return true;
}
}
