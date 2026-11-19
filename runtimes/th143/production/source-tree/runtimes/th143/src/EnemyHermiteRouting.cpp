#include "EnemyHermiteRouting.hpp"
namespace th143 {
i32 enemy_hermite_routing(AnmView actor,Vm& vm,VmHost& host,u32 rate){
 const u32 op=vm.instruction->opcode;if(op!=425&&op!=426)return -2;
 const u32 base=op==425?0x88:0xcc,at=op==425?0x39c:0x404;
 const float x=vm.float_argument(3,host),y=vm.float_argument(4,host),ax=vm.float_argument(1,host),ay=vm.float_argument(2,host),bx=vm.float_argument(5,host),by=vm.float_argument(6,host);
 const u32 duration=u32(vm.integer_argument(0,host));if(vm.failed)return -2;auto state=actor.sub(at);
 state.put(0x64,state.get(0x64)&~1u);state.put(0x50,duration);state.put(0x60,8);
 for(u32 i=0;i<3;++i)state.put(0x0c+i*4,actor.get(base+i*4));
 state.put(0x24,word(ax));state.put(0x28,word(ay));state.put(0x2c,0);
 state.put(0x30,word(bx));state.put(0x34,word(by));state.put(0x38,0);
 state.put(0x18,double(x)>-999999.?word(x):actor.get(base));state.put(0x1c,double(y)>-999999.?word(y):actor.get(base+4));state.put(0x20,0);
 if(!(state.get(0x4c)&1)){state.put(0x48,rate);state.put(0x4c,state.get(0x4c)|1);}
 state.put(0x3c,0xffffffff);state.put(0x40,0);state.put(0x44,0);actor.put(base+0x40,actor.get(base+0x40)&~15u);return 0;
}
}
