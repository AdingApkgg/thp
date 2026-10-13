#include "th14-natural-input-fixture.cpp"
#include <algorithm>
#include <cmath>
// Read-only telemetry for replaying archived ordinary keys. No game writes.
API(failure_state) const u32* failure_state(){
 static u32 words[32];std::fill(words,words+32,0);
 words[0]=session.state.stage;words[1]=session.state.frame;
 if(!session.battle||!session.battle->player)return words;
 const auto& b=*session.battle;const auto& p=*b.player;const auto pos=p.motion.state.position;
 words[2]=b.frame;words[3]=p.state.life_state;words[4]=p.state.state_timer.current;
 words[5]=p.state.invincibility.current;words[6]=float_bits(pos.x);words[7]=float_bits(pos.y);
 words[8]=session.economy.lives;words[9]=session.economy.th14_bombs;
 words[10]=b.bomb&&b.bomb->state.active;words[11]=b.spell_flags;
 for(auto* node=b.enemies.first;node;node=node->next){const auto& e=node->value->state;
  if(e.boss_slot>=0&&e.health>0){words[12]=e.health;words[13]=e.max_health;words[14]=e.lifetime.current;words[15]=e.flags;
   words[24]=e.timer_2bc.current;words[25]=e.interrupts[0].health;words[26]=e.interrupts[0].time;words[27]=e.damage_immunity.current;break;}}
 float best=1e20f;u32 closest_state=0,closest_flags=0;float closest_size=0,closest_x=0,closest_y=0;
 for(auto* bullet=b.bullets.first_th14();bullet;bullet=bullet->th14_active_next){
  if((bullet->state!=1&&bullet->state!=2)||!(bullet->flags&2)||bullet->collision_delay)continue;
  const float x=bullet->position.x-pos.x,y=bullet->position.y-pos.y;
  const float r=bullet->hitbox.x*bullet->th14_size;
  const float distance=x*x+y*y-r*r-p.collision().radius*p.collision().radius;
  if(distance<best){best=distance;closest_state=bullet->state;closest_flags=bullet->flags;closest_size=bullet->th14_size;closest_x=x;closest_y=y;}
 }
 words[16]=float_bits(best);words[17]=closest_state;words[18]=closest_flags;words[19]=float_bits(closest_size);
 words[20]=float_bits(closest_x);words[21]=float_bits(closest_y);words[22]=b.bullets.active_count;
 words[23]=p.state.transition_timer.current;words[28]=p.th14_scale.flags;words[29]=float_bits(p.th14_scale.factor);
 words[30]=float_bits(p.collision().radius);words[31]=b.spells.frame_count;return words;
}
