#include "HudMessageWindow.hpp"
namespace th143 {
bool retire_hud_message_window(AnmView s,HudMessageWindowHost& h){
 auto v=h.message_window_visual(s.get(0x6c));
 if(v.data){v.put(0x1c,v.get(0x1c)|0x20);if(!v.get(0x588)){u32 node=v.get(0x584),budget=0;while(node){u32 token,next;if(++budget>100000||!h.message_window_read(node,token)||!h.message_window_read(node+4,next))return false;auto child=h.message_window_state(token);if(!child.data)return false;child.put(0x1c,child.get(0x1c)|0x20);node=next;}}}
 s.put(0x6c,0);return true;
}
namespace {
AnmView child(AnmView s,i32 id,HudMessageWindowHost& h){auto v=h.message_window_visual(s.get(0x6c));if(!v.data){s.put(0x6c,0);return{};}v=h.message_window_visual(s.get(0x6c));if(!v.data){s.put(0x6c,0);return{};}return h.message_window_child(v,id);}
}
bool create_hud_message_window(AnmView s,u32 resource,i32 index,float x,float y,float width,HudMessageWindowHost& h){
 if(!retire_hud_message_window(s,h))return false;u32 handle;if(!h.message_window_create(resource,signed_word(u32(index)+0xcf),{x,y,0},handle))return false;s.put(0x6c,handle);
 auto a=child(s,signed_word(u32(index)+0x9f),h);if(!a.data)return false;a.put(0x4bc,word(width));
 auto b=child(s,signed_word(u32(index)+0xbf),h);if(!b.data)return false;b.put(0x4bc,word(width));s.put(0x1b4,u32(index));return true;
}
bool resize_hud_message_window(AnmView s,i32 index,float width,HudMessageWindowHost& h){
 auto a=child(s,signed_word(u32(index)+0x9f),h);if(!a.data)return false;const float value=width+16.f;a.put(0x4bc,word(value));
 auto b=child(s,signed_word(u32(index)+0xbf),h);if(!b.data)return false;b.put(0x4bc,word(value));return true;
}
}
