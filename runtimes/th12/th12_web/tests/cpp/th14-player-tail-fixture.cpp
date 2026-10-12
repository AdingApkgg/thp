#include "../../cpp/game/GameSessionResources.hpp"
#include "../../cpp/game/PlayerFrame.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameResources source;static GameSessionResources resources;
static AnmManager animations;static GameEconomy economy;
struct World:PlayerFrameWorld {i32 lives=0,fragments=0;
    bool display_lives(i32 a,i32 b)override{lives=a;fragments=b;return true;}
} world;
static std::unique_ptr<PlayerFrame> player;static std::vector<u32> values;
static void timer(const Timer& t){values.insert(values.end(),{u32(t.previous),u32(t.current),float_bits(t.fractional)});}
static void vec(Vec3 p){values.insert(values.end(),{float_bits(p.x),float_bits(p.y),float_bits(p.z)});}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open_archive) i32 open_archive(const u8* p,u32 n){return source.open_archive(p,n)&&resources.load_core(source);}
static bool begin(i32 selection){
    player.reset();animations.clear();economy={};animations.rate=1;animations.fallback_sprites=&resources.core.ascii;values.clear();
    player=std::make_unique<PlayerFrame>(resources.core.shots[selection],resources.core.players[selection/2],resources.core.bullet,animations,economy,world,7,6);
    player->input.movement.character=selection/2;player->input.movement.subtype=selection%2;return player->initialize();
}
API(parameters) i32 parameters(i32 selection){
    if(!begin(selection))return 0;auto& s=player->state;const auto& h=resources.core.shots[selection].header;
    values={float_bits(h.hitbox),float_bits(h.attraction_diameter),float_bits(h.attraction_speed)};
    vec(s.hit_half);vec(s.pickup_size);vec(s.focused_half);
    for(const auto& b:{s.hit,s.pickup,s.focused_attract,s.unfocused_attract}){vec(b.minimum);vec(b.maximum);}return 1;
}
API(stage) i32 stage(u32 flags,i32 x,i32 y,i32 fragments){
    if(!begin(0))return 0;auto& p=*player;auto& s=p.state;auto& m=p.motion.state;
    for(auto* t:{&s.state_timer,&s.transition_timer,&s.th14_shooting_age,&p.shots.schedule.timer})t->set(73,&animations.rate);
    p.th14_scale.flags=flags;p.th14_scale.interpolation.duration=37;p.th14_scale.factor=3;
    m.x=x;m.y=y;economy.lives=2;economy.life_fragments=fragments;
    auto& shot=p.shots.player;shot.th14_cached_power=shot.th14_attached_count=37;
    shot.th14_focused_hits=shot.th14_plain_hits=shot.th14_hits_184bc=37;
    if(!p.start_stage())return 0;
    values={u32(s.life_state)};for(const auto* t:{&s.state_timer,&s.transition_timer,&s.th14_shooting_age,&p.shots.schedule.timer})timer(*t);
    for(const auto& point:m.th14_history)values.insert(values.end(),{u32(point[0]),u32(point[1])});
    values.insert(values.end(),{p.th14_scale.flags,u32(shot.th14_cached_power),u32(shot.th14_attached_count),0,0,shot.th14_plain_hits,shot.th14_focused_hits,shot.th14_hits_184bc,u32(p.th14_scale.interpolation.duration),float_bits(p.th14_scale.factor)});
    return 1;
}
API(lives) i32 lives(){return world.lives;}
API(fragments) i32 fragments(){return world.fragments;}
static bool fired=false;
API(tail) i32 tail(i32 env,u32 flags,i32 age,u32 rate,i32 life,i32 schedule,i32 warp){
    values.clear();animations.rate=float_bits(rate);PlayerFrameState state;PlayerFrameInput input;
    state.state_timer.set(59,&animations.rate);state.transition_timer.set(7,&animations.rate);state.th14_shooting_age.set(age,&animations.rate);
    input.movement.bomb=env==1;input.movement.enemy_manager=env!=2;input.movement.enemies=env!=3;input.shooting_blocked=env==4;
    ShtResource sht;sht.header.max_power_level=4;sht.groups.resize(10);AnmResource anm;ShotManager shots(sht,anm,animations,world);
    shots.schedule.timer.set(schedule,&animations.rate);shots.locked_target=reinterpret_cast<Enemy*>(0x1234);shots.target_locked=1;
    shots.player.state=life;shots.player.held=1;shots.player.power=400;shots.player.power_step=100;shots.player.warp_state=warp;
    fired=player_th14_tick_clocks(state,input,flags);
    if(fired){if(!shots.fire())return 0;}else{shots.schedule.timer.set(-1,&animations.rate);shots.locked_target=nullptr;shots.target_locked=0;}
    for(const auto* t:{&state.state_timer,&state.transition_timer,&state.th14_shooting_age,&shots.schedule.timer})timer(*t);
    values.insert(values.end(),{u32(reinterpret_cast<uintptr_t>(shots.locked_target)),u32(shots.target_locked),1000});return 1;
}
API(fire) i32 fire(){return fired;}
API(blink) i32 blink(i32 invincible,i32 frame,i32 previous,i32 mode,u32 rate){
    values.clear();animations.rate=float_bits(rate);PlayerFrameState state;AnmVm body;
    state.state_timer.set(frame,&animations.rate);if(previous)state.state_timer.previous=frame;
    state.invincibility.set(invincible,&animations.rate);body.th13_native_flags=(0x12345678&~0x60000u)|(u32(mode)<<17);body.secondary_color=0x87654321;
    player_th14_blink(body,state);if(state.invincibility.current>0)state.invincibility.advance(-1);
    values={body.th13_native_flags,body.secondary_color};timer(state.invincibility);return 1;
}
API(value) u32 value(u32 n){return values.at(n);}
API(size) u32 size(){return values.size();}
