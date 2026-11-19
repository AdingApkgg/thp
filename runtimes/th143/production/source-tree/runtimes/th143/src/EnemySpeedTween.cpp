#include "EnemySpeedTween.hpp"
namespace th143 {
i32 enemy_speed_command(Emitters& actor,Vm& vm,VmHost& host,AnmTimerHost& rates){
 const u32 op=vm.instruction->opcode;if(op<444||op>447)return -2;const u32 position=op<446?0x88:0xcc;
 if(!(op&1)){const float speed=vm.float_argument(0,host);if(vm.failed)return -2;if(double(speed)>-999999.)actor.put(position+0x18,word(speed));actor.put(position+0x40,actor.get(position+0x40)&~15u);return 0;}
 const u32 at=op==445?0x49c:0x4fc;float target=vm.float_argument(2,host);const u32 from=actor.get(position+0x18);const i32 duration=vm.integer_argument(0,host);if(vm.failed)return -2;if(duration<=0){actor.put(at+0x28,0);return 0;}
 const u32 mode=u32(vm.integer_argument(1,host));if(!(double(target)>-999999.))target=mode==7?0.f:real(from);const u32 count=u32(vm.integer_argument(0,host));if(vm.failed)return -2;
 actor.put(at,from);actor.put(at+0x28,count);actor.put(at+0x2c,mode);actor.put(at+8,0);actor.put(at+12,0);actor.put(at+4,word(target));scalar_reset_timer({actor.data.data()+at},rates);actor.put(position+0x40,actor.get(position+0x40)&~15u);return 0;
}
}
