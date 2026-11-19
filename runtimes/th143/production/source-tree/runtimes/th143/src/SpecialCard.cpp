#include "SpecialCard.hpp"
#include <algorithm>
namespace th143 {
namespace {
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
void reset(AnmView o,u32 at,AnmTimerHost& h){if(!(o.get(at+16)&1)){o.put(at+12,h.global_rate_token());o.put(at+16,o.get(at+16)|1);}o.put(at,0xffffffff);o.put(at+4,0);o.put(at+8,0);}
bool tick(AnmView o,u32 at,AnmTimerHost& h){u32 p=o.get(at+12),old=o.get(at+4);float r=1;if(p&&!h.timer_rate(p,r))return false;o.put(at,old);bool unit=!p||(r>real(0x3f7d70a4)&&r<real(0x3f8147ae));float v=o.floating(at+8)+(unit?1.f:r);o.put(at+4,unit?old+1:truncate(v));o.put(at+8,word(v));return true;}
}
bool start_special_card(AnmView o,SpecialCardGlobals& g,u32 card,const u8* name,u32 n,u32 duration,AnmTimerHost& rates,SpecialCardHost& host){
 if(!o.data||!name||n>=0x40||std::memchr(name,0,n))return false;reset(o,0x24,rates);o.put(0x78,card);std::memcpy(o.data+0x38,name,n);o.data[0x38+n]=0;o.put(0x7c,((o.get(0x7c)|3)&0xffffff47)|(g.mode==1?0x20:0));o.put(0x7c,o.get(0x7c)&~0x40u);o.put(0x90,1);
 for(auto row:{std::array<u32,3>{g.ascii_resource,0,0x14},{g.text_resource,2,0x18},{g.ascii_resource,1,0x1c}}){u32 handle;if(!host.special_create(row[0],i32(row[1]),handle))return false;o.put(row[2],handle);}
 auto text=host.special_visual(o.get(0x18));if(!text.data)o.put(0x18,0);if(!host.special_text(text,name,n)||!host.special_sound(33))return false;
 u32 handle;if(!host.special_create(g.effect_resource,3,handle))return false;o.put(0x20,handle);std::array<float,3> p;bool exists;if(!host.special_boss_position(p,exists)||!exists)return false;
 for(u32 i=0;i<3;++i)o.put(0xac+i*4,word(p[i]));auto vm=host.special_visual(handle);if(vm.data)for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,word(p[i]));
 for(i32 script:{1,2}){vm=host.special_visual(o.get(0x20));if(!vm.data){o.put(0x20,0);return false;}auto child=host.special_child(vm,script);if(!child.data)return false;child.put(0x4b4,duration);}
 o.put(0x88,duration);const u32 bonus=(g.difficulty+4)*50000u;o.put(0x80,bonus);o.put(0x84,signed_word(bonus)>=1000000000?999999999:bonus);
 if(!host.special_create(g.effect_resource,10,handle))return false;
 const auto* d=scene_descriptor(g.scene);if(!d)return false;const bool current=signed_word(g.dirty)<6&&d->parameters[10]!=0xffffffff||(card>=52&&card<=63);
 const u32 a=current?10:1,b=current?12:3;const i32 slot=signed_word(d->parameters[a]);if(slot<0||slot>=6)return false;
 // Descriptor resource slots are supplied as owner-local indices by the host.
 if(!host.special_create(0x80000000u|u32(slot),signed_word(d->parameters[a+1]),handle))return false;o.put(0x10,handle);
 const i32 second=signed_word(d->parameters[b]);if(second!=-1){if(second<0||second>=6||!host.special_create(0x80000000u|u32(second),signed_word(d->parameters[b+1]),handle))return false;}
 return true;
}
bool stop_special_card(AnmView o,SpecialCardGlobals& g,SpecialCardHost& h){
 if(!(o.get(0x7c)&1))return true;if(!h.special_background(true))return false;for(u32 at:{0x14u,0x18u,0x1cu})if(!h.special_signal(o.get(at),1))return false;o.put(0x7c,o.get(0x7c)&~1u);if(!h.special_retire(o.get(0x10)))return false;o.put(0x10,0);o.put(0x7c,o.get(0x7c)&~0x20u);if(!h.special_retire(o.get(0x20)))return false;o.put(0x20,0);
 if(o.get(0x7c)&2){u32 v=g.score+u32(signed_word(o.get(0x80))/10);g.score=v>=1000000000?999999999:v;if(!h.special_sound(46))return false;}return !(o.get(0x7c)&0x80)||h.special_sound(69);
}
bool update_special_card(AnmView o,SpecialCardGlobals& g,float y,AnmTimerHost& rates,SpecialCardHost& h){
 if(!(o.get(0x7c)&1))return true;o.put(0x90,o.get(0x90)+1);const i32 time=signed_word(o.get(0x28));if(time>=60&&!h.special_background(false))return false;
 if(time>=300&&!(o.get(0x7c)&8)){const i32 base=signed_word(o.get(0x84)),den=signed_word(o.get(0x88))-300;if(!den)return false;const i32 next=signed_word(o.get(0x80))-(base-base/3)/den;o.put(0x80,u32(next/10)*10);}
 if(!tick(o,0x24,rates))return false;
 if(signed_word(o.get(0x28))>=120){const u32 flags=o.get(0x7c);const bool reverse=(flags&0x100)!=0;const bool hide=!(flags&4)&&(!reverse?y<96.f:y>352.f);const bool show=(flags&4)&&(!reverse?y>128.f:y<320.f);
  if(hide||show){for(u32 at:{0x14u,0x18u,0x1cu})if(!h.special_signal(o.get(at),hide?3:2))return false;o.put(0x7c,hide?flags|4:flags&~4u);}}
 std::array<float,3> p;bool exists;if(!h.special_boss_position(p,exists))return false;if(exists)for(u32 i=0;i<3;++i){const float v=(p[i]-o.floating(0xac+i*4))*.05f+o.floating(0xac+i*4);o.put(0xac+i*4,word(v));}
 auto vm=h.special_visual(o.get(0x20));if(vm.data)for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,o.get(0xac+i*4));if((o.get(0x7c)&0x20)&&g.mode!=1)o.put(0x7c,o.get(0x7c)&~0x20u);return true;
}
}
