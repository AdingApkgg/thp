#include "FailureManualPageV152.hpp"
namespace th143 {
bool advance_failure_manual_page_v152(AnmView menu,u32 self,PauseManualPageHost& h){
 if(!menu.data||menu.get(0x3ec)!=11)return false;
 auto call=[&](u32 e,u32 owner,std::initializer_list<u32> a){return h.pause_manual_call(e,owner,a);};
 u32 manual;
 if(menu.get(0x14)==20){
  if(!call(0x484730,self+0x1e8,{})||!call(0x4347b0,0,{})||!h.pause_manual_read(0x4e6b60,&manual,4))return false;
  const u32 x=0x43000000;if(!h.pause_manual_write(manual+0x12c,&x,4))return false;
 }else if(!h.pause_manual_read(0x4e6b60,&manual,4))return false;
 if(!manual)return true;u32 done;if(!h.pause_manual_read(manual+0x128,&done,4))return false;if(!done)return true;
 return call(0x434860,0,{})&&call(0x447630,self,{1})&&call(0x4087f0,self+0x10,{0})&&call(0x4846f0,self+0x1e8,{});
}
}
