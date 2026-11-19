#include "LaserKind2Wait.hpp"
namespace th143 {
bool activate_laser_kind2_wait(AnmView v,u32 rate){
 const i32 cursor=signed_word(v.get(0x594));if(cursor>=18)return true;if(cursor<0)return false;
 const u32 row=0x5ec+u32(cursor)*0x2c,type=v.get(row+0x20),active=v.get(0x598);
 if(!type||(!v.get(row+0x24)&&active)||(type&active))return true;if(type!=0x80000000u)return false;
 const u32 duration=v.get(row+0x10);if(signed_word(duration)>0){
  v.put(0x598,active|type);if(!(v.get(0x1fc)&1u)){v.put(0x1f8,rate);v.put(0x1fc,v.get(0x1fc)|1u);}
  v.put(0x1ec,duration-1);v.put(0x1f0,duration);v.put(0x1f4,word(float(signed_word(duration))));
 }
 v.put(0x594,u32(cursor)+1);return true;
}
}
