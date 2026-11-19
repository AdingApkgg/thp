#include "EnemyOffsetPositionTween.hpp"
namespace th143 {
i32 enemy_offset_position_tween_command(ActorState& actor,Vm& vm,VmHost& host,AnmTimerHost& rates){
 const u32 op=vm.instruction->opcode;if(op!=436&&op!=437)return -2;const u32 base=op==436?0x88:0xcc,at=op==436?0x39c:0x404;AnmView s{actor.fields.data.data()+at};
 float x=vm.float_argument(2,host),y=vm.float_argument(3,host);const i32 duration=vm.integer_argument(0,host);if(vm.failed)return -2;if(duration<=0){s.put(0x50,0);return 0;}
 x=(actor.get(0x4100)&0x80000)?actor.fields.floating(base)-x:actor.fields.floating(base)+x;y=actor.fields.floating(base+4)+y;
 const u32 count=u32(vm.integer_argument(0,host));if(vm.failed)return -2;s.put(0x50,count);for(u32 i=0;i<3;++i){s.put(0x24+i*4,0);s.put(0x30+i*4,0);}
 const u32 mode=u32(vm.integer_argument(1,host));if(vm.failed)return -2;s.put(0x64,s.get(0x64)&~1u);s.put(0x60,mode);
 for(u32 i=0;i<3;++i)s.put(0xc+i*4,actor.get(base+i*4));s.put(0x18,double(x)>-999999.?word(x):actor.get(base));s.put(0x1c,double(y)>-999999.?word(y):actor.get(base+4));s.put(0x20,0);
 if(!(s.get(0x4c)&1)){s.put(0x48,rates.global_rate_token());s.put(0x4c,s.get(0x4c)|1);}s.put(0x3c,0xffffffff);s.put(0x40,0);s.put(0x44,0);actor.put(base+0x40,actor.get(base+0x40)&~15u);return 0;
}
}
