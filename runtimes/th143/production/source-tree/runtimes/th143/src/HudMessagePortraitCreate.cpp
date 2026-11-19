#include "HudMessagePortraitCreate.hpp"
namespace th143 {
bool create_hud_message_portrait(AnmView s,u8 op,const u8* p,u32 n,const HudMessagePortraitResources& r,HudMessagePortraitCreateHost& host){
 u32 resource,script,slot,index=0,destination;
 if(op==1){constexpr u32 scripts[]={37,0,46};if(r.player_index>=3)return false;resource=r.player_resource;script=scripts[r.player_index];destination=0x40;}
 else {
  if(op!=2&&op!=20&&op!=31)return false;
  if(op==31)index=1;else{if(!p||n<4)return false;std::memcpy(&index,p,4);if(index>=5)return false;}
  const u32 at=r.scene_descriptor+index*36+(op==20?0x2c:0x34);
  if(!host.portrait_read_word(at,slot)||!host.portrait_read_word(at+4,script)||slot>=128||!host.portrait_read_word(r.enemy_manager+0xa0+slot*4,resource))return false;
  destination=op==20?0x68:0x44+index*4;
 }
 u32 handle;if(!host.portrait_create(resource,signed_word(script),handle))return false;s.put(destination,handle);if(op==2||op==31)s.put(0x1b0,0);return true;
}
}
