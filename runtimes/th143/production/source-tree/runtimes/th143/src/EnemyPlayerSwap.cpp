#include "EnemyPlayerSwap.hpp"
namespace th143 {
namespace {u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000u;}}
bool swap_enemy_player(AnmView enemy,PlayerState& player,AnmView shadow,SoundQueue& audio,EnemyPlayerSwapHost& host,i32& result){
 if(!enemy.data)return false;
 const std::array<float,3> origin{enemy.floating(0x44),enemy.floating(0x48),enemy.floating(0x4c)};
 const bool cloaked=(player.get(0x1847c)&0x100u)!=0;const u32 at=cloaked?0x184b4u:0x5e0u;
 const std::array<float,3> previous{player.floating(at),player.floating(at+4),player.floating(at+8)};
 if(cloaked){if(!shadow.data)return false;for(u32 i=0;i<3;++i)shadow.put(0x3c+i*4,word(origin[i]));}
 else{
  for(u32 i=0;i<2;++i){const u32 fixed=truncate(origin[i]*128.f);player.put(0x5ec+i*4,fixed);player.put(0x5e0+i*4,word(float(signed_word(fixed))*real(0x3c000000)));}
  for(u32 i=0;i<8;++i)player.put(0xd7c0+i*0xe4,1);
 }
 for(u32 i=0;i<3;++i)enemy.put(0x88+i*4,word(previous[i]));
 if(!host.enemy_swap_sound(85,origin[0]))return false;
 auto queue=audio.view();for(u32 i=0;i<12;++i){const i32 id=signed_word(queue.get(i*4));if(id<0){queue.put(i*4,84);queue.put(0x30+i*4,0xffffffffu);break;}if(id==84){queue.put(0x30+i*4,0xffffffffu);break;}}
 const u32 resource=player.get(0x10);if(!host.enemy_swap_visual(resource,14,previous)||!host.enemy_swap_visual(resource,15,origin))return false;
 result=0;return true;
}
}
