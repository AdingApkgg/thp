#include "PauseEquipmentPage.hpp"
namespace th143 {
bool advance_pause_equipment_page(PauseMenu& menu,PauseEquipmentPageHost& h){
 auto m=menu.view();if(m.get(0x3ec)!=11)return false;u32 returned=0;
 auto read=[&](u32 p,u32& v){return h.equipment_page_read(p,&v,4);};
 auto write=[&](u32 p,u32 v){return h.equipment_page_write(p,&v,4);};
 auto call=[&](u32 e,u32 owner,std::initializer_list<u32> a){return h.equipment_page_call(e,owner,a,returned);};
 auto place=[&](u32 x,u32 y){u32 owner,state;if(!read(0x4e6b68,owner)||!read(owner+0x2b0,state)||!write(owner+0x484,x)||!write(owner+0x488,y)||!write(owner+0x48c,0))return false;return !state||call(0x438380,owner,{});};
 if(m.get(0x14)==20){
  u32 primary,secondary;if(!read(0x4e4710,primary)||!read(0x4e4714,secondary))return false;m.put(0x3f0,primary);m.put(0x3f4,secondary);
  if(!call(0x484730,menu.self+0x1e8,{})||!call(0x436ee0,0,{})||!place(0x43700000,0x43c80000)||!call(0x436c30,0,{2}))return false;
 }
 if(signed_word(m.get(0x14))<25)return true;
 if(!call(0x438350,0,{}))return false;if(returned)return true;
 if(!call(0x436ee0,0,{})||!place(0x447f0000,0x441c0000)||!call(0x436c30,0,{1}))return false;
 u32 primary,secondary;if(!read(0x4e4710,primary)||!read(0x4e4714,secondary))return false;
 if(primary==m.get(0x3f0)&&secondary==m.get(0x3f4))return call(0x472be0,0,{10})&&call(0x447630,menu.self,{3})&&call(0x4846f0,menu.self+0x1e8,{});
 return call(0x484320,0,{m.get(0x1ec),1})&&call(0x484320,0,{m.get(0x1e8),1})&&write(0x4e4ebc,10);
}
}
