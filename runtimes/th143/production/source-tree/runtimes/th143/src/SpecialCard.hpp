#pragma once
#include "AnmSignal.hpp"
#include "SceneCatalog.hpp"
namespace th143 {
struct SpecialCardGlobals {
 u32 ascii_resource=0,text_resource=0,effect_resource=0,mode=0,difficulty=0,dirty=0,scene=0,score=0;
};
struct SpecialCardHost {
 virtual ~SpecialCardHost()=default;
 virtual bool special_create(u32 resource,i32 script,u32& handle)=0;
 virtual AnmView special_visual(u32 handle)=0;
 virtual AnmView special_child(AnmView parent,i32 script)=0;
 virtual bool special_signal(u32 handle,i32 signal)=0;
 virtual bool special_retire(u32 handle)=0;
 virtual bool special_text(AnmView,const u8*,u32)=0;
 virtual bool special_sound(u32)=0;
 virtual bool special_boss_position(std::array<float,3>&,bool& exists)=0;
 virtual bool special_background(bool paused)=0;
};
//418e30 creation,4195f0 closure and418920 per-frame progression.
bool start_special_card(AnmView,SpecialCardGlobals&,u32 card,const u8* name,u32 name_bytes,u32 duration,AnmTimerHost&,SpecialCardHost&);
bool stop_special_card(AnmView,SpecialCardGlobals&,SpecialCardHost&);
bool update_special_card(AnmView,SpecialCardGlobals&,float player_y,AnmTimerHost&,SpecialCardHost&);
}
