#include "HudMessageText.hpp"
#include "HudMessageTextDecode.hpp"
namespace th143 {
bool execute_hud_message_text(AnmView s,const u8* encoded,u32 bytes,HudMessageTextHost& h){
 auto resolve=[&](u32 at){u32 handle=s.get(at);auto v=h.message_text_resolve(handle);s.put(at,handle);return v;};
 auto draw=[&](u32 at,u32 color,i32 font,i32 x,i32 pitch,const u8* text,u32 n){auto v=resolve(at);return v.data&&h.message_text_draw(v,color,0,font,x,pitch,text,n);};
 auto position=[&](u32 at){u32 handle=s.get(at);const bool ok=h.message_text_position(handle,{s.floating(0x1a0),s.floating(0x1a4),s.floating(0x1a8)});s.put(at,handle);return ok;};
 const bool second=s.get(0x188)!=0;u32 side=s.get(0x190);if(side>=3)return false;
 if(!second&&!s.get(0x18c)){
  s.put(0x1ac,0);
  constexpr u8 blank[]={' ',' '};for(u32 at:{0x58u,0x5cu,0x60u,0x64u})if(!draw(at,s.get(0x194+side*4),(s.get(0x184)>>1)&1,0,at>=0x60?1:0,blank,2))return false;
  s.put(0x18c,1);for(u32 at:{0x58u,0x5cu,0x60u,0x64u})if(!h.message_text_signal(s.get(at),3,false))return false;
 }
 std::array<u8,256> decoded;u32 written;if(!decode_hud_message_text(encoded,bytes,decoded.data(),decoded.size(),written))return false;const u32 n=written-1;
 if(n&&decoded[0]=='|'){
  u32 cursor=1;auto integer=[&](i32& value){while(cursor<n&&(decoded[cursor]==' '||decoded[cursor]=='\t'))++cursor;bool negative=false;if(cursor<n&&(decoded[cursor]=='-'||decoded[cursor]=='+'))negative=decoded[cursor++]=='-';u32 v=0;while(cursor<n&&decoded[cursor]>='0'&&decoded[cursor]<='9')v=v*10+decoded[cursor++]-'0';value=signed_word(negative?0-v:v);};
  i32 x,pitch;integer(x);while(cursor<n&&decoded[cursor]!=',')++cursor;if(cursor==n)return false;++cursor;integer(pitch);while(cursor<n&&decoded[cursor]!=',')++cursor;if(cursor==n)return false;++cursor;
  const u32 at=second?0x64:0x60;auto v=resolve(at);if(!v.data)return false;v.put(0x1c,v.get(0x1c)|0x800);
  if(!draw(at,0x303030,2,x,pitch,decoded.data()+cursor,n-cursor)||!position(at)||!h.message_text_signal(s.get(at),2,!second))return false;return true;
 }
 const u32 raw_width=((n*8)&~15u)-28u;const float candidate=float(raw_width)*2.f;const float width=candidate>s.floating(0x1ac)?candidate:s.floating(0x1ac);s.put(0x1ac,word(width));
 const i32 index=signed_word(side+((s.get(0x184)>>2)&15)*2+(second?8:0));
 if(!h.message_text_window(s,index,s.floating(0x1a0),s.floating(0x1a4),width)||!h.message_text_width(s,index,s.floating(0x1ac)))return false;
 const u32 at=second?0x5c:0x58;auto v=resolve(at);if(!v.data)return false;v.put(0x1c,v.get(0x1c)|0x800);
 side=s.get(0x190);if(side>=3||!draw(at,s.get(0x194+side*4),(s.get(0x184)>>1)&1,0,0,decoded.data(),n))return false;
 if(signed_word(side)>=1){for(u32 slot:{0x58u,0x60u,0x5cu,0x64u})if(!position(slot))return false;}else if(!position(at))return false;
 if(!h.message_text_signal(s.get(at),2,true))return false;
 if(second){s.put(0x188,0);s.put(0x18c,0);}else s.put(0x188,s.get(0x188)+1);return true;
}
}
