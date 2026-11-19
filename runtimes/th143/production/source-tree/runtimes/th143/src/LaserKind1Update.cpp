#include "LaserKind1Update.hpp"
#include <cmath>
namespace th143 {
namespace {
void set_zero_timer(AnmView t,u32 global){if(!(t.get(0x10)&1)){t.put(0xc,global);t.put(0x10,t.get(0x10)|1);}t.put(0,0xffffffff);t.put(4,0);t.put(8,0);}
bool decrement(AnmView t,LaserKind1Host& h){float rate=1;const u32 pointer=t.get(0xc);if(pointer&&!h.timer_rate(pointer,rate))return false;const bool unit=!pointer||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float next=t.floating(8)-(unit?1.f:rate);if(!std::isfinite(next))return false;t.put(0,t.get(4));t.put(8,word(next));t.put(4,next>=-2147483648.f&&next<2147483648.f?u32(i32(next)):0x80000000u);return true;}
bool dispatch(AnmView v){
 for(u32 steps=0;steps<64;++steps){const i32 cursor=signed_word(v.get(0x594));if(cursor>=18)return true;if(cursor<0)return false;auto row=v.sub(0x61c+u32(cursor)*0x2c);const u32 type=row.get(0x20);if(!type||(!row.get(0x24)&&v.get(0x598)))return true;
  if(type==0x80)v.put(0x5b4,row.get(0x10));else if(type==0x400)v.put(0x10,3);else if(type==0x100000)v.put(0x950,(v.get(0x950)&(row.get(0x10)?0xfffffe3fu:0xfffffe1fu))|(row.get(0x10)?0x20u:0u));
  v.put(0x594,u32(cursor)+1);
 }return false;
}
}
bool update_laser_kind1(AnmView v,u32 token,LaserKind1Host& host,LaserKind1UpdateServices& services,i32& result){
 if(!v.data||!dispatch(v))return false;const u32 active=v.get(0x598);
 if(active){if(active&0x80000000u){if(signed_word(v.get(0x1f0))<=0)v.put(0x598,active^0x80000000u);else if(!decrement(v.sub(0x1ec),host))return false;}if(v.get(0x5b4))v.put(0x5b4,v.get(0x5b4)-1);}
 float rate;if(!host.timer_rate(host.global_rate_token(),rate))return false;
 const float target=v.floating(0x5e0),length=v.floating(0x70);if(target>length){float next=v.floating(0x78)*rate+length;if(next>target)next=target;v.put(0x70,word(next));}
 float angle=v.floating(0x5dc)*rate+v.floating(0x6c);u32 wraps=0;while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(wraps++>32)break;}while(angle<real(0xc0490fdb)){angle+=real(0x40c90fdb);if(wraps++>32)break;}v.put(0x6c,word(angle));
 if(v.get(0x618)&1){std::array<float,3> p;bool present;if(!services.boss_position||!services.boss_position(p,present))return false;if(present)for(u32 i=0;i<3;++i)v.put(0x54+i*4,word(p[i]));}
 for(u32 i=0;i<3;++i)v.put(0x54+i*4,word(v.floating(0x5cc+i*4)*rate+v.floating(0x54+i*4)));
 u32 mode=v.get(0x10);i32 time=signed_word(v.get(0x1c));
 if(mode==3){if(time>=signed_word(v.get(0x5f0))){set_zero_timer(v.sub(0x18),host.global_rate_token());v.put(0x10,4);}}
 else{
  if(mode==4){const i32 duration=signed_word(v.get(0x5f4));if(time<duration){v.put(0x74,word((v.floating(0x5e8)*v.floating(0x20))/float(duration)));mode=0;}else{set_zero_timer(v.sub(0x18),host.global_rate_token());v.put(0x10,2);v.put(0x74,v.get(0x5e8));mode=2;time=0;}}
  if(mode==2&&time>=signed_word(v.get(0x5f8))){set_zero_timer(v.sub(0x18),host.global_rate_token());v.put(0x10,5);mode=5;time=0;}
  if(mode==5){const i32 duration=signed_word(v.get(0x5fc));if(time>=duration){result=1;return true;}const float width=v.floating(0x5e8);v.put(0x74,word(width-(v.floating(0x20)*width)/float(duration)));}
 }
 if(!services.contact||!services.contact(token,false))return false;
 u32 width,height;const u32 sprite=v.get(0x964);if(!sprite||!host.read(sprite+0x38,&height,4)||!host.read(sprite+0x34,&width,4))return false;
 auto main=v.sub(0x938);main.put(0x18,main.get(0x18)|8);main.put(0x60,word(v.floating(0x74)/real(height)));main.put(0x18,main.get(0x18)|8);main.put(0x64,word(v.floating(0x70)/real(width)));
 if(anm_step(main,host)==-2)return false;if(v.floating(0x7c)==0.f&&anm_step(v.sub(0xf04),host)==-2)return false;result=0;return true;
}
}
