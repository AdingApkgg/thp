#include "../../cpp/game/BombController.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {
ShtResource sht;AnmResource anm;AnmManager animations;GameEconomy economy;
struct World:PlayerFrameWorld,BombWorld {
    BombController* bomb=nullptr;i32 calls=0;bool refuse=false;
    bool special_damage(const Vec3& p,const Vec2& s,i32& out)override{++calls;return !refuse&&bomb->damage(p,s,out);}
    bool bomb_sound(i32,float,bool)override{return true;}
    bool bomb_stop_sound(i32)override{return true;}
    bool bomb_cancel(Vec3,float,u32,bool)override{return true;}
    i32 count=0;i32& bomb_count()override{return count;}
    bool bomb_background_color(u32)override{return true;}
    bool bomb_refund_power()override{return true;}
    bool bomb_cancel_beam(Vec3,bool)override{return true;}
} world;
PlayerFrame player(sht,anm,anm,animations,economy,world);
BombController bomb(animations,anm,player,world,7,&anm);
i32 damage=0,score=0,calls=0;
}
API(direct) i32 direct(i32 selection){bomb.selection=selection;bomb.state.active=1;i32 value=1234;return bomb.damage({1,2,3},{16,16},value)?value:-999;}
API(run) i32 run(i32 selection,i32 active,i32 advanced,i32 occupied){
    economy={};sht.header.native_extra[0]=220;world.bomb=&bomb;world.calls=0;world.refuse=false;
    bomb.selection=selection;bomb.state.active=active;
    ShotManager shots(sht,anm,animations,world);shots.player.special_active=active;
    if(occupied){if(!shots.th14_death_area({0,0,0}))return 0;shots.update_th14_areas();}
    const Vec2 size{16,16};const bool ok=shots.damage_th14({0,0,0},&size,0,0,advanced,economy,damage);
    score=economy.score_units;calls=world.calls;return ok;
}
API(value) i32 value(i32 n){return n==0?damage:n==1?score:calls;}
API(circle) i32 circle(float radius,float x,i32 ticked,i32 advanced,float rate){
    economy={};sht.header.native_extra[0]=220;world.bomb=&bomb;world.calls=0;world.refuse=false;animations.rate=rate;
    bomb.selection=3;bomb.state.active=1;ShotManager shots(sht,anm,animations,world);shots.player.special_active=1;
    if(!shots.th14_bomb_circle({0,0,0},radius,0,0,90))return 0;
    if(ticked)shots.update_th14_areas();const Vec2 size{16,16};
    const bool ok=shots.damage_th14({x,0,0},&size,0,0,advanced,economy,damage);score=economy.score_units;calls=world.calls;return ok;
}
API(refusal) i32 refusal(){world.refuse=true;ShotManager shots(sht,anm,animations,world);shots.player.special_active=1;i32 out=99;Vec2 size{16,16};return !shots.damage_th14({0,0,0},&size,0,0,true,economy,out)&&shots.last_error==13;}
