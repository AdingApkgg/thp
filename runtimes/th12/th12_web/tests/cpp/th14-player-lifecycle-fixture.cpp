#include "../../cpp/game/GameSessionResources.hpp"
#include "../../cpp/game/PlayerFrame.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameResources source;
static GameSessionResources resources;
static AnmManager animations;
static GameEconomy economy;
static std::unique_ptr<PlayerFrame> player;
struct World:PlayerFrameWorld {
    std::vector<std::vector<u32>> events;i32 deaths=7,combo=9;
    bool player_sound(i32 id)override{events.push_back({1,u32(id)});return true;}
    bool player_effect(Vec3 p,i32 script)override{events.push_back({0,u32(script),float_bits(p.x),float_bits(p.y),float_bits(p.z)});return animations.create(resources.core.effect,script,8,0,false,false,&p)!=nullptr;}
    bool display_lives(i32 a,i32 b)override{events.push_back({2,u32(a),u32(b)});return true;}
    bool bombs_changed(i32 a,i32 b)override{events.push_back({3,u32(a),u32(b)});return true;}
    bool enemy_death()override{++deaths;combo=0;return true;}
    bool start_bomb()override{combo=0;return true;}
    bool attract_items()override{return true;}
    bool cancel_bullets(const Vec3* p,float r,bool skip)override{if(!p)return false;events.push_back({5,float_bits(p->x),float_bits(p->y),float_bits(p->z),float_bits(r),u32(skip)});return true;}
    bool cancel_lasers(const Vec3* p,float r,bool reward,bool skip)override{events.push_back({6,u32(p!=nullptr),p?float_bits(p->x):0,p?float_bits(p->y):0,p?float_bits(p->z):0,float_bits(r),u32(reward),u32(skip)});return true;}
    bool game_over(bool replay)override{events.push_back({7,u32(replay)});return true;}
} world;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open_archive) i32 open_archive(const u8* p,u32 n){return source.open_archive(p,n)&&resources.load_core(source);}
API(run) i32 run(i32 kind,i32 lives,i32 bombs,i32 fragments,i32 power,i32 frame,u32 pressed,i32 available,i32 active,u32 flags,i32 elapsed,u32 scale_flags,u32 rate){
    player.reset();animations.clear();animations.fallback_sprites=&resources.core.ascii;economy={};animations.rate=float_bits(rate);
    auto& core=resources.core;player=std::make_unique<PlayerFrame>(core.shots[0],core.players[0],core.bullet,animations,economy,world,7,6);
    if(!player->initialize())return 0;
    economy.lives=lives;economy.life_fragments=fragments;economy.th14_bombs=bombs;economy.th14_bomb_fragments=fragments;economy.power=power;economy.point_value=5000000;economy.rank=1000;
    auto& p=*player;p.state.life_state=kind==4?4:kind==3?3:kind==2?2:kind==0?0:1;p.state.state_timer.set(frame,&animations.rate);p.state.invincibility.set(20,&animations.rate);
    p.motion.state.position={12.25,400,3};p.motion.state.x=1568;p.motion.state.y=51200;p.state.death_position={-25.5,375.25,-2};p.motion.state.option_count=4;
    p.spell={flags,elapsed,12345};p.th14_scale.flags=scale_flags;p.input.movement.held=2;p.input.movement.pressed=pressed;p.input.special_available=available;p.input.special_active=active;
    world.events.clear();world.deaths=7;world.combo=9;
    return kind==5?p.hit():kind==6?p.die():p.update();
}
API(value) u32 value(u32 n){
    auto& p=*player;auto& s=p.state;auto& m=p.motion.state;
    const u32 v[]={u32(s.life_state),u32(s.state_timer.current),u32(s.invincibility.current),u32(m.x),u32(m.y),float_bits(m.position.x),float_bits(m.position.y),float_bits(m.position.z),float_bits(s.death_position.x),float_bits(s.death_position.y),float_bits(s.death_position.z),u32(economy.lives),u32(economy.th14_bombs),u32(economy.th14_bomb_fragments),u32(economy.power),p.spell.flags,u32(p.spell.bonus),u32(world.deaths),u32(world.combo),float_bits(animations.rate),u32(economy.point_value),u32(economy.rank)};
    return v[n];
}
API(event_count) u32 event_count(){return world.events.size();}
API(event_size) u32 event_size(u32 n){return world.events.at(n).size();}
API(event_value) u32 event_value(u32 n,u32 j){return world.events.at(n).at(j);}
API(error) i32 error(){return player->last_error?player->last_error:animations.last_error;}
