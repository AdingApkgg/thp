#include "ReplaySaveDraw.hpp"
namespace th143 {
bool draw_replay_save(AnmView menu,AnmView ascii,u32 current,ReplaySaveDrawHost& host){
 ascii.put(0x191c8,0);const u32 selected=menu.get(0x38);const i32 elapsed=signed_word(menu.get(0x14));float y=224.f;
 if(elapsed<10){const float row=float(signed_word(selected))*15.f+64.f;const float delta=(224.f-row)*float(elapsed);y=delta/10.f+row;}
 if(!host.replay_name_cursor(menu,{198.f,y,0.f}))return false;
 u32 header,day,within;std::array<i32,9> time;
 if(!host.replay_draw_read(current+0x1c,header)||!host.replay_draw_localtime(header+0x14,time)||!host.replay_draw_read(header+0x88,day)||!host.replay_draw_read(header+0x8c,within))return false;
 return host.replay_draw_line({144.f,y,0.f},0x4c6808,{selected+1,u32(time[5]%100),u32(time[4])+1,u32(time[3]),u32(time[2]),u32(time[1]),day+1,within+1});
}
}
