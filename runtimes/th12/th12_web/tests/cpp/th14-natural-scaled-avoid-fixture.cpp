#include "th14-campaign-replay-fixture.cpp"
#include <algorithm>
#include <cmath>
#include <limits>
// This driver selects ordinary held keys. It never calls combat_tick or writes
// invincibility, lives, power, score, enemy health, timers or completion flags.
static u32 natural_keys=0,natural_frames=0,natural_bombs=0,natural_deaths=0,natural_bomb_requests=0;
static i32 natural_previous_life=0;
static float natural_danger=0;
static bool natural_collection_enabled=false;
static float natural_bomb_clearance=90.f;
API(natural_bomb_margin) void natural_bomb_margin(float margin){natural_bomb_clearance=margin;}
API(natural_config) void natural_config(u32 flags){natural_collection_enabled=(flags&1)!=0;}
API(natural_begin) u32 natural_begin(u32 selection,u32 difficulty){
 natural_keys=natural_frames=natural_bombs=natural_deaths=natural_bomb_requests=0;natural_previous_life=0;natural_danger=0;
 return campaign_begin(selection,difficulty);
}
API(natural_tick) u32 natural_tick(){
 ++natural_frames;u32 held=513;const bool was_bomb=session.battle&&session.battle->bomb&&session.battle->bomb->state.active;
 if(session.battle&&session.battle->player){
  const auto& player=*session.battle->player;const auto& motion=player.motion.state;const Vec3 origin=motion.position;
  const bool protected_now=player.state.invincibility.current>35||was_bomb;
  const bool collecting=natural_collection_enabled&&session.battle->items.active_count>8&&(player.state.invincibility.current>80||session.battle->bullets.active_count<30);
  const float target_y=collecting?96.f:380.f;
  float target_x=0;for(auto* node=session.battle->enemies.first;node;node=node->next){const auto& enemy=node->value->state;if(enemy.boss_slot>=0&&enemy.health>0){target_x=std::clamp(enemy.current.position.x,-150.f,150.f);break;}}
  const auto actual_shape=player.collision();
  const float player_radius=std::max({actual_shape.radius,std::abs(actual_shape.maximum.x-actual_shape.position.x),std::abs(actual_shape.maximum.y-actual_shape.position.y),4.f});
  const u32 directions[]{0,16,32,64,128,16|64,16|128,32|64,32|128};
  float best=-std::numeric_limits<float>::infinity(),best_clearance=0;u32 chosen=0;
  for(bool focused:{true,false}){const float speed=float(focused?motion.focus_speed:motion.normal_speed)/128.f;for(u32 direction:directions){
   float dx=(direction&128?1.f:0.f)-(direction&64?1.f:0.f),dy=(direction&32?1.f:0.f)-(direction&16?1.f:0.f);
   const bool use_focus=focused&&session.battle->enemies.count&&motion.transition_timer>=4;
   const i32 native_speed=dx&&dy?(use_focus?motion.focus_diagonal:motion.normal_diagonal):(use_focus?motion.focus_speed:motion.normal_speed);
   i32 move_x=i32(dx)*native_speed,move_y=i32(dy)*native_speed;
   player_th14_bomb_displacement(move_x,move_y,motion.th14_bomb_shift,motion.th14_movement_factor);
   dx=float(move_x)/128.f;dy=float(move_y)/128.f;
   float clearance=10000;
   if(!protected_now){
   // Controller-only prediction: enemy bodies also threaten ordinary keys.
   for(auto* node=session.battle->enemies.first;node;node=node->next){
    const auto& enemy=node->value->state;
    if((enemy.flags&0x400022u)||enemy.collision_immunity.current>12)continue;
    const float radius=std::max(std::abs(enemy.collision_box.x),std::abs(enemy.collision_box.y))*.5f+player_radius;
    for(int step:{1,4,8,12}){
     const float px=std::clamp(origin.x+dx*step,-180.f,180.f),py=std::clamp(origin.y+dy*step,24.f,424.f);
     const float x=enemy.current.position.x+enemy.current.velocity.x*step-px,y=enemy.current.position.y+enemy.current.velocity.y*step-py;
     clearance=std::min(clearance,x*x+y*y-radius*radius);
    }
   }
   for(auto* bullet=session.battle->bullets.first_th14();bullet;bullet=bullet->th14_active_next){
    if(bullet->state<1||bullet->collision_delay>12)continue;
    if(std::abs(bullet->position.x-origin.x)>180||std::abs(bullet->position.y-origin.y)>180)continue;
    for(int step:{1,4,8,12}){
     const float px=std::clamp(origin.x+dx*step,-180.f,180.f),py=std::clamp(origin.y+dy*step,24.f,424.f);
     const float x=bullet->position.x+bullet->velocity.x*step-px,y=bullet->position.y+bullet->velocity.y*step-py;
     const float radius=std::max(std::abs(bullet->hitbox.x),std::abs(bullet->hitbox.y))+player_radius;
     clearance=std::min(clearance,x*x+y*y-radius*radius);
    }
   }
   for(auto* laser=session.battle->lasers.first();laser;laser=laser->next){
    if(!laser->rectangle_enabled||laser->marked||!std::isfinite(laser->width)||!std::isfinite(laser->angle))continue;
    for(int step:{1,4,8,12}){const float px=std::clamp(origin.x+dx*step,-180.f,180.f),py=std::clamp(origin.y+dy*step,24.f,424.f);float distance=10000;
     if(laser->type==2){const auto& path=reinterpret_cast<const Th14LaserCurve*>(laser)->path.samples;for(u32 i=1;i<path.size();++i){const auto& a=path[i-1].position;const auto& b=path[i].position;const float sx=b.x-a.x,sy=b.y-a.y,squared=sx*sx+sy*sy,t=squared>0?std::clamp(((px-a.x)*sx+(py-a.y)*sy)/squared,0.f,1.f):0;const float x=px-a.x-t*sx,y=py-a.y-t*sy;distance=std::min(distance,x*x+y*y);}}
     else if(laser->type<2){const float x=px-laser->position.x,y=py-laser->position.y,c=std::cos(laser->angle),s=std::sin(laser->angle),along=x*c+y*s,across=-x*s+y*c,outside=along-std::clamp(along,0.f,std::max(laser->length,0.f));distance=outside*outside+across*across;}
     const float radius=laser->width*.5f+player_radius+1.f;clearance=std::min(clearance,distance-radius*radius);
    }
   }
   }
   const float x=std::clamp(origin.x+dx*12,-180.f,180.f),y=std::clamp(origin.y+dy*12,24.f,424.f);
   const float score=std::min(clearance,1600.f)-0.02f*(x-target_x)*(x-target_x)-0.015f*(y-target_y)*(y-target_y);
   if(score>best){best=score;chosen=direction|(focused?8:0);best_clearance=clearance;}
  }}
  held|=chosen;natural_danger=best_clearance;
  const bool active_bomb=session.battle->bomb&&session.battle->bomb->state.active;
  if((player.state.life_state==4||(best_clearance<natural_bomb_clearance&&player.state.invincibility.current<=0))&&!active_bomb&&session.economy.th14_bombs>0&&(session.game_input.held&2)==0){held|=2;++natural_bomb_requests;}
 }
 // Release fire for one frame periodically so dialog confirmation gets a real
 // edge from GameInput, rather than injecting its pressed/repeat fields.
 if(natural_frames%45==0)held&=~1u;
 natural_keys=held;const auto ok=session.update({held});if(session.battle&&session.battle->bomb&&session.battle->bomb->state.active&&!was_bomb)++natural_bombs;if(session.battle&&session.battle->player){const auto life=session.battle->player->state.life_state;if(life!=natural_previous_life&&life==2)++natural_deaths;natural_previous_life=life;}return ok;
}
API(natural_stat) u32 natural_stat(u32 field){
 const u32 values[]{natural_frames,natural_keys,natural_bombs,natural_deaths,float_bits(natural_danger),session.battle&&session.battle->player?u32(session.battle->player->state.invincibility.current):0,session.battle&&session.battle->player?u32(session.battle->player->state.life_state):0,natural_bomb_requests};return values[field];
}
API(natural_save) u32 natural_save(){return session.save_replay("NATURAL",saved_replay,session.state.phase==GameSessionPhase::finished||session.state.phase==GameSessionPhase::ending);}
