#include "ReplayListDraw.hpp"
namespace th143 {
bool draw_replay_list(AnmView menu,AnmView ascii,ReplayListDrawHost& host){
 std::array<float,3> p={144.f,64.f,0.f};
 for(u32 i=0;i<25;++i){
  ascii.put(0x191c8,0);ascii.put(0x191b0,menu.get(0x38)==i?0xffffff00:0xff808080);
  const u32 object=menu.get(0x204+i*4);
  if(object){u32 header,day,within;std::array<i32,9> time;
   if(!host.replay_draw_read(object+0x1c,header)||!host.replay_draw_localtime(header+0x14,time)||!host.replay_draw_read(header+0x88,day)||!host.replay_draw_read(header+0x8c,within))return false;
   if(!host.replay_draw_line(p,0x4c67b0,{i+1,header,u32(time[5]%100),u32(time[4])+1,u32(time[3]),u32(time[2]),u32(time[1]),day+1,within+1}))return false;
  }else if(!host.replay_draw_line(p,0x4c67dc,{i+1}))return false;
  p[1]+=15.f;
 }
 ascii.put(0x191b0,0xffffffff);return true;
}
}
